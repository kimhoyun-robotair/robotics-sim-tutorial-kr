"""Open a local animated recorder lab or capture with the real SyntheticRecorder API."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Run a bounded native recorder capture instead of the interactive GUI lab")
    parser.add_argument("--frames", type=int, default=10)
    parser.add_argument("--steps", type=int, default=None, help="GUI update limit or headless capture timeout; omitted: GUI stays open, headless uses 10000")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.frames < 1 or (args.steps is not None and args.steps < 1):
        parser.error("frames and steps must be positive")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    task = None
    try:
        import asyncio
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        enable_extension("isaacsim.replicator.synthetic_recorder")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        import custom_writer
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
        from isaacsim.replicator.synthetic_recorder.synthetic_recorder import SyntheticRecorder
        # SyntheticRecorder는 설정에 따라 합성 데이터 기록을 시작하고 정지하는 녹화 API이다.
        from pxr import UsdGeom, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # 새 USD Stage를 열어 이 예제의 장면을 구성한다.
        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        stage.SetTimeCodesPerSecond(60)
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(120)
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        cube = UsdGeom.Cube.Define(stage, "/World/Carton")
        cube.CreateSizeAttr(1)
        cube.AddTranslateOp().Set((0, 0, 0))
        add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(700)
        # USD 카메라 Prim을 정의한다. 센서 이미지 출력은 별도의 render product나 Camera API로 연결한다.
        camera = UsdGeom.Camera.Define(stage, "/World/AnimatedCamera")
        translation = camera.AddTranslateOp()
        translation.Set((-1, 0, 7), 0)
        translation.Set((1, 0, 7), 120)
        config = {"writer_name":"BasicWriter", "num_frames":args.frames, "rt_subframes":4,
                  "control_timeline":True, "out_dir":"recording", "out_working_dir":str(output),
                  "basic_writer_params":{"rgb":True,"bounding_box_2d_tight":True,"semantic_segmentation":True},
                  "rp_data":[["/World/AnimatedCamera",512,512,"animated"]]}
        (output / "recorder_config.json").write_text(json.dumps(config,indent=2))
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "recorder_stage.usda"))
        if args.headless:
            recorder = SyntheticRecorder()
            for name, value in config.items():
                setattr(recorder, name, value)
            # SyntheticRecorder의 기록 시작·정지 처리를 비동기로 수행한다.
            task = asyncio.ensure_future(recorder.start_stop_async())
            for _ in range(args.steps if args.steps is not None else 10000):
                if task.done() or not app.is_running():
                    break
                app.update()
            if not task.done():
                raise RuntimeError("Native recorder exceeded --steps")
            task.result()
            if not list(output.rglob("*.png")):
                raise RuntimeError("Native recorder produced no PNG files")
        else:
            print(f"Load Writer > Config: {output / 'recorder_config.json'}")
            updates = 0
            while app.is_running() and (args.steps is None or updates < args.steps):
                app.update()
                updates += 1
    finally:
        try:
            if task is not None and not task.done():
                task.cancel()
        finally:
            # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
            app.close()


if __name__ == "__main__":
    main()
