#!/usr/bin/env python3
"""Publish the actual World simulation clock through native Jazzy rclpy.

Run with Isaac Sim 6.0.1 python.sh after sourcing /opt/ros/jazzy/setup.bash.
This uses Python ROS messages; the lesson also explains the OmniGraph path.
"""
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seconds", type=float, default=120.0,
                        help="Maximum wall-clock run time after stage setup")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        parser.error("--seconds must be between 1 and 3600")

    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless, "renderer": "RayTracedLighting"})
    node = None
    ros = None
    exit_code = 1
    try:
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension("isaacsim.ros2.bridge")
        app.update()
        import rclpy
        from rclpy.qos import qos_profile_clock
        from rosgraph_msgs.msg import Clock
        from isaacsim.core.api import World

        ros = rclpy
        ros.init(args=[])
        node = ros.create_node("tutorial_clock")
        publisher = node.create_publisher(Clock, "/clock", qos_profile_clock)
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        world.reset()
        deadline = time.monotonic() + args.seconds
        previous = -1
        print("READY: /clock publisher; ROS_DOMAIN_ID must match the external terminal.")
        while app.is_running() and time.monotonic() < deadline:
            started = time.monotonic()
            world.step(render=True)
            ros.spin_once(node, timeout_sec=0.0)
            if world.is_playing():
                stamp_ns = round(world.current_time * 1_000_000_000)
                # Pausing must not generate duplicate timestamps; Stop/Play starts a new run.
                if stamp_ns < previous:
                    raise RuntimeError("Simulation time moved backwards; restart the scene for a new run")
                if stamp_ns > previous:
                    message = Clock()
                    message.clock.sec, message.clock.nanosec = divmod(stamp_ns, 1_000_000_000)
                    publisher.publish(message)
                    previous = stamp_ns
            time.sleep(max(0.0, 1 / 60 - (time.monotonic() - started)))
        if previous < 0:
            raise RuntimeError("No clock messages were published")
        exit_code = 0
    finally:
        if node is not None:
            node.destroy_node()
        if ros is not None and ros.ok():
            ros.shutdown()
        app.close(exit_code=exit_code)


if __name__ == "__main__":
    main()
