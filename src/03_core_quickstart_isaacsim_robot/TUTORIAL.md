# 03. 로봇 관절을 읽고, 자세 변경과 속도 제어를 비교하기

## 이번에 배우는 것

**Franka 팔과 Nova Carter를 불러와 관절 정보를 조사하고, 상태를 직접 바꾸는 명령과 목표를 추종하는 명령의 차이를 확인합니다.**

02번에서 Jetbot 바퀴의 속도 목표를 보냈습니다. 이번에는 로봇 팔도 함께 사용합니다. 팔에는 구간이 바뀔 때 관절 위치를 한 번 지정하고, 차량에는 구간 내내 바퀴 속도 목표를 보냅니다. 겉으로는 모두 로봇을 움직이는 코드지만, 물리 상태에 관여하는 방식이 다릅니다.

| 대상 | Stage 경로 | 이 실습의 명령 | 확인할 결과 |
|---|---|---|---|
| Franka Panda | `/World/Arm` | `set_joint_positions()` | 구간 시작 때 팔 자세가 바뀝니다. |
| Nova Carter | `/World/Car` | `set_joint_velocity_targets()` | 바퀴가 목표 속도를 추종하며 차체가 이동합니다. |
| 관절 정보 | `joint_info.json` | 초기화 후 조회 | 이름·자유도 수·한계·초기 위치입니다. |
| 시간별 상태 | `states.csv` | 매 단계 관찰 | 구간, 차량 위치, 두 로봇의 관절 위치입니다. |

관절로 연결된 강체 시스템을 **articulation**이라고 부릅니다. DOF는 제어 가능한 자유도이며, 전체 관절 수에는 고정 관절 등이 포함될 수 있어 두 개수가 항상 같지는 않습니다.

## 1. 두 로봇의 네 구간 실행하기

Isaac Sim 5.1, 지원 GPU·드라이버와 다음 NVIDIA 자산이 필요합니다. 경로는 5.1 자산 루트 기준입니다.

| 로봇 | 자산 경로 |
|---|---|
| Franka | `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd` |
| Carter | `/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd` |

저장소 루트에서 아래 명령을 실행하세요. `~/isaacsim`은 실제 설치 위치에 맞춥니다.

```bash
~/isaacsim/python.sh src/03_core_quickstart_isaacsim_robot/run.py --steps 480
```

물리 간격은 1/60초이므로 480단계는 물리 시간 8초입니다. 이를 마치면 앱이 종료됩니다. `--headless`를 추가하면 창 없이 실행합니다. 단계 수를 생략한 GUI는 각 120단계의 네 구간을 반복하고, Headless는 480단계로 종료합니다.

로컬 자산을 사용할 때는 `--arm-usd /실제/경로/franka.usd --car-usd /실제/경로/nova_carter.usd`를 함께 추가하세요. 두 경로 모두 지정하면 코드가 기본 자산 루트를 조회하지 않습니다. USD의 하위 참조 파일도 있어야 합니다.

### 코드에서 볼 부분

USD를 `/World/Arm`, `/World/Car`에 참조한 후 각각 `Articulation`으로 감쌉니다. 로봇의 초기 y 위치는 +1.2 m와 −1.2 m여서 서로 겹치지 않습니다. `world.reset()` 다음에 물리 핸들이 유효한지 확인하고 관절 정보를 저장합니다.

이 API는 여러 로봇을 한꺼번에 다루는 배열 형식을 사용합니다. 따라서 로봇 한 대의 위치도 `(1, 3)`, 관절 위치도 `(1, K)` 형태입니다. 첫 번째 축의 `1`은 로봇 수, `K`는 대상으로 삼은 관절 수입니다.

팔은 일곱 `panda_joint`와 두 손가락 관절을 이름으로 찾습니다. 차량에서는 **`joint_wheel_left`, `joint_wheel_right` 두 관절만** 선택합니다. 모든 Carter 관절에 같은 속도를 보내는 코드가 아닙니다.

