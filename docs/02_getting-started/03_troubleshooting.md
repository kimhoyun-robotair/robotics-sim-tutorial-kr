# 시작 단계 문제 해결

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [Jazzy 환경 설치](02_installation-jazzy.md)

오류를 한꺼번에 고치려 하면 SDF, Gazebo 서버, 렌더링, 브리지, ROS 2 작업 공간 환경 가운데 원인을 찾기 어렵다. 이 장에서는 환경 → 정적 파일 → Gazebo Transport → ROS 2 브리지 → TF·컨트롤러 순서로 진단 범위를 줄여나간다.

## 먼저 실행 환경을 확인한다

각 절은 해당 증상이 생겼을 때 선택해 따라 한다. `examples/...` 같은 상대 경로를 사용하는 명령은 `cd ~/robotics-sim-tutorial-kr`로 저장소 루트에 이동한 뒤 실행한다. `gz topic -e`와 `tf2_echo`는 계속 출력되므로 확인 후 `Ctrl+C`를 누른다.

문제가 발생한 터미널에서 다음 출력을 기록한다.

```bash
date -Is
. /etc/os-release
printf 'OS=%s %s ARCH=%s\n' "$VERSION_ID" "$VERSION_CODENAME" "$(dpkg --print-architecture)"
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-unset}"
printf 'RMW_IMPLEMENTATION=%s\n' "${RMW_IMPLEMENTATION:-default}"
printf 'GZ_PARTITION=%s\n' "${GZ_PARTITION:-default}"
type -a ros2 || true
type -a gz || true
gz sim --versions
```

본편 기준은 Ubuntu 24.04 Noble, amd64, `ROS_DISTRO=jazzy`, Gazebo Sim 8 계열이다.

## `ros2` 명령을 찾지 못한다

현재 셸에 Jazzy 기본 ROS 환경을 불러오지 않았거나 Jazzy가 설치되지 않은 상태이다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    command -v ros2
    printenv ROS_DISTRO
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    command -v ros2
    printenv ROS_DISTRO
    ```

`/opt/ros/jazzy/setup.*` 자체가 없다면 패키지 상태를 확인한다.

```bash
apt-cache policy ros-jazzy-desktop
dpkg-query -W ros-jazzy-desktop
```

## `gz` 또는 `ros_gz`를 찾지 못한다

Gazebo 실행 파일과 ROS 연동 패키지를 따로 확인한다.

```bash
command -v gz
apt-cache policy ros-jazzy-ros-gz
dpkg-query -W ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
```

패키지가 없다면 Jazzy apt 저장소가 활성화되었는지 확인한 뒤 다시 설치한다.

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control
```

## 다른 ROS 또는 Gazebo 설치가 섞인다

여러 기본 ROS 환경이나 소스 빌드가 앞에 있으면 플러그인 ABI와 Python 패키지가 서로 다른 경로에서 로드될 수 있다.

```bash
type -a ros2
type -a gz
printf '%s\n' "${AMENT_PREFIX_PATH:-unset}" | tr ':' '\n'
printf '%s\n' "${CMAKE_PREFIX_PATH:-unset}" | tr ':' '\n'
printf '%s\n' "${GZ_SIM_SYSTEM_PLUGIN_PATH:-unset}" | tr ':' '\n'
```

새 터미널을 열고 `/opt/ros/jazzy/setup.bash`만 불러온 상태에서 문제가 재현되는지 확인한다. 이후 실습 작업 공간 환경을 마지막에 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

## SDF 또는 Xacro 문법 오류가 발생한다

GUI를 실행하기 전에 파일 문법부터 확인한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

SDF 오류의 줄과 열을 먼저 고친다. XML에서는 닫는 태그, 따옴표, 태그 중첩이 흔한 원인이다. 예를 들어 플러그인 파라미터는 플러그인 요소 안에 있어야 한다.

```xml
<!-- 올바른 구조이다. -->
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
</plugin>
```

