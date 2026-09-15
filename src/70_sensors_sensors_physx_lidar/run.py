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
parser.add_argument('--rotation-rate', type=float, default=0)
parser.add_argument('--no-colliders', action='store_true')

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
    from pxr import Gf,UsdPhysics,Semantics
    enable_extension('isaacsim.sensors.physx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.physx import _range_sensor
    for i,y in enumerate((-2.,2.)):
        cube=world.scene.add(FixedCuboid(f'/World/Target{i}',name=f'target{i}',position=np.array([4.,y,1.]),size=1))
        sem=Semantics.SemanticsAPI.Apply(cube.prim,'Semantics')
        sem.CreateSemanticTypeAttr('class')
        sem.CreateSemanticDataAttr(f'target_{i}')
        if args.no_colliders:
            UsdPhysics.CollisionAPI(cube.prim).GetCollisionEnabledAttr().Set(False)
    success,sensor=omni.kit.commands.execute('RangeSensorCreateLidar',path='/World/Lidar',translation=Gf.Vec3d(0,0,1),min_range=.1,max_range=20,horizontal_fov=360,vertical_fov=30,horizontal_resolution=1,vertical_resolution=2,rotation_rate=args.rotation_rate,draw_lines=True,high_lod=True,enable_semantics=True)
    if not success:
        raise RuntimeError('PhysX lidar creation failed')
    interface=_range_sensor.acquire_lidar_sensor_interface()
    world.reset()
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
    world.pause()
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    path=str(sensor.GetPath())
    depth=np.asarray(interface.get_linear_depth_data(path))
    points=np.asarray(interface.get_point_cloud_data(path))
    prims=interface.get_prim_data(path)
    if depth.size==0:
        raise RuntimeError('No PhysX lidar depth buffer')
    np.savez(output/'lidar.npz',depth=depth,points=points,azimuth=interface.get_azimuth_data(path),zenith=interface.get_zenith_data(path))
    (output/'hit_prims.json').write_text(json.dumps(np.asarray(prims).tolist(),indent=2))
    print({'depth_shape':list(depth.shape),'returns_below_max_range':int(np.count_nonzero(depth<20))})
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        world.play()
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                depth = np.asarray(interface.get_linear_depth_data(path))
                points = np.asarray(interface.get_point_cloud_data(path))
finally:
    app.close()
