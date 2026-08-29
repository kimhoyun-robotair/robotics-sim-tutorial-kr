# gz_ros2_control과 controller

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** TF·Joint State·RViz

## 학습 목표

- Gazebo joint, `gz_ros2_control`, controller manager의 관계를 설명한다.
- URDF command/state interface와 controller YAML을 함께 읽는다.
- 2륜·4륜 DiffDrive controller 구성을 작성한다.
- 4륜 skid-steer와 조향식 Ackermann의 기구학 및 구현 대안을 구분한다.
- 직접 Gazebo System과 `ros2_control` backend 중 하나를 선택한다.

## 제어 경로 두 가지

Harmonic에서 바퀴를 움직이는 방법은 크게 두 가지이다.

| 경로 | 명령 흐름 | 장점 | 적합한 경우 |
|---|---|---|---|
| Gazebo System | ROS `/cmd_vel` → `ros_gz_bridge` → DiffDrive/AckermannSteering System | 설정이 작고 빠르게 실습할 수 있다 | 모델·기구학·bridge 입문 |
| `gz_ros2_control` | ROS controller → command interface → `GazeboSimSystem` → joint | lifecycle, interface claim, controller 교체를 사용할 수 있다 | 실제 ROS 제어 구조와 가까운 통합 |

한 모델의 같은 joint에 두 backend를 동시에 연결하지 않는다. 현재 2륜 `tutorial_bot`은 Xacro 인자로 backend를 택하고, 4륜 rover 예제는 직접 Gazebo System을 사용한다.

## 1. URDF에서 simulated hardware 선언하기

`gz_ros2_control`은 URDF의 `<ros2_control>` 블록에 선언한 interface만 controller에 노출한다.

```xml
<ros2_control name="GazeboSimSystem" type="system">
  <hardware>
    <plugin>gz_ros2_control/GazeboSimSystem</plugin>
  </hardware>

  <joint name="left_wheel_joint">
    <command_interface name="position"/>
    <command_interface name="velocity"/>
    <command_interface name="effort"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
    <state_interface name="effort"/>
  </joint>

  <joint name="right_wheel_joint">
    <command_interface name="position"/>
    <command_interface name="velocity"/>
    <command_interface name="effort"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
    <state_interface name="effort"/>
  </joint>
</ros2_control>
```

Gazebo plugin은 controller YAML 위치와 ROS namespace를 받는다.

```xml
<gazebo>
  <plugin filename="gz_ros2_control-system"
          name="gz_ros2_control::GazeboSimROS2ControlPlugin">
    <parameters>$(arg controller_parameters_file)</parameters>
    <ros><namespace>$(arg ros_namespace)</namespace></ros>
  </plugin>
</gazebo>
```

Harmonic에서는 `gz_ros2_control-system`을 사용한다. Gazebo Classic의 `gazebo_ros2_control`과 다른 plugin이다.

## 2. 2륜 DiffDrive controller YAML

실행 기준 파일은 `examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`이다.

```yaml
controller_manager:
  ros__parameters:
    update_rate: 100
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

diff_drive_controller:
  ros__parameters:
    left_wheel_names: [left_wheel_joint]
    right_wheel_names: [right_wheel_joint]
    wheel_separation: 0.38
    wheel_radius: 0.06
    base_frame_id: base_link
    odom_frame_id: odom
    enable_odom_tf: true
    publish_rate: 30.0
    use_stamped_vel: true
```

`wheel_separation`과 `wheel_radius`는 Xacro 형상과 같아야 한다. radius가 5% 크게 설정되면 같은 encoder 회전량으로 계산한 선형 이동 거리도 약 5% 크게 나온다.

## 3. controller 활성화와 interface 확인

통합 launch가 `joint_state_broadcaster`와 `diff_drive_controller`를 활성화한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=false rviz:=false
```

다른 terminal에서 확인한다.

```bash
ros2 control list_controllers
ros2 control list_hardware_components
ros2 control list_hardware_interfaces
```

정상 상태에서는 두 controller가 `active`이고 wheel position·velocity state interface와 claimed velocity command interface가 보인다.

controller를 수동으로 전환할 때는 같은 command interface를 두 controller가 동시에 claim하지 않게 한다.

```bash
ros2 control switch_controllers \
  --deactivate diff_drive_controller \
  --activate joint_trajectory_controller \
  --strict

ros2 control switch_controllers \
  --deactivate joint_trajectory_controller \
  --activate diff_drive_controller \
  --strict
