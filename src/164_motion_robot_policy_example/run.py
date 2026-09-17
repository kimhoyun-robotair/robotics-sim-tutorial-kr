"""Run genuine installed H1 or Spot policies with a timed velocity sequence."""
import argparse
from itertools import count
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", choices=("h1", "spot"), default="spot")
    parser.add_argument("--robots", type=int, default=1)
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 2000")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output" / "trajectory.csv")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 2000
    if (args.steps is not None and args.steps < 2) or not 1 <= args.robots <= 10:
        parser.error("steps >= 2 and 1 <= robots <= 10 are required")
    if args.output.exists():
        parser.error("Output exists; choose another --output")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy, SpotFlatTerrainPolicy
        # H1FlatTerrainPolicy는 H1 로봇의 평지 보행 정책을 불러오고 관측값으로부터 제어 명령을 계산한다.
        # SpotFlatTerrainPolicy는 Spot 로봇의 평지 보행 정책을 실행하는 예제 클래스이다.

        dt = 0.005 if args.robot == "h1" else 0.002
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=dt, rendering_dt=0.02)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        robot_type = H1FlatTerrainPolicy if args.robot == "h1" else SpotFlatTerrainPolicy
        robots = [
            robot_type(
                prim_path=f"/World/Robot_{i}", name=f"robot_{i}",
                position=np.array([0.0, i * 2.0, 1.05 if args.robot == "h1" else 0.8]),
            )
            for i in range(args.robots)
        ]
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        initialized = False
        command = np.zeros(3)

        def control(step_size: float) -> None:
            nonlocal initialized
            if not initialized:
                for robot in robots:
                    robot.initialize()
                initialized = True
            else:
                for robot in robots:
                    # 보행 정책에 물리 시간 간격과 이동 명령을 전달하여 이번 step의 로봇 제어를 계산한다.
                    robot.forward(step_size, command)

        # 물리 step마다 실행할 콜백을 등록한다. 콜백의 시간 간격으로 제어 계산을 맞출 수 있다.
        world.add_physics_callback("policy_sequence", control)
        with args.output.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "robot", "vx_command", "vy_command", "yaw_command", "x", "y", "z"])
            for step in count():
                if args.steps is not None and step >= args.steps:
                    break
                if not app.is_running():
                    break
                phase = int(step * dt / 2) % 3
                command[:] = [(0.4, 0, 0), (0.3, 0, 0.4), (0, 0, 0)][phase]
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=False)
                if not args.headless and step % round(0.02 / dt) == 0:
                    world.render()
                if not app.is_running():
                    break
                if step % round(0.1 / dt) == 0:
                    for i, robot in enumerate(robots):
                        position, _ = robot.robot.get_world_pose()
                        writer.writerow([step * dt, i, *command.tolist(), *position.tolist()])
            if app.is_running():
                for robot in robots:
                    print(robot.robot.name, "final world pose:", robot.robot.get_world_pose())
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
