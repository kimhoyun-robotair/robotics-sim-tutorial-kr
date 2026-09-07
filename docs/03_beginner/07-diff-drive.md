# DiffDrive로 `tutorial_bot` 움직이기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [2륜과 캐스터 바퀴](06-joints.md)

## 학습 목표

- Gazebo DiffDrive 시스템의 실제 플러그인 태그와 주요 파라미터를 설명한다.
- 좌우 바퀴 각속도에서 로봇 선속도와 각속도를 계산한다.
- Gazebo Transport와 ROS 2를 bridge해 키보드 조종으로 주행한다.
- 바퀴 오도메트리를 `/wheel_odom_path`로 누적하고 RViz에서 궤적을 확인한다.

## 3단계 Xacro와 DiffDrive 시스템

`03-diff-drive.xacro`는 차체, 좌우 바퀴와 캐스터, DiffDrive 플러그인을 차례로 조립한다.

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="tutorial_bot">
  <xacro:include filename="../macros/stage_components.xacro"/>
  <xacro:stage_base/>
  <xacro:stage_wheels/>
  <xacro:stage_diff_drive/>
</robot>
```

`stage_diff_drive`의 실제 플러그인 정의는 다음과 같다.

```xml
<xacro:macro name="stage_diff_drive" params="model_name:=tutorial_bot">
  <gazebo>
    <plugin filename="gz-sim-diff-drive-system"
            name="gz::sim::systems::DiffDrive">
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.38</wheel_separation>
      <wheel_radius>0.06</wheel_radius>
      <odom_publish_frequency>30</odom_publish_frequency>
      <frame_id>odom</frame_id>
      <child_frame_id>base_link</child_frame_id>
    </plugin>
    <plugin filename="gz-sim-joint-state-publisher-system"
            name="gz::sim::systems::JointStatePublisher">
      <topic>/model/${model_name}/joint_state</topic>
      <update_rate>30</update_rate>
      <joint_name>left_wheel_joint</joint_name>
      <joint_name>right_wheel_joint</joint_name>
    </plugin>
  </gazebo>
</xacro:macro>
```

`<gazebo>` 블록은 URDF 표준 링크·조인트 바깥의 시뮬레이터 확장이다. Gazebo가 URDF를 SDF로 변환할 때 모델 수준 `<plugin>`으로 옮긴다. DiffDrive는 좌우 `continuous` 조인트만 제어하며 `caster_joint`는 구동 목록에 넣지 않는다. JointStatePublisher는 두 바퀴 조인트의 현재 각도를 내보내 ROS의 바퀴 TF가 갱신되게 한다. 현재 [Harmonic API](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1JointStatePublisher.html)의 `update_rate`는 발행률의 상한이다. 오래된 세부 버전에서 값이 적용되지 않는다면 실제 발행률을 확인하고 Jazzy 패키지를 갱신한다.

## DiffDrive 파라미터 읽기

| 파라미터 | 이 예제 값 | 의미 |
|---|---:|---|
| `left_joint` | `left_wheel_joint` | 왼쪽 구동 바퀴 조인트이다. 여러 왼쪽 바퀴라면 태그를 반복할 수 있다. |
| `right_joint` | `right_wheel_joint` | 오른쪽 구동 바퀴 조인트이다. 여러 오른쪽 바퀴라면 태그를 반복할 수 있다. |
| `wheel_separation` | `0.38` m | 좌우 바퀴 중심 사이 거리이다. 생략 시 기본값은 1.0 m이다. |
| `wheel_radius` | `0.06` m | 구동 바퀴 반지름이다. 생략 시 기본값은 0.2 m이다. |
| `odom_publish_frequency` | `30` Hz | 바퀴 회전으로 계산한 오도메트리 발행 주기이다. 기본값은 50 Hz이다. |
| `frame_id` | `odom` | 오도메트리 위치와 자세의 기준 프레임이다. |
| `child_frame_id` | `base_link` | 오도메트리가 추정하는 로봇 몸체 프레임이다. |

다음 선택 파라미터를 추가하면 토픽, 프레임, 속도 제한을 명시적으로 고정할 수 있다.

```xml
<topic>/model/tutorial_bot/cmd_vel</topic>
<odom_topic>/model/tutorial_bot/odometry</odom_topic>
<tf_topic>/model/tutorial_bot/tf</tf_topic>
<max_linear_velocity>0.8</max_linear_velocity>
<max_angular_velocity>2.0</max_angular_velocity>
<max_linear_acceleration>1.0</max_linear_acceleration>
<max_angular_acceleration>3.0</max_angular_acceleration>
```

`topic`, `odom_topic`, `tf_topic`을 생략하면 모델 이름을 사용한 `/model/tutorial_bot/...` 기본 토픽이 만들어진다. 반면 이 예제는 `frame_id=odom`, `child_frame_id=base_link`를 명시해 ROS 메시지와 RViz 설정의 프레임 이름을 고정한다.

## 먼저 자동 검증하기

설치된 3단계 Xacro를 전개하고 세 운동을 독립적으로 검증한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/03-diff-drive.xacro"
xacro "$stage" > /tmp/tutorial_bot-stage-03.urdf
check_urdf /tmp/tutorial_bot-stage-03.urdf
./scripts/check_diff_drive.sh \
  --scenarios straight,arc,spin \
  --evidence /tmp/tutorial-diff-drive-evidence
```

