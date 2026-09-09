"""A UI extension owns its window, while the user owns the authored USD stage."""

import math

import omni.ext
import omni.timeline
import omni.ui as ui
import omni.usd
from pxr import Gf, UsdGeom, UsdLux

ROOT_PATH = "/World/TutorialScene"
OWNER = "tutorial.scene"


def get_editable_stage():
    if not omni.timeline.get_timeline_interface().is_stopped():
        raise RuntimeError("먼저 Stop을 누른다. Pause 상태에서는 편집하지 않는다.")
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("File > New로 Stage를 먼저 만든다.")
    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.z:
        raise RuntimeError("이 도구는 Z-up Stage에서 실행한다.")
    if not math.isclose(UsdGeom.GetStageMetersPerUnit(stage), 1.0):
        raise RuntimeError("이 도구는 metersPerUnit=1인 Stage에서 실행한다.")
    root = stage.GetPrimAtPath(ROOT_PATH)
    if root and root.GetCustomDataByKey("tutorialOwner") != OWNER:
        raise RuntimeError(f"{ROOT_PATH}를 다른 장면이 사용한다. 덮어쓰지 않는다.")
    return stage


def create_scene():
    stage = get_editable_stage()
    # Rebuild only this tool's explicitly marked root: repeated clicks are safe.
    if stage.GetPrimAtPath(ROOT_PATH):
        stage.RemovePrim(ROOT_PATH)
    root = UsdGeom.Xform.Define(stage, ROOT_PATH)
    root.GetPrim().SetCustomDataByKey("tutorialOwner", OWNER)
    cube = UsdGeom.Cube.Define(stage, ROOT_PATH + "/Cube")
    cube.CreateSizeAttr(0.4)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.5))
    cube.CreateDisplayColorAttr([Gf.Vec3f(0.05, 0.3, 0.9)])
    light = UsdLux.DomeLight.Define(stage, ROOT_PATH + "/Light")
    light.CreateIntensityAttr(700.0)
    omni.usd.get_context().get_selection().set_selected_prim_paths([str(cube.GetPath())], True)
    return "Cube와 Light를 만들었다. Viewport에 마우스를 놓고 F를 누른다."


def remove_scene():
    stage = get_editable_stage()
    if stage.GetPrimAtPath(ROOT_PATH):
        stage.RemovePrim(ROOT_PATH)
    return "이 도구의 장면을 지웠다."


class TutorialSceneExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._window = ui.Window("Tutorial Scene Builder", width=460, height=190)
        with self._window.frame:
            with ui.VStack(spacing=8):
                ui.Label("Z-up / 1 m Stage에서 Stop 후 사용한다.", word_wrap=True)
                ui.Button("Create / Reset Scene", clicked_fn=self._create)
                ui.Button("Remove Scene", clicked_fn=self._remove)
                self._status = ui.Label("장면을 만들 준비가 되었다.", word_wrap=True)

    def _create(self):
        self._run(create_scene)

    def _remove(self):
        self._run(remove_scene)

    def _run(self, action):
        try:
            self._status.text = action()
        except Exception as exc:
            self._status.text = f"실행하지 못했다: {exc}"

    def on_shutdown(self):
        # Release callbacks held by the UI. Do not delete the user's saved scene.
        if self._window is not None:
            self._window.destroy()
            self._window = None
        self._status = None
