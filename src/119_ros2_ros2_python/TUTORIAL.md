# 119. Python에서 ROS 발행 시점을 직접 정하기

## 이번에 배우는 것

**같은 시뮬레이션 시간을 자동 tick과 수동 impulse로 각각 발행하고, 실행 신호와 메시지 값의 차이를 비교합니다.**

05번에서는 내 반복문이 `world.step()`으로 물리를 진행했습니다. 이번에도 Python이 진행 단계를 소유하며, 특정 단계에서만 ROS 발행을 요청합니다. 두 시계 토픽은 시간의 원천이 같고 발행 시점만 다릅니다.

| 구성 | 자동 발행 | 수동 발행 |
|---|---|---|
| 토픽 | `/sim_time` | `/manual_time` |
| 실행 신호 | On Playback Tick | On Impulse Event |
| 시간값 | Isaac Read Simulation Time | 같은 노드의 같은 시간 |
| 기본 간격 | playback tick마다 | 10스텝마다 |
| 로컬 기록 | 별도 수신 기록 없음 | impulse 요청 프레임을 JSON에 기록 |

`camera_manual.py`는 이 생각을 영상 발행 Gate에 적용하는 두 번째 실행 파일입니다.

## 1. 자동 시계와 수동 시계 함께 실행하기

Isaac Sim 5.1, 지원 GPU, Ubuntu 24.04의 ROS 2 Jazzy가 필요합니다. 아래는 저장소 루트의 Bash 명령입니다. Ubuntu 22.04/Humble에서는 `jazzy` 값과 라이브러리·source 경로를 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 내부 브리지를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=1
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/119_ros2_ros2_python/run.py --every 10 --domain-id 1
```

설치 위치가 다르면 `ISAAC_SIM`을 수정하세요. 기본 GUI는 창을 닫을 때까지 실행합니다. `--steps 1200`을 추가하면 1200스텝 후 종료하며 `--headless`만 주어도 기본 1200스텝을 사용합니다.

터미널 B에서는 시스템 ROS를 준비합니다. 이 실습의 기본 Domain ID는 **1**입니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=1
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /sim_time
```

같은 환경의 다른 ROS 터미널에서 `ros2 topic echo /manual_time`을 실행해 두 출력을 함께 봅니다. 관찰은 Ctrl+C로 종료하세요. 두 토픽 타입은 `rosgraph_msgs/msg/Clock`이며 `/clock`이라는 이름으로 발행하는 실습은 아닙니다.

### 코드에서 볼 부분

```python
if frame % args.every == 0:
    og.Controller.set(og.Controller.attribute('/ClockLab/Impulse.state:enableImpulse'), True)
```

프레임 0, 10, 20…에서 수동 실행을 요청한 뒤 `sim.step(render=True)`로 시뮬레이션을 진행합니다. impulse 설정은 실행 예약이고, publisher가 읽을 시간은 별도로 연결한 Simulation Time입니다.

```text
Tick ─────────→ Auto.execIn      Time.simulationTime → Auto.timeStamp
Impulse ──────→ Manual.execIn    Time.simulationTime → Manual.timeStamp
```

Context는 `useDomainIDEnvVar=False`이며 `--domain-id` 값을 직접 사용합니다. 따라서 터미널 A의 환경변수만 0으로 바꾸어도 실행 옵션이 1이면 발행기는 Domain 1에 있습니다. 수신 터미널을 옵션과 맞추세요.

### 실행 결과 확인하기

수신 누락 없이 연속 메시지를 비교하면 자동 시계는 약 1/60초, 수동 시계는 약 `10/60=0.1667초` 간격으로 증가할 것으로 예상합니다. Clock의 시간은 `sec + nanosec/10^9`로 읽을 수 있습니다. 실제 벽시계 수신 빈도는 GPU·앱 처리 속도에 따라 달라집니다.

앱을 정상 종료하면 이 튜토리얼 폴더의 `output/clock_schedule.json`이 완성됩니다.

| JSON 항목 | 의미 |
|---|---|
| `domain_id` | 실제 Context에 지정한 번호 |
| `requested_steps` | 실행 한도, 무제한 GUI는 `null` |
| `manual_trigger_schedule[].frame` | impulse를 요청한 0부터 시작하는 프레임 |
| `simulation_time_before_step` | 요청을 기록한 시점의 스텝 진행 전 시간 |

