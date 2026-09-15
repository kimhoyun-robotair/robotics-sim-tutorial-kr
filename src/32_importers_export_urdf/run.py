"""Export one local robot in visual-only, visual+collision, and collision-only variants."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 1 or args.output.exists():
        parser.error('positive frames and a new output directory are required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, UsdGeom, UsdPhysics
        enable_extension('isaacsim.asset.exporter.urdf')
        from nvidia.srl.from_usd.to_urdf import UsdToUrdf
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(stage, '/Robot')
        stage.SetDefaultPrim(root.GetPrim())
        for name, position, mass, diagonal in [
            ('base', (0, 0, 0), 1.0, (0.0067, 0.0067, 0.0067)),
            ('link', (0, 0, 0.2), 0.5, (0.0034, 0.0034, 0.0034)),
        ]:
            body = UsdGeom.Xform.Define(stage, f'/Robot/{name}')
            body.AddTranslateOp().Set(Gf.Vec3d(*position))
            UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
            mass_api = UsdPhysics.MassAPI.Apply(body.GetPrim())
            mass_api.CreateMassAttr(mass)
            mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*diagonal))
            mass_api.CreatePrincipalAxesAttr(Gf.Quatf(1.0))
            mesh = UsdGeom.Cube.Define(stage, f'/Robot/{name}/shape')
            mesh.CreateSizeAttr(0.2)
            UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        joint = UsdPhysics.RevoluteJoint.Define(stage, '/Robot/hinge')
        joint.CreateBody0Rel().SetTargets(['/Robot/base'])
        joint.CreateBody1Rel().SetTargets(['/Robot/link'])
        joint.CreateAxisAttr('Y')
        joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.2))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
        joint.CreateLowerLimitAttr(-60.0)
        joint.CreateUpperLimitAttr(60.0)
        sphere = UsdGeom.Sphere.Define(stage, '/Robot/link/experiment_sphere')
        sphere.CreateRadiusAttr(0.03)
        sphere.AddTranslateOp().Set(Gf.Vec3d(0.13, 0, 0))
        summary = {}
        for mode in ('visual', 'both', 'collision'):
            if mode != 'visual':
                UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
            sphere.CreateVisibilityAttr(UsdGeom.Tokens.invisible if mode == 'collision' else UsdGeom.Tokens.inherited)
            destination = args.output / mode
            destination.mkdir()
            stage.GetRootLayer().Export(str(destination / 'source.usda'))
            target = destination / 'robot.urdf'
            UsdToUrdf(stage, root='/Robot').save_to_file(
                str(target), mesh_dir='meshes', mesh_path_prefix='./', use_uri_file_prefix=False,
            )
            tree = ElementTree.parse(target)
            summary[mode] = {key: len(tree.findall(f'.//{key}')) for key in ('link', 'joint', 'visual', 'collision')}
        (args.output / 'counts.json').write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
