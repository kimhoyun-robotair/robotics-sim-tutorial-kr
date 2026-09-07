# 프로젝트: ROS 2로 주행하고 RViz에서 관측하기

> **난이도:** 초급 프로젝트<br>
> **Gazebo:** Harmonic<br>
> **ROS 2:** Jazzy<br>
> **선행 학습:** `ros_gz_bridge`

## 프로젝트 목표

지금까지 만든 `tutorial_bot`을 하나의 ROS 2 launch 파일로 실행한다. 키보드 조종으로 주행하고, Gazebo와 ROS 양쪽에서 오도메트리를 확인하며, RViz에서 로봇 TF·2D LiDAR·RGB-D 점군·IMU·바퀴 주행 궤적을 동시에 관측한다.

완성할 구성은 차체와 좌우 구동 바퀴, 캐스터, 2D 라이다, RGB-D 카메라, IMU이다. `gz_ros2_control`이 바퀴를 제어하고 브리지와 TF 발행자가 ROS 2와 RViz에 관측값을 전달한다. 앞 장의 수동 실행 프로그램은 모두 종료한 뒤 시작한다.

<figure class="course-figure" markdown="span">
  ![이동하는 실습 bot과 ROS 2에서 확인하는 오도메트리 라이다 카메라 IMU 시계 결과](../assets/beginner/final-project-observable.svg)
  <figcaption>그림 7. 완료 기준은 process 실행 여부가 아니라 이동량, 센서 메시지, TF, trajectory를 실제로 확인하는 것이다.</figcaption>
</figure>

## 1. 소스와 실행 환경 역할을 연결한다

| 역할 | 실제 파일 |
|---|---|
| 공통 로봇 | `tutorial_bot_description/urdf/tutorial_bot.urdf.xacro` |
| 센서 매크로 | `tutorial_bot_description/urdf/sensors/*.xacro` |
| training 월드 | `tutorial_bot_gazebo/worlds/training.sdf` |
| 컨트롤러 | `tutorial_bot_control/config/controllers.yaml` |
| 브리지 | `tutorial_bot_bringup/config/bridge-intermediate.yaml` |
| 실행 구성 | `tutorial_bot_bringup/launch/simulation.launch.py` |
| RViz | `tutorial_bot_bringup/rviz/tutorial_bot.rviz` |

공통 Xacro는 초급용 Gazebo DiffDrive와 ROS 통합용 `gz_ros2_control`을 인자로 선택한다.

```xml
<xacro:arg name="control_backend" default="gazebo_diff_drive"/>
<xacro:property name="control_backend" value="$(arg control_backend)"/>

<xacro:if value="${control_backend == 'gazebo_diff_drive'}">
  <gazebo>
    <plugin filename="gz-sim-diff-drive-system"
            name="gz::sim::systems::DiffDrive">
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.38</wheel_separation>
      <wheel_radius>0.06</wheel_radius>
    </plugin>
  </gazebo>
</xacro:if>

<xacro:if value="${control_backend == 'gz_ros2_control'}">
  <ros2_control name="GazeboSimSystem" type="system">
    <hardware><plugin>gz_ros2_control/GazeboSimSystem</plugin></hardware>
    <joint name="left_wheel_joint">
      <command_interface name="velocity"/>
      <state_interface name="position"/>
      <state_interface name="velocity"/>
    </joint>
    <!-- right_wheel_joint도 같은 interface를 정의한다. -->
  </ros2_control>
  <gazebo>
    <plugin filename="gz_ros2_control-system"
            name="gz_ros2_control::GazeboSimROS2ControlPlugin">
      <parameters>$(arg controller_parameters_file)</parameters>
    </plugin>
  </gazebo>
</xacro:if>
```

위 XML은 분기 구조를 보여주는 발췌본이며 완성된 파일을 대신하지 않는다. 같은 조인트에 두 제어 방식을 동시에 붙이지 않는다. 초급 검사 스크립트는 Gazebo 자체 DiffDrive를, 통합 실행 구성은 `gz_ros2_control`을 선택한다.

## 2. 작업 공간을 빌드한다

저장소 루트에서 의존성을 설치하고 작업 공간을 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
cd ../..
```

IMU RViz 디스플레이와 키보드 조종이 없다면 설치한다.

```bash
sudo apt update
sudo apt install ros-jazzy-rviz-imu-plugin ros-jazzy-teleop-twist-keyboard
```

## 3. 먼저 자동 통합 검증을 실행한다

GUI를 열기 전에 Gazebo 자체 DiffDrive와 브리지의 최소 경로를 검증한다.

```bash
./scripts/check_ros_gz_bridge.sh --preflight-only
./scripts/check_ros_gz_bridge.sh
```

검사 스크립트는 ROS 속도 명령을 Gazebo DiffDrive로 보내고, 생성된 오도메트리를 다시 ROS에서 받는지 확인한다.

이 검사는 앞 장의 Gazebo 자체 구동 경로를 확인한다. 아래 프로젝트의 `gz_ros2_control` 경로는 컨트롤러 활성화와 실제 키보드 주행을 통해 별도로 확인한다.

동시에 `/scan`, `/imu`, RGB 영상, `/clock`도 수신한다. 다음 두 줄은 각 메시지 필드를 파싱한 뒤에만 출력된다.

```text
ROS cmd_vel to Gazebo verified: odom x=0.40..., linear.x=0.20...
Gazebo sensors to ROS verified: scan=360, image=320x240, IMU and clock received.
```

## 4. Gazebo와 RViz를 함께 실행한다

터미널 1에서 통합 launch를 실행한다. 다른 프로그램을 이어서 입력하지 말고 이 터미널은 실행 상태로 둔다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=false
```

