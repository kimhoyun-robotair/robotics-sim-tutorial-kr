# 105. 차체 속도 명령이 두 바퀴의 회전으로 바뀌는 과정

## 이번에 배우는 것

**ROS 2의 Twist 메시지로 TurtleBot을 움직이고, 전진·회전 명령이 좌우 바퀴 각속도로 변환되는 과정을 확인합니다.**

로봇에게 “왼쪽 바퀴를 몇 번 돌리세요”보다 “초당 0.2 m로 전진하세요”라고 명령하는 편이 자연스럽습니다. 두 바퀴로 움직이는 로봇에서는 차체의 선속도와 각속도를 각각의 바퀴 속도로 바꾸는 차동 구동 제어기가 필요합니다.

| 단계 | 이 실습의 데이터 | 단위 |
|---|---|---|
| ROS 입력 | `/cmd_vel`의 `linear.x`, `angular.z` | m/s, rad/s |
| 차동 구동 변환 | `DifferentialController` | 바퀴 각속도 rad/s |
| 관절 명령 | 왼쪽·오른쪽 wheel joint | rad/s |
| 물리 결과 | 콘솔 `position_m`와 화면 | 위치 m와 차체 방향 |

`run.py`는 수신 그래프를 만들지만 주행 명령을 자체 생성하지 않습니다. 명령은 별도 ROS 터미널에서 보냅니다.

## 1. 두 터미널에서 로봇과 명령 준비하기

기본 환경은 Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1과 지원 NVIDIA RTX GPU입니다. Ubuntu 22.04에서는 아래 `jazzy`를 `humble`로 바꿉니다. 두 프로세스가 같은 컴퓨터에서 통신하는 실습입니다.

**터미널 A**는 시스템 ROS를 source하지 않은 새 터미널로 준비합니다. 저장소 루트에서 Isaac Sim 내부 ROS 라이브러리를 지정하고 실행하세요. 라이브러리 경로 설정은 이 터미널에서 한 번만 합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib"
"$ISAAC_SIM/python.sh" src/105_ros2_ros2_drive_turtlebot/run.py
```

기본 TurtleBot USD는 `Isaac/Robots/Turtlebot/Turtlebot3/turtlebot3_burger.usd`입니다. 공식 자산에 접근할 수 있어야 합니다. 준비한 로컬 USD를 쓰려면 `--robot-usd /절대/경로/turtlebot.usd`를 추가합니다. 그 로봇에도 같은 두 바퀴 관절 이름이 필요합니다.

**터미널 B**는 시스템 ROS를 사용하는 Bash 터미널입니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic info /cmd_vel -v
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: 0.0}}'
```

`ROS_DOMAIN_ID`는 통신 그룹 번호입니다. A와 B가 같아야 합니다. 외부 ROS의 Python 환경을 Isaac Sim에 섞지 않아도 두 프로세스는 DDS 메시지로 통신합니다.

### 실행 결과 확인하기

A의 콘솔에서 `actual_joint_names`에 `wheel_left_joint`, `wheel_right_joint`가 있는지 먼저 봅니다. 전진 명령 뒤에는 다음 두 관찰을 연결합니다.

- `wheel_commands_rad_s`의 두 값이 약 8 rad/s로 같아집니다.
- `position_m`과 화면에서 차체 위치가 변합니다.

명령 발행을 Ctrl+C로 끝낸 뒤 **반드시 0 속도 메시지를 따로 보내** 정지 반응도 확인하세요.

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

이 그래프는 송신이 끊겼을 때 자동 정지시키는 시간 감시 기능이 없습니다. 새 메시지가 없으면 마지막 명령을 유지합니다.

GUI 실행은 창을 닫으면 종료합니다. `--steps 1200`처럼 한도를 지정할 수 있고, `--headless`만 쓰면 기본 3600단계에서 끝납니다.

## 2. Twist에서 관절 명령까지 그래프 따라가기

A의 실행 창에서 **Window > Graph Editors > Action Graph**를 열고 `/DriveGraph`를 선택하세요.

