# ROS 2 Jazzy와 Gazebo Harmonic 설치

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [지원 환경과 호환성](00_compatibility.md)

## 학습 목표

- Ubuntu 24.04에 ROS 2 Jazzy apt 저장소를 설정한다.
- Jazzy와 짝이 맞는 Gazebo Harmonic, `ros_gz`, `gz_ros2_control`을 설치한다.
- `rosdep`과 `colcon`으로 tutorial workspace를 빌드한다.
- SDF, Xacro, bridge YAML, ROS 2 launch를 각각 검사한다.

## 1. 운영체제와 locale을 확인한다

이 절차는 native Ubuntu 24.04 Noble을 기준으로 한다. 먼저 배포판, architecture, UTF-8 locale을 확인한다.

```bash
. /etc/os-release
printf 'Ubuntu=%s (%s)\n' "$VERSION_ID" "$VERSION_CODENAME"
dpkg --print-architecture
locale
```

`VERSION_ID`가 `24.04`, codename이 `noble`이어야 한다. locale 출력에 UTF-8이 없다면 다음과 같이 설정한다.

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale
```

## 2. ROS 2 apt 저장소를 등록한다

ROS 2의 [Jazzy Ubuntu deb 설치 문서](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)가 제공하는 `ros2-apt-source` 패키지로 key와 source 설정을 등록한다. 이 bootstrap 명령은 최신 release 번호를 조회하므로 네트워크 연결이 필요하다.

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo apt update

ROS_APT_SOURCE_VERSION=$(curl -s \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F 'tag_name' | awk -F'"' '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
```

다운로드 URL이나 설치 방식은 시간이 지나며 갱신될 수 있다. 위 명령이 공식 문서와 달라졌다면 공식 Jazzy 문서의 절차를 우선한다. 따라서 뭔가 이상하다 싶으면 공식 문서를 참조하는 것을 권장한다.

## 3. Jazzy와 Harmonic 통합 패키지를 설치한다

desktop 도구, 개발 도구, Jazzy용 Gazebo 통합, 제어 plugin, keyboard teleop을 설치한다.

```bash
sudo apt upgrade
sudo apt install -y \
  ros-jazzy-desktop \
  ros-dev-tools \
  ros-jazzy-ros-gz \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-rviz-imu-plugin \
  python3-venv
```

`ros-jazzy-ros-gz`가 Jazzy에 대응하는 Gazebo Harmonic 의존성을 가져온다. 이 조합에서는 OSRF 저장소에서 다른 Gazebo release를 별도로 설치할 필요가 없다.

!!! warning "Classic과 Harmonic 패키지를 섞지 않는다"

    `gazebo`, `gazebo11`, `gazebo_ros_pkgs`, `libgazebo_ros_diff_drive.so`는 Gazebo Classic 계열이다. 이 과정의 `gz sim`, `ros_gz`, `gz_ros2_control`과 교차 사용하지 않는다.

## 4. 새 터미널의 환경을 설정한다

설치 직후 새 터미널을 열고 사용하는 shell에 맞는 setup 파일을 불러온다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    ```

자동 설정을 원하면 사용하는 shell의 설정 파일에 setup 한 줄을 직접 추가한다. 여러 ROS distribution을 번갈아 사용한다면 자동으로 source하지 않고 터미널마다 명시적으로 선택하는 편이 안전하다.

```bash
# ~/.bashrc에 추가할 내용
source /opt/ros/jazzy/setup.bash
```

설치 결과를 확인한다.

```bash
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-unset}"
gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
ros2 pkg prefix ros_gz_image
ros2 pkg prefix gz_ros2_control
ros2 pkg executables ros_gz_sim
```

`ROS_DISTRO=jazzy`, Gazebo Sim 8 계열, 각 package prefix와 `ros_gz_sim create` 실행 파일이 확인되어야 한다.

## 5. rosdep을 준비하고 workspace를 빌드한다

`rosdep init`은 한 컴퓨터에서 한 번만 실행한다. 이미 초기화되었다는 메시지가 나오면 다시 만들지 않고 update만 실행한다.

```bash
sudo rosdep init
rosdep update
```

저장소 루트에서 tutorial workspace로 이동해 `package.xml`의 의존성을 설치한다. 이 단계에서 Nav2, controller, message package처럼 통합 예제가 요구하는 추가 deb도 함께 설치된다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

새 터미널에서는 항상 underlay를 먼저, workspace overlay를 나중에 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 pkg prefix tutorial_bot_bringup
```

