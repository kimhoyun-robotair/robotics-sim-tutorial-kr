# 118. 차체의 조향 명령을 네 바퀴 운동으로 바꾸기

## 이번에 배우는 것

**Leatherback에 Ackermann 명령을 보내고, 중심 조향각 하나가 좌우 앞바퀴의 서로 다른 각도로 바뀌는 과정을 확인합니다.**

자동차가 커브를 돌 때 안쪽 바퀴와 바깥쪽 바퀴는 서로 다른 반경을 따라갑니다. 두 바퀴를 똑같이 꺾으면 바퀴가 향하는 방향과 이동 방향이 어긋날 수 있습니다. Ackermann Controller는 차체 치수와 중심 조향각을 사용해 각 바퀴의 조향각·회전 속도를 계산합니다.

| 구성 | 입력 또는 역할 |
|---|---|
| `setup_stage.py` | 이미 배치한 Leatherback에 제어 그래프 추가 |
| `drive.py --mode drive` | 고정 속도·조향각을 반복 발행 |
| `drive.py --mode twist` | Twist의 선속도·각속도를 Ackermann으로 변환 |
| Steer 제어기 | 앞바퀴 두 조향 관절의 위치 제어 |
| Wheels 제어기 | 네 바퀴 관절의 속도 제어 |

그래프만 생성해서는 차량이나 바닥이 생기지 않습니다. 먼저 실제 차량 자산을 준비합니다.

## 1. Leatherback과 제어 그래프 준비하기

Isaac Sim 5.1, 지원 GPU, Ubuntu 24.04의 ROS 2 Jazzy, `ackermann_msgs`가 필요합니다. 아래는 저장소 루트의 Bash 명령입니다. Ubuntu 22.04/Humble에서는 `jazzy` 값과 경로·패키지 이름을 `humble`로 바꾸세요.

터미널 A는 시스템 ROS를 source하지 않은 새 셸입니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

설치 위치가 다르면 `ISAAC_SIM`을 바꾸세요. 터미널 B에서는 시스템 ROS를 준비합니다. Ackermann 메시지 패키지가 없을 때만 아래 설치 명령을 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 interface show ackermann_msgs/msg/AckermannDriveStamped
# 메시지 패키지가 없을 때
sudo apt install ros-jazzy-ackermann-msgs
```

1. Isaac Sim에서 **File > New**로 빈 장면을 열고 **Create > Environments > Flat Grid**를 추가합니다.
2. Content Browser에서 **Isaac Sim > ROBOTS > NVIDIA > Leatherback**의 `leatherback.usd`를 가져옵니다. 공식 자산 경로는 `Isaac/Robots/NVIDIA/Leatherback/leatherback.usd`입니다.
3. 차량을 Stage의 **`/Leatherback`**에 놓고 Translate를 `(0,0,0)`으로 맞춥니다. 자산 서버 또는 로컬 5.1 asset pack에 접근할 수 있어야 합니다.
4. Stop 상태에서 **Window > Script Editor**에 `src/118_ros2_ros2_ackermann_controller/setup_stage.py` 전체를 붙여 넣고 실행합니다.
5. `Ackermann graph ready`가 출력되면 `/AckermannLab`을 확인하고 Play합니다.

### 설정에서 볼 부분

| Ackermann 입력 | 값 | 계산에서 쓰는 의미 |
|---|---|---|
| `wheelBase` | 0.32 m | 앞·뒤 차축 사이 거리 |
| `trackWidth` | 0.24 m | 좌·우 바퀴 사이 거리 |
| `frontWheelRadius`, `backWheelRadius` | 0.052 m | 이동 속도를 바퀴 각속도로 변환 |
| `maxWheelRotation` | 0.7854 rad | 조향 한도 |
| `maxWheelVelocity` | 20 rad/s | 바퀴 각속도 한도 |
| `maxAcceleration` | 1 m/s² | 가속도 한도 |
| `maxSteeringAngleVelocity` | 1 rad/s | 조향각 변화율 한도 |

차체 속도의 단위 m/s와 바퀴 회전 속도의 rad/s를 구분하세요. 직진 근사에서는 속도 0.4 m/s를 반지름 0.052 m로 나누어 약 7.69 rad/s를 얻습니다.

### 실행 결과 확인하기

터미널 B에서 실행합니다.

```bash
python3 src/118_ros2_ros2_ackermann_controller/drive.py --mode drive --seconds 15 --speed 0.4 --steering 0.3
```

동일한 ROS 환경의 다른 터미널에서는 실행 중 메시지를 읽습니다.

```bash
ros2 topic echo /ackermann_cmd --once
```

`drive.speed=0.4`, `drive.steering_angle=0.3`, `header.frame_id=base_link`를 확인하세요. 타이머는 0.05초 간격으로 발행하도록 설정되어 있습니다. Viewport에서는 앞바퀴가 조향되고 네 바퀴가 회전하며 차체가 좌회전하는지 함께 관찰합니다. 정상 종료 시 송신기는 0 속도·0 조향 명령을 마지막으로 보냅니다.

## 2. 조향·구동 배열과 Twist 변환 읽기

### 코드에서 볼 부분

```text
AckermannDriveStamped
    → Subscribe
    → Ackermann Controller
        ├─ wheelAngles → Steer.positionCommand
        └─ wheelRotationVelocity → Wheels.velocityCommand
