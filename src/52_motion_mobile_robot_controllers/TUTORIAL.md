# 52. 차체 속도를 바퀴 명령으로 바꾸기

## 이번에 배우는 것

**같은 전진·회전 요구가 차동 구동, 전방향 구동, 자동차식 조향에서 어떻게 다른 관절 명령이 되는지 비교합니다.**

로봇에게 “앞으로 0.3 m/s로 가세요”라고 말하려면 바퀴 반지름과 배치를 알아야 합니다. 작은 바퀴는 같은 거리를 가는 동안 더 많이 돌아야 하고, 선회할 때는 안쪽과 바깥쪽 바퀴의 움직임도 달라집니다. 이번에는 controller가 계산한 명령과 실제 차체 위치를 함께 확인합니다.

| 선택값 `--robot` | 로봇 | 입력의 의미 | 출력 |
|---|---|---|---|
| `differential` | Jetbot | 전진 m/s, yaw rad/s | 좌우 바퀴 각속도 |
| `holonomic` | Kaya | 전진·측면 m/s, yaw rad/s | 세 바퀴 각속도 |
| `ackermann` | Leatherback | 조향각 rad, 차체 속도 m/s 등 | 앞바퀴 조향각 2개, 구동 속도 4개 |

**`--turn`은 앞의 두 모드에서는 회전 속도, Ackermann에서는 조향각**입니다. 숫자가 같아도 같은 선회 조건을 뜻하지 않습니다.

## 1. 먼저 Jetbot의 좌우 바퀴를 비교하기

Isaac Sim 5.1과 선택한 로봇의 5.1 Assets가 필요합니다. 로봇별 경로는 `Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`, `Kaya/kaya.usd`, `Leatherback/leatherback.usd`입니다. 뒤의 두 경로도 `Isaac/Robots/NVIDIA/` 아래에 있습니다.

아래 명령은 **저장소 루트** 기준입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/52_motion_mobile_robot_controllers/run.py \
  --robot differential --speed 0.3 --turn 0.3 --steps 600
```

바닥 위 Jetbot에 일정한 주행 명령을 600단계 적용하고 종료합니다. 결과는 이 폴더의 새 `output/run_*/drive.json`입니다. `--headless`로 창 없이 실행할 수 있으며, GUI에서 `--steps`를 생략하면 창을 닫을 때까지 계속 주행합니다.

### 코드에서 볼 부분

```python
controller = DifferentialController(
    'differential', wheel_radius=0.03, wheel_base=0.1125)
command = [args.speed, args.turn]
action = controller.forward(command)
```

반지름 `r=0.03 m`, 양 바퀴 간격 `L=0.1125 m`로 차체 전진 속도 `v`와 회전 속도 `ω`를 바퀴 각속도로 바꿉니다.

```text
왼쪽 바퀴: (v − ωL/2) / r
오른쪽 바퀴: (v + ωL/2) / r
```

위 명령의 계산값은 왼쪽 **9.4375 rad/s**, 오른쪽 **10.5625 rad/s**입니다. 양수 yaw를 만들기 위해 오른쪽 바퀴 목표가 더 큽니다. 이는 기구학 계산으로 얻은 **명령 기대값**이며, 물리에서 측정한 실제 바퀴 속도는 아닙니다.

계산은 반복문 밖에서 한 번 수행합니다. 반복문에서는 `apply_wheel_actions(action)`으로 동일 명령을 계속 전달하고 물리를 진행합니다. GUI에서 차체가 밀려도 목표 경로로 복귀시키는 위치 제어는 하지 않습니다.

### 실행 결과 확인하기

| `drive.json` 항목 | 확인할 내용 |
|---|---|
| `controller`, `command` | 어떤 구동 방식과 입력을 사용했는지 |
| `wheel_velocity_targets_rad_s` | controller가 계산한 바퀴 목표 |
| `steering_targets_rad` | Ackermann의 조향 목표, 다른 모드는 `null` |
| `initial_position_m`, `final_position_m` | 실제 차체 시작·마지막 위치 |
| `orientation_wxyz` | 마지막 방향 quaternion |

Jetbot의 바퀴 목표를 위 계산값과 비교하고, 차체가 선회했는지는 위치와 방향을 함께 보세요. 원을 돌아 시작점 근처에 올 수 있으므로 변위가 작다고 움직이지 않았다고 판단하면 안 됩니다. 이 파일에는 이동 경로 전체나 실제 바퀴 속도는 저장되지 않습니다.

## 2. 옆으로 가는 Kaya와 조향하는 Leatherback

다음 두 명령은 각각 새 실행으로 진행하세요.

```bash
~/isaacsim/python.sh src/52_motion_mobile_robot_controllers/run.py \
  --robot holonomic --speed 0 --lateral 0.3 --turn 0 --steps 600

