"""Isaac Sim 5.1 standalone sensor lab; see TUTORIAL.md for interpretation."""
import argparse
import json
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Positive simulation step limit; omitted: GUI runs until closed, headless runs 240 steps')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--interactive', action='store_true', help='Compatibility flag: GUI already stays open when --steps is omitted; explicit --steps takes priority')
parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')
parser.add_argument('--config', default='Example_Rotary')
parser.add_argument('--scan-hz', type=float, default=10)

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
sample_steps = args.steps if args.steps is not None else 240
output = args.output or Path(__file__).resolve().parent / 'output' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
output.mkdir(parents=True, exist_ok=False)
from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless, 'enable_motion_bvh': False})
try:
    import numpy as np
    import omni.usd
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid, VisualCuboid
    from pxr import UsdLux
    world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
    stage = omni.usd.get_context().get_stage()
    UsdLux.DomeLight.Define(stage, '/World/Light').CreateIntensityAttr(1000)

    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.sensors.rtx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.rtx import LidarRtx
    world.scene.add_default_ground_plane()
    for i, position in enumerate(([5,0,1],[-5,0,1],[0,5,1],[0,-5,1])):
        world.scene.add(FixedCuboid(prim_path=f'/World/Wall{i}',name=f'wall{i}',position=np.array(position),scale=np.array([1,1,2]),size=1))
    sensor = LidarRtx('/World/Lidar',translation=np.array([0.,0.,1.]),orientation=np.array([1.,0.,0.,0.]),config_file_name=args.config,**{'omni:sensor:Core:scanRateBaseHz':args.scan_hz})
    world.reset()
    sensor.initialize()

    name = 'IsaacExtractRTXSensorPointCloudNoAccumulator'
    sensor.attach_annotator(name)
    counts=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        data=sensor.get_current_frame().get(name,{})
        points=np.asarray(data.get('data',np.empty((0,3))))
        counts.append(int(len(points)))
    if not points.size:
        raise RuntimeError('No returns from RTX Lidar; inspect sensor config and timeline')
    np.save(output/'points.npy',points)
    (output/'measurements.json').write_text(json.dumps({'config':args.config,'scan_hz':args.scan_hz,'returns_per_frame':counts,'last_shape':list(points.shape)},indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                data = sensor.get_current_frame().get(name, {})
    if app.is_running():
        sensor.detach_all_annotators()
finally:
    app.close()