이 파일은 **실제 impulse 요청 기록**이며 DDS 수신 기록이 아닙니다. 메시지의 정확한 timestamp와 동일한 값이라고 단정하지 말고, 요청 프레임 간격과 외부 수신 간격을 각각 확인하세요. 기록은 실행 중 순차 작성되어 정상 종료 전에는 완성된 JSON이 아닐 수 있습니다. 기존 파일은 덮어쓰지 않으므로 재실행에는 새 `--output` 경로를 지정합니다.

## 2. 같은 방식으로 카메라 발행 Gate 제어하기

앞의 시계 앱을 종료한 뒤 터미널 A에서 실행합니다.

```bash
"$ISAAC_SIM/python.sh" src/119_ros2_ros2_python/camera_manual.py
```

이 예제는 `Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd` 자산을 사용하므로 5.1 asset 서버 또는 로컬 asset pack 접근이 필요합니다. 터미널 A의 `ROS_DOMAIN_ID=1`을 유지하고 터미널 B도 1로 둡니다. 카메라 파일에는 `--domain-id` 옵션이 없으며 기본 ROS Context가 환경변수를 사용합니다.

카메라는 `/Camera`, 영상 frame은 `sim_camera`입니다. ROS 터미널에서 `ros2 run rqt_image_view rqt_image_view`를 실행하고 `/rgb`, `/depth`를 차례로 선택하세요. `/camera_info`도 발행합니다.

### 코드에서 볼 부분

카메라 그래프는 먼저 한 번 평가됩니다.

```python
og.Controller.evaluate_sync(ros_camera_graph)
```

이 평가로 Viewport·Render Product와 센서 후처리 파이프라인을 준비합니다. 그 뒤 코드가 RGB·Depth·CameraInfo의 Gate 경로를 찾아 켜고 끕니다. Gate의 `step=0`은 실행을 막고 `step=1`은 통과시킵니다.

```python
if frame % 5 == 0:
    og.Controller.attribute(rgb_camera_gate_path + ".inputs:step").set(1)

if frame % 60 == 0:
    og.Controller.attribute(depth_camera_gate_path + ".inputs:step").set(1)
```

매 반복에서 세 Gate를 먼저 0으로 두고 선택한 것만 1로 엽니다. CameraInfo는 매 프레임 1로 둡니다. 그래서 RGB는 5프레임 주기, depth는 60프레임 주기로 발행 기회가 생깁니다.

이 파일은 `simulation_context.step(render=True)` **뒤에서** 다음 Gate 값을 설정합니다. 따라서 분기문의 `frame=0`을 첫 수신 이미지의 정확한 frame 번호로 해석하지 마세요. 초기 파이프라인 준비 이후 지속되는 주기를 비교하는 것이 목적입니다. 카메라 회전식은 `frame/4.0`이므로 Play 프레임당 0.25°입니다.

### 실행 결과 확인하기

RGB에서 카메라 시점이 자주 갱신되고 depth는 더 드문 간격으로 바뀌는지 확인하세요. 두 토픽의 수신 빈도와 CameraInfo의 frame을 함께 읽습니다. 단순히 topic 목록에 이름이 있다는 사실보다 실제 영상의 갱신을 관찰해야 합니다.

GUI에서 Pause·Stop해도 카메라 앱 창은 남습니다. 코드는 이때 `app.update()`로 화면을 갱신하고 Play를 기다립니다. `--steps N`은 **물리 스텝과 Pause/Stop 중 앱 업데이트를 모두 세는 한도**입니다. 한도를 생략한 GUI는 창을 닫을 때까지, headless는 1200회 업데이트 후 종료합니다. 이 한도는 Gate의 `inputs:step`과 다른 값입니다.

## 3. 진행 단계와 발행 요청의 관계 정리

```text
시계 run.py
impulse 설정 → sim.step() → 선택한 Clock 발행 → 다음 반복

camera_manual.py
sim.step() → 다음 센서 발행을 위한 Gate 값 설정 → 다음 반복
```

두 파일 모두 Python에서 실행 시점을 고르지만 설정하는 대상과 순서가 다릅니다. 시계에서는 실행 이벤트를 요청하고, 카메라에서는 이미 준비된 렌더 후처리 파이프라인의 Gate를 제어합니다. 앱이 진행하는 시간, 내가 발행을 요청한 시점, 외부 수신기가 받은 시점도 각각 구분해야 합니다.

공식 standalone의 다른 예제를 이어 볼 때는 Isaac Sim 설치 폴더의 `standalone_examples/api/isaacsim.ros2.bridge/`를 사용합니다. 다음 파일은 이 폴더의 CLI가 아니라 설치된 별도 예제입니다.

