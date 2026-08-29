# 시작 단계 문제 해결

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [Jazzy 환경 설치](02_installation-jazzy.md)

오류를 한꺼번에 고치려 하면 SDF, Gazebo server, rendering, bridge, ROS 2 overlay 가운데 원인을 찾기 어렵다. 이 장에서는 환경 → 정적 파일 → Gazebo Transport → ROS 2 bridge → TF·controller 순서로 경계를 좁힌다.

## 먼저 진단 정보를 고정한다

문제가 발생한 터미널에서 다음 출력을 저장한다. 다른 터미널의 환경은 같다고 가정하지 않는다.

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

현재 shell에 Jazzy underlay를 불러오지 않았거나 Jazzy가 설치되지 않은 상태이다.

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

`/opt/ros/jazzy/setup.*` 자체가 없다면 package 상태를 확인한다.

```bash
apt-cache policy ros-jazzy-desktop
dpkg-query -W ros-jazzy-desktop
```

## `gz` 또는 `ros_gz`를 찾지 못한다

Gazebo executable과 ROS integration package를 따로 확인한다.

```bash
command -v gz
apt-cache policy ros-jazzy-ros-gz
dpkg-query -W ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
```

패키지가 없다면 Jazzy apt source가 활성화되었는지 확인한 뒤 다시 설치한다.

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control
```

## 다른 ROS 또는 Gazebo 설치가 섞인다

여러 underlay나 source build가 앞에 있으면 plugin ABI와 Python package가 서로 다른 경로에서 로드될 수 있다.

```bash
type -a ros2
type -a gz
printf '%s\n' "${AMENT_PREFIX_PATH:-unset}" | tr ':' '\n'
printf '%s\n' "${CMAKE_PREFIX_PATH:-unset}" | tr ':' '\n'
printf '%s\n' "${GZ_SIM_SYSTEM_PLUGIN_PATH:-unset}" | tr ':' '\n'
```

새 터미널을 열고 `/opt/ros/jazzy/setup.bash`만 불러온 상태에서 문제가 재현되는지 확인한다. 이후 tutorial overlay를 마지막에 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

## SDF 또는 Xacro 문법 오류가 발생한다

GUI를 실행하기 전에 parser부터 확인한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

SDF 오류의 line과 column을 먼저 고친다. XML에서는 닫는 태그, 따옴표, nesting이 흔한 원인이다. 예를 들어 plugin parameter는 plugin 요소 안에 있어야 한다.

```xml
<!-- 올바른 구조이다. -->
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
</plugin>
```

Xacro 오류라면 생성된 URDF가 아니라 `.urdf.xacro` 원본을 수정한다. `xacro` 명령이 실패하면 `/tmp/tutorial_bot.urdf`는 불완전할 수 있으므로 후속 spawn을 시도하지 않는다.

## server와 GUI 가운데 어디에서 실패하는지 확인한다

verbosity를 높이고 server-only로 실행한다.

```bash
gz sim -v 4 -s -r examples/gazebo/worlds/first-world.sdf
```

server가 계속 실행되고 다른 터미널의 `gz topic -l`에 `/clock`이 보이면 physics와 Transport는 동작한다.

```bash
gz topic -l | sort
gz topic -e -t /clock
```

이 상태에서 GUI만 별도로 연결한다.

```bash
gz sim -g
```

server는 동작하지만 GUI만 실패하면 display 또는 rendering 문제로 범위를 좁힐 수 있다.

## GUI가 열리지 않거나 검은 화면이 나온다

display session과 OpenGL renderer를 확인한다. `glxinfo`가 없다면 `mesa-utils`를 설치한다.

```bash
printf 'SESSION=%s DISPLAY=%s WAYLAND=%s\n' \
  "${XDG_SESSION_TYPE:-unset}" "${DISPLAY:-unset}" "${WAYLAND_DISPLAY:-unset}"
sudo apt install -y mesa-utils
glxinfo -B
```

하드웨어 가속 경로의 문제인지 확인할 때만 software rendering으로 비교 실행한다.

```bash
LIBGL_ALWAYS_SOFTWARE=1 gz sim -r examples/gazebo/worlds/first-world.sdf
```

원격 shell이나 display가 없는 CI에서는 GUI를 억지로 열지 않고 server-only 경로를 사용한다.

```bash
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

## 다른 Gazebo session과 섞인다

Gazebo Transport discovery 범위가 같으면 이전 server나 다른 사용자의 토픽이 보일 수 있다. 디버깅에 사용할 고유 partition을 정하고 관련된 모든 터미널에서 같은 값을 설정한다.

```bash
export GZ_PARTITION="tutorial_${USER}_debug"
printf '%s\n' "$GZ_PARTITION"
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

bridge와 `gz topic`을 실행하는 터미널에도 같은 `GZ_PARTITION`을 설정한다. 무관한 process를 `pkill`이나 `killall`로 종료하지 않는다.

## model, mesh, world 리소스를 찾지 못한다

상대 경로는 현재 working directory에 따라 달라질 수 있다. 먼저 실제 파일을 확인한다.

```bash
pwd
test -f examples/gazebo/worlds/first-world.sdf
ros2 pkg prefix --share tutorial_bot_gazebo
```

자체 model이나 mesh를 `model://` URI로 참조할 때는 해당 model 디렉터리의 부모를 resource path에 추가한다.