```

Steer의 관절 순서는 왼쪽·오른쪽입니다. Wheels는 **앞왼쪽 → 앞오른쪽 → 뒤왼쪽 → 뒤오른쪽**으로 연결합니다. 설치된 5.1 노드의 출력 순서에 맞춘 것입니다.

```text
Knuckle__Upright__Front_Left, Knuckle__Upright__Front_Right

Wheel__Knuckle__Front_Left, Wheel__Knuckle__Front_Right,
Wheel__Upright__Rear_Left, Wheel__Upright__Rear_Right
```

배열 값이 올바르더라도 관절 이름 순서가 다르면 다른 바퀴에 적용됩니다. `/AckermannLab`에서 두 출력 배열과 각 제어기의 `jointNames`를 같이 읽으세요. `Tick.deltaSeconds → Ackermann.dt`는 가속·조향 변화율 제한에 사용할 시간 간격을 제공합니다. 송신 메시지의 가속도와 조향 변화율은 각각 0.5이며 그래프의 최대 한도 안에서 적용됩니다.

### Twist를 받아 보기

고정 명령 송신기를 종료하고 터미널 B에서 변환기를 실행합니다.

```bash
python3 src/118_ros2_ros2_ackermann_controller/drive.py --mode twist --seconds 60
```

다른 ROS 터미널에서 전진·회전 Twist를 지속 발행합니다.

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.4}, angular: {z: 0.3}}"
```

변환기의 핵심은 다음 식입니다.

```python
steering = math.atan(args.wheel_base * yaw_rate / speed) if abs(speed)>1e-6 else 0.0
```

차축 간 거리 0.32 m, 속도 0.4 m/s, 각속도 0.3 rad/s이면 조향각은 `atan(0.24)`, 약 0.236 rad입니다. `/ackermann_cmd`에서 변환된 값을 확인하세요. `linear.x=0`에서는 조향각도 0으로 처리하므로 각속도만 보내도 제자리 회전하지 않습니다.

Twist 발행을 Ctrl+C로 끝내고 변환기는 유지해 보세요. 마지막 입력 후 기본 0.5초가 지나면 변환기가 0 명령을 보내는지 확인합니다. 키보드로 입력하려면 `teleop_twist_keyboard`를 별도 설치해 같은 `/cmd_vel`에 발행할 수 있습니다.

### 실행 결과 확인하기

메시지가 0이 되었다고 차체 속도가 같은 순간 정확히 0이 될 필요는 없습니다. 제어기의 가속 제한과 물리 상태를 따라 감속합니다. **0 명령 수신, 바퀴 감속, 차체 정지**를 순서대로 관찰하세요. 마지막 0 메시지의 DDS 수신까지 보장하는 확인 코드는 없으므로 실제 장면을 확인하고 실습을 마칩니다.

### 공식 ROS 패키지와 비교하기

원문의 `isaac_tutorials` 송신기와 `cmdvel_to_ackermann`을 비교하려면 로컬 `drive.py`를 먼저 종료하세요. 이들은 별도의 [IsaacSim-5.1.0 ROS 워크스페이스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/tree/IsaacSim-5.1.0)에 있습니다. 시스템 Jazzy와 `rosdep`, `colcon`이 준비된 터미널 B에서 아래처럼 별도 작업 폴더를 만들고 빌드합니다. 경로가 이미 있다면 기존 체크아웃의 버전·빌드 상태를 확인하세요.

