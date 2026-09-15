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

    from isaacsim.core.api.materials import OmniPBR
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.sensors.rtx')
    app.update()
    if not app.is_running():
        raise SystemExit(0)
    from isaacsim.sensors.rtx import apply_nonvisual_material
    materials=[('aluminum','paint','emissive'),('steel','clearcoat','emissive'),('concrete','paint','emissive')]
    report=[]
    for i,(base,coating,behavior) in enumerate(materials):
        cube=VisualCuboid(f'/World/Box{i}',name=f'box{i}',position=np.array([0,i*2,1.]),color=np.array([.3,.6,.8]))
        mat=OmniPBR(prim_path=f'/World/Looks/Material{i}',name=f'material{i}',color=np.array([.3,.6,.8]))
        apply_nonvisual_material(mat.prim,base,coating,behavior)
        cube.apply_visual_material(mat)
        attrs={a.GetName():str(a.Get()) for a in mat.prim.GetAttributes() if 'sensor' in a.GetName().lower() or 'nonvisual' in a.GetName().lower()}
        report.append({'prim':str(mat.prim.GetPath()),'base':base,'coating':coating,'behavior':behavior,'authored_attributes':attrs})
    world.reset()
    for _ in range(sample_steps):
        if not app.is_running():
            raise SystemExit(0)
        world.step(render=True)
        if not app.is_running():
            raise SystemExit(0)
    stage.GetRootLayer().Export(str(output/'materials.usda'))
    (output/'material_attributes.json').write_text(json.dumps(report,indent=2))
    print(f'Output: {output.resolve()}')
    if args.steps is None and not args.headless:
        print('Snapshot saved. Live simulation continues until you close the GUI; files are not appended.')
        while app.is_running():
            world.step(render=True)
            if not app.is_running():
                break
finally:
    app.close()
