# 106. ROS 노드는 어느 시계를 따라갈까요?

## 이번에 배우는 것

**Isaac Sim의 시간을 ROS 2 `/clock`으로 보내고, 시스템 시간 발행과 외부 시계 수신을 비교합니다.**

시뮬레이션에서 1초가 흘렀다고 실제 시계도 반드시 1초 흐른 것은 아닙니다. ROS 노드가 센서나 로봇 상태의 시간을 같은 기준으로 읽으려면 어느 시계를 따를지 정해야 합니다.

| `--mode` | 그래프의 역할 | `/clock`에 담기는 값 |
|---|---|---|
| `simulation` 기본값 | 시뮬레이션 시간 발행 | 물리 재생에 따라 진행하는 시간 |
| `system` | 시스템 시간 발행 | 운영체제 시계의 시간 |
| `subscribe` | 외부 시계 수신 | 다른 ROS 발행자가 보낸 시간 |

세 모드는 각각 따로 실행합니다. 같은 `/clock`에 서로 다른 시계를 동시에 발행하면 수신자가 일관된 시간 기준을 사용하기 어렵습니다.

## 1. 시뮬레이션 시간을 발행하고 받아 보기

Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1과 지원 NVIDIA RTX GPU가 기본 환경입니다. Ubuntu 22.04에서는 아래 `jazzy`를 `humble`로 바꿉니다.

**터미널 A**는 시스템 ROS를 source하지 않은 새 터미널입니다. 저장소 루트에서 다음 설정을 한 번 적용하고 실행하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib"
"$ISAAC_SIM/python.sh" src/106_ros2_ros2_clock/run.py
```

**터미널 B**는 외부 ROS 명령을 위한 Bash 터미널입니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /clock
```

A는 Isaac Sim 내부 ROS 라이브러리, B는 시스템 ROS를 사용합니다. 두 Python 환경을 한 프로세스에 섞지 않고 DDS로 메시지를 주고받습니다. Domain ID와 RMW 설정은 양쪽을 맞춥니다.

### 코드에서 볼 부분

기본 모드의 `/ClockGraph`는 다음 연결을 만듭니다.

```text
On Playback Tick.tick ─────────→ Publish Clock.execIn
ROS2 Context.context ──────────→ Publish Clock.context
Read Simulation Time.simulationTime → Publish Clock.timeStamp
```

실행 연결은 발행 시점을 정하고, `timeStamp` 연결은 발행할 시간값을 정합니다. `run.py`는 물리·렌더 간격을 모두 1/60초로 설정합니다.

```python
values.append(("Time.inputs:resetOnStop", args.reset_on_stop))
```

`--reset-on-stop`을 생략하면 False입니다. 이 설정은 같은 앱에서 Stop 후 다시 Play할 때 시간을 처음으로 되돌릴지 정합니다.

### 실행 결과 확인하기

`rosgraph_msgs/msg/Clock`의 `clock.sec`, `clock.nanosec`가 증가하는지 보세요. 예를 들어 `sec=1`, `nanosec=200000000`은 다음과 같이 1.2초입니다.

```text
1 + 200000000 / 1000000000 = 1.2초
```

같은 터미널에서 다음 명령을 쓰려면 Ctrl+C로 `echo`를 끝내세요. `ros2 topic hz /clock`으로 수신률도 볼 수 있습니다. 다만 이는 실제 시계 기준 메시지 도착 빈도입니다. 물리 간격이 1/60초라고 외부 수신률이 항상 정확히 60 Hz여야 하는 것은 아닙니다.

GUI는 창을 닫을 때까지 실행합니다. `--steps 1200`을 추가하면 해당 반복 단계 뒤 종료하고, `--headless`의 기본 한도는 1200단계입니다. 재생/정지 비교에는 단계 제한 없는 GUI 실행을 사용하세요.

## 2. 시계 사용과 시계 수신 비교하기

외부 노드가 `/clock`을 받는 것과 그 시계를 실제로 사용하는 것은 별도 설정입니다. B와 같은 ROS 설정의 추가 터미널에서 RViz를 실행합니다.

```bash
ros2 run rviz2 rviz2
```

다른 ROS 터미널에서 `ros2 node list`로 RViz의 실제 이름을 확인하세요. 이름이 `/rviz`라면 다음과 같이 설정합니다.

```bash
ros2 param set /rviz use_sim_time true
```

이름이 다르면 실제 이름으로 바꿉니다. RViz의 ROS Time이 `/clock`을 따르고, Isaac Sim 재생을 멈추면 진행도 멈추는지 확인하세요. `use_sim_time`은 **수신 노드의 시계 선택 파라미터**이지 Isaac Sim의 계산 속도 옵션이 아닙니다.

### 코드에서 볼 부분

A의 첫 앱을 종료하고 같은 터미널 환경에서 시스템 시간 모드를 실행합니다.

```bash
"$ISAAC_SIM/python.sh" src/106_ros2_ros2_clock/run.py --mode system
```