실행 구성은 다음 작업을 함께 수행한다.

1. 설치된 `training.sdf`를 Gazebo에서 연다.
2. Xacro를 `control_backend:=gz_ros2_control`로 확장한다.
3. `robot_state_publisher`와 로봇 spawn을 시작한다.
4. `joint_state_broadcaster`와 `diff_drive_controller`를 순서대로 활성화한다.
5. 센서 브리지와 영상 브리지를 시작한다.
6. `/odom`을 `/wheel_odom_path`로 누적한다.
7. RViz 설정을 연다.

실행 구성 코드에서 Xacro 인자를 만드는 부분은 다음과 같다.

```python
robot_description = ParameterValue(
    Command([
        "xacro ", str(xacro_path),
        " control_backend:=gz_ros2_control",
        " controller_parameters_file:=", str(controller_config),
    ]),
    value_type=str,
)
```

launch는 `get_package_share_directory`로 설치된 파일을 찾는다. 따라서 빌드 후 `install/setup.bash`를 불러와야 한다.

## 5. 키보드 조종을 연결한다

Jazzy의 [`diff_drive_controller`](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)는 `geometry_msgs/msg/TwistStamped`를 받는다. 터미널 2에서 타임스탬프를 포함하는 `stamped` 옵션을 켜고, 컨트롤러와 같은 시뮬레이션 시간을 사용한다. 발행 토픽도 컨트롤러 입력으로 바꾼다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p stamped:=true -p use_sim_time:=true \
  -p frame_id:=base_link \
  -p speed:=0.2 -p turn:=0.6 \
  -p repeat_rate:=10.0 -p key_timeout:=0.6 \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

`i`를 누르고 있으면 직진하고 `j`, `l`로 회전하며 `k`로 멈춘다. 명령은 10 Hz로 반복되고, 키 입력이 0.6초 없으면 정지한다. 컨트롤러의 명령 시간 검사에 맞추기 위해 `/clock`과 `use_sim_time`을 함께 사용한다. 한국어 입력기가 켜져 있으면 키가 전달되지 않을 수 있으므로 영문 입력 상태를 사용한다.

명령 타입과 구독자를 확인한다.

```bash
ros2 topic type /diff_drive_controller/cmd_vel
ros2 topic info -v /diff_drive_controller/cmd_vel
```

예상 타입은 `geometry_msgs/msg/TwistStamped`이고 활성 컨트롤러의 구독자가 하나 이상 있어야 한다.

## 6. 바퀴 오도메트리와 궤적을 확인한다

통합 실행 구성은 다음 설정으로 `odom_to_path`를 실행한다.

```python
wheel_odom_path = Node(
    package="tutorial_bot_bringup",
    executable="odom_to_path",
    parameters=[{
        "use_sim_time": True,
        "odom_topic": "/odom",
        "path_topic": "/wheel_odom_path",
        "max_poses": 2000,
        "minimum_translation": 0.01,
    }],
)
```

확인용 터미널 3을 열고 [시작 전 환경 설정](index.md)을 불러온다. 직진과 회전을 수행한 뒤 메시지를 확인한다. `ros2 topic hz`는 수치를 확인한 뒤 `Ctrl+C`로 종료한다.

```bash
ros2 topic echo --once /odom
ros2 topic echo --once /wheel_odom_path
ros2 topic hz /odom
```

`/odom.pose.pose`가 이동하고 Path의 `poses`가 누적되면 바퀴 회전 → 오도메트리 → 궤적 경로가 정상이다. Path는 바퀴 오도메트리를 그대로 누적하므로 참값이 아니다. 미끄러짐이나 잘못된 바퀴 반지름이 있으면 실제 위치와 오차가 생긴다.

## 7. TF를 확인한다