Xacro 오류라면 생성된 URDF가 아니라 `.urdf.xacro` 원본을 수정한다. `xacro` 명령이 실패하면 `/tmp/tutorial_bot.urdf`는 불완전할 수 있으므로 로봇 생성 명령을 실행하지 않는다.

## 서버와 GUI 가운데 어디에서 실패하는지 확인한다

자세한 로그를 켜고 서버 전용으로 실행한다.

```bash
gz sim -v 4 -s -r examples/gazebo/worlds/first-world.sdf
```

서버가 계속 실행되고 다른 터미널의 `gz topic -l`에 `/clock`이 보이면 물리와 Transport는 동작한다.

```bash
gz topic -l | sort
gz topic -e -t /clock
```

이 상태에서 GUI만 별도로 연결한다.

```bash
gz sim -g
```

서버는 동작하지만 GUI만 실패하면 디스플레이 또는 렌더링 문제로 범위를 좁힐 수 있다.

## GUI가 열리지 않거나 검은 화면이 나온다

화면 연결 상태와 OpenGL 렌더러를 확인한다. `glxinfo`가 없다면 `mesa-utils`를 설치한다.

```bash
printf 'SESSION=%s DISPLAY=%s WAYLAND=%s\n' \
  "${XDG_SESSION_TYPE:-unset}" "${DISPLAY:-unset}" "${WAYLAND_DISPLAY:-unset}"
sudo apt install -y mesa-utils
glxinfo -B
```

하드웨어 가속 경로의 문제인지 확인할 때만 소프트웨어 렌더링으로 비교 실행한다.

```bash
LIBGL_ALWAYS_SOFTWARE=1 gz sim -r examples/gazebo/worlds/first-world.sdf
```

원격 셸이나 디스플레이가 없는 CI에서는 GUI를 억지로 열지 않고 서버 전용 경로를 사용한다.

```bash
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

## GUI 없이 실행하면 센서만 나오지 않는다

`-s`는 GUI를 끄는 옵션이다. 카메라와 GPU 라이다에 필요한 렌더링까지 끄지는 않는다. 디스플레이 없는 환경에서는 렌더링 경로도 준비해야 한다. Gazebo 자체 센서 월드는 [Harmonic의 EGL 렌더링](https://gazebosim.org/api/sim/8/headless_rendering.html) 옵션으로 실행할 수 있다.

```bash
gz sim -s -r --headless-rendering \
  examples/ros2_ws/src/tutorial_bot_gazebo/worlds/sensor-test.sdf
```

센서가 실제로 달린 로봇을 생성해야 메시지가 나온다. 이 옵션에서도 GPU 드라이버 초기화가 실패하면 소프트웨어 렌더링과 가상 화면으로 비교한다. 통합 launch를 실행하는 경우에는 다음 예제를 사용한다.

```bash
sudo apt install -y xvfb libgl1-mesa-dri
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
xvfb-run -a env LIBGL_ALWAYS_SOFTWARE=1 \
  ros2 launch tutorial_bot_bringup simulation.launch.py \
  gui:=false rviz:=false nav2:=false
```

오류 없이 실행된 뒤 다른 터미널에서 `/scan`과 `/camera/image`를 확인한다. 소프트웨어 렌더링에서는 속도가 느릴 수 있으므로 타임스탬프가 증가하는지와 실제 수신률을 함께 확인한다.

## 다른 Gazebo 실행과 토픽이 섞인다

Gazebo Transport의 검색 범위가 같으면 이전 서버나 다른 사용자의 토픽이 보일 수 있다. 디버깅에 사용할 고유한 통신 구역(partition)을 정하고 관련된 모든 터미널에서 같은 값을 설정한다.

```bash
export GZ_PARTITION="tutorial_${USER}_debug"
printf '%s\n' "$GZ_PARTITION"
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

브리지와 `gz topic`을 실행하는 터미널에도 같은 `GZ_PARTITION`을 설정한다. 무관한 프로세스를 `pkill`이나 `killall`로 종료하지 않는다.

