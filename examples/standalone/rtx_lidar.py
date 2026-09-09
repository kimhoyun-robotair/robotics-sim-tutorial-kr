"""Check an RTX lidar against six known planes, 3 m from the sensor origin.

Run: $ISAACSIM_PATH/python.sh examples/standalone/rtx_lidar.py [--gui]
Sensor and world axes coincide, so the XYZ comparison requires no TF conversion.
"""

from smoke_common import add_light, application, arguments, require


args = arguments("rtx_lidar")
with application(args, "rtx_lidar") as (simulation_app, metrics):
    import carb.settings
    import numpy as np
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import FixedCuboid
    from isaacsim.sensors.rtx import LidarRtx

    carb.settings.get_settings().set_bool("/app/sensors/nv/lidar/outputBufferOnGPU", True)
    world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
    add_light(world.stage)
    # Interior surfaces lie on x/y/z = +/-3.0 m; the lidar is outside every wall collider.
    for axis in range(3):
        for sign in (-1, 1):
            position = np.zeros(3)
            position[axis] = sign * 3.05
            scale = np.full(3, 6.2)
            scale[axis] = 0.1
            name = f"wall_{axis}_{'positive' if sign > 0 else 'negative'}"
            world.scene.add(FixedCuboid(
                prim_path=f"/World/{name}", name=name, position=position,
                size=1.0, scale=scale, color=np.array([0.6, 0.6, 0.6]),
            ))
    lidar = LidarRtx(
        prim_path="/World/Lidar", translation=np.zeros(3),
        orientation=np.array([1.0, 0.0, 0.0, 0.0]), config_file_name="Example_Rotary",
    )
    world.reset()
    lidar.initialize()
    annotator_name = "IsaacExtractRTXSensorPointCloudNoAccumulator"
    lidar.attach_annotator(annotator_name)
    samples = []
    previous_time = -1.0
    all_points = []
    for step in range(600):
        require(simulation_app.is_running(), "Application closed before lidar capture")
        world.step(render=True)
        if step < 120:
            continue
        frame = lidar.get_current_frame()
        timestamp = float(frame.get("rendering_time", -1))
        require(np.isfinite(timestamp), "Nonfinite lidar timestamp")
        if timestamp == previous_time or timestamp < 0:
            continue
        payload = frame.get(annotator_name)
        if not isinstance(payload, dict) or payload.get("data") is None:
            continue
        points = np.asarray(payload["data"])
        if points.size == 0:
            continue
        require(timestamp > previous_time, "Lidar time went backwards")
        previous_time = timestamp
        require(points.ndim == 2 and points.shape[1] == 3, f"Unexpected lidar shape: {points.shape}")
        require(np.isfinite(points).all(), "Lidar contains NaN/Inf")
        distances = np.linalg.norm(points, axis=1)
        valid = distances > 0.1
        require(valid.mean() > 0.9 and valid.sum() >= 32, "Too few valid returns in the closed test room")
        points = points[valid]
        plane_error = np.min(np.abs(np.abs(points) - 3.0), axis=1)
        require(float(np.quantile(plane_error, 0.99)) < 0.08, "Point cloud misses the known wall planes")
        require((np.abs(points) <= 3.1).all(), "Lidar returns lie outside the test room")
        samples.append([timestamp, float(len(points)), float(np.quantile(plane_error, 0.99))])
        all_points.append(points.copy())
        if len(samples) >= 30:
            break
    require(len(samples) >= 30, f"Only {len(samples)} fresh lidar outputs arrived within 600 steps")
    data = np.asarray(samples)
    require(np.diff(data[:, 0]).max() < 0.25, "Lidar output stalled for 0.25 simulated seconds")
    np.savez_compressed(args.output_dir / "lidar_data.npz", points=np.concatenate(all_points), samples=data)
    metrics.update({"config": "Example_Rotary", "annotator": annotator_name,
                    "fresh_outputs": len(samples), "minimum_points": int(data[:, 1].min()),
                    "maximum_p99_plane_error_m": float(data[:, 2].max()),
                    "sensor_position_m": [0, 0, 0], "sensor_orientation_wxyz": [1, 0, 0, 0],
                    "artifacts": ["lidar_data.npz"]})
    lidar.detach_annotator(annotator_name)
