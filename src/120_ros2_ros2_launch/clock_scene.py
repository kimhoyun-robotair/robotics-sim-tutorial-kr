"""A standalone scene launched through the official ROS isaacsim launcher."""
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='Simulation steps before exit; omitted: GUI until closed, headless 3600')
parser.add_argument('--headless', action='store_true')
args = parser.parse_args()
if args.steps is not None and args.steps < 1:
    parser.error('steps must be positive')
if args.steps is None and args.headless:
    args.steps = 3600
from isaacsim import SimulationApp
app = SimulationApp({'headless':args.headless})
try:
    import omni.graph.core as og
    import numpy as np
    from isaacsim.core.api import World
    from isaacsim.core.api.objects import DynamicCuboid
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.ros2.bridge')
    app.update()
    world = World(stage_units_in_meters=1)
    world.scene.add_default_ground_plane()
    cube = world.scene.add(DynamicCuboid(prim_path='/World/LaunchCube',name='launch_cube',
                                        position=np.array([0,0,2.0]),size=0.4))
    keys = og.Controller.Keys
    og.Controller.edit({'graph_path':'/LaunchClock','evaluator_name':'execution'}, {
        keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),
                           ('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),
                           ('Clock','isaacsim.ros2.bridge.ROS2PublishClock')],
        keys.CONNECT:[('Tick.outputs:tick','Clock.inputs:execIn'),
                      ('Time.outputs:simulationTime','Clock.inputs:timeStamp')],
        keys.SET_VALUES:[('Clock.inputs:topicName','/clock')]})
    world.reset()
    world.play()
    world.step(render=True)
    print('LOCAL_CLOCK_SCENE_READY',flush=True)
    step = 0
    while app.is_running() and (args.steps is None or step < args.steps):
        world.step(render=True)
        step += 1
    print('Final cube world position:',cube.get_world_pose()[0],flush=True)
    world.stop()
finally:
    app.close()
