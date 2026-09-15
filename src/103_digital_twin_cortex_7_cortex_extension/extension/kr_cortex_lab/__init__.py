import asyncio

import numpy as np
import omni.ext
import omni.ui as ui
from isaacsim.core.utils.stage import create_new_stage_async
from isaacsim.cortex.framework.cortex_world import CortexWorld
from isaacsim.cortex.framework.df import DfNetwork, DfState, DfStateMachineDecider
from isaacsim.cortex.framework.dfb import DfRobotApiContext
from isaacsim.cortex.framework.robot import add_franka_to_stage


class Reach(DfState):
    def step(self):
        self.context.robot.arm.send_end_effector(target_position=self.context.goal)
        return self


class CortexLab(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.world = None
        self.context = None
        self.pending = None
        self.window = ui.Window("KR Cortex World Lab", width=360, height=180)
        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("Start in a new empty Isaac Sim session.")
                ui.Button("LOAD NEW WORLD", clicked_fn=lambda: self.schedule(self.load))
                ui.Button("TARGET LEFT", clicked_fn=lambda: self.set_goal([0.5, 0.25, 0.5]))
                ui.Button("TARGET RIGHT", clicked_fn=lambda: self.set_goal([0.5, -0.25, 0.5]))
                ui.Button("RESET", clicked_fn=lambda: self.schedule(self.reset))
                self.status = ui.Label("Ready")

    def schedule(self, operation):
        if self.pending is not None and not self.pending.done():
            return
        self.pending = asyncio.ensure_future(operation())
        self.pending.add_done_callback(self.report)

    def report(self, task):
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            self.status.text = f"Failed: {error}"
            raise error

    async def load(self):
        if self.world is not None:
            await self.reset()
            return
        if CortexWorld.instance() is not None:
            raise RuntimeError("An existing World is active. Restart Isaac Sim before this isolated lab.")
        await create_new_stage_async()
        self.world = CortexWorld()
        await self.world.initialize_simulation_context_async()
        robot = self.world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/Franka"))
        self.world.scene.add_default_ground_plane()
        self.context = DfRobotApiContext(robot)
        self.context.goal = np.array([0.5, 0.25, 0.5])
        self.world.add_decider_network(DfNetwork(DfStateMachineDecider(Reach()), context=self.context))
        await self.world.reset_async()
        self.world.add_physics_callback("kr_cortex_step", lambda dt: self.world.step(False, False))
        await self.world.play_async()
        self.status.text = "Running: left target"

    async def reset(self):
        if self.world is None:
            return
        await self.world.reset_async()
        self.world.reset_cortex()
        await self.world.play_async()
        self.status.text = "Reset complete"

    def set_goal(self, position):
        if self.context is not None:
            self.context.goal = np.array(position)
            self.status.text = f"Goal: {position}"

    def on_shutdown(self):
        if self.pending is not None and not self.pending.done():
            self.pending.cancel()
        if self.world is not None and self.world.physics_callback_exists("kr_cortex_step"):
            self.world.remove_physics_callback("kr_cortex_step")
            self.world.pause()
        self.window = None
