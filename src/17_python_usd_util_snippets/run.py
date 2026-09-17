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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

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
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.viewports import set_camera_view
        # set_camera_view는 뷰포트 카메라를 eye 위치에 두고 target 지점을 바라보도록 설정한다.
        from pxr import Gf, UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.

        if not 1 <= args.count <= 100000:
            raise ValueError("--count must be 1..100000")
        if args.headless and args.mode == "debug":
            raise ValueError("DebugDraw needs a visible viewport; omit --headless")
        stage = omni.usd.get_context().get_stage()
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
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
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            prototype = UsdGeom.Cube.Define(stage, "/World/Instancer/Prototype")
            prototype.CreateSizeAttr(0.05)
            prototype.CreateDisplayColorAttr([Gf.Vec3f(0, 1, 1)])
            geometry.CreatePrototypesRel().SetTargets([prototype.GetPath()])
            geometry.CreateProtoIndicesAttr([0] * args.count)
            positions = geometry.CreatePositionsAttr(base)
        else:
            enable_extension("isaacsim.util.debug_draw")
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            from isaacsim.util.debug_draw import _debug_draw
            # _debug_draw는 뷰포트에 디버깅용 점과 선을 그리는 인터페이스를 제공한다.

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
            # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
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
            # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
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
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
