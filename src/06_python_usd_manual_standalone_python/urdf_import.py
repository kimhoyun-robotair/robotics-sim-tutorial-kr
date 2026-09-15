"""Import the installed Carter URDF and inspect its wheel drives in Isaac Sim 5.1."""

import argparse
from itertools import count
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None,
        help="Positive application update limit; omitted: keep GUI open (headless: 1000)",
    )
    parser.add_argument("--fix-base", action="store_true", help="Fix the robot base to the world")
    parser.add_argument("--self-collision", action="store_true", help="Enable collisions between robot links")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    step_limit = args.steps if args.steps is not None else (1000 if args.headless else None)

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.kit.commands
        import omni.timeline
        import omni.usd
        from isaacsim.core.prims import Articulation
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, PhysicsSchemaTools, PhysxSchema, UsdLux, UsdPhysics

        extension_id = "isaacsim.asset.importer.urdf"
        enable_extension(extension_id)
        extension_path = get_extension_path_from_name(extension_id)
        if not extension_path:
            raise RuntimeError("The Isaac Sim 5.1 URDF importer extension is unavailable")
        urdf = Path(extension_path) / "data/urdf/robots/carter/urdf/carter.urdf"
        if not urdf.is_file():
            raise FileNotFoundError(urdf)
        success, config = omni.kit.commands.execute("URDFCreateImportConfig")
        if not success:
            raise RuntimeError("Could not create the URDF import configuration")
        config.merge_fixed_joints = False
        config.convex_decomp = False
        config.import_inertia_tensor = True
        config.distance_scale = 1.0
        config.fix_base = args.fix_base
        config.self_collision = args.self_collision
        success, robot_path = omni.kit.commands.execute(
            "URDFParseAndImportFile", urdf_path=str(urdf),
            import_config=config, get_articulation_root=True,
        )
        if not success or not robot_path:
            raise RuntimeError(f"Could not import {urdf}")
        stage = omni.usd.get_context().get_stage()
        physics = UsdPhysics.Scene.Define(stage, "/physicsScene")
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
        physics.CreateGravityMagnitudeAttr(9.81)
        settings = PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
        settings.CreateEnableCCDAttr(True)
        settings.CreateEnableStabilizationAttr(True)
        settings.CreateEnableGPUDynamicsAttr(False)
        settings.CreateBroadphaseTypeAttr("MBP")
        settings.CreateSolverTypeAttr("TGS")
        PhysicsSchemaTools.addGroundPlane(
            stage, "/Ground", "Z", 1500, Gf.Vec3f(0, 0, -0.25), Gf.Vec3f(0.5),
        )
        UsdLux.DistantLight.Define(stage, "/Light").CreateIntensityAttr(1000)
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0.5])
        for name in ("left_wheel", "right_wheel"):
            joint = stage.GetPrimAtPath(f"/carter/joints/{name}")
            if not joint.IsValid():
                raise RuntimeError(f"Imported Carter is missing its {name} joint")
            drive = UsdPhysics.DriveAPI.Get(joint, "angular")
            drive.GetTargetVelocityAttr().Set(150.0)
            drive.GetDampingAttr().Set(15000.0)
            drive.GetStiffnessAttr().Set(0.0)
        omni.timeline.get_timeline_interface().play()
        app.update()
        if not app.is_running():
            return
        robot = Articulation(robot_path)
        robot.initialize()
        if not robot.is_physics_handle_valid():
            raise RuntimeError(f"Articulation failed to initialize at {robot_path}")
        print({"robot": robot_path, "fix_base": args.fix_base,
               "self_collision": args.self_collision, "wheel_target_degrees_per_second": 150.0})
        for step in count():
            if not app.is_running() or (step_limit is not None and step >= step_limit):
                break
            app.update()
    finally:
        app.close()


if __name__ == "__main__":
    main()
