# 110. 늦게 접속한 수신자에게도 메시지 전달하기

## 이번에 배우는 것

**한 번 보낸 문자열을 나중에 실행한 수신자가 받을 수 있는지 비교하며, QoS의 보존 정책을 이해합니다.**

실시간 센서 영상은 다음 프레임을 받으면 되지만, 시작할 때 한 번 보낸 설정은 늦게 접속한 노드에도 필요할 수 있습니다. ROS 2의 **QoS**는 메시지를 어떻게 전달하고 보관할지 정하는 약속입니다. 발행기와 수신기가 호환되는 약속을 사용해야 데이터가 도착합니다.

| 요소 | 이번 실습에서 하는 일 |
|---|---|
| GUI의 Generic Publisher | `/topic`에 `qos_lesson` 문자열 발행 |
| ROS2 QoS Profile | 전달 정책을 JSON 문자열로 구성 |
| `qos_profile.json` | 최근 1개를 보존하는 Custom 정책 |
| Countdown | 초기 발행 이후 실행 신호를 멈춤 |
| `listen.py` | 요청한 QoS로 실제 메시지를 기다림 |

**메시지를 한 번만 보내는 것과, 보낸 메시지를 보관하는 것은 별개의 설정입니다.** 이번에는 실행 연결과 QoS를 함께 바꿔 이 차이를 확인합니다.

## 1. 계속 발행하는 문자열부터 받기

Isaac Sim 5.1과 지원 GPU, ROS 2 Humble 또는 Jazzy의 `rclpy`, `std_msgs`가 필요합니다. 저장소 루트에서 Bash 터미널을 두 개 준비하세요. 아래는 Ubuntu 24.04의 Jazzy 예시이며 Ubuntu 22.04/Humble에서는 배포판 이름과 라이브러리·source 경로를 함께 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸입니다. Isaac Sim 설치 경로를 맞추고 내부 브리지를 사용하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

터미널 B에서는 시스템 ROS를 사용합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

1. Isaac Sim의 **File > New**로 빈 장면을 엽니다.
2. **Tools > Robotics > ROS 2 OmniGraphs > Generic Publisher**에서 **Publish String**을 선택합니다. 생성한 그래프를 우클릭해 **Open Graph**로 여세요.
3. String 상수의 값을 `qos_lesson`으로 바꿉니다. 발행기의 메시지 타입은 `std_msgs/msg/String`, `topicName`은 `/topic`으로 맞춥니다. 생성된 그래프에서 String 출력이 Publisher의 `data`, Tick이 `execIn`, Context가 `context`에 연결되어 있는지도 확인하세요.
4. **ROS2 QoS Profile** 노드를 추가하고 `qosProfile` 출력을 발행기의 같은 입력에 연결합니다. `createProfile`은 **Sensor Data**로 선택하세요.
5. Play 후 터미널 B에서 실제 정책과 문자열을 확인합니다.

```bash
ros2 topic info /topic -v
python3 src/110_ros2_ros2_qos/listen.py --volatile --best-effort --timeout 10
```

### 실행 결과 확인하기

정책 정보에서 publisher의 Reliability와 Durability를 읽으세요. Sensor Data 설정에서는 best effort와 volatile을 확인할 수 있어야 합니다. 수신기는 다음과 같이 첫 메시지의 내용을 출력하고 종료합니다.

```text
received_data= 'qos_lesson'
```

`--best-effort --volatile`은 이 실험의 발행 정책에 맞는 수신 요청입니다. 기본 `listen.py`는 reliable·transient local을 요청하므로 같은 명령으로 바꿔도 항상 연결된다고 기대하면 안 됩니다.

## 2. 초기 메시지를 보존하고 뒤늦게 구독하기

Stop한 뒤 그래프의 **Tick → Publisher.execIn 연결을 제거**합니다. QoS만 바꾸고 Tick을 남겨 두면 계속 새로운 문자열이 발행되어 과거 메시지를 받은 것인지 구분할 수 없습니다.

### 설정에서 볼 부분

1. **On Stage Event**와 **Countdown**을 추가합니다.
2. Stage Event의 `eventName`을 **Simulation Start Play**로 설정합니다.
3. `StageEvent.execOut → Countdown.execIn`, `Countdown.tick → Publisher.execIn`을 연결합니다.
4. Countdown의 `duration=3`, `period=1`을 지정합니다. 이 초기 세 번의 실행은 Generic Publisher의 준비 두 번과 메시지 발행 한 번에 쓰입니다.
5. QoS Profile은 **Custom을 먼저 선택**하고 아래 값을 넣습니다. 또는 QoS 노드 연결을 해제한 뒤 `qos_profile.json` 전체를 Publisher의 `qosProfile` 문자열에 붙여 넣습니다. 둘 중 한 방식만 사용하세요.

```json
{
  "history": "keepLast",
  "depth": 1,
  "reliability": "reliable",
  "durability": "transientLocal",
  "deadline": 0.0,
  "lifespan": 0.0,
  "liveliness": "systemDefault",
  "leaseDuration": 0.0
}
```

