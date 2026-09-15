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
parser.add_argument('--target-speed', type=float, default=-.5)

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
sample_steps = args.steps if args.steps is not None else 240
output = args.output or Path(__file__).resolve().parent / 'output' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
output.mkdir(parents=True, exist_ok=False)
from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless, 'enable_motion_bvh': True})
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
    import omni.replicator.core as rep
    from isaacsim.core.utils.extensions import enable_extension
    from pxr import Gf, UsdPhysics
    enable_extension('isaacsim.sensors.rtx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    world.scene.add_default_ground_plane()
    target=world.scene.add(DynamicCuboid('/World/Target',name='target',position=np.array([8.,0.,1.]),scale=np.array([1.,3.,2.]),size=1,mass=1))
    from pxr import PhysxSchema
    PhysxSchema.PhysxRigidBodyAPI.Apply(target.prim).CreateDisableGravityAttr(True)
    success,sensor=omni.kit.commands.execute('IsaacSensorCreateRtxRadar',path='/World/Radar',translation=Gf.Vec3d(0,0,1),orientation=Gf.Quatd(1,0,0,0),force_camera_prim=False)
    if not success:
        raise RuntimeError('RTX radar creation failed')
    product=rep.create.render_product(sensor.GetPath(),(1,1))
    annotator=rep.AnnotatorRegistry.get_annotator('IsaacExtractRTXSensorPointCloudNoAccumulator')
    annotator.attach([product.path])
    world.reset()
    target.set_linear_velocity(np.array([args.target_speed,0.,0.]))
    counts=[]
    last_nonempty=None
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        data=annotator.get_data()
        points=np.asarray(data.get('data',[]))
        counts.append(int(len(points)))
        if points.size:
            last_nonempty=points.copy()
    if last_nonempty is None:
        raise RuntimeError('Radar produced no point cloud; check RTX GPU, Motion BVH and target in FOV')
    np.save(output/'points.npy',last_nonempty)
    (output/'measurements.json').write_text(json.dumps({'motion_bvh':True,'target_speed_m_s':args.target_speed,'returns_per_frame':counts,'target_final_position':target.get_world_pose()[0].tolist(),'note':'Point clouds alone do not expose Doppler velocity'},indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                data = annotator.get_data()
    if app.is_running():
        annotator.detach()
        product.destroy()
finally:
    app.close()
