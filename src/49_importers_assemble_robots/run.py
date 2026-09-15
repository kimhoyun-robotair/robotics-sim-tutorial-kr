"""Assemble the installed UR10e and Allegro assets using the native 5.1 RobotAssembler."""
import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true', help='Prepare both references for the GUI workflow')
    parser.add_argument('--cancel', action='store_true', help='Begin and then cancel the session-layer assembly')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=240, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Require a new output directory and finite headless frame limit')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    os.chdir(args.output)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        from isaacsim.storage.native import get_assets_root_path
        from pxr import Gf, UsdGeom, UsdPhysics
        enable_extension('isaacsim.robot_setup.assembler')
        from isaacsim.robot_setup.assembler import RobotAssembler
        world = World(stage_units_in_meters=1.0)
        stage = get_current_stage()
        root = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(root.GetPrim())
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac 5.1 asset root unavailable')
        add_reference_to_stage(assets + '/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd', '/World/ur10e')
        add_reference_to_stage(assets + '/Isaac/Robots/WonikRobotics/AllegroHand/allegro_hand_instanceable.usd', '/World/allegro_hand')
        base_mount = '/World/ur10e/ee_link'
        hand_mount = '/World/allegro_hand/allegro_mount'
        for path in (base_mount, hand_mount):
            if not stage.GetPrimAtPath(path).IsValid():
                raise RuntimeError(f'Missing 5.1 mounting frame: {path}')
        assembler = RobotAssembler()
        if not args.prepare_only:
            assembler.begin_assembly(stage, '/World/ur10e', base_mount, '/World/allegro_hand', hand_mount, 'Gripper', 'allegro_hand')
            if args.cancel:
                assembler.cancel_assembly()
            else:
                hand = UsdGeom.Xformable(stage.GetPrimAtPath('/World/allegro_hand'))
                matrix = hand.GetLocalTransformation()
                for axis in (Gf.Vec3d(0, 0, 1), Gf.Vec3d(0, 1, 0)):
                    matrix = Gf.Matrix4d().SetRotate(Gf.Rotation(axis, -90)) * matrix
                hand.MakeMatrixXform().Set(matrix)
                assembler.assemble()
                world.reset()
        preview_steps = args.steps or 240
        frame = 0
        while app.is_running() and frame < preview_steps:
            if not args.prepare_only and not args.cancel:
                world.step(render=not args.headless)
            else:
                app.update()
            frame += 1
        if not app.is_running():
            return
        if not args.prepare_only and not args.cancel:
            base_transform = omni.usd.get_world_transform_matrix(stage.GetPrimAtPath(base_mount))
            attach_transform = omni.usd.get_world_transform_matrix(stage.GetPrimAtPath(hand_mount))
            distance = (base_transform.ExtractTranslation() - attach_transform.ExtractTranslation()).GetLength()
            print('Measured mounting-frame separation, meters:', distance)
            world.stop()
            assembler.finish_assemble()
        joints = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdPhysics.FixedJoint)]
        stage.GetRootLayer().Export(str(args.output / 'assembled.usda'))
        (args.output / 'report.json').write_text(json.dumps({'fixed_joint_paths': joints, 'cancelled': args.cancel}, indent=2))
        print('Authored fixed joints:', joints)
        if args.steps == 0:
            while app.is_running():
                app.update()
    finally:
        app.close()


if __name__ == '__main__':
    main()
