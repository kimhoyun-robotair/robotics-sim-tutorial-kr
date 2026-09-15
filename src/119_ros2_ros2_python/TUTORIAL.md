# 119. ROS 2 Bridge in Standalone Workflow

권장 학습 순서 **119** · ROS 2 연결과 기본 통신 · 출처 ID `t022`

**목표:** Python이 물리 스텝을 소유하는 standalone 실행에서 `/sim_time`과 `/manual_time`의 발행 시점을 비교합니다. 로컬 `run.py`는 공식 수동 clock 예제에 실행 기록과 선택적인 종료 스텝을 추가합니다.

## 이 실습의 의도

Python의 스텝 루프가 자동 playback tick과 수동 impulse 발행을 어떻게 구분하는지 두 Clock 토픽으로 비교한다. 같은 시뮬레이션 시간을 서로 다른 실행 신호에 연결해 시간값의 원천과 발행 시점이 별개임을 확인한다. 기본 `run.py`는 시계 그래프와 trigger 기록을 만들고, `camera_manual.py`는 센서 Gate를 선택한 프레임에 여는 별도 확장 실습이다.

## 실행 후 확인할 것

- `/ClockLab`에서 Auto는 Tick, Manual은 Impulse에 연결되고 둘 다 Time의 simulationTime을 읽는지 확인한다. 외부 `/sim_time`, `/manual_time`의 타입은 모두 `rosgraph_msgs/msg/Clock`이며 기본 실행은 `/clock`이라는 이름으로 발행하지 않는다.
- 기본 `--domain-id 1`은 환경변수보다 우선하므로 수신 터미널도 Domain ID=1로 맞춘다. `/manual_time`은 `--every 10`에서 수신 누락 없이 연속 표본을 받았다면 약 10/60초씩 증가하고, `/sim_time`은 playback tick마다 발행된다.
- `--every 30`으로 바꾸어 새 출력 파일에 실행하면 수동 토픽의 정상 연속 간격은 약 0.5초가 되어야 한다. 이는 시뮬레이션 시간 간격이며 `ros2 topic hz`의 벽시계 값이 반드시 2 Hz여야 한다는 뜻은 아니다.
- 정상 종료 뒤 `output/clock_schedule.json`의 `manual_trigger_schedule`에서 기본 frame이 0, 10, 20… 순서인지 확인한다. `simulation_time_before_step`은 impulse 설정 직전의 시간이며, 기록 자체는 발행 완료나 DDS 수신 증거가 아니므로 ROS echo를 함께 확인한다.
- 기존 출력 파일을 다시 지정하면 실행 전에 오류가 나는 것은 기록 덮어쓰기를 막는 동작이다. GUI 무제한 실행의 `requested_steps`는 null이고, 실행 도중 파일은 아직 완성된 JSON이 아닐 수 있으므로 정상 종료 후 읽는다.
- 별도 `camera_manual.py`에서는 `/rgb`·`/depth`의 `sensor_msgs/msg/Image`와 `/camera_info`의 `CameraInfo`, frame=`sim_camera`를 확인한다. 초기 준비 이후 RGB는 Play 5프레임, depth는 60프레임마다 Gate를 열고 정보는 매 프레임 보낸다. 창고 asset이 필요한 이 경로의 `--steps`는 Pause/Stop 중 앱 업데이트도 포함하므로 기본 시계 실험의 관찰 범위와 구별한다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 물리와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 명시하면 해당 스텝 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1200스텝으로 종료하며, `--steps 0`과 음수는 허용하지 않습니다.

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


## 실행과 관찰

1. 위의 터미널 A 환경 변수만 설정하고 GUI 실행 명령 대신 아래 명령을 실행합니다. 현재 작업 디렉터리는 이 패키지 폴더입니다.

   ```bash
   python3 run.py --help
   "$ISAAC_SIM/python.sh" run.py --every 10 --domain-id 1
   ```

2. 터미널 B에서 `export ROS_DOMAIN_ID=1`로 맞춥니다. GUI가 로딩되는 동안 구독을 준비합니다.

   ```bash
   ros2 topic echo /manual_time
   ```

3. 또 다른 ROS 터미널에서 같은 Domain ID로 `ros2 topic echo /sim_time`을 실행합니다. 수동 토픽의 연속 타임스탬프 차이는 정상 동작 시 약 `10/60`초입니다. `ros2 topic hz`는 벽시계 수신률이므로 반드시 6 Hz라고 단정하지 마세요.
4. `output/clock_schedule.json`은 실제로 impulse를 설정한 프레임을 메모리에 모으지 않고 파일에 순차 기록합니다. 창을 정상 종료하면 JSON 기록이 완성됩니다. 무제한 실행의 `requested_steps`는 `null`이며 기록 파일 크기는 관찰 시간에 따라 증가합니다. 네트워크 수신 확인은 위 ROS CLI가 담당합니다. 기존 파일이 있으면 `--output output/second.json`을 지정합니다.

## 코드와 개념

