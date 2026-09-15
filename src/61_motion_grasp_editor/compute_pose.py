"""Apply an exported isaac_grasp transform to an actual supplied object pose."""
import argparse
import json
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grasp-file', required=True, type=Path)
    parser.add_argument('--name', default='grasp_0')
    parser.add_argument('--object-position', nargs=3, type=float, default=[0.5, 0.0, 0.2])
    parser.add_argument('--object-quaternion', nargs=4, type=float, default=[1.0, 0.0, 0.0, 0.0], metavar=('W', 'X', 'Y', 'Z'))
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output' / 'target.json')
    args = parser.parse_args()
    if not args.grasp_file.is_file():
        parser.error('grasp-file must exist')
    values = args.object_position + args.object_quaternion
    if not all(math.isfinite(value) for value in values):
        parser.error('pose must contain finite numbers')
    if not math.isclose(sum(x * x for x in args.object_quaternion), 1.0, abs_tol=1e-5):
        parser.error('object-quaternion must have unit norm, in W X Y Z order')
    if args.output.exists():
        parser.error('Output exists; choose another --output')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': True})
    try:
        import numpy as np
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension('isaacsim.robot_setup.grasp_editor')
        from isaacsim.robot_setup.grasp_editor import import_grasps_from_file
        spec = import_grasps_from_file(str(args.grasp_file.resolve()))
        if args.name not in spec.get_grasp_names():
            raise ValueError(f'Unknown grasp {args.name}; available: {spec.get_grasp_names()}')
        position, quaternion = spec.compute_gripper_pose_from_rigid_body_pose(
            args.name, np.array(args.object_position), np.array(args.object_quaternion)
        )
        result = {'grasp': args.name, 'position': position.tolist(), 'quaternion_wxyz': quaternion.tolist()}
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
        print(json.dumps(result, indent=2))
    finally:
        app.close()


if __name__ == '__main__':
    main()
