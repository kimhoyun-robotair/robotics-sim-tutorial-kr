"""Standalone Python: Jetbot → wheel velocity → physics step → pose CSV."""

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutorial_common.runtime import (
    add_common_arguments,
    close_app,
    asset_path,
    launch_app,
    output_directory,
    positive_float,
    positive_int,
    write_json,
)
from motion import motion_command


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--pattern", choices=["straight", "turn", "square"], default="square"
    )
    parser.add_argument("--steps", type=positive_int, default=2880, help="물리 step 수")
    parser.add_argument("--dt", type=positive_float, default=1 / 60)
    parser.add_argument("--speed", type=positive_float, default=0.10, help="m/s")
    parser.add_argument(
        "--side", type=positive_float, default=1.0, help="사각형 한 변 m"
    )
    parser.add_argument("--robot-usd", help="기본 Jetbot 대신 사용할 USD")
    parser.add_argument("--wheel-radius", type=positive_float, default=0.03)
    parser.add_argument("--wheel-base", type=positive_float, default=0.1125)
    parser.add_argument(
        "--wheel-joints", nargs=2, default=["left_wheel_joint", "right_wheel_joint"]
    )
    args = parser.parse_args()
    output = output_directory("01_mobile", args.output)
    app = launch_app(args.headless)
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.robot.wheeled_robots.controllers.differential_controller import (
            DifferentialController,
        )
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot

        # World는 Scene 등록과 reset을 관리한다. dt의 단위는 초이다.
        world = World(
            stage_units_in_meters=1.0, physics_dt=args.dt, rendering_dt=args.dt
        )
        world.scene.add_default_ground_plane()
        usd = args.robot_usd or asset_path("/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd")
        robot = world.scene.add(
            WheeledRobot(
                prim_path="/World/Robot",
                name="robot",
                wheel_dof_names=args.wheel_joints,
                create_robot=True,
                usd_path=usd,
                position=np.array([0.0, 0.0, 0.05]),
            )
        )
        controller = DifferentialController(
            name="drive",
            wheel_radius=args.wheel_radius,
            wheel_base=args.wheel_base,
        )
        world.reset()  # articulation의 physics handle이 준비된 다음 제어한다.
        for _ in range(60):
            world.step(render=not args.headless)
        initial, _ = robot.get_world_pose()
        completed = 0
        with (output / "pose.csv").open("w", newline="", encoding="utf-8") as stream:
            log = csv.writer(stream)
            log.writerow(
                [
                    "step",
                    "time_s",
                    "x_m",
                    "y_m",
                    "z_m",
                    "qw",
                    "qx",
                    "qy",
                    "qz",
                    "v_m_s",
                    "w_rad_s",
                ]
            )
            for step in range(args.steps):
                if not app.is_running():
                    break
                if not world.is_playing():
                    # GUI의 Stop/Pause 이후 새 실험은 다시 실행한다. 중간 reset으로 로그를 섞지 않는다.
                    break
                v, w = motion_command(
                    step * args.dt, args.pattern, args.speed, args.side
                )
                robot.apply_wheel_actions(controller.forward(command=[v, w]))
                world.step(render=not args.headless)
                position, orientation = (
                    robot.get_world_pose()
                )  # quaternion 순서: w, x, y, z
                if not np.isfinite(position).all():
                    raise RuntimeError("robot pose에 NaN/Inf가 발생했습니다.")
                log.writerow(
                    [step, (step + 1) * args.dt, *position, *orientation, v, w]
                )
                completed += 1
        robot.apply_wheel_actions(controller.forward(command=[0.0, 0.0]))
        final, _ = robot.get_world_pose()
        write_json(
            output / "summary.json",
            {
                "isaac_sim": "5.1.0",
                "execution_context": "standalone",
                "asset": usd,
                "pattern": args.pattern,
                "dt_s": args.dt,
                "steps": completed,
                "requested_steps": args.steps,
                "completed": completed == args.steps,
                "start_xyz_m": initial.tolist(),
                "end_xyz_m": final.tolist(),
                "displacement_xy_m": math.dist(initial[:2], final[:2]),
                "wheel_radius_m": args.wheel_radius,
                "wheel_base_m": args.wheel_base,
                "wheel_joints": args.wheel_joints,
            },
        )
        world.stop()
        print(f"주행 결과: {output}")
    finally:
        close_app(app)


if __name__ == "__main__":
    main()
