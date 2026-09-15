"""Build the Ackermann graph after placing Leatherback at /Leatherback in the GUI."""
import omni.graph.core as og
import omni.usd
from pxr import Sdf
from isaacsim.core.utils.extensions import enable_extension

enable_extension('isaacsim.ros2.bridge')
enable_extension('isaacsim.robot.wheeled_robots')
stage = omni.usd.get_context().get_stage()
if stage is None or not stage.GetPrimAtPath('/Leatherback'):
    raise RuntimeError('Load the Leatherback USD at /Leatherback before running this file')
if stage.GetPrimAtPath('/AckermannLab'):
    raise RuntimeError('/AckermannLab exists; use a fresh tutorial stage')
keys = og.Controller.Keys
values = [('Subscribe.inputs:topicName','ackermann_cmd'),
          ('Steer.inputs:targetPrim',[Sdf.Path('/Leatherback')]),
          ('Wheels.inputs:targetPrim',[Sdf.Path('/Leatherback')]),
          ('Steer.inputs:jointNames',['Knuckle__Upright__Front_Left','Knuckle__Upright__Front_Right']),
          ('Wheels.inputs:jointNames',['Wheel__Knuckle__Front_Left','Wheel__Knuckle__Front_Right',
                                      'Wheel__Upright__Rear_Left','Wheel__Upright__Rear_Right'])]
for name,value in {'backWheelRadius':0.052,'frontWheelRadius':0.052,'maxWheelRotation':0.7854,
                   'maxWheelVelocity':20.0,'trackWidth':0.24,'wheelBase':0.32,
                   'maxAcceleration':1.0,'maxSteeringAngleVelocity':1.0}.items():
    values.append(('Ackermann.inputs:'+name,value))
connections = [('Tick.outputs:tick','Subscribe.inputs:execIn'),
               ('Tick.outputs:tick','Ackermann.inputs:execIn'),
               ('Tick.outputs:deltaSeconds','Ackermann.inputs:dt'),
               ('Context.outputs:context','Subscribe.inputs:context'),
               ('QoS.outputs:qosProfile','Subscribe.inputs:qosProfile'),
               ('Ackermann.outputs:execOut','Steer.inputs:execIn'),
               ('Ackermann.outputs:execOut','Wheels.inputs:execIn'),
               ('Ackermann.outputs:wheelAngles','Steer.inputs:positionCommand'),
               ('Ackermann.outputs:wheelRotationVelocity','Wheels.inputs:velocityCommand')]
for name in ['speed','acceleration','steeringAngle','steeringAngleVelocity']:
    connections.append(('Subscribe.outputs:'+name,'Ackermann.inputs:'+name))
og.Controller.edit({'graph_path':'/AckermannLab','evaluator_name':'execution'}, {
    keys.CREATE_NODES:[('Tick','omni.graph.action.OnPlaybackTick'),
                       ('Context','isaacsim.ros2.bridge.ROS2Context'),
                       ('QoS','isaacsim.ros2.bridge.ROS2QoSProfile'),
                       ('Subscribe','isaacsim.ros2.bridge.ROS2SubscribeAckermannDrive'),
                       ('Ackermann','isaacsim.robot.wheeled_robots.AckermannController'),
                       ('Steer','isaacsim.core.nodes.IsaacArticulationController'),
                       ('Wheels','isaacsim.core.nodes.IsaacArticulationController')],
    keys.SET_VALUES:values,keys.CONNECT:connections})
print('Ackermann graph ready. Press Play and run drive.py in a ROS terminal.')
