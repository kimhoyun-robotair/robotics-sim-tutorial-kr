"""Profile real CPU work and Kit updates with named Tracy zones."""
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--frames", type=int, default=600,
                    help="Updates per profiling batch; also the default headless update limit")
parser.add_argument("--steps", type=int, default=None,
                    help="Total update limit; omitted repeats batches until you close the GUI")
parser.add_argument("--items", type=int, default=20000)
parser.add_argument("--headless", action="store_true")
args = parser.parse_args()
if args.frames <= 0 or args.items <= 0:
    parser.error("frames and items must be positive")
if args.steps is not None and args.steps <= 0:
    parser.error("steps must be positive")
step_limit = args.steps if args.steps is not None else (args.frames if args.headless else None)
from isaacsim import SimulationApp
app = SimulationApp({"headless": args.headless, "profiler_backend": ["tracy"]})
try:
    import math
    import carb.profiler
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension("omni.kit.profiler.tracy")

    @carb.profiler.profile
    def compute_values(count):
        return sum(math.sin(i * 0.001) for i in range(count))

    checksum = 0.0
    frame = 0
    batch_frames = 0
    while app.is_running() and (step_limit is None or frame < step_limit):
        carb.profiler.begin(1, "lesson_cpu_batch")
        try:
            checksum += compute_values(args.items)
        finally:
            carb.profiler.end(1)
        app.update()
        frame += 1
        batch_frames += 1
        if batch_frames == args.frames:
            print("frames", batch_frames, "items", args.items, "checksum", checksum)
            checksum = 0.0
            batch_frames = 0
    if batch_frames:
        print("frames", batch_frames, "items", args.items, "checksum", checksum)
finally:
    app.close()
