"""Run the installed H1 policy and record its real observation/action contract."""
import argparse
from itertools import count
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 1200")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--speed", type=float, default=0.5, help="Body-frame forward command, m/s")
    parser.add_argument("--policy", type=Path, help="An exported H1 TorchScript policy with the same 69/19 contract")
    parser.add_argument("--environment", type=Path, help="Matching H1 env.yaml")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 1200
    if (args.steps is not None and args.steps < 2) or not 0 <= args.speed <= 1:
        parser.error("steps >= 2 and 0 <= speed <= 1 are required")
    if bool(args.policy) != bool(args.environment):
        parser.error("--policy and --environment must be provided together")
    for path in (args.policy, args.environment):
        if path is not None and not path.is_file():
            parser.error(f"Missing file: {path}")
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "contract.json"
    trace_path = args.output / "trace.csv"
    if report_path.exists() or trace_path.exists():
        parser.error("Output files already exist; choose a fresh --output directory")

    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy
        # H1FlatTerrainPolicy는 H1 로봇의 평지 보행 정책을 불러오고 관측값으로부터 제어 명령을 계산한다.

        class InspectedH1(H1FlatTerrainPolicy):
            first_observation = None

            def _compute_observation(self, command):
                observation = super()._compute_observation(command)
                if self.first_observation is None:
                    self.first_observation = observation.copy()
                return observation

        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=0.005, rendering_dt=0.04)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        controller = InspectedH1(prim_path="/World/H1", position=np.array([0.0, 0.0, 1.05]))
        if args.policy:
            controller.load_policy(str(args.policy.resolve()), str(args.environment.resolve()))
        world.set_simulation_dt(physics_dt=controller._dt, rendering_dt=8 * controller._dt)
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        joint_names = []
        position, _ = controller.robot.get_world_pose()
        first_step = True
        command = np.array([args.speed, 0.0, 0.0])

        def control(dt: float) -> None:
            nonlocal first_step
            if first_step:
                controller.initialize()
                first_step = False
            else:
                controller.forward(dt, command)

        # 물리 step마다 실행할 콜백을 등록한다. 콜백의 시간 간격으로 제어 계산을 맞출 수 있다.
        world.add_physics_callback("h1_policy", control)
        with trace_path.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["physics_step", "x_m", "y_m", "z_m", "command_vx_m_s"])
            for step in count():
                if args.steps is not None and step >= args.steps:
                    break
                if not app.is_running():
                    break
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=False)
                if not args.headless and step % 8 == 0:
                    world.render()
                if not app.is_running():
                    break
                joint_names = controller.robot.dof_names
                position, _ = controller.robot.get_world_pose()
                if not np.isfinite(position).all():
                    raise RuntimeError("Robot position became non-finite")
                writer.writerow([step, *position.tolist(), args.speed])
        if controller.first_observation is None:
            if not app.is_running():
                print("Window closed before the first policy inference; trace retained.")
                return
            raise RuntimeError("No policy inference took place")
        report = {
            "joint_names": joint_names,
            "physics_dt": controller._dt,
            "decimation": controller._decimation,
            "policy_hz": 1 / (controller._dt * controller._decimation),
            "default_joint_positions": controller.default_pos.tolist(),
            "first_observation": controller.first_observation.tolist(),
            "last_action": controller.action.tolist(),
            "final_position": position.tolist(),
        }
        with report_path.open("x") as stream:
            json.dump(report, stream, indent=2)
        print(json.dumps(report, indent=2))
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
