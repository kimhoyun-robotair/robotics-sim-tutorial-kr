"""Isaac Sim 5.1 Script Editor: 빈 장면에서 RGB/깊이/클래스 10장을 저장한다."""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

import carb.settings
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.utils.semantics import add_labels
from pxr import Gf, UsdGeom, UsdLux


async def capture_dataset():
    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None or not stage.GetRootLayer().anonymous:
        raise RuntimeError("기존 작업을 저장하고 File > New로 새 장면을 만든다.")
    if not omni.timeline.get_timeline_interface().is_stopped():
        raise RuntimeError("먼저 Stop을 누른다.")
    existing = [
        str(prim.GetPath()) for prim in stage.Traverse()
        if str(prim.GetPath()) != "/World"
        and not str(prim.GetPath()).startswith("/OmniverseKit_")
    ]
    if existing:
        raise RuntimeError(f"빈 장면이 필요하다: {existing[:5]}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output = Path.home() / "isaacsim-course" / "outputs" / ("sdg_" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    settings = carb.settings.get_settings()
    previous_dlss = settings.get("/rtx/post/dlss/execMode")
    previous_capture = settings.get("/omni/replicator/captureOnPlay")
    writer = None
    render_product = None
    completed = 0
    try:
        rep.orchestrator.set_capture_on_play(False)
        settings.set("/rtx/post/dlss/execMode", 2)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        root = UsdGeom.Xform.Define(stage, "/World")
        stage.SetDefaultPrim(root.GetPrim())
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(700.0)

        # 물리 시뮬레이션 없이 정지한 물체의 위치를 바꿔 가며 촬영한다.
        ground = UsdGeom.Cube.Define(stage, "/World/Ground")
        ground.CreateSizeAttr(1.0)
        ground.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.05))
        ground.AddScaleOp().Set(Gf.Vec3f(4.0, 4.0, 0.1))
        ground.CreateDisplayColorAttr([Gf.Vec3f(0.25, 0.25, 0.25)])
        cube = UsdGeom.Cube.Define(stage, "/World/Cube")
        cube.CreateSizeAttr(0.4)
        translation = cube.AddTranslateOp()
        translation.Set(Gf.Vec3d(0.0, 0.0, 0.2))
        cube.CreateDisplayColorAttr([Gf.Vec3f(0.15, 0.65, 0.95)])
        add_labels(cube.GetPrim(), labels=["course_cube"], instance_name="class")

        camera = rep.create.camera(position=(2.0, 2.0, 1.5), look_at=(0.0, 0.0, 0.2))
        render_product = rep.create.render_product(camera, (640, 480))
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(
            output_dir=str(output), rgb=True, distance_to_camera=True,
            semantic_segmentation=True,
        )
        writer.attach([render_product])
        for index in range(10):
            if context.get_stage() != stage:
                raise RuntimeError("촬영 중 Stage가 바뀌었다. 새 장면에서 다시 실행한다.")
            translation.Set(Gf.Vec3d(-0.45 + 0.1 * index, 0.0, 0.2))
            await rep.orchestrator.step_async(rt_subframes=4, delta_time=0.0)
            completed += 1
        await rep.orchestrator.wait_until_complete_async()
        print(f"[course] capture requests complete: {completed}, output: {output}")
    finally:
        if writer is not None:
            writer.detach()
        if render_product is not None:
            render_product.destroy()
        try:
            await rep.orchestrator.wait_until_complete_async()
        finally:
            if previous_dlss is not None:
                settings.set("/rtx/post/dlss/execMode", previous_dlss)
            if previous_capture is not None:
                rep.orchestrator.set_capture_on_play(bool(previous_capture))
            manifest = {
                "isaac_sim": "5.1.0", "requested_frames": 10,
                "completed_capture_requests": completed,
                "resolution": [640, 480], "class": "course_cube",
                "depth_kind": "distance_to_camera", "depth_unit": "meter",
                "rt_subframes": 4, "dlss_quality_mode": 2,
                "validated_images": False,
            }
            (output / "manifest.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )


old_task = globals().get("course_capture_task")
if old_task is not None and not old_task.done():
    raise RuntimeError("촬영이 진행 중이다. 완료 후 새 장면에서 다시 실행한다.")
course_capture_task = asyncio.ensure_future(capture_dataset())


def report_capture_result(task):
    if task.cancelled():
        print("[course] capture cancelled; inspect partial output")
    elif task.exception() is not None:
        print(f"[course] capture failed: {task.exception()}")


course_capture_task.add_done_callback(report_capture_result)
