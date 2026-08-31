"""Isaac Sim 5.1 standalone smoke test.

Run with: $ISAACSIM_PATH/python.sh examples/standalone/hello_stage.py
"""

from isaacsim import SimulationApp


simulation_app = SimulationApp(
    {
        "headless": True,
        "width": 640,
        "height": 480,
        "disable_viewport_updates": True,
    }
)

try:
    import numpy as np

    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid

    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Cube",
            name="falling_cube",
            position=np.array([0.0, 0.0, 1.0]),
            size=0.2,
            color=np.array([0.2, 0.7, 1.0]),
        )
    )
    world.reset()
    for _ in range(240):
        world.step(render=False)

    position, _ = cube.get_world_pose()
    print(f"final_z={position[2]:.4f}")
finally:
    simulation_app.close()

