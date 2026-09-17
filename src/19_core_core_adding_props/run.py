"""Rubik 에셋의 강체·충돌체·질량·반발 재질 실험 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Rubik 에셋의 강체·충돌체·질량·반발 재질 실험')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 360)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--physics", choices=["visual", "rigid", "mesh", "sphere"], default="sphere")
    parser.add_argument("--asset", help="Rubik USD override; default official Props/Rubiks_Cube/rubiks_cube.usd")
    parser.add_argument("--mass", type=float, default=0.1, help="Mass in kg")
    parser.add_argument("--restitution", type=float, default=0.8)
    parser.add_argument("--slope", type=float, default=10.0, help="Ground rotation around X in degrees")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 360
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from pxr import Usd, UsdGeom, UsdPhysics, UsdShade
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.prims import SingleRigidPrim, SingleXFormPrim
        # SingleRigidPrim은 하나의 강체 Prim을 감싸 자세와 속도 등의 물리 상태를 조작한다.
        # SingleXFormPrim은 하나의 USD Prim을 감싸 위치, 회전, 스케일을 조작한다.
        from isaacsim.core.utils.stage import add_reference_to_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        from isaacsim.core.utils.nucleus import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        # euler_angles_to_quat는 Euler 회전을 쿼터니언으로 변환한다. 기본 입력 단위는 라디안이다.
        if args.mass <= 0 or not 0 <= args.restitution <= 1:
            raise ValueError("--mass must be positive and --restitution must be in [0, 1]")
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        ground = world.scene.add_default_ground_plane()
        ground.set_world_pose(orientation=euler_angles_to_quat(np.array([args.slope, 0.0, 0.0]), degrees=True))
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset rubiks_cube.usd")
        asset = args.asset or asset_root + "/Isaac/Props/Rubiks_Cube/rubiks_cube.usd"
        root = add_reference_to_stage(usd_path=asset, prim_path="/World/Rubik")
        for prim in list(Usd.PrimRange(root)):
            if prim.IsInstance():
                # Prim의 instanceable 여부를 설정하여 참조한 자산의 인스턴싱 사용을 제어한다.
                prim.SetInstanceable(False)
        meshes = [prim for prim in Usd.PrimRange(root) if prim.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise RuntimeError(f"No Rubik meshes resolved from {asset}; check the 5.1 asset installation")
        # 비교 실험의 시작 조건을 명시한다. 참고 에셋에 있던 물리 스키마를 제거한다.
        for prim in Usd.PrimRange(root):
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                prim.RemoveAPI(UsdPhysics.CollisionAPI)
            if prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                prim.RemoveAPI(UsdPhysics.MeshCollisionAPI)
        material = UsdShade.Material.Define(world.stage, "/World/RubikPhysicsMaterial")
        physics_material = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        physics_material.CreateStaticFrictionAttr(0.5)
        physics_material.CreateDynamicFrictionAttr(0.4)
        physics_material.CreateRestitutionAttr(args.restitution)
        colliders = []
        if args.physics == "mesh":
            for mesh in meshes:
                # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
                UsdPhysics.CollisionAPI.Apply(mesh)
                UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr("convexHull")
                colliders.append(mesh)
        elif args.physics == "sphere":
            sphere = UsdGeom.Sphere.Define(world.stage, "/World/Rubik/PhysicsSphere")
            sphere.CreateRadiusAttr(0.07)
            sphere.MakeInvisible()
            UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
            colliders.append(sphere.GetPrim())
        for collider in colliders:
            # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
            UsdShade.MaterialBindingAPI.Apply(collider).Bind(material, materialPurpose="physics")
        if args.physics == "visual":
            # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
            prop = world.scene.add(SingleXFormPrim(prim_path="/World/Rubik", name="rubik", position=np.array([0.0, 0.0, 1.0])))
        else:
            # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
            UsdPhysics.RigidBodyAPI.Apply(root)
            UsdPhysics.MassAPI.Apply(root).CreateMassAttr(args.mass)
            prop = world.scene.add(SingleRigidPrim(prim_path="/World/Rubik", name="rubik", position=np.array([0.0, 0.0, 1.0])))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        # World가 사용하는 Stage의 루트 레이어를 USD 파일로 저장한다.
        world.stage.GetRootLayer().Export(str(output / "configured_scene.usda"))
        samples = []
        for step in range(sample_steps):
            if not app.is_running():
                return
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                return
            if step % 15 == 0:
                samples.append({"step": step, "position_m": prop.get_world_pose()[0].tolist()})
                if step % 60 == 0:
                    print(samples[-1])
        if not app.is_running():
            return
        result = {"physics": args.physics, "asset": asset, "colliders": [str(prim.GetPath()) for prim in colliders],
                  "mass_kg": args.mass, "restitution": args.restitution, "slope_deg": args.slope, "samples": samples}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print("output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
