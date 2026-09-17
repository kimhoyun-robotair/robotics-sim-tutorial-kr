"""직접 작성한 차동구동 제어기와 목표 위치 피드백 비교 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='직접 작성한 차동구동 제어기와 목표 위치 피드백 비교')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 900)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--controller", choices=["custom", "differential", "pose"], default="pose")
    parser.add_argument("--linear", type=float, default=0.2, help="Forward velocity m/s")
    parser.add_argument("--angular", type=float, default=0.785398, help="Yaw velocity rad/s (open loop)")
    parser.add_argument("--goal", type=float, nargs=2, default=[0.8, 0.8], metavar=("X", "Y"))
    parser.add_argument("--asset", help="Jetbot USD override")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 900
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
        from isaacsim.core.api.controllers import BaseController
        # BaseController는 관측값으로부터 제어 명령을 계산하는 사용자 제어기의 기본 클래스이다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.core.utils.nucleus import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.robot.wheeled_robots.robots import WheeledRobot
        # WheeledRobot은 바퀴 관절을 지정해 이동 로봇을 구성하고 바퀴에 제어 명령을 적용하는 클래스이다.
        from isaacsim.robot.wheeled_robots.controllers import DifferentialController, WheelBasePoseController
        # DifferentialController는 선속도와 회전 각속도를 좌우 바퀴 속도로 변환하는 차동 구동 제어기이다.
        # WheelBasePoseController는 현재 자세와 목표 위치를 이용해 하위 바퀴 제어기에 전달할 이동 명령을 계산한다.
        class UnicycleController(BaseController):
            def __init__(self):
                super().__init__(name="local_unicycle")
                self.radius = 0.03
                self.track = 0.1125
            def forward(self, command):
                linear, angular = command
                left = (linear - angular * self.track / 2) / self.radius
                right = (linear + angular * self.track / 2) / self.radius
                return ArticulationAction(joint_velocities=np.array([left, right]))
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset jetbot.usd")
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(WheeledRobot(prim_path="/World/Jetbot", name="jetbot",
            wheel_dof_names=["left_wheel_joint", "right_wheel_joint"], create_robot=True,
            usd_path=args.asset or asset_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        custom = UnicycleController()
        differential = DifferentialController(name="differential", wheel_radius=0.03, wheel_base=0.1125)
        pose = WheelBasePoseController(name="pose", open_loop_wheel_controller=differential, is_holonomic=False)
        command = np.array([args.linear, args.angular])
        print("Custom wheel targets rad/s:", custom.forward(command).joint_velocities)
        print("Built-in wheel targets rad/s:", differential.forward(command).joint_velocities)
        goal = np.array([*args.goal, 0.0])
        def drive_robot():
            # 로봇의 월드 위치와 회전 쿼터니언을 읽는다.
            position, orientation = robot.get_world_pose()
            if args.controller == "pose":
                action = pose.forward(start_position=position, start_orientation=orientation,
                                      goal_position=goal, lateral_velocity=abs(args.linear), position_tol=0.04)
            elif args.controller == "custom":
                action = custom.forward(command)
            else:
                action = differential.forward(command)
            # 바퀴에 해당하는 관절에 제어 명령을 적용한다.
            robot.apply_wheel_actions(action)
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)

        trajectory = []
        final_position = robot.get_world_pose()[0]
        for step in range(sample_steps):
            if not app.is_running():
                return
            drive_robot()
            if not app.is_running():
                return
            final_position = robot.get_world_pose()[0]
            if step % 60 == 0:
                position = final_position
                trajectory.append({"step": step, "position_m": position.tolist(), "goal_error_m": float(np.linalg.norm(position[:2]-goal[:2]))})
                print(trajectory[-1])
        result = {"controller": args.controller, "goal_m": goal.tolist(), "samples": trajectory,
                  "final_goal_error_m": float(np.linalg.norm(final_position[:2]-goal[:2]))}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print("output=", output)
        while args.steps is None and not args.headless and app.is_running():
            drive_robot()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
