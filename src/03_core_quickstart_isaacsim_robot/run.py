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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    # isaac sim 시작
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.prims import Articulation
        # Articulation은 관절로 연결된 로봇들을 묶어 관절 상태와 제어 목표를 배열로 다룬다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.core.utils.viewports import set_camera_view
        # set_camera_view는 뷰포트 카메라를 eye 위치에 두고 target 지점을 바라보도록 설정한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from pxr import UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.

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
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(
            omni.usd.get_context().get_stage(), "/World/Light"
        ).CreateIntensityAttr(1500)
        add_reference_to_stage(usd_path=arm_usd, prim_path="/World/Arm")
        add_reference_to_stage(usd_path=car_usd, prim_path="/World/Car")
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
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
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()

        description = {}
        for label, robot in (("arm", arm), ("car", car)):
            if not robot.is_physics_handle_valid():
                raise RuntimeError(
                    f"{label} articulation did not initialize; verify its USD dependencies."
                )
            # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
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
        arm_indices = [arm.get_dof_index(name) for name in arm_names]
        wheel_indices = [car.get_dof_index(name) for name in wheel_names]
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
                        moved if phase in (1, 3) else home, joint_indices=arm_indices
                    )
                    previous_phase = phase
                    print(
                        f"phase={phase}: {'moving' if phase in (1, 3) else 'stopped'}"
                    )
                speed = args.wheel_speed if phase in (1, 3) else 0.0
                car.set_joint_velocity_targets(
                    np.array([[speed, speed]]), joint_indices=wheel_indices
                )
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
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
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
