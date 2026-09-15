"""Use the supported OBJ-to-USD converter; the included OBJ is an original fixture."""
import argparse
import asyncio
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--obj', type=Path, default=Path(__file__).parent / 'sample.obj')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless preview updates; does not limit GUI lifetime')
    parser.add_argument('--steps', type=int, default=None, help='Preview updates after conversion; omitted keeps GUI open')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = args.frames
    if args.steps is not None and args.steps < 1:
        parser.error('--steps must be positive')
    if not args.obj.is_file() or args.frames < 1 or args.timeout <= 0 or args.output.exists():
        parser.error('Existing OBJ, positive frames/timeout, and a new output directory are required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        enable_extension('omni.kit.asset_converter')
        import omni.kit.asset_converter
        from pxr import UsdGeom
        converted = args.output.resolve() / 'converted.usd'
        context = omni.kit.asset_converter.AssetConverterContext()
        task = omni.kit.asset_converter.get_instance().create_converter_task(
            str(args.obj.resolve()), str(converted), None, context,
        )
        future = asyncio.ensure_future(task.wait_until_finished())
        deadline = time.monotonic() + args.timeout
        while not future.done():
            if time.monotonic() > deadline or not app.is_running():
                future.cancel()
                raise TimeoutError('OBJ conversion did not complete within the requested timeout')
            app.update()
        if not future.result():
            raise RuntimeError(f'OBJ conversion failed: {task.get_error_message()}')
        add_reference_to_stage(str(converted), '/World/Imported')
        stage = get_current_stage()
        meshes = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise RuntimeError('Conversion produced no meshes')
        print('Converted mesh prims:', meshes)
        step = 0
        while app.is_running() and (args.steps is None or step < args.steps):
            app.update()
            step += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
