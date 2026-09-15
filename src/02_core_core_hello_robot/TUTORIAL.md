# 02. Jetbot의 바퀴에 명령을 보내면 어떻게 움직일까요?

## 이번에 배우는 것

**Jetbot USD를 장면에 불러오고, 두 Python API로 같은 바퀴 속도 명령을 보내 실제 이동을 비교합니다.**

01번에서는 코드로 큐브를 만들었습니다. 로봇은 외형뿐 아니라 여러 링크와 관절 설정도 필요하므로, 이번에는 NVIDIA가 제공하는 Jetbot USD를 참조합니다. 모델을 불러오는 일과 초기화된 관절을 제어하는 일을 나눠 살펴보세요.

| 구분 | `--api robot` | `--api wheeled` |
|---|---|---|
| Python 객체 | `Robot` | `WheeledRobot` |
| 모델 준비 | USD reference를 먼저 추가합니다. | `create_robot=True`와 `usd_path`를 전달합니다. |
| 바퀴 지정 | 이름으로 인덱스를 찾습니다. | `wheel_dof_names`에 이름을 전달합니다. |
| 명령 전달 | 컨트롤러의 `apply_action()` | `apply_wheel_actions()` |
| 비교할 결과 | 실제 바퀴 속도와 차체 이동 | 같은 입력에서 같은 종류의 주행 |

두 경로의 기본 목표는 좌우 바퀴 각각 **4 rad/s**입니다. 바퀴의 회전 속도이지 차체의 전진 속도 4 m/s가 아닙니다.

## 1. Robot으로 Jetbot 주행하기

Isaac Sim 5.1과 지원 GPU·드라이버, Jetbot 자산이 필요합니다. 코드가 찾는 파일은 5.1 자산 루트 아래 `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`입니다. 네트워크 자산을 사용한다면 해당 서버에 접근할 수 있어야 합니다.

저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/02_core_core_hello_robot/run.py --api robot --steps 600 --wheel-speeds 4 4
```

600단계는 물리 시간 10초입니다 (왜 인지는 `world` 선언에서 단위를 보면 알 수 있죠!). 끝나면 결과를 저장하고 앱이 종료됩니다. `--steps`를 빼면 창을 닫을 때까지 주행하고, `--headless`에서 생략하면 600단계로 제한합니다. 로컬 자산을 쓰려면 같은 명령에 `--asset /실제/경로/jetbot.usd`를 추가하세요. USD가 참조하는 메시와 재질 파일도 함께 있어야 합니다.

### 코드에서 볼 부분

```python
add_reference_to_stage(usd_path=asset, prim_path="/World/Jetbot")
robot = world.scene.add(Robot(prim_path="/World/Jetbot", name="jetbot"))
```

첫 줄은 외부 USD를 현재 Stage의 `/World/Jetbot`에 연결합니다. 둘째 줄은 그 로봇을 Python에서 조회·제어할 객체로 감싸고 Scene에 등록합니다. `Robot(...)`에 경로만 넣는다고 Jetbot 모델이 저절로 만들어지는 것은 아닙니다.

`world.reset()` 이후 다음 이름으로 바퀴 인덱스를 찾습니다.

```python
wheel_names = ["left_wheel_joint", "right_wheel_joint"]
wheel_indices = np.array([robot.get_dof_index(name) for name in wheel_names])
```

DOF는 독립적으로 움직이는 자유도입니다. 모델마다 배열 순서가 달라질 수 있으므로 왼쪽·오른쪽 바퀴를 이름으로 찾습니다. 그 순서에 맞춰 두 속도를 전달합니다.

```python
robot.get_articulation_controller().apply_action(ArticulationAction(
    joint_velocities=np.array(args.wheel_speeds), joint_indices=wheel_indices))
```

`ArticulationAction`은 목표와 대상을 담는 명령 묶음입니다. 이를 보낸 뒤 `world.step()`이 물리를 진행해야 접촉과 구동 설정을 거친 실제 움직임이 나타납니다.

### 실행 결과 확인하기

터미널의 `DOF before reset`과 `DOF after reset`을 비교하세요. 초기화 전에는 관절 정보가 아직 준비되지 않을 수 있습니다. 이후에는 바퀴 이름과 인덱스를 읽을 수 있어야 합니다. 주행 중 출력되는 `wheel_rad_s`는 요청한 목표가 아니라 로봇에서 읽은 실제 바퀴 속도입니다.

결과는 이 폴더의 `output/고유번호/result.json`에 저장됩니다.

| JSON 항목 | 의미 |
|---|---|
| `command_rad_s` | 입력한 왼쪽·오른쪽 바퀴 목표입니다. |
| `wheel_indices` | 실제 articulation에서 찾은 바퀴 위치입니다. |
| `displacement_m` | 최종 위치에서 초기 위치를 뺀 월드 좌표 이동 벡터입니다. |
| `final_position_m` | 월드 좌표계에서 읽은 최종 위치입니다. |
| `orientation_wxyz` | 최종 회전을 나타내는 쿼터니언입니다. |

좌우 목표가 같으면 전진 방향으로 이동하는지 확인하세요. `displacement_m`은 이동 경로의 총 길이가 아닙니다. 곡선으로 돌아 출발점 가까이에 오면, 많이 주행해도 이 벡터의 크기는 작을 수 있습니다.

## 2. WheeledRobot으로 같은 명령 보내기

첫 실행이 끝난 뒤 API 선택만 바꿔 실행합니다. 비교를 위해 단계 수와 속도는 그대로 둡니다.

```bash
~/isaacsim/python.sh src/02_core_core_hello_robot/run.py --api wheeled --steps 600 --wheel-speeds 4 4
```

### 코드에서 볼 부분

```python
robot = world.scene.add(WheeledRobot(
    prim_path="/World/Jetbot", name="jetbot",
    wheel_dof_names=wheel_names, create_robot=True, usd_path=asset))
