"""Keep this package's native Isaac Sim example open after successful finite work."""

import argparse
from pathlib import Path
import runpy
import signal
import sys


def run_native(script: Path, native_args: list[str], *, headless: bool, steps: int | None) -> None:
    import isaacsim

    original_app = isaacsim.SimulationApp
    applications = []

    class TutorialApp(original_app):
        def __init__(self, launch_config=None, *args, **kwargs):
            self._tutorial_close_requested = False
            config = dict(launch_config or {})
            config["headless"] = headless
            super().__init__(config, *args, **kwargs)
            applications.append(self)

        def close(self, *args, **kwargs):
            # Native examples close before returning; this runner owns the real cleanup.
            self._tutorial_close_requested = True

        def is_running(self):
            return not self._tutorial_close_requested and super().is_running()

    previous_argv = sys.argv
    previous_path = sys.path[:]
    previous_sigint = signal.getsignal(signal.SIGINT)
    isaacsim.SimulationApp = TutorialApp
    sys.argv = [str(script), *native_args]
    sys.path.insert(0, str(script.parent))
    try:
        runpy.run_path(str(script), run_name="__main__")
        signal.signal(signal.SIGINT, previous_sigint)
        if not applications:
            raise RuntimeError("Native example returned without creating a SimulationApp")
        app = applications[-1]
        app._tutorial_close_requested = False
        # The native pipeline has flushed writers and destroyed its render products.
        if not headless:
            print("Work completed. Inspect the GUI; close the window or press Ctrl+C to exit.", flush=True)
            updates = 0
            while app.is_running() and (steps is None or updates < steps):
                app.update()
                updates += 1
    finally:
        isaacsim.SimulationApp = original_app
        sys.argv = previous_argv
        sys.path[:] = previous_path
        signal.signal(signal.SIGINT, previous_sigint)
        for app in reversed(applications):
            original_app.close(app)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, help="GUI updates after finite work; omit to wait for window close")
    parser.add_argument("script", type=Path)
    parser.add_argument("native_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be a positive integer")
    run_native(args.script.resolve(), args.native_args, headless=args.headless, steps=args.steps)


if __name__ == "__main__":
    main()
