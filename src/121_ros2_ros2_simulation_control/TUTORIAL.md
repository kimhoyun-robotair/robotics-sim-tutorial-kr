# 121. ROS 서비스로 장면을 만들고 시뮬레이션을 멈추기

## 이번에 배우는 것

**외부 Python 클라이언트로 큐브를 생성하고 위치를 바꾼 뒤, 지정한 단계만 실행하고 일시정지 상태로 돌아오는지 확인합니다.**

시뮬레이터의 Play 버튼을 사람이 누르는 대신 다른 프로그램에서 제어하고 싶을 때가 있습니다. `simulation_interfaces`는 이런 요청을 ROS 서비스와 액션으로 표현합니다. 서비스는 요청과 응답을 한 쌍으로 주고받는 통신 방식입니다.

| 구성 | 실행 장소 | 역할 |
|---|---|---|
| `isaacsim.ros2.sim_control` 확장 | Isaac Sim | 시뮬레이션 상태와 장면 변경 요청 처리 |
| `control.py` | 시스템 ROS Python | 생성·이동·조회·단계 실행 요청 |
| `cube.usda` | 시뮬레이터가 읽을 로컬 파일 | 크기 0.5 m의 녹색 큐브 자산 |
| `GetEntityState` | 서비스 응답 | 요청한 위치가 적용됐는지 재확인 |

이번 큐브에는 강체가 없습니다. 위치 변경과 중력 운동이 섞이지 않아 서비스가 쓴 좌표를 바로 확인할 수 있습니다.

## 1. 시뮬레이터와 외부 클라이언트 실행하기

아래는 같은 Linux 컴퓨터의 **Isaac Sim 5.1.0과 ROS 2 Jazzy**를 사용하는 Bash 절차입니다. 지원 GPU가 필요합니다. 터미널 A는 시뮬레이터용, B는 시스템 ROS용으로 나눕니다.

**터미널 A**는 `/opt/ros`를 source하지 않은 상태에서 시작합니다. Isaac Sim의 Python 3.11에는 내부 ROS 라이브러리를 연결합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge --/isaac/startup/ros_sim_control_extension=True
```

**File > New**로 실습할 빈 장면을 엽니다. **Window > Extensions**에서 `isaacsim.ros2.sim_control`이 켜져 있는지 확인하세요. 별도의 Action Graph는 만들지 않습니다.

**터미널 B**는 저장소 루트에서 다음을 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
sudo apt install ros-jazzy-simulation-interfaces
ros2 interface show simulation_interfaces/srv/SetSimulationState
python3 src/121_ros2_ros2_simulation_control/control.py --steps 10
```

`control.py`가 종료되어도 Isaac Sim 창은 남습니다. Cube를 선택하고 **F**를 눌러 프레이밍하세요. 스크립트는 기존 시뮬레이터를 제어하며 앱을 직접 시작하거나 종료하지 않습니다.

### 실행 결과 확인하기

| 터미널 출력 | 의미 | 함께 확인할 것 |
|---|---|---|
| `Spawned entity:` | 생성 서비스가 반환한 경로 | `/ControlLessonCube`와 자식 `Geometry` |
| `Verified world position:` | 위치를 다시 조회하여 비교 완료 | x=1, y=2, z=3 m |
| `Verified PAUSED after stepping` | 단계 실행 뒤 상태 재조회 완료 | 타임라인 일시정지 |

큐브는 공중에 그대로 있습니다. 강체 없는 도형의 변환값을 편집했기 때문에 정상입니다. 기본 실행은 생성한 큐브를 남기며 CSV는 저장하지 않습니다.

## 2. 요청을 보내고 결과를 다시 읽는 코드 살펴보기

### 코드에서 볼 부분

먼저 클라이언트가 Play 후 Pause를 요청합니다. 이후 자산을 생성할 때 다음 값들을 사용합니다.

```python
request = SpawnEntity.Request(
    name=args.name, allow_renaming=False, uri=str(args.asset.resolve()))
request.initial_pose.pose.orientation.w = 1.0
```

`uri`는 `cube.usda`의 절대 경로입니다. 파일 내용 자체를 ROS로 보내지 않으므로 **그 경로의 파일을 시뮬레이터가 직접 읽을 수 있어야 합니다.** 처음에 같은 컴퓨터에서 실습하는 이유입니다. `orientation.w=1`은 회전 없는 정상 quaternion을 지정합니다.

