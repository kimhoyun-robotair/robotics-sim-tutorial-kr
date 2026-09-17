"""Author the H1 policy's initial state and drive properties with explicit unit conversion."""
import argparse
import json
import math
from pathlib import Path
import re


def matching_value(pattern_values, name):
    matches = [value for pattern, value in pattern_values.items() if re.fullmatch(pattern, name)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one configuration for {name}: {matches}")
    return float(matches[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("h1_policy.json"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="UI update limit; omitted or 0 keeps the stage open without policy inference; headless requires a positive value")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("headless requires positive --steps")
    cfg = json.loads(args.config.read_text())
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from pxr import Gf, Sdf, UsdGeom, UsdPhysics, PhysxSchema
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        root = get_assets_root_path()
        if not root:
            raise RuntimeError("Isaac Sim 5.1 asset root not available")
        source = root + "/Isaac/Robots/Unitree/H1/h1.usd"
        if not Sdf.Layer.FindOrOpen(source):
            raise RuntimeError(f"Cannot read {source}")
        layer = Sdf.Layer.CreateNew(str(output / "h1_policy.usda"))
        layer.subLayerPaths = [source]
        layer.Save()
        context = omni.usd.get_context()
        if not context.open_stage(layer.identifier):
            raise RuntimeError("Cannot open the H1 override stage")
        stage = context.get_stage()
        for _ in range(1200):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            if not context.is_stage_loading():
                break
        if context.is_stage_loading():
            raise RuntimeError("H1 loading timed out after 1200 updates")
        robot_prim = stage.GetPrimAtPath("/h1")
        if not robot_prim:
            raise RuntimeError("H1 asset does not contain /h1")
        # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
        transform = UsdGeom.Xformable(robot_prim)
        transform.ClearXformOpOrder()
        transform.AddTranslateOp(opSuffix="policy").Set(Gf.Vec3d(*cfg["base_position_m"]))
        transform.AddOrientOp(opSuffix="policy").Set(Gf.Quatf(1, Gf.Vec3f(0)))
        reports = []
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        for prim in stage.Traverse():
            if not prim.IsA(UsdPhysics.RevoluteJoint):
                continue
            name = prim.GetName()
            groups = [g for g in cfg["actuators"].values() if any(re.fullmatch(p, name) for p in g["joint_names_expr"])]
            if len(groups) != 1:
                raise ValueError(f"Missing or ambiguous actuator group for {name}")
            group = groups[0]
            position = matching_value(cfg["joint_positions_rad"], name)
            stiffness = matching_value(group["stiffness"], name)
            damping = matching_value(group["damping"], name)
            # 관절에 구동 API를 적용한다. stiffness·damping·목표값으로 관절 구동 방식을 설정한다.
            drive = UsdPhysics.DriveAPI.Apply(prim, "angular")
            drive.CreateTypeAttr("force")
            drive.CreateTargetPositionAttr(math.degrees(position))
            drive.CreateTargetVelocityAttr(0)
            drive.CreateStiffnessAttr(stiffness * math.pi / 180)
            drive.CreateDampingAttr(damping * math.pi / 180)
            drive.CreateMaxForceAttr(group["effort_limit"])
            state = PhysxSchema.JointStateAPI.Apply(prim, "angular")
            state.CreatePositionAttr(math.degrees(position))
            state.CreateVelocityAttr(0)
            joint = PhysxSchema.PhysxJointAPI.Apply(prim)
            joint.CreateMaxJointVelocityAttr(math.degrees(group["velocity_limit"]))
            reports.append({"joint": name, "initial_position_rad": position, "usd_position_deg": math.degrees(position),
                            "stiffness_rad": stiffness, "usd_stiffness_per_deg": stiffness * math.pi / 180,
                            "damping_rad": damping, "usd_damping_per_deg": damping * math.pi / 180,
                            "max_effort_nm": group["effort_limit"], "max_velocity_rad_s": group["velocity_limit"]})
        if len(reports) != 19:
            raise RuntimeError(f"Expected the H1 policy's 19 controlled joints; found {len(reports)}")
        # 현재 루트 레이어의 변경을 원래 연결된 USD 파일에 저장한다.
        stage.GetRootLayer().Save()
        (output / "joint_configuration.json").write_text(json.dumps(reports, indent=2))
        print(json.dumps(reports, indent=2))
        print("Configuration authored. This script does not run a locomotion policy.")
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            app.update()
            count += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
