"""Isaac Sim 5.1 standalone sensor lab; see TUTORIAL.md for interpretation."""
import argparse
import json
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Positive app update limit; omitted: keep GUI open (headless: 240 updates)')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--interactive', action='store_true', help='Compatibility option: GUI stays open by default; explicit --steps still exits')
parser.add_argument('--output', type=Path, help='New output directory; existing paths are refused')

args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error('steps must be positive; interactive requires GUI')
step_limit = args.steps if args.steps is not None else (240 if args.headless else None)
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

    from pxr import UsdGeom
    UsdGeom.Xform.Define(stage,'/World/StaticSet')
    for i in range(2):
        cube=VisualCuboid(f'/World/StaticSet/Box{i}',name=f'box{i}',position=np.array([i*2,0.,1.]),size=1)
        if i==1:
            UsdGeom.Imageable(cube.prim).MakeInvisible()
    world.reset()
    world.stop()
    stage.GetRootLayer().Export(str(output/'static_scene.usda'))
    print('Tools > Physics API Editor: select /World/StaticSet and follow TUTORIAL.md.')
    print(f'Output: {output.resolve()}')
    update_count = 0
    while app.is_running() and (step_limit is None or update_count < step_limit):
        app.update()
        update_count += 1
finally:
    app.close()
