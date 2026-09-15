import argparse
import asyncio
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Convert the package's local OBJ mesh to USD"
    )
    parser.add_argument(
        "--input", type=Path, default=Path(__file__).with_name("tetrahedron.obj")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Positive update limit; omitted: GUI stays open (headless: 3600)",
    )
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (3600 if args.headless else None)
    if not args.input.is_file():
        parser.error("--input must be an existing mesh file")
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "convert-%Y%m%d-%H%M%S-%f.usda"
    )
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    task = None
    try:
        from isaacsim.core.utils.extensions import enable_extension

        enable_extension("omni.kit.asset_converter")
        app.update()
        import omni.kit.asset_converter

        async def convert():
            context = omni.kit.asset_converter.AssetConverterContext()
            context.use_meter_as_world_unit = True
            conversion = omni.kit.asset_converter.get_instance().create_converter_task(
                str(args.input.resolve()),
                str(output.resolve()),
                lambda current, total: None,
                context,
            )
            if not await conversion.wait_until_finished():
                raise RuntimeError(conversion.get_detailed_error())

        task = asyncio.ensure_future(convert())
        updates = 0
        while app.is_running() and not task.done() and (step_limit is None or updates < step_limit):
            app.update()
            updates += 1
        if not app.is_running():
            return
        if not task.done():
            raise TimeoutError("Asset conversion exceeded --steps application updates")
        task.result()
        if not output.is_file():
            raise RuntimeError(
                "Converter completed without producing the requested USD"
            )
        print(output.resolve())
        while args.steps is None and not args.headless and app.is_running():
            app.update()
    finally:
        if task is not None and not task.done():
            task.cancel()
        app.close()


if __name__ == "__main__":
    main()
