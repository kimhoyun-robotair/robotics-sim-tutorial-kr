# 106. ROS 2 시계: 시뮬레이션 시간과 실제 시간

권장 학습 순서 **106** · ROS 2 연결과 기본 통신 · 출처 ID `t009`

예상 결과는 `/clock`에서 시간이 증가하고, 수신 모드에서는 외부에서 보낸 `1.2`초가 그래프 출력에 나타나는 것이다. 공식 GUI 실습을 같은 노드로 만드는 독립 실행 코드와 GUI 재구성 절차를 함께 제공한다.

## 이 실습의 의도

같은 `/clock` 메시지라도 시뮬레이션 시간과 운영체제 시간 중 무엇을 담는지에 따라 의미가 달라짐을 확인한다. 장면에 물체를 추가하지 않고 시계 그래프만 만들어 시간 데이터에 집중한다. 기본 `simulation` 모드는 시뮬레이션 시간을 발행하고, `system`은 시간 원천을 바꾸며, `subscribe`는 외부 시간값을 읽는 별도 실험이다.

## 실행 후 확인할 것

- 기본 실행의 `/ClockGraph`에서 `Time.simulationTime → Clock.timeStamp`를 확인하고, 외부 `ros2 topic echo /clock`에서 `rosgraph_msgs/msg/Clock`의 `sec`·`nanosec`를 연속 수신한다. 재생 중 시간이 증가하면 발행과 수신을 확인한 것이며 시작값이 Unix 시간일 필요는 없다.
- 발행은 매 playback tick에 연결되고 물리·렌더 간격은 1/60초다. `ros2 topic hz /clock`의 벽시계 수신률은 실제 실행 속도에 따라 달라지므로 고정 60 Hz를 합격 조건으로 삼지 않는다.
- RViz 노드에 `use_sim_time=true`를 적용한 뒤 ROS Time이 `/clock`을 따르고 재생 중지 시 멈추는지 본다. 값 수신과 RViz의 시계 사용은 별도 확인 항목이다.
- `--mode system`을 단독 실행하면 `/clock` 값이 운영체제 시각 기준으로 바뀌어야 한다. 다른 clock publisher를 종료한 상태에서 비교한다.
- `--mode subscribe`에서 아래의 1.2초 메시지를 보내면 콘솔 `received_clock_seconds`가 1.2로 바뀌어야 한다. 콘솔은 60스텝마다 읽으며, 이 값 수신만으로 물리 진행이 외부 시계에 동기화되는 것은 아니다.
- Stop/Play 초기화 비교는 `--reset-on-stop` 없이 실행한 경우와 플래그를 넣어 새로 실행한 경우로 나누고, 각 실행 안에서 Stop/Play를 수행한다. 기존 [실행 기록](RUNTIME_CHECK.md)은 기본 발행 모드의 제한된 수신 예시이며, 수신 모드와 GUI 실험까지 확인한 기록은 아니다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 물리와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 명시하면 해당 스텝 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1200스텝으로 종료하며, `--steps 0`과 음수는 허용하지 않습니다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. Standalone `run.py`는 이 확장을 직접 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## 실행과 관찰

1. 터미널 A에서 시뮬레이션 시간을 발행한다.

   ```bash
   "$ISAAC_SIM/python.sh" run.py
   ```