`allow_renaming=False`이므로 같은 이름이 있으면 오류로 알려줍니다. 재실행하려면 `--name /ControlLessonCube2`를 사용하거나, 처음부터 `--delete`를 지정하여 검증을 마친 자기 큐브를 마지막에 삭제하세요.

위치를 설정할 때는 좌표계도 명시합니다.

```python
move.state.header.frame_id = 'world'
move.state.pose.position.x = 1.0
move.state.pose.position.y = 2.0
move.state.pose.position.z = 3.0
```

이 좌표는 **world 기준 위치**입니다. 코드는 `SetEntityState` 응답을 받은 후 `GetEntityState`로 다시 읽고, 각 성분의 오차가 `1e-6`보다 크면 실패로 처리합니다.

마지막에는 `/step_simulation`을 호출하고 `/get_simulation_state`를 조회합니다. 기대 상태는 `SimulationState.STATE_PAUSED`, 즉 2입니다. 요청 전송과 실제 반영 확인을 별도 단계로 둔 구조입니다.

### 서비스와 액션 비교하기

기본 실행이 끝난 뒤 터미널 B에서 상태를 직접 읽어 보세요.

```bash
ros2 service call /get_simulation_state simulation_interfaces/srv/GetSimulationState '{}'
ros2 service call /get_entity_state simulation_interfaces/srv/GetEntityState '{entity: /ControlLessonCube}'
ros2 action send_goal /simulate_steps simulation_interfaces/action/SimulateSteps '{steps: 20}' --feedback
```

`--delete`로 큐브를 삭제했다면 두 번째 조회는 대상이 없다고 응답합니다. 액션은 단계 실행의 진행 피드백을 받을 수 있다는 점이 단일 서비스 응답과 다릅니다. 완료 후 상태를 다시 조회해 Pause 복귀를 확인하세요. 요청 단계 수를 벽시계 초로 읽지는 않습니다. 공식 5.1 구현에는 요청 프레임과 내부 단계가 일대일이 아닌 경우도 설명되어 있습니다.


### entity 목록과 world 전체 제어 비교하기

큐브 하나의 조회를 확인했다면 같은 ROS 터미널에서 관련 entity를 찾아보세요.

```bash
ros2 service call /get_entities simulation_interfaces/srv/GetEntities "{filters: {filter: '^/ControlLesson'}}"
ros2 service call /get_entity_info simulation_interfaces/srv/GetEntityInfo '{entity: /ControlLessonCube}'
ros2 service call /get_entities_states simulation_interfaces/srv/GetEntitiesStates "{filters: {filter: '^/ControlLesson'}}"
```

필터는 경로에 적용하는 정규식입니다. `^/ControlLesson`은 그 이름으로 시작하는 경로를 찾습니다. `GetEntityInfo`의 정보와 `GetEntityState`의 pose는 서로 다른 응답입니다. 속도·가속도 필드도 타입에 있지만 이 자산은 비강체이고 5.1에서 가속도 설정은 지원하지 않습니다. 0 값만 보고 실제 가속도를 측정했다고 해석하지 마세요.

이제 보관할 Stage를 저장하고 **실습 장면에서만** world 교체를 수행합니다. 저장소 루트로 돌아온 ROS 터미널에서 자산의 절대 경로를 먼저 구하세요.

```bash
lesson_asset="$(realpath src/121_ros2_ros2_simulation_control/cube.usda)"
ros2 service call /set_simulation_state simulation_interfaces/srv/SetSimulationState '{state: {state: 2}}'
ros2 service call /load_world simulation_interfaces/srv/LoadWorld "{uri: '$lesson_asset'}"
ros2 service call /get_current_world simulation_interfaces/srv/GetCurrentWorld '{}'
ros2 service call /unload_world simulation_interfaces/srv/UnloadWorld '{}'
```

`SpawnEntity`는 기존 Stage 안에 객체를 추가하지만 `LoadWorld`는 **현재 Stage 전체를 연 USD로 교체**합니다. 로드 후에는 `cube.usda`의 `/CubeAsset`과 현재 world의 URI를 확인합니다. Unload 뒤에는 빈 Stage가 되어야 합니다. Playing 중 로드·제거 요청은 거절되므로 먼저 Pause 또는 Stop합니다.

`GetAvailableWorlds`로 지정 폴더의 후보도 조회할 수 있습니다.

