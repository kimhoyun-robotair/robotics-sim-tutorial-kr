"""UR10의 c-space, timestamped, task-space, composite 궤적을 생성합니다."""
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
    parser.add_argument('--trajectory', choices=['cspace', 'timestamped', 'taskspace', 'composite'], default='cspace')
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
        import lula
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import VisualCuboid
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.extensions import get_extension_path_from_name
        from isaacsim.storage.native import get_assets_root_path
        from isaacsim.robot_motion.motion_generation import (LulaCSpaceTrajectoryGenerator,
            LulaTaskSpaceTrajectoryGenerator, LulaKinematicsSolver, ArticulationTrajectory)
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        world = World(stage_units_in_meters=1.0, physics_dt=1./60.)
        # 공식 관절 경로는 로봇 원점 아래도 지나므로 바닥을 작업영역 밖에 둔다.
        floor_z = -2.0
        world.scene.add_default_ground_plane(z_position=floor_z)
        add_reference_to_stage(assets + '/Isaac/Robots/UniversalRobots/ur10/ur10.usd', '/World/ur10')
        robot = world.scene.add(SingleArticulation('/World/ur10', name='ur10'))
        world.reset()
        configs = Path(get_extension_path_from_name('isaacsim.robot_motion.motion_generation')) / 'motion_policy_configs/universal_robots/ur10'
        kwargs = {'robot_description_path': str(configs / 'rmpflow/ur10_robot_description.yaml'),
                  'urdf_path': str(configs / 'ur10_robot.urdf')}
        kinematics = LulaKinematicsSolver(**kwargs)
        if args.trajectory in ('cspace', 'timestamped'):
            generator = LulaCSpaceTrajectoryGenerator(**kwargs)
            points = np.array([[-0.41, 0.5, -2.36, -1.28, 5.13, -4.71], [-1.43, 1., -2.58, -1.53, 6., -4.74],
                               [-2.83, 0.34, -2.11, -1.38, 1.26, -4.71], [-0.41, 0.5, -2.36, -1.28, 5.13, -4.71]])
            if args.trajectory == 'timestamped':
                trajectory = generator.compute_timestamped_c_space_trajectory(points, np.array([0., 5., 10., 13.]))
            else:
                trajectory = generator.compute_c_space_trajectory(points)
            targets = [kinematics.compute_forward_kinematics('ee_link', point)[0] for point in points]
        elif args.trajectory == 'taskspace':
            generator = LulaTaskSpaceTrajectoryGenerator(**kwargs)
            targets = np.array([[0.3, -0.3, 0.1], [0.3, 0.3, 0.1], [0.3, 0.3, 0.5], [0.3, -0.3, 0.5], [0.3, -0.3, 0.1]])
            orientations = np.tile(np.array([0., 1., 0., 0.]), (len(targets), 1))
            trajectory = generator.compute_task_space_trajectory_from_points(targets, orientations, 'ee_link')
        else:
            generator = LulaTaskSpaceTrajectoryGenerator(**kwargs)
            rotation = lula.Rotation3(np.pi/2, np.array([1., 0., 0.]))
            path = lula.create_task_space_path_spec(lula.Pose3(rotation, np.array([0.3, -0.1, 0.3])))
            path.add_translation(np.array([0.3, -0.1, 0.5]))
            path.add_rotation(lula.Rotation3(np.pi/3, np.array([1., 0., 0.])))
            path.add_three_point_arc(np.array([0.3, 0.3, 0.3]), np.array([0.3, 0., 0.5]), constant_orientation=True)
            composite = lula.create_composite_path_spec(np.zeros(6))
            composite.add_task_space_path_spec(path, lula.CompositePathSpec.TransitionMode.FREE)
            joint_path = lula.create_c_space_path_spec(np.zeros(6))
            joint_path.add_c_space_waypoint(np.array([0., 0.5, -2., -1.28, 5.13, -4.71]))
            composite.add_c_space_path_spec(joint_path, lula.CompositePathSpec.TransitionMode.FREE)
            trajectory = generator.compute_task_space_trajectory_from_path_spec(composite, 'ee_link')
            targets = [np.array([0.3, -0.1, 0.3]), np.array([0.3, -0.1, 0.5]), np.array([0.3, 0.3, 0.3])]
        if trajectory is None:
            raise RuntimeError('Lula가 궤적을 만들지 못했습니다. joint limit/waypoint/시간 제한을 확인하세요')
        for index, position in enumerate(targets):
            world.scene.add(VisualCuboid(f'/World/waypoint_{index}', name=f'waypoint_{index}', size=0.025,
                position=position, color=np.array([1., 0.2, 0.2])))
        actions = ArticulationTrajectory(robot, trajectory, physics_dt=1./60.).get_action_sequence()
        if not actions:
            raise RuntimeError('생성된 action sequence가 비어 있습니다')
        # 시작 상태 설정에만 teleport를 사용한다. 재생 중에는 drive target을 적용한다.
        robot.set_joint_positions(actions[0].joint_positions, joint_indices=actions[0].joint_indices)
        trace = []
        executed_steps = 0
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            action = actions[min(step, len(actions)-1)]
            robot.apply_action(action)
            world.step(render=not args.headless)
            if not app.is_running():
                break
            executed_steps += 1
            if step % 15 == 0:
                measured = robot.get_joint_positions()[action.joint_indices]
                trace.append({'step': step, 'target_positions': np.asarray(action.joint_positions).tolist(),
                              'measured_positions': measured.tolist()})
            step += 1
        result = {'mode': args.trajectory, 'physics_dt_s': 1./60., 'ground_plane_z_m': floor_z, 'action_count': len(actions),
                  'duration_s': (len(actions)-1)/60., 'completed_sequence': executed_steps >= len(actions), 'trace': trace}
        (output / 'trajectory.json').write_text(json.dumps(result, indent=2))
        print('Trajectory:', args.trajectory, 'actions:', len(actions), 'full playback:', result['completed_sequence'])
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
