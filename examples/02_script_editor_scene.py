"""Run inside Isaac Sim 6.0.1 Script Editor on a stopped, Z-up, metre stage."""

import asyncio
import math

import omni.kit.app
import omni.timeline
import omni.usd
from pxr import Gf, UsdGeom, UsdLux

ROOT_PATH = "/World/ScriptEditorDemo"
OWNER = "tutorial.script_editor"


async def build_scene():
    context = omni.usd.get_context()
    stage = context.get_stage()
    if stage is None:
        raise RuntimeError("File > New로 빈 Stage를 먼저 만든다.")
    if not omni.timeline.get_timeline_interface().is_stopped():
        raise RuntimeError("Stop을 누른 뒤 실행한다.")
    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z or not math.isclose(UsdGeom.GetStageMetersPerUnit(stage), 1.0):
        raise RuntimeError("이 실습은 Z-up, metersPerUnit=1인 Stage가 필요하다.")
    existing = stage.GetPrimAtPath(ROOT_PATH)
    if existing and existing.GetCustomDataByKey("tutorialOwner") != OWNER:
        raise RuntimeError(f"다른 장면이 {ROOT_PATH}를 사용한다. 경로를 먼저 확인한다.")
    # Let Kit process queued UI work. Never use time.sleep in its UI thread.
    await omni.kit.app.get_app().next_update_async()
    if context.get_stage() != stage or not omni.timeline.get_timeline_interface().is_stopped():
        raise RuntimeError("대기 중 Stage 또는 Timeline 상태가 바뀌었다. 다시 실행한다.")
    existing = stage.GetPrimAtPath(ROOT_PATH)
    if existing and existing.GetCustomDataByKey("tutorialOwner") != OWNER:
        raise RuntimeError("대기 중 다른 도구가 이 경로를 사용했다. 장면을 확인한다.")
    if existing:
        stage.RemovePrim(ROOT_PATH)
    root = UsdGeom.Xform.Define(stage, ROOT_PATH)
    root.GetPrim().SetCustomDataByKey("tutorialOwner", OWNER)
    cube = UsdGeom.Cube.Define(stage, ROOT_PATH + "/Cube")
    cube.CreateSizeAttr(0.4)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.5))
    cube.CreateDisplayColorAttr([Gf.Vec3f(0.05, 0.3, 0.9)])
    light = UsdLux.DomeLight.Define(stage, ROOT_PATH + "/Light")
    light.CreateIntensityAttr(700.0)
    context.get_selection().set_selected_prim_paths([str(cube.GetPath())], True)
    print(f"장면 생성 완료: {ROOT_PATH}. Viewport에 마우스를 놓고 F를 누른다.")


def show_result(task):
    if not task.cancelled():
        error = task.exception()
        if error is not None:
            print(f"장면 생성 실패: {error}")


# Script Editor keeps globals between runs. Cancel an earlier pending invocation.
previous_task = globals().get("_scene_task")
if previous_task is not None and not previous_task.done():
    previous_task.cancel()
_scene_task = asyncio.ensure_future(build_scene())
_scene_task.add_done_callback(show_result)
