"""Observe UR10 flip/pallet contact events and capture native SDG scenarios."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bins", type=int, default=2)
    parser.add_argument("--steps", type=int, default=None, help="Maximum app updates during generation; omitted: GUI stays open, headless uses 60000")
    parser.add_argument("--flip-frames", type=int, default=4)
    parser.add_argument("--pallet-frames", type=int, default=16)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (60000 if args.headless else None)
    if not 1 <= args.bins <= 36 or min(args.flip_frames, args.pallet_frames) < 1:
        parser.error("bins must be 1..36; steps and frame counts must be positive")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a new --output; already exists: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    task = None
    demo = None
    try:
        import asyncio
        import random
        import omni.kit.app
        import omni.replicator.core as rep
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension("isaacsim.examples.interactive")
        app.update()
        from isaacsim.examples.interactive.ur10_palletizing.ur10_palletizing import BinStacking
        from palletizing import PalletizingSDGDemo

        async def run():
            nonlocal demo
            random.seed(42)
            rep.set_global_seed(42)
            sample = BinStacking()
            await sample.load_world_async()
            await sample.on_event_async()
            for _ in range(3):
                await omni.kit.app.get_app().next_update_async()
            demo = PalletizingSDGDemo(output)
            demo.BIN_FLIP_SCENARIO_FRAMES = args.flip_frames
            demo.PALLET_SCENARIO_FRAMES = args.pallet_frames
            demo.start(args.bins)
            if not demo.is_running():
                raise RuntimeError("UR10 stage or bin_0 did not initialize")
            while demo.is_running():
                if demo._capture_task is not None and demo._capture_task.done():
                    demo._capture_task.result()
                await omni.kit.app.get_app().next_update_async()
            await rep.orchestrator.wait_until_complete_async()

        task = asyncio.ensure_future(run())
        updates = 0
        while app.is_running() and not task.done() and (step_limit is None or updates < step_limit):
            app.update()
            updates += 1
        if not app.is_running():
            return
        if not task.done():
            raise RuntimeError("UR10 run exceeded --steps before requested bins were captured")
        task.result()
        captures = list(output.glob("writer_bin_*"))
        if len(captures) != args.bins or not list(output.rglob("*.png")):
            raise RuntimeError(f"Missing pallet outputs: {output}")
        print(f"Pallet capture folders: {len(captures)}; actual PNGs: {len(list(output.rglob('*.png')))}")
        while args.steps is None and not args.headless and app.is_running():
            app.update()
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
            if demo is not None:
                if demo._capture_task is not None and not demo._capture_task.done():
                    demo._capture_task.cancel()
                demo.clear()
        finally:
            app.close()


if __name__ == "__main__":
    main()
