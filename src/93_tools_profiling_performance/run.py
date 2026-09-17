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
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({"headless": args.headless, "profiler_backend": ["tracy"]})
try:
    import math
    import carb.profiler
    # carb.profiler는 코드 구간의 실행 시간을 프로파일러에 기록하기 위한 API이다.
    from isaacsim.core.utils.extensions import enable_extension
    # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
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
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
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
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
