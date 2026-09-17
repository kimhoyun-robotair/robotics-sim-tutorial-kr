"""Franka 집기와 놓기: 직접 정의한 Task와 내장 Task — Isaac Sim 5.1 standalone lesson."""
import argparse
from itertools import count
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Franka 집기와 놓기: 직접 정의한 Task와 내장 Task')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 1800)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--task", choices=["custom", "builtin"], default="custom")
    parser.add_argument("--target", type=float, nargs=3, default=[-0.3, -0.3, 0.02575], metavar=("X", "Y", "Z"))
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (1800 if args.headless else None)
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
        from isaacsim.robot.manipulators.examples.franka.tasks import PickPlace
        # PickPlace는 로봇 팔과 집을 물체를 구성하고 위치 등의 관측값을 제공하는 예제 Task이다.
        from isaacsim.robot.manipulators.examples.franka.controllers import PickPlaceController
        # PickPlaceController는 물체 접근·잡기·이동·놓기 단계를 진행하며 로봇의 관절 명령을 계산한다.
        from pick_task import LocalPickTask
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        task = (LocalPickTask(target=args.target) if args.task == "custom" else
                PickPlace(name="builtin_pick", target_position=np.array(args.target)))
        # 작업을 World에 등록하여 장면 구성과 관측값·초기화를 World와 함께 관리한다.
        world.add_task(task)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        params = task.get_params()
        robot = world.scene.get_object(params["robot_name"]["value"])
        cube = world.scene.get_object(params["cube_name"]["value"])
        controller = PickPlaceController(name="pick_place", gripper=robot.gripper, robot_articulation=robot)
        controller.reset()
        robot.gripper.set_joint_positions(robot.gripper.joint_opened_positions)
        completed_step = None
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            # 등록된 작업이 제공하는 로봇·물체·목표의 관측값을 읽어 제어기에 전달한다.
            observations = world.get_observations()
            if not controller.is_done():
                # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                robot.apply_action(controller.forward(
                    picking_position=observations[cube.name]["position"],
                    placing_position=observations[cube.name]["target_position"],
                    current_joint_positions=observations[robot.name]["joint_positions"]))
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                return
            if controller.is_done() and completed_step is None:
                completed_step = step
                print("Controller state machine finished at", step, "; checking actual cube pose separately")
            if step % 120 == 0:
                print("step", step, "cube_m", cube.get_world_pose()[0], "controller_done", controller.is_done())
            if completed_step is not None and step - completed_step >= 120:
                break
        if not app.is_running():
            return
        error = float(np.linalg.norm(cube.get_world_pose()[0] - np.array(args.target)))
        result = {"task": args.task, "controller_done": bool(controller.is_done()),
                  "cube_position_m": cube.get_world_pose()[0].tolist(), "target_m": args.target,
                  "cube_target_error_m": error, "within_3cm": error < 0.03}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