## 모델, 메시, 월드 리소스를 찾지 못한다

상대 경로는 현재 작업 디렉터리에 따라 달라질 수 있다. 먼저 실제 파일을 확인한다.

```bash
pwd
test -f examples/gazebo/worlds/first-world.sdf
ros2 pkg prefix --share tutorial_bot_gazebo
```

자체 모델이나 메시를 `model://` URI로 참조할 때는 해당 모델 디렉터리의 부모를 리소스 검색 경로에 추가한다.

```bash
tutorial_model_parent=/absolute/path/that/contains/model_directories
test -d "$tutorial_model_parent"
export GZ_SIM_RESOURCE_PATH="$tutorial_model_parent:${GZ_SIM_RESOURCE_PATH:-}"
printf '%s\n' "$GZ_SIM_RESOURCE_PATH" | tr ':' '\n'
```

이 저장소의 `first-world.sdf`는 외부 모델을 참조하지 않으므로 이 변수가 없어도 실행되어야 한다. Fuel URL을 사용하는 예제는 네트워크와 로컬 캐시 상태를 별도로 확인한다.

## Gazebo 토픽은 있지만 ROS 2 토픽이 없다

먼저 Gazebo 쪽 발행자가 실제로 존재하는지 확인한다.

```bash
gz topic -l | sort
gz topic -i -t /model/tutorial_bot/odometry
```

그다음 브리지 프로세스와 ROS 통신 그래프를 확인한다.

```bash
ros2 node list
ros2 topic list -t
ros2 node info /ros_gz_bridge
```

브리지 YAML의 양쪽 이름, 양쪽 타입, 방향이 실제 토픽과 일치해야 한다. 상태 토픽은 다음과 같이 `GZ_TO_ROS`를 사용한다.

```yaml
- ros_topic_name: "/odom"
  gz_topic_name: "/model/tutorial_bot/odometry"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS
```

명령 토픽에 같은 방향을 사용하면 키보드 입력이 Gazebo에 도달하지 않는다. `cmd_vel`은 반대 방향으로 설정한다.

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ
```

## 센서 토픽이 보이지만 메시지를 받지 못한다

센서 데이터는 best-effort QoS를 사용하는 경우가 많다. 실제 발행자와 구독자의 QoS를 확인한다.

```bash
ros2 topic info -v /scan
ros2 topic echo /scan --qos-reliability best_effort --once
```

Gazebo 쪽에서도 메시지가 나오는지 분리한다.

```bash
gz topic -i -t /tutorial_bot/lidar
gz topic -e -t /tutorial_bot/lidar
```

Gazebo에서도 메시지가 없다면 브리지가 아니라 `<sensor>` 설정, Sensors 시스템, 시뮬레이션 일시 정지 상태를 확인한다.

```xml
<sensor name="lidar" type="gpu_lidar">
  <always_on>true</always_on>
  <update_rate>10</update_rate>
  <topic>/tutorial_bot/lidar</topic>
  <!-- <lidar>의 scan과 range 설정이 이어진다. -->
