"""Bounded Jetbot startup, straight drive, stop, and reset checks for Isaac Sim 5.1."""

from smoke_common import add_light, application, arguments, require


args = arguments("drive_jetbot")
with application(args, "drive_jetbot") as (simulation_app, metrics):
    import numpy as np
    from pxr import Usd, UsdGeom, UsdPhysics
    from isaacsim.core.api import World
    from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController
    from isaacsim.robot.wheeled_robots.robots import WheeledRobot
    from isaacsim.storage.native import get_assets_root_path

    world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
    world.scene.add_default_ground_plane()
    add_light(world.stage)
    root = get_assets_root_path()
    require(root is not None, "Isaac Sim 5.1 assets are unavailable; check the asset root/network")
    asset = root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
    wheel_names = ["left_wheel_joint", "right_wheel_joint"]
    robot = world.scene.add(WheeledRobot(
        prim_path="/World/Jetbot", name="jetbot", wheel_dof_names=wheel_names,
        create_robot=True, usd_path=asset, position=np.array([0.0, 0.0, 0.10]),
    ))
    robot_prim = world.stage.GetPrimAtPath("/World/Jetbot")
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render", "proxy"])
    collider_bottoms = []
    for prim in Usd.PrimRange(robot_prim, Usd.TraverseInstanceProxies()):
        if prim.HasAPI(UsdPhysics.CollisionAPI) and prim.IsA(UsdGeom.Gprim):
            if UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() is False:
                continue
            box = cache.ComputeWorldBound(prim).ComputeAlignedBox()
            if not box.IsEmpty():
                collider_bottoms.append(float(box.GetMin()[2]))
    require(collider_bottoms, "Robot has no loaded collision geometry")
    # Conservative world-space bounds catch floor overlap before the first physics step.
    require(min(collider_bottoms) >= 0.0, "Robot collider overlaps the floor at spawn")
    world.reset()
    require(all(name in robot.dof_names for name in wheel_names), f"Unexpected DOFs: {robot.dof_names}")
    wheel_indices = np.array([robot.dof_names.index(name) for name in wheel_names])
    robot.get_articulation_controller().switch_control_mode("velocity")
    controller = DifferentialController(name="diff", wheel_radius=0.03, wheel_base=0.1125)

    def command(linear_speed):
        robot.apply_wheel_actions(controller.forward([linear_speed, 0.0]))
        require(simulation_app.is_running(), "Application closed before the drive test completed")
        world.step(render=args.gui)
        p, q = robot.get_world_pose()
        joint_velocity = robot.get_joint_velocities()
        require(np.isfinite(np.r_[p, q, joint_velocity]).all(), "Nonfinite robot state")
        require(-0.03 < p[2] < 0.5, "Robot fell through the floor or was launched upward")
        require(abs(float(np.linalg.norm(q)) - 1.0) < 0.02, "Invalid robot quaternion")
        require(1 - 2 * (q[1] ** 2 + q[2] ** 2) > np.cos(np.deg2rad(25)), "Robot tilted or collapsed")
        return p.copy(), joint_velocity[wheel_indices].copy()

    # Let the unloaded robot settle before measuring motion.
    for _ in range(180):
        start, _ = command(0.0)
    history = []
    for step in range(240):
        # Ramp to 0.12 m/s over 0.5 s; decelerate over the same duration.
        speed = 0.12 * min(1.0, (step + 1) / 30) if step < 120 else 0.12 * max(0.0, (150 - step) / 30)
        p, wheel_velocity = command(speed)
        require(abs(float(p[2] - start[2])) < 0.05, "Robot base height changed excessively")
        history.append([step / 60, speed, *p, *wheel_velocity])
    data = np.asarray(history)
    displacement = p[:2] - start[:2]
    require(0.10 < displacement[0] < 0.5, f"Unexpected forward motion: {displacement}")
    require(abs(displacement[1]) < 0.08, "Straight motion drifted sideways")
    require(np.abs(data[-30:, -2:]).max() < 0.3, "Wheel velocity did not settle after stopping")
    require(np.linalg.norm(data[-1, 2:4] - data[-30, 2:4]) < 0.02, "Robot kept drifting after stop")
    np.savetxt(args.output_dir / "drive.csv", data, delimiter=",", comments="",
               header="sim_time_s,command_m_s,x_m,y_m,z_m,left_rad_s,right_rad_s")
    world.reset()
    reset_position, _ = robot.get_world_pose()
    require(np.linalg.norm(reset_position - np.array([0.0, 0.0, 0.10])) < 0.02,
            "Reset did not restore the robot spawn pose")
    metrics.update({"asset": asset, "wheel_dof_names": wheel_names,
                    "spawn_collider_min_z_m": min(collider_bottoms),
                    "displacement_xy_m": displacement.tolist(),
                    "max_final_wheel_speed_rad_s": float(np.abs(data[-30:, -2:]).max()),
                    "artifacts": ["drive.csv"], "render_validation": "NOT_TESTED"})
