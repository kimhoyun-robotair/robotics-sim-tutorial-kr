"""Merge two authored meshes with distinct materials through the native merge command."""
import argparse
import json
import traceback
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clear-transform', action='store_true')
    parser.add_argument('--keep-sources', action='store_true')
    parser.add_argument('--prepare-only', action='store_true', help='Leave the source meshes for the GUI exercise')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=240, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Use a new output directory and a finite headless frame limit')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        import omni.kit.commands
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, Sdf, UsdGeom, UsdShade
        if not enable_extension('isaacsim.util.merge_mesh'):
            raise RuntimeError('Could not enable isaacsim.util.merge_mesh')
        from isaacsim.util.merge_mesh.commands import MergeMeshesCommand
        omni.kit.commands.register(MergeMeshesCommand)
        stage = omni.usd.get_context().get_stage()
        points = [(-.1,-.1,-.1),(.1,-.1,-.1),(.1,.1,-.1),(-.1,.1,-.1),(-.1,-.1,.1),(.1,-.1,.1),(.1,.1,.1),(-.1,.1,.1)]
        faces = [0,3,2,1, 4,5,6,7, 0,1,5,4, 1,2,6,5, 2,3,7,6, 3,0,4,7]
        paths = []
        for i, color in enumerate(((.8,.1,.1),(.1,.2,.8))):
            source = UsdGeom.Xform.Define(stage, f'/World/Source_{i}')
            source.AddTranslateOp().Set(Gf.Vec3d(1+i*.3, 0, .2))
            mesh = UsdGeom.Mesh.Define(stage, f'/World/Source_{i}/Geometry')
            mesh.CreatePointsAttr(points)
            mesh.CreateFaceVertexCountsAttr([4]*6)
            mesh.CreateFaceVertexIndicesAttr(faces)
            mesh.CreateSubdivisionSchemeAttr('none')
            material = UsdShade.Material.Define(stage, f'/World/Looks/Material_{i}')
            shader = UsdShade.Shader.Define(stage, f'/World/Looks/Material_{i}/Shader')
            shader.CreateIdAttr('UsdPreviewSurface')
            shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
            paths.append(str(source.GetPath()))
        omni.usd.get_context().get_selection().set_selected_prim_paths(paths, True)
        if not args.prepare_only:
            ok, merged_path = omni.kit.commands.execute(
                'isaacsim.util.merge_mesh.commands.MergeMeshes', source=paths, clear_transform=args.clear_transform,
                deactivate_source=not args.keep_sources, combine_materials=True, materials_destination='/World/MergedLooks',
            )
            if not ok:
                raise RuntimeError('Native mesh merge failed')
            merged = UsdGeom.Mesh(stage.GetPrimAtPath(merged_path))
            if not merged:
                raise RuntimeError('The merge command did not produce a Mesh prim')
            report = {'merged_path': merged_path, 'faces': len(merged.GetFaceVertexCountsAttr().Get()),
                      'subsets': len(UsdGeom.Subset.GetAllGeomSubsets(UsdGeom.Imageable(merged.GetPrim()))),
                      'sources_active': [stage.GetPrimAtPath(p).IsActive() for p in paths]}
            if report['faces'] != 12 or report['subsets'] != 2:
                raise RuntimeError(f'Merged topology/material partition mismatch: {report}')
            if report['sources_active'] != [args.keep_sources] * len(paths):
                raise RuntimeError(f'Source activation state mismatch: {report}')
            (args.output / 'report.json').write_text(json.dumps(report, indent=2))
            print(report)
        stage.GetRootLayer().Export(str(args.output / 'scene.usda'))
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            app.update()
            count += 1
    except Exception:
        traceback.print_exc()
        raise
    finally:
        app.close()


if __name__ == '__main__':
    main()