```

이 경로는 모델 참조와 바퀴 이름의 대응을 `WheeledRobot`에 맡깁니다. 반복문 안의 명령도 짧아집니다.

```python
robot.apply_wheel_actions(ArticulationAction(
    joint_velocities=np.array(args.wheel_speeds)))
```

명령에는 바퀴 속도 두 개만 넣습니다. `WheeledRobot`이 기억한 바퀴 이름을 사용해 전체 관절 중 대상에 대응시킵니다. 새로운 주행 물리 법칙을 쓰는 것은 아니며, 로봇의 바퀴 관절에 목표를 전달하는 절차를 줄여 줍니다.

### 실행 결과 확인하기

두 실행의 `result.json`에서 `api`는 달라도 `command_rad_s`는 `[4.0, 4.0]`인지 확인하세요. 실제 바퀴 인덱스와 주행 방향도 비교합니다. 모든 위치 성분이 소수점 끝자리까지 같아야 한다는 기준보다는, 같은 바퀴에 같은 목표를 전달했는지부터 확인하는 것이 좋습니다.

## 3. 모델·명령·실제 상태 정리

```text
Jetbot USD → Stage에 참조 → reset으로 관절 초기화
         → 바퀴 이름과 인덱스 대응 → 속도 목표 전달
         → 물리 계산 → 바퀴 실제 속도와 차체 위치 관찰
```

**명령값과 관찰값은 서로 다릅니다.** 목표 4 rad/s를 보냈어도 실제 바퀴는 가속 과정을 거칠 수 있습니다. 바퀴 반지름, 접촉, 마찰이 차체 이동을 결정하므로 여기서는 고정된 이동 거리를 정답으로 두지 않습니다. 쿼터니언 네 성분도 Euler 각도로 바로 읽지 마세요.

## 4. 간단한 확인 실험

`robot` 경로에서 **왼쪽 목표 하나만** 4에서 2 rad/s로 줄입니다.

```bash
~/isaacsim/python.sh src/02_core_core_hello_robot/run.py --api robot --steps 600 --wheel-speeds 2 4
```

양쪽 바퀴 속도 차이로 직선에서 곡선 주행으로 바뀌는지 보세요. `orientation_wxyz`의 변화와 이동 벡터를 함께 읽습니다. API, 실행 길이, 자산은 그대로이므로 이번 변화는 바퀴 목표 차이와 연결해 해석할 수 있습니다.

## 실행할 때 막히면

- **자산 루트를 찾지 못함**: 5.1 자산 경로를 설정하거나 `--asset`으로 실제 Jetbot USD를 지정하세요.
- **로봇 일부가 없거나 참조 오류가 나옴**: 최상위 USD만 복사했는지 확인하세요. 하위 메시·재질의 상대 경로도 유지해야 합니다.
- **바퀴 이름을 찾지 못함**: 이 코드는 Jetbot의 두 관절 이름을 사용합니다. 다른 로봇 USD를 지정했다면 이름과 제어 구조가 다릅니다.
- **Stop/Play 후 제어가 이상함**: 초기화 과정을 다시 수행하도록 프로그램을 재실행하세요.
- **결과 폴더가 이미 존재함**: `--output`은 새 폴더만 허용합니다. 생략하면 실행별 폴더를 만듭니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)에 대응합니다. 로봇 추가, 초기화 후 관절 조회, `Robot`과 `WheeledRobot`의 명령 전달을 독립 실행으로 구성했습니다. 최종 이동 벡터를 기록하는 JSON은 이 실습의 비교 도구입니다.

`tutorial.json`에는 두 바퀴 자유도와 전진 이동에 대한 부분 실행 기록이 있습니다. 그 기록이 모든 API·속도 조건을 검증한 것은 아니므로, 두 API와 곡선 주행 비교는 위 절차로 확인하세요.
