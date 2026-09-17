"""독립 상태와 좌표 offset으로 여러 로봇 작업 확장 — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='독립 상태와 좌표 offset으로 여러 로봇 작업 확장')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 2400)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--retreat-steps", type=int, default=200, help="Backward motion steps before picking")
    parser.add_argument("--asset", help="Jetbot USD override")

    parser.add_argument("--tasks", type=int, default=3, help="Number of independent Jetbot/Franka pairs")
    parser.add_argument("--spacing", type=float, default=2.0, help="Lane spacing in meters")
    parser.add_argument("--seed", type=int, default=7, help="Reproducible target randomization")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (2400 if args.headless else None)
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.nucleus import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.robot.manipulators.examples.franka.controllers import PickPlaceController
        # PickPlaceController는 물체 접근·잡기·이동·놓기 단계를 진행하며 로봇의 관절 명령을 계산한다.
        from isaacsim.robot.wheeled_robots.controllers import DifferentialController, WheelBasePoseController
        # DifferentialController는 선속도와 회전 각속도를 좌우 바퀴 속도로 변환하는 차동 구동 제어기이다.
        # WheelBasePoseController는 현재 자세와 목표 위치를 이용해 하위 바퀴 제어기에 전달할 이동 명령을 계산한다.
        from handover_task import HandoverTask
        if args.retreat_steps < 1:
            raise ValueError("--retreat-steps must be positive")
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset jetbot.usd")
        asset = args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        if args.tasks < 1 or args.spacing < 1.5:
            raise ValueError("--tasks must be positive; --spacing must be at least 1.5 m")
        rng = np.random.default_rng(args.seed)
        tasks = [HandoverTask(name=f"lane_{index}", jetbot_asset=asset,
            offset=np.array([0.0, (index - (args.tasks-1)/2) * args.spacing, 0.0]),
            goal_x=float(rng.uniform(1.2, 1.6)), retreat_steps=args.retreat_steps) for index in range(args.tasks)]
        for task in tasks:
            # 작업을 World에 등록하여 장면 구성과 관측값·초기화를 World와 함께 관리한다.
            world.add_task(task)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        controllers = []
        for task in tasks:
            drive = WheelBasePoseController(name=task.name + "_pose", open_loop_wheel_controller=
                DifferentialController(name=task.name + "_drive", wheel_radius=0.03, wheel_base=0.1125))
            pick = PickPlaceController(name=task.name + "_pick_control", gripper=task.franka.gripper,
                robot_articulation=task.franka,
                events_dt=[0.008, 0.002, 0.5, 0.1, 0.05, 0.05, 0.0025, 1.0, 0.008, 0.08])
            drive.reset()
            pick.reset()
            controllers.append((drive, pick))
            print("task", task.name, "parameters", task.get_params())
        completed_step = None
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            # 등록된 작업이 제공하는 로봇·물체·목표의 관측값을 읽어 제어기에 전달한다.
            observations = world.get_observations()
            for task, (drive, pick) in zip(tasks, controllers):
                state = observations[task.name + "_event"]
                if state == 0:
                    pose = observations[task.jetbot.name]
                    task.jetbot.apply_wheel_actions(drive.forward(start_position=pose["position"],
                        start_orientation=pose["orientation"], goal_position=pose["goal_position"]))
                elif state == 1:
                    task.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=np.array([-8.0, -8.0])))
                else:
                    task.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=np.zeros(2)))
                    if not pick.is_done():
                        cube = observations[task.cube.name]
                        task.franka.apply_action(pick.forward(picking_position=cube["position"],
                            placing_position=cube["target_position"],
                            current_joint_positions=observations[task.franka.name]["joint_positions"]))
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if step % 120 == 0:
                print("step", step, "events", {task.name: task.event for task in tasks})
            if args.steps is None and not args.headless:
                if completed_step is None and all(pick.is_done() for _, pick in controllers):
                    completed_step = step
                if completed_step is not None and step - completed_step >= 120:
                    break
        if not app.is_running():
            return
        results = []
        for task, (_, pick) in zip(tasks, controllers):
            cube = task.get_observations()[task.cube.name]
            error = float(np.linalg.norm(cube["position"] - cube["target_position"]))
            results.append({"task": task.name, "event": task.event, "controller_done": bool(pick.is_done()),
                "jetbot_position_m": task.jetbot.get_world_pose()[0].tolist(), "cube_position_m": cube["position"].tolist(),
                "target_m": cube["target_position"].tolist(), "cube_target_error_m": error, "within_3cm": error < 0.03})
        (output / "result.json").write_text(json.dumps(results, indent=2))
        print(json.dumps(results), "output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
