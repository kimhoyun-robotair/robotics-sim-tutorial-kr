"""Scene used for launch/attach debugging; close the GUI when finished."""
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--frames", type=int, default=240,
                    help="Default headless update count when --steps is omitted")
parser.add_argument("--steps", type=int, default=None,
                    help="Update limit; omitted keeps the GUI open until you close it")
parser.add_argument("--headless", action="store_true")
parser.add_argument("--height", type=float, default=1.0)
args = parser.parse_args()
if args.frames <= 0 or args.height <= 0:
    parser.error("frames and height must be positive")
if args.steps is not None and args.steps <= 0:
    parser.error("steps must be positive")
step_limit = args.steps if args.steps is not None else (args.frames if args.headless else None)
from isaacsim import SimulationApp
app = SimulationApp({"headless": args.headless})
try:
    import omni.usd
    from pxr import Gf, UsdGeom
    stage = omni.usd.get_context().get_stage()
    cube = UsdGeom.Cube.Define(stage, "/World/DebugCube")
    cube.CreateSizeAttr(0.2)
    position = Gf.Vec3d(0, 0, args.height)
    cube.AddTranslateOp().Set(position)
    print("breakpoint position:", position)
    frame = 0
    while app.is_running() and (step_limit is None or frame < step_limit):
        app.update()
        frame += 1
finally:
    app.close()