`keepLast`와 `depth=1`은 가장 최근의 메시지 하나를 유지한다는 뜻입니다. `transientLocal`은 늦게 접속한 수신자에게 그 보관분을 제공하는 정책입니다. JSON의 depth는 정수, 시간 관련 값은 실수로 입력합니다.

Play 후 Countdown의 초기 실행이 끝날 때까지 기다립니다. **그 뒤에도 Play와 Isaac Sim 창은 유지**하세요. 이제 터미널 B에서 다음을 실행하고, 종료 후 한 번 더 실행합니다.

```bash
python3 src/110_ros2_ros2_qos/listen.py --timeout 10
```

두 수신기 모두 `received_data= 'qos_lesson'`을 출력하는지 확인합니다. 수신기가 처음 실행되는 시점에 새 발행이 없었다면 보관된 메시지를 읽은 것입니다.

### 코드에서 볼 부분

`listen.py`는 수신기 쪽 정책을 다음처럼 선택합니다.

```python
profile = QoSProfile(depth=1,
    durability=DurabilityPolicy.VOLATILE if args.volatile else DurabilityPolicy.TRANSIENT_LOCAL,
    reliability=ReliabilityPolicy.BEST_EFFORT if args.best_effort else ReliabilityPolicy.RELIABLE)
```

받은 메시지를 `samples`에 넣고 첫 항목이 생기면 기다림을 끝냅니다. 시간 제한에는 `time.monotonic()`을 사용하므로 `/clock`을 발행하지 않아도 timeout이 동작합니다. 아무 메시지도 받지 못하면 성공 문구 대신 `TimeoutError`를 냅니다.

### 실행 결과 확인하기

| 시점과 수신 요청 | 기대하는 관찰 |
|---|---|
| 초기 발행이 끝난 뒤 기본 수신기 실행 | 보관된 문자열 1개 수신 |
| 같은 조건에서 두 번째 기본 수신기 실행 | 그 수신기도 문자열 수신 |
| Isaac Sim을 닫은 뒤 새 수신기 실행 | 기존 발행기의 보관분을 기대할 수 없음 |

`transientLocal`의 보관 장소는 살아 있는 publisher입니다. 디스크에 영구 저장하는 기능으로 이해하면 안 됩니다.

## 3. 실행 횟수와 전달 정책의 차이 정리

```text
Countdown: 언제, 몇 번 발행할지 결정
QoS: 발행한 메시지를 어떻게 전달·보관할지 결정
Subscriber QoS: 어떤 전달·보관 조건으로 받을지 요청
```

reliable은 전달 신뢰성에 관한 정책이며, 그것만으로 과거 메시지를 다시 받을 수 있게 되지는 않습니다. 늦게 접속한 수신을 비교하려면 durability도 봐야 합니다. 반대로 transient local을 설정해도 발행기의 실행 신호가 계속 들어오면 새 메시지가 계속 생깁니다.

## 4. 간단한 확인 실험

초기 발행이 끝난 동일한 장면에서 **수신기의 `--volatile` 옵션 하나만 추가**해 보세요.

```bash
python3 src/110_ros2_ros2_qos/listen.py --volatile --timeout 10
```

새 발행이 없다면 이번 수신기는 보관된 과거 데이터를 받지 못하고 timeout으로 끝날 것으로 예상합니다. 앞의 기본 수신기와 기다리는 시간·reliability는 같고 durability 요청만 달라집니다. 다시 기본 명령을 실행해 문자열을 받을 수 있는지도 확인하세요.

## 실행할 때 막히면

- **volatile 수신기도 바로 문자열을 받음**: Countdown이 아직 진행 중이거나 Tick 연결이 남아 있을 수 있습니다. `ros2 topic info /topic -v`로 다른 publisher도 확인하세요.
- **모든 수신기가 timeout**: String 데이터 연결, 초기 세 번의 실행, QoS 호환성을 확인하세요. 발행기가 살아 있는지도 확인합니다.
- **QoS UI 값이 바뀌지 않음**: 노드 바깥을 클릭한 뒤 다시 선택해 갱신된 값을 확인하세요. 저장할 정책은 Custom을 먼저 선택해 작성합니다.
- **depth가 `UNKNOWN`으로 보임**: Fast DDS의 정책 조회에서는 이렇게 표시될 수 있습니다. 이 값만으로 JSON 입력 실패라 단정하지 말고 실제 늦은 수신 결과를 확인하세요.
- **`rclpy` import 오류**: `listen.py`는 터미널 B의 시스템 `python3`용입니다. Isaac Sim의 `python.sh`와 바꿔 쓰지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS 2 Quality of Service](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)에 대응하며, 환경 설정은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고합니다.

GUI 발행기에 정책 JSON과 시간 제한 수신기를 더해 늦은 구독을 비교하도록 구성했습니다. `tutorial.json`의 검증 상태는 `not_run`입니다. 위 출력과 timeout은 실습에서 확인할 기준이며, 실제 GUI·DDS 수신을 수행한 기록은 아닙니다.
