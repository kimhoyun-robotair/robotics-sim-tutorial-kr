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
parser.add_argument('--rays', type=int, default=9)

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
    cube=world.scene.add(FixedCuboid('/World/Target',name='target',position=np.array([3.,0.,1.]),size=.5))
    success,sensor=omni.kit.commands.execute('IsaacSensorCreateLightBeamSensor',path='/World/Curtain',translation=Gf.Vec3d(0,0,.25),num_rays=args.rays,curtain_length=1.5,forward_axis=Gf.Vec3d(1,0,0),curtain_axis=Gf.Vec3d(0,0,1),min_range=.1,max_range=10,draw_lines=True)
    if not success:
        raise RuntimeError('Lightbeam creation failed')
    interface=_range_sensor.acquire_lightbeam_sensor_interface()
    world.reset()
    rows=[]
    for i in range(sample_steps):
        cube.set_world_pose(position=np.array([3.,np.sin(i/30),1.]))
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        path=str(sensor.GetPath())
        hits=np.asarray(interface.get_beam_hit_data(path))
        depth=np.asarray(interface.get_linear_depth_data(path))
        rows.append({'time_s':float(world.current_time),'beam_hit':hits.tolist(),'depth_m':depth.tolist()})
    (output/'lightbeam.json').write_text(json.dumps(rows,indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        frame_index = sample_steps
        while app.is_running():
            if world.is_playing():
                cube.set_world_pose(position=np.array([3., np.sin(frame_index / 30), 1.]))
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                hits = np.asarray(interface.get_beam_hit_data(path))
                depth = np.asarray(interface.get_linear_depth_data(path))
                frame_index += 1
finally:
    app.close()
