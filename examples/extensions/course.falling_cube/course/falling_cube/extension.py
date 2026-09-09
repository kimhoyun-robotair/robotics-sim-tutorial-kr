"""GUI의 실행 루프를 유지하면서 작업, 구독, 창을 정리하는 최소 Extension."""

import asyncio

import carb
import omni.ext
import omni.kit.app
import omni.physx
import omni.timeline
import omni.ui as ui
import omni.usd

from .scene import ROOT, build_scene


class FallingCubeExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._alive = True
        self._task = None
        self._physics_sub = None
        self._owned_stage = None
        self._elapsed = 0.0
        self._next_report = 1.0
        self._context = omni.usd.get_context()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage_sub = self._context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event, name="course.falling_cube.stage"
        )
        self._window = ui.Window("Course Falling Cube", width=460, height=150)
        with self._window.frame:
            with ui.VStack(spacing=6):
                ui.Label("Save your work, then choose File > New.")
                ui.Button("Build in empty stage", clicked_fn=self._request_build)
                self._status = ui.Label("Build, select Cube, press F, then Play.", word_wrap=True)
        carb.log_info(f"[course] enabled: {ext_id}")

    def _request_build(self):
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.ensure_future(self._build_async())

    async def _build_async(self):
        try:
            if not self._timeline.is_stopped():
                raise RuntimeError("먼저 Stop을 누른다. Pause 상태에서는 생성하지 않는다.")
            candidate_stage = self._context.get_stage()
            # UI에 제어권을 넘긴다. 이것은 physics 한 step을 실행하라는 뜻이 아니다.
            await omni.kit.app.get_app().next_update_async()
            if not self._alive or self._context.get_stage() != candidate_stage:
                return
            if not self._timeline.is_stopped():
                raise RuntimeError("장면 생성 전에 Play가 눌렸다. Stop 후 다시 시도한다.")
            build_scene(candidate_stage)
            self._owned_stage = candidate_stage
            self._elapsed = 0.0
            self._next_report = 1.0
            self._physics_sub = omni.physx.get_physx_interface().subscribe_physics_step_events(
                self._on_physics_step
            )
            self._status.text = "Created. Select Cube, press F, then Play."
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if self._alive:
                self._status.text = str(exc)
            carb.log_error(f"[course] build failed: {exc}")

    def _on_physics_step(self, dt):
        if not self._alive or self._context.get_stage() != self._owned_stage:
            return
        if not self._owned_stage.GetPrimAtPath(ROOT + "/Cube"):
            return
        self._elapsed += float(dt)
        if self._elapsed >= self._next_report:
            carb.log_info(f"[course] accumulated physics time: {self._elapsed:.2f} s")
            self._next_report += 1.0

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.CLOSING):
            if self._task is not None and not self._task.done():
                self._task.cancel()
            self._physics_sub = None
            self._owned_stage = None

    def on_shutdown(self):
        self._alive = False
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None
        self._physics_sub = None
        self._stage_sub = None
        self._owned_stage = None
        if self._window is not None:
            self._window.destroy()
        self._window = None
        self._status = None
        # 앱과 장면은 사용자의 것이다. clear_instance/new_stage/close를 호출하지 않는다.
        carb.log_info("[course] disabled; callbacks and window released")
