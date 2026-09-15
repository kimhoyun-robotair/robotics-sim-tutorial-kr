# 130. ROS 2 Python Custom OmniGraph Node

권장 학습 순서 **130** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t031`

**목표:** `std_msgs/msg/Int32`를 수신하는 사용자 정의 Python OmniGraph 노드를 실행하고 피보나치 값을 출력합니다. 이 폴더의 `exts/kr.ros2.fibonacci`는 완전한 로컬 확장 소스입니다. 원문의 VS Code 생성 단계 대신 설치된 `omni.graph.tools`가 `.ogn`에서 database를 생성하는 5.1 방식을 사용합니다.

## 이 실습의 의도

사용자 Python 노드에 ROS 구독 상태를 두고, 수신한 정수를 OmniGraph 출력으로 변환하는 실습입니다. `.ogn`은 포트·자료형을 정의하고 `OgnFibonacci.py`는 비차단 수신, 범위 검사, 계산, Stop 시 정리를 담당합니다. 기본 그래프는 Tick과 Fibonacci 노드만 만들기 때문에 화면에 숫자가 자동 표시되지는 않으며, 결과는 노드 Property에서 먼저 확인합니다. 각 노드가 자기 ROS context를 소유하도록 구성해 다른 ROS 노드를 종료하지 않고 자신의 구독을 다시 준비하는 과정도 살펴봅니다.

## 실행 후 확인할 것

- **확장과 그래프:** `kr.ros2.fibonacci` 활성화 후 `/FibonacciLab`에 `ROS2 Fibonacci Lesson` 노드가 생성되는지 확인합니다. `.ogn`/`.py` 파일이 있다는 사실과 Kit에서 노드가 등록되는 것은 별도 단계입니다.
- **메시지에 따른 값:** Play 후 `/number`에 Int32 10을 보내면 `outputs:fibonacci=55`, 0은 0, 20은 6765인지 확인합니다. 실제 수신 후 바뀐 출력으로 계산 경로를 확인합니다.
- **출력 실행 시점:** 새 메시지가 없으면 `execOut`이 비활성이고, 마지막 숫자가 Property에 남을 수 있습니다. 이는 매 프레임 새 계산 결과를 내보낸다는 뜻이 아닙니다. Print Text를 원하면 아래의 변환·실행 선을 추가합니다.
- **범위 거절:** -1 또는 94를 보내면 `Input must be 0..93` 경고가 나고 새 출력 실행이 발생하지 않는지 봅니다. 이전 유효 숫자가 남아 있어도 잘못된 입력을 계산한 결과로 읽지 않습니다.
- **구독 수명:** Stop→Play 뒤 10을 다시 보내 55가 나오는지 확인합니다. topic을 `/other_number`로 바꾼 실험에서는 새 토픽에 반응하고 이전 `/number`에만 보낸 값에는 새 출력 실행이 없어야 합니다.

## 실행 환경: 이 폴더만으로 시작하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Linux, ROS 2 Humble(이 문서의 명령 기준)이 필요합니다. ROS를 통해 다른 프로세스와 통신하므로 시뮬레이터와 ROS 터미널을 구분합니다. `ISAAC_SIM`은 실제 설치 디렉터리로 바꾸세요.

**터미널 A — Isaac Sim**: ROS 시스템 환경을 source하지 않은 새 Bash에서 내부 Python 3.11용 브리지를 사용합니다. `.bashrc`가 `/opt/ros`를 자동 source한다면 해당 줄을 적용하지 않은 깨끗한 셸을 사용하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

**터미널 B — ROS CLI**: 별도 Bash에서 시스템 ROS를 사용합니다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic list
```

Humble의 기본 Python 3.10 모듈을 Isaac Sim의 Python 3.11에 넣으면 ABI 오류가 납니다. Jazzy를 사용한다면 두 터미널의 배포판 이름과 내부 라이브러리 경로를 모두 `jazzy`로 바꿉니다. 같은 컴퓨터에서 먼저 실습하세요. 여러 컴퓨터는 DDS 네트워크/방화벽 설정도 일치해야 합니다. 다른 로컬 튜토리얼이나 공통 모듈은 필요하지 않습니다.


## 로컬 확장 실행

1. 위 터미널 A 환경을 설정하고 GUI 실행 대신, **이 패키지 폴더**에서 실행합니다.

   ```bash
   "$ISAAC_SIM/isaac-sim.sh" --ext-folder "$PWD/exts" --enable kr.ros2.fibonacci
   ```