`SimulationApp`이 Kit의 모듈/플러그인 로더를 시작한 뒤 `omni.graph.core`를 import합니다. `SimulationContext.step(render=True)`는 물리 계산과 앱 업데이트를 진행하고, `OnPlaybackTick`은 매 렌더 프레임 실행 신호를 냅니다. `OnImpulseEvent.state:enableImpulse=True`는 원하는 프레임에만 한 번 실행하도록 예약합니다. `IsaacReadSimulationTime`은 실행 신호가 아니라 두 publisher가 읽을 시간을 제공합니다. `ROS2Context`의 `useDomainIDEnvVar=False`는 `--domain-id`를 환경 변수보다 우선합니다.

USD의 `/ClockLab`은 파일 경로가 아니라 Stage 안의 그래프 prim 경로입니다. 발행 토픽 이름 `/manual_time`과 별개입니다. 이 예제는 실시간 속도를 보장하지 않습니다. 외부 제어기는 시뮬레이션 시간 기준으로 계산해야 합니다.

## 원문의 다른 standalone 실습도 직접 실행하기

아래 표의 수동 카메라는 이 폴더의 `camera_manual.py`로 실행합니다. NVIDIA 5.1.0 예제의 수동 발행 동작을 보존하고 창 유지와 종료 옵션을 추가한 독립 실행 파일입니다. 나머지 파일은 **Isaac Sim 5.1.0 설치에 포함된 공식 예제**이며, 해당 소스를 열어 지정한 줄의 값을 바꿔 관찰합니다. 필요하면 현재 패키지 폴더에 복사해 수정하여 설치 파일을 보존합니다.

| 원문 실습 | 실행 파일: 별도 표시가 없으면 `$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/` 아래 | 실습 변경/관찰 |
|---|---|---|
| 주기 카메라 | `camera_periodic.py` | Simulation Gate의 RGB step=5, depth step=60을 찾아 RGB만 10으로 바꾸고 RGB/Depth 토픽 수신률 비교 |
| 수동 카메라 | **이 폴더의** `camera_manual.py` | RGB는 5프레임, depth는 60프레임마다 gate를 열고 CameraInfo는 매 프레임 발행; depth 주기만 바꾸어 갱신 관찰 |
| Carter stereo | `carter_stereo.py` | Play 중 left/right RGB, odometry, TF, PointCloud2 토픽을 `ros2 topic list -t`로 확인; 두 영상이 같은 센서가 아님을 비교 |
| 복수 로봇 | `carter_multiple_robot_navigation.py --environment hospital` 또는 `--environment office` | 환경만 바꾸고 로봇별 토픽 namespace와 TF 확인; Nav2 제어는 외부 workspace 필요 |
| MoveIt | `moveit.py` | `joint_states`, joint command, `/clock`, TF 그래프 연결과 robot prim 경로 확인; 계획기는 외부 MoveIt workspace 필요 |
| 수신 이벤트 | `subscriber.py` | `ros2 topic pub -r 1 /move_cube std_msgs/msg/Empty '{}'`를 실행하고 매 수신에 cube 위치가 바뀌는지 확인 |

수동 카메라는 위 터미널 A의 환경을 설정한 뒤 이 패키지에서 실행합니다.

```bash
"$ISAAC_SIM/python.sh" camera_manual.py
# 유한 실행 점검: 120번의 main-loop update 뒤 종료
"$ISAAC_SIM/python.sh" camera_manual.py --headless --steps 120
```

카메라 예제는 Simple Warehouse asset에 접근해야 합니다. GUI에서 Pause 또는 Stop을 눌러도 창은 계속 유지되고 Play로 다시 발행을 진행할 수 있습니다. `--steps`는 Play 중 시뮬레이션 스텝과 Pause/Stop 중 앱 업데이트를 모두 셉니다. 생략하면 GUI는 창을 닫을 때까지 유지되고, headless는 1200회로 종료합니다. 원본의 `IsaacSimulationGate.inputs:step`은 센서 발행 여부를 제어하는 그래프 속성이며 GUI 종료 옵션 `--steps`와 별개입니다. 카메라 회전과 발행 주기는 Play 중 진행한 프레임을 기준으로 합니다. [출처와 변경 고지](NOTICE.md), [라이선스](LICENSE-NVIDIA-EXAMPLES)를 함께 제공합니다.

예를 들어 `"$ISAAC_SIM/python.sh" "$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/subscriber.py"`로 실행하며 종료는 Ctrl-C입니다. 카메라 영상은 `ros2 run rqt_image_view rqt_image_view`로 `/rgb`, `/depth`를 선택합니다. RTX/Franka/Carter 예제는 설치의 5.1 asset 서버 접근 또는 로컬 asset pack이 추가로 필요합니다. RViz의 검은 depth 영상만으로 발행 실패라 판단하지 말고 Image 도구에서 확인합니다.

## 한 가지 변수 실험과 문제 해결

`--every 10`을 `--every 30`으로 바꾸고 새 출력 파일을 지정하세요. manual timestamp 간격만 0.5초로 증가하고 자동 발행은 유지되어야 합니다. 토픽이 안 보이면 Domain ID부터 확인하세요. 그래프 노드 종류를 찾지 못하면 Extension Manager에서 `isaacsim.ros2.bridge`가 활성화됐는지 확인합니다. GUI 실행에서는 `--steps`를 생략하면 창을 닫을 때까지 관찰할 수 있습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
