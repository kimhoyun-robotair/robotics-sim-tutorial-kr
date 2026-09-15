"""Read, change, and verify the tutorial cube's USD translation through real ROS services."""
import argparse
import json
import math
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--position', type=float, nargs=3, default=[1, 2, 3], metavar=('X', 'Y', 'Z'))
parser.add_argument('--timeout', type=float, default=10.0)
args = parser.parse_args()
if not math.isfinite(args.timeout) or args.timeout <= 0 or not all(math.isfinite(x) for x in args.position):
    parser.error('timeout must be positive and all numeric arguments finite')
import rclpy
from isaac_ros2_messages.srv import GetPrimAttribute, SetPrimAttribute
rclpy.init()
node = rclpy.create_node('prim_attribute_lesson')
def call(service_type, name, request):
    client = node.create_client(service_type, name)
    try:
        if not client.wait_for_service(timeout_sec=args.timeout):
            raise TimeoutError(f'{name} unavailable; is Isaac Sim playing?')
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=args.timeout)
        if not future.done():
            raise TimeoutError(f'{name} did not respond')
        response = future.result()
        if not response.success:
            raise RuntimeError(response.message)
        return response
    finally:
        node.destroy_client(client)
try:
    request = GetPrimAttribute.Request(path='/World/Cube', attribute='xformOp:translate')
    before = call(GetPrimAttribute, '/get_prim_attribute', request)
    print('before:', before.value)
    call(SetPrimAttribute, '/set_prim_attribute', SetPrimAttribute.Request(
        path='/World/Cube', attribute='xformOp:translate', value=json.dumps(args.position)))
    after = call(GetPrimAttribute, '/get_prim_attribute', request)
    actual = json.loads(after.value)
    if len(actual) != 3 or any(abs(a-b)>1e-6 for a,b in zip(actual,args.position)):
        raise RuntimeError(f'Read-back differs: wanted {args.position}, received {actual}')
    print('verified translation:', actual)
finally:
    node.destroy_node()
    rclpy.shutdown()
