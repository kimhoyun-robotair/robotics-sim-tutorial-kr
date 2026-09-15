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
parser.add_argument('--separation', type=float, default=.8, help='Center separation in meters for unit cubes')

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
    enable_extension('isaacsim.sensors.physx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.physx import ProximitySensor,register_sensor,clear_sensors
    world.scene.add_default_ground_plane()
    cube1=world.scene.add(DynamicCuboid('/World/Cube1',name='cube1',position=np.array([args.separation/2,0.,3.]),size=1,mass=1))
    cube2=world.scene.add(DynamicCuboid('/World/Cube2',name='cube2',position=np.array([-args.separation/2,0.,3.]),size=1,mass=1))
    sensor=ProximitySensor(cube1.prim)
    register_sensor(sensor)
    world.reset()
    rows=[]
    try:
        for _ in range(sample_steps):
            if not app.is_running():
                raise SystemExit(0)
            world.step(render=True)
            if not app.is_running():
                raise SystemExit(0)
            data=sensor.get_data()
            rows.append({'simulation_time_s':float(world.current_time),'overlaps':{str(path):{'distance':float(value['distance']),'duration':float(value['duration'])} for path,value in data.items()}})
        (output/'proximity.json').write_text(json.dumps(rows,indent=2))
        print({'frames':len(rows),'frames_with_overlap':sum(bool(r['overlaps']) for r in rows)})
        stage.GetRootLayer().Export(str(output/'scene.usda'))
        print(f'Output: {output.resolve()}')
        if args.steps is None and not args.headless:
            print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
            while app.is_running():
                world.step(render=True)
                if not app.is_running():
                    break
                if world.is_playing():
                    data = sensor.get_data()
    finally:
        clear_sensors()
finally:
    app.close()
