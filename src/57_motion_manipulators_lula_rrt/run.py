"""Lula RRT로 장애물이 있는 Franka 경로를 계획하고 시각화합니다."""
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
    parser.add_argument('--target', nargs=3, type=float, default=[0.45, 0.5, 0.7])
    parser.add_argument('--max-iterations', type=int, default=5000)
    parser.add_argument('--max-cspace-dist', type=float, default=0.01)
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

        from isaacsim.robot_motion.motion_generation import PathPlannerVisualizer
        from isaacsim.robot_motion.motion_generation.lula import RRT
        if args.max_iterations < 1 or args.max_cspace_dist <= 0:
            raise ValueError('RRT iterations와 interpolation 간격은 양수여야 합니다')
        config = interface_config_loader.load_supported_path_planner_config('Franka', 'RRT')
        planner = RRT(**config)
        planner.set_max_iterations(args.max_iterations)
        obstacle = world.scene.add(VisualCuboid('/World/wall', name='wall', size=1.,
            scale=np.array([0.1, 0.4, 0.4]), position=np.array([0.3, 0.6, 0.6])))
        planner.add_obstacle(obstacle)
        visualizer = PathPlannerVisualizer(robot, planner)
        actions = []
        action_index = 0
        last_target = None
        plans = []
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            current, _ = target.get_world_pose()
            if step % 60 == 0 and (last_target is None or np.linalg.norm(current-last_target) > 0.01):
                planner.set_robot_base_pose(*robot.get_world_pose())
                planner.set_end_effector_target(current)
                planner.update_world()
                actions = visualizer.compute_plan_as_articulation_actions(max_cspace_dist=args.max_cspace_dist)
                action_index = 0
                last_target = current.copy()
                record = {'step': step, 'target_m': current.tolist(), 'success': bool(actions),
                          'joint_positions': [np.asarray(a.joint_positions).tolist() for a in actions],
                          'joint_indices': [] if not actions else np.asarray(actions[0].joint_indices).tolist()}
                plans.append(record)
                print('RRT plan:', len(actions), 'interpolated actions; success:', bool(actions))
            if action_index < len(actions):
                robot.apply_action(actions[action_index])
                action_index += 1
            world.step(render=not args.headless)
            step += 1
        (output / 'plans.json').write_text(json.dumps(plans, indent=2))
        print('Output:', output)
        if not any(plan['success'] for plan in plans):
            raise RuntimeError('RRT가 경로를 찾지 못했습니다. plans.json과 목표/장애물/반복 제한을 확인하세요')
    finally:
        app.close()


if __name__ == "__main__":
    main()
