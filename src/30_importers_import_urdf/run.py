"""Import a local URDF, or import the bundled Franka and run its RMPflow target task."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--franka', action='store_true')
    parser.add_argument('--urdf', type=Path, default=Path(__file__).parent / 'arm.urdf')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 360 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if not args.urdf.is_file():
        parser.error('an existing URDF is required')
    if args.output.exists():
        parser.error('Choose a new --output directory')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import numpy as np
        import omni.kit.commands
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        from isaacsim.core.utils.stage import get_current_stage
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.core.prims import SingleArticulation
        enable_extension('isaacsim.asset.importer.urdf')
        from isaacsim.asset.importer.urdf import _urdf
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        source = args.urdf.resolve()
        if args.franka:
            source = Path(get_extension_path_from_name('isaacsim.asset.importer.urdf')) / 'data/urdf/robots/franka_description/robots/panda_arm_hand.urdf'
        config = _urdf.ImportConfig()
        config.fix_base = True
        config.make_default_prim = False
        config.self_collision = False
        config.distance_scale = 1.0
        config.density = 0.0
        ok, model = omni.kit.commands.execute('URDFParseFile', urdf_path=str(source), import_config=config)
        if not ok or not model:
            raise RuntimeError(f'URDF parsing failed: {source}')
        for name in model.joints:
            model.joints[name].drive.strength = 1047.19751 if args.franka else 20.0
            model.joints[name].drive.damping = 52.35988 if args.franka else 1.0
        ok, robot_path = omni.kit.commands.execute(
            'URDFImportRobot', urdf_path=str(source), urdf_robot=model, import_config=config,
        )
        if not ok or not robot_path:
            raise RuntimeError('URDF import failed')
        if args.franka:
            from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget
            from isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller import RMPFlowController
            world.add_task(FollowTarget(name='follow', franka_prim_path=robot_path, franka_robot_name='arm', target_name='target'))
            world.reset()
            robot = world.scene.get_object('arm')
            controller = RMPFlowController(name='follow_controller', robot_articulation=robot)
        else:
            robot = world.scene.add(SingleArticulation(prim_path=robot_path, name='arm'))
            controller = None
        get_current_stage().GetRootLayer().Export(str(args.output / 'imported.usda'))
        world.reset()
        joint_names = robot.dof_names
        joint_positions = robot.get_joint_positions().tolist()
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            if controller:
                observations = world.get_observations()
                robot.apply_action(controller.forward(
                    target_end_effector_position=observations['target']['position'],
                    target_end_effector_orientation=observations['target']['orientation'],
                ))
            else:
                robot.apply_action(ArticulationAction(joint_positions=np.array([0.5])))
            world.step(render=not args.headless)
            if not app.is_running():
                break
            joint_positions = robot.get_joint_positions().tolist()
            step += 1
        report = {'source': str(source), 'prim_path': robot_path, 'joint_names': joint_names,
                  'joint_positions': joint_positions}
        (args.output / 'report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        app.close()


if __name__ == '__main__':
    main()
