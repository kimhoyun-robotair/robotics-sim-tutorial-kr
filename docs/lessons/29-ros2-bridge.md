# 29. Jazzy와 Isaac Sim을 연결하는 ROS 2 Bridge

[전체 목차](../../README.md) · [다음: 시간과 QoS](30-clock-qos.md)

## 이번 단계에서 할 일

Isaac Sim 안에서 발생한 일을 외부 ROS 2 프로그램이 받아 보도록 연결한다. 아직 센서나 주행 명령을 붙이지 않는다. 같은 컴퓨터의 두 터미널에서 통신 환경을 맞추고, 다음 단계의 `/clock` 실험을 실행할 준비를 한다. Ubuntu 24.04 LTS, ROS 2 Jazzy 설치와 Isaac Sim 6.0.1 실행이 먼저 끝나 있어야 한다.

ROS 노드는 메시지를 보내거나 받는 프로그램이다. 토픽은 메시지의 통로 이름이며, `geometry_msgs/msg/Twist`처럼 자료형도 정해져 있다. `/cmd_vel`이라는 이름만 맞추고 자료형을 다르게 선택하면 통신하지 못한다. Bridge는 시뮬레이터의 시간·센서·관절 데이터를 ROS 메시지로 바꾸고, 반대 방향의 제어 명령도 받아들인다.

## 1. 6.0.1의 Extension 구성을 구분한다

| Extension | 담당하는 일 | 직접 다룰 때 |
|---|---|---|
| `isaacsim.ros2.bridge` | 아래 구성 요소를 함께 활성화하는 진입점 | 첫 실습에서 켜는 항목 |
| `isaacsim.ros2.core` | ROS 라이브러리, 통신 기반, 공통 설정 | 내부 라이브러리 경로·설정을 점검할 때 |
| `isaacsim.ros2.nodes` | ROS용 OmniGraph 노드 | GUI로 publisher·subscriber를 연결할 때 |
| `isaacsim.ros2.ui` | 그래프 생성 등 사용자 인터페이스 | 메뉴의 자동 생성 기능을 쓸 때 |
| `isaacsim.ros2.examples` | ROS 예제 | 공식 샘플 장면을 열 때 |

이 구분은 다섯 종류의 ROS를 뜻하지 않는다. 통신 기능, 그래프 처리, UI, 예제의 의존성을 나눈 것이다. 화면 없이 실행하는 프로그램은 UI가 필요 없고, 그래프를 쓰지 않는 Python 프로그램은 자신이 생성한 ROS 노드를 직접 처리할 수 있다. 처음에는 umbrella Extension인 `isaacsim.ros2.bridge`를 활성화하면 된다. [6.0.1 Bridge API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.ros2.bridge/docs/index.html)

**Extension 이름과 OmniGraph 노드의 고유 ID는 서로 다르다.** 예를 들어 TF 노드의 Extension은 `isaacsim.ros2.nodes`이지만 고유 ID는 `isaacsim.ros2.bridge.ROS2PublishTransformTree`이다. 코드 문자열을 검색해 `bridge`를 모두 `nodes`로 바꾸면 잘못된 노드 이름을 만들게 된다. [노드 메타데이터](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.ros2.nodes/docs/ogn/OgnROS2PublishTransformTree.html)

## 2. 터미널 두 개를 준비한다

터미널 A는 Isaac Sim을 실행하고, 터미널 B는 `ros2` 명령과 외부 Python 프로그램을 실행한다. 둘 다 새로 열고 다음 설정을 **각각** 입력한다. `TUTORIAL_ROOT`는 실제 저장소 위치로 지정한다.

```bash
source /opt/ros/jazzy/setup.bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
cd "$TUTORIAL_ROOT"
python3 --version
python3 -c 'import rclpy; print(rclpy.__file__)'
ros2 doctor --report
```

`TUTORIAL_ROOT`에 저장소를 다른 곳에 내려받았다면 그 위치를 넣는다. Domain ID 61은 이 튜토리얼에서 정한 실습값이며 버전 번호나 필수 설정이 아니다. 두 프로세스가 같은 값을 사용해야 한다.

