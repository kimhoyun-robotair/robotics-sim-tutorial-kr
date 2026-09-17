import argparse
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Scene Setup Snippets")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None,
        help="Positive physics step limit; omitted: GUI stays open (headless: 240)",
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--mass", type=float, default=1.0)
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 240
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        # carb는 Kit 기반 실행 환경의 설정·로그 등 공통 기능을 제공하는 Carbonite 바인딩이다.
        import numpy as np
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.api.objects import DynamicCuboid
        # DynamicCuboid는 큐브 형상에 강체와 충돌 속성을 함께 부여하므로 중력과 접촉에 반응한다.
        from isaacsim.core.api.materials import PhysicsMaterial
        # PhysicsMaterial은 접촉 시 사용할 정지·동마찰과 반발 계수를 설정하는 물리 재질이다.
        from isaacsim.core.prims import RigidPrim
        # RigidPrim은 지정한 경로의 강체들을 묶어 위치, 속도, 질량 등을 배열로 읽고 설정하는 API이다.
        from isaacsim.core.utils.semantics import add_labels
        # add_labels는 Prim에 의미 라벨을 부여하여 합성 데이터에서 객체의 클래스를 구분할 수 있게 한다.
        from omni.physx import get_physx_scene_query_interface
        # get_physx_scene_query_interface는 PhysX 장면에 광선·겹침 질의를 실행할 인터페이스를 반환한다.
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdPhysics, UsdLux, PhysxSchema
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.

        if not 0.01 <= args.mass <= 100:
            raise ValueError("--mass must be between 0.01 and 100 kg")
        # stage_units_in_meters는 장면 길이 단위이고, physics_dt·rendering_dt는 각각 물리·렌더링 시간 간격(초)이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        physics = UsdPhysics.Scene.Get(stage, world.get_physics_context().prim_path)
        physics.CreateGravityMagnitudeAttr(9.81)
        physx = PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
        physx.CreateEnableCCDAttr(True)
        physx.CreateEnableStabilizationAttr(True)
        material = PhysicsMaterial(
            prim_path="/World/Looks/Friction", static_friction=0.5, dynamic_friction=0.5
        )
        for i, x in enumerate((-1.0, 0.0, 1.0)):
            bottom = DynamicCuboid(
                prim_path=f"/World/Bottom_{i}",
                name=f"bottom_{i}",
                position=np.array([x, 0, 0.25]),
                size=0.5,
                mass=args.mass,
                color=np.array([0.6, 0.1, 0.1]),
            )
            top = DynamicCuboid(
                prim_path=f"/World/Top_{i}",
                name=f"top_{i}",
                position=np.array([x, 0, 1.0]),
                size=0.5,
                mass=args.mass,
                color=np.array([0.1, 0.1, 0.6]),
            )
            bottom.apply_physics_material(material)
            top.apply_physics_material(material)
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        bottoms = world.scene.add(
            RigidPrim(
                "/World/Bottom_[0-2]",
                name="bottom_view",
                track_contact_forces=True,
                contact_filter_prim_paths_expr=["/World/Top_.*"],
                max_contact_count=60,
            )
        )
        tops = world.scene.add(RigidPrim("/World/Top_[0-2]", name="top_view"))
        mesh = UsdGeom.Mesh.Define(stage, "/World/Mesh")
        mesh.CreatePointsAttr(
            [(-0.2, -0.2, 0), (0.2, -0.2, 0), (0, 0.2, 0), (0, 0, 0.4)]
        )
        mesh.CreateFaceVertexCountsAttr([3, 3, 3, 3])
        mesh.CreateFaceVertexIndicesAttr([0, 2, 1, 0, 1, 3, 1, 2, 3, 2, 0, 3])
        mesh.CreateSubdivisionSchemeAttr("none")
        mesh.AddTranslateOp().Set(Gf.Vec3d(0, 2, 0.1))
        # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr(
            "convexHull"
        )
        UsdPhysics.MassAPI.Apply(mesh.GetPrim()).CreateMassAttr(2.0)
        # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
        UsdPhysics.RigidBodyAPI.Apply(mesh.GetPrim())
        for prim in Usd.PrimRange(stage.GetPrimAtPath("/World")):
            if prim.IsA(UsdGeom.Mesh):
                add_labels(prim, labels=[prim.GetName()], instance_name="class")
        preview = UsdShade.Material.Define(stage, "/World/Looks/Green")
        shader = UsdShade.Shader.Define(stage, "/World/Looks/Green/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0, 0.7, 0.2)
        )
        preview.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )
        # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(preview)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        marker = UsdGeom.Xform.Define(stage, "/World/AlignedMarker")
        # USD 변환을 누적 계산하는 캐시를 만든다. 부모 변환을 포함한 월드 변환을 얻을 수 있다.
        pose = UsdGeom.XformCache().GetLocalToWorldTransform(mesh.GetPrim())
        marker.AddTransformOp().Set(pose)
        selection = omni.usd.get_context().get_selection()
        selection.set_selected_prim_paths([str(mesh.GetPath())], True)
        initial_size = (
            UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
            .ComputeWorldBound(mesh.GetPrim())
            .ComputeAlignedRange()
            .GetSize()
        )
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(output / "initial_scene.usda"))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        for i in range(sample_steps):
            if not app.is_running():
                return
            if i == sample_steps // 2:
                tops.apply_forces(np.array([[1.0, 0, 0]] * 3))
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
        if not app.is_running():
            return
        query = get_physx_scene_query_interface()
        # 시작점과 방향으로 광선을 쏘아 범위 안에서 가장 가까운 충돌 정보를 조회한다.
        ray = query.raycast_closest(carb.Float3(0, 0, 3), carb.Float3(0, 0, -1), 5.0)
        overlap_paths = []

        def collect(hit):
            overlap_paths.append(str(hit.rigid_body))
            return True

        # 지정한 상자 영역과 겹치는 충돌 형상을 조회한다.
        query.overlap_box(
            carb.Float3(2, 0.4, 0.6),
            carb.Float3(0, 0, 0.5),
            carb.Float4(0, 0, 0, 1),
            collect,
            False,
        )
        contact = bottoms.get_contact_force_data(dt=1 / 60)
        friction = bottoms.get_friction_data(dt=1 / 60)
        report = {
            "mesh_world_size_m": list(initial_size),
            "selected_prims": selection.get_selected_prim_paths(),
            "mesh_world_position": list(pose.ExtractTranslation()),
            "bottom_positions": bottoms.get_world_poses()[0].tolist(),
            "top_positions": tops.get_world_poses()[0].tolist(),
            "net_contact_forces_N": bottoms.get_net_contact_forces(dt=1 / 60).tolist(),
            "top_bottom_contact_matrix_N": bottoms.get_contact_force_matrix(
                dt=1 / 60
            ).tolist(),
            "contact_data": [x.tolist() for x in contact],
            "friction_data": [x.tolist() for x in friction],
            "raycast": {
                "hit": bool(ray["hit"]),
                "distance_m": float(ray["distance"]) if ray["hit"] else None,
                "rigid_body": str(ray.get("rigidBody", "")),
            },
            "overlap_bodies": overlap_paths,
        }
        (output / "scene_queries.json").write_text(json.dumps(report, indent=2))
        print(
            json.dumps(
                {
                    k: v
                    for k, v in report.items()
                    if k not in ("contact_data", "friction_data")
                },
                indent=2,
            )
        )
        print(f"Outputs: {output.resolve()}")
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