이번에는 시간 노드가 `IsaacReadSystemTime`으로 바뀌고 `systemTime`이 발행기에 연결됩니다. 토픽 이름과 메시지 구조가 같아도 값의 기준이 바뀝니다. 운영체제 시각을 담으므로 시뮬레이션 경과 시간처럼 0 근처에서 시작할 필요가 없습니다.

다음으로 시스템 시간 앱을 종료하고 수신 모드를 실행하세요.

```bash
"$ISAAC_SIM/python.sh" src/106_ros2_ros2_clock/run.py --mode subscribe
```

B에서 한 번 발행합니다.

```bash
ros2 topic pub --once /clock rosgraph_msgs/msg/Clock 'clock: {sec: 1, nanosec: 200000000}'
```

### 실행 결과 확인하기

A의 콘솔에 `received_clock_seconds= 1.2`가 나타나는지 봅니다. 코드는 60단계마다 수신 노드 출력을 읽으므로 메시지 도착과 콘솔 표시가 같은 순간일 필요는 없습니다.

**이 수신 그래프는 외부 시간값을 읽을 뿐, Isaac Sim의 물리 시간을 그 값으로 설정하지 않습니다.** 출력이 1.2로 바뀌었다는 사실은 수신 확인이며 외부 시계에 맞춘 물리 동기화의 증거는 아닙니다.

그래프를 GUI에서 직접 만들려면 실행 중인 `run.py` 창을 종료하고 A에서 `"$ISAAC_SIM/isaac-sim.sh"`로 새 앱을 여세요. **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한 뒤 새 장면의 Action Graph에 Tick, Context, Read Simulation Time, Publish Clock을 추가하고 1절의 연결을 만듭니다. **Tools > Robotics > ROS 2 OmniGraphs > Clock**의 shortcut으로도 발행 구조를 만들 수 있습니다. 수신 실험은 시간 노드와 발행기를 Subscribe Clock으로 바꾼 별도 장면에서 진행합니다.

## 3. 시간값과 시간 사용의 차이 정리

```text
Isaac Sim 시간 읽기 → Clock 메시지 발행 → 외부 노드 수신
                                          ↓ use_sim_time=true
                                      그 노드의 ROS 시간으로 사용

외부 Clock 발행 → Isaac Sim Subscribe Clock 출력
                 (이 연결만으로 물리 시간을 바꾸지는 않음)
```

메시지의 초·나노초는 시각 데이터입니다. 실제 계산 속도나 수신 빈도를 알고 싶다면 각각 다른 측정이 필요합니다. 다음 RTF 실습은 시뮬레이션 시간과 실제 경과 시간의 비율을 다룹니다.

## 4. 간단한 확인 실험

진행 중인 다른 모드의 앱을 종료한 뒤 기본 발행 모드에서 **`--reset-on-stop` 유무만** 바꾸어 비교하세요. A의 환경 설정은 그대로 사용합니다.

```bash
"$ISAAC_SIM/python.sh" src/106_ros2_ros2_clock/run.py --reset-on-stop
```

각 실행 안에서 시간이 충분히 증가한 뒤 Stop → Play를 수행합니다. 기본 False에서는 시간값이 이전 진행값에서 이어지고, True에서는 다시 0 부근에서 시작하는지 봅니다. Pause와 Stop은 구분합니다.

B에서 앞의 수신 출력을 종료했다면 `ros2 topic echo /clock`을 다시 실행하세요.

프로세스를 종료했다가 새로 시작한 결과만 비교하면 같은 앱의 Stop 처리 차이를 확인할 수 없습니다. B의 `/clock` 출력에서 정지 전 마지막 값과 재생 후 첫 값의 관계를 보세요.

## 실행할 때 막히면

- **`/clock`이 안 보임**: Bridge 로딩과 A/B의 Domain ID, RMW를 확인하세요. 발행 앱이 재생 중이어야 합니다.
- **RViz ROS Time이 0에서 멈춤**: 실제 RViz 노드에 `use_sim_time=true`를 적용했는지, `/clock`을 수신하는지 확인하세요.
- **시간이 번갈아 크게 뛰거나 돌아감**: 다른 `/clock` 발행기가 동시에 있는지 `ros2 topic info /clock -v`로 확인하세요.
- **수신 모드의 콘솔이 바로 안 바뀜**: Play 상태와 60단계 출력 간격을 확인하세요. 이 모드에는 자체 clock 발행기가 없습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)에 대응합니다. 공식 그래프를 세 CLI 모드로 구성했으며, 내부·외부 ROS 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 이전 기본 발행 코드에서 Jazzy 수신 노드로 메시지 100개와 시간 증가를 확인한 기록입니다. 현재 파일의 결과는 위 기준으로 다시 확인하세요. `tutorial.json`의 부분 실행 검증은 시스템 시간·수신 모드·RViz·Stop/Play 비교까지 포함하지 않습니다.
