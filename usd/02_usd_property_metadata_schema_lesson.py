"""Property / Metadata / Schema 학습용 OpenUSD 예제.

대상: pxr.Usd, pxr.UsdGeom, pxr.UsdPhysics를 제공하는 Python 환경.
Isaac Sim의 Script Editor에서도 별도 메모리 Stage를 만들어 실행할 수 있습니다.
현재 Isaac Sim 화면의 Stage를 교체하거나 기존 파일을 덮어쓰지 않습니다.
물리 설정 데이터만 작성하며, 물리 엔진이나 열 시뮬레이션을 실행하지 않습니다.

검증 범위: Python 문법은 검사했습니다. 작성 환경에 pxr 런타임이 없어
OpenUSD / Isaac Sim에서의 실제 실행은 검증하지 않았습니다.

공식 API 참고:
https://openusd.org/release/api/class_usd_attribute.html
https://openusd.org/release/api/class_usd_relationship.html
https://openusd.org/release/api/class_usd_object.html
https://openusd.org/release/api/class_usd_geom_cube.html
https://openusd.org/release/api/class_usd_physics_rigid_body_a_p_i.html
https://openusd.org/release/api/class_usd_physics_mass_a_p_i.html
https://openusd.org/release/api/class_usd_collection_a_p_i.html
"""
from pathlib import Path

try:
    from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf
except ImportError as exc:
    raise ImportError(
        "pxr 모듈을 불러오지 못했습니다. OpenUSD Python 환경 또는 "
        "Isaac Sim Script Editor에서 실행하세요. Isaac Sim의 Python 환경에 "
        "별도의 USD 패키지를 임의로 덮어 설치하지 마세요."
    ) from exc


def require_success(ok: bool, description: str) -> None:
    """bool을 반환하는 USD authoring API의 실패를 명시적으로 보고합니다."""
    if not ok:
        raise RuntimeError(description)


def build_lesson_stage() -> Usd.Stage:
    """독립적인 Stage를 만들고 각 개념의 관찰 결과를 출력합니다."""
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    stage.SetTimeCodesPerSecond(24.0)
    stage.SetStartTimeCode(0.0)
    stage.SetEndTimeCode(24.0)
    stage.SetInterpolationType(Usd.InterpolationTypeLinear)

    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    robot = UsdGeom.Xform.Define(stage, "/World/Robot").GetPrim()
    cube = UsdGeom.Cube.Define(stage, "/World/Robot/Body")
    body = cube.GetPrim()
    camera = UsdGeom.Camera.Define(stage, "/World/Camera").GetPrim()

    # 1. Schema fallback: Property가 있지만 사용자가 값을 쓰지는 않은 상태.
    size = cube.GetSizeAttr()
    print("[1] size: valid, authored-property, authored-value, resolved-value")
    print(bool(size), size.IsAuthored(), size.HasAuthoredValue(), size.Get())
    # 일반적인 기본 USD 환경의 예상 결과: True False False 2.0

    # 선언을 작성하는 것과 값을 작성하는 것은 다릅니다.
    cube.CreateSizeAttr()
    print("after CreateSizeAttr():", size.IsAuthored(), size.HasAuthoredValue(), size.Get())
    # 예상: True False 2.0

    require_success(size.Set(1.0), "size 작성 실패")
    # Cube의 크기를 변경하면 그 크기에 맞는 extent도 함께 작성합니다.
    cube.CreateExtentAttr([
        Gf.Vec3f(-0.5, -0.5, -0.5),
        Gf.Vec3f(0.5, 0.5, 0.5),
    ])
    print("after Set(1.0):", size.HasAuthoredValue(), size.Get())

    # 2. 사용자 정의 Attribute. 값이 없다는 것은 Attribute가 없다는 뜻이 아닙니다.
    temperature = body.CreateAttribute(
        "demo:temperature", Sdf.ValueTypeNames.Float,
        custom=True, variability=Sdf.VariabilityVarying,
    )
    print("[2] new temperature:", bool(temperature), temperature.Get())
    # 예상: True None
    require_success(temperature.Set(20.0), "temperature default 작성 실패")
    require_success(temperature.Set(20.0, Usd.TimeCode(0)), "t=0 작성 실패")
    require_success(temperature.Set(30.0, Usd.TimeCode(24)), "t=24 작성 실패")
    print("default:", temperature.Get())
    print("t=12:", temperature.Get(Usd.TimeCode(12)))
    print("samples:", temperature.GetTimeSamples())
    # 예상: default=20.0, t=12=25.0, samples=[0.0, 24.0]

    # 3. Relationship은 대상의 경로를 기록합니다. 자동 카메라 제어는 아닙니다.
    camera_rel = body.CreateRelationship("demo:camera", custom=True)
    require_success(camera_rel.SetTargets([camera.GetPath()]), "relationship 작성 실패")
    print("[3] relationship path:", camera_rel.GetPath())
    print("target paths:", [str(path) for path in camera_rel.GetTargets()])
    for target_path in camera_rel.GetTargets():
        # 이 예제의 target은 Prim입니다. 일반 Relationship은 Property도 가리킬 수 있습니다.
        target_prim = stage.GetPrimAtPath(target_path)
        if not target_prim:
            raise RuntimeError(f"대상 Prim을 찾을 수 없습니다: {target_path}")
        print("target prim type:", target_prim.GetTypeName())

    # 4. Prim과 Property는 각각 자신의 Metadata를 가집니다.
    require_success(
        body.SetMetadata("documentation", "Cube used in the USD lesson."),
        "Prim documentation 작성 실패",
    )
    body.SetCustomDataByKey("demo:assetId", "body-001")
    require_success(
        temperature.SetMetadata("documentation", "Teaching value; not a thermal simulation."),
        "Attribute documentation 작성 실패",
    )
    temperature.SetCustomDataByKey("demo:unit", "degC")
    print("[4] Prim metadata:", body.GetMetadata("documentation"))
    print("Attribute value:", temperature.Get())
    print("Attribute metadata:", temperature.GetMetadata("documentation"))
    print("Custom metadata unit:", temperature.GetCustomDataByKey("demo:unit"))

    # 5. API Schema의 Python 래퍼 생성만으로 스키마가 적용되지는 않습니다.
    _rigid_body_wrapper = UsdPhysics.RigidBodyAPI(body)
    print("[5] before Apply:", body.HasAPI(UsdPhysics.RigidBodyAPI))
    rigid_body = UsdPhysics.RigidBodyAPI.Apply(body)
    if not rigid_body:
        raise RuntimeError("RigidBodyAPI 적용 실패")
    rigid_body.CreateRigidBodyEnabledAttr(True)

    mass_api = UsdPhysics.MassAPI.Apply(body)
    if not mass_api:
        raise RuntimeError("MassAPI 적용 실패")
    mass_api.CreateMassAttr(2.0)
    print("after Apply:", body.HasAPI(UsdPhysics.RigidBodyAPI))
    print("Prim type (still Cube):", body.GetTypeName())
    print("mass:", mass_api.GetMassAttr().Get())
    print("same mass via generic API:", body.GetAttribute("physics:mass").Get())
    print("applied APIs:", body.GetAppliedSchemas())

    # 6. Multiple-apply API Schema: 한 Prim에 이름이 다른 두 Collection.
    parts = Usd.CollectionAPI.Apply(robot, "parts")
    sensors = Usd.CollectionAPI.Apply(robot, "sensors")
    if not parts or not sensors:
        raise RuntimeError("CollectionAPI 적용 실패")
    parts.CreateIncludesRel().SetTargets([body.GetPath()])
    sensors.CreateIncludesRel().SetTargets([camera.GetPath()])
    print("[6] collection properties:", parts.GetIncludesRel().GetName(), sensors.GetIncludesRel().GetName())

    # 7. Non-applied API Schema: apiSchemas에 별도 적용 기록을 남기지 않는 접근 API.
    transform_api = UsdGeom.XformCommonAPI(robot)
    require_success(transform_api.SetTranslate(Gf.Vec3d(1, 0, 0)), "Robot 이동 작성 실패")
    print("[7] Robot applied APIs:", robot.GetAppliedSchemas())
    print("Robot translate:", robot.GetAttribute("xformOp:translate").Get())

    # 실제 실행 환경에서 기본 예상 결과를 점검합니다.
    assert body.GetTypeName() == "Cube"
    assert body.IsA(UsdGeom.Cube)
    assert body.IsA(UsdGeom.Xformable)
    assert body.HasAPI(UsdPhysics.RigidBodyAPI)
    assert body.HasAPI(UsdPhysics.MassAPI)
    assert size.Get() == 1.0
    assert temperature.Get() == 20.0
    assert temperature.Get(Usd.TimeCode(12)) == 25.0
    assert body.GetAttribute("physics:mass").Get() == 2.0
    assert temperature.GetCustomDataByKey("demo:unit") == "degC"
    assert camera_rel.GetTargets() == [camera.GetPath()]
    return stage


