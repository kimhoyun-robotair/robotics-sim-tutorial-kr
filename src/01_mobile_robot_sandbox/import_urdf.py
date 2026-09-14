"""Standalone Python: 포함된 차동구동 URDF를 재사용 가능한 USD asset으로 변환."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tutorial_common.runtime import (
    add_common_arguments,
    close_app,
    launch_app,
    output_directory,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    parser.add_argument(
        "--urdf",
        type=Path,
        default=Path(__file__).parent / "assets" / "learning_bot.urdf",
    )
    args = parser.parse_args()
    source = args.urdf.resolve()
    if not source.is_file():
        parser.error(f"URDF가 없습니다: {source}")
    output = output_directory("01_urdf", args.output)
    app = launch_app(args.headless)
    try:
        import omni.kit.commands
        from isaacsim.core.utils.extensions import enable_extension
        from pxr import Usd, UsdPhysics, UsdShade

        enable_extension("isaacsim.asset.importer.urdf")
        app.update()
        status, config = omni.kit.commands.execute("URDFCreateImportConfig")
        if not status:
            raise RuntimeError("URDF importer 설정 생성 실패")
        config.merge_fixed_joints = False
        config.fix_base = False
        config.import_inertia_tensor = True
        config.distance_scale = 1.0
        config.make_default_prim = True
        config.create_physics_scene = False
        destination = output / "robot.usd"
        status, root = omni.kit.commands.execute(
            "URDFParseAndImportFile",
            urdf_path=str(source),
            import_config=config,
            dest_path=str(destination),
            get_articulation_root=True,
        )
        if not status or not destination.is_file():
            raise RuntimeError("URDF → USD 변환 실패")
        stage = Usd.Stage.Open(str(destination))
        wheels = []
        for prim in stage.Traverse():
            if prim.GetName() in ("left_wheel_joint", "right_wheel_joint") and prim.IsA(
                UsdPhysics.RevoluteJoint
            ):
                drive = UsdPhysics.DriveAPI.Apply(prim, "angular")
                drive.CreateStiffnessAttr(0.0)
                drive.CreateDampingAttr(2.0)
                drive.CreateMaxForceAttr(2.0)
                wheels.append(str(prim.GetPath()))
        if len(wheels) != 2:
            raise RuntimeError(f"이 실습의 wheel joint 이름을 확인하세요: {wheels}")
        material = UsdShade.Material.Define(
            stage, str(stage.GetDefaultPrim().GetPath()) + "/CasterMaterial"
        )
        physics = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        physics.CreateStaticFrictionAttr(0.0)
        physics.CreateDynamicFrictionAttr(0.0)
        for prim in stage.Traverse():
            if "caster" in str(prim.GetPath()).lower() and prim.HasAPI(
                UsdPhysics.CollisionAPI
            ):
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(
                    material, materialPurpose="physics"
                )
        stage.GetRootLayer().Save()
        write_json(
            output / "import.json",
            {
                "urdf": str(source),
                "usd": str(destination),
                "articulation_root": root,
                "wheel_joint_paths": wheels,
                "wheel_radius_m": 0.03,
                "wheel_base_m": 0.1125,
            },
        )
        print(f"USD asset: {destination}", flush=True)
    finally:
        close_app(app)


if __name__ == "__main__":
    main()
