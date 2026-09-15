"""Open a non-instanceable Franka reference for the native Lula/XRDF editor."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=None,
                        help='App update limit; omitted/0 keeps the GUI open until closed')
    parser.add_argument('--frames', type=int, default=0,
                        help='Legacy headless update limit when --steps is omitted; does not limit GUI')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.frames < 0 or args.steps < 0 or (args.headless and args.steps == 0):
        parser.error('nonnegative limits required; headless requires positive --steps (or legacy --frames)')
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        from isaacsim.core.api import World
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        from isaacsim.storage.native import get_assets_root_path
        enable_extension('isaacsim.robot_setup.xrdf_editor')
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac Sim 5.1 asset root is unavailable')
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        add_reference_to_stage(assets + '/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd', '/World/Franka')
        stage = get_current_stage()
        for prim in list(stage.Traverse()):
            if prim.IsInstanceable():
                prim.SetInstanceable(False)
        world.reset()
        print('Select /World/Franka in Tools > Robotics > Lula Robot Description Editor.')
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
