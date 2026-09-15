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
parser.add_argument('--mass', type=float, default=1)

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

    from isaacsim.sensors.physics import ContactSensor, _sensor
    world.scene.add_default_ground_plane()
    cube=world.scene.add(DynamicCuboid('/World/Cube',name='cube',position=np.array([0.,0.,2.]),size=.5,mass=args.mass))
    sensor=ContactSensor('/World/Cube/Contact',frequency=60,min_threshold=0,max_threshold=1e7,radius=-1)
    world.reset()
    interface=_sensor.acquire_contact_sensor_interface()
    rows=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        reading=interface.get_sensor_reading('/World/Cube/Contact',use_latest_data=True)
        rows.append({'time_s':float(reading.time),'valid':bool(reading.is_valid),'contact':bool(reading.in_contact),'force_N':float(reading.value),'height_m':float(cube.get_world_pose()[0][2])})
    if not any(r['valid'] and r['contact'] for r in rows):
        raise RuntimeError('No valid contact observed; simulate long enough for the cube to land')
    (output/'contact.json').write_text(json.dumps(rows,indent=2))
    print({'last_force_N':rows[-1]['force_N'],'weight_N':args.mass*9.81})
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                reading = interface.get_sensor_reading('/World/Cube/Contact', use_latest_data=True)
finally:
    app.close()
