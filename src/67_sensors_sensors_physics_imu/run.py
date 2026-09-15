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
parser.add_argument('--filter-width', type=int, default=1)
parser.add_argument('--read-gravity', action=argparse.BooleanOptionalAction, default=True)

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

    from isaacsim.sensors.physics import IMUSensor, _sensor
    world.scene.add_default_ground_plane()
    cube=world.scene.add(DynamicCuboid('/World/Cube',name='cube',position=np.array([0.,0.,2.]),size=.5,mass=1))
    sensor=IMUSensor('/World/Cube/Imu',frequency=60,translation=np.zeros(3),orientation=np.array([1.,0.,0.,0.]),linear_acceleration_filter_size=args.filter_width,angular_velocity_filter_size=args.filter_width,orientation_filter_size=args.filter_width)
    world.reset()
    interface=_sensor.acquire_imu_sensor_interface()
    rows=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        reading=interface.get_sensor_reading('/World/Cube/Imu',use_latest_data=True,read_gravity=args.read_gravity)
        rows.append({'time_s':float(reading.time),'valid':bool(reading.is_valid),'linear_acceleration':[float(reading.lin_acc_x),float(reading.lin_acc_y),float(reading.lin_acc_z)],'angular_velocity':[float(reading.ang_vel_x),float(reading.ang_vel_y),float(reading.ang_vel_z)],'height_m':float(cube.get_world_pose()[0][2])})
    if not any(r['valid'] for r in rows):
        raise RuntimeError('No valid IMU readings')
    (output/'imu.json').write_text(json.dumps(rows,indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                reading = interface.get_sensor_reading('/World/Cube/Imu', use_latest_data=True, read_gravity=args.read_gravity)
finally:
    app.close()
