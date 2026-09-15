"""RMP 항목을 순서대로 활성화하며 Franka 추종 오차를 비교합니다."""
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
    parser.add_argument('--phase', choices=['baseline', 'cspace', 'target', 'collision', 'directional', 'orientation', 'limits', 'damping'], default='baseline')
    parser.add_argument('--target-gain', type=float, help='target_rmp.accel_p_gain 한 값만 덮어쓰기')
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

        from copy import deepcopy
        import yaml
        from isaacsim.robot_motion.motion_generation import RmpFlow, ArticulationMotionPolicy, ArticulationKinematicsSolver
        config = interface_config_loader.load_supported_motion_policy_config('Franka', 'RMPflow')
        with open(config['rmpflow_config_path']) as stream:
            tuning = yaml.safe_load(stream)
        original = deepcopy(tuning['rmp_params'])
        params = tuning['rmp_params']
        if args.phase != 'baseline':
            # 모든 항목의 metric와 inertia를 끈 뒤 필요한 항목만 복구한다.
            for values in params.values():
                for key in list(values):
                    if key in ('metric_weight', 'metric_scalar', 'min_metric_scalar', 'max_metric_scalar', 'min_metric_alpha', 'inertia', 'weight'):
                        values[key] = 0.0
            phases = ['cspace', 'target', 'collision', 'directional', 'orientation', 'limits', 'damping']
            level = phases.index(args.phase)
            active = ['cspace_target_rmp']
            if level >= 1:
                active.append('target_rmp')
            if level >= 2:
                active.append('collision_rmp')
            if level >= 4:
                active.append('axis_target_rmp')
            if level >= 5:
                active.extend(['joint_limit_rmp', 'joint_velocity_cap_rmp'])
            if level >= 6:
                active.append('damping_rmp')
            for key in active:
                params[key] = deepcopy(original[key])
            params['cspace_target_rmp']['inertia'] = original['cspace_target_rmp']['inertia'] if level >= 6 else 0.0
            if 1 <= level < 3:
                params['target_rmp']['min_metric_alpha'] = 0.0
                params['target_rmp']['metric_alpha_length_scale'] = 100000.0
                params['target_rmp']['proximity_metric_boost_scalar'] = 1.0
        if args.target_gain is not None:
            if args.target_gain < 0:
                raise ValueError('--target-gain must be nonnegative')
            params['target_rmp']['accel_p_gain'] = args.target_gain
        local_config = output / 'rmpflow.yaml'
        local_config.write_text(yaml.safe_dump(tuning, sort_keys=False))
        config['rmpflow_config_path'] = str(local_config)
        policy = RmpFlow(**config)
        obstacle = world.scene.add(FixedCuboid('/World/obstacle', name='obstacle', size=1.,
            scale=np.array([0.1, 0.2, 0.4]), position=np.array([0.4, 0.15, 0.4])))
        policy.add_obstacle(obstacle)
        policy.visualize_collision_spheres()
        motion = ArticulationMotionPolicy(robot, policy, default_physics_dt=1./60.)
        kinematics = ArticulationKinematicsSolver(robot, policy.get_kinematics_solver(), 'right_gripper')
        trace = []
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            position, _ = target.get_world_pose()
            policy.set_robot_base_pose(*robot.get_world_pose())
            policy.set_end_effector_target(position, np.array([0., 0., 1., 0.]))
            policy.update_world()
            robot.apply_action(motion.get_next_articulation_action())
            world.step(render=not args.headless)
            if not app.is_running():
                break
            if step % 15 == 0:
                ee_position, _ = kinematics.compute_end_effector_pose()
                trace.append({'step': step, 'end_effector_m': ee_position.tolist(),
                              'error_m': float(np.linalg.norm(ee_position-position)),
                              'joint_velocities_rad_s': robot.get_joint_velocities().tolist()})
            step += 1
        (output / 'tuning_trace.json').write_text(json.dumps({'phase': args.phase, 'trace': trace}, indent=2))
        print('Phase:', args.phase, 'last sample:', trace[-1] if trace else None)
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
