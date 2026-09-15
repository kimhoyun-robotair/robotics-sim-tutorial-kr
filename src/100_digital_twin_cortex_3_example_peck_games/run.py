"""Run the local Cortex behavior in a complete Franka workcell."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--headless", action="store_true")
parser.add_argument("--interactive", action="store_true", help="Wait for viewport Play before running")
parser.add_argument("--steps", type=int, default=None,
                    help="Physics steps before exit; omitted: GUI until closed, headless 1800")
parser.add_argument("--behavior", choices=['peck_state_machine', 'peck_decider_network', 'peck_game'], default='peck_state_machine')
args = parser.parse_args()
if (args.steps is not None and args.steps < 1) or (args.headless and args.interactive):
    parser.error("Use positive steps; interactive mode requires a window")
if args.steps is None and args.headless:
    args.steps = 1800
from isaacsim import SimulationApp
app = SimulationApp({"headless": args.headless})
try:
    import numpy as np
    from isaacsim.core.api.objects import DynamicCuboid
    from isaacsim.cortex.framework.cortex_utils import load_behavior_module
    from isaacsim.cortex.framework.cortex_world import CortexWorld
    from isaacsim.cortex.framework.robot import add_franka_to_stage
    world = CortexWorld()
    robot = world.add_robot(add_franka_to_stage(name="franka", prim_path="/World/Franka"))
    specs = [("RedCube", [0.7, 0, 0]), ("BlueCube", [0, 0, 0.7]),
             ("YellowCube", [0.7, 0.7, 0]), ("GreenCube", [0, 0.7, 0])]
    width = 0.0515
    for x, (name, color) in zip(np.linspace(0.3, 0.7, 4), specs):
        cube = world.scene.add(DynamicCuboid(prim_path=f"/World/Obs/{name}", name=name,
                  size=width, color=np.array(color), position=np.array([x, -0.4, width / 2])))
        robot.register_obstacle(cube)
    world.scene.add_default_ground_plane()
    module = load_behavior_module(str(Path(__file__).resolve().parent / (args.behavior + ".py")))
    network = module.make_decider_network(robot)
    world.add_decider_network(network)
    world.run(app, play_on_entry=not args.interactive,
              is_done_cb=lambda: args.steps is not None and world.current_time_step_index >= args.steps)
    print(f"Cortex loop ended at physics step {world.current_time_step_index}; inspect task behavior separately")
finally:
    app.close()