검사 스크립트는 scenario마다 새 월드를 시작하고 실제 오도메트리를 읽는다. `straight`는 양의 x와 작은 y·yaw, `arc`는 양의 x·y·yaw, `spin`은 작은 x·y와 양의 yaw를 요구한다.

## 바퀴 속도와 로봇 속도

왼쪽과 오른쪽 바퀴 각속도를 각각 $\omega_L$, $\omega_R$라 하면 로봇 중심의 선속도 $v$와 반시계 방향 각속도 $\omega$는 다음과 같다.

\[
v=\frac{r}{2}(\omega_R+\omega_L),\qquad
\omega=\frac{r}{L}(\omega_R-\omega_L)
\]

원하는 로봇 속도를 바퀴 속도로 바꾸는 역기구학은 다음과 같다.

\[
\omega_R=\frac{v+L\omega/2}{r},\qquad
\omega_L=\frac{v-L\omega/2}{r}
\]

??? note "역기구학 식 유도"
    첫 두 식에서 $2v/r=\omega_R+\omega_L$, $L\omega/r=\omega_R-\omega_L$를 얻는다. 두 식을 더하고 빼면 오른쪽과 왼쪽 바퀴 식이 각각 나온다.

이 예제는 $r=0.06\,\mathrm{m}$, $L=0.38\,\mathrm{m}$를 사용한다.

<figure markdown="span">
  ![좌우 바퀴 속도 조합에 따른 직진, 원호, 제자리 회전 궤적](../assets/beginner/diff-drive-trajectories.svg)
  <figcaption>그림 3. 같은 속도는 직진, 서로 다른 양의 속도는 원호, 반대 속도는 제자리 회전을 만든다.</figcaption>
</figure>

### 직진 계산

$v=0.24\,\mathrm{m/s}$, $\omega=0$이면 두 바퀴 속도는 같다.

\[
\omega_R=\omega_L=\frac{0.24}{0.06}=4.00\,\mathrm{rad/s}
\]

### 왼쪽 원호 계산

$v=0.18\,\mathrm{m/s}$, $\omega=0.60\,\mathrm{rad/s}$이면 다음 값을 얻는다.

\[
\omega_R=\frac{0.18+0.38(0.60)/2}{0.06}=4.90\,\mathrm{rad/s}
\]

\[
\omega_L=\frac{0.18-0.38(0.60)/2}{0.06}=1.10\,\mathrm{rad/s}
\]

오른쪽 바퀴가 더 빠르므로 로봇은 왼쪽으로 돌고, 순간 회전 반지름은 $R=v/\omega=0.30\,\mathrm{m}$이다.

### 제자리 회전 계산

$v=0$, $\omega=1.00\,\mathrm{rad/s}$이면 다음과 같다.

\[
\omega_R=+3.17\,\mathrm{rad/s},\qquad
\omega_L=-3.17\,\mathrm{rad/s}
\]

두 바퀴가 반대 방향으로 돌기 때문에 중심 이동은 작고 yaw만 증가한다.

## 통합 실습: 로봇 생성부터 키보드 조종까지

