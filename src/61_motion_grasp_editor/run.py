"""Open the official gripper/object stage and enable the native Grasp Editor."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, type=Path, help='Local USD extracted from the official tutorial ZIP')
    parser.add_argument('--steps', type=int, default=None,
                        help='App update limit; omitted/0 keeps the GUI open until closed')
    parser.add_argument('--frames', type=int, default=0,
                        help='Legacy headless update limit when --steps is omitted; does not limit GUI')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    if not args.stage.is_file():
        parser.error(f'Missing USD: {args.stage}')
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.frames < 0 or args.steps < 0 or (args.headless and args.steps == 0):
        parser.error('nonnegative limits required; headless requires positive --steps (or legacy --frames)')
    from isaacsim import SimulationApp

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension('isaacsim.robot_setup.grasp_editor')
        if not omni.usd.get_context().open_stage(str(args.stage.resolve())):
            raise RuntimeError('Could not open tutorial stage')
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            app.update()
            count += 1
    finally:
        app.close()


if __name__ == '__main__':
    main()
