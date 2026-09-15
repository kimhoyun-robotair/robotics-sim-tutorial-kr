"""Author a reusable depth-camera USD asset, then inspect it in the GUI.

API source: Isaac Sim 5.1 camera_add_depth_sensor.py and the Depth Sensors guide
https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera_depth.html
"""
import argparse
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None,
                    help='Positive Kit update limit; omitted keeps the GUI open until closed')
parser.add_argument('--headless', action='store_true',
                    help='Export without a GUI; omitted --steps uses one update')
parser.add_argument('--output', type=Path, help='New USD output file; existing paths are refused')
args = parser.parse_args()
if args.steps is not None and args.steps < 1:
    parser.error('steps must be positive')
output = args.output or Path(__file__).resolve().parent / 'output' / (
    'depth_camera_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.usd')
if output.exists():
    parser.error(f'output already exists: {output}')
output.parent.mkdir(parents=True, exist_ok=True)
step_limit = args.steps if args.steps is not None else (1 if args.headless else None)

from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless})
try:
    from isaacsim.core.utils.stage import get_current_stage
    from isaacsim.sensors.camera import Camera, SingleViewDepthSensorAsset

    stage = get_current_stage()
    root = stage.DefinePrim('/root', 'Xform')
    camera = Camera(prim_path='/root/Camera')
    stage.DefinePrim('/root/TemplateRenderProduct', 'Scope')
    SingleViewDepthSensorAsset.add_template_render_product(
        parent_prim_path='/root/TemplateRenderProduct',
        camera_prim_path='/root/Camera',
        **{'omni:rtx:post:depthSensor:baselineMM': 42},
    )
    stage.SetDefaultPrim(root)
    if not stage.Export(str(output)):
        raise RuntimeError(f'Could not export depth camera: {output}')
    print(f'Depth camera asset: {output.resolve()}')
    frame = 0
    while app.is_running() and (step_limit is None or frame < step_limit):
        app.update()
        frame += 1
finally:
    app.close()
