"""OmniGraph: tick → clock, camera RGB/depth/info, RTX LaserScan publisher."""

import omni.graph.core as og


def create_graph(camera_product: str, lidar_product: str) -> None:
    keys = og.Controller.Keys
    nodes = [
        ("Tick", "omni.graph.action.OnPlaybackTick"),
        ("Time", "isaacsim.core.nodes.IsaacReadSimulationTime"),
        ("Clock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ("RGB", "isaacsim.ros2.bridge.ROS2CameraHelper"),
        ("Depth", "isaacsim.ros2.bridge.ROS2CameraHelper"),
        ("Info", "isaacsim.ros2.bridge.ROS2CameraInfoHelper"),
        ("Lidar", "isaacsim.ros2.bridge.ROS2RtxLidarHelper"),
    ]
    connects = [
        ("Tick.outputs:tick", f"{name}.inputs:execIn")
        for name in ("Clock", "RGB", "Depth", "Info", "Lidar")
    ]
    connects.append(("Time.outputs:simulationTime", "Clock.inputs:timeStamp"))
    values: list[tuple[str, str | int]] = [("Clock.inputs:topicName", "clock")]
    for name, topic in (
        ("RGB", "camera/rgb"),
        ("Depth", "camera/depth"),
        ("Info", "camera/camera_info"),
    ):
        values.extend(
            [
                (f"{name}.inputs:renderProductPath", camera_product),
                (f"{name}.inputs:frameId", "camera_optical_frame"),
                (f"{name}.inputs:topicName", topic),
                (f"{name}.inputs:frameSkipCount", 3),
            ]
        )
    values.extend(
        [
            ("RGB.inputs:type", "rgb"),
            ("Depth.inputs:type", "depth"),
            ("Lidar.inputs:renderProductPath", lidar_product),
            ("Lidar.inputs:frameId", "laser"),
            ("Lidar.inputs:topicName", "scan_raw"),
            ("Lidar.inputs:type", "laser_scan"),
        ]
    )
    og.Controller.edit(
        {"graph_path": "/World/ROSGraph", "evaluator_name": "execution"},
        {
            keys.CREATE_NODES: nodes,
            keys.CONNECT: connects,
            keys.SET_VALUES: values,
        },
    )
