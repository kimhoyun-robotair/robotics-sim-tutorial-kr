# 130. ROS 정수를 받아 계산하는 Python OmniGraph 노드 만들기

## 이번에 배우는 것

**사용자 Python 노드를 확장으로 등록하고, ROS에서 받은 정수의 피보나치 수를 그래프 출력으로 내보냅니다.**

이번에는 기존 노드를 연결하는 데서 한 걸음 더 나아가 노드의 포트와 계산을 직접 정의합니다. 피보나치 수는 `F(0)=0`, `F(1)=1`, 이후에는 앞의 두 수를 더한 값입니다. 계산은 간단하게 두고, 메시지를 기다리는 방식과 구독 상태의 수명을 살펴봅니다.

| 파일 | 담당하는 부분 | 예 |
|---|---|---|
| `config/extension.toml` | 확장과 의존성 등록 | ROS Bridge, `omni.graph.tools` |
| `OgnFibonacci.ogn` | 입력·출력 포트 계약 | topic, execIn, uint64 출력 |
| `OgnFibonacci.py` | 구독·계산·정리 | 10을 받으면 55 출력 |
| `setup_graph.py` | 실습 그래프 생성 | Tick → Fibonacci |

그래프는 매 Tick에 호출되지만 새 결과는 **새 메시지를 받았을 때만** 내보냅니다. 이 둘의 주기가 같을 필요는 없습니다.

## 1. 로컬 확장을 켜고 정수 보내기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0**과 지원 GPU가 필요합니다. 시스템 ROS를 source하지 않은 Bash에서 저장소 루트로 이동한 뒤 실행하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --ext-folder "$PWD/src/130_ros2_ros2_custom_omnigraph_node_python/exts" --enable kr.ros2.fibonacci
```

1. **Window > Extensions**에서 `kr.ros2.fibonacci`가 Enabled인지 확인합니다.
2. **File > New**로 빈 Stage를 열고 **Window > Script Editor**에서 이 폴더의 `setup_graph.py` 전체를 실행합니다.
3. **Window > Graph Editors > Action Graph**에서 `/FibonacciLab`을 엽니다. Tick과 **ROS2 Fibonacci Lesson** 노드가 보이면 Play하세요.
4. 별도 시스템 ROS Bash에서 아래 메시지를 보냅니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic pub --once /number std_msgs/msg/Int32 '{data: 10}'
```

### 실행 결과 확인하기

Fibonacci 노드의 Property에서 `outputs:fibonacci`가 **55**인지 확인하세요. 기본 그래프는 Viewport 숫자 표시나 CSV 기록을 만들지 않습니다. 값이 화면 위에 자동으로 나타나지 않아도 Property에서 확인할 수 있습니다.

다음 입력도 하나씩 보내 보세요.

| 입력 data | 기대 출력 |
|---|---|
| 0 | 0 |
| 1 | 1 |
| 20 | 6765 |

`--once` 명령은 발행 후 끝나지만 그래프와 구독은 Play 중 계속 유지됩니다. 다음 입력을 보내기 전에 원하는 출력이 갱신됐는지 확인하세요.

## 2. 메시지 처리와 노드 상태 살펴보기

### 코드에서 볼 부분

`.ogn`은 입력 `execIn`, `topic`과 출력 `execOut`, `fibonacci`를 정의합니다. `fibonacci`는 `uint64`이므로 음수 없이 64비트에 들어가는 값이어야 합니다. 설치된 `omni.graph.tools`는 확장 안의 `.ogn`과 Python 구현을 찾아 데이터베이스 코드를 생성합니다. 생성된 `OgnFibonacciDatabase.py`를 이 폴더에서 직접 작성하지 않는 이유입니다.

계산 진입부를 살펴보세요.

```python
db.outputs.execOut = og.ExecutionAttributeState.DISABLED
rclpy.spin_once(state.node, timeout_sec=0.0)
number, state.number = state.number, None
if number is None:
    return True
```

실제 코드에서는 이 앞뒤로 topic 변경과 구독 초기화도 처리합니다. 여기서 중요한 점은 **메시지가 없으면 바로 반환**한다는 것입니다. 기다리는 동안 렌더링을 멈추지 않고 다음 Tick에서 다시 확인합니다. 처리한 값은 `None`으로 비워 같은 입력을 매 Tick 새 메시지처럼 계산하지 않습니다.

계산은 앞의 두 값을 갱신하는 반복문입니다.

```python
previous, current = 0, 1
for _ in range(number):
    previous, current = current, previous + current
db.outputs.fibonacci = previous
db.outputs.execOut = og.ExecutionAttributeState.ENABLED
```

입력 범위는 `0..93`입니다. `F(93)=12200160415121876738`은 uint64 안에 들어가지만 F(94)는 최대값 `2^64−1`을 넘습니다. 구현은 계산 전에 범위를 검사합니다.

### 구독은 누가 정리하나요?

`SubscriberState`는 노드 인스턴스마다 ROS Context와 구독 노드를 소유합니다. Stop, topic 변경, 노드 해제 시 자기 노드와 Context를 정리합니다. 다른 ROS 노드와 공유하는 전역 Context를 종료하지 않도록 한 구조입니다.

Stop → Play한 뒤 10을 다시 보내 55가 나오는지 확인하세요. 이 확인은 계산식뿐 아니라 정리된 구독이 다시 준비되는 과정도 살펴봅니다.

### 실행 결과 확인하기

-1 또는 94를 보내면 `Input must be 0..93` 경고가 나오고 새 출력 실행은 발생하지 않아야 합니다. 이전 유효 숫자는 Property에 남을 수 있습니다. **숫자가 남아 있다는 사실을 잘못된 입력의 계산 결과로 읽지 마세요.**