## 6. XML 원본을 정적으로 검사한다

SDF world는 `gz sdf -k`로 검사한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sdf -k examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
```

Xacro는 최종 URDF로 확장한 뒤 URDF tree를 검사한다.

```bash
xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

Xacro 원본의 DiffDrive 부분은 다음과 같이 URDF 안의 `<gazebo>` 확장 태그로 작성한다.

```xml
<gazebo>
  <plugin filename="gz-sim-diff-drive-system"
          name="gz::sim::systems::DiffDrive">
    <left_joint>left_wheel_joint</left_joint>
    <right_joint>right_wheel_joint</right_joint>
    <wheel_separation>0.38</wheel_separation>
    <wheel_radius>0.06</wheel_radius>
    <odom_publish_frequency>30</odom_publish_frequency>
  </plugin>
</gazebo>
```

`xacro`가 이 XML을 포함한 URDF를 생성하고, `ros_gz_sim create`가 `robot_description` 토픽에서 읽어 Gazebo entity로 생성한다.

## 7. bridge YAML이 무엇을 연결하는지 확인한다

Gazebo Transport와 ROS 2 DDS는 별도 graph이므로 토픽마다 이름, type, 방향을 선언한다. 다음은 `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`의 핵심 항목이다.

```yaml
- topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS
  qos_profile: CLOCK

- ros_topic_name: "/cmd_vel"
  gz_topic_name: "/model/tutorial_bot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ

- ros_topic_name: "/odom"
  gz_topic_name: "/model/tutorial_bot/odometry"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS
```

`topic_name`은 양쪽 이름이 같을 때 사용하는 축약형이다. 명령 토픽은 ROS 2에서 Gazebo로, 상태와 sensor 토픽은 Gazebo에서 ROS 2로 전달한다. YAML은 다음처럼 bridge node의 `config_file` parameter로 전달한다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args \
  -p config_file:="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge.yaml"
```

## 8. launch가 파일을 조합하는 방식을 확인한다

통합 launch는 world, robot description, spawn, bridge, controller를 순서대로 구성한다. 다음 Python 조각은 Gazebo와 YAML bridge를 시작하는 최소 구조이다.

```python
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    gazebo_share = Path(get_package_share_directory("tutorial_bot_gazebo"))
    bringup_share = Path(get_package_share_directory("tutorial_bot_bringup"))
    ros_gz_share = Path(get_package_share_directory("ros_gz_sim"))

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(ros_gz_share / "launch" / "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": f"-r {gazebo_share / 'worlds' / 'training.sdf'}",
            "on_exit_shutdown": "true",
        }.items(),
    )
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{
            "config_file": str(bringup_share / "config" / "bridge.yaml")
        }],
        output="screen",
    )
    return LaunchDescription([gazebo, bridge])
```

전체 구현은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`에 있다. 전체 stack을 처음 확인할 때는 Nav2와 GUI 도구를 꺼서 process 수를 줄인다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  gui:=false rviz:=false nav2:=false
```

별도 터미널에서 clock, controller, odometry를 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 topic echo /clock --once
ros2 control list_controllers
ros2 topic echo /odom --once
```

확인을 마치면 launch 터미널에서 `Ctrl+C`를 누른다.

## 설치 완료 기준

다음 결과를 모두 얻으면 설치가 완료된 상태이다.

1. `gz sim --versions`가 Gazebo Sim 8 계열을 출력해야 한다.
2. `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control` package prefix를 찾아야 한다.
3. `colcon build --symlink-install`이 오류 없이 끝나야 한다.
4. 두 SDF와 Xacro에서 정적 검사 오류가 없어야 한다.
5. 통합 launch에서 `/clock`과 `/odom`을 한 번 이상 받아야 한다.

실패한 계층은 [시작 단계 문제 해결](03_troubleshooting.md)에서 순서대로 진단한다.
