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

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        from isaacsim.core.utils.viewports import set_camera_view
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics

        enable_extension("isaacsim.robot.schema")
        app.update()
        from usd.schema.isaac import robot_schema as rs
        from usd.schema.isaac.robot_schema import utils

        stage = Usd.Stage.CreateNew(str(output / "robot.usda"))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdLux.DistantLight.Define(stage, "/Light").CreateIntensityAttr(1500)
        robot = UsdGeom.Xform.Define(stage, "/Robot").GetPrim()
        stage.SetDefaultPrim(robot)
        for name, z in (("base_link", 0.1), ("arm_link", 0.5)):
            cube = UsdGeom.Cube.Define(stage, "/Robot/" + name)
            cube.CreateSizeAttr(0.2)
            cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, z))
            UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
            UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        joint = UsdPhysics.RevoluteJoint.Define(stage, "/Robot/shoulder")
        joint.CreateBody0Rel().SetTargets([Sdf.Path("/Robot/base_link")])
        joint.CreateBody1Rel().SetTargets([Sdf.Path("/Robot/arm_link")])
        joint.CreateAxisAttr("Y")
        joint.CreateLowerLimitAttr(-90)
        joint.CreateUpperLimitAttr(90)
        joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.2))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, -0.2))
        point = UsdGeom.Xform.Define(stage, "/Robot/arm_link/ToolMount").GetPrim()
        UsdGeom.Xformable(point).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.1))
        configuration = output / "configuration"
        configuration.mkdir()
        layer = Sdf.Layer.CreateNew(str(configuration / "robot_schema.usda"))
        stage.GetRootLayer().subLayerPaths.append("configuration/robot_schema.usda")
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
        omni.usd.get_context().open_stage(str(output / "robot.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0.3])
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            app.update()
    finally:
        app.close()


if __name__ == "__main__":
    main()
