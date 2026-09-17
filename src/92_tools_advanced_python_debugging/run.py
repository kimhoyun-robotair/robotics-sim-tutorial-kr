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
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({"headless": args.headless})
try:
    import omni.usd
    # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
    # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
    from pxr import Gf, UsdGeom
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
    # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
    stage = omni.usd.get_context().get_stage()
    # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
    cube = UsdGeom.Cube.Define(stage, "/World/DebugCube")
    cube.CreateSizeAttr(0.2)
    position = Gf.Vec3d(0, 0, args.height)
    cube.AddTranslateOp().Set(position)
    print("breakpoint position:", position)
    frame = 0
    while app.is_running() and (step_limit is None or frame < step_limit):
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        frame += 1
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