```

## 4. 2륜 차동구동 운동학

오른쪽·왼쪽 바퀴 각속도를 \(\omega_r,\omega_l\), 반지름을 \(r\), 바퀴 간격을 \(L\)이라 하면 다음과 같다.

\[
v=\frac{r}{2}(\omega_r+\omega_l),\qquad
\Omega=\frac{r}{L}(\omega_r-\omega_l)
\]

<figure class="course-figure" id="intermediate-controller-kinematics">
  <img src="../../assets/intermediate/controller-kinematics.svg" alt="차동구동 바퀴 운동학과 controller lifecycle 상태도" loading="lazy">
  <figcaption>그림 1. 바퀴 속도는 차체의 선속도와 각속도로 변환되고 lifecycle이 interface 소유권을 제한한다.</figcaption>
</figure>

## 계산 예제: 바퀴 속도에서 차체 속도로

<div class="course-worked" data-worked-example="controller-kinematics">
반지름 \(r=0.06\,\mathrm{m}\), 바퀴 간격 \(L=0.38\,\mathrm{m}\), \(\omega_r=8\), \(\omega_l=4\,\mathrm{rad/s}\)이면 \(v=r(\omega_r+\omega_l)/2=0.36\,\mathrm{m/s}\), \(\Omega=r(\omega_r-\omega_l)/L=0.632\,\mathrm{rad/s}\)이다. trajectory controller를 활성화하기 전에 DiffDrive를 비활성화해야 같은 command interface의 중복 claim을 피할 수 있다.
</div>

## 5. 실제 4륜 skid-steer DiffDrive 예제

4륜 공통 형상은 `examples/ros2_ws/src/tutorial_bot_description/urdf/macros/rover_components.xacro`에 있다. top-level `examples/ros2_ws/src/tutorial_bot_description/urdf/rovers/rover_diff.urdf.xacro`는 같은 wheel macro를 네 번 호출한다.

```xml
<xacro:include filename="../macros/rover_components.xacro"/>
<xacro:rover_chassis/>
<xacro:fixed_axle_wheel prefix="front_left"
    x="${rover_wheelbase / 2.0}" y="${rover_track_width / 2.0}"/>
<xacro:fixed_axle_wheel prefix="front_right"
    x="${rover_wheelbase / 2.0}" y="-${rover_track_width / 2.0}"/>
<xacro:fixed_axle_wheel prefix="rear_left"
    x="-${rover_wheelbase / 2.0}" y="${rover_track_width / 2.0}"/>
<xacro:fixed_axle_wheel prefix="rear_right"
    x="-${rover_wheelbase / 2.0}" y="-${rover_track_width / 2.0}"/>
```

Harmonic DiffDrive System은 `<left_joint>`와 `<right_joint>`를 반복해서 받을 수 있다. 같은 편의 앞·뒤 바퀴를 각각 두 번 선언한다.

```xml
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>front_left_wheel_joint</left_joint>
  <left_joint>rear_left_wheel_joint</left_joint>
  <right_joint>front_right_wheel_joint</right_joint>
  <right_joint>rear_right_wheel_joint</right_joint>
  <wheel_separation>${rover_track_width}</wheel_separation>
  <wheel_radius>${rover_wheel_radius}</wheel_radius>
  <odom_publish_frequency>30</odom_publish_frequency>
  <topic>/model/$(arg model_name)/cmd_vel</topic>
  <odom_topic>/model/$(arg model_name)/odometry</odom_topic>
</plugin>
```

이 방식은 네 바퀴 모두 조향 joint 없이 고정하고 좌우 속도 차이로 회전한다. 회전 중 횡방향 slip이 필수이므로 타이어 마찰과 wheel odometry 오차를 실제 관찰로 조정해야 한다.

실행과 teleop은 다음과 같다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

RViz에서 `/odom`과 `/wheel_odom_path`가 회전 궤적을 그리는지 확인한다.

## 6. 실제 AckermannSteering 예제

Ackermann 모델은 앞바퀴에 z축 steering joint를 하나씩 만들고, 각 knuckle 아래에 wheel joint를 둔다.

```xml
<joint name="front_left_steering_joint" type="revolute">
  <parent link="base_link"/>
  <child link="front_left_knuckle_link"/>
  <origin xyz="0.28 0.31 -0.07" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-0.70" upper="0.70" effort="40" velocity="2.0"/>
</joint>

<joint name="front_left_wheel_joint" type="continuous">
  <parent link="front_left_knuckle_link"/>
  <child link="front_left_wheel_link"/>
  <axis xyz="0 1 0"/>