화면 표시가 필요하면 To String과 Print Text를 추가하여 `fibonacci → To String → Print Text.text`, `execOut → Print Text.execIn`을 연결하고 To Screen을 켭니다. 숫자 데이터 선과 새 결과 도착을 알리는 실행 선을 모두 연결해야 합니다.


### VS Code 생성기와 로컬 확장 구조 비교하기

원문의 생성 과정을 함께 익히려면 VS Code의 **Isaac Sim VS Code Edition**을 준비하고 별도 출력 폴더에 확장을 생성하세요.

1. **Template > Extension**에서 이름을 `custom.python.ros2_node`로 정합니다.
2. Ready-to-use와 Python OmniGraph 구성 요소를 선택하고 Create합니다.
3. 생성물의 `extension.toml`에서 Python 모듈 이름을 확인하고 `isaacsim.ros2.bridge`와 필요한 노드 의존성을 추가합니다.
4. 생성된 `.ogn`의 입력·출력과 Python `compute`를 로컬 `OgnFibonacci.ogn/.py`와 비교합니다. topic, uint64 결과, 실행 출력과 노드별 구독 상태가 어느 파일에 정의되는지 찾아보세요.
5. 실제 Fibonacci 구현을 옮긴다면 **생성된 모듈·Database 이름에 맞춰 import와 클래스 이름도 함께 변경**해야 합니다. 로컬의 `kr_ros2_fibonacci.ogn.OgnFibonacciDatabase`를 새 확장에 그대로 적지 않습니다.
6. 새 확장의 부모 폴더를 Isaac Sim의 Extension Search Paths에 등록하여 활성화하고, 원래 로컬 그래프와 별도로 같은 10 → 55 입력·출력을 확인합니다.

생성기는 파일 구조를 준비합니다. 구독을 매번 새로 만드는 대신 인스턴스 상태에 보관하고 Stop 때 정리하는 동작은 구현 코드에서 연결해야 합니다. 기본 실습은 이미 그 구조를 가진 로컬 확장을 사용하므로 생성기를 별도로 실행하지 않아도 진행할 수 있습니다.

## 3. Tick과 메시지 도착의 차이 정리

```text
매 Tick → 구독 준비/비차단 수신 확인
           ├─ 메시지 없음 → 마지막 출력값 유지, execOut 비활성
           ├─ 범위 밖 입력 → 경고, 새 결과 없음
           └─ 유효 입력 → 피보나치 계산 → 값 저장 + execOut 활성
```

**데이터 포트는 마지막 값을 보관하고 실행 포트는 새 결과를 사용할 시점을 알립니다.** 뒤에 연결한 노드가 값만 읽는지, 새 실행 신호에 반응하는지에 따라 보이는 동작이 달라집니다.

USD에 저장되는 것은 그래프와 입력 설정입니다. ROS Context와 수신 상태는 Python 메모리에 있으므로 Stage만 다른 컴퓨터로 복사할 때도 이 노드 구현 확장이 필요합니다.

## 4. 간단한 확인 실험

Fibonacci 노드의 **topic만 `/other_number`**로 바꾸고 Play 중 다음을 보냅니다.

```bash
ros2 topic pub --once /other_number std_msgs/msg/Int32 '{data: 10}'
```

출력은 55가 되어야 합니다. 이전 토픽도 비교하려면 다음처럼 구독자 대기를 끄고 보냅니다.

```bash
ros2 topic pub --once --wait-matching-subscriptions 0 /number std_msgs/msg/Int32 '{data: 20}'
```

출력이 6765로 바뀌지 않는지 확인하세요. topic 변경을 감지하면 이전 구독을 정리하기 때문입니다. `--once`는 기본적으로 구독자 하나를 기다리므로, 구독을 없앤 이전 토픽의 비교에는 대기 수 0을 명시합니다. 이 옵션은 [ROS 2 Jazzy topic publisher](https://github.com/ros2/ros2cli/blob/jazzy/ros2topic/ros2topic/verb/pub.py)에 정의되어 있습니다.

## 실행할 때 막히면

- **노드 검색이 안 됨**: `--ext-folder`가 `exts` 디렉터리를 가리키는지, 확장이 Enabled인지 확인하세요.
- **생성된 Database 모듈을 찾지 못함**: Console에서 OGN 생성 오류와 `omni.graph.tools` 의존성 로드를 확인하세요. 파일 존재만으로 등록 완료를 판단하지 않습니다.
- **`rclpy` 심볼 오류**: 시스템 Jazzy Python 3.12 환경이 시뮬레이터 터미널에 섞이지 않았는지 확인하세요.
- **이전 숫자만 남음**: Play, 현재 topic 입력, 새 메시지 수신과 범위 경고를 확인하세요.
- **Property에는 값이 있는데 화면에는 없음**: 기본 그래프에는 Print Text가 없습니다. 표시를 추가했다면 To Screen과 execOut 연결을 확인하세요.

Ubuntu 22.04/Humble은 내부 라이브러리와 외부 ROS 경로를 모두 `humble`로 바꿉니다. 실습을 마치면 Stop 후 앱을 닫으세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Python Custom OmniGraph Node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python.html)에 대응합니다. [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 함께 참고하세요.

원문의 템플릿 생성 과정을 로컬 확장 소스로 제공하고, 입력 범위 검사와 노드별 Context 정리를 구현한 실습입니다. 파일·계산·포트 계약은 대조했으며 확장 로드, Stop/Play, DDS 수신은 이번 개정에서 실행하지 않았습니다. `tutorial.json`은 `verification: not_run`입니다.