동적 `odom → base_link`는 diff drive 컨트롤러가, URDF 기반 `base_link → sensor_link`는 `robot_state_publisher`가 담당한다.

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 run tf2_ros tf2_echo base_link camera_optical_frame
```

각 `tf2_echo`는 계속 출력되므로 확인 후 `Ctrl+C`를 누른다. 첫 좌표 변환은 주행할 때 바뀌고 센서 좌표 변환은 고정돼야 한다. 센서 메시지의 `header.frame_id`와 TF 자식 이름도 일치해야 한다.

## 8. RViz에서 센서를 확인한다

RViz Fixed Frame을 `odom`으로 둔다. 저장된 설정에는 다음 디스플레이가 들어 있다.

| Display | 토픽 | 성공 기준 |
|---|---|---|
| RobotModel | `/robot_description` | 차체, 구동 바퀴, 캐스터, 센서 장착부가 보인다 |
| TF | `/tf`, `/tf_static` | 모든 센서 프레임이 한 트리에 연결된다 |
| Odometry | `/odom` | 위치와 방향을 나타내는 화살표가 로봇을 따라간다 |
| Path | `/wheel_odom_path` | 주행 궤적이 선으로 누적된다 |
| LaserScan | `/scan` | 벽과 장애물 윤곽이 보인다 |
| Camera | `/camera/image` | RGB 영상이 갱신된다 |
| PointCloud2 | `/camera/points` | RGB-D 점군이 3차원으로 보인다 |
| IMU | `/imu` | IMU 자세 축이 갱신된다 |

토픽 자체도 독립적으로 확인한다.

```bash
ros2 topic echo /scan --field header --qos-reliability best_effort --once
ros2 topic echo /imu --qos-reliability best_effort --once
ros2 topic echo /camera/camera_info --qos-reliability best_effort --once
ros2 topic echo /camera/depth/image --field header --qos-reliability best_effort --once
ros2 topic echo /camera/points --field header --qos-reliability best_effort --once
```

영상과 CameraInfo의 프레임은 `camera_optical_frame`, RGB-D 점군 프레임은 `camera_link`여야 한다. PointCloud2와 LaserScan의 Reliability Policy는 `Best Effort`로 둔다. 점군이 단순히 보이는 것에 그치지 않고, 바닥은 수평이고 장애물은 실제 Gazebo 위치와 맞는지 확인한다. Camera 디스플레이가 오류라면 Image 디스플레이로 영상부터 확인하고 CameraInfo와 TF를 차례로 점검한다.

## 9. 완료 조건

다음 항목을 모두 확인하면 초급 프로젝트를 완료한 것이다.

- 키보드 조종 명령에 따라 로봇이 직진하고 회전한다.
- RTF가 1에 가까운 환경에서 `/odom`이 약 30 Hz로 발행되고 위치가 변한다.
- `/wheel_odom_path`의 위치 표본 수가 늘고 RViz에 궤적이 보인다.
- `odom → base_link → lidar_link/camera_optical_frame/imu_link` TF가 이어진다.
- `/scan`은 360개 거리 값을 포함한다.
- RGB 영상은 320×240이고 깊이 영상과 점군도 갱신된다.
- `/imu`와 `/clock`이 시뮬레이션 시간 기준으로 갱신된다.

## 10. 고장 진단 순서

### 로봇이 움직이지 않는다

`/diff_drive_controller/cmd_vel` 타입이 `TwistStamped`인지, teleop의 `stamped:=true`가 적용됐는지, 컨트롤러가 active인지 확인한다.

```bash
ros2 control list_controllers
ros2 topic info -v /diff_drive_controller/cmd_vel
```

### RViz 센서가 모두 오류 상태이다

Fixed Frame을 `odom`으로 설정하고 TF를 먼저 확인한다. 센서마다 따로 고치기 전에 공통 부모인 `base_link`까지의 좌표 변환을 확인한다.

### 카메라만 보이지 않는다

`ros_gz_image` 프로세스, `/tutorial_bot/camera/image` Gazebo 토픽, `/camera/image` ROS 토픽 순서로 확인한다. 서버의 `ogre2` 초기화 오류도 함께 확인한다.

### Path가 생기지 않는다

`/odom`에 메시지가 있는지, `odom_to_path` 노드가 실행 중인지, `minimum_translation`보다 충분히 이동했는지 확인한다.

## 종료하기

조종 터미널에서 `k`로 정지한 뒤 `Ctrl+C`로 종료한다. 이어서 launch 터미널에서 `Ctrl+C`를 누른다. launch가 실행한 Gazebo, 브리지, RViz도 함께 종료되는지 확인한다.

## 확장 과제

- `05-sensor-gallery.xacro`와 `bridge-sensor-gallery.yaml`로 단안·스테레오·어안 카메라와 3D 라이다를 동시에 관측한다.
- 바퀴 반지름을 의도적으로 10% 바꾸고 같은 명령에서 궤적 축척이 어떻게 달라지는지 비교한다.
- 중급 과정에서 `map → odom`과 Nav2 path를 바퀴 주행 궤적과 겹쳐 본다.

## 정리

초급 프로젝트는 모델, 컨트롤러, 센서, 브리지, TF, teleop, RViz를 하나의 데이터 흐름로 연결한다. 다음 단계에서는 실행 구성과 TF의 소유권, `gz_ros2_control`, Nav2를 더 엄격하게 다룬다.

[이전: ROS 2와 연결](10-ros-gz-bridge.md) · [다음: 중급 과정](../04_intermediate/index.md)
