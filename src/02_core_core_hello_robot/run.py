"""Jetbot USD 참조와 Robot/WheeledRobot 관절 명령 비교 — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Jetbot USD 참조와 Robot/WheeledRobot 관절 명령 비교')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 600 steps)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--api", choices=["robot", "wheeled"], default="robot")
    parser.add_argument("--wheel-speeds", type=float, nargs=2, default=[4.0, 4.0], metavar=("LEFT", "RIGHT"))
    parser.add_argument("--asset", help="Jetbot USD override, absolute file path or URL")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 600
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    # isaac sim 시작
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        from isaacsim.core.api.robots import Robot
        # isaacsim의 core api 중 robot을 호출할 수 있는 API
        # USD scene에 있는 로봇을 감싸서 Joint 상태를 읽거나 제어할 수 있게함
        from isaacsim.core.utils.stage import add_reference_to_stage
        # USD 파일을 현재 scene에 연결하는 기능을 제공
        from isaacsim.core.utils.nucleus import get_assets_root_path
        # Isaac Sim Asset의 루트 경로를 찾기
        from isaacsim.core.utils.types import ArticulationAction
        # Isaac Sim에서 활용 가능한 다양한 명령 및 상태 변수들을 담는 자료형
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        # 로봇의 유형(type)별로 모듈들을 다 모아놓은 네임스페이스
        # 예를 들어서 WheeledRobot은 바퀴가 달린 로봇을 위한 모듈
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        world.scene.add_default_ground_plane()
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac 5.1 asset root unavailable; provide --asset /absolute/path/jetbot.usd")
        asset = args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        wheel_names = ["left_wheel_joint", "right_wheel_joint"]
        if args.api == "robot":
            # API를 robot이라고 사용한다면?
            add_reference_to_stage(usd_path=asset, prim_path="/World/Jetbot")
            # Prim을 Robot으로 사용
            robot = world.scene.add(Robot(prim_path="/World/Jetbot", name="jetbot"))
        else:
            # 그렇지 않다면 WheeledRobot으로 사용
            robot = world.scene.add(WheeledRobot(prim_path="/World/Jetbot", name="jetbot",
                wheel_dof_names=wheel_names, create_robot=True, usd_path=asset))
        print("DOF before reset:", robot.num_dof)
        world.reset()
        wheel_indices = np.array([robot.get_dof_index(name) for name in wheel_names])
        initial_position = robot.get_world_pose()[0].copy()
        print("DOF after reset:", robot.num_dof, "names:", robot.dof_names, "wheel indices:", wheel_indices)
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            if args.api == "robot":
                # API가 robot이면 robot.get_articulation_controller().apply_action()을 사용해서 바퀴 속도를 제어
                robot.get_articulation_controller().apply_action(ArticulationAction(
                    joint_velocities=np.array(args.wheel_speeds), joint_indices=wheel_indices))
            else:
                # API가 wheeled이면 robot.apply_wheel_actions() 함수를 사용해서 간단하게 바퀴 속도를 제어
                robot.apply_wheel_actions(ArticulationAction(joint_velocities=np.array(args.wheel_speeds)))
            world.step(render=not args.headless)
            if step % 120 == 0:
                print("step", step, "position_m", robot.get_world_pose()[0], "wheel_rad_s", robot.get_joint_velocities()[wheel_indices])
        final_position, orientation = robot.get_world_pose()
        result = {"api": args.api, "dof_names": robot.dof_names, "wheel_indices": wheel_indices.tolist(),
                  "command_rad_s": args.wheel_speeds, "displacement_m": (final_position-initial_position).tolist(),
                  "final_position_m": final_position.tolist(), "orientation_wxyz": orientation.tolist()}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
    finally:
        app.close()


if __name__ == "__main__":
    main()
