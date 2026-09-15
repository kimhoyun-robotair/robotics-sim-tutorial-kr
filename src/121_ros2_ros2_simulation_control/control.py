"""Spawn a local USD, set/read its world pose, and step a paused Isaac Sim via ROS services."""
import argparse
import math
from pathlib import Path
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps',type=int,default=10)
parser.add_argument('--timeout',type=float,default=20)
parser.add_argument('--asset',type=Path,default=Path(__file__).with_name('cube.usda'))
parser.add_argument('--name',default='/ControlLessonCube')
parser.add_argument('--delete',action='store_true',help="Delete the entity spawned by this run after verification")
args = parser.parse_args()
if args.steps < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
    parser.error('steps and timeout must be positive')
if not args.asset.is_file():
    parser.error(f'Asset not found: {args.asset}')
import rclpy
from simulation_interfaces.msg import Result, SimulationState
from simulation_interfaces.srv import (GetSimulatorFeatures, SetSimulationState, GetSimulationState,
    SpawnEntity, SetEntityState, GetEntityState, StepSimulation, DeleteEntity)
rclpy.init()
node = rclpy.create_node('simulation_control_lesson')
def call(service_type,name,request):
    client = node.create_client(service_type,name)
    try:
        if not client.wait_for_service(timeout_sec=args.timeout):
            raise TimeoutError(f'Service {name} unavailable')
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node,future,timeout_sec=args.timeout)
        if not future.done():
            raise TimeoutError(f'Service {name} response timed out')
        response = future.result()
        if service_type is not GetSimulatorFeatures and response.result.result != Result.RESULT_OK:
            raise RuntimeError(f'{name}: {response.result.result} {response.result.error_message}')
        return response
    finally:
        node.destroy_client(client)
try:
    features = call(GetSimulatorFeatures,'/get_simulator_features',GetSimulatorFeatures.Request())
    print('Simulator features:',features)
    call(SetSimulationState,'/set_simulation_state',SetSimulationState.Request(
        state=SimulationState(state=SimulationState.STATE_PLAYING)))
    call(SetSimulationState,'/set_simulation_state',SetSimulationState.Request(
        state=SimulationState(state=SimulationState.STATE_PAUSED)))
    request = SpawnEntity.Request(name=args.name,allow_renaming=False,uri=str(args.asset.resolve()))
    request.initial_pose.pose.orientation.w = 1.0
    spawned = call(SpawnEntity,'/spawn_entity',request)
    entity = spawned.entity_name
    print('Spawned entity:',entity)
    move = SetEntityState.Request(entity=entity)
    move.state.header.frame_id = 'world'
    move.state.pose.position.x = 1.0
    move.state.pose.position.y = 2.0
    move.state.pose.position.z = 3.0
    move.state.pose.orientation.w = 1.0
    call(SetEntityState,'/set_entity_state',move)
    actual = call(GetEntityState,'/get_entity_state',GetEntityState.Request(entity=entity)).state.pose.position
    if any(abs(a-b)>1e-6 for a,b in zip([actual.x,actual.y,actual.z],[1,2,3])):
        raise RuntimeError(f'Unexpected world position: {actual}')
    print('Verified world position:',actual)
    call(StepSimulation,'/step_simulation',StepSimulation.Request(steps=args.steps))
    state = call(GetSimulationState,'/get_simulation_state',GetSimulationState.Request())
    if state.state.state != SimulationState.STATE_PAUSED:
        raise RuntimeError('StepSimulation did not return to PAUSED')
    print('Verified PAUSED after stepping')
    if args.delete:
        call(DeleteEntity,'/delete_entity',DeleteEntity.Request(entity=entity))
        print('Deleted entity created by this run:',entity)
finally:
    node.destroy_node()
    rclpy.shutdown()
