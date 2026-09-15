"""Run genuine Isaac asset rules on authored defects, then verify focused repairs."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep-defects', action='store_true', help='Leave the defective stage open for native GUI validation')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Use a new output directory and finite headless frame limit')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension('isaacsim.asset.validation')
        from omni.asset_validator.core import ValidationEngine
        from isaacsim.asset.validation.physics_rules import RigidBodyHasMassAPI, InvisibleCollisionMeshHasPurposeGuide
        from pxr import Gf, UsdGeom, UsdPhysics
        stage = omni.usd.get_context().get_stage()
        root = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(root.GetPrim())
        cube = UsdGeom.Cube.Define(stage, '/World/DefectiveBody')
        cube.CreateSizeAttr(0.1)
        UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        mass = UsdPhysics.MassAPI.Apply(cube.GetPrim())
        mass.CreateMassAttr(0.0)
        mass.CreateDiagonalInertiaAttr(Gf.Vec3f(0, 0, 0))
        mass.CreatePrincipalAxesAttr(Gf.Quatf(2.0))
        cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
        engine = ValidationEngine(init_rules=False)
        engine.enable_rule(RigidBodyHasMassAPI)
        engine.enable_rule(InvisibleCollisionMeshHasPurposeGuide)
        before = [str(issue) for issue in engine.validate(stage).issues()]
        if not before:
            raise RuntimeError('The real validator did not report the intentionally authored defects')
        stage.GetRootLayer().Export(str(args.output / 'before.usda'))
        report = {'enabled_rules': ['RigidBodyHasMassAPI', 'InvisibleCollisionMeshHasPurposeGuide'], 'before': before}
        if not args.keep_defects:
            mass.GetMassAttr().Set(1.0)
            mass.GetDiagonalInertiaAttr().Set(Gf.Vec3f(1/600, 1/600, 1/600))
            mass.GetPrincipalAxesAttr().Set(Gf.Quatf(1.0))
            cube.CreatePurposeAttr(UsdGeom.Tokens.guide)
            after = [str(issue) for issue in engine.validate(stage).issues()]
            report['after'] = after
            if after:
                raise RuntimeError(f'Focused repairs still fail the enabled rules: {after}')
            stage.GetRootLayer().Export(str(args.output / 'after.usda'))
        (args.output / 'validation.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
