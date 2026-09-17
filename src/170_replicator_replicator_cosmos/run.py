"""Capture synchronized CosmosWriter clips from the official warehouse/Carter scene."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--clips", type=int, default=2)
    parser.add_argument("--frames", type=int, default=10, help="Frames per clip")
    parser.add_argument("--capture-interval", type=int, default=2)
    parser.add_argument("--start-delay", type=float, default=0.1)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--canny-low", type=int, default=10)
    parser.add_argument("--canny-high", type=int, default=100)
    parser.add_argument("--semantic-mapping", type=Path, help="Optional semantic class to RGBA JSON mapping")
    parser.add_argument("--target", type=float, nargs=3, default=(3, 3, 0), metavar=("X", "Y", "Z"))
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output")
    parser.add_argument("--steps", type=int, default=None,
                        help="GUI app updates after generation; omitted: keep GUI open; headless: no inspection")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if min(args.clips, args.frames, args.capture_interval, args.width, args.height) < 1:
        parser.error("Clip/frame/interval/resolution values must be positive")
    if args.start_delay < 0 or not 0 <= args.canny_low <= args.canny_high <= 255:
        parser.error("Nonnegative delay and 0 <= Canny low <= high <= 255 are required")
    mapping = json.loads(args.semantic_mapping.read_text(encoding="utf-8")) if args.semantic_mapping else None
    if mapping is not None and (not isinstance(mapping, dict) or not mapping or any(
        not isinstance(key, str) or not isinstance(color, list) or len(color) != 4
        or any(not isinstance(v, int) or not 0 <= v <= 255 for v in color)
        for key, color in mapping.items()
    )):
        parser.error("Semantic mapping must be a nonempty object of class names to four integer RGBA components")
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output exists; choose a new path: {output}")

    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        # carb는 Kit 기반 실행 환경의 설정·로그 등 공통 기능을 제공하는 Carbonite 바인딩이다.
        import omni.replicator.core as rep
        # omni.replicator.core는 장면 무작위화와 합성 데이터 생성을 위한 API이다.
        # render product는 카메라의 렌더링 출력이며, annotator는 데이터를 추출하고 writer는 결과를 저장한다.
        import omni.timeline
        # omni.timeline은 시뮬레이션 시간과 재생·일시정지·정지를 제어하는 API이다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from pxr import UsdGeom
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.

        assets = get_assets_root_path()
        if not assets:
            raise RuntimeError("Isaac Sim 5.1 asset root is unavailable")
        context = omni.usd.get_context()
        scene = assets + "/Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd"
        if not context.open_stage(scene):
            raise RuntimeError(f"Cannot open warehouse: {scene}")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        stage = context.get_stage()
        carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)
        carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)
        # 타임라인 재생에 따른 자동 캡처 여부를 설정한다. False이면 아래의 명시적 캡처 호출로 제어한다.
        rep.orchestrator.set_capture_on_play(False)
        robot_path = "/NavWorld/CarterNav"
        robot = add_reference_to_stage(
            usd_path=assets + "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd",
            prim_path=robot_path,
        )
        app.update()
        target = stage.GetPrimAtPath(robot_path + "/targetXform")
        camera = stage.GetPrimAtPath(robot_path + "/chassis_link/sensors/front_hawk/left/camera_left")
        if not target.IsValid() or not camera.IsValid():
            raise RuntimeError("Carter navigation target or front camera is missing; verify 5.1 sample assets")
        for prim, position in ((robot, (-6, 4, 0)), (target, args.target)):
            attr = prim.GetAttribute("xformOp:translate")
            if not attr:
                # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
                attr = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
            attr.Set(tuple(position))
        timeline = omni.timeline.get_timeline_interface()
        timeline.set_end_time(max(timeline.get_end_time(), 1000000.0))
        timeline.play()
        delay_end = timeline.get_current_time() + args.start_delay
        for _ in range(1000):
            if timeline.get_current_time() >= delay_end:
                break
            app.update()
        else:
            raise RuntimeError("Timeline failed to reach the requested start delay in 1000 updates")

        output.mkdir(parents=True, exist_ok=False)
        # 카메라와 해상도를 연결한 render product를 만든다. 이후 annotator나 writer를 여기에 연결한다.
        render_product = rep.create.render_product(camera.GetPath(), (args.width, args.height))
        # 등록된 writer를 이름으로 선택한다. initialize로 출력 설정을 지정한 뒤 render product에 연결한다.
        writer = rep.WriterRegistry.get("CosmosWriter")
        writer.initialize(output_dir=str(output), use_instance_id=True, segmentation_mapping=mapping,
                          canny_threshold_low=args.canny_low, canny_threshold_high=args.canny_high)
        # writer를 render product에 연결하여 캡처한 데이터가 writer로 전달되게 한다.
        writer.attach(render_product)
        observations = []
        try:
            for clip in range(args.clips):
                for frame in range(args.frames):
                    if not app.is_running():
                        raise RuntimeError("Application closed before capture completed")
                    # Replicator의 캡처를 한 번 진행한다. rt_subframes는 캡처를 위한 렌더링 누적 프레임 수이다.
                    rep.orchestrator.step(pause_timeline=False)
                    observations.append({"clip": clip, "frame": frame, "timeline_seconds": timeline.get_current_time()})
                    if frame < args.frames - 1:
                        for _ in range(args.capture_interval - 1):
                            app.update()
                # 예약된 합성 데이터 처리와 writer의 저장 작업이 끝날 때까지 기다린다.
                rep.orchestrator.wait_until_complete()
                writer.next_clip()
            rep.orchestrator.wait_until_complete()
        finally:
            # writer와 render product의 연결을 해제한다.
            writer.detach()
            render_product.destroy()
            timeline.pause()
        (output / "capture_times.json").write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
        missing = [str(output / f"clip_{clip:04}" / f"{modality}.mp4")
                   for clip in range(args.clips) for modality in ("rgb", "depth", "segmentation", "shaded_seg", "edges")
                   if not (output / f"clip_{clip:04}" / f"{modality}.mp4").is_file()]
        if missing:
            raise RuntimeError(f"Video encoding did not produce expected files: {missing}")
        print(f"Captured {args.clips} clips × {args.frames} frames into {output}")
        inspection_updates = 0
        while not args.headless and app.is_running() and (args.steps is None or inspection_updates < args.steps):
            app.update()
            inspection_updates += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
