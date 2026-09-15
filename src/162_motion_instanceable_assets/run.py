"""Xform 참조 계층으로 동일 geometry를 USD instance로 공유합니다."""
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
    parser.add_argument('--count', type=int, default=4)
    parser.add_argument('--no-instancing', action='store_true')
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
        from pxr import Usd, UsdGeom, Gf
        import omni.usd
        if args.count < 1:
            raise ValueError('--count must be positive')
        # 두 파일을 함께 이동하면 상대 참조가 유지된다.
        mesh_stage = Usd.Stage.CreateNew(str(output / 'meshes.usda'))
        UsdGeom.SetStageMetersPerUnit(mesh_stage, 1.0)
        UsdGeom.SetStageUpAxis(mesh_stage, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(mesh_stage, '/Geometry')
        mesh_stage.SetDefaultPrim(root.GetPrim())
        UsdGeom.Cube.Define(mesh_stage, '/Geometry/Cube').GetSizeAttr().Set(0.5)
        mesh_stage.GetRootLayer().Save()
        stage = Usd.Stage.CreateNew(str(output / 'instances.usda'))
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        world = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(world.GetPrim())
        rows = []
        for i in range(args.count):
            link = UsdGeom.Xform.Define(stage, f'/World/Robot_{i}/Link')
            link.AddTranslateOp().Set(Gf.Vec3d(i * 0.8, 0., 0.25))
            geometry = UsdGeom.Xform.Define(stage, f'/World/Robot_{i}/Link/Geometry').GetPrim()
            geometry.GetReferences().AddReference('./meshes.usda', '/Geometry')
            geometry.SetInstanceable(not args.no_instancing)
            rows.append({'path': str(geometry.GetPath()), 'is_instance': geometry.IsInstance(),
                         'prototype': str(geometry.GetPrototype().GetPath()) if geometry.IsInstance() else None,
                         'child_is_instance_proxy': stage.GetPrimAtPath(str(geometry.GetPath()) + '/Cube').IsInstanceProxy()})
        stage.GetRootLayer().Save()
        omni.usd.get_context().open_stage(str(output / 'instances.usda'))
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            app.update()
        (output / 'instances.json').write_text(json.dumps(rows, indent=2))
        print(json.dumps(rows, indent=2))
        print('Output:', output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