```text
ROS2 Subscribe Twist
    ├─ linearVelocity → BreakVector3.x ─┐
    └─ angularVelocity → BreakVector3.z ┤
                               DifferentialController
                                        ↓ velocityCommand
                               ArticulationController
                                        ↓
                              왼쪽·오른쪽 바퀴 관절
```

### 코드에서 볼 부분

제어기에 들어가는 실제 설정은 다음과 같습니다.

| 설정 | 값 | 의미 |
|---|---|---|
| `wheelRadius` | `0.025` m | 명령 변환에 사용할 바퀴 반지름 |
| `wheelDistance` | `0.16` m | 좌우 바퀴 사이 거리 |
| `maxLinearSpeed` | `0.22` m/s | 차체 선속도 제한 |
| `maxAngularSpeed` | `1.0` rad/s | 차체 회전 속도 제한 |
| `jointNames` | `[wheel_left_joint, wheel_right_joint]` | 속도 배열을 적용할 순서 |

이 값들은 현재 코드의 제어기 설정입니다. 다른 TurtleBot 모델이나 직접 가져온 USD를 쓰면 실제 치수도 일치하는지 확인해야 합니다. 예를 들어 104번에서 사용하는 [Jazzy Burger URDF](https://raw.githubusercontent.com/ROBOTIS-GIT/turtlebot3/jazzy/turtlebot3_description/urdf/turtlebot3_burger.urdf)의 바퀴 충돌 반지름은 0.033 m로, 여기의 0.025 m와 다릅니다. 그 USD를 `--robot-usd`로 넣었다면 바퀴 명령 8 rad/s가 계산되는 것과 차체가 실제로 0.2 m/s로 가는 것을 같은 결과로 보지 마세요. 치수를 맞추려면 제어기 설정도 별도로 조정해야 합니다.

Tick 연결은 **언제 실행할지**, 숫자 데이터 연결은 **어떤 값을 전달할지**를 정합니다. 여기서는 Tick이 수신기뿐 아니라 Differential과 Actuator에도 연결되어 마지막 명령을 매 재생 tick에 적용합니다.

코드는 로봇 아래 기존 Articulation Root API를 찾아 제거한 뒤 `/World/turtlebot3_burger`에 하나를 둡니다. 그 경로를 `robotPath`에 사용합니다. 이는 현재 Stage에서 하는 수정이며 외부 원본 USD 파일을 덮어쓰는 작업이 아닙니다.

같은 그래프를 GUI로 직접 구성하려면 독립 실행을 종료하고 A의 같은 환경에서 `"$ISAAC_SIM/isaac-sim.sh"`로 새 앱을 엽니다. **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화하고 거리 단위가 1 m인 새 Stage에 같은 TurtleBot USD를 `/World/turtlebot3_burger`로 추가하세요. **Create > Physics**에서 Ground Plane과 Physics Scene을, **Create > Light**에서 조명을 추가합니다.

직접 가져온 로봇의 `/base_footprint` 등에 Articulation Root가 이미 있다면 해당 Prim의 Property에서 **Physics > Articulation Root**를 제거하고 부모 `/World/turtlebot3_burger`에 추가하세요. 하나의 로봇에 Root를 중복해서 두지 않습니다. 준비가 끝나면 **Window > Graph Editors > Action Graph > New Action Graph**에서 다음 순서로 연결합니다.

1. On Playback Tick, ROS2 Context, ROS2 Subscribe Twist, Break Vector3 두 개, Differential Controller, Articulation Controller를 추가합니다.
2. Tick을 수신기·차동 제어기·관절 제어기의 `execIn`에 연결하고, Context 출력을 수신기의 `context`에 연결합니다. Context의 `useDomainIDEnvVar`를 켜서 A에 설정한 domain을 사용합니다.
3. Twist의 `linearVelocity`·`angularVelocity`를 각각 Break Vector3의 `tuple`에 연결합니다. 선속도의 `x`, 각속도의 `z`를 차동 제어기의 입력으로 사용하세요.
4. `velocityCommand`를 관절 제어기로 연결하고 위 표의 치수·제한·로봇 경로·관절 이름을 입력합니다. 이름 배열을 노드로 만들 때는 Constant Token 두 개와 Make Array를 사용합니다. Constant String 배열은 필요한 token 배열과 타입이 다릅니다.
5. 수신 토픽을 `/cmd_vel`로 맞추고 Play한 뒤 터미널 B에서 같은 명령을 보냅니다. 이 장면은 1 m 단위이므로 선속도를 그대로 쓰며, 다른 거리 단위에서는 Scale To/From Stage Unit 변환도 필요합니다.

### 실행 결과 확인하기

제자리 회전을 확인하려면 전진 송신을 끝내고 다음 명령을 보냅니다.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.0}, angular: {z: 0.5}}'
```

좌우 명령이 반대 부호가 되고 차체 방향이 바뀌는지 보세요. 콘솔의 위치만으로는 제자리 회전 각도를 읽을 수 없으므로 화면의 방향도 확인합니다. 접지 과도응답 때문에 위치가 완전히 한 점에 고정될 필요는 없습니다. 관찰 후 송신을 끝내고 앞의 0 속도 명령을 보냅니다.

## 3. 차체 속도와 바퀴 속도의 관계 정리

차체 선속도를 `v`, 각속도를 `ω`, 바퀴 간 거리를 `L`, 반지름을 `r`이라 하면 다음과 같습니다.

```text
왼쪽 바퀴 각속도  = (v - ωL/2) / r
오른쪽 바퀴 각속도 = (v + ωL/2) / r
```

`v=0.2`, `ω=0`이면 `0.2/0.025=8` rad/s로 두 바퀴가 같습니다. `v=0`, `ω=0.5`이면 왼쪽 -1.6, 오른쪽 +1.6 rad/s입니다. 서로 다른 두 관찰을 같은 계산으로 설명할 수 있습니다.

물리·렌더 간격은 1/60초, 콘솔 출력은 120단계마다입니다. 이 로그 간격을 `/cmd_vel`의 10 Hz 송신률이나 제어 빈도로 해석하지 마세요.

## 4. 간단한 확인 실험

전진 명령의 `linear.x=0.2`는 유지하고 **`angular.z`만 0에서 0.5로** 바꿔 보세요.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: 0.5}}'
```

