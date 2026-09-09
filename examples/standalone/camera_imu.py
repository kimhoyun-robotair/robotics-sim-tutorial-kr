"""Known scene RGB/depth + stationary IMU regression exercise for Isaac Sim 5.1.

Run: $ISAACSIM_PATH/python.sh examples/standalone/camera_imu.py [--gui]
Depth is distance to the image plane, in metres. Images use (height, width).
"""

from smoke_common import add_light, application, arguments, require


args = arguments("camera_imu")
with application(args, "camera_imu") as (simulation_app, metrics):
    import numpy as np
    from PIL import Image
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
    from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
    from isaacsim.sensors.camera import Camera
    from isaacsim.sensors.physics import IMUSensor, _sensor

    world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
    world.scene.add_default_ground_plane()
    add_light(world.stage)
    world.scene.add(FixedCuboid(
        prim_path="/World/Target", name="target", size=0.5,
        position=np.array([0.0, 0.0, 0.25]), color=np.array([0.8, 0.04, 0.04]),
    ))
    # A real rigid body is required: an empty Xform cannot supply IMU acceleration.
    body = world.scene.add(DynamicCuboid(
        prim_path="/World/ImuBody", name="imu_body", size=0.2, mass=1.0,
        position=np.array([-1.0, 0.0, 0.20]), color=np.array([0.04, 0.1, 0.8]),
    ))
    imu = world.scene.add(IMUSensor(
        prim_path="/World/ImuBody/Imu", name="imu", frequency=60,
        translation=np.zeros(3), orientation=np.array([1.0, 0.0, 0.0, 0.0]),
        linear_acceleration_filter_size=1, angular_velocity_filter_size=1,
        orientation_filter_size=1,
    ))
    camera_position = np.array([0.0, 0.0, 3.0])
    # Camera's default API axes: +X forward, +Z up. +90 degrees about Y looks down.
    camera_orientation = euler_angles_to_quats(np.array([0, 90, 0]), degrees=True)
    camera = Camera(
        prim_path="/World/Camera", position=camera_position,
        orientation=camera_orientation, frequency=30, resolution=(640, 480),
    )
    world.reset()
    camera.initialize()
    camera.set_clipping_range(0.1, 20.0)
    camera.add_distance_to_image_plane_to_frame()
    imu_interface = _sensor.acquire_imu_sensor_interface()

    frames = []
    image_dir = args.output_dir / "frames"
    image_dir.mkdir(exist_ok=True)
    imu_samples = []
    previous_camera_time = -1.0
    previous_imu_time = -1.0
    # Bounded warmup and collection: the outer runner also enforces wall time.
    for step in range(600):
        require(simulation_app.is_running(), "Application closed before capture")
        world.step(render=True)
        position, orientation = body.get_world_pose()
        require(np.isfinite(np.r_[position, orientation]).all(), "Nonfinite IMU body pose")
        require(position[2] > -0.02, "IMU body fell through the floor")
        if step < 180:
            continue

        reading = imu_interface.get_sensor_reading(
            imu.prim_path, use_latest_data=True, read_gravity=True
        )
        require(reading.is_valid, "IMU reading is invalid after warmup")
        acceleration = np.array([reading.lin_acc_x, reading.lin_acc_y, reading.lin_acc_z])
        angular_velocity = np.array([reading.ang_vel_x, reading.ang_vel_y, reading.ang_vel_z])
        require(np.isfinite(np.r_[reading.time, acceleration, angular_velocity]).all(), "Nonfinite IMU output")
        require(reading.time > previous_imu_time, "IMU timestamp is not increasing")
        previous_imu_time = reading.time
        require(abs(np.linalg.norm(acceleration) - 9.81) < 0.5, "Stationary IMU gravity is incorrect")
        require(np.linalg.norm(angular_velocity) < 0.1, "Stationary IMU angular velocity is too large")
        imu_samples.append([reading.time, *acceleration, *angular_velocity])

        frame = camera.get_current_frame()
        # In 5.1, rendering_frame can be Fabric time metadata, not an integer.
        camera_time = float(frame.get("rendering_time", -1))
        require(np.isfinite(camera_time), "Nonfinite camera timestamp")
        if camera_time == previous_camera_time or camera_time < 0:
            continue
        rgba = camera.get_rgba()
        depth = camera.get_depth()
        if rgba is None or depth is None or rgba.size == 0 or depth.size == 0:
            continue
        require(camera_time > previous_camera_time, "Camera timestamp went backwards")
        previous_camera_time = camera_time
        require(rgba.shape == (480, 640, 4), f"Unexpected RGBA shape: {rgba.shape}")
        require(depth.shape == (480, 640), f"Unexpected depth shape: {depth.shape}")
        rgb = rgba[..., :3].astype(np.float32)
        require(np.isfinite(rgb).all(), "Nonfinite RGB data")
        require(2.0 < float(rgb.mean()) < 253.0 and float(rgb.std()) > 2.0,
                "Reference RGB is black, saturated, or uniform")
        roi_rgb = rgb[230:250, 310:330]
        require(float(roi_rgb[..., 0].mean()) > 1.2 * float(roi_rgb[..., 1].mean()),
                "The red target is missing from the image centre")
        roi_depth = depth[230:250, 310:330]
        require(np.isfinite(roi_depth).all() and (roi_depth > 0).all(), "Target depth is invalid")
        depth_error = float(np.abs(roi_depth - 2.5).max())
        require(depth_error < 0.05, f"Camera target depth error: {depth_error} m")
        require(not np.isnan(depth).any(), "Depth contains NaN")
        # Inf elsewhere can legitimately denote a ray that hits no surface.
        Image.fromarray(rgba[..., :3].astype(np.uint8)).save(
            image_dir / f"frame_{len(frames):04d}.png"
        )
        frames.append([float(len(frames)), camera_time,
                       float(rgb.mean()), depth_error])
        if len(frames) >= 30:
            break

    require(len(frames) >= 30, f"Only {len(frames)} unique camera frames arrived within 600 steps")
    frame_samples = np.asarray(frames)
    require(np.all(np.diff(frame_samples[:, 1]) > 0), "Camera timestamps do not increase")
    measured_hz = (len(frames) - 1) / (frame_samples[-1, 1] - frame_samples[0, 1])
    # Check stalls separately from rate calibration: wrapper scheduling can quantize periods.
    require(np.diff(frame_samples[:, 1]).max() < 0.15, "Camera output stalled for 0.15 simulated seconds")
    intrinsics = camera.get_intrinsics_matrix()
    require(intrinsics.shape == (3, 3) and np.isfinite(intrinsics).all(), "Invalid camera intrinsics")
    Image.fromarray(rgba[..., :3].astype(np.uint8)).save(args.output_dir / "rgb.png")
    np.savez_compressed(
        args.output_dir / "sensor_data.npz", rgba=rgba, depth=depth,
        intrinsics=intrinsics, camera_position=camera_position,
        camera_orientation=camera_orientation, camera_frames=frame_samples,
        camera_axes=np.array("world"), quaternion_order=np.array("wxyz"),
        imu=np.asarray(imu_samples),
    )
    metrics.update({"unique_camera_frames": len(frames), "camera_sim_rate_hz": float(measured_hz),
                    "max_target_depth_error_m": float(frame_samples[:, 3].max()),
                    "imu_samples": len(imu_samples), "imu_gravity_enabled": True,
                    "artifacts": ["rgb.png", "frames/", "sensor_data.npz"]})
