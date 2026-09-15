"""SingleArticulation과 ArticulationAction으로 Franka 팔/손가락을 제어합니다."""
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
    parser.add_argument('--fingers-only', action='store_true')
    parser.add_argument('--finger-width', type=float, default=0.02)
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
        from isaacsim.storage.native import get_assets_root_path
        if not 0.0 <= args.finger_width <= 0.04:
            raise ValueError('finger-width는 손가락 하나의 이동량이며 0~0.04 m입니다')
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 Assets 경로를 찾을 수 없습니다')
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/panda')
        robot = world.scene.add(SingleArticulation('/World/panda', name='panda'))
        world.reset()
        names = ['panda_finger_joint1', 'panda_finger_joint2'] if args.fingers_only else [f'panda_joint{i}' for i in range(1, 8)] + ['panda_finger_joint1', 'panda_finger_joint2']
        indices = np.array([robot.get_dof_index(name) for name in names])
        targets = np.array([args.finger_width] * 2 if args.fingers_only else [0., -1., 0., -2.2, 0., 2.4, 0.8, args.finger_width, args.finger_width])
        initial = robot.get_joint_positions()[indices].copy()
        measured = initial.copy()
        action = ArticulationAction(joint_positions=targets, joint_indices=indices)
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            robot.apply_action(action)
            world.step(render=not args.headless)
            if not app.is_running():
                break
            measured = robot.get_joint_positions()[indices].copy()
            step += 1
        result = {'joint_names': names, 'joint_indices': indices.tolist(), 'initial': initial.tolist(),
                  'targets': targets.tolist(), 'measured': measured.tolist(),
                  'absolute_error': np.abs(measured - targets).tolist()}
        (output / 'joints.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