코드의 치수로 계산하면 왼쪽 약 6.4, 오른쪽 약 9.6 rad/s입니다. 양쪽 모두 앞으로 돌되 오른쪽이 더 빨라 곡선으로 이동해야 합니다. 제자리 회전과 달리 차체 위치도 계속 변합니다. 실험 뒤 0 속도를 보내세요.

## 실행할 때 막히면

- **`/cmd_vel` 구독자가 없음**: Bridge 로딩, A/B의 domain과 RMW 설정을 확인하세요. 시스템 ROS와 내부 ROS 환경이 섞였다면 A를 새로 준비합니다.
- **바퀴 명령은 나오지만 몸체가 움직이지 않음**: 실제 관절 이름, 이동 가능한 base, 바퀴 접지와 drive를 확인하세요.
- **로봇 자산 로딩 오류**: 공식 자산 접근 또는 `--robot-usd` 경로부터 확인합니다. 자산 실패와 ROS 수신 실패는 별도 문제입니다.
- **Ctrl+C 후에도 계속 주행함**: 마지막 명령을 유지하는 구조입니다. 두 속도가 0인 메시지를 보내세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)에 대응합니다. 공식 GUI 그래프를 Python으로 구성하고, 주행 확인을 쉽게 하려고 Simple Room 대신 평평한 바닥을 사용합니다. 환경 분리는 [5.1 ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

바퀴 명령과 실제 차체 이동, 0 명령 후 정지를 각각 확인하세요. `tutorial.json`의 검증 상태는 `not_run`이며 GPU 주행·외부 ROS 통합 성공을 기록한 자료는 없습니다.