</joint>
```

실제 top-level 파일 `examples/ros2_ws/src/tutorial_bot_description/urdf/rovers/rover_ackermann.urdf.xacro`는 뒤 좌우 바퀴를 traction joint로, 앞 좌우 joint를 steering joint로 지정한다.

```xml
<plugin filename="gz-sim-ackermann-steering-system"
        name="gz::sim::systems::AckermannSteering">
  <left_joint>rear_left_wheel_joint</left_joint>
  <right_joint>rear_right_wheel_joint</right_joint>
  <left_steering_joint>front_left_steering_joint</left_steering_joint>
  <right_steering_joint>front_right_steering_joint</right_steering_joint>
  <wheel_separation>${rover_track_width}</wheel_separation>
  <kingpin_width>${rover_track_width}</kingpin_width>
  <wheel_base>${rover_wheelbase}</wheel_base>
  <wheel_radius>${rover_wheel_radius}</wheel_radius>
  <steering_limit>0.60</steering_limit>
  <odom_publish_frequency>30</odom_publish_frequency>
</plugin>
```

`wheel_separation`은 구동 바퀴 중심 간격, `kingpin_width`는 실제 조향축 사이 거리, `wheel_base`는 앞·뒤 차축 간 거리이다. 이 모델에서는 앞 조향축이 `y=±0.31 m`에 있으므로 앞의 두 값은 모두 0.62 m이고, wheelbase는 0.56 m, 바퀴 반지름은 0.10 m이다. Xacro의 joint 위치를 바꾸면 플러그인의 기하 파라미터도 같은 값으로 바꿔야 한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

같은 unstamped `/cmd_vel` teleop을 사용한다. `angular.z`는 제자리 회전 명령이 아니라 주행 곡률로 해석되므로 속도가 0이면 skid-steer처럼 제자리에서 돌지 않는다.

## 7. Ackermann을 `ros2_control`로 바꾸는 대안

실제 rover 예제는 Harmonic AckermannSteering System을 사용한다. 실제 하드웨어와 같은 controller manager 구조가 필요하면 뒤 traction joint에는 velocity command, 앞 steering joint에는 position command interface를 선언하고 Jazzy의 Ackermann controller를 선택한다.

```yaml
controller_manager:
  ros__parameters:
    ackermann_controller:
      type: ackermann_steering_controller/AckermannSteeringController

ackermann_controller:
  ros__parameters:
    traction_joints_names:
      [rear_right_wheel_joint, rear_left_wheel_joint]
    steering_joints_names:
      [front_right_steering_joint, front_left_steering_joint]
    traction_wheels_radius: 0.10
    traction_track_width: 0.62
    steering_track_width: 0.62
    wheelbase: 0.56
    base_frame_id: base_footprint
    odom_frame_id: odom
    enable_odom_tf: true
    position_feedback: false
```

Jazzy controller의 reference 입력은 `geometry_msgs/msg/TwistStamped`이고 기본 topic은 `/<controller_name>/reference`이다. 직접 Gazebo System의 입력은 bridge된 `geometry_msgs/msg/Twist`이다. 따라서 backend를 바꿀 때는 plugin만 바꾸지 말고 URDF interface, controller type, input type·topic, odometry·TF 소유자를 함께 바꿔야 한다.

!!! note "top-level Xacro를 분리한 이유"
    `rover_diff.urdf.xacro`와 `rover_ackermann.urdf.xacro`는 공통 형상 macro만 공유하고 drive System은 따로 선언한다. DiffDrive와 AckermannSteering을 한 모델에 동시에 load하면 같은 바퀴에 두 System이 명령하므로 올바른 비교가 아니다.

## 문제 해결

- `gz_ros2_control` package를 찾지 못하면 `ros-jazzy-gz-ros2-control` 설치와 `package.xml` 의존성을 확인한다.
- controller가 `inactive`에서 멈추면 joint 이름, command interface, 이미 claim한 controller를 확인한다.
- `/cmd_vel`을 발행해도 2륜 로봇이 움직이지 않으면 Jazzy DiffDrive가 요구하는 stamped input과 remap을 확인한다.
- 4륜 skid가 회전하지 않으면 앞·뒤 joint가 양쪽 목록에 모두 들어갔는지와 횡마찰을 확인한다.
- Ackermann 앞바퀴 방향이 반대면 steering joint z축과 joint limit 부호를 확인한다.
- odometry가 두 번 발행되면 controller/System의 odom·TF 소유자가 중복되지 않았는지 확인한다.

## 정리

`gz_ros2_control`은 Gazebo joint를 ROS controller interface로 노출하고 lifecycle과 interface 소유권을 제공한다. 빠른 Gazebo 기구학 실습에는 직접 DiffDrive/AckermannSteering System이 적합하고, controller 전환과 실제 하드웨어 호환 구조에는 `gz_ros2_control`이 적합하다. 어느 경로를 택하든 geometry, command type, odometry, TF 계약을 한 묶음으로 맞춰야 한다.

[이전: TF·Joint State·RViz](06-tf-rviz.md) · [다음: 센서 심화](08-advanced-sensors.md)
