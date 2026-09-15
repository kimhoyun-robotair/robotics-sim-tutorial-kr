# 107. 시뮬레이션의 진행 속도를 실제 시계와 비교하기

## 이번에 배우는 것

**시뮬레이션 시간과 실제 경과 시간의 비율인 RTF를 ROS 2로 발행하고, 인위적인 대기 시간이 측정에 미치는 영향을 확인합니다.**

물리 계산 간격을 1/60초로 정해도 컴퓨터가 한 단계를 계산하는 데 걸리는 시간은 달라질 수 있습니다. 실제로 얼마나 빠르게 진행하는지 보려면 시뮬레이션 시간과 실제 시계를 비교해야 합니다.

| 관찰 대상 | 의미 | 표시 위치 |
|---|---|---|
| RTF | 시뮬레이션 경과 시간 / 실제 경과 시간 | `/topic`의 `Float32.data` |
| 같은 노드의 측정값 | 콘솔에서 주기적으로 읽은 RTF | `measured_rtf` |
| `--delay` | 매 단계 뒤 추가하는 실제 대기 시간, 초 | CLI 옵션 |
| 물리 간격 | 한 단계에서 진행할 시뮬레이션 시간 | `1/60`초로 고정 |

RTF=0.5이면 시뮬레이션 1초가 진행하는 데 실제로 약 2초 걸렸다는 뜻입니다. 단위 없는 비율이므로 FPS나 Hz를 붙이지 않습니다.

## 1. 측정한 RTF를 ROS 메시지로 받아 보기

기본 환경은 Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1과 지원 NVIDIA RTX GPU입니다. Ubuntu 22.04에서는 아래 `jazzy`를 `humble`로 바꿉니다.

**터미널 A**는 시스템 ROS를 source하지 않은 새 터미널입니다. 저장소 루트에서 내부 Bridge 라이브러리 경로를 한 번 설정하고 실행하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib"
"$ISAAC_SIM/python.sh" src/107_ros2_ros2_rtf/run.py
```

빈 장면에서 시간 측정과 발행 그래프를 재생합니다. **터미널 B**는 외부 ROS를 쓰는 Bash 터미널로 준비합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic type /topic
ros2 topic echo /topic
```

A와 B의 Domain ID와 RMW는 맞추되 시스템 ROS 라이브러리를 A에 추가로 source하지 않습니다. 같은 메시지를 DDS로 교환하므로 내부와 외부의 Python 버전이 같을 필요는 없습니다.

### 실행 결과 확인하기

타입은 `std_msgs/msg/Float32`이고, 메시지의 `data`가 측정한 RTF입니다. A에서는 `measured_rtf`가 60단계마다 출력됩니다.

처음 몇 프레임에는 로딩이나 초기화가 섞일 수 있습니다. 이후 일정 구간의 경향을 보세요. 값이 1보다 작거나 큰 경우 모두 의미가 있으며, **항상 정확히 1.0이어야 성공하는 실습은 아닙니다.**

콘솔과 ROS 출력은 같은 노드에서 값을 읽지만 서로 다른 시점에 보이므로 숫자가 매 줄 정확히 같을 필요는 없습니다. GUI는 창을 닫으면 끝나고 `--steps 1200`처럼 한도를 줄 수 있습니다. `--headless`만 쓰면 기본 1200단계에서 종료합니다.

## 2. RTF 측정 노드와 Generic Publisher 연결 읽기

실행 창의 Action Graph에서 `/RTFGraph`를 엽니다.

```text
On Playback Tick.tick → Publisher.execIn
ROS2 Context.context  → Publisher.context
Isaac Real Time Factor.rtf → Publisher.data
```

RTF 노드가 실제 시간 비율을 측정하고 Generic Publisher가 ROS 메시지로 보냅니다. 상수 1.0을 발행하는 그래프가 아닙니다.

### 코드에서 볼 부분

Generic Publisher는 어떤 메시지를 쓸지 먼저 지정해야 합니다.

```python
("Publisher.inputs:messagePackage", "std_msgs")
("Publisher.inputs:messageSubfolder", "msg")
("Publisher.inputs:messageName", "Float32")
```

이 설정으로 `Float32`의 필드인 `data` 입력이 만들어집니다. 코드가 메시지 타입을 설정한 뒤 `app.update()`를 거쳐 다음 연결을 하는 이유입니다.

```python
og.Controller.connect(
    og.Controller.attribute("/RTFGraph/RTF.outputs:rtf"),
    og.Controller.attribute("/RTFGraph/Publisher.inputs:data")
)
```