| 파일 | 확인할 흐름과 추가 조건 |
|---|---|
| `camera_periodic.py` | RGB step=5, depth step=60의 고정 Gate 간격을 비교합니다. Simple Warehouse 자산이 필요합니다. |
| `subscriber.py` | `/move_cube`의 Empty 메시지를 받을 때 큐브의 목표 위치를 바꿉니다. 외부 ROS 송신과 시뮬레이션의 실제 위치 적용을 나누어 봅니다. |
| `carter_stereo.py` | Carter의 좌·우 영상과 TF·오도메트리 통합을 관찰합니다. Carter 자산이 필요합니다. |
| `carter_multiple_robot_navigation.py --environment hospital` | 여러 로봇의 namespace와 TF를 비교합니다. `office` 환경도 선택할 수 있으며 실제 Nav2 주행 명령에는 별도 ROS 워크스페이스가 필요합니다. |
| `moveit.py` | `/isaac_joint_states`와 `/isaac_joint_commands`의 제어 연결을 확인합니다. Franka·환경 자산과 외부 MoveIt 계획기를 준비해야 동작 계획까지 실험할 수 있습니다. |

예를 들어 카메라 앱을 닫고 터미널 A에서 다음 수신 예제를 실행하세요.

```bash
"$ISAAC_SIM/python.sh" "$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/subscriber.py"
```

같은 Domain ID의 터미널 B에서 `ros2 topic pub --rate 1 /move_cube std_msgs/msg/Empty '{}'`를 실행하면 수신에 따라 큐브 위치가 바뀌는지 관찰할 수 있습니다. 송신은 Ctrl+C, 시뮬레이터는 창을 닫아 종료합니다. 설치 예제를 수정하려면 사본을 사용하고 로컬 `run.py`의 `--steps`, `--every` 옵션을 다른 예제에도 그대로 전달하지 마세요.

## 4. 간단한 확인 실험

카메라 앱을 종료하고 시계 실험으로 돌아옵니다. **`--every`만 10에서 30으로 바꾸고** 기록 보존을 위해 새 출력 파일을 지정하세요.

```bash
"$ISAAC_SIM/python.sh" src/119_ros2_ros2_python/run.py --every 30 --domain-id 1 --output src/119_ros2_ros2_python/output/clock_every30.json
```

수동 시계의 연속 timestamp 간격은 약 `30/60=0.5초`, 요청 프레임은 0, 30, 60…으로 바뀝니다. 자동 시계는 같은 tick 연결을 유지합니다. 정상 종료 후 JSON을 읽고 두 ROS 토픽의 수신 결과와 비교하세요. `--output` 상대경로는 현재 작업 폴더, 여기서는 저장소 루트 기준입니다.

## 실행할 때 막히면

- **토픽이 전혀 안 보임**: `run.py`의 `--domain-id`와 수신 셸을 비교하세요. 이 예제는 기본값 1이 환경변수보다 우선합니다.
- **기존 출력 파일 오류**: 새 `--output` 파일명을 사용하세요. 기본 기록을 덮어쓰지 않는 동작입니다.
- **JSON 파싱이 실패함**: 실행 중이거나 비정상 종료된 기록인지 확인하세요. 정상적인 앱 종료 뒤 읽습니다.
- **카메라 파일에 `--every`를 줬더니 오류**: 이 옵션은 시계 파일에만 있습니다. 카메라는 소스의 5·60프레임 조건으로 Gate를 제어합니다.
- **Pause 중인데 `--steps` 한도로 카메라 창이 종료됨**: 이 파일의 한도는 앱 업데이트도 셉니다. GUI를 오래 관찰하려면 한도를 생략하세요.
- **창고가 비거나 카메라가 검음**: 자산 접근과 초기 렌더 준비를 확인하세요. 기본 시계 실험은 창고 자산을 사용하지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS 2 Bridge in Standalone Workflow](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_python.html)에 대응합니다. 내부 브리지 설정은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

시계 파일은 발행 요청 기록과 종료 옵션을 포함한 로컬 실습입니다. `camera_manual.py`는 NVIDIA 예제에 GUI 수명·정리 처리를 추가했으며 [변경 고지](NOTICE.md)와 [라이선스](LICENSE-NVIDIA-EXAMPLES)를 제공합니다. `tutorial.json`은 `verification: not_run`이고 실제 DDS 시계·영상 수신은 이번 개정에서 실행 검증하지 않았습니다.
