"""차동 Jetbot, 전방향 Kaya, Ackermann Leatherback의 바퀴 제어를 비교합니다."""
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
    parser.add_argument('--robot', choices=['differential', 'holonomic', 'ackermann'], default='differential')
    parser.add_argument('--speed', type=float, default=0.3, help='전진 속도 m/s')
    parser.add_argument('--turn', type=float, default=0.3, help='yaw rad/s; Ackermann에서는 조향각 rad')
    parser.add_argument('--lateral', type=float, default=0.2, help='Kaya의 측면 속도 m/s')
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
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        # WheeledRobot은 바퀴 관절을 지정해 이동 로봇을 구성하고 바퀴에 제어 명령을 적용하는 클래스이다.
        from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController
        # DifferentialController는 선속도와 회전 각속도를 좌우 바퀴 속도로 변환하는 차동 구동 제어기이다.
        from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import HolonomicController
        # HolonomicController는 전방·측방·회전 속도 명령을 바퀴 배치에 맞는 관절 속도로 변환한다.
        from isaacsim.robot.wheeled_robots.controllers.ackermann_controller import AckermannController
        # AckermannController는 Ackermann 조향 구조에 맞춰 조향 관절과 구동 바퀴의 명령을 계산한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        if args.robot == 'differential':
            # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
            robot = world.scene.add(WheeledRobot(prim_path='/World/Jetbot', name='jetbot',
                wheel_dof_names=['left_wheel_joint', 'right_wheel_joint'], create_robot=True,
                usd_path=assets + '/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd', position=np.array([0., 0., 0.1])))
            controller = DifferentialController('differential', wheel_radius=0.03, wheel_base=0.1125)
            command = [args.speed, args.turn]
        elif args.robot == 'holonomic':
            robot = world.scene.add(WheeledRobot(prim_path='/World/Kaya', name='kaya',
                wheel_dof_names=['axle_0_joint', 'axle_1_joint', 'axle_2_joint'], create_robot=True,
                usd_path=assets + '/Isaac/Robots/NVIDIA/Kaya/kaya.usd', position=np.array([0., 0., 0.1])))
            controller = HolonomicController(name='holonomic', wheel_radius=np.array([0.04]*3),
                wheel_positions=np.array([[-0.0980432, 0.000636773, -0.050501], [0.0493475, -0.084525, -0.050501], [0.0495291, 0.0856937, -0.050501]]),
                wheel_orientations=np.array([[0., 0., 0., 1.], [0.866, 0., 0., -0.5], [0.866, 0., 0., 0.5]]),
                mecanum_angles=np.array([90., 90., 90.]))
            command = [args.speed, args.lateral, args.turn]
        else:
            add_reference_to_stage(assets + '/Isaac/Robots/NVIDIA/Leatherback/leatherback.usd', '/World/Leatherback')
            robot = world.scene.add(SingleArticulation('/World/Leatherback', name='leatherback'))
            controller = AckermannController('ackermann', wheel_base=1.65, track_width=1.25,
                front_wheel_radius=0.25, back_wheel_radius=0.25)
            command = [args.turn, 0., args.speed, 0., 0.]
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
        initial, orientation = robot.get_world_pose()
        position = initial.copy()
        if args.robot == 'ackermann':
            steering = np.array([robot.get_dof_index('Knuckle__Upright__Front_' + side) for side in ['Left', 'Right']])
            wheel_names = ['Wheel__Knuckle__Front_Left', 'Wheel__Knuckle__Front_Right', 'Wheel__Upright__Rear_Left', 'Wheel__Upright__Rear_Right']
            wheels = np.array([robot.get_dof_index(name) for name in wheel_names])
            robot.get_articulation_controller().switch_dof_control_mode(int(steering[0]), 'position')
            robot.get_articulation_controller().switch_dof_control_mode(int(steering[1]), 'position')
            for index in wheels:
                robot.get_articulation_controller().switch_dof_control_mode(int(index), 'velocity')
        action = controller.forward(command)
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            if args.robot == 'ackermann':
                # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                robot.apply_action(ArticulationAction(joint_positions=action.joint_positions, joint_indices=steering))
                robot.apply_action(ArticulationAction(joint_velocities=action.joint_velocities, joint_indices=wheels))
            else:
                # 바퀴에 해당하는 관절에 제어 명령을 적용한다.
                robot.apply_wheel_actions(action)
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            position, orientation = robot.get_world_pose()
            step += 1
        result = {'controller': args.robot, 'command': command,
                  'wheel_velocity_targets_rad_s': np.asarray(action.joint_velocities).tolist(),
                  'steering_targets_rad': None if action.joint_positions is None else np.asarray(action.joint_positions).tolist(),
                  'initial_position_m': initial.tolist(), 'final_position_m': position.tolist(),
                  'orientation_wxyz': orientation.tolist()}
        (output / 'drive.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        print('Output:', output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