~/isaacsim/python.sh src/52_motion_mobile_robot_controllers/run.py \
  --robot ackermann --speed 1.1 --turn 0.1 --steps 600
```

Kaya는 차체가 바라보는 방향을 바꾸지 않고 옆으로 가도록 요구합니다. `HolonomicController`는 세 바퀴의 위치·방향·반지름과 roller 각도를 사용해 `[vx, vy, yaw_rate]`를 각 바퀴 속도로 바꿉니다. 코드의 바퀴 순서와 `axle_0_joint`~`axle_2_joint`의 순서가 맞아야 원하는 방향으로 움직입니다.

### 코드에서 볼 부분

Leatherback에서는 관절의 역할이 둘로 나뉩니다.

```python
robot.apply_action(ArticulationAction(
    joint_positions=action.joint_positions, joint_indices=steering))
robot.apply_action(ArticulationAction(
    joint_velocities=action.joint_velocities, joint_indices=wheels))
```

앞바퀴의 **방향을 꺾는 두 관절에는 위치**, 바퀴를 **굴리는 네 관절에는 속도**를 보냅니다. 코드도 steering 관절은 position 모드, wheel 관절은 velocity 모드로 설정합니다. 서로 다른 관절 인덱스 집합으로 보내므로 두 명령이 역할을 나눕니다.

Ackermann 입력은 `[steering_angle, steering_velocity, speed, acceleration, dt]` 순서입니다. 이 실습은 `[args.turn, 0, args.speed, 0, 0]`을 사용합니다. 차축 간격은 1.65 m, 좌우 바퀴 간격은 1.25 m, 바퀴 반지름은 0.25 m입니다. 선회 원의 안쪽과 바깥쪽 바퀴는 다른 궤적을 따라야 하므로 좌우 조향각을 따로 계산합니다.

### 실행 결과 확인하기

Kaya에서는 속도 목표가 3개인지, 실제로 측면 이동하는지 확인하세요. `--lateral`은 Kaya 분기에서만 읽으므로 Jetbot에 넣어도 측면 이동 기능이 생기지 않습니다.

Leatherback에서는 조향 목표 2개와 바퀴 속도 4개를 확인하세요. `--speed 1.1`의 단위는 **차체 m/s**이며 바퀴 rad/s가 아닙니다. Kaya의 `mecanum_angles=[90, 90, 90]`은 설치된 5.1 controller에서 degree 기반 회전에 사용합니다. 이를 `π/2`로 바꾸지 마세요. 관련 구동 방식과 입력은 [공식 Mobile Robot Controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html)와 함께 볼 수 있습니다.

### 같은 바퀴 명령을 OmniGraph로 연결하기

Python 실행을 종료하고 `~/isaacsim/isaac-sim.sh`로 새 창을 여세요. 먼저 Jetbot으로 데이터 연결을 익힙니다.

1. 빈 stage에 Content Browser의 위 Jetbot USD를 reference로 추가합니다. 로봇 prim을 `/World/Jetbot`으로 맞추고 z=0.1 m에 두세요. **Create > Physics > Physics Scene**과 **Ground Plane**으로 물리 장면과 바닥을 준비합니다.
2. **Window > Graph Editors > Action Graph**에서 새 그래프를 만들고 **On Playback Tick**, **Differential Controller**, **Articulation Controller**를 추가하세요. 마지막 노드의 타입은 `IsaacArticulationController`입니다.
3. Tick의 실행 출력을 두 controller의 `execIn`에 각각 연결합니다. Differential Controller에는 다음 실행 출력이 없으므로 그 뒤에 실행 선을 직렬로 연결하지 않습니다.
4. Differential Controller의 `wheelRadius=0.03`, `wheelDistance=0.1125`, `linearVelocity=0.3`, `angularVelocity=0.3`으로 지정하세요. 출력 `velocityCommand`를 Articulation Controller의 같은 이름 입력에 연결합니다.
5. Articulation Controller의 `robotPath=/World/Jetbot`, `jointNames=[left_wheel_joint, right_wheel_joint]`로 맞춥니다. 이름 배열에는 Construct Array를 사용할 수 있습니다. `jointIndices`, 위치·effort 명령은 비우세요.
6. Play하고 선회 방향을 확인한 뒤 `angularVelocity`만 0으로 바꿔 직진 명령을 비교하세요. 이 수동 그래프는 `drive.json`을 자동 저장하지 않습니다.

다른 로봇도 **구동 변환 노드의 데이터 출력과 관절 명령 종류**를 맞추는 원리는 같습니다.

| 구동 노드 | 입력과 데이터 연결 | 관절 선택 |
|---|---|---|
| Holonomic Controller | 코드의 바퀴 반지름·위치·방향·roller 각 배열을 각각 `wheelRadius`, `wheelPositions`, `wheelOrientations`, `mecanumAngles` 포트에 넣고 `inputVelocity=[0,0.3,0]`으로 설정; `jointVelocityCommand`를 velocityCommand로 연결 | `axle_0_joint`, `axle_1_joint`, `axle_2_joint` 순서 |
| Ackermann Controller | `wheelBase=1.65`, `trackWidth=1.25`, `frontWheelRadius=0.25`, `backWheelRadius=0.25`, `speed=1.1`, `steeringAngle=0.1`; `wheelAngles`는 positionCommand로, `wheelRotationVelocity`는 velocityCommand로 연결 | 조향용과 구동용 Articulation Controller를 따로 두고 2절 코드의 두 인덱스 집합에 해당하는 관절 이름 지정 |

Kaya는 Tick 실행을 Holonomic과 Articulation Controller 양쪽에 연결합니다. Ackermann은 Tick에서 Ackermann의 `execIn`으로, 해당 노드의 `execOut`에서 두 Articulation Controller로 연결할 수 있습니다. 각 그래프의 `robotPath`는 선택한 로봇의 실제 prim 경로로 바꾸세요.

## 3. 기구학 명령과 실제 주행의 관계 정리

```text
차체에 원하는 움직임
    → 바퀴 배치와 크기로 변환
    → 관절 위치·속도 목표
    → drive, 바닥 마찰, 접촉을 거친 실제 차체 pose