```bash
tutorial_model_parent=/absolute/path/that/contains/model_directories
test -d "$tutorial_model_parent"
export GZ_SIM_RESOURCE_PATH="$tutorial_model_parent:${GZ_SIM_RESOURCE_PATH:-}"
printf '%s\n' "$GZ_SIM_RESOURCE_PATH" | tr ':' '\n'
```

이 저장소의 `first-world.sdf`는 외부 model을 참조하지 않으므로 이 변수가 없어도 실행되어야 한다. Fuel URL을 사용하는 예제는 네트워크와 local cache 상태를 별도로 확인한다.

## Gazebo 토픽은 있지만 ROS 2 토픽이 없다

먼저 Gazebo 쪽 producer가 실제로 존재하는지 확인한다.

```bash
gz topic -l | sort
gz topic -i -t /model/tutorial_bot/odometry
```

그다음 bridge process와 ROS graph를 확인한다.

```bash
ros2 node list
ros2 topic list -t
ros2 node info /ros_gz_bridge
```

bridge YAML의 양쪽 이름, 양쪽 type, 방향이 실제 토픽과 일치해야 한다. 상태 토픽은 다음과 같이 `GZ_TO_ROS`를 사용한다.

```yaml
- ros_topic_name: "/odom"
  gz_topic_name: "/model/tutorial_bot/odometry"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS
```

명령 토픽에 같은 방향을 사용하면 keyboard 입력이 Gazebo에 도달하지 않는다. `cmd_vel`은 반대 방향으로 설정한다.

```yaml
- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ
```

## 센서 토픽이 보이지만 메시지를 받지 못한다

sensor data는 best-effort QoS를 사용하는 경우가 많다. 실제 publisher와 subscriber의 QoS를 확인한다.

```bash
ros2 topic info -v /scan
ros2 topic echo /scan --qos-reliability best_effort --once
```

Gazebo 쪽에서도 메시지가 나오는지 분리한다.

```bash
gz topic -i -t /tutorial_bot/lidar
gz topic -e -t /tutorial_bot/lidar
```

Gazebo에서도 메시지가 없다면 bridge가 아니라 `<sensor>` 설정, Sensors system, simulation pause 상태를 확인한다.

```xml
<sensor name="lidar" type="gpu_lidar">
  <always_on>true</always_on>
  <update_rate>10</update_rate>
  <topic>/tutorial_bot/lidar</topic>
  <!-- <lidar>의 scan과 range 설정이 이어진다. -->
</sensor>
```

## TF 또는 RViz 표시가 멈춘다

simulation time을 사용하는 node는 `/clock` bridge와 `use_sim_time`이 모두 필요하다.

```bash
ros2 topic echo /clock --once
ros2 param get /robot_state_publisher use_sim_time
ros2 run tf2_ros tf2_echo odom base_link
```

`robot_state_publisher`가 실행 중인지, `robot_description` parameter가 있는지 확인한다.

```bash
ros2 node info /robot_state_publisher
ros2 param get /robot_state_publisher robot_description > /tmp/robot_description.txt
```

RViz의 Fixed Frame이 실제로 존재하는 `odom` 또는 `base_link`인지 확인한다. frame 이름에 prefix나 namespace를 적용했다면 bridge, state publisher, RViz 설정에서 같은 이름을 사용해야 한다.

## controller가 시작되지 않는다

controller manager service와 controller 상태를 확인한다.

```bash
ros2 service type /controller_manager/list_controllers
ros2 control list_controllers
ros2 topic list | grep controller
```

`gz_ros2_control` plugin 설정의 parameter 파일 경로와 system 이름을 확인한다.

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

source tree의 상대 경로가 아니라 설치된 package share의 controller YAML을 launch가 전달하는지 확인한다.

## 변경한 파일이 실행에 반영되지 않는다

workspace를 다시 빌드하고 underlay와 overlay를 올바른 순서로 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 pkg prefix tutorial_bot_description
ros2 pkg prefix tutorial_bot_bringup
```

`ros2 pkg prefix`가 예상하지 않은 workspace를 가리키면 새 터미널에서 source 순서를 다시 구성한다.

## 재현 보고에 포함할 내용

도움을 요청할 때 다음 정보를 함께 제공한다.

1. 실행한 전체 명령과 현재 working directory를 기록한다.
2. `ROS_DISTRO`, `gz sim --versions`, package prefix 출력을 기록한다.
3. `gz sim -v 4`의 최초 오류부터 관련 stack trace까지 기록한다.
4. `gz topic -l`과 `ros2 topic list -t`를 함께 기록한다.
5. 사용한 world, Xacro, bridge YAML, launch 인자를 기록한다.
6. server-only에서도 실패하는지, GUI에서만 실패하는지 구분한다.

이 정보가 있으면 문제를 설치, parser, server, rendering, bridge, ROS 2 application 계층으로 빠르게 분류할 수 있다.
