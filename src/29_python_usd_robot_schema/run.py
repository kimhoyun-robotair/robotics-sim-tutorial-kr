import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot Schema")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: GUI stays open (headless: 120)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
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
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.viewports import set_camera_view
        # set_camera_view는 뷰포트 카메라를 eye 위치에 두고 target 지점을 바라보도록 설정한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.

        enable_extension("isaacsim.robot.schema")
        # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
        # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
        app.update()
        from usd.schema.isaac import robot_schema as rs
        # robot_schema는 USD Prim에 로봇·링크·관절·부착점 등의 의미와 관계를 기록하는 Isaac 로봇 스키마이다.
        from usd.schema.isaac.robot_schema import utils
        # robot_schema의 utils는 스키마에 기록한 링크·관절 관계로 로봇 트리를 생성하고 출력하는 도구이다.

        # 새 USD 파일에 연결된 Stage를 만든다. Kit에서 현재 열어 둔 Stage와 별도로 구성할 수 있다.
        stage = Usd.Stage.CreateNew(str(output / "robot.usda"))
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(stage, "/Light").CreateIntensityAttr(1500)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        robot = UsdGeom.Xform.Define(stage, "/Robot").GetPrim()
        stage.SetDefaultPrim(robot)
        for name, z in (("base_link", 0.1), ("arm_link", 0.5)):
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            cube = UsdGeom.Cube.Define(stage, "/Robot/" + name)
            cube.CreateSizeAttr(0.2)
            cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
            # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
            UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
            # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        # 두 몸체 사이의 회전 관절을 정의한다. 연결 대상과 관절 축·제한을 이어서 지정한다.
        joint = UsdPhysics.RevoluteJoint.Define(stage, "/Robot/shoulder")
        joint.CreateBody0Rel().SetTargets([Sdf.Path("/Robot/base_link")])
        joint.CreateBody1Rel().SetTargets([Sdf.Path("/Robot/arm_link")])
        joint.CreateAxisAttr("Y")
        joint.CreateLowerLimitAttr(-90)
        joint.CreateUpperLimitAttr(90)
        joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.2))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, -0.2))
        point = UsdGeom.Xform.Define(stage, "/Robot/arm_link/ToolMount").GetPrim()
        # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
        UsdGeom.Xformable(point).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
        configuration = output / "configuration"
        configuration.mkdir()
        layer = Sdf.Layer.CreateNew(str(configuration / "robot_schema.usda"))
        stage.GetRootLayer().subLayerPaths.append("configuration/robot_schema.usda")
        # with 블록 안에서 수행하는 USD 편집이 기록될 대상 레이어를 지정한다.
        with Usd.EditContext(stage, layer):
            rs.ApplyRobotAPI(robot)
            robot.GetAttribute(rs.Attributes.DESCRIPTION.name).Set(
                "Two-link educational robot"
            )
            robot.GetAttribute(rs.Attributes.NAMESPACE.name).Set("tutorial_robot")
            for name in ("base_link", "arm_link"):
                prim = stage.GetPrimAtPath("/Robot/" + name)
                rs.ApplyLinkAPI(prim)
                robot.GetRelationship(rs.Relations.ROBOT_LINKS.name).AddTarget(
                    prim.GetPath()
                )
            rs.ApplyJointAPI(joint.GetPrim())
            robot.GetRelationship(rs.Relations.ROBOT_JOINTS.name).AddTarget(
                joint.GetPath()
            )
            rs.ApplyReferencePointAPI(point)
            point.GetAttribute(rs.Attributes.DESCRIPTION.name).Set(
                "Tool attachment point"
            )
            point.GetAttribute(rs.Attributes.FORWARD_AXIS.name).Set("Z")
        layer.Save()
        # 현재 루트 레이어의 변경을 원래 연결된 USD 파일에 저장한다.
        stage.GetRootLayer().Save()
        tree = utils.GenerateRobotLinkTree(stage, robot)
        utils.PrintRobotTree(tree)
        report = {
            "robot_schemas": robot.GetAppliedSchemas(),
            "links": [
                str(p)
                for p in robot.GetRelationship(
                    rs.Relations.ROBOT_LINKS.name
                ).GetTargets()
            ],
            "joints": [
                str(p)
                for p in robot.GetRelationship(
                    rs.Relations.ROBOT_JOINTS.name
                ).GetTargets()
            ],
            "reference_point_schemas": point.GetAppliedSchemas(),
            "joint_body0": [str(p) for p in joint.GetBody0Rel().GetTargets()],
            "joint_body1": [str(p) for p in joint.GetBody1Rel().GetTargets()],
        }
        (output / "schema_report.json").write_text(json.dumps(report, indent=2))
        # USD 파일을 Kit의 현재 Stage로 연다.
        omni.usd.get_context().open_stage(str(output / "robot.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0.3])
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            app.update()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
