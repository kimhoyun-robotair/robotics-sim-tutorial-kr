# ROS 2 Jazzy와 Gazebo Harmonic 설치

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [지원 환경과 호환성](00_compatibility.md)

## 학습 목표

- Ubuntu 24.04에 ROS 2 Jazzy apt 저장소를 설정한다.
- Jazzy와 짝이 맞는 Gazebo Harmonic, `ros_gz`, `gz_ros2_control`을 설치한다.
- `rosdep`과 `colcon`으로 실습 작업 공간을 빌드한다.
- SDF, Xacro, 브리지 YAML, ROS 2 실행 구성을 각각 검사한다.

## 1. 운영체제와 문자 인코딩을 확인한다

이 절차는 Ubuntu 24.04 Noble을 컴퓨터에 직접 설치한 환경을 기준으로 한다. `Ctrl+Alt+T`로 터미널을 열고 배포판, CPU 아키텍처, 문자 인코딩을 확인한다. 아래 명령은 Bash 기준이며, `$` 같은 프롬프트 표시는 입력하지 않는다.

```bash
. /etc/os-release
printf 'Ubuntu=%s (%s)\n' "$VERSION_ID" "$VERSION_CODENAME"
dpkg --print-architecture
locale
```

Ubuntu 버전이 `24.04`, 코드명이 `noble`이어야 한다. `locale` 출력에서 `ko_KR.UTF-8`이나 `en_US.UTF-8`처럼 UTF-8이 보이면 다음 설정을 건너뛴다. UTF-8이 없다면 다음과 같이 설정한다.

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale
```

## 2. ROS 2 apt 저장소를 등록한다

ROS 2의 [Jazzy Ubuntu deb 설치 문서](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)가 제공하는 `ros2-apt-source` 패키지로 서명 키와 apt 저장소를 등록한다. 최신 설치 패키지의 버전을 조회하므로 네트워크 연결이 필요하다.

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo apt update

ROS_APT_SOURCE_VERSION=$(curl -fsSL \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F 'tag_name' | awk -F'"' '{print $4}')

printf '설치 패키지 버전: %s\n' "$ROS_APT_SOURCE_VERSION"
```

버전 번호가 비어 있지 않은지 확인한 뒤 패키지를 내려받는다.

```bash
curl -fL -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

```

다운로드가 오류 없이 끝났을 때만 설치한다.

```bash
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
```

다운로드 URL이나 설치 방식은 시간이 지나며 갱신될 수 있다. 출력된 설치 패키지 버전이 비어 있으면 중단한다. 위 명령이 공식 문서와 달라졌다면 공식 Jazzy 문서의 절차를 우선한다. 버전 조회가 실패하거나 다운로드가 오류로 끝났다면 다음 설치 명령을 실행하지 말고 네트워크와 공식 안내를 확인한다.

## 3. Jazzy와 Harmonic 통합 패키지를 설치한다

RViz를 포함한 데스크톱 도구, 개발 도구, Gazebo 연동 패키지, 제어 플러그인, 키보드 조종 도구를 설치한다.

```bash
sudo apt upgrade
sudo apt install -y \
  ros-jazzy-desktop \
  ros-dev-tools \
  ros-jazzy-ros-gz \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-rviz-imu-plugin \
  python3-venv git ros-jazzy-xacro liburdfdom-tools
```

`ros-jazzy-ros-gz`가 Jazzy에 대응하는 Gazebo Harmonic 의존성을 가져온다. 이 조합에서는 OSRF 저장소에서 다른 Gazebo 배포판을 별도로 설치할 필요가 없다.

!!! warning "Classic과 Harmonic 패키지를 섞지 않는다"

    `gazebo`, `gazebo11`, `gazebo_ros_pkgs`, `libgazebo_ros_diff_drive.so`는 Gazebo Classic 계열이다. 이 과정의 `gz sim`, `ros_gz`, `gz_ros2_control`과 교차 사용하지 않는다.

