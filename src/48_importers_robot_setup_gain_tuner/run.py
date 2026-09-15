"""Measure a real imported joint's step/sine response or open it in the native Gain Tuner."""
import argparse
import csv
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kp', type=float, default=20.0)
    parser.add_argument('--kd', type=float, default=1.0)
    parser.add_argument('--wave', choices=('step', 'sine'), default='step')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--interactive', action='store_true', help='Native GUI controls the robot; --steps still limits execution')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 600 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.kp <= 0 or args.kd < 0 or args.output.exists() or (args.interactive and args.headless):
        parser.error('Require positive kp, nonnegative kd, new output, and visible interactive mode')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import numpy as np
        import omni.kit.commands
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension('isaacsim.asset.importer.urdf')
        enable_extension('isaacsim.robot_setup.gain_tuner')
        from isaacsim.asset.importer.urdf import _urdf
        world = World(stage_units_in_meters=1.0, physics_dt=1/120, rendering_dt=1/60)
        config = _urdf.ImportConfig()
        config.fix_base = True
        config.default_drive_type = _urdf.UrdfJointTargetType.JOINT_DRIVE_POSITION
        source = str((Path(__file__).parent / 'arm.urdf').resolve())
        ok, model = omni.kit.commands.execute('URDFParseFile', urdf_path=source, import_config=config)
        if not ok or not model:
            raise RuntimeError('Could not parse local arm')
        model.joints['shoulder'].drive.strength = args.kp
        model.joints['shoulder'].drive.damping = args.kd
        ok, robot_path = omni.kit.commands.execute('URDFImportRobot', urdf_path=source, urdf_robot=model, import_config=config)
        if not ok:
            raise RuntimeError('Could not import local arm')
        robot = world.scene.add(SingleArticulation(prim_path=robot_path, name='arm'))
        world.reset()
        if args.interactive:
            step = 0
            while app.is_running() and (args.steps == 0 or step < args.steps):
                app.update()
                step += 1
        else:
            with (args.output / 'response.csv').open('x', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['time_s', 'target_rad', 'actual_rad', 'velocity_rad_s', 'error_rad'])
                step = 0
                while app.is_running() and (args.steps == 0 or step < args.steps):
                    t = step / 120
                    target = (0.5 if t >= 0.5 else 0.0) if args.wave == 'step' else 0.3 * math.sin(2*math.pi*0.5*t)
                    robot.apply_action(ArticulationAction(joint_positions=np.array([target]), joint_velocities=np.array([0.0])))
                    world.step(render=not args.headless)
                    if not app.is_running():
                        break
                    actual = float(robot.get_joint_positions()[0])
                    velocity = float(robot.get_joint_velocities()[0])
                    writer.writerow([t, target, actual, velocity, target-actual])
                    step += 1
            print('Measured response:', args.output / 'response.csv')
    finally:
        app.close()


if __name__ == '__main__':
    main()
