import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot Simulation Snippets")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: GUI stays open (headless: 120)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument(
        "--control",
        choices=[
            "position",
            "single-position",
            "velocity",
            "single-velocity",
            "effort",
        ],
        default="position",
    )
    parser.add_argument("--usd", help="Optional local Franka Panda USD path")
    parser.add_argument(
        "--target",
        type=float,
        default=0.2,
        help="Position offset rad, velocity rad/s, or effort Nm",
    )
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (120 if args.headless else None)
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import csv
        import math
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
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from pxr import UsdLux, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.

        if not math.isfinite(args.target) or abs(args.target) > 0.5:
            raise ValueError(
                "Use a finite --target with magnitude <= 0.5 for this small-motion exercise"
            )
        root = get_assets_root_path() if not args.usd else ""
        if root is None:
            raise RuntimeError(
                "Isaac 5.1 assets unavailable; use --usd for a local Franka USD"
            )
        usd = args.usd or root + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        variants = {}
        for i in (1, 2):
            prim = add_reference_to_stage(usd, f"/World/Franka_{i}")
            variants[str(prim.GetPath())] = {
                name: prim.GetVariantSet(name).GetVariantNames()
                for name in prim.GetVariantSets().GetNames()
            }
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robots = world.scene.add(
            Articulation(
                "/World/Franka_[1-2]",
                name="frankas",
                positions=np.array([[-1, 0, 0], [1, 0, 0]]),
            )
        )
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        if not robots.is_physics_handle_valid():
            raise RuntimeError("Franka articulation initialization failed")
        names = [f"panda_joint{i}" for i in range(1, 8)] + [
            "panda_finger_joint1",
            "panda_finger_joint2",
        ]
        missing = set(names) - set(robots.dof_names)
        if missing:
            raise RuntimeError(f"Franka asset has different joints: {sorted(missing)}")
        home = np.array([[0, -0.4, 0, -1.8, 0, 1.4, 0.5, 0.04, 0.04]] * 2)
        robots.set_joint_positions(home, joint_names=names)
        controlled = (
            ["panda_joint2"] if args.control.startswith("single") else names[:7]
        )
        if args.control in ("velocity", "single-velocity"):
            # 관절 제어기의 stiffness·damping 계수를 설정하여 목표 추종 응답을 조절한다.
            robots.set_gains(
                kps=np.zeros((2, len(controlled))),
                kds=np.full((2, len(controlled)), 20.0),
                joint_names=controlled,
            )
        elif args.control == "effort":
            controlled = ["panda_joint2"]
            robots.set_gains(
                kps=np.zeros((2, 1)), kds=np.zeros((2, 1)), joint_names=controlled
            )
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        report = {
            "count": robots.count,
            "num_dof": robots.num_dof,
            "num_joints": robots.num_joints,
            "dof_names": robots.dof_names,
            "limits": robots.get_dof_limits().tolist(),
            "variants": variants,
            "control": args.control,
            "controlled_joints": controlled,
            "physics_joint_prims": [
                str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)
            ],
        }
        (output / "robot_info.json").write_text(json.dumps(report, indent=2))
        with (output / "states.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                ["step", "robot", "positions", "velocities", "applied_efforts"]
            )
            for step in count():
                if not app.is_running() or (step_limit is not None and step >= step_limit):
                    break
                if args.control in ("position", "single-position"):
                    targets = np.array(
                        [
                            [
                                home[row, names.index(name)]
                                + args.target * math.sin(step / 60)
                                for name in controlled
                            ]
                            for row in range(2)
                        ]
                    )
                    # 관절 제어기가 추종할 목표 위치를 설정한다. 현재 관절 상태를 즉시 바꾸는 호출은 아니다.
                    robots.set_joint_position_targets(targets, joint_names=controlled)
                elif args.control in ("velocity", "single-velocity"):
                    # 관절 제어기가 추종할 목표 속도를 설정한다.
                    robots.set_joint_velocity_targets(
                        np.full((2, len(controlled)), args.target),
                        joint_names=controlled,
                    )
                else:
                    # 관절에 적용할 effort를 설정한다. 회전 관절에서는 토크 명령이다.
                    robots.set_joint_efforts(
                        np.full((2, 1), args.target), joint_names=controlled
                    )
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                q = robots.get_joint_positions()
                qd = robots.get_joint_velocities()
                efforts = robots.get_applied_joint_efforts()
                for row in range(2):
                    writer.writerow(
                        [
                            step + 1,
                            row,
                            json.dumps(q[row].tolist()),
                            json.dumps(qd[row].tolist()),
                            json.dumps(efforts[row].tolist()),
                        ]
                    )
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
