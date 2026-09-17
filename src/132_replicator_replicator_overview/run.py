"""Create a labeled stage and inspect Replicator RGB/semantic outputs."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--interactive", action="store_true", help="Legacy GUI flag; GUI stays open by default, and --steps still limits inspection")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.frames < 1 or (args.interactive and args.headless):
        parser.error("frames must be positive; interactive needs a GUI")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Choose a fresh --output: {output}")
    output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
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
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # 주변을 둘러싸는 DomeLight를 생성하여 장면의 환경 조명을 설정한다.
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(600)
        for name, x in [("Labeled", -1.5), ("Unlabeled", 1.5)]:
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube = UsdGeom.Cube.Define(stage, f"/World/{name}")
            cube.CreateSizeAttr(1)
            cube.AddTranslateOp().Set((x, 0, 0.5))
            if name == "Labeled":
                add_labels(cube.GetPrim(), labels=["carton"], instance_name="class")
        camera = rep.create.camera(position=(5, 6, 4), look_at=(0, 0, 0.5))
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        rp = rep.create.render_product(camera, (512, 512))
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        # 등록된 writer를 선택하여 이미지와 주석 데이터의 저장 형식을 정한다.
        writer = rep.writers.get("BasicWriter")
        writer.initialize(output_dir=str(output), rgb=True, semantic_segmentation=True,
                          colorize_semantic_segmentation=True, bounding_box_2d_tight=True)
        # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
        writer.attach(rp)
        for _ in range(args.frames):
            # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
            rep.orchestrator.step(delta_time=0.0, rt_subframes=4)
        # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
        rep.orchestrator.wait_until_complete()
        # writer와 render product의 연결을 해제한다.
        writer.detach()
        rp.destroy()
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "labels.usda"))
        print(f"Labeled=/World/Labeled; Unlabeled=/World/Unlabeled; inspect {output}")
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            inspection_updates += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
