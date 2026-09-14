"""Standalone Python: Jetbot + RGB/depth + RTX 2D LiDAR + IMU + ROS 2."""

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutorial_common.runtime import (
    add_common_arguments,
    close_app,
    asset_path,
    launch_app,
    output_directory,
    positive_int,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--steps", type=positive_int, default=36000, help="기본 10분 (60 Hz)"
    )
    parser.add_argument(
        "--no-realtime", action="store_true", help="wall clock pacing 해제"
    )
    args = parser.parse_args()
    output = output_directory("02_ros2", args.output)
    app = launch_app(args.headless)
    node = None
    ros_started = False
    lidar_product = None
    try:
        import numpy as np
        import omni.kit.commands
        import omni.replicator.core as rep
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import FixedCuboid
        from isaacsim.core.prims import SingleRigidPrim
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.robot.wheeled_robots.controllers.differential_controller import (
            DifferentialController,
        )
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        from isaacsim.sensors.camera import Camera
        from isaacsim.sensors.physics import IMUSensor
        from pxr import Gf, Usd, UsdPhysics

        enable_extension("isaacsim.ros2.bridge")
        app.update()
        import rclpy  # Bridge 활성화 이후 bundled rclpy를 import한다.
        from graphs import create_graph
        from ros_interface import RobotInterface

        dt = 1 / 60
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=dt)
        world.scene.add_default_ground_plane()
        robot = world.scene.add(
            WheeledRobot(
                prim_path="/World/Robot",
                name="robot",
                wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
                create_robot=True,
                usd_path=asset_path("/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"),
                position=np.array([0.0, 0.0, 0.05]),
            )
        )
        body_paths = [
            str(prim.GetPath())
            for prim in Usd.PrimRange(world.stage.GetPrimAtPath("/World/Robot"))
            if prim.HasAPI(UsdPhysics.RigidBodyAPI)
            and prim.GetName().lower() in ("chassis", "base_link")
        ]
        if len(body_paths) != 1:
            raise RuntimeError(
                f"센서를 부착할 Jetbot chassis를 확인하세요: {body_paths}"
            )
        body = body_paths[0]
        chassis = world.scene.add(SingleRigidPrim(prim_path=body, name="chassis"))
        for index, (position, scale) in enumerate(
            [
                ([2.0, 0.0, 0.4], [0.1, 4.0, 0.8]),
                ([-2.0, 0.0, 0.4], [0.1, 4.0, 0.8]),
                ([0.0, 2.0, 0.4], [4.0, 0.1, 0.8]),
                ([0.0, -2.0, 0.4], [4.0, 0.1, 0.8]),
                ([0.8, 0.8, 0.2], [0.3, 0.3, 0.4]),
            ]
        ):
            world.scene.add(
                FixedCuboid(
                    prim_path=f"/World/Wall_{index}",
                    name=f"wall_{index}",
                    position=np.array(position),
                    scale=np.array(scale),
                    size=1.0,
                )
            )
        camera = world.scene.add(
            Camera(prim_path=body + "/Camera", name="camera", resolution=(320, 240))
        )
        camera.set_local_pose(
            translation=np.array([0.08, 0.0, 0.2]),
            orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            camera_axes="world",
        )
        camera.set_clipping_range(near_distance=0.01, far_distance=20.0)
        imu = world.scene.add(
            IMUSensor(
                prim_path=body + "/IMU",
                name="imu",
                dt=dt,
                translation=np.array([0.0, 0.0, 0.15]),
            )
        )
        status, lidar = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/Lidar",
            parent=body,
            config="Example_Rotary_2D",
            translation=(0.0, 0.0, 0.25),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
            **{
                "omni:sensor:Core:nearRangeM": 0.05,
                "omni:sensor:Core:farRangeM": 10.0,
                "omni:sensor:Core:scanRateBaseHz": 10,
                "omni:sensor:Core:reportRateBaseHz": 3600,
                "omni:sensor:Core:azimuthErrorStd": 0.0,
            },
        )
        if not status:
            raise RuntimeError("RTX LiDAR 생성 실패")
        lidar_product = rep.create.render_product(lidar.GetPath(), (1, 1))
        world.reset()
        create_graph(camera.get_render_product_path(), lidar_product.path)
        rclpy.init()
        ros_started = True
        node = RobotInterface(camera)
        controller = DifferentialController(
            name="drive", wheel_radius=0.03, wheel_base=0.1125
        )
        steps = 0
        with (output / "odom.csv").open("w", newline="", encoding="utf-8") as stream:
            log = csv.writer(stream)
            log.writerow(["time_s", "x_m", "y_m", "z_m", "command_v", "command_w"])
            for step in range(args.steps):
                if not app.is_running() or not world.is_playing():
                    break
                began = time.monotonic()
                rclpy.spin_once(node, timeout_sec=0.0)
                velocity = node.command.current(time.monotonic())
                robot.apply_wheel_actions(controller.forward(command=list(velocity)))
                world.step(render=True)
                node.publish_state(chassis, imu, world.current_time)
                if step % 6 == 0:
                    log.writerow(
                        [world.current_time, *chassis.get_world_pose()[0], *velocity]
                    )
                steps += 1
                if not args.no_realtime:
                    time.sleep(max(0.0, dt - (time.monotonic() - began)))
        write_json(
            output / "summary.json",
            {
                "isaac_sim": "5.1.0",
                "steps": steps,
                "physics_dt_s": dt,
                "odom_source": "ground_truth",
                "chassis_prim": body,
            },
        )
        world.stop()
        print(f"ROS 2 결과: {output}", flush=True)
    finally:
        try:
            if node is not None:
                node.destroy_node()
            if ros_started:
                import rclpy

                rclpy.shutdown()
            if lidar_product is not None:
                lidar_product.destroy()
        finally:
            close_app(app)


if __name__ == "__main__":
    main()