2. **Window > Extensions**에서 `kr.ros2.fibonacci`가 Enabled인지 확인합니다. UI로 경로를 등록하려면 Extension Manager의 메뉴→Settings→Extension Search Paths에 이 폴더의 `exts` 절대 경로를 추가합니다.
3. 새 Stage의 **Window > Script Editor**에서 `setup_graph.py`를 열어 Run합니다. `/FibonacciLab`에 Tick과 `ROS2 Fibonacci Lesson` 노드가 생깁니다. **Window > Graph Editors > Action Graph**에서 엽니다.
4. Play 후 터미널 B에서 발행합니다.

   ```bash
   ros2 topic pub --once /number std_msgs/msg/Int32 '{data: 10}'
   ```

   Fibonacci 노드의 Outputs `fibonacci`가 **55**인지 확인합니다. 화면 표시를 원하면 **To String**과 **Print Text**를 추가해 Fibonacci 값→To String value→Print Text text, Fibonacci execOut→Print Text execIn을 연결하고 Print Text의 **To Screen**을 켭니다. 콘솔에서 보려면 To Screen을 끄고 Log Level을 Warning으로 설정합니다.
5. 0을 발행하면 0, 1이면 1, 20이면 6765입니다. 94 또는 -1을 보내면 경고가 나고 출력 실행이 발생하지 않습니다. 이는 uint64 범위 밖 계산을 미리 거절하는 로컬 개선입니다.
6. Stop→Play를 반복한 뒤 10을 다시 보내보세요. 노드가 다시 구독하고 55를 출력해야 합니다. 다른 그래프의 ROS 노드가 함께 정지하면 context 수명 관리가 잘못된 것입니다.

## 파일과 API 해설

`.ogn`은 입력 `execIn`, `topic`과 출력 `execOut`, `fibonacci`의 **계약**입니다. `.py`는 계산/통신 구현입니다. 확장 의존성에 `omni.graph.tools`를 선언하면 이 설치의 `ExtensionContentsStandalone`이 `nodes/`의 `.ogn`/`.py` 쌍을 탐색하고 Kit 캐시에 database 코드를 생성합니다. 따라서 이 패키지에는 생성된 `OgnFibonacciDatabase.py`를 고정 복사하지 않습니다.

`SubscriberState`는 graph node instance마다 별도입니다. `BaseResetNode`가 timeline Stop을 받아 `custom_reset`을 호출합니다. 로컬 구현은 **자기 Context**를 만들고 자기 것만 shutdown하여 다른 ROS 노드의 전역 context를 종료하지 않습니다. `spin_once(timeout_sec=0.0)`은 렌더 스레드를 메시지 대기로 붙잡지 않습니다. 메시지가 없으면 출력 실행을 켜지 않고, 새 값이 왔을 때만 downstream 노드를 실행합니다.

`uint64`의 최대값은 2⁶⁴−1입니다. F(93)=12200160415121876738까지 들어가지만 F(94)는 넘습니다. 범위를 먼저 검사하므로 큰 입력으로 긴 계산이 생기지 않습니다. 화면 숫자가 시간이 지나며 사라지는 것은 Print Text의 표시 시간이 끝난 것이며 반복 메시지가 자동 발행된다는 뜻은 아닙니다.

USD에는 `/FibonacciLab` 그래프가 저장되지만 메시지 큐와 context는 Python 메모리에 있습니다. Stage 파일만 다른 컴퓨터로 복사한다면 노드 구현 확장도 함께 필요합니다. 이 폴더 전체를 복사하면 구현과 가이드를 같이 가져갈 수 있습니다.

## 원문의 VS Code template 방식을 비교하기

Isaac Sim VS Code Edition이 설치된 환경에서는 **Template > Extension**에서 Ext. name=`custom.python.ros2_node`, Ready-to-use extension 및 Omnigraph node를 체크합니다. 생성된 config에 `isaacsim.ros2.bridge` dependency, 생성된 OGN에 Int32 topic 입력/uint64 출력, Python 구현에 per-node subscription과 reset을 넣는 것이 원문의 구성입니다. 이 패키지는 동일 핵심 동작을 로컬 확장으로 제공하므로 별도 공통 튜토리얼을 읽거나 VS Code 템플릿을 생성할 필요가 없습니다.

## 한 가지 변수 실험과 문제 해결

Fibonacci 노드의 topic만 `/other_number`로 바꾸고 해당 토픽에 10을 발행합니다. 이전 `/number`에는 더 이상 반응하지 않아야 합니다. custom node를 찾지 못하면 확장 활성화/콘솔의 OGN 생성 오류를 확인합니다. `rclpy` ABI 오류는 시스템 ROS의 Python 경로가 터미널 A에 섞인 경우를 먼저 확인합니다. 출력은 받지만 viewport에 안 뜨면 Print Text To Screen/실행 선을 봅니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
