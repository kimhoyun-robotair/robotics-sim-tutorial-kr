import argparse
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Util Snippets")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: GUI stays open (headless: 120)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument(
        "--mode", choices=["points", "instancer", "debug"], default="points"
    )
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--zero-delay", action="store_true")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 120
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp

    app = SimulationApp(
        {
            "headless": args.headless,
            "extra_args": [
                "--/app/hydraEngine/waitIdle=1",
                "--/app/updateOrder/checkForHydraRenderComplete=1000",
                "--/exts/isaacsim.ros2.bridge/publish_multithreading_disabled=1",
            ]
            if args.zero_delay
            else [],
        }
    )
    try:
        import math
        import random
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, UsdGeom, UsdLux

        if not 1 <= args.count <= 100000:
            raise ValueError("--count must be 1..100000")
        if args.headless and args.mode == "debug":
            raise ValueError("DebugDraw needs a visible viewport; omit --headless")
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        set_camera_view(eye=[5, 5, 4], target=[0, 0, 1])
        rng = random.Random(7)
        base = [
            (rng.uniform(-2, 2), rng.uniform(-1, 1), rng.uniform(0.2, 2))
            for _ in range(args.count)
        ]
        samples = [Gf.Vec3f(*point) for point in base]
        draw = None
        if args.mode == "points":
            geometry = UsdGeom.Points.Define(stage, "/World/Points")
            positions = geometry.CreatePointsAttr(base)
            geometry.CreateWidthsAttr([0.05] * args.count)
            geometry.CreateDisplayColorPrimvar("constant").Set([Gf.Vec3f(1, 0, 1)])
        elif args.mode == "instancer":
            geometry = UsdGeom.PointInstancer.Define(stage, "/World/Instancer")
            prototype = UsdGeom.Cube.Define(stage, "/World/Instancer/Prototype")
            prototype.CreateSizeAttr(0.05)
            prototype.CreateDisplayColorAttr([Gf.Vec3f(0, 1, 1)])
            geometry.CreatePrototypesRel().SetTargets([prototype.GetPath()])
            geometry.CreateProtoIndicesAttr([0] * args.count)
            positions = geometry.CreatePositionsAttr(base)
        else:
            enable_extension("isaacsim.util.debug_draw")
            app.update()
            from isaacsim.util.debug_draw import _debug_draw

            draw = _debug_draw.acquire_debug_draw_interface()
        def render_frame(frame):
            samples = [
                Gf.Vec3f(x, y, z + 0.2 * math.sin(frame / 15 + x))
                for x, y, z in base
            ]
            if draw:
                draw.clear_points()
                draw.draw_points(
                    [tuple(p) for p in samples],
                    [(1, 0.3, 0, 1)] * args.count,
                    [5.0] * args.count,
                )
            else:
                positions.Set(samples)
            app.update()
            return samples

        try:
            for frame in range(sample_steps):
                if not app.is_running():
                    return
                samples = render_frame(frame)
            if not app.is_running():
                return
            camera = UsdGeom.Camera.Define(stage, "/World/CalibrationCamera")
            camera.CreateFocalLengthAttr(35.0)
            camera.CreateHorizontalApertureAttr(36.0)
            camera.CreateVerticalApertureAttr(24.0)
            width, height = 960, 640
            focal = float(camera.GetFocalLengthAttr().Get())
            ha = float(camera.GetHorizontalApertureAttr().Get())
            va = float(camera.GetVerticalApertureAttr().Get())
            report = {
                "mode": args.mode,
                "point_count": args.count,
                "focal_x_px": width * focal / ha,
                "focal_y_px": height * focal / va,
                "principal_point_px": [width / 2, height / 2],
                "horizontal_fov_rad": 2 * math.atan(ha / (2 * focal)),
                "zero_delay_requested": args.zero_delay,
                "final_positions": [list(p) for p in samples],
            }
            (output / "rendering.json").write_text(json.dumps(report, indent=2))
            stage.GetRootLayer().Export(str(output / "geometry.usda"))
            print(
                {
                    key: value
                    for key, value in report.items()
                    if key != "final_positions"
                }
            )
            print(f"Outputs: {output.resolve()}")
            frame = sample_steps
            while args.steps is None and not args.headless and app.is_running():
                render_frame(frame)
                frame += 1
        finally:
            if draw and app.is_running():
                draw.clear_points()
    finally:
        app.close()


if __name__ == "__main__":
    main()