이 예제의 브리지 YAML은 항목별 `frame_id`와 `qos_profile`을 사용하므로 **`ros_gz_bridge` 1.0.22 이상**이 필요하다. 예전에 Jazzy를 설치했다면 브리지도 갱신한다. [공식 변경 이력](https://github.com/gazebosim/ros_gz/blob/0fa70cb7c15f7500c495190020dd6292188c8e54/ros_gz_bridge/CHANGELOG.rst)에 따르면 두 기능은 각각 1.0.20과 1.0.22에 추가되었다.

```bash
sudo apt update
sudo apt install --only-upgrade ros-jazzy-ros-gz-bridge
tutorial_bridge_version="$(dpkg-query -W -f='${Version}' ros-jazzy-ros-gz-bridge)"
printf 'ros_gz_bridge=%s\n' "$tutorial_bridge_version"
dpkg --compare-versions "$tutorial_bridge_version" ge 1.0.22 \
  && echo "브리지 버전 조건을 만족한다."
```

버전 조건을 만족한다는 문구가 없으면 브리지를 갱신한 뒤 실습을 진행한다. 소스에서 빌드한 브리지를 사용한다면 `ros2 pkg prefix ros_gz_bridge`로 실제 선택된 경로와 해당 소스 버전도 확인한다.

## 4. 새 터미널의 환경을 설정한다

설치 직후 새 터미널을 열고 사용하는 셸에 맞는 setup 파일을 불러온다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    ```

자동 설정을 원하면 사용하는 셸의 설정 파일에 setup 한 줄을 직접 추가한다. 여러 ROS 배포판을 번갈아 사용한다면 자동으로 불러오지 않고 터미널마다 명시적으로 선택하는 편이 안전하다.

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

`ROS_DISTRO=jazzy`, Gazebo Sim 8 계열, 각 패키지 설치 경로와 `ros_gz_sim create` 실행 파일이 확인되어야 한다.

## 5. Jazzy 예제를 내려받고 빌드한다

### 5.1. Jazzy 브랜치만 내려받기

처음 실습한다면 홈 디렉터리에 저장소를 내려받는다. 이미 내려받았다면 중복 복제하지 말고 기존 저장소로 이동한 뒤 현재 브랜치를 확인한다. 이 문서의 경로는 `~/robotics-sim-tutorial-kr`을 기준으로 한다. 다른 위치에 저장했다면 `cd` 경로만 바꾼다.

```bash
cd ~
git clone --branch Jazzy --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd ~/robotics-sim-tutorial-kr
git branch --show-current
```

마지막 출력은 대소문자를 포함해 `Jazzy`여야 한다. 저장소 루트는 `README.md`, `docs`, `examples`가 함께 있는 디렉터리를 뜻한다.

### 5.2. 의존성 설치와 빌드

`rosdep init`은 한 컴퓨터에서 한 번만 실행한다. 이미 초기화되었다는 메시지가 나오면 다시 만들지 않고 갱신만 실행한다.

```bash
sudo rosdep init
rosdep update
```

저장소 루트에서 실습 작업 공간으로 이동해 `package.xml`의 의존성을 설치한다. 이 단계에서 Nav2, 컨트롤러, 메시지 패키지처럼 통합 예제가 요구하는 추가 deb도 함께 설치된다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
cd ../..
```

빌드가 끝나면 `Summary`에 패키지 실패가 없어야 한다. 마지막 `cd ../..`는 이후 명령이 기준으로 삼는 저장소 루트로 돌아오는 명령이다. 새 터미널에서는 다음 세 줄로 작업 위치와 ROS 환경을 준비한다. `source` 설정은 해당 터미널에만 적용된다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 pkg prefix tutorial_bot_bringup
```

## 6. XML 원본을 정적으로 검사한다

SDF 월드는 `gz sdf -k`로 검사한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sdf -k examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
```

Xacro는 최종 URDF로 확장한 뒤 URDF 링크 트리를 검사한다.

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

`xacro`가 이 XML을 포함한 URDF를 생성하고, `ros_gz_sim create`가 `robot_description` 토픽에서 읽어 Gazebo 개체로 생성한다.

## 7. 브리지 YAML이 무엇을 연결하는지 확인한다

Gazebo Transport와 ROS 2 DDS는 서로 다른 통신 그래프이므로 토픽마다 이름, 타입, 방향을 선언한다. 다음은 `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml`의 핵심 항목이다.

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

`topic_name`은 양쪽 이름이 같을 때 사용하는 축약형이다. 명령 토픽은 ROS 2에서 Gazebo로, 상태와 센서 토픽은 Gazebo에서 ROS 2로 전달한다. YAML은 다음처럼 브리지 노드의 `config_file` 파라미터로 전달한다. 이 명령은 계속 실행되므로 로그를 확인한 뒤 `Ctrl+C`로 종료한다. 다음 통합 실행 단계에서는 브리지가 자동으로 시작된다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args \
  -p config_file:="$(ros2 pkg prefix --share tutorial_bot_bringup)/config/bridge.yaml"
```

## 8. 실행 구성이 파일을 조합하는 방식을 확인한다

ROS 2의 launch 파일은 여러 프로그램을 함께 실행하는 Python 파일이다. 다음 코드는 Gazebo와 브리지를 묶는 방식만 보여주는 읽기용 예제이다. 로봇 생성과 제어는 아래의 완성된 `simulation.launch.py`로 실행한다.

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
            "config_file": str(bringup_share / "config" / "bridge-intermediate.yaml")
        }],
        output="screen",
    )
    return LaunchDescription([gazebo, bridge])
```

완성된 구현은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`에 있다. 이 파일은 `gz_ros2_control`로 바퀴를 제어하므로 센서와 시계만 연결하는 `bridge-intermediate.yaml`을 사용한다. 앞 절의 `bridge.yaml`은 초급 Gazebo DiffDrive 실습용이다. 전체 실행 구성을 처음 확인할 때는 Nav2와 GUI 도구를 꺼서 프로세스 수를 줄인다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  gui:=false rviz:=false nav2:=false
```

로그에서 컨트롤러 활성화가 끝나면 별도 터미널에서 시계, 컨트롤러, 오도메트리를 확인한다. `gui:=false`여도 카메라와 GPU 라이다는 렌더링이 필요하다. 화면 없는 서버에서 렌더링 오류가 나면 [문제 해결](03_troubleshooting.md)의 화면 없는 센서 실행 절차를 따른다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 topic echo /clock --once
ros2 control list_controllers
ros2 topic echo /odom --once
```

확인을 마치면 시뮬레이션을 실행한 터미널에서 `Ctrl+C`를 누른다.

## 설치 완료 기준

다음 결과를 모두 얻으면 설치가 완료된 상태이다.

1. `gz sim --versions`가 Gazebo Sim 8 계열을 출력해야 한다.
2. `ros_gz_sim`, `ros_gz_bridge`, `gz_ros2_control` 패키지 설치 경로를 찾아야 한다.
3. `colcon build --symlink-install`이 오류 없이 끝나야 한다.
4. 두 SDF와 Xacro에서 정적 검사 오류가 없어야 한다.
5. 통합 실행 구성에서 `/clock`과 `/odom`을 한 번 이상 받아야 한다.

실패한 계층은 [시작 단계 문제 해결](03_troubleshooting.md)에서 순서대로 진단한다.