</sensor>
```

## TF 또는 RViz 표시가 멈춘다

시뮬레이션 시간을 사용하는 노드는 `/clock` 브리지와 `use_sim_time`이 모두 필요하다.

```bash
ros2 topic echo /clock --once
ros2 param get /robot_state_publisher use_sim_time
ros2 run tf2_ros tf2_echo odom base_link
```

`robot_state_publisher`가 실행 중인지, `robot_description` 파라미터가 있는지 확인한다.

```bash
ros2 node info /robot_state_publisher
ros2 param get /robot_state_publisher robot_description > /tmp/robot_description.txt
```

RViz의 Fixed Frame이 실제로 존재하는 `odom` 또는 `base_link`인지 확인한다. 프레임 이름에 접두사나 네임스페이스를 적용했다면 브리지, 상태 발행자, RViz 설정에서 같은 이름을 사용해야 한다.

## RViz Pointcloud가 기울거나 로봇과 따로 움직인다

메시지 수신, 시간, 좌표계를 순서대로 확인한다. Fixed Frame을 `odom`으로 두고 센서 프레임까지 TF가 연결되는지 검사한다.

```bash
ros2 topic echo /camera/points --field header --qos-reliability best_effort --once
ros2 topic echo /camera/camera_info --field header --qos-reliability best_effort --once
ros2 run tf2_ros tf2_echo odom camera_link
```

이 저장소의 Harmonic RGB-D Pointcloud은 `camera_link`, 영상과 CameraInfo는 `camera_optical_frame`이어야 한다. 두 프레임은 축 방향이 다르다. Pointcloud YAML의 `frame_id: camera_link`가 빠지거나 브리지가 1.0.22보다 오래되었으면 [설치 안내](02_installation-jazzy.md)에 따라 갱신한 뒤 다시 실행한다. 헤더 이름만 바꿔도 되는 이유는 이 예제의 점 좌표가 이미 본체 좌표계로 생성되기 때문이다. 다른 센서에는 그 센서의 실제 좌표계를 확인해 적용한다.

RViz의 LaserScan·PointCloud2에서 Reliability Policy를 `Best Effort`로 맞춘다. Camera 디스플레이가 실패하지만 Image는 나온다면 `/camera/camera_info`, 영상의 프레임, TF를 확인한다. 로봇이 주행할 때 장애물 위치가 함께 움직이면 중복된 `odom → base_link` 발행자나 잘못된 센서 장착 변환도 확인한다.

## 컨트롤러가 시작되지 않는다

컨트롤러 관리자 서비스와 컨트롤러 상태를 확인한다.

```bash
ros2 service type /controller_manager/list_controllers
ros2 control list_controllers
ros2 topic list | grep controller
```

`gz_ros2_control` 플러그인 설정의 파라미터 파일 경로와 시스템 이름을 확인한다.

```xml
<ros2_control name="GazeboSimSystem" type="system">
  <hardware>
    <plugin>gz_ros2_control/GazeboSimSystem</plugin>
  </hardware>
  <!-- wheel joint command/state interface가 이어진다. -->
</ros2_control>

<gazebo>
  <plugin filename="gz_ros2_control-system"
          name="gz_ros2_control::GazeboSimROS2ControlPlugin">
    <parameters>controllers.yaml</parameters>
  </plugin>
</gazebo>
```

소스 디렉터리 기준 상대 경로가 아니라 설치된 패키지 share의 컨트롤러 YAML을 실행 구성이 전달하는지 확인한다.

## 변경한 파일이 실행에 반영되지 않는다

작업 공간을 다시 빌드하고 기본 ROS 환경과 작업 공간 환경을 올바른 순서로 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
colcon build --symlink-install
source install/setup.bash
cd ../..
ros2 pkg prefix tutorial_bot_description
ros2 pkg prefix tutorial_bot_bringup
```

`ros2 pkg prefix`가 예상하지 않은 작업 공간을 가리키면 새 터미널에서 환경을 불러오는 순서를 다시 확인한다.

## 재현 보고에 포함할 내용

문제 해결을 요청할 때 다음 정보를 함께 제공하면 실행 환경과 재현 절차를 확인하기 쉽다.

1. 실행한 전체 명령과 현재 작업 디렉터리를 기록한다.
2. `ROS_DISTRO`, `gz sim --versions`, 패키지 설치 경로 출력을 기록한다.
3. `gz sim -v 4`의 최초 오류부터 오류 직전부터의 로그까지 기록한다.
4. `gz topic -l`과 `ros2 topic list -t`를 함께 기록한다.
5. 사용한 월드, Xacro, 브리지 YAML, 실행 구성 인자를 기록한다.
6. 서버 전용에서도 실패하는지, GUI에서만 실패하는지 구분한다.

이 정보가 있으면 문제를 설치, 파일 문법, 서버, 렌더링, 브리지, ROS 2 프로그램으로 빠르게 분류할 수 있다.
