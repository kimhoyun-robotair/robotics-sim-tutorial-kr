"""RMPflow로 Franka가 목표를 추종하며 등록된 장애물을 회피합니다."""
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
    parser.add_argument('--target', nargs=3, type=float, default=[0.5, 0., 0.7])
    parser.add_argument('--debug-spheres', action='store_true')
    parser.add_argument('--ignore-state', action='store_true', help='디버깅: RMPflow 내부 rollout과 실제 관절 분리')
    parser.add_argument('--obstacle-y', type=float, default=0.15)
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
        from isaacsim.core.api.objects import VisualCuboid, FixedCuboid
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        from isaacsim.robot_motion.motion_generation import interface_config_loader
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        world = World(stage_units_in_meters=1.0, physics_dt=1./60.)
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/panda')
        robot = world.scene.add(SingleArticulation('/World/panda', name='panda'))
        target = world.scene.add(VisualCuboid('/World/target', name='target', size=0.04,
            position=np.array(args.target), color=np.array([1., 0.2, 0.2])))
        world.reset()

        from isaacsim.robot_motion.motion_generation import RmpFlow, ArticulationMotionPolicy, ArticulationKinematicsSolver
        config = interface_config_loader.load_supported_motion_policy_config('Franka', 'RMPflow')
        policy = RmpFlow(**config)
        obstacle = world.scene.add(FixedCuboid('/World/obstacle', name='obstacle', size=1.,
            scale=np.array([0.1, 0.2, 0.4]), position=np.array([0.4, args.obstacle_y, 0.4]),
            color=np.array([0.2, 0.3, 0.8])))
        policy.add_obstacle(obstacle)
        policy.set_ignore_state_updates(args.ignore_state)
        if args.debug_spheres:
            policy.visualize_collision_spheres()
            policy.visualize_end_effector_position()
        motion = ArticulationMotionPolicy(robot, policy, default_physics_dt=1./60.)
        kinematics = ArticulationKinematicsSolver(robot, policy.get_kinematics_solver(), 'right_gripper')
        trace = []
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            position, _ = target.get_world_pose()
            policy.set_robot_base_pose(*robot.get_world_pose())
            policy.set_end_effector_target(position)
            policy.update_world()
            robot.apply_action(motion.get_next_articulation_action())
            world.step(render=not args.headless)
            if not app.is_running():
                break
            if step % 30 == 0:
                ee_position, _ = kinematics.compute_end_effector_pose()
                trace.append({'step': step, 'target_m': position.tolist(), 'end_effector_m': ee_position.tolist(),
                              'position_error_m': float(np.linalg.norm(ee_position-position))})
            step += 1
        (output / 'tracking.json').write_text(json.dumps(trace, indent=2))
        print(json.dumps(trace[-1], indent=2) if trace else 'No physics step executed')
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