```python
if phase != previous_phase:
    arm.set_joint_positions(
        moved if phase in (1, 3) else home, joint_indices=arm_indices
    )
    previous_phase = phase
speed = args.wheel_speed if phase in (1, 3) else 0.0
car.set_joint_velocity_targets(
    np.array([[speed, speed]]), joint_indices=wheel_indices
)
```

`set_joint_positions()`는 현재 관절 상태를 직접 지정합니다. 이 파일은 팔의 자세 유지용 목표를 반복 갱신하지 않습니다. 반면 차량의 속도 목표는 매 단계 전달하고, 바퀴 drive와 물리 계산이 실제 속도를 결정합니다.

### 실행 결과 확인하기

단계 수를 지정하면 전체 실행을 네 구간으로 나눕니다. 기본 `--steps 480`에서는 다음 순서가 한 번 진행됩니다.

| `phase` | CSV의 `step` | 팔에 한 번 지정하는 자세 | 차량 바퀴 목표 |
|---|---|---|---|
| 0 | 1~120 | `home` | 0 rad/s |
| 1 | 121~240 | `moved` | 1 rad/s |
| 2 | 241~360 | `home` | 0 rad/s |
| 3 | 361~480 | `moved` | 1 rad/s |

결과는 이 폴더의 `output/날짜-시간/`에 저장됩니다. `joint_info.json`에서 `dof_names`와 `limits`를 먼저 읽고, `states.csv`의 `arm_q`, `car_q` 배열을 그 순서에 대응시키세요. 팔의 회전 관절 위치는 rad, 직선으로 움직이는 손가락 위치는 m 단위입니다.

`car_x_m`, `car_y_m`이 주행 구간에서 변하는지 확인합니다. 정지 목표를 보낸 순간에도 감속 과정이 있을 수 있습니다. 팔은 구간 시작에만 상태를 지정하므로 각 구간의 모든 `arm_q`가 `home` 또는 `moved`와 완전히 같아야 한다고 판단하지 마세요.

## 2. GUI에서 조사하고 Script Editor에서 관찰하기

### GUI 설정에서 볼 부분

독립 실행을 종료한 뒤 `~/isaacsim/isaac-sim.sh`로 새 창을 엽니다.

1. **File > New**로 장면을 만들고 지면과 Distant Light를 추가합니다. **Create > Robots > Franka Emika Panda Arm**으로 로봇을 넣으세요.
2. 로봇 루트를 선택하고 **Tools > Physics > Physics Inspector**를 엽니다. 관절 한계와 기본 위치를 살펴보고 오른쪽 위 메뉴에서 stiffness·damping 열도 표시해 보세요.
3. 회전 관절 하나를 한계 안에서 조금 움직입니다. 변경한 값을 기본값으로 확정할 때는 초록 체크를 누릅니다.
4. **Tools > Robotics > Omnigraph Controllers > Joint Position**을 엽니다. **Robot Prim > Add**에서 Franka를 선택하고 **OK**로 그래프를 생성합니다.
5. Stage의 **Graph > Position_Controller > JointCommandArray**를 선택합니다. 나머지 값은 유지한 채 첫 번째 팔 관절 목표만 0.2 rad 정도로 바꾸고 Play에서 움직임을 확인하세요.
6. **Window > Graph Editors > Action Graph > Edit Action Graph**에서 생성된 그래프를 선택합니다. 배열의 위치 명령이 Articulation Controller로 들어가는 연결과 대상 로봇 경로를 따라가 보세요.

이 그래프는 관절 위치 **목표**를 제어기에 전달합니다. 앞의 독립 실행이 구간 시작에 팔 상태를 직접 지정한 것과 비교할 수 있습니다.

### Script Editor 코드에서 볼 부분

GUI 그래프 실습과 별개로 **새 Isaac Sim 창**을 열고 빈 장면에서 `script_editor.py` 전체를 실행하세요. **Window > Script Editor**를 사용합니다. 파일은 바닥·조명·Franka를 만들고 비동기로 초기화합니다. `Ready` 출력 후 같은 탭에서 아래 호출을 하나씩 실행하세요.

