# 121. ROS2 Simulation Control

권장 학습 순서 **121** · ROS 2 연결과 기본 통신 · 출처 ID `t034`

**목표:** Action Graph 없이 ROS 서비스/액션으로 timeline과 USD entity를 조작합니다. `control.py`는 로컬 `cube.usda`를 spawn하고 위치를 쓰고 다시 읽은 뒤, 유한 step 후 PAUSED 상태를 확인합니다. 다른 프로세스가 시뮬레이터를 제어하는 native ROS workflow입니다.

## 이 실습의 의도

외부 ROS 클라이언트가 시뮬레이터의 실행 상태와 장면 객체를 명시적으로 바꾸고, 응답을 다시 조회해 적용 여부를 확인하는 실습입니다. `cube.usda`에는 강체를 넣지 않아 중력 운동과 위치 쓰기를 섞지 않고 서비스 동작을 관찰합니다. `control.py`의 기본 작업은 객체 생성→world 위치 설정·조회→지정 step 실행→PAUSED 확인까지이며, 시뮬레이터와 `sim_control` 확장은 먼저 별도로 실행해야 합니다.

## 실행 후 확인할 것

- **객체 생성:** ROS 터미널의 `Spawned entity:`와 Stage의 `/ControlLessonCube`를 비교합니다. 그 아래 `Geometry`가 크기 0.5 m의 녹색 Cube이고, 기본 실행 후에도 장면에 남아 있어야 합니다.
- **쓰기와 읽기 일치:** `Verified world position:` 응답의 x/y/z가 `(1,2,3)`인지 확인하고 GUI에서 해당 객체를 프레이밍합니다. 이는 쓰기 요청만 보낸 것이 아니라 `GetEntityState`로 다시 읽은 결과입니다.
- **step 이후 상태:** `Verified PAUSED after stepping`과 `/get_simulation_state`의 state=2를 확인합니다. step 수를 늘려도 Cube가 떨어지지 않는 것은 강체 없는 로컬 자산의 의도된 동작입니다.
- **재실행과 삭제:** 같은 이름의 entity가 남아 있으면 자동 덮어쓰지 않습니다. 새 `--name`을 사용하거나 `--delete` 실행의 마지막 삭제 로그와 Stage에서 해당 entity가 사라진 것을 확인합니다.
- **확장 실습의 경계:** `/simulate_steps`의 피드백·취소와 world 로드/제거는 아래 명령을 직접 수행할 때 확인하는 항목입니다. 기본 `control.py`의 성공이 모든 서비스·액션의 검증을 뜻하지는 않습니다.

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


## 준비와 실행

Isaac Sim 5.1.0, Linux, ROS 2 Humble 또는 Jazzy, `simulation_interfaces`가 필요합니다. 위 두 터미널 환경을 준비한 후 터미널 B에 인터페이스를 설치합니다.

```bash
sudo apt install ros-humble-simulation-interfaces
ros2 interface show simulation_interfaces/srv/SetSimulationState
```

터미널 A의 GUI 실행 명령에는 다음 옵션을 추가합니다.

```bash
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge --/isaac/startup/ros_sim_control_extension=True
```

UI 방식은 **Window > Extensions**에서 `isaacsim.ros2.sim_control`을 Enable합니다. 새 Stage에서 이 패키지 폴더의 터미널 B로 실행합니다.

```bash
python3 control.py --steps 10
```

1. 코드가 PLAYING→PAUSED로 전환하고 `/ControlLessonCube`에 `cube.usda`를 reference로 추가합니다. 파일 URI는 **시뮬레이터가 볼 수 있는 절대 경로**여야 하므로 같은 컴퓨터에서 실행합니다.
2. world 위치 `(1,2,3)`을 쓰고 GetEntityState 실제 응답으로 검증합니다. Cube를 선택하여 F로 프레이밍하면 그 위치에서 볼 수 있습니다.
3. StepSimulation 후 상태가 2(PAUSED)인지 실제 서비스로 확인합니다. Cube에는 강체가 없으므로 step만으로 떨어지지 않습니다. 재실행 시 같은 이름을 덮어쓰지 않습니다. `--name /ControlLessonCube2`를 쓰거나 첫 실행에 `--delete`를 주어 **자신이 만든 entity만** 마지막에 지웁니다.

## 상태, entity, world 전체 인터페이스 실습

아래 예제는 터미널 B에서 실행합니다. 응답의 `result.result`와 `error_message`를 함께 봅니다. 단, `GetSimulatorFeatures` 응답은 `features`만 가지므로 별도의 result 필드가 없습니다.

