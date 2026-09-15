# 118. ROS 2 Ackermann Controller

권장 학습 순서 **118** · ROS 2 연결과 기본 통신 · 출처 ID `t020`

**목표:** Leatherback의 두 조향 관절과 네 바퀴 관절을 `AckermannDriveStamped` 메시지로 구동하고, `Twist`의 선속도/각속도를 조향각으로 바꿉니다. 로컬 `setup_stage.py`가 실제 그래프를 만들며 `drive.py`가 명령을 발행합니다. 차량 USD는 공식 5.1 asset을 사용합니다.

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


## 차량 준비와 그래프 생성

1. 터미널 B에 메시지와 키보드 도구가 없다면 `sudo apt install ros-humble-ackermann-msgs ros-humble-teleop-twist-keyboard`로 준비합니다. 이 패키지의 로컬 publisher/converter는 `isaac_tutorials`나 다른 로컬 튜토리얼을 필요로 하지 않습니다.
2. 터미널 A에서 GUI를 열고 새 Stage에 **Create > Environments > Flat Grid**를 추가합니다. Content Browser의 **Isaac Sim > ROBOTS > NVIDIA > Leatherback**에서 `leatherback.usd`를 끌어옵니다. 공식 경로는 `/Isaac/Robots/NVIDIA/Leatherback/leatherback.usd`이며 asset root는 5.1 서버/로컬 pack입니다.
3. Stage에서 차량 최상위 이름을 `Leatherback`으로 맞추고 Translate를 `(0,0,0)`으로 설정합니다. 로컬 `setup_stage.py`를 **Window > Script Editor**에서 열어 Run합니다. Script Editor 파일은 시스템 Python으로 실행하지 않습니다.
4. **Window > Graph Editors > Action Graph**에서 `/AckermannLab`을 엽니다. Ackermann Controller 입력을 확인합니다.

   | 입력 | 값/단위 |
   |---|---|
   | `frontWheelRadius`, `backWheelRadius` | 0.052 m |
   | `wheelBase` | 0.32 m (앞뒤 차축 간 거리) |
   | `trackWidth` | 0.24 m (좌우 바퀴 간 거리) |
   | `maxWheelRotation` | 0.7854 rad |
   | `maxWheelVelocity` | 20 rad/s |
   | `maxAcceleration` | 1 m/s² |
   | `maxSteeringAngleVelocity` | 1 rad/s |

5. `Steer`는 `Knuckle__Upright__Front_Left`, `Knuckle__Upright__Front_Right`의 **positionCommand**를 받습니다. `Wheels`는 **velocityCommand**를 받습니다. 설치된 5.1 OGN의 `wheelRotationVelocity` 출력 순서가 앞왼쪽→앞오른쪽→뒤왼쪽→뒤오른쪽이므로 로컬 코드는 jointNames도 그 순서로 맞춥니다. 원문의 후륜 우선 목록을 배열 순서 확인 없이 복사하지 않습니다.
6. Play 후 이 패키지 폴더의 터미널 B에서 실행합니다.

   ```bash
   python3 drive.py --mode drive --seconds 15 --speed 0.4 --steering 0.3
   ros2 topic echo /ackermann_cmd --once
   ```

   두 명령은 동시에 관찰할 별도 ROS 터미널에서 실행해도 됩니다. 차량이 완만하게 좌회전하고 종료 시 속도 0 명령이 나가야 합니다. Stage를 저장하려면 패키지 아래 새 USD 이름으로 Save As합니다.

## Twist에서 조향각으로

```bash
# 터미널 B: 60초 동안 변환기 실행
python3 drive.py --mode twist --seconds 60
# 다른 ROS 터미널
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

`i` 전진, `u` 전진 좌회전, `o` 전진 우회전, `,` 후진, `k` 정지로 움직입니다. 변환기는 `steering = atan(wheelBase * angular.z / linear.x)`를 사용합니다. `linear.x=0`에서는 제자리 회전이 불가능하므로 0 조향/속도를 냅니다. 입력이 0.5초 동안 없으면 정지합니다. 이 로컬 변환기의 모델/timeout은 학습용이며 공식 `cmdvel_to_ackermann` 구현을 복제했다고 주장하지 않습니다.

원문의 공식 publisher도 비교하려면 NVIDIA [IsaacSim-ros_workspaces 5.1.0](https://github.com/isaac-sim/IsaacSim-ros_workspaces/tree/IsaacSim-5.1.0)의 `humble_ws`를 별도 준비하고 시스템 ROS 터미널에서 `git submodule update --init --recursive`, `rosdep install -i --from-path src --rosdistro humble -y`, `colcon build`, `source install/local_setup.bash`를 수행합니다. 이후 `ros2 run isaac_tutorials ros2_ackermann_publisher.py` 또는 `ros2 launch cmdvel_to_ackermann cmdvel_to_ackermann.launch.py acceleration:=0.5 steering_velocity:=0.5`를 실행합니다. 로컬 publisher와 동시에 실행하지 않습니다. 공식 완성 장면은 Content Browser **Isaac Sim > Samples > ROS2 > Scenario > leatherback_ackermann**, 차량은 **Samples > ROS2 > Robots > Leatherback_ROS**입니다.

## API/Omniverse 해설과 성공 기준

AckermannDrive의 `steering_angle`은 두 앞바퀴 사이 가상의 중심 바퀴 각도입니다. Ackermann Controller가 좌우 조향각과 네 바퀴 회전 속도를 계산하고 Articulation Controller가 관절에 적용합니다. USD prim 경로 `/Leatherback`과 내부 jointNames는 ROS 토픽 이름 `ackermann_cmd`와 역할이 다릅니다. Tick→controller와 `deltaSeconds→dt`는 가속/조향 속도 제한을 각 스텝에 적용합니다. QoS Profile은 DDS 전달 규칙이며 차량 동역학과 별개입니다.

메시지 수신만으로 운전 성공이라 판단하지 마세요. 앞바퀴 조향, 네 바퀴 회전, 차량 위치 변화 모두 관찰합니다. 후속 실험은 `--steering`만 0.15로 바꿔 더 큰 회전 반경을 확인하는 것입니다. 차가 움직이지 않으면 Play, targetPrim, jointNames, articulation drive를 확인합니다. 크게 미끄러지면 속도를 낮추고 바퀴 순서/반지름을 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_ackermann_controller.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
