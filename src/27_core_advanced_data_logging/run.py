"""DataLogger로 Franka 목표 추종 기록과 action/scene 재생 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='DataLogger로 Franka 목표 추종 기록과 action/scene 재생')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 600)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--mode", choices=["record", "trajectory", "scene"], default="record")
    parser.add_argument("--input", type=Path, help="Previously recorded trajectory.json for replay")
    parser.add_argument("--amplitude", type=float, default=0.1, help="Target Y motion amplitude in meters")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 600
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
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget
        # FollowTarget은 로봇 팔이 따라갈 목표 Prim과 로봇을 구성하는 예제 Task이다.
        from isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller import RMPFlowController
        # RMPFlowController는 목표 말단 자세를 추종하도록 RMPflow 기반 관절 명령을 계산하는 예제 제어기이다.
        if args.mode != "record" and (args.input is None or not args.input.is_file()):
            raise ValueError("Replay requires --input pointing to a recorded trajectory.json")
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        task = FollowTarget(name="follow_for_logging")
        # 작업을 World에 등록하여 장면 구성과 관측값·초기화를 World와 함께 관리한다.
        world.add_task(task)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        params = task.get_params()
        robot = world.scene.get_object(params["robot_name"]["value"])
        target = world.scene.get_object(params["target_name"]["value"])
        # World의 데이터 로거를 얻어 step별 상태 기록과 저장에 사용한다.
        logger = world.get_data_logger()
        controller = RMPFlowController(name="follow", robot_articulation=robot)
        replay_errors = []

        def follow_target(step):
            target.set_world_pose(position=np.array([0.45, args.amplitude*np.sin(step/120), 0.45]))
            observation = task.get_observations()[target.name]
            action = controller.forward(target_end_effector_position=observation["position"],
                                        target_end_effector_orientation=observation["orientation"])
            # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
            robot.apply_action(action)
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)

        if args.mode == "record":
            def log_frame(tasks, scene):
                position, orientation = target.get_world_pose()
                # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
                return {"joint_positions": robot.get_joint_positions().tolist(),
                        "applied_joint_positions": robot.get_applied_action().joint_positions.tolist(),
                        "target_position": position.tolist(), "target_orientation": orientation.tolist()}
            logger.add_data_frame_logging_func(log_frame)
            logger.start()
            for step in range(sample_steps):
                if not app.is_running():
                    break
                follow_target(step)
            logger.pause()
            logger.save(log_path=str(output / "trajectory.json"))
        else:
            logger.load(log_path=str(args.input))
            frame_count = logger.get_num_of_data_frames()
            if frame_count == 0:
                raise ValueError("Input log has no frames")
            first = logger.get_data_frame(data_frame_index=0).data
            # 관절 위치 상태를 직접 설정한다. 물리 제어기의 목표 위치를 지정하는 호출과 구분된다.
            robot.set_joint_positions(np.array(first["joint_positions"]))
            replay_steps = min(args.steps, frame_count) if args.steps is not None else (min(sample_steps, frame_count) if args.headless else frame_count)
            for index in range(replay_steps):
                if not app.is_running():
                    break
                frame = logger.get_data_frame(data_frame_index=index)
                robot.apply_action(ArticulationAction(joint_positions=np.array(frame.data["applied_joint_positions"])))
                if args.mode == "scene":
                    target.set_world_pose(position=np.array(frame.data["target_position"]),
                                          orientation=np.array(frame.data["target_orientation"]))
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                error = float(np.linalg.norm(robot.get_joint_positions()-np.array(frame.data["joint_positions"])))
                replay_errors.append(error)
                if index % 120 == 0:
                    print("frame", index, "recorded_time_s", frame.current_time, "joint_state_L2_error", error)
        if not app.is_running():
            return
        result = {"mode": args.mode, "data_frames": logger.get_num_of_data_frames(),
                  "replayed_frames": len(replay_errors), "mean_joint_state_L2_error": float(np.mean(replay_errors)) if replay_errors else None,
                  "final_target_m": target.get_world_pose()[0].tolist()}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), "output=", output)
        step = sample_steps
        while args.steps is None and not args.headless and app.is_running():
            if args.mode == "record":
                follow_target(step)
                step += 1
            else:
                world.step(render=True)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
