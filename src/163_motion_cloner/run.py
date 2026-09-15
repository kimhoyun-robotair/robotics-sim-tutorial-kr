"""Cloner와 GridCloner로 환경 복제, 일괄 포즈 변경, 충돌 필터를 관찰합니다."""
import argparse
from itertools import count
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 600")
    parser.add_argument("--output", type=Path, help="새 결과 디렉터리; 기존 경로는 거부")
    parser.add_argument('--layout', choices=['grid', 'line'], default='grid')
    parser.add_argument('--count', type=int, default=4)
    parser.add_argument('--spacing', type=float, default=3.0)
    parser.add_argument('--copy', action='store_true', help='USD Inherits 대신 독립 복사')
    parser.add_argument('--replicate-physics', action='store_true')
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 600
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
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
        from pxr import UsdGeom
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from isaacsim.core.cloner import Cloner, GridCloner
        from isaacsim.core.prims import XFormPrim
        if args.count < 1 or args.spacing <= 0:
            raise ValueError('count와 spacing은 양수여야 합니다')
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        cloner = GridCloner(spacing=args.spacing) if args.layout == 'grid' else Cloner()
        cloner.define_base_env('/World/envs')
        paths = cloner.generate_paths('/World/envs/env', args.count)
        UsdGeom.Xform.Define(world.stage, paths[0])
        source = DynamicCuboid(paths[0] + '/cube', name='source', size=0.5,
                               position=np.array([0., 0., 1.0]), color=np.array([0.2, 0.6, 1.0]))
        kwargs = {'source_prim_path': paths[0], 'prim_paths': paths,
                  'copy_from_source': args.copy, 'replicate_physics': args.replicate_physics}
        if args.layout == 'line':
            kwargs['positions'] = np.array([[i * args.spacing, 0., 0.] for i in range(args.count)])
        cloner.clone(**kwargs)
        cloner.filter_collisions('/physicsScene', '/World/collisionGroups', paths,
                                 global_paths=['/World/defaultGroundPlane'])
        # 5.1 설치본의 복수 prim 래퍼는 XFormPrim이다. 문서의 XFormPrimView는 이전 이름이다.
        boxes = XFormPrim('/World/envs/env_.*/cube', name='all_boxes')
        positions, orientations = boxes.get_world_poses()
        positions[:, 2] += 1.5
        boxes.set_world_poses(positions, orientations)
        world.reset()
        initial, _ = boxes.get_world_poses()
        final = initial.copy()
        scene_path = str(output / 'cloned_scene.usda')
        world.stage.GetRootLayer().Export(scene_path)
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            world.step(render=not args.headless)
            if app.is_running():
                final, _ = boxes.get_world_poses()
        records = {'paths': paths, 'initial_positions_m': initial.tolist(),
                   'final_positions_m': final.tolist(), 'copy_from_source': args.copy,
                   'replicate_physics': args.replicate_physics}
        (output / 'poses.json').write_text(json.dumps(records, indent=2))
        if app.is_running():
            world.stage.GetRootLayer().Export(scene_path)
        print(json.dumps(records, indent=2))
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