| 분류 | 서비스/타입 | 실습 |
|---|---|---|
| 기능 | `/get_simulator_features`, `GetSimulatorFeatures` | 지원 기능/포맷을 먼저 확인 |
| 상태 | `/get_simulation_state`, `GetSimulationState` | 현재 state 확인 |
| 상태 쓰기 | `/set_simulation_state`, `SetSimulationState` | `{state: {state: 1}}` Play, 2 Pause, 0 Stop/reset, 3 Quit |
| 경로 목록 | `/get_entities`, `GetEntities` | `{filters: {filter: '^/ControlLesson'}}` |
| 정보 | `/get_entity_info`, `GetEntityInfo` | `{entity: '/ControlLessonCube'}`; 현재 category는 OBJECT |
| 개별 상태 | `/get_entity_state`, `GetEntityState` | 동일 entity의 pose/twist 조회 |
| 묶음 상태 | `/get_entities_states`, `GetEntitiesStates` | 같은 regex로 여러 entity의 pose/twist 조회 |
| 생성 | `/spawn_entity`, `SpawnEntity` | URI가 없으면 Xform, 있으면 USD reference |
| 삭제 | `/delete_entity`, `DeleteEntity` | `{entity: '/ControlLessonCube'}` |
| reset | `/reset_simulation`, `ResetSimulation` | Stop, service로 spawn한 prim 제거, timeline 재시작 |
| pose/속도 | `/set_entity_state`, `SetEntityState` | world frame pose/twist 설정; local frame은 미지원 |
| 스텝 | `/step_simulation`, `StepSimulation` | PAUSED에서 `{steps: 10}`; 완료 후 PAUSED |
| world 로드 | `/load_world`, `LoadWorld` | `{uri: '/absolute/path/to/world.usda'}`; 이전 Stage를 교체 |
| world 제거 | `/unload_world`, `UnloadWorld` | 빈 Stage 생성 |
| 현재 world | `/get_current_world`, `GetCurrentWorld` | 파일 URI/name; 메모리 Stage는 untitled_world |
| 사용 가능 world | `/get_available_worlds`, `GetAvailableWorlds` | tag, 추가 경로, offline_only로 검색 |

타입 전체 경로는 모두 `simulation_interfaces/srv/<표의 타입>`입니다. 실제 명령 예:

```bash
ros2 service call /get_entities simulation_interfaces/srv/GetEntities "{filters: {filter: '^/ControlLesson'}}"
ros2 service call /get_entity_info simulation_interfaces/srv/GetEntityInfo "{entity: '/ControlLessonCube'}"
ros2 service call /get_entities_states simulation_interfaces/srv/GetEntitiesStates "{filters: {filter: 'ControlLesson'}}"
ros2 service call /get_current_world simulation_interfaces/srv/GetCurrentWorld '{}'
ros2 service call /get_available_worlds simulation_interfaces/srv/GetAvailableWorlds "{additional_sources: ['/absolute/path/to/this/package'], offline_only: true, continue_on_error: true}"
```

`GetEntities` 필터는 POSIX extended regex입니다. `^/World`는 접두 경로, `mesh$`는 끝 이름을 찾습니다. `entity_namespace`는 spawn prim의 `isaac:namespace`에 저장되며 prim 이름 그 자체와 다릅니다. `allow_renaming:false`는 이름 충돌을 오류로 반환합니다.

World 작업은 저장하지 않은 Stage를 바꾸므로 실습 Stage에서만 수행합니다. 먼저 0(Stop) 또는 2(Pause)로 만든 뒤, `load_world`에 이 패키지 `cube.usda`의 절대 경로를 넣습니다. `get_current_world`에서 로드 URI를 확인하고 `unload_world`로 빈 Stage가 되는지 봅니다. `load_world`는 USD 포맷만 지원하며 Playing 상태는 거절됩니다.

## 피드백이 있는 Action

```bash
ros2 service call /set_simulation_state simulation_interfaces/srv/SetSimulationState '{state: {state: 2}}'
ros2 action send_goal /simulate_steps simulation_interfaces/action/SimulateSteps '{steps: 20}' --feedback
```

진행 중 completed/remaining 피드백, 완료 result, 이후 PAUSED 상태를 확인합니다. Action은 서비스와 달리 진행 피드백과 취소를 지원합니다. 원문은 1 frame 요청에 내부적으로 2 step이 사용될 수 있다고 명시하므로 요청 정수 하나를 고정된 벽시계 시간으로 해석하지 않습니다.

## API/Omniverse 해설과 실험

확장의 `ROS2ServiceManager`는 ROS executor를 관리하고 `SimulationControl`이 `omni.timeline`/Stage API를 호출합니다. Action Graph의 Play Tick과 독립적이므로 Pause 중에도 서비스에 응답할 수 있습니다. USD prim을 entity 이름으로 사용하고 reference는 외부 USD의 내용을 Stage에 합성합니다. `simulationInterfacesSpawned` attribute로 생성된 entity를 추적하여 ResetSimulation에서 제거합니다.

5.1의 GetEntityState에서 강체는 pose와 속도를, 비강체는 pose와 0 속도를 반환합니다. acceleration은 현재 0으로 보고하며 SetEntityState의 acceleration도 적용하지 않습니다. 0이라는 값이 가속도를 실제 측정했다는 뜻은 아닙니다.

한 가지 변수 실험은 `--steps`만 10→20으로 바꾸는 것입니다. 매번 다른 entity 이름을 주거나 `--delete`를 사용하고 PAUSED 복귀를 확인합니다. `RESULT_INCORRECT_STATE`는 먼저 Pause해야 한다는 뜻입니다. `RESOURCE_PARSE_ERROR`는 시뮬레이터 쪽 URI/권한/포맷을, 서비스가 없으면 확장 활성화/인터페이스 설치/Domain ID를 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