```python
inspect_robot()
move_robot()
inspect_robot()
start_logging()
```

`inspect_robot()`은 호출한 순간의 관절 정보를 한 번 출력합니다. `move_robot()`은 팔 자세를 직접 지정합니다. `start_logging()`은 다음 물리 콜백을 등록해 반복 관찰합니다.

```python
tutorial_world.add_physics_callback(
    "quickstart_robot_state",
    lambda dt: print(dt, arm_handle.get_joint_positions()),
)
```

`dt`는 물리 간격이고 뒤의 배열은 그 시점의 실제 관절 위치입니다. 반복문으로 `world.step()`을 호출하지 않아도 재생 중인 GUI가 물리를 진행합니다.

### 실행 결과 확인하기

Play 상태에서 `start_logging()` 후 출력이 계속 늘어나는지 보세요. 관찰을 마치면 같은 탭에서 `stop_logging()`을 실행합니다. 이 함수는 콜백만 제거하며 앱을 종료하지 않습니다. Script Editor 방식은 CSV를 저장하지 않으므로 출력 영역에서 한 번 읽기와 반복 읽기의 차이를 확인합니다.

## 3. 상태 지정과 목표 전달 정리

```text
팔 상태 직접 지정 → 해당 시점의 관절 위치 변경 → 이후 물리 상태 관찰
바퀴 속도 목표 전달 → 구동기가 목표 추종 → 접촉을 거쳐 차체 이동
물리 콜백 등록 → 물리가 진행될 때마다 실제 관절 상태 읽기
```

관절 값을 해석하려면 이름·배열 순서·단위가 먼저 필요합니다. `joint_info.json`과 `states.csv`를 함께 만든 이유도 여기에 있습니다. 숫자 배열만 보지 않고 어느 로봇의 어느 관절인지 연결해서 읽어 보세요.

## 4. 간단한 확인 실험

차량의 주행 목표만 절반으로 줄입니다.

```bash
~/isaacsim/python.sh src/03_core_quickstart_isaacsim_robot/run.py --steps 480 --wheel-speed 0.5
```

구간 전환 시점과 팔 명령은 그대로이고 주행 구간의 바퀴 목표만 달라집니다. `car_q`의 바퀴 관절 변화와 `car_x_m`, `car_y_m`을 이전 실행과 비교하세요. 이동 거리는 가속·접촉의 영향으로 정확히 절반이 아닐 수 있지만, 속도 목표를 줄인 효과를 관찰할 수 있습니다.

## 실행할 때 막히면

- **자산 루트나 articulation 초기화 오류**: 두 USD와 하위 참조가 모두 열리는지 확인하세요. 로컬 파일을 쓰면 두 자산 옵션을 함께 지정합니다.
- **`unexpected joints` 오류**: 자산 관절 이름이 예상과 다릅니다. 생성된 `joint_info.json`에서 누락된 이름을 확인하세요.
- **Script Editor에서 기존 World 오류**: File > New만으로 Python의 World가 사라지지는 않습니다. 새 앱 창에서 시작하세요.
- **콜백 출력이 늘지 않음**: Pause 상태인지 확인하고 Play를 재개하세요. 출력이 많으면 `stop_logging()`으로 해제합니다.
- **GUI 그래프가 팔을 움직이지 않음**: 그래프의 대상 경로와 실제 로봇 루트, 배열의 관절 순서, Play 상태를 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Basic Robot Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim_robot.html)에 대응합니다. 원문의 로봇 조사·그래프·콜백·네 구간 제어를 유지하면서, 차량 명령은 두 바퀴 관절에만 보내고 상태를 파일로 기록하도록 구성했습니다.

관절 API의 배경은 [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)를 참고하세요. 위 관찰값은 실행 시 확인할 기준입니다. `tutorial.json`의 현재 실행 검증 상태는 `not_run`입니다.
