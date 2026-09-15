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
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController
        from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import HolonomicController
        from isaacsim.robot.wheeled_robots.controllers.ackermann_controller import AckermannController
        from isaacsim.storage.native import get_assets_root_path
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        if args.robot == 'differential':
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
        world.reset()
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
                robot.apply_action(ArticulationAction(joint_positions=action.joint_positions, joint_indices=steering))
                robot.apply_action(ArticulationAction(joint_velocities=action.joint_velocities, joint_indices=wheels))
            else:
                robot.apply_wheel_actions(action)
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
        app.close()


if __name__ == "__main__":
    main()