```

controller의 출력이 맞는지는 배열과 계산으로 확인합니다. 실제 주행은 차체 pose와 화면에서 확인합니다. 바퀴가 미끄러지거나 바닥 접촉이 안정되지 않으면 둘 사이에 차이가 생깁니다.

또한 이 프로그램은 고정 명령을 계속 보내는 실습입니다. 목적지에 가까워지면 감속하거나 오차를 되돌리는 내비게이션 기능은 없습니다. `--steps`가 길어지면 같은 입력으로 더 오래 주행합니다.

## 4. 간단한 확인 실험

1절의 Jetbot 명령에서 **`--turn`만 0.3에서 0으로** 바꿔 실행하세요.

이번에는 좌우 바퀴 목표가 모두 `0.3 / 0.03 = 10 rad/s`여야 합니다. 먼저 JSON에서 같은 값인지 확인하고 화면에서는 선회 대신 직진에 가까운 움직임을 관찰하세요. 명령이 같아도 접촉 조건 때문에 실제 경로가 완벽한 직선이 아닐 수 있습니다.

## 실행할 때 막히면

- **로봇이 보이지 않음**: 선택한 모드의 5.1 USD와 종속 mesh 경로가 접근 가능한지 확인하세요.
- **구동 controller 노드를 찾을 수 없음**: Extension Manager에서 `isaacsim.robot.wheeled_robots`를 활성화한 뒤 Action Graph 검색을 다시 확인하세요.
- **Kaya가 엉뚱한 방향으로 이동함**: 바퀴 이름 순서, 위치·quaternion 배열, roller 각도를 함께 확인하세요. quaternion 순서는 w, x, y, z입니다.
- **Leatherback이 꺾이기만 하거나 구동이 안 됨**: steering과 wheel 인덱스를 구분하고 각각의 position/velocity 모드를 유지하세요.
- **최종 위치가 시작점과 비슷함**: 회전 후 돌아왔을 수 있습니다. 방향과 실제 주행 화면을 함께 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Mobile Robot Controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html)에 대응합니다. 세 구동 구조의 고정 입력을 실제 자산에 전달하고 명령 배열과 차체 pose를 저장합니다.

`tutorial.json`은 `not_run` 상태입니다. 위 바퀴 수치는 공식 차동 구동 관계와 코드 입력으로 계산한 기대값입니다. 이번 개정에서 세 로봇의 실제 주행·속도 추종을 새로 측정하지 않았습니다.
