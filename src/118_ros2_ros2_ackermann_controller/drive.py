"""Publish Ackermann commands or convert Twist commands for the Leatherback lab."""
import argparse
import math
import time
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=['drive','twist'], default='drive')
parser.add_argument('--seconds', type=float, default=15)
parser.add_argument('--speed', type=float, default=0.4, help='m/s for drive mode')
parser.add_argument('--steering', type=float, default=0.3, help='radians for drive mode')
parser.add_argument('--wheel-base', type=float, default=0.32)
parser.add_argument('--timeout', type=float, default=0.5, help='Stop if Twist input becomes stale')
args = parser.parse_args()
if not all(math.isfinite(x) for x in [args.seconds,args.speed,args.steering,args.wheel_base,args.timeout]):
    parser.error('numeric arguments must be finite')
if args.seconds <= 0 or args.wheel_base <= 0 or args.timeout <= 0:
    parser.error('seconds, wheel-base and timeout must be positive')
if abs(args.speed)>1.0 or abs(args.steering)>0.7854:
    parser.error('use |speed| <= 1 m/s and |steering| <= 0.7854 radians')
import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist
rclpy.init()
node = rclpy.create_node('leatherback_commands')
publisher = node.create_publisher(AckermannDriveStamped, '/ackermann_cmd', 10)
latest = {'speed': 0.0, 'steering': 0.0, 'time': -float('inf')}
def receive(message):
    speed = message.linear.x
    yaw_rate = message.angular.z
    if not math.isfinite(speed) or not math.isfinite(yaw_rate):
        node.get_logger().error('Ignored non-finite Twist')
        return
    speed = max(-1.0, min(1.0, speed))
    steering = math.atan(args.wheel_base * yaw_rate / speed) if abs(speed)>1e-6 else 0.0
    latest.update(speed=speed, steering=max(-0.7854,min(0.7854,steering)),time=time.monotonic())
subscription = node.create_subscription(Twist, '/cmd_vel', receive, 10) if args.mode=='twist' else None
def publish(speed, steering):
    message = AckermannDriveStamped()
    message.header.stamp = node.get_clock().now().to_msg()
    message.header.frame_id = 'base_link'
    message.drive.speed = speed
    message.drive.steering_angle = steering
    message.drive.acceleration = 0.5
    message.drive.steering_angle_velocity = 0.5
    publisher.publish(message)
def tick():
    if args.mode == 'drive':
        publish(args.speed,args.steering)
    elif time.monotonic()-latest['time'] <= args.timeout:
        publish(latest['speed'],latest['steering'])
    else:
        publish(0.0,0.0)
timer = node.create_timer(0.05,tick)
try:
    deadline = time.monotonic()+args.seconds
    while rclpy.ok() and time.monotonic()<deadline:
        rclpy.spin_once(node,timeout_sec=0.05)
finally:
    node.destroy_timer(timer)
    if rclpy.ok():
        publish(0.0,0.0)
        rclpy.spin_once(node,timeout_sec=0.1)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
