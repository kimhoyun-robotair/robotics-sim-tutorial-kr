"""Run in Script Editor on the official multi-sensor publish-rate scenario, BEFORE first Play."""
import carb
import omni.graph.core as og
import omni.timeline
import omni.usd
TARGET_FPS = 60
RGB_SKIP = 3
LIDAR_SKIP = 11
INFO_SKIP = 5
stage = omni.usd.get_context().get_stage()
timeline = omni.timeline.get_timeline_interface()
if timeline.is_playing():
    raise RuntimeError("Stop and reload the scenario before configuring rates")
updates = {
    "/World/turtlebot3_burger/base_scan/ROS_LidarRTX/LaserScanPublish.inputs:frameSkipCount": LIDAR_SKIP,
    "/World/turtlebot3_burger/base_scan/ROS_LidarRTX/PointCloudPublish.inputs:enabled": False,
    "/World/ActionGraph_camera/isaac_create_render_product_01.inputs:enabled": False,
    "/World/ActionGraph_camera/ros2_camera_helper.inputs:frameSkipCount": RGB_SKIP,
    "/World/ActionGraph_camera/ros2_camera_helper_02.inputs:enabled": False,
    "/World/ActionGraph_camera/ros2_camera_info_helper.inputs:frameSkipCount": INFO_SKIP,
}
for path in updates:
    if not og.Controller.attribute(path).is_valid():
        raise RuntimeError(f"Expected official scenario attribute is missing: {path}")
for path, value in updates.items():
    og.Controller.set(og.Controller.attribute(path), value)
    print(path, "=", og.Controller.attribute(path).get())
stage.SetTimeCodesPerSecond(TARGET_FPS)
timeline.set_target_framerate(TARGET_FPS)
settings = carb.settings.get_settings()
settings.set_bool("/app/runLoops/main/rateLimitEnabled", True)
settings.set_int("/app/runLoops/main/rateLimitFrequency", TARGET_FPS)
settings.set_int("/persistent/simulation/minFrameRate", TARGET_FPS)
print("Configured target FPS=", TARGET_FPS, "Press Play; measure actual rates with ros2 topic hz")
