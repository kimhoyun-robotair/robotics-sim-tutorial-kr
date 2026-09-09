"""작은 검사 물체의 RGB/분할 데이터셋. Isaac Sim 6.0.1 python.sh로 실행한다."""
import argparse
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--seed", type=int, default=601)
    parser.add_argument("--fixed", action="store_true", help="무작위 변화를 끄고 기준 영상을 만든다")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/dataset"))
    args = parser.parse_args()
    if not 1 <= args.frames <= 1000:
        parser.error("--frames는 1~1000이어야 한다")
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("새 출력 폴더를 지정한다. 이전 결과와 섞지 않는다")
    output.mkdir(parents=True, exist_ok=True)

    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless, "width": 640, "height": 480})
    writer = None
    product = None
    success = False
    try:
        import carb.settings
        import omni.replicator.core as rep
        import omni.usd
        from pxr import Gf, UsdGeom, UsdLux

        omni.usd.get_context().new_stage()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, "/World").GetPrim())
        rep.orchestrator.set_capture_on_play(False)
        carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
        carb.settings.get_settings().set("/exts/isaacsim.core.throttling/enable_async", False)
        rng = random.Random(args.seed)
        rep.set_global_seed(args.seed)

        # 바닥과 물체는 정적이다. 데이터 생성 중 접촉/관성의 영향을 먼저 배제한다.
        floor = UsdGeom.Cube.Define(stage, "/World/InspectionTable")
        floor.CreateSizeAttr(1.0)
        floor.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
        floor.AddScaleOp().Set(Gf.Vec3d(4, 4, 0.1))
        floor.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.35, 0.35)])
        target = UsdGeom.Cube.Define(stage, "/World/Part")
        target.CreateSizeAttr(0.4)
        translate = target.AddTranslateOp()
        rotate = target.AddRotateXYZOp()
        translate.Set(Gf.Vec3d(0, 0, 0.2))
        rotate.Set(Gf.Vec3f(0, 0, 0))
        target.CreateDisplayColorAttr([Gf.Vec3f(0.7, 0.12, 0.04)])
        rep.functional.modify.semantics(target.GetPrim(), {"class": "inspection_part"}, mode="add")
        light = UsdLux.DomeLight.Define(stage, "/World/InspectionLight")
        intensity = light.CreateIntensityAttr(1000.0)
        camera = rep.functional.create.camera(
            position=(1.7, 1.7, 1.4), look_at=(0, 0, 0.2),
            parent="/World", name="DatasetCamera",
        )
        # Replicator render_product 해상도는 (width, height)이다.
        # CameraSensor의 (height, width) 규칙과 혼동하지 않는다.
        product = rep.create.render_product(camera, (640, 480))
        for _ in range(30):
            app.update()
        backend = rep.backends.get("DiskBackend")
        backend.initialize(output_dir=str(output))
        writer = rep.writers.get("BasicWriter")
        writer.initialize(backend=backend, rgb=True, semantic_segmentation=True,
                          colorize_semantic_segmentation=True)
        writer.attach(product)
        records = []
        for frame in range(args.frames):
            if not app.is_running():
                raise RuntimeError("사용자가 앱을 닫아 데이터 생성이 중단되었다")
            x, y = (0.0, 0.0) if args.fixed else (rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35))
            yaw = 0.0 if args.fixed else rng.uniform(-45.0, 45.0)
            lux = 1000.0 if args.fixed else rng.uniform(700.0, 1300.0)
            translate.Set(Gf.Vec3d(x, y, 0.2))
            rotate.Set(Gf.Vec3f(0, 0, yaw))
            intensity.Set(lux)
            rep.orchestrator.step(rt_subframes=4, delta_time=0.0)
            records.append({"frame": frame, "position_m": [x, y, 0.2],
                            "yaw_deg": yaw, "light_intensity": lux})
        rep.orchestrator.wait_until_complete()
        if not stage.GetRootLayer().Export(str(output / "scene.usda")):
            raise RuntimeError("USD 장면 저장에 실패했다")
        (output / "manifest.json").write_text(json.dumps({
            "target_version": "6.0.1", "seed": args.seed, "fixed": args.fixed,
            "expected_frames": args.frames, "resolution_wh": [640, 480],
            "class_label": "inspection_part", "frames": records,
            "status": "CAPTURED_REQUIRES_INSPECTION",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"CAPTURED: {output}; scripts/inspect_dataset.py로 검사한다")
        success = True
    finally:
        try:
            if writer is not None:
                writer.detach()
            if product is not None:
                product.destroy()
        except Exception:
            import traceback
            traceback.print_exc()
            success = False
        finally:
            # fast_shutdown은 close가 반환하기 전에 프로세스를 끝낼 수 있다.
            app.close(exit_code=0 if success else 1)
        if not success:
            raise RuntimeError("데이터셋 생성 또는 종료 정리에 실패했다")


if __name__ == "__main__":
    main()