def inspect_prim(stage: Usd.Stage, path: str) -> None:
    """장면을 수정하지 않고 Prim / Property / Metadata를 나눠 출력합니다."""
    prim = stage.GetPrimAtPath(path)
    if not prim:
        raise ValueError(f"Prim을 찾을 수 없습니다: {path}")

    print("\n=== INSPECT ===")
    print("Prim:", prim.GetPath())
    print("typeName:", prim.GetTypeName())
    print("applied schemas:", prim.GetAppliedSchemas())
    print("authored prim metadata:", prim.GetAllAuthoredMetadata())
    print("all property names:", prim.GetPropertyNames())
    print("authored properties:", [prop.GetName() for prop in prim.GetAuthoredProperties()])
    for attr in prim.GetAttributes():
        print(
            "ATTR", attr.GetName(),
            "type=", str(attr.GetTypeName()),
            "custom=", attr.IsCustom(),
            "authored-value=", attr.HasAuthoredValue(),
            "default=", attr.Get(),
            "time-samples=", attr.GetTimeSamples(),
        )
        print("  authored metadata:", attr.GetAllAuthoredMetadata())
    for rel in prim.GetRelationships():
        print("REL", rel.GetName(), "targets=", [str(p) for p in rel.GetTargets()])


def export_lesson(stage: Usd.Stage, filename: str) -> Path:
    """요청한 경우에만 루트 레이어를 새 USDA 파일로 저장합니다. 덮어쓰기하지 않습니다."""
    path = Path(filename).expanduser().resolve()
    if path.suffix.lower() != ".usda":
        raise ValueError("파일 확장자는 .usda를 사용하세요.")
    if path.exists():
        raise FileExistsError(f"기존 파일을 덮어쓰지 않습니다: {path}")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"상위 폴더가 없습니다: {path.parent}")
    require_success(stage.GetRootLayer().Export(str(path)), f"저장 실패: {path}")
    return path


if __name__ == "__main__":
    # stage 변수를 유지해야 해당 Stage의 USD 객체들을 계속 사용할 수 있습니다.
    stage = build_lesson_stage()
    inspect_prim(stage, "/World/Robot/Body")
    print("\n=== AUTHORED ROOT LAYER ===")
    print(stage.GetRootLayer().ExportToString())
    # 파일이 필요한 경우, 존재하지 않는 파일 경로로 직접 호출하세요.
    # export_lesson(stage, "property_metadata_schema.usda")
