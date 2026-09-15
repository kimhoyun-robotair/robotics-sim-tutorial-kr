"""Inspect Franka and Nova Carter, then alternate stopped and moving phases."""

import argparse
from itertools import count
import csv
from datetime import datetime
import json
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Positive step limit; omitted: keep GUI open (headless: 480 steps)",
    )
    parser.add_argument(
        "--wheel-speed", type=float, default=1.0, help="Wheel velocity target, rad/s"
    )
    parser.add_argument("--arm-usd", help="Override Franka USD path or URL")
    parser.add_argument("--car-usd", help="Override Nova Carter USD path or URL")
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; an existing directory is rejected",
    )
    args = parser.parse_args()
    if (args.steps is not None and args.steps < 1) or not math.isfinite(args.wheel_speed):
        parser.error("--steps must be positive and --wheel-speed must be finite")
    if args.steps is None and args.headless:
        args.steps = 480
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.prims import Articulation
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.viewports import set_camera_view
        from isaacsim.storage.native import get_assets_root_path
        from pxr import UsdLux

        root = get_assets_root_path() if not (args.arm_usd and args.car_usd) else ""
        if root is None:
            raise RuntimeError(
                "Isaac assets unavailable; configure the 5.1 asset root or provide both --arm-usd and --car-usd."
            )
        arm_usd = (
            args.arm_usd or root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        )
        car_usd = (
            args.car_usd or root + "/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd"
        )
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        UsdLux.DistantLight.Define(
            omni.usd.get_context().get_stage(), "/World/Light"
        ).CreateIntensityAttr(1500)
        add_reference_to_stage(usd_path=arm_usd, prim_path="/World/Arm")
        add_reference_to_stage(usd_path=car_usd, prim_path="/World/Car")
        arm = world.scene.add(
            Articulation(
                "/World/Arm", name="arm", positions=np.array([[0.0, 1.2, 0.0]])
            )
        )
        car = world.scene.add(
            Articulation(
                "/World/Car", name="car", positions=np.array([[0.0, -1.2, 0.0]])
            )
        )
        set_camera_view(eye=[5.0, 4.0, 3.0], target=[0.0, 0.0, 0.7])
        world.reset()

        description = {}
        for label, robot in (("arm", arm), ("car", car)):
            if not robot.is_physics_handle_valid():
                raise RuntimeError(
                    f"{label} articulation did not initialize; verify its USD dependencies."
                )
            description[label] = {
                "num_joints": robot.num_joints,
                "num_dof": robot.num_dof,
                "dof_names": list(robot.dof_names),
                "limits": robot.get_dof_limits().tolist(),
                "initial_positions": robot.get_joint_positions().tolist(),
            }
        (output / "joint_info.json").write_text(
            json.dumps(description, indent=2), encoding="utf-8"
        )
        print(json.dumps(description, indent=2))
        arm_names = [f"panda_joint{i}" for i in range(1, 8)] + [
            "panda_finger_joint1",
            "panda_finger_joint2",
        ]
        wheel_names = ["joint_wheel_left", "joint_wheel_right"]
        for robot, names in ((arm, arm_names), (car, wheel_names)):
            missing = set(names) - set(robot.dof_names)
            if missing:
                raise RuntimeError(
                    f"Asset has unexpected joints: missing {sorted(missing)}; see joint_info.json."
                )
        home = np.array([[0.0, -0.4, 0.0, -1.8, 0.0, 1.4, 0.5, 0.04, 0.04]])
        moved = np.array([[-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04]])
        previous_phase = -1
        with (output / "states.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                ["step", "phase", "time_s", "car_x_m", "car_y_m", "arm_q", "car_q"]
            )
            for step in count():
                if not app.is_running() or (args.steps is not None and step >= args.steps):
                    break
                phase = (step // 120) % 4 if args.steps is None else min(3, 4 * step // args.steps)
                if phase != previous_phase:
                    arm.set_joint_positions(
                        moved if phase in (1, 3) else home, joint_names=arm_names
                    )
                    previous_phase = phase
                    print(
                        f"phase={phase}: {'moving' if phase in (1, 3) else 'stopped'}"
                    )
                speed = args.wheel_speed if phase in (1, 3) else 0.0
                car.set_joint_velocity_targets(
                    np.array([[speed, speed]]), joint_names=wheel_names
                )
                world.step(render=not args.headless)
                car_position = car.get_world_poses()[0][0]
                arm_q = arm.get_joint_positions()[0].tolist()
                car_q = car.get_joint_positions()[0].tolist()
                writer.writerow(
                    [
                        step + 1,
                        phase,
                        (step + 1) / 60,
                        float(car_position[0]),
                        float(car_position[1]),
                        json.dumps(arm_q),
                        json.dumps(car_q),
                    ]
                )
                if phase == 3 and step % 30 == 0:
                    print(f"car joint positions: {car_q}")
        print(f"Measured joint properties and state trace: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
