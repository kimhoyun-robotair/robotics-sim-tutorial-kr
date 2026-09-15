"""Create the hierarchy and String/TF graphs for the namespace lab in Script Editor."""
import asyncio
import omni.graph.core as og
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom
from isaacsim.core.utils.extensions import enable_extension

enable_extension('isaacsim.ros2.bridge')
async def setup():
    stage = omni.usd.get_context().get_stage()
    if stage is None or stage.GetPrimAtPath('/mock_robot'):
        raise RuntimeError('Open a new stage without /mock_robot first')
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    positions = {'': (0,0,0), '/base_link': (0,0,0),
                 '/base_link/lidar_link': (0,0,0.4), '/base_link/camera_link': (0,0,0.2),
                 '/base_link/wheel_left': (-0.2,0,0), '/base_link/wheel_right': (0.2,0,0)}
    for suffix, pos in positions.items():
        xf = UsdGeom.Xform.Define(stage, '/mock_robot' + suffix)
        xf.AddTranslateOp().Set(Gf.Vec3d(*pos))
    for name in ['lidar_link','camera_link','wheel_left']:
        prim = stage.GetPrimAtPath('/mock_robot/base_link/'+name)
        prim.CreateAttribute('isaac:namespace', Sdf.ValueTypeNames.String, custom=True).Set(name)
    keys = og.Controller.Keys
    prefix = '/mock_robot/base_link/wheel_left'
    og.Controller.edit({'graph_path': prefix+'/String_graph', 'evaluator_name': 'execution'}, {
        keys.CREATE_NODES: [('Tick','omni.graph.action.OnPlaybackTick'),
                            ('Publisher','isaacsim.ros2.bridge.ROS2Publisher')],
        keys.SET_VALUES: [('Publisher.inputs:messagePackage','std_msgs'),
                          ('Publisher.inputs:messageSubfolder','msg'),
                          ('Publisher.inputs:messageName','String'),
                          ('Publisher.inputs:topicName','topic')],
        keys.CONNECT: [('Tick.outputs:tick','Publisher.inputs:execIn')]})
    await omni.kit.app.get_app().next_update_async()
    og.Controller.attribute(prefix+'/String_graph/Publisher.inputs:data').set('wheel namespace lesson')
    og.Controller.edit({'graph_path': prefix+'/TF_graph', 'evaluator_name': 'execution'}, {
        keys.CREATE_NODES: [('Tick','omni.graph.action.OnPlaybackTick'),
                            ('Time','isaacsim.core.nodes.IsaacReadSimulationTime'),
                            ('TF','isaacsim.ros2.bridge.ROS2PublishTransformTree')],
        keys.SET_VALUES: [('TF.inputs:targetPrims',[Sdf.Path('/mock_robot')])],
        keys.CONNECT: [('Tick.outputs:tick','TF.inputs:execIn'),
                       ('Time.outputs:simulationTime','TF.inputs:timeStamp')]})
    print('Hierarchy and wheel String/TF graphs created; add Hawk/Lidar following TUTORIAL.md.')

namespace_setup_task = asyncio.ensure_future(setup())
