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

    from pxr import UsdGeom,UsdPhysics,Gf
    from isaacsim.core.prims import SingleArticulation
    world.scene.add_default_ground_plane()
    UsdGeom.Xform.Define(stage,'/World/Arm')
    root=DynamicCuboid('/World/Arm/Base',name='base',position=np.array([0.,0.,2.]),size=.2,mass=1)
    link=DynamicCuboid('/World/Arm/Link',name='link',position=np.array([.75,0.,2.]),scale=np.array([1.5,.15,.15]),size=1,mass=args.mass)
    fixed=UsdPhysics.FixedJoint.Define(stage,'/World/Arm/FixedRoot')
    fixed.CreateBody1Rel().SetTargets(['/World/Arm/Base'])
    fixed.CreateLocalPos0Attr(Gf.Vec3f(0,0,2))
    UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
    joint=UsdPhysics.RevoluteJoint.Define(stage,'/World/Arm/Joint')
    joint.CreateBody0Rel().SetTargets(['/World/Arm/Base'])
    joint.CreateBody1Rel().SetTargets(['/World/Arm/Link'])
    joint.CreateLocalPos0Attr(Gf.Vec3f(0,0,0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(-.75,0,0))
    joint.CreateAxisAttr('Y')
    joint.CreateLowerLimitAttr(-80)
    joint.CreateUpperLimitAttr(80)
    drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'angular')
    drive.CreateStiffnessAttr(100)
    drive.CreateDampingAttr(10)
    drive.CreateTargetPositionAttr(0)
    robot=world.scene.add(SingleArticulation('/World/Arm',name='arm'))

    world.reset()
    dof=robot.get_dof_index('Joint')
    link_index=robot._articulation_view.get_link_index('Link')
    rows=[]
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
        rows.append({'time_s':float(world.current_time),'applied_effort_Nm':float(robot.get_applied_joint_efforts()[dof]),'measured_effort_Nm':float(robot.get_measured_joint_efforts()[dof]),'incoming_force_torque':robot.get_measured_joint_forces()[link_index].tolist()})
    (output/'joint_forces.json').write_text(json.dumps({'dof_index':int(dof),'link_index':int(link_index),'samples':rows},indent=2))
    stage.GetRootLayer().Export(str(output/'arm.usda'))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
            if world.is_playing():
                robot.get_applied_joint_efforts()
                robot.get_measured_joint_efforts()
                robot.get_measured_joint_forces()
finally:
    app.close()