앞 장의 Gazebo를 모두 종료한 뒤 시작한다. 여기서는 프로그램별 역할을 익히기 위해 터미널을 나눈다. 각 터미널은 계속 실행해 두고 다음 번호의 터미널을 새로 연다. 먼저 예제 패키지를 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
colcon build --symlink-install
source install/setup.bash
cd ../..
```

### 터미널 1: 월드 실행

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
gz sim -r examples/gazebo/worlds/first-world.sdf
```

### 터미널 2: 3단계 로봇 생성

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/03-diff-drive.xacro"
xacro "$stage" > /tmp/tutorial_bot-stage-03.urdf
gz sdf -p /tmp/tutorial_bot-stage-03.urdf > /tmp/tutorial_bot-stage-03.sdf

model_sdf=/tmp/tutorial_bot-stage-03.sdf
gz service -s /world/first_world/create \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 3000 \
  --req "sdf_filename: \"$model_sdf\" pose { position { z: 0.12 } }"

gz topic -l | grep '/model/tutorial_bot/'

ros2 run robot_state_publisher robot_state_publisher \
  /tmp/tutorial_bot-stage-03.urdf --ros-args -p use_sim_time:=true
```

목록에 `/model/tutorial_bot/cmd_vel`, `/model/tutorial_bot/odometry`, `/model/tutorial_bot/joint_state`가 나타나야 한다. 마지막 명령은 URDF를 ROS에 제공하고, 브리지된 `/joint_states`를 받아 바퀴 TF를 갱신한 채 실행 상태를 유지한다.

### 터미널 3: Gazebo와 ROS 2 브리지 실행

실제 `bridge.yaml`은 명령과 오도메트리 방향을 다음처럼 분리한다.

```yaml
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

- ros_topic_name: "/joint_states"
  gz_topic_name: "/model/tutorial_bot/joint_state"
  ros_type_name: "sensor_msgs/msg/JointState"
  gz_type_name: "gz.msgs.Model"
  direction: GZ_TO_ROS
```

YAML 브리지를 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 run ros_gz_bridge parameter_bridge --ros-args \
  -p config_file:="$PWD/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml"
```

### 터미널 4: 바퀴 오도메트리를 Path로 누적

`odom_to_path`는 `/odom`의 위치와 자세를 최소 0.01 m 간격으로 최대 2,000개 저장하고 `nav_msgs/msg/Path`를 발행한다.

```python
self.declare_parameter("odom_topic", "/odom")
self.declare_parameter("path_topic", "/wheel_odom_path")
self.declare_parameter("max_poses", 2000)
self.declare_parameter("minimum_translation", 0.01)
```

별도 터미널에서 노드를 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 run tutorial_bot_bringup odom_to_path --ros-args \
  -p use_sim_time:=true \
  -p odom_topic:=/odom \
  -p path_topic:=/wheel_odom_path \
  -p max_poses:=2000 \
  -p minimum_translation:=0.01
```

### 터미널 5: 키보드 조종 실행

필요하면 `sudo apt install ros-jazzy-teleop-twist-keyboard`로 패키지를 설치한다. 실행한 터미널을 클릭해 키보드 입력이 그 창으로 전달되게 한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p speed:=0.2 -p turn:=0.6 \
  -p repeat_rate:=10.0 -p key_timeout:=0.6 \
  -r cmd_vel:=/cmd_vel
```

`i`를 누르고 있으면 전진하고 `j`·`l`은 제자리 회전, `k`는 정지이다. 키를 놓으면 `key_timeout` 뒤 정지 명령을 보낸다. 이 모드에서 teleop은 `geometry_msgs/msg/Twist`를 발행하고, 브리지가 같은 형식의 Gazebo Twist로 변환한다.

## RViz에서 바퀴 주행 궤적 확인하기

새 터미널에서 저장소의 RViz 설정을 연다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
rviz2 -d "$(ros2 pkg prefix --share tutorial_bot_bringup)/rviz/tutorial_bot.rviz" \
  --ros-args -p use_sim_time:=true
```

이 단계는 센서가 없으므로 RViz 왼쪽 목록에서 LiDAR, Camera, IMU, PointCloud2 디스플레이의 체크를 끈다. RobotModel, TF, Wheel Odometry, Wheel Odom Trajectory를 확인한다. 설정에는 다음 두 주행 디스플레이가 들어 있다.

```yaml
- Class: rviz_default_plugins/Odometry
  Name: Wheel Odometry
  Keep: 1000
  Topic:
    Value: /odom