기대 결과는 시스템 Python 3.12와 Jazzy의 `rclpy` 경로가 출력되는 것이다. Isaac Sim 6.0.1도 Python 3.12를 사용하므로 Ubuntu 24.04/Jazzy의 기본 조합이 일치한다. Humble용 Python 3.10으로 빌드한 메시지 패키지를 가져와 사용하지 않는다. 사용자 정의 메시지 역시 Python 3.12 환경에서 빌드해야 한다. [Python 메시지 공식 설명](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_custom_message_python.html)

## 3. GUI에서 Bridge를 활성화한다

터미널 A에서 다음 명령을 실행한다.

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. GUI가 열리면 **Window > Extensions**로 이동한다.
2. 검색 칸에 `isaacsim.ros2.bridge`를 입력한다.
3. Extension이 활성화되어 있는지 확인한다. 로딩 오류가 있으면 **Window > Console**의 오류를 먼저 읽는다.
4. **Tools > Robotics > ROS 2 OmniGraphs** 메뉴가 보이는지 확인한다.
5. 아직 ROS 그래프를 만들지 않았다면 `/clock`이 없는 것이 정상이다. Extension을 켜는 것과 publisher를 생성하는 것은 별도 작업이다.

ROS 그래프는 일반적으로 **Play** 중에 동작한다. 토픽이 없다고 의심될 때는 먼저 장면을 재생했는지 확인한다. 직접 `rclpy`를 사용하는 Python 예제에서는 개발자가 메시지를 발행하는 시점을 결정하므로, 본 저장소 코드에도 `world.is_playing()` 조건을 넣었다. [ROS FAQ](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/ros2_faq.html)

## 4. Python에서는 시작 순서를 지킨다

다음은 standalone 파일 안에서 사용하는 코드 조각이다. GUI의 Script Editor에는 이미 실행 중인 앱이 있으므로 `SimulationApp`을 또 만들지 않는다.

```python
from isaacsim import SimulationApp
app = SimulationApp({"headless": False})

from isaacsim.core.utils.extensions import enable_extension
enable_extension("isaacsim.ros2.bridge")
app.update()

import rclpy
from geometry_msgs.msg import Twist
rclpy.init(args=[])
node = rclpy.create_node("my_isaac_node")
# 매 프레임 rclpy.spin_once(node, timeout_sec=0.0)으로 수신을 처리한다.
node.destroy_node()
rclpy.shutdown()
app.close()
```

`rclpy.spin(node)`를 시뮬레이션 루프 앞에서 실행하면 ROS 수신 대기에 머물러 화면 갱신으로 돌아오지 못한다. 매 프레임 `spin_once(..., timeout_sec=0.0)`로 짧게 처리하거나, Extension이라면 수명 주기와 충돌하지 않는 executor 구조를 만든다. 전체 실행 파일은 [06_ros_clock.py](../../examples/06_ros_clock.py)에 있다.

## 문제를 좁히는 순서

| 증상 | 먼저 확인할 것 |
|---|---|
| `import rclpy` 실패 | 해당 터미널에서 Jazzy를 source했는지, Python이 3.12인지 |
| GUI Bridge 로딩 실패 | 5.1 설치 폴더를 실행했는지, 서로 다른 ROS 라이브러리를 중복 설정했는지 |
| 터미널마다 다른 토픽 목록 | Domain ID·RMW 설정과 실행한 ROS 배포판 |
| 메뉴는 있으나 `/clock`이 없음 | clock 그래프 또는 Python publisher를 만들었는지, Play 중인지 |
| 설정 변경 후 이전 정보가 남음 | 같은 환경에서 `ros2 daemon stop` 후 `ros2 daemon start` |

이 단계의 기본 경로는 **시스템 Jazzy를 source하는 방식**이다. 내부 라이브러리를 쓰는 별도 환경과 섞지 않는다. 6.0.1의 내부 Jazzy 라이브러리는 `exts/isaacsim.ros2.core/jazzy/lib` 쪽이며, 5.1의 경로를 복사하면 안 된다. 내부 경로 설정이 필요한 경우에는 설치 단계와 공식 설치 안내로 돌아간다.

## 완료 기준과 과제

두 터미널에서 Python 3.12와 동일한 Domain ID를 확인하고, GUI의 Bridge가 오류 없이 켜지면 준비가 끝난다. 아직 실제 메시지 송수신을 검증한 것은 아니다. 다음 단계에서 이를 확인한다. 과제로 터미널 B의 Domain ID만 62로 바꾸었을 때 다음 단계의 `/clock`이 보이지 않는 이유를 설명한 뒤, 반드시 61로 복원한다.
