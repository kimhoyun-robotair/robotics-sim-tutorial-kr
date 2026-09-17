import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Core API Overview")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )

    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 120
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
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from isaacsim.core.prims import RigidPrim
        # RigidPrim은 지정한 경로의 강체들을 묶어 위치, 속도, 질량 등을 배열로 읽고 설정하는 API이다.
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics, PhysxSchema
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.

        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        physics = world.get_physics_context().prim_path
        scene = UsdPhysics.Scene.Get(stage, physics)
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)
        PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateEnableCCDAttr(True)
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        raw_cube = UsdGeom.Cube.Define(stage, "/World/RawCube")
        raw_cube.CreateSizeAttr(0.4)
        raw_cube.AddTranslateOp().Set(Gf.Vec3d(-0.5, 0, 2))
        # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
        UsdPhysics.RigidBodyAPI.Apply(raw_cube.GetPrim())
        # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
        UsdPhysics.CollisionAPI.Apply(raw_cube.GetPrim())
        UsdPhysics.MassAPI.Apply(raw_cube.GetPrim()).CreateMassAttr(1.0)
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        raw = world.scene.add(RigidPrim("/World/RawCube", name="raw"))
        wrapped = world.scene.add(
            DynamicCuboid(
                prim_path="/World/WrappedCube",
                name="wrapped",
                position=np.array([0.5, 0, 2]),
                size=0.4,
                mass=1.0,
            )
        )
        report = {
            str(p.GetPath()): p.GetAppliedSchemas()
            for p in (raw_cube.GetPrim(), stage.GetPrimAtPath("/World/WrappedCube"))
        }
        (output / "schemas.json").write_text(json.dumps(report, indent=2))
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "scene.usda"))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        with (output / "heights.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["step", "raw_z_m", "wrapped_z_m"])
            for i in count():
                if not app.is_running() or (args.steps is not None and i >= args.steps):
                    break
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
                writer.writerow(
                    [
                        i + 1,
                        float(raw.get_world_poses()[0][0, 2]),
                        float(wrapped.get_world_pose()[0][2]),
                    ]
                )
        print(
            "Scene registry:",
            world.scene.get_object("raw").name,
            world.scene.get_object("wrapped").name,
        )
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
