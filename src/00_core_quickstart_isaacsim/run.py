"""Compare visual geometry, rigid bodies, and collision shapes in Isaac Sim 5.1."""

import argparse
from itertools import count
import csv
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 240 steps)"
    )
    parser.add_argument(
        "--height", type=float, default=1.5, help="Initial cube center height in metres"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; an existing directory is rejected",
    )
    args = parser.parse_args()
    if (args.steps is not None and args.steps < 1) or not 0.3 <= args.height <= 10.0:
        parser.error(
            "--steps must be positive and --height must be between 0.3 and 10 metres"
        )
    if args.steps is None and args.headless:
        args.steps = 240
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)

    from isaacsim import SimulationApp
    # SimulationApp은 Python 코드에서 Isaac Sim을 시작하고, Frame 갱신에 들어가고, 종료까지 지원하는 class이다.
    # 기본적으로 from isaacsim import SimulationApp를 통해 import 가능하며, SimulationApp을 생성할 때 headless 모드 여부를 설정할 수 있다.
    # 예를 들어서 다음과 같이 작성한다면
    # from isaacsim import SimulationApp
    # app = SimulationApp({"headless": False})
    # for _ in range(100):
    #     app.update()
    # app.close()
    # 이러면 100프레임 동안 isaac sim이 실행이 되고 그 다음 종료된다.

    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Isaac Sim에서 열려있는 Stage (객체, 조명 등이 들어있는 USD Scene 전체)를 가져오는데 사용한다.
        # stage = omni.usd.get_context().get_stage()
        # 이렇게 가져온 stage에 다양한 객체나 조명 등을 추가할 수 있다.
        from isaacsim.core.api import World
        # isaacsim.core.api.World는 Stage 내부 객체들을 관리/초기화/물리+렌더링 부여를 진행하는 클래스이다.
        from isaacsim.core.api.objects import DynamicCuboid, VisualCuboid
        # isaacsim.core.api.objects는 크기, 위치, 색상 등을 전달해서 기본 도형을 쉽게 만드는 클래스들을 제공한다.
        # 이중에 DynamicCuboid는 강체(rigid body)+충돌이 적용된 큐브이며
        # VisualCuboid는 외형만 존재하는 큐브로 물리법칙이 부여되지 않은 큐브이다.
        from isaacsim.core.prims import GeometryPrim, RigidPrim, XFormPrim
        # isaacsim.core.prims는 prim을 다루기 위한 API이다.
        # prim은 USD Scene 안의 객체 단위이다.
        # 이 API는 경로를 지정한 Prim을 조작할 수 있는 기능을 제공하게 된다.
        # XFormPrim은 위치, 회전, 스케일을 조작하며
        # RigidPrim은 질량, 속도 등 강체의 속성을 조작하고
        # GeometryPrim은 형상과 충돌 등의 속성을 조작한다.
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        # isaacsim.core.utils.rotations은 회전을 다루기 위한 API이다.
        # euler_angles_to_quat는 말 그대로 euler angle을 쿼터니언으로 변환한다.
        # 기본 입력 단위는 라디안으로 주어진다.
        from isaacsim.core.utils.viewports import set_camera_view
        # isaacsim.core.utils.viewports는 장면을 바라보는 시점을 설정하기 위한 API이다.
        from pxr import Gf, UsdGeom, UsdLux
        # pxr은 USD를 직접 다루는 OpenUSD 라이브러리의 Python Binding이다.
        # 이중에서 Gf는 USD의 위치, 색상에 사용할 벡터 값을
        # UsdGeom은 큐브 같은 USD 형상의 위치, 회전, 스케일
        # UsdLux는 조명 USD를 다룬다.

        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 여기서는 단위계를 m를 사용하고, 물리 및 렌더링 시간 간격을 60분의 1초로 설정한다는 뜻이다.
        # 아래 world.reset(), world.step(render=True)는 각각 초기화와 시뮬레이션 진행을 의미하는 함수들이다.
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1000)
        set_camera_view(eye=[5.0, 5.0, 4.0], target=[0.0, 0.0, 0.8])
        # 카메라를 eye 위치에 두고, target 지점을 바라보는 식으로 설정가능하다.

        # 외형만 존재하는 큐브를 생성하고, 그걸 USD Scene에 등록한다.
        # 그리고 뒤에 조작이 편하라고 visual이라는 이름의 파이썬 변수에 참조를 할당한다.
        visual = world.scene.add(
            VisualCuboid(
                prim_path="/World/Visual",
                name="visual",
                position=np.array([-1.0, 0.0, args.height]),
                size=0.3,
                color=np.array([1.0, 1.0, 0.0]),
            )
        )

        # 이번에는 먼저 외형만 존재하는 큐브를 생성하고
        VisualCuboid(
            prim_path="/World/RigidOnly",
            name="rigid_geometry",
            position=np.array([0.0, 0.0, args.height]),
            size=0.3,
            color=np.array([1.0, 0.2, 0.2]),
        )
        # 거기에 강체 속성을 할당해서 scene에 추가하고, rigid_only라는 이름의 변수로 저장한다.
        rigid_only = world.scene.add(
            RigidPrim(
                "/World/RigidOnly",
                name="rigid_only",
                masses=np.array([1.0]),
            )
        )
        # 이것 또한 마찬가지이다.
        VisualCuboid(
            prim_path="/World/Converted",
            name="converted_geometry",
            position=np.array([1.0, 0.0, args.height]),
            size=0.3,
            color=np.array([0.0, 1.0, 1.0]),
        ) # 큐브를 먼저 생성하고
        converted = world.scene.add(
            RigidPrim("/World/Converted", name="converted", masses=np.array([1.0]))
        ) # 같은 큐브에 강체 속성을 부여한다.
        GeometryPrim("/World/Converted").apply_collision_apis() # 이후 거기에 충돌 속성까지 부여한다.

        # 이번에는 DynamicCuboid를 통해서 
        # 한번에 큐브 + 강체 + 충돌 속성을 부여한다.
        dynamic = world.scene.add(
            DynamicCuboid(
                prim_path="/World/Dynamic",
                name="dynamic",
                position=np.array([2.0, 0.0, args.height]),
                size=0.3,
                mass=1.0,
                color=np.array([0.1, 0.4, 1.0]),
            )
        )

        # 이 코드는 큐브를 직접 정의하고
        raw = UsdGeom.Cube.Define(stage, "/World/RawUsd")
        # 큐브의 크기, 색상, 위치(병진+회전), 스케일을 직접 정의하는 코드이다.
        raw.CreateSizeAttr(0.3)
        raw.CreateDisplayColorAttr([Gf.Vec3f(0.7, 0.3, 0.9)])
        raw.AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 1.0))
        raw.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, 45.0))
        raw.AddScaleOp().Set(Gf.Vec3f(1.0, 1.5, 0.5))

        # 이거는 Prim 이름에서 짐작이 가능하겠지만
        # 위에 정의한 visual이랑 가리키는 동일한 큐브를 조작하는 코드이다.
        # 오해하면 안되는건 USD scene에 /World/Visual 큐브는 하나이다.
        # 단지 파이썬에서 visual이라는 변수랑 core_transform이라는 변수로 2가지 방식으로 접근해서
        # 조작하는 것 뿐이다.
        core_transform = XFormPrim("/World/Visual", name="visual_transform")
        core_transform.set_world_poses(
            positions=np.array([[-1.0, 0.0, args.height]]),
            orientations=np.array(
                [euler_angles_to_quat(np.array([0.0, 0.0, np.pi / 4]))]
            ),
        )
        core_transform.set_local_scales(np.array([[1.0, 1.5, 0.5]]))
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "initial_scene.usda"))
        world.reset()
        with (output / "heights.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "step",
                    "time_s",
                    "visual_z_m",
                    "rigid_only_z_m",
                    "converted_z_m",
                    "dynamic_z_m",
                ]
            )
            for step in count():
                if not app.is_running() or (args.steps is not None and step >= args.steps):
                    break
                world.step(render=not args.headless)
                heights = [
                    float(visual.get_world_pose()[0][2]),
                    float(rigid_only.get_world_poses()[0][0, 2]),
                    float(converted.get_world_poses()[0][0, 2]),
                    float(dynamic.get_world_pose()[0][2]),
                ]
                writer.writerow([step + 1, (step + 1) / 60, *heights])
                if step % 60 == 0 or (args.steps is not None and step == args.steps - 1):
                    print(
                        f"step={step + 1}: z(visual, rigid-only, converted, dynamic)={heights}"
                    )
        print(f"Scene and measured heights: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
