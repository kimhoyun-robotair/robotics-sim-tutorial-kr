"""Lula FK와 IK를 계산하고 실제 관절 상태에서 말단 위치 오차를 측정합니다."""
import argparse
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None,
                        help="Physics step limit; omitted/0: GUI until closed, headless default: 600")
    parser.add_argument("--output", type=Path, help="새 결과 디렉터리; 기존 경로는 거부")
    parser.add_argument('--target', nargs=3, type=float, default=[0.3, 0., 0.5])
    parser.add_argument('--frame', default='right_gripper')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 600 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires positive steps")
    if args.output is None:
        parent = Path(__file__).resolve().parent / "output"
        parent.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="run_", dir=parent))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import VisualCuboid, FixedCuboid
        # VisualCuboid는 강체·충돌 속성 없이 외형만 만드는 큐브로, 목표 위치 표시 등에 사용한다.
        # FixedCuboid는 충돌 가능한 고정 큐브로, 바닥이나 움직이지 않는 장애물을 만들 때 사용한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.robot_motion.motion_generation import interface_config_loader
        # interface_config_loader는 지원 로봇의 기구학·모션 정책 설정 파일 경로와 매개변수를 불러온다.
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1./60.)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/panda')
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleArticulation('/World/panda', name='panda'))
        target = world.scene.add(VisualCuboid('/World/target', name='target', size=0.04,
            position=np.array(args.target), color=np.array([1., 0.2, 0.2])))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()

        from isaacsim.robot_motion.motion_generation import LulaKinematicsSolver, ArticulationKinematicsSolver
        # LulaKinematicsSolver는 로봇 모델을 이용해 정기구학과 역기구학을 계산한다.
        # ArticulationKinematicsSolver는 시뮬레이터의 로봇 관절과 기구학 계산기를 연결한다.
        # 말단 자세를 계산하거나 역기구학 결과를 로봇에 적용할 ArticulationAction으로 받을 수 있다.
        config = interface_config_loader.load_supported_lula_kinematics_solver_config('Franka')
        solver = LulaKinematicsSolver(**config)
        frames = solver.get_all_frame_names()
        if args.frame not in frames:
            raise ValueError(f'알 수 없는 frame {args.frame}; 가능 목록: {frames}')
        kinematics = ArticulationKinematicsSolver(robot, solver, args.frame)
        trace = []
        successes = 0
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            position, _ = target.get_world_pose()
            # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
            solver.set_robot_base_pose(*robot.get_world_pose())
            # 목표 말단 자세에 도달하는 관절 명령과 계산 성공 여부를 구한다.
            action, success = kinematics.compute_inverse_kinematics(position)
            if success:
                successes += 1
                # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                robot.apply_action(action)
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            if step % 30 == 0:
                # 현재 관절 상태로부터 말단 위치·회전을 계산한다.
                ee_position, rotation = kinematics.compute_end_effector_pose()
                trace.append({'step': step, 'ik_success': bool(success), 'fk_position_m': ee_position.tolist(),
                              'fk_rotation_matrix': rotation.tolist(), 'target_m': position.tolist(),
                              'position_error_m': float(np.linalg.norm(position-ee_position))})
            step += 1
        (output / 'kinematics.json').write_text(json.dumps({'frame': args.frame, 'available_frames': frames, 'trace': trace}, indent=2))
        print(json.dumps(trace[-1], indent=2) if trace else 'No physics step executed')
        print('Output:', output)
        if successes == 0:
            raise RuntimeError('IK가 한 번도 수렴하지 않았습니다. 목표가 작업영역 안인지 확인하세요')
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
