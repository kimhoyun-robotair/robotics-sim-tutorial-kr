import asyncio
import numpy as np
import omni.kit.app
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid


async def run_interactive():
    if World.instance() is not None:
        raise RuntimeError("Use a fresh GUI instance for this exercise.")
    world = World(stage_units_in_meters=1.0)
    await world.initialize_simulation_context_async()
    world.scene.add_default_ground_plane()
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/FallingCube",
            name="cube",
            position=np.array([0, 0, 2.0]),
            size=0.4,
        )
    )
    await world.reset_async()
    samples = []

    def record(dt):
        samples.append((float(dt), float(cube.get_world_pose()[0][2])))

    world.add_physics_callback("interactive_record", record)
    try:
        while len(samples) < 120:
            await omni.kit.app.get_app().next_update_async()
    finally:
        world.remove_physics_callback("interactive_record")
        await world.pause_async()
    print("Interactive callback samples:", samples)


interactive_task = asyncio.ensure_future(run_interactive())
interactive_task.add_done_callback(lambda task: task.result())
