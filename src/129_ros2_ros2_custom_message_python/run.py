"""Publish a Python-3.11-built SampleMsg from Isaac Sim's rclpy."""
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--steps', type=int, default=None, help='App updates before exit; omitted: GUI until closed, headless uses --frames')
parser.add_argument('--frames', type=int, default=1200, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
parser.add_argument('--headless', action='store_true')
parser.add_argument('--number', type=int, default=23)
args = parser.parse_args()
if args.frames < 1 or not -(2**63) <= args.number < 2**63:
    parser.error('frames must be positive and number must fit int64')
if args.steps is not None and args.steps < 1:
    parser.error('--steps must be positive')
if args.steps is None and args.headless:
    args.steps = args.frames
from isaacsim import SimulationApp
app = SimulationApp({'headless': args.headless})
try:
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.ros2.bridge')
    app.update()
    import rclpy
    from custom_message.msg import SampleMsg
    rclpy.init()
    node = rclpy.create_node('custom_message_from_isaac')
    try:
        publisher = node.create_publisher(SampleMsg, '/custom_sample', 10)
        message = SampleMsg()
        message.my_string.data = 'hello from Isaac Sim 5.1'
        message.my_num = args.number
        print('Constructed custom message:', message)
        frame = 0
        while app.is_running() and (args.steps is None or frame < args.steps):
            if frame % 30 == 0:
                publisher.publish(message)
            rclpy.spin_once(node, timeout_sec=0.0)
            app.update()
            frame += 1
    finally:
        node.destroy_node()
        rclpy.shutdown()
finally:
    app.close()
