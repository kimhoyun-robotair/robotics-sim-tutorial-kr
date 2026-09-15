"""Generic Pose publisher/subscriber: read and write full Cube translation and quaternion."""
import asyncio
import omni.graph.core as og
import omni.kit.app
import omni.usd
from pxr import Gf, Sdf, UsdGeom
from isaacsim.core.utils.extensions import enable_extension

enable_extension('isaacsim.ros2.bridge')
async def setup():
    stage = omni.usd.get_context().get_stage()
    if stage is None or stage.GetPrimAtPath('/GenericPose') or stage.GetPrimAtPath('/World/Cube'):
        raise RuntimeError('Use a new stage without /GenericPose or /World/Cube')
    UsdGeom.SetStageMetersPerUnit(stage,1.0)
    UsdGeom.Xform.Define(stage,'/World')
    cube = UsdGeom.Cube.Define(stage,'/World/Cube')
    cube.CreateSizeAttr(0.5)
    cube.AddTranslateOp().Set(Gf.Vec3d(0,0,0.5))
    cube.AddOrientOp().Set(Gf.Quatf(1,0,0,0))
    keys = og.Controller.Keys
    values = [('Pub.inputs:topicName','/object_pose_observed'),('Sub.inputs:topicName','/object_pose'),
              ('Read.inputs:prim',[Sdf.Path('/World/Cube')]),('Read.inputs:name','xformOp:translate'),
              ('Write.inputs:prim',[Sdf.Path('/World/Cube')]),('Write.inputs:name','xformOp:translate'),
              ('ReadOrientation.inputs:prim',[Sdf.Path('/World/Cube')]),
              ('ReadOrientation.inputs:name','xformOp:orient'),
              ('WriteOrientation.inputs:prim',[Sdf.Path('/World/Cube')]),
              ('WriteOrientation.inputs:name','xformOp:orient'),
              ('ToQuaternion.inputs:role','Quaternion')]
    for node in ['Pub','Sub']:
        values.extend([(node+'.inputs:messagePackage','geometry_msgs'),
                       (node+'.inputs:messageSubfolder','msg'),(node+'.inputs:messageName','Pose')])
    og.Controller.edit({'graph_path':'/GenericPose','evaluator_name':'execution'}, {
        keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),
                           ('Context','isaacsim.ros2.bridge.ROS2Context'),
                           ('Pub','isaacsim.ros2.bridge.ROS2Publisher'),
                           ('Sub','isaacsim.ros2.bridge.ROS2Subscriber'),
                           ('Read','omni.graph.nodes.ReadPrimAttribute'),
                           ('Break','omni.graph.nodes.BreakVector3'),
                           ('Make','omni.graph.nodes.MakeVector3'),
                           ('Write','omni.graph.nodes.WritePrimAttribute'),
                           ('ReadOrientation','omni.graph.nodes.ReadPrimAttribute'),
                           ('BreakOrientation','omni.graph.nodes.BreakVector4'),
                           ('MakeOrientation','omni.graph.nodes.MakeVector4'),
                           ('ToQuaternion','omni.graph.nodes.ToFloat'),
                           ('WriteOrientation','omni.graph.nodes.WritePrimAttribute')],
        keys.SET_VALUES:values,
        keys.CONNECT:[('Tick.outputs:tick','Pub.inputs:execIn'),('Tick.outputs:tick','Sub.inputs:execIn'),
                      ('Context.outputs:context','Pub.inputs:context'),('Context.outputs:context','Sub.inputs:context'),
                      ('Read.outputs:value','Break.inputs:tuple'),('Make.outputs:tuple','Write.inputs:value'),
                      ('Sub.outputs:execOut','Write.inputs:execIn'),
                      ('ReadOrientation.outputs:value','BreakOrientation.inputs:tuple'),
                      ('MakeOrientation.outputs:tuple','ToQuaternion.inputs:value'),
                      ('ToQuaternion.outputs:converted','WriteOrientation.inputs:value'),
                      ('Sub.outputs:execOut','WriteOrientation.inputs:execIn')]})
    await omni.kit.app.get_app().next_update_async()
    connections = []
    for axis in ['x','y','z']:
        connections.extend([('Break.outputs:'+axis,'Pub.inputs:position:'+axis),
                            ('Sub.outputs:position:'+axis,'Make.inputs:'+axis)])
    # OG quaternion storage is [real, i, j, k]; Make/Break4 labels are tuple slots.
    for slot, ros_axis in [('x','w'),('y','x'),('z','y'),('w','z')]:
        connections.extend([('BreakOrientation.outputs:'+slot,'Pub.inputs:orientation:'+ros_axis),
                            ('Sub.outputs:orientation:'+ros_axis,'MakeOrientation.inputs:'+slot)])
    og.Controller.edit('/GenericPose',{keys.CONNECT:connections})
    print('Full Pose graph ready. Play and publish /object_pose; observe /object_pose_observed.')
generic_pose_setup_task = asyncio.ensure_future(setup())
