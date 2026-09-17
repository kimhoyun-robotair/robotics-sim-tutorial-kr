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
# SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
# headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
app = SimulationApp({'headless': args.headless})
try:
    from isaacsim.core.utils.extensions import enable_extension
    # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
    enable_extension('isaacsim.ros2.bridge')
    # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
    # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
    app.update()
    # rclpy는 ROS 2의 Python 클라이언트 라이브러리이다. 여기서는 Isaac Sim 프로세스에서 ROS 노드를 만든다.
    import rclpy
    # SampleMsg는 별도 ROS 작업 공간에서 빌드한 사용자 메시지 타입이며 publisher의 메시지 형식으로 사용한다.
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
            # 대기 시간을 0으로 두어 ROS 콜백을 처리한 뒤 Kit 프레임 갱신으로 돌아간다.
            rclpy.spin_once(node, timeout_sec=0.0)
            app.update()
            frame += 1
    finally:
        node.destroy_node()
        rclpy.shutdown()
finally:
    # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
    app.close()
