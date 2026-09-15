"""Convert a local MJCF pendulum or installed humanoid/ant, then inspect real USD joints."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=('local', 'ant', 'humanoid'), default='local')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 300 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.output.exists():
        parser.error('a new output directory is required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.kit.commands
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        from isaacsim.core.utils.stage import get_current_stage
        from pxr import UsdPhysics
        enable_extension('isaacsim.asset.importer.mjcf')
        world = World(stage_units_in_meters=1.0, physics_dt=0.01, rendering_dt=0.01)
        world.scene.add_default_ground_plane()
        source = Path(__file__).parent / 'pendulum.xml'
        if args.model != 'local':
            source = Path(get_extension_path_from_name('isaacsim.asset.importer.mjcf')) / 'data/mjcf' / f'nv_{args.model}.xml'
        ok, config = omni.kit.commands.execute('MJCFCreateImportConfig')
        if not ok:
            raise RuntimeError('MJCF configuration could not be created')
        config.set_fix_base(args.model == 'local')
        config.set_make_default_prim(False)
        ok, result = omni.kit.commands.execute(
            'MJCFCreateAsset', mjcf_path=str(source.resolve()), import_config=config, prim_path='/World/Imported',
        )
        stage = get_current_stage()
        if not ok or not stage.GetPrimAtPath('/World/Imported').IsValid():
            raise RuntimeError(f'MJCF import failed: {result}')
        joints = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]
        if not joints:
            raise RuntimeError('Imported model contains no USD physics joint')
        stage.GetRootLayer().Export(str(args.output / 'imported.usda'))
        world.reset()
        stage_meters_per_unit = stage.GetMetadata("metersPerUnit")
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            world.step(render=not args.headless)
            step += 1
        report = {'source': str(source), 'joints': joints, 'stage_meters_per_unit': stage_meters_per_unit}
        (args.output / 'report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        app.close()


if __name__ == '__main__':
    main()
