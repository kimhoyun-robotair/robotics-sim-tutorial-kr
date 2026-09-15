"""A nonblocking, independently owned rclpy subscriber inside an OmniGraph node."""
import rclpy
from rclpy.context import Context
from std_msgs.msg import Int32
import omni.graph.core as og
from isaacsim.core.nodes import BaseResetNode
from kr_ros2_fibonacci.ogn.OgnFibonacciDatabase import OgnFibonacciDatabase

class SubscriberState(BaseResetNode):
    def __init__(self):
        self.context = None
        self.node = None
        self.topic = None
        self.number = None
        super().__init__(initialize=False)

    def start(self, topic):
        self.context = Context()
        rclpy.init(context=self.context)
        try:
            self.node = rclpy.create_node('fibonacci_lesson', context=self.context)
            self.node.create_subscription(Int32, topic, self.receive, 10)
        except Exception:
            self.custom_reset()
            raise
        self.topic = topic
        self.initialized = True

    def receive(self, message):
        self.number = message.data

    def custom_reset(self):
        if self.node is not None:
            self.node.destroy_node()
            self.node = None
        if self.context is not None:
            if self.context.ok():
                self.context.shutdown()
            self.context = None
        self.number = None
        self.topic = None
        self.initialized = False

class OgnFibonacci:
    @staticmethod
    def internal_state():
        return SubscriberState()

    @staticmethod
    def compute(db):
        state = db.per_instance_state
        db.outputs.execOut = og.ExecutionAttributeState.DISABLED
        if state.initialized and state.topic != db.inputs.topic:
            state.custom_reset()
        if not state.initialized:
            state.start(db.inputs.topic)
        rclpy.spin_once(state.node, timeout_sec=0.0)
        number, state.number = state.number, None
        if number is None:
            return True
        if not 0 <= number <= 93:
            db.log_warn('Input must be 0..93 so Fibonacci fits uint64')
            return False
        previous, current = 0, 1
        for _ in range(number):
            previous, current = current, previous + current
        db.outputs.fibonacci = previous
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        return True

    @staticmethod
    def release(node):
        state = OgnFibonacciDatabase.per_instance_internal_state(node)
        if state is not None:
            state.custom_reset()
            state.reset()
