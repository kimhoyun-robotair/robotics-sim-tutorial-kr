"""UR10e+Robotiq: gripper, IK, RMPflow, pick-and-place 네 실습 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='UR10e+Robotiq: gripper, IK, RMPflow, pick-and-place 네 실습')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Physics step limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--exercise", choices=["gripper", "ik", "rmpflow", "pick"], default="pick")
    parser.add_argument("--asset", help="Configured UR10e+Robotiq USD override")
    parser.add_argument("--target", type=float, nargs=3, default=[0.5, 0.0, 0.5])
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 6000 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import yaml
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid, VisualCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        # VisualCuboid는 강체·충돌 속성 없이 외형만 만드는 큐브로, 목표 위치 표시 등에 사용한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        # euler_angles_to_quat는 Euler 회전을 쿼터니언으로 변환한다. 기본 입력 단위는 라디안이다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.robot.manipulators import SingleManipulator
        # SingleManipulator는 로봇 팔의 관절 구조, 말단 장치와 그리퍼를 함께 다루는 클래스이다.
        from isaacsim.robot.manipulators.grippers import ParallelGripper
        # ParallelGripper는 지정한 손가락 관절의 열린 위치와 닫힌 위치를 이용해 평행 그리퍼를 제어한다.
        from isaacsim.robot.manipulators.controllers import PickPlaceController
        # PickPlaceController는 물체 접근·잡기·이동·놓기 단계를 진행하며 로봇의 관절 명령을 계산한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        import isaacsim.robot_motion.motion_generation as mg
        # motion_generation은 기구학 계산, 경로·궤적 생성, RMPflow 정책을 로봇 제어에 연결하는 API이다.
        physics_dt = 1/200 if args.exercise == "pick" else 1/60
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=physics_dt, rendering_dt=physics_dt)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset ur_gripper.usd")
        asset = args.asset or asset_root + "/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd"
        add_reference_to_stage(usd_path=asset, prim_path="/ur")
        gripper = ParallelGripper(end_effector_prim_path="/ur/ee_link/robotiq_arg2f_base_link",
            joint_prim_names=["finger_joint"], joint_opened_positions=np.array([0.0]),
            joint_closed_positions=np.array([0.7]), action_deltas=np.array([-0.7]), use_mimic_joints=True)
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleManipulator(prim_path="/ur", name="ur10e",
            end_effector_prim_path="/ur/ee_link/robotiq_arg2f_base_link", gripper=gripper))
        target = world.scene.add(VisualCuboid(prim_path="/World/Target", name="target", size=0.04,
            position=np.array(args.target), orientation=euler_angles_to_quat(np.array([-np.pi, 0.0, np.pi])),
            color=np.array([1.0, 0.2, 0.1])))
        cube = None
        place_goal = np.array([-0.3, 0.6, 0.05])
        if args.exercise == "pick":
            cube = world.scene.add(DynamicCuboid(prim_path="/World/Cube", name="cube", size=1,
                scale=np.array([0.1, 0.0515, 0.1]), position=np.array([0.3, 0.3, 0.3]), color=np.array([0.1, 0.2, 1.0])))
            target.set_world_pose(position=place_goal)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        config = Path(__file__).resolve().parent / "config"
        description = yaml.safe_load((config / "robot_descriptor.yaml").read_text())
        arm_indices = np.array([robot.get_dof_index(name) for name in description["cspace"]])
        # 관절 위치 상태를 직접 설정한다. 물리 제어기의 목표 위치를 지정하는 호출과 구분된다.
        robot.set_joint_positions(np.array(description["default_q"]), joint_indices=arm_indices)
        gripper.set_joint_positions(np.array([0.0]))
        solver = None
        motion = None
        pick = None
        if args.exercise == "ik":
            lula = mg.LulaKinematicsSolver(robot_description_path=str(config / "robot_descriptor.yaml"),
                                           urdf_path=str(config / "ur10e_kinematics.urdf"))
            # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
            lula.set_robot_base_pose(*robot.get_world_pose())
            solver = mg.ArticulationKinematicsSolver(robot, lula, "ee_link_robotiq_arg2f_base_link")
        elif args.exercise in ["rmpflow", "pick"]:
            rmp = mg.lula.motion_policies.RmpFlow(robot_description_path=str(config / "robot_descriptor.yaml"),
                urdf_path=str(config / "ur10e_kinematics.urdf"), rmpflow_config_path=str(config / "ur10e_rmpflow_common.yaml"),
                end_effector_frame_name="ee_link_robotiq_arg2f_base_link", maximum_substep_size=0.00334)
            rmp.set_robot_base_pose(*robot.get_world_pose())
            motion = mg.MotionPolicyController(name="ur_motion", articulation_motion_policy=mg.ArticulationMotionPolicy(robot, rmp, physics_dt))
            if args.exercise == "pick":
                pick = PickPlaceController(name="pick", cspace_controller=motion, gripper=gripper,
                    end_effector_initial_height=0.6,
                    events_dt=[0.005, 0.002, 1.0, 0.05, 0.0008, 0.005, 0.0008, 0.1, 0.0008, 0.008])
        ik_failures = 0
        samples = []
        target_error = float(np.linalg.norm(robot.end_effector.get_world_pose()[0]-target.get_world_pose()[0]))
        cube_target_error = float(np.linalg.norm(cube.get_world_pose()[0]-place_goal)) if cube else None
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            if args.exercise == "gripper":
                fraction = (step % 800) / 400
                goal = 0.7 * (fraction if fraction <= 1 else 2-fraction)
                gripper.apply_action(ArticulationAction(joint_positions=np.array([goal])))
            elif args.exercise == "ik":
                position, orientation = target.get_world_pose()
                action, success = solver.compute_inverse_kinematics(target_position=position, target_orientation=orientation)
                if success:
                    # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                    robot.apply_action(action)
                else:
                    ik_failures += 1
            elif args.exercise == "rmpflow":
                position, orientation = target.get_world_pose()
                robot.apply_action(motion.forward(target_end_effector_position=position, target_end_effector_orientation=orientation))
            elif not pick.is_done():
                # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
                robot.apply_action(pick.forward(picking_position=cube.get_world_pose()[0], placing_position=place_goal,
                    current_joint_positions=robot.get_joint_positions(), end_effector_offset=np.array([0.0, 0.0, 0.20])))
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            target_error = float(np.linalg.norm(robot.end_effector.get_world_pose()[0]-target.get_world_pose()[0]))
            cube_target_error = float(np.linalg.norm(cube.get_world_pose()[0]-place_goal)) if cube else None
            if step % 100 == 0:
                sample = {"step": step, "end_effector_m": robot.end_effector.get_world_pose()[0].tolist(),
                          "finger_rad": gripper.get_joint_positions().tolist()}
                if cube is not None:
                    sample["cube_m"] = cube.get_world_pose()[0].tolist()
                samples.append(sample)
                print(sample)
            step += 1
        result = {"exercise": args.exercise, "ik_failures": ik_failures, "samples": samples,
                  "controller_done": bool(pick.is_done()) if pick else None,
                  "target_error_m": target_error,
                  "cube_target_error_m": cube_target_error}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