- Class: rviz_default_plugins/Path
  Name: Wheel Odom Trajectory
  Line Style: Lines
  Line Width: 0.03
  Topic:
    Value: /wheel_odom_path
```

이 예제의 DiffDrive는 odom 프레임을 `odom`으로 명시하고 RViz Fixed Frame도 `odom`으로 설정한다. `No transform`이 나오면 먼저 실제 메시지의 프레임을 읽어 설정과 같은지 확인한다.

```bash
ros2 topic echo --once /odom nav_msgs/msg/Odometry | sed -n '1,12p'
```

이 예제에서는 `header.frame_id: odom`, `child_frame_id: base_link`가 나와야 한다. 다른 이름이면 다른 모델이나 이전 브리지가 실행 중인지 먼저 확인한다. 의도적으로 프레임 이름을 바꿨다면 플러그인과 TF, RViz 설정도 함께 맞춘다. teleop으로 사각형이나 원을 주행하면 `Wheel Odometry` 화살표가 누적되고 `Wheel Odom Trajectory` 선이 같은 경로를 잇는다.

토픽 수준에서도 누적 여부를 확인한다. `ros2 topic hz`는 계속 실행되므로 수치를 읽은 뒤 `Ctrl+C`를 눌러 다음 명령으로 넘어간다.

```bash
ros2 topic hz /odom
ros2 topic echo --once /wheel_odom_path nav_msgs/msg/Path
```

실시간 계수(RTF)가 1에 가까우면 `/odom`은 약 30 Hz이고, 움직인 뒤 `poses` 배열이 둘 이상이면 정상이다. 이 궤적은 참값이 아니라 바퀴 회전으로 적분한 오도메트리이므로 미끄러짐이 생기면 실제 Gazebo 위치·자세와 차이가 누적될 수 있다.

!!! tip "한 번에 실행하는 통합 실행 구성"
    최종 모델과 `gz_ros2_control`, TF, RViz를 함께 확인하려면 `ros2 launch tutorial_bot_bringup simulation.launch.py nav2:=false gui:=true rviz:=true`를 사용한다. 이 실행 구성도 `/odom`을 `odom_to_path`에 연결해 `/wheel_odom_path`를 발행한다. 이 경우 `diff_drive_controller`는 `TwistStamped`를 받으므로 [초급 프로젝트의 키보드 조종 명령](11_project-tutorial-bot.md)을 사용한다. 먼저 이 장에서 실행한 Gazebo, 브리지, 상태 발행자, RViz를 종료해 중복 발행을 막는다.

## Gazebo Transport에서 직접 명령하기

브리지를 거치지 않고 플러그인만 분리해 확인하려면 다음과 같이 왼쪽 원호 명령을 보낸다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.18} angular: {z: 0.60}'
gz topic -e -t /model/tutorial_bot/odometry -n 1
# 관찰 후 정지 명령을 보낸다.
gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist \
  -p 'linear: {x: 0.0} angular: {z: 0.0}'
```

ROS 경로가 실패할 때 이 명령이 동작하면 DiffDrive는 정상이고 브리지 또는 ROS 토픽 설정에 문제가 있다는 뜻이다.

## 문제 해결

- Gazebo 명령 토픽이 없으면 3단계 Xacro에 DiffDrive 플러그인이 있고 spawn 서비스가 `data: true`를 반환했는지 확인한다.
- ROS `/cmd_vel`에 구독자가 없으면 `bridge.yaml` 경로와 `direction: ROS_TO_GZ`를 확인한다.
- 직진 명령인데 회전하면 바퀴 간격과 반지름뿐 아니라 left/right 조인트 매핑을 확인한다.
- 왼쪽 원호가 오른쪽으로 휘면 `left_joint`와 `right_joint`가 뒤바뀌었을 가능성이 크다.
- `/odom`은 있지만 Path가 비어 있으면 `odom_to_path`가 실행 중인지와 `minimum_translation`보다 멀리 움직였는지 확인한다.
- RViz에 Path가 보이지 않으면 `/wheel_odom_path`의 `header.frame_id`, RViz Fixed Frame, `use_sim_time`을 함께 확인한다.

[다음: Gazebo 센서](08-sensors.md)