```bash
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$HOME/isaac_ros_workspaces_51"
cd "$HOME/isaac_ros_workspaces_51/jazzy_ws"
rosdep install -i --from-paths src --rosdistro jazzy -y
colcon build
source install/local_setup.bash
```

`rosdep` 초기 설정과 배포판별 의존성은 [5.1 워크스페이스 준비](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html#setting-up-workspaces)를 따릅니다. 이 시스템 ROS 워크스페이스는 터미널 B에서 source하고 Isaac Sim용 터미널 A에는 섞지 않습니다.

Play 상태의 차량에서 `ros2 run isaac_tutorials ros2_ackermann_publisher.py`로 공식 고정 명령을 확인할 수 있습니다. 이 송신기를 종료한 뒤 `ros2 launch cmdvel_to_ackermann cmdvel_to_ackermann.launch.py acceleration:=0.5 steering_velocity:=0.5`를 실행하고 별도 ROS 터미널에서 Twist를 보내면 공식 변환 경로를 비교합니다. 로컬 변환기의 `--timeout 0.5`가 이 외부 패키지에도 적용된다고 가정하지 마세요.

완성된 차량과 경주 트랙은 Content Browser의 **Isaac Sim > Sample > ROS2 > Scenario > leatherback_ackermann**에 있고, 그래프가 붙은 차량은 **Sample > ROS2 > Robots > Leatherback_ROS**에 있습니다. 둘 중 하나를 새 장면으로 열어 실제 관절·제어 그래프를 로컬 `/AckermannLab`과 비교할 수 있습니다.

## 3. 중심 조향각과 회전 반경 정리

단순 자전거 모델에서는 차축 간 거리 L과 중심 조향각 δ에 대해 `R=L/tan(δ)`로 회전 반경을 설명할 수 있습니다. L=0.32 m일 때 δ=0.3 rad이면 약 1.03 m, δ=0.15 rad이면 약 2.12 m입니다.

이는 미끄럼이 없고 조향이 목표에 도달한 상태의 기하적 근사입니다. 실제 궤적에는 가속·조향 전환·접촉이 영향을 줍니다. 그래도 같은 속도에서 조향각이 작아지면 회전 반경이 커진다는 경향을 예상할 수 있습니다.

## 4. 간단한 확인 실험

고정 명령 모드에서 **`--steering`만 0.3에서 0.15로 바꿔 보세요.** 같은 시작 자세에서 비교하려면 Stop으로 장면을 초기화한 뒤 Play합니다.

```bash
python3 src/118_ros2_ros2_ackermann_controller/drive.py --mode drive --seconds 15 --speed 0.4 --steering 0.15
```

앞바퀴 각도가 작아지고 궤적이 더 완만한 곡선이 되는지 확인하세요. 속도나 차축 간 거리를 동시에 바꾸지 않아야 조향각의 영향을 분리할 수 있습니다.

## 실행할 때 막히면

- **`Load the Leatherback USD at /Leatherback` 오류**: 차량이 `/World/Leatherback` 등에 놓였는지 확인하세요. 현재 스크립트는 정확히 `/Leatherback`을 요구합니다.
- **`/AckermannLab exists` 오류**: 그래프를 중복 생성하지 않도록 중단한 것입니다. 기존 그래프를 확인하거나 새 실습 Stage를 준비하세요.
- **메시지는 오지만 차체가 안 움직임**: Play, 두 제어기의 대상, 관절 순서, 바닥 접촉과 drive 설정을 확인합니다.
- **Twist 제어가 잠깐 움직인 뒤 멈춤**: 0.5초 입력 timeout을 확인하세요. 지속 주행하려면 위처럼 주기적으로 Twist를 보냅니다.
- **바퀴가 이상하게 미끄러짐**: 차량 치수·관절 순서를 확인하고 낮은 속도로 비교하세요. 토픽 이름만 맞는다고 바퀴 배열까지 맞는 것은 아닙니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS 2 Ackermann Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_ackermann_controller.html)에 대응하며, 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 Leatherback 자산에 로컬 그래프와 송신기·Twist 변환기를 연결합니다. 외부 `cmdvel_to_ackermann` 패키지를 실행하는 구성과는 구현이 다릅니다. 바퀴 출력 순서는 설치된 5.1 Ackermann 노드 스키마와 대조했습니다. `tutorial.json`은 `verification: not_run`이며 실제 주행·정지·DDS 수신은 이번 개정에서 실측하지 않았습니다.
