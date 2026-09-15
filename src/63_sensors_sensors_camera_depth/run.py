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
parser.add_argument('--baseline-mm', type=float, default=55)
parser.add_argument('--noise-sigma', type=float, default=1)

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

    from isaacsim.sensors.camera import SingleViewDepthSensor
    from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
    world.scene.add_default_ground_plane()
    for i,z in enumerate((.5,1.2)):
        world.scene.add(FixedCuboid(prim_path=f'/World/Box{i}',name=f'box{i}',position=np.array([i-.5,0,z/2]),scale=np.array([.6,.6,z]),size=1))
    camera = SingleViewDepthSensor('/World/Depth', position=np.array([0.,0.,4.]), orientation=euler_angles_to_quats(np.array([0.,90.,0.]),degrees=True), resolution=(640,480), frequency=30)
    world.reset()
    camera.initialize(attach_rgb_annotator=False)
    camera.set_focal_length(.018)
    camera.set_horizontal_aperture(.036)
    camera.set_vertical_aperture(.027)
    camera.set_baseline_mm(args.baseline_mm)
    camera.set_focal_length_pixel(320)
    camera.set_sensor_size_pixel(640)
    camera.set_max_disparity_pixel(110)
    camera.set_noise_mean(.5)
    camera.set_noise_sigma(args.noise_sigma)
    camera.set_min_distance(.5)
    camera.set_max_distance(100)
    camera.attach_annotator('DepthSensorDistance')
    camera.attach_annotator('distance_to_image_plane')
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
    frame = camera.get_current_frame()
    arrays = {key:np.asarray(frame[key]) for key in ('DepthSensorDistance','distance_to_image_plane')}
    report = {}
    for key,array in arrays.items():
        valid = array[np.isfinite(array)&(array>0)]
        if not valid.size:
            raise RuntimeError(f'No finite positive depth for {key}')
        report[key] = {'shape':list(array.shape),'valid_pixels':int(valid.size),'median_m':float(np.median(valid))}
    np.savez(output/'depth.npz',**arrays)
    (output/'measurements.json').write_text(json.dumps(report,indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                frame = camera.get_current_frame()
finally:
    app.close()
