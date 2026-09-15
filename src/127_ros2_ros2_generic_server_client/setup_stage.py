"""Create a SetBool generic ROS server and impulse-controlled client in Script Editor."""
import asyncio
import omni.graph.core as og
import omni.kit.app
import omni.usd
from isaacsim.core.utils.extensions import enable_extension

enable_extension('isaacsim.ros2.bridge')
async def setup():
    stage = omni.usd.get_context().get_stage()
    if stage is None or stage.GetPrimAtPath('/ServiceLab'):
        raise RuntimeError('Use a new stage without /ServiceLab')
    keys = og.Controller.Keys
    values = []
    for node in ['Request','Response','Client']:
        values.extend([(node+'.inputs:messagePackage','std_srvs'),
                       (node+'.inputs:messageSubfolder','srv'),
                       (node+'.inputs:messageName','SetBool')])
    values.extend([('Request.inputs:serviceName','/service_name'),
                   ('Client.inputs:serviceName','/service_name')])
    graph, _, _, _ = og.Controller.edit({'graph_path':'/ServiceLab','evaluator_name':'execution'}, {
        keys.CREATE_NODES: [('Tick','omni.graph.action.OnPlaybackTick'),
                            ('Impulse','omni.graph.action.OnImpulseEvent'),
                            ('Context','isaacsim.ros2.bridge.ROS2Context'),
                            ('Request','isaacsim.ros2.bridge.OgnROS2ServiceServerRequest'),
                            ('Response','isaacsim.ros2.bridge.OgnROS2ServiceServerResponse'),
                            ('Client','isaacsim.ros2.bridge.OgnROS2ServiceClient')],
        keys.SET_VALUES: values,
        keys.CONNECT: [('Tick.outputs:tick','Request.inputs:execIn'),
                       ('Impulse.outputs:execOut','Client.inputs:execIn'),
                       ('Context.outputs:context','Request.inputs:context'),
                       ('Context.outputs:context','Response.inputs:context'),
                       ('Context.outputs:context','Client.inputs:context'),
                       ('Request.outputs:serverHandle','Response.inputs:serverHandle'),
                       ('Request.outputs:onReceived','Response.inputs:onReceived')]})
    await omni.kit.app.get_app().next_update_async()
    og.Controller.attribute('/ServiceLab/Response.inputs:Response:success').set(True)
    og.Controller.attribute('/ServiceLab/Response.inputs:Response:message').set('Accepted by Isaac Sim SetBool lab')
    og.Controller.attribute('/ServiceLab/Client.inputs:Request:data').set(True)
    print('Press Play. CLI requests work immediately; trigger Client with enableImpulse=True.')

service_setup_task = asyncio.ensure_future(setup())
