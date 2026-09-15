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
parser.add_argument('--lens', choices=['none','pinhole','fisheye'], default='none')

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

    from isaacsim.sensors.camera import Camera
    from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
    world.scene.add_default_ground_plane()
    for i, x in enumerate((-1.0, 0.0, 1.0)):
        world.scene.add(FixedCuboid(prim_path=f'/World/Box{i}', name=f'box{i}', position=np.array([x, 0, .5]), size=.8, color=np.array([i/2, .3, 1-i/2])))
    camera = Camera('/World/Camera', position=np.array([0., 0., 5.]), orientation=euler_angles_to_quats(np.array([0.,90.,0.]), degrees=True), resolution=(640,480), frequency=30)
    world.reset()
    camera.initialize()
    camera.add_motion_vectors_to_frame()
    camera.set_focal_length(.018)
    camera.set_horizontal_aperture(.036)
    camera.set_vertical_aperture(.027)
    camera.set_lens_aperture(0)
    if args.lens == 'none':
        camera.set_opencv_pinhole_properties(cx=320, cy=240, fx=320, fy=320, pinhole=[0.0]*12)
    elif args.lens == 'pinhole':
        camera.set_opencv_pinhole_properties(cx=320, cy=240, fx=320, fy=320, pinhole=[.14,-.03,0,0,.009,0,0,0])
    elif args.lens == 'fisheye':
        camera.set_opencv_fisheye_properties(cx=320, cy=240, fx=320, fy=320, fisheye=[.05,.01,-.003,-.0005])
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
    rgba = camera.get_rgba()
    if rgba.size == 0:
        raise RuntimeError('Camera returned no image; increase steps and inspect renderer logs')
    from PIL import Image
    Image.fromarray(rgba.astype(np.uint8)).save(output/'rgba.png')
    points = np.array([[-1.,0.,.9],[0.,0.,.9],[1.,0.,.9]])
    intrinsic = np.array([[320.,0.,320.],[0.,320.,240.],[0.,0.,1.]])
    world_homogeneous = np.column_stack((points,np.ones(len(points))))
    image_homogeneous = (intrinsic @ camera.get_view_matrix_ros()[:3,:] @ world_homogeneous.T).T
    projected = image_homogeneous[:,:2] / image_homogeneous[:,2:3] if args.lens != 'fisheye' else np.empty((0,2))
    frame = camera.get_current_frame()
    np.savez(output/'camera.npz', rgba=rgba, projected_points=projected, motion_vectors=frame['motion_vectors'])
    (output/'measurements.json').write_text(json.dumps({'lens':args.lens,'rgba_shape':list(rgba.shape),'projected_points':projected.tolist(),'projection_note':'Ideal pinhole projection of configured K; distorted lens modes require their own distortion mapping','intrinsic_matrix':intrinsic.tolist()},indent=2))
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
