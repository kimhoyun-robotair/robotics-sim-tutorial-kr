#!/usr/bin/env python3
"""ROS closed-loop teaching scene: a bounded kinematic cuboid, clock, odom and TF.

This is a communication/kinematics fixture, not a wheeled robot physics model.
The cuboid intentionally has no rigid-body or joint API. No external USD assets.
"""
import argparse
import json
import math
from pathlib import Path
import time


def bounded_command(linear, angular):
    """Reject nonfinite data and constrain requested planar speed."""
    if not math.isfinite(linear) or not math.isfinite(angular):
        return 0.0, 0.0
    return max(-0.2, min(0.2, linear)), max(-0.6, min(0.6, angular))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seconds", type=float, default=180)
    parser.add_argument("--output", type=Path, default=Path("artifacts/ros_scene.json"))
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        parser.error("--seconds must be between 1 and 3600")

    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless, "renderer": "RayTracedLighting"})
    node = None
    ros = None
    report = {"status": "FAIL", "fixture": "kinematic_cuboid", "frames": 0,
              "commands_received": 0, "watchdog_stops": 0, "workspace_stops": 0}
    try:
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension("isaacsim.ros2.bridge")
        app.update()
        import rclpy
        from rclpy.qos import QoSProfile, qos_profile_clock
        from geometry_msgs.msg import Twist, TransformStamped
        from nav_msgs.msg import Odometry
        from rosgraph_msgs.msg import Clock
        from tf2_msgs.msg import TFMessage
        from isaacsim.core.api import World
        from pxr import Gf, UsdGeom, UsdLux
        import omni.usd

        ros = rclpy
        ros.init(args=[])
        node = ros.create_node("tutorial_kinematic_scene")
        clock_pub = node.create_publisher(Clock, "/clock", qos_profile_clock)
        odom_pub = node.create_publisher(Odometry, "/tutorial/odom", 10)
        tf_pub = node.create_publisher(TFMessage, "/tf", 10)
        command = {"v": 0.0, "w": 0.0, "received": -math.inf}

        def receive(message):
            command["v"], command["w"] = bounded_command(message.linear.x, message.angular.z)
            command["received"] = time.monotonic()
            report["commands_received"] += 1

        # Depth one avoids a backlog of old motion commands after a slow render frame.
        node.create_subscription(Twist, "/tutorial/cmd_vel", receive, QoSProfile(depth=1))
        dt = 1 / 60
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        body = UsdGeom.Xform.Define(stage, "/World/TutorialBase")
        translate = body.AddTranslateOp()
        rotate = body.AddRotateZOp()
        box = UsdGeom.Cube.Define(stage, "/World/TutorialBase/Body")
        box.CreateSizeAttr(1.0)
        box.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
        box.AddScaleOp().Set(Gf.Vec3f(0.4, 0.3, 0.2))
        box.CreateDisplayColorAttr([Gf.Vec3f(0.08, 0.42, 0.75)])
        light = UsdLux.DomeLight.Define(stage, "/World/TutorialLight")
        light.CreateIntensityAttr(800.0)
        world.reset()
        x = y = yaw = 0.0
        previous_time = world.current_time
        deadline = time.monotonic() + args.seconds
        print("READY: /tutorial/cmd_vel -> cuboid -> /tutorial/odom and /tf; /clock active.")
        print("Limits: |v|<=0.2 m/s, |w|<=0.6 rad/s, watchdog=0.5 wall seconds, |x,y|<=2 m.")
        while app.is_running() and time.monotonic() < deadline:
            started = time.monotonic()
            ros.spin_once(node, timeout_sec=0.0)
            if not world.is_playing():
                command["v"] = command["w"] = 0.0
                command["received"] = -math.inf
                app.update()
                previous_time = world.current_time
                time.sleep(0.01)
                continue
            v, w = command["v"], command["w"]
            if time.monotonic() - command["received"] > 0.5:
                if v != 0.0 or w != 0.0:
                    report["watchdog_stops"] += 1
                command["v"] = command["w"] = 0.0
                v = w = 0.0
            next_x = x + v * math.cos(yaw) * dt
            next_y = y + v * math.sin(yaw) * dt
            if abs(next_x) > 2.0 or abs(next_y) > 2.0:
                command["v"] = command["w"] = 0.0
                v = w = 0.0
                report["workspace_stops"] += 1
            else:
                x, y = next_x, next_y
                yaw = math.atan2(math.sin(yaw + w * dt), math.cos(yaw + w * dt))
            translate.Set(Gf.Vec3d(x, y, 0))
            rotate.Set(math.degrees(yaw))
            world.step(render=True)
            now = world.current_time
            if now <= previous_time:
                raise RuntimeError("Simulation time reset or failed to advance; restart this scene for a new run")
            previous_time = now
            clock = Clock()
            clock.clock.sec, clock.clock.nanosec = divmod(round(now * 1e9), 1_000_000_000)
            clock_pub.publish(clock)
            odom = Odometry()
            odom.header.stamp = clock.clock
            odom.header.frame_id = "odom"
            odom.child_frame_id = "tutorial_base"
            odom.pose.pose.position.x = x
            odom.pose.pose.position.y = y
            odom.pose.pose.orientation.z = math.sin(yaw / 2)
            odom.pose.pose.orientation.w = math.cos(yaw / 2)
            odom.twist.twist.linear.x = v
            odom.twist.twist.angular.z = w
            # Small nonzero covariance identifies this as idealized fixture odometry.
            for index in (0, 7, 14, 21, 28, 35):
                odom.pose.covariance[index] = 1e-6
                odom.twist.covariance[index] = 1e-6
            odom_pub.publish(odom)
            transform = TransformStamped()
            transform.header = odom.header
            transform.child_frame_id = odom.child_frame_id
            transform.transform.translation.x = x
            transform.transform.translation.y = y
            transform.transform.rotation = odom.pose.pose.orientation
            tf_pub.publish(TFMessage(transforms=[transform]))
            report["frames"] += 1
            time.sleep(max(0.0, dt - (time.monotonic() - started)))
        if report["frames"] == 0:
            raise RuntimeError("No simulation frames completed")
        report.update(status="PASS", final_pose={"x": x, "y": y, "yaw": yaw})
        report["scope"] = "scene execution only; external communication requires ros_acceptance.py"
    except BaseException as error:
        report["status"] = "FAIL"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if node is not None:
            node.destroy_node()
        if ros is not None and ros.ok():
            ros.shutdown()
        app.close(exit_code=0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
