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

        from isaacsim.robot_motion.motion_generation import LulaKinematicsSolver, ArticulationKinematicsSolver
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
            solver.set_robot_base_pose(*robot.get_world_pose())
            action, success = kinematics.compute_inverse_kinematics(position)
            if success:
                successes += 1
                robot.apply_action(action)
            world.step(render=not args.headless)
            if not app.is_running():
                break
            if step % 30 == 0:
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
        app.close()


if __name__ == "__main__":
    main()