입력 필드가 생성되기 전에 연결하면 `inputs:data`를 찾지 못할 수 있습니다. 그래프의 노드 생성, 타입 설정, 동적 필드 생성, 연결 순서가 의미를 갖습니다.

공식 GUI 방식도 확인하려면 첫 실행을 종료하고 A에서 `"$ISAAC_SIM/isaac-sim.sh"`로 새 앱을 여세요. **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화합니다. **Tools > Robotics > ROS 2 OmniGraphs > Generic Publisher**에서 **Publish RTF as Float32**를 선택하면 `/Graph/ROS_GenericPub` 그래프가 만들어집니다. Open Graph로 위 데이터 연결을 비교한 뒤 Play합니다.

### 실행 결과 확인하기

Publisher의 `topicName=/topic`과 `messageName=Float32`를 확인하고 B에서 메시지를 받습니다. 그래프가 보이는 것은 설정이 작성되었다는 확인이고, 실제 `data` 수신은 ROS 통신까지 이어졌다는 확인입니다.

수신률을 별도로 측정하더라도 RTF와 구분하세요. 같은 B 터미널을 쓴다면 Ctrl+C로 echo를 끝내고 `ros2 topic hz /topic`을 실행합니다. 이 값이 30 Hz라는 것은 초당 메시지 도착 수이며 RTF=30이라는 뜻이 아닙니다. 이후 RTF 숫자를 비교할 때는 hz를 종료하고 echo를 다시 실행하세요.

## 3. 물리 간격과 실제 속도의 관계 정리

```text
물리 60단계 × (1/60초) = 시뮬레이션 1초
이 구간에 실제 2초가 걸렸다면 RTF = 1/2 = 0.5
이 구간에 실제 0.5초가 걸렸다면 RTF = 1/0.5 = 2.0
```

앞의 `/clock`은 시뮬레이션이 현재 몇 초에 있는지 전달합니다. RTF는 그 시간이 실제 시계에 비해 얼마나 빠르게 진행하는지 표현합니다. 시간값과 진행 속도는 함께 사용할 수 있지만 같은 측정은 아닙니다.

## 4. 간단한 확인 실험

앞서 GUI shortcut으로 만든 발행기도 종료하고, 1절의 터미널 A에서 **`--delay`만 `0.04`로** 바꿔 다시 실행합니다. A의 내부 ROS 환경 설정은 그대로 사용합니다.

```bash
"$ISAAC_SIM/python.sh" src/107_ros2_ros2_rtf/run.py --delay 0.04
```

실제 코드에서는 단계 뒤에 다음 대기를 추가합니다.

```python
if args.delay:
    time.sleep(args.delay)
```

한 번에 진행하는 물리 시간은 그대로이고 실제 경과 시간만 늘어납니다. 초기 로딩을 지난 뒤 기본 실행보다 RTF가 낮아지는지 비교하세요. 화면 설정, 단계 한도, 다른 실행 프로그램을 같게 유지하면 대기 시간의 영향을 읽기 쉽습니다.

한 프레임의 숫자 하나보다 여러 출력의 경향을 보세요. 이 실험은 CPU/GPU 성능을 따로 분리하는 벤치마크가 아니라 **실제 대기 시간이 시간 비율에 반영되는지** 확인하는 실험입니다.

## 실행할 때 막히면

- **`/topic`의 타입이 다름**: 다른 예제가 같은 토픽으로 발행하는지 확인하고 이전 발행기를 종료하세요.
- **`Publisher.inputs:data`가 없음**: 메시지 패키지·이름의 철자와 Bridge 로딩을 확인하세요. 타입 설정 뒤 앱 업데이트가 필요한 구조입니다.
- **초기 값이 0 또는 크게 튐**: 초기화 직후와 안정된 재생 구간을 구분해 관찰하세요.
- **메시지는 오는데 지연 효과가 불분명함**: 이전 실행이 종료되었는지, 같은 화면 조건에서 충분한 구간을 비교했는지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Publish Real Time Factor (RTF)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtf.html)에 대응합니다. 공식 Generic Publisher 그래프를 코드로 만들고, 콘솔 측정과 `--delay` 비교를 추가했습니다. ROS 환경은 [5.1 ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

실제 Float32 수신과 추가 대기에 따른 RTF 변화가 확인 기준입니다. `tutorial.json`의 검증 상태는 `not_run`이며 특정 RTF 수치를 측정한 실행 기록은 없습니다.
