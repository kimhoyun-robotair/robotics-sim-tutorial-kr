"""Drop a 0.2 m, 1 kg cube and verify contact/settling over two resets.

Run: $ISAACSIM_PATH/python.sh examples/standalone/hello_stage.py [--gui]
This checks physics. It does not claim that camera rendering was tested.
"""

from smoke_common import add_light, application, arguments, require


args = arguments("hello_stage")
with application(args, "hello_stage") as (simulation_app, metrics):
    import numpy as np
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid

    world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
    world.scene.add_default_ground_plane()
    add_light(world.stage)
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Cube", name="falling_cube",
            position=np.array([0.0, 0.0, 1.0]), size=0.2, mass=1.0,
            color=np.array([0.2, 0.7, 1.0]),
        )
    )

    history = []
    for run in range(2):
        world.reset()
        start, _ = cube.get_world_pose()
        require(abs(float(start[2]) - 1.0) < 0.02, "Reset did not restore the initial pose")
        tail = []
        for step in range(240):
            require(simulation_app.is_running(), "Application closed before the test completed")
            world.step(render=args.gui)
            position, orientation = cube.get_world_pose()
            velocity = cube.get_linear_velocity()
            require(np.isfinite(np.r_[position, orientation, velocity]).all(), "Nonfinite cube state")
            require(-0.02 < position[2] < 1.1, "Cube fell through the floor or became unstable")
            if step >= 180:
                tail.append([float(position[2]), float(np.linalg.norm(velocity))])
        tail = np.asarray(tail)
        require(np.abs(tail[:, 0] - 0.1).max() < 0.02, "Cube did not settle at half its height")
        require(tail[:, 1].max() < 0.05, "Cube is still moving after the settling period")
        history.append({"run": run, "final_z_m": float(tail[-1, 0]),
                        "max_tail_speed_m_s": float(tail[:, 1].max())})
    metrics.update({"physics_dt_s": 1 / 60, "steps_per_reset": 240, "runs": history,
                    "render_validation": "NOT_TESTED"})
