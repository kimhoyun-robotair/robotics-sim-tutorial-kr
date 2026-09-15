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
parser.add_argument('--pattern', choices=['zigzag','two-band'], default='zigzag')

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

    import omni.kit.commands
    from isaacsim.core.utils.extensions import enable_extension
    from pxr import Gf
    enable_extension('isaacsim.sensors.physx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.physx import _range_sensor
    world.scene.add(FixedCuboid('/World/Wall',name='wall',position=np.array([5.,0.,1.]),scale=np.array([.2,8.,4.]),size=1))
    success,sensor=omni.kit.commands.execute('RangeSensorCreateGeneric',path='/World/Generic',translation=Gf.Vec3d(0,0,1),min_range=.1,max_range=20,draw_points=True,draw_lines=False,sampling_rate=2400)
    if not success:
        raise RuntimeError('Generic sensor creation failed')
    path=str(sensor.GetPath())
    interface=_range_sensor.acquire_generic_sensor_interface()
    phase=np.linspace(0,1,12000,endpoint=False)
    azimuth=.5*(2/np.pi)*np.arcsin(np.sin(2*np.pi*10*phase))
    elevation=.2*np.sin(2*np.pi*phase) if args.pattern == 'zigzag' else np.where(phase < .5,-.2,.2)
    pattern=np.stack((azimuth,elevation)).copy()
    offsets=np.zeros((pattern.shape[1],3))
    world.reset()
    batches=0
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        if interface.send_next_batch(path):
            interface.set_next_batch_rays(path,pattern)
            interface.set_next_batch_offsets(path,offsets)
            batches+=1
    world.pause()
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    depth=np.asarray(interface.get_linear_depth_data(path))
    if not depth.size:
        raise RuntimeError('No generic sensor depth; inspect batching and sampling rate')
    np.savez(output/'pattern_and_depth.npz',angles_rad=pattern,origin_offsets_m=offsets,depth_m=depth)
    (output/'measurements.json').write_text(json.dumps({'batches_sent':batches,'rays_in_batch':int(pattern.shape[1]),'last_depth_count':int(depth.size),'min_depth_m':float(depth.min())},indent=2))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        world.play()
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                if interface.send_next_batch(path):
                    interface.set_next_batch_rays(path, pattern)
                    interface.set_next_batch_offsets(path, offsets)
                depth = np.asarray(interface.get_linear_depth_data(path))
finally:
    app.close()
