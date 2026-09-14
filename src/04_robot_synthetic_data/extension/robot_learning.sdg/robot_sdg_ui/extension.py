"""Kit Extension: Kit가 lifecycle을 소유하며 callback은 async 작업을 예약한다."""

import asyncio
from datetime import datetime
from pathlib import Path

import omni.ext
import omni.kit.app
import omni.replicator.core as rep
import omni.ui as ui
import omni.usd
from isaacsim.core.api import World
from isaacsim.storage.native import get_assets_root_path_async
from omni.kit.viewport.utility import get_active_viewport
from robot_sdg.dataset import DatasetScene


class DatasetExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self.scene = None
        self.world = None
        self.loaded_stage = None
        self.task = None
        self.closed = False
        self.window = ui.Window("Robot Learning SDG", width=460, height=350)
        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label(
                    "Start in an empty Stage. Preview uses the robot camera.",
                    word_wrap=True,
                )
                with ui.HStack():
                    ui.Label("Seed")
                    self.seed = ui.IntField().model
                    self.seed.set_value(7)
                with ui.HStack():
                    ui.Label("Episodes")
                    self.episodes = ui.IntField().model
                    self.episodes.set_value(2)
                with ui.HStack():
                    ui.Label("Frames per episode")
                    self.frames = ui.IntField().model
                    self.frames.set_value(10)
                ui.Label("Output parent directory")
                self.output = ui.StringField().model
                self.output.set_value(str(Path.home() / "isaac_learning_outputs"))
                with ui.HStack():
                    ui.Button("Load / Preview", clicked_fn=lambda: self.schedule(False))
                    ui.Button("Generate", clicked_fn=lambda: self.schedule(True))
                    ui.Button("Cancel", clicked_fn=self.cancel)
                self.status = ui.Label("Ready", word_wrap=True, identifier="sdg_status")

    def schedule(self, generate: bool) -> None:
        if self.task is not None and not self.task.done():
            self.status.text = "A job is already running."
            return
        self.task = asyncio.ensure_future(self.run(generate))

    async def run(self, generate: bool) -> None:
        try:
            episodes, frames = (
                self.episodes.get_value_as_int(),
                self.frames.get_value_as_int(),
            )
            if episodes <= 0 or frames <= 0:
                raise ValueError("Episodes and frames must be positive.")
            if self.scene is None:
                stage = omni.usd.get_context().get_stage()
                world_prim = stage.GetPrimAtPath("/World")
                if World.instance() is not None or (
                    world_prim.IsValid() and list(world_prim.GetChildren())
                ):
                    raise RuntimeError(
                        "Open a fresh empty Stage before loading this tutorial."
                    )
                self.world = World(
                    stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60
                )
                self.loaded_stage = stage
                await self.world.initialize_simulation_context_async()
                assets_root = await get_assets_root_path_async()
                if assets_root is None:
                    raise RuntimeError("Isaac Sim assets are unavailable.")
                self.scene = DatasetScene(
                    self.world,
                    seed=self.seed.get_value_as_int(),
                    assets_root=assets_root,
                )
                await self.world.reset_async()
                self.scene.initialize_camera()
            if omni.usd.get_context().get_stage() != self.loaded_stage:
                raise RuntimeError(
                    "Stage changed. Disable and enable this extension before continuing."
                )
            self.scene.seed = self.seed.get_value_as_int()
            viewport = get_active_viewport()
            if viewport is not None:
                viewport.camera_path = self.scene.camera.prim_path
            await self.world.play_async()
            if not generate:
                self.scene.randomize(0)
                for _ in range(8):
                    await omni.kit.app.get_app().next_update_async()
                await self.world.pause_async()
                self.status.text = (
                    "Preview ready. Change the seed or generate a dataset."
                )
                return
            output = Path(
                self.output.get_value_as_string()
            ).expanduser().resolve() / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            self.scene.frames_written = 0
            self.scene.attach_writer(output)
            for episode in range(episodes):
                self.scene.randomize(episode)
                for frame in range(frames):
                    self.scene.drive_forward()
                    for _ in range(4):
                        await omni.kit.app.get_app().next_update_async()
                    await rep.orchestrator.step_async(
                        rt_subframes=4, delta_time=0.0, pause_timeline=False
                    )
                    self.scene.record_metadata(episode, frame)
                    self.status.text = (
                        f"Episode {episode + 1}/{episodes}, frame {frame + 1}/{frames}"
                    )
            await rep.orchestrator.wait_until_complete_async()
            self.status.text = (
                f"Saved {self.scene.frames_written} frames.\nFolder: {output.name}"
            )
        except asyncio.CancelledError:
            if not self.closed:
                self.status.text = "Cancelled. Completed frames remain on disk."
            raise
        except Exception as error:
            if not self.closed:
                self.status.text = str(error)
            import carb

            carb.log_error(str(error))
        finally:
            try:
                if self.scene is not None:
                    await rep.orchestrator.wait_until_complete_async()
                    self.scene.detach_writer()
                if (
                    self.world is not None
                    and omni.usd.get_context().get_stage() == self.loaded_stage
                ):
                    await self.world.pause_async()
            finally:
                if self.closed:
                    self.release()

    def cancel(self) -> None:
        if self.task is not None and not self.task.done():
            self.task.cancel()

    def release(self) -> None:
        if self.scene is not None:
            self.scene.detach_writer()
        self.scene = None
        if self.world is not None:
            self.world.clear_all_callbacks()
            if World.instance() is self.world:
                self.world.clear_instance()
            self.world = None
        self.loaded_stage = None

    def on_shutdown(self) -> None:
        self.closed = True
        self.cancel()
        if self.task is None or self.task.done():
            self.release()
        self.window.destroy()
        self.window = None