2. 터미널 B에서 `ros2 topic echo /clock --once`와 `ros2 topic hz /clock`를 실행한다. `clock.sec`와 `nanosec`가 시뮬레이션 진행에 따라 증가한다. 시작 시간이 Unix epoch와 같을 필요는 없다.
3. RViz를 `ros2 run rviz2 rviz2`로 켠다. `ros2 node list`에서 실제 RViz 노드 이름을 찾고, 그 이름이 `/rviz`라면 `ros2 param set /rviz use_sim_time true`를 실행한다. 화면 하단 ROS Time이 Isaac Sim 시각을 따른다. Play를 멈추면 시계 발행과 ROS 시간이 멈춘다.
4. 프로세스를 끝낸 뒤 `"$ISAAC_SIM/python.sh" run.py --mode system`으로 다시 실행한다. `/clock` 값이 운영체제 시간 기준으로 바뀐다. 동시에 두 Clock publisher를 실행하면 시간을 서로 덮어쓰므로 한 모드씩 실험한다.
5. 수신만 하는 모드는 다음과 같다. 발행 모드를 종료하고 실행한다.

   ```bash
   "$ISAAC_SIM/python.sh" run.py --mode subscribe
   ```

   터미널 B:

   ```bash
   ros2 topic pub --once /clock rosgraph_msgs/msg/Clock "clock: {sec: 1, nanosec: 200000000}"
   ```

   A의 `received_clock_seconds=`가 `1.2`로 바뀌는지 본다. 수신 노드는 타임스탬프 데이터를 읽는 것이며, 이 그래프만으로 Isaac Sim 물리 시간을 외부 시계에 동기화하지는 않는다.

## 같은 그래프를 GUI로 만들기

1. 새 Stage에서 **Window > Graph Editors > Action Graph > New Action Graph**를 연다.
2. **On Playback Tick**, **ROS2 Context**, **Isaac Read Simulation Time**, **ROS2 Publish Clock**을 놓는다.
3. Tick의 `tick → Publish Clock.execIn`, Context의 `context → Publish Clock.context`, 시간 노드의 `simulationTime → Publish Clock.timeStamp`를 연결한다. `topicName=/clock`이다.
4. Stop 후 `resetOnStop=True`를 설정하고 Play/Stop/Play를 반복한다. 재시작 시 0으로 돌아간다. 기본 False는 시간 역행 때문에 TF 버퍼가 무효화되는 문제를 줄인다.
5. 시스템 시간 실험에서는 시간 노드만 **Isaac Read System Time**으로 교체하고 `systemTime`을 연결한다.
6. 수신 실험에서는 별도 새 Stage에 Tick, Context, **ROS2 Subscribe Clock**을 만든다. Tick과 Context를 수신 노드에 연결하고 `topicName=/clock`으로 둔다. Property의 `outputs:timeStamp`를 본다.
7. 자동 생성도 확인한다. **Tools > Robotics > ROS 2 OmniGraphs > Clock**에서 Graph Path를 `/ClockShortcut`으로 지정하면 같은 시계 발행 구조가 만들어진다.

## 사용한 API와 개념

`SimulationApp`은 Kit와 확장을 먼저 시작한다. 이후 `World.step(render=True)`가 물리/화면 업데이트를 진행하고, `og.Controller.edit`는 노드·연결·속성값을 USD Stage에 작성한다. `ROS2Context`는 ROS 네트워크를 만들고 `ROS2PublishClock`이 `rosgraph_msgs/msg/Clock`으로 변환한다. `use_sim_time`은 **외부 ROS 노드의 파라미터**이며 Isaac Sim의 프레임 속도 설정이 아니다. 카메라/Lidar Helper로 시스템 시간 스탬프를 쓰려면 각 Helper의 `useSystemTime=True`도 필요하다.

## 한 가지 바꾸기와 문제 해결

`--reset-on-stop` 하나만 바꾸고 Stop/Play 전후 시간을 비교한다. 단순히 프로세스를 다시 시작하는 것과 동일 프로세스에서 타임라인을 다시 시작하는 것은 구분한다. ROS 시각이 0에 머물면 `/clock` 수신, Play 상태, 실제 RViz 노드 이름을 확인한다. 토픽이 전혀 보이지 않으면 두 터미널의 domain/RMW와 Bridge 활성 상태를 확인한다. Windows에서 RViz GUI가 열리지 않아도 `ros2 topic echo`로 시간 수신은 별도로 검사할 수 있다.

## 출처와 검증 범위

- [공식 5.1 ROS clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html#simulation-time-and-clock)
- [공식 5.1 publisher](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html#running-ros-2-clock-publisher)
- [공식 5.1 subscriber](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html#running-ros-2-clock-subscriber)
- [공식 5.1 메뉴 shortcut](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html#graph-shortcut)

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
