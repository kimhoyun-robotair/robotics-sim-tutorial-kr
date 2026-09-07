# 1. 빌드하고 키보드로 움직이기

이 단계에서는 센서나 Nav2 설정을 수정하지 않습니다. 제공된 패키지를 빌드한 뒤,
Gazebo에서 로봇이 만들어지고 ROS 명령으로 움직이는지 먼저 확인합니다.

## 1-1. 설치 환경 확인

Ubuntu 24.04에서 [앞 장의 설치 과정](../02_getting-started/02_installation-jazzy.md)을 완료한 상태로 시작합니다.
터미널을 열고 다음을 실행하세요.

```bash
source /opt/ros/jazzy/setup.bash
printenv ROS_DISTRO
gz sim --versions
```

첫 번째 출력은 `jazzy`, Gazebo Sim의 주 버전은 `8`이어야 합니다.
Harmonic은 Gazebo Sim 8을 사용하는 배포판입니다. ROS 패키지는 Jazzy용 `ros_gz`를 사용합니다.
[공식 ROS/Gazebo 호환표](https://gazebosim.org/docs/harmonic/ros_installation/)에서 조합을 확인할 수 있습니다.

필요한 도구를 설치합니다. `sudo` 명령은 관리자 암호를 물어볼 수 있습니다.

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-gz ros-jazzy-xacro ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-teleop-twist-keyboard ros-jazzy-teleop-twist-joy ros-jazzy-joy \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox \
  python3-colcon-common-extensions python3-rosdep
```

센서 QoS와 점군의 frame 보정을 위해 `ros_gz_bridge` **1.0.22 이상**이 필요합니다.
아래 명령으로 버전을 확인하고, 오래된 버전이면 업데이트하세요.

```bash
dpkg-query -W -f='${Version}\n' ros-jazzy-ros-gz-bridge
sudo apt install --only-upgrade ros-jazzy-ros-gz-bridge
```

`1.0.22`보다 낮은 버전만 제공된다면 ROS apt 저장소 설정부터 확인합니다.
버전 조건은 각 패키지의 `package.xml`에도 명시했습니다.

## 1-2. Jazzy 브랜치와 작업 폴더 확인

아직 저장소를 내려받지 않았다면 다음 명령으로 **Jazzy만** 가져옵니다.
이미 이 저장소의 Jazzy 브랜치에서 실습 중이라면 clone 명령은 생략하세요.

```bash
cd ~
git clone --branch Jazzy --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd ~/robotics-sim-tutorial-kr
git branch --show-current
```

출력이 `Jazzy`인지 확인합니다. 이후 명령은 저장소를 `~/robotics-sim-tutorial-kr`에 둔 경우입니다.
다른 폴더에 받았다면 `cd` 경로만 실제 위치에 맞추세요.

```bash
cd ~/robotics-sim-tutorial-kr/examples/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --symlink-install --packages-up-to simple_rover f1tenth_sim nav2_programming
source install/setup.bash
ros2 pkg prefix simple_rover
ros2 pkg prefix f1tenth_sim
ros2 pkg executables nav2_programming
```

`rosdep`이 초기화되지 않았다는 오류가 나면 `sudo rosdep init`을 **최초 한 번** 실행한 뒤
`rosdep update`부터 다시 진행합니다. 빌드에 실패했다면 마지막 오류부터 해결하고 다음 단계로 넘어가세요.
`ros2 pkg prefix`에는 현재 워크스페이스의 `install` 경로가 나와야 합니다.

## 1-3. 로봇 띄우기

첫 번째 터미널에서 다음을 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/robotics-sim-tutorial-kr/examples/ros2_ws/install/setup.bash
ros2 launch simple_rover spawn_robot.launch.py
```

벽과 상자가 있는 `rover_arena` 월드, 초록색 바퀴의 로봇, RViz가 열립니다.
이 월드는 기본 도형으로 구성되어 있어 Fuel 모델을 따로 내려받지 않습니다.
처음 로봇을 만드는 동안 RViz에 TF 경고가 잠깐 보일 수 있습니다. `/clock`과 `/odom`이 들어온 뒤 사라지는지 확인하세요.

두 번째 터미널을 열어 ROS 환경을 다시 읽고 시뮬레이션 상태를 확인합니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/robotics-sim-tutorial-kr/examples/ros2_ws/install/setup.bash
ros2 topic echo /clock --once
ros2 topic echo /odom --once --field header
ros2 run tf2_ros tf2_echo odom base_link
```

`/clock`의 시간이 흐르고 `odom → base_link` 변환이 나오면 로봇과 bridge가 연결된 것입니다.
`tf2_echo`는 계속 실행되는 명령이므로 확인 후 `Ctrl+C`로 종료합니다.

## 1-4. 키보드로 이동하고 멈추기

두 번째 터미널에서 키보드 조종 노드를 실행합니다.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p speed:=0.2 -p turn:=0.4 -p stamped:=false
```

이 터미널을 클릭한 상태에서 `i`를 누르면 전진하고, `j`/`l`은 제자리 회전,
`k`는 정지입니다. Gazebo 창에 키보드 포커스가 가 있으면 명령이 전달되지 않습니다.
먼저 짧게 전진한 뒤 `k`로 멈추세요. 종료하기 전에도 `k`를 누릅니다.

명령 흐름을 직접 보고 싶다면 세 번째 터미널에서 환경을 읽고 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/robotics-sim-tutorial-kr/examples/ros2_ws/install/setup.bash
ros2 topic echo /cmd_vel
```

`linear.x`는 전후 속도(m/s), `angular.z`는 회전 속도(rad/s)입니다.
이 프로젝트의 bridge는 `geometry_msgs/msg/Twist`를 사용합니다.
`TwistStamped`를 같은 토픽에 발행하면 연결되지 않습니다.

키보드 없이 한 번씩 명령을 보내는 방법도 있습니다. 이 경우 구동 플러그인이 마지막 명령을 유지할 수 있으므로
반드시 정지 명령까지 실행하세요.

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.15}, angular: {z: 0.0}}'
# 원하는 만큼 짧게 움직인 뒤 아래 명령으로 정지
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

## 1-5. 실행 옵션

| 목적 | 명령/인자 | 의미 |
|---|---|---|
| RViz만 생략 | `rviz:=false` | Gazebo GUI는 유지 |
| Gazebo GUI 생략 | `gui:=false rviz:=false` | 서버와 센서 계산은 유지 |
| 화면 없는 EGL 렌더링 | `gui:=false rviz:=false headless:=true` | 지원되는 GPU/EGL 환경 필요 |
| 조이스틱 사용 | `joy:=true` | 기본값은 꺼짐; 버튼/축은 `config/MXswitch.config.yaml` 참고 |
| RGB 카메라만 사용 | `camera:=rgb` | 깊이 영상과 RGB-D 점군은 발행하지 않음 |
| 카메라 생략 | `camera:=none` | 라이다·IMU는 유지 |
| 시작 위치 변경 | `x:=1.0 y:=0.0 yaw:=0.0` | 단위는 m, m, rad |

예를 들어 카메라를 끄고 RViz 없이 실행하려면 기존 launch를 종료한 뒤 다음을 실행합니다.

```bash
ros2 launch simple_rover spawn_robot.launch.py camera:=none rviz:=false
```

GPU 라이다와 RGB-D 센서는 렌더링을 사용합니다. `gui:=false`는 GUI를 끄는 옵션이며,
센서에 필요한 렌더링 기능까지 없애는 옵션은 아닙니다.
[Harmonic의 headless 렌더링 설명](https://gazebosim.org/api/sim/8/headless_rendering.html)을 참고하세요.

## 확인 후 다음 단계로

로봇이 움직이는데 RViz의 바퀴가 고정되어 있다면 `/joint_states`부터 확인합니다.
로봇 자체가 없다면 `ros2 topic echo /robot_description --once --qos-durability transient_local`로
URDF가 발행되는지 확인하세요. 환경을 읽지 않은 터미널에서 생긴 `Package not found`는
`source .../install/setup.bash` 후 다시 실행하면 됩니다.

이제 [센서와 RViz 확인](02_sensors-and-rviz.md)으로 넘어갑니다.
