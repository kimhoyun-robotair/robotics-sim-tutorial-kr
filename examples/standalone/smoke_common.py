"""Shared reporting for the Isaac Sim 5.1 runtime exercises (stdlib only)."""

import argparse
import contextlib
import json
import time
import traceback
from pathlib import Path


def arguments(name):
    parser = argparse.ArgumentParser(description=f"Isaac Sim 5.1: {name}")
    parser.add_argument("--gui", action="store_true", help="Show the Isaac Sim window")
    parser.add_argument("--output-dir", type=Path, default=Path("results") / name)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    return args


def require(condition, message):
    # Unlike assert, this check remains active when Python runs with -O.
    if not condition:
        raise RuntimeError(message)


@contextlib.contextmanager
def application(args, name):
    """Create Kit before runtime imports; preserve a report even on failure."""
    report = {"test": name, "status": "RUNNING", "metrics": {}}
    path = args.output_dir / "result.json"

    def save():
        path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    save()
    app = None
    started = time.monotonic()
    try:
        from isaacsim import SimulationApp

        app = SimulationApp(
            {"headless": not args.gui, "width": 640, "height": 480,
             "renderer": "RayTracedLighting", "multi_gpu": False}
        )
        yield app, report["metrics"]
        report["status"] = "PASS"
    except BaseException as exc:
        report["status"] = "FAIL"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        try:
            if app is not None:
                app.close()
        except BaseException as exc:
            report["status"] = "FAIL"
            report["close_error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            report["elapsed_seconds"] = round(time.monotonic() - started, 3)
            save()
            print(f"{report['status']}: {path}", flush=True)


def add_light(stage):
    """Explicit light avoids dependence on a viewport's default illumination."""
    from pxr import UsdLux

    light = UsdLux.DomeLight.Define(stage, "/World/Light")
    light.CreateIntensityAttr(700.0)
