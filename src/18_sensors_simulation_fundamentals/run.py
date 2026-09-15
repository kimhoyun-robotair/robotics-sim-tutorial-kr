"""Isaac Sim 5.1 standalone sensor lab; see TUTORIAL.md for interpretation."""
import argparse
import json
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Positive acquisition frame limit; omitted: record 240 frames, then keep GUI open (headless: exit after 240)')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--interactive', action='store_true', help='Compatibility option: GUI stays open by default; explicit --steps still exits')
parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')
parser.add_argument('--height', type=float, default=2)
parser.add_argument('--ccd', action='store_true')

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
acquisition_steps = args.steps if args.steps is not None else 240
keep_gui_open = not args.headless and args.steps is None
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

    from pxr import UsdPhysics,PhysxSchema
    world.scene.add_default_ground_plane()
    with_collision=world.scene.add(DynamicCuboid('/World/WithCollider',name='with_collision',position=np.array([-1.,0.,args.height]),size=.5,mass=1))
    without_collision=world.scene.add(DynamicCuboid('/World/WithoutCollider',name='without_collision',position=np.array([1.,0.,args.height]),size=.5,mass=1))
    UsdPhysics.CollisionAPI(without_collision.prim).GetCollisionEnabledAttr().Set(False)
    if args.ccd:
        scene=world.get_physics_context().get_current_physics_scene_prim()
        PhysxSchema.PhysxSceneAPI.Apply(scene).CreateEnableCCDAttr(True)
        PhysxSchema.PhysxRigidBodyAPI.Apply(with_collision.prim).CreateEnableCCDAttr(True)
    world.reset()
    rows=[]
    for _ in range(acquisition_steps):
        if not app.is_running():
            break
        world.step(render=True)
        rows.append({'time_s':float(world.current_time),'with_collider_z':float(with_collision.get_world_pose()[0][2]),'without_collider_z':float(without_collision.get_world_pose()[0][2])})
    (output/'fall.json').write_text(json.dumps(rows,indent=2))
    stage.GetRootLayer().Export(str(output/'scene.usda'))
    print(f'Output: {output.resolve()}')
    while keep_gui_open and app.is_running():
        world.step(render=True)
finally:
    app.close()