```bash
ros2 service call /get_available_worlds simulation_interfaces/srv/GetAvailableWorlds \
  "{additional_sources: ['$(dirname "$lesson_asset")'], offline_only: true, continue_on_error: true}"
```

목록 조회는 실제 파일 로드와 다릅니다. URI와 포맷을 읽은 뒤 LoadWorld로 확인하세요. `ResetSimulation` 역시 단순 Pause와 다릅니다. 5.1 구현은 reset 요청에서 서비스로 생성한 prim을 정리하고 타임라인을 재시작하므로, 유지해야 하는 객체가 있는 상태에서 상태 조회와 혼동하여 호출하지 마세요.

서비스 응답의 `result.result`와 `error_message`를 함께 읽습니다. `GetSimulatorFeatures`는 `features` 목록을 반환하는 예외로 별도의 result 필드가 없습니다. 이런 차이는 `ros2 interface show simulation_interfaces/srv/<타입>`으로 직접 확인할 수 있습니다.

## 3. 제어 요청과 확인의 관계 정리

```text
지원 기능 조회 → Play → Pause
  → cube.usda를 entity로 생성
  → world 위치 쓰기 → 같은 entity의 위치 읽기
  → N단계 실행 → PAUSED 상태 읽기
  → --delete가 있으면 생성한 entity 삭제
```

**쓰기 응답과 재조회 결과를 함께 보면 “요청을 받았다”와 “원하는 상태가 됐다”를 나누어 확인할 수 있습니다.** 원문의 world 로드·제거는 Stage 전체를 바꾸는 기능입니다. 이 실습은 한 entity의 생성과 이동에 집중합니다.

## 4. 간단한 확인 실험

world 교체 실습 뒤에는 새 빈 Stage에서 기본 명령을 다시 실행해 `/ControlLessonCube`를 만드세요. 이어 **`--name`만 다른 경로로** 바꾸어 한 번 더 실행합니다.

```bash
python3 src/121_ros2_ros2_simulation_control/control.py --steps 10
python3 src/121_ros2_ros2_simulation_control/control.py --steps 10 --name /ControlLessonCube2
```

두 실행의 `Spawned entity:` 경로가 달라지고 Stage에 두 root가 생겨야 합니다. 위치는 둘 다 `(1,2,3)`이어서 Viewport에서는 서로 겹쳐 보일 수 있습니다. 아래 조회로 서로 다른 entity임을 확인하세요.

```bash
ros2 service call /get_entities simulation_interfaces/srv/GetEntities "{filters: {filter: '^/ControlLesson'}}"
```

이번에는 같은 좌표라도 entity 이름이 다르면 별도 객체라는 것을 확인합니다. 기본 클라이언트의 단계 수를 바꾸는 것만으로는 강체 없는 큐브의 pose와 최종 PAUSED 출력이 달라지지 않으므로, 그 두 값만으로 정확한 단계 수를 측정했다고 판단하지 않습니다.

## 실행할 때 막히면

- **`Service ... unavailable`**: sim_control 확장과 두 터미널의 Domain ID를 확인하세요. 기본 대기 시간은 20초이며 초기화가 더 걸리면 준비 후 다시 실행합니다.
- **자산 읽기 오류**: `--asset`이 실제 USD 파일인지, 시뮬레이터도 그 절대 경로를 읽을 수 있는지 확인하세요.
- **같은 이름의 entity가 이미 있음**: 새 이름을 사용하세요. 실패한 이전 실행은 마지막 삭제 단계까지 도달하지 않았을 수 있습니다.
- **`RESULT_INCORRECT_STATE`**: 수동 단계 요청 전에 상태를 Pause로 바꾸세요. 기본 클라이언트는 이 순서를 직접 수행합니다.
- **큐브가 떨어지지 않음**: `cube.usda`에는 `RigidBodyAPI`가 없습니다. 이번 결과는 서비스로 설정한 pose입니다.

Ubuntu 22.04/Humble을 사용한다면 위 명령의 `jazzy`를 `humble`로 맞추세요. 시뮬레이터와 외부 ROS의 배포판을 함께 변경합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)에 대응합니다. 환경 구성은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 참고하세요.

로컬 코드는 생성·위치 재조회·단계 실행·Pause 확인을 연결합니다. 원문 전체의 world 관리와 모든 서비스/액션을 자동 시험하는 코드는 아닙니다. `tutorial.json`은 `verification: not_run`이며 이 문서의 출력값은 실제 실행 시 확인할 기준입니다.
