# gz_ros2_control과 컨트롤러

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** TF·Joint State·RViz

## 학습 목표

- Gazebo 조인트, `gz_ros2_control`, 컨트롤러 관리자의 관계를 설명한다.
- URDF의 명령·상태 인터페이스와 컨트롤러 YAML을 함께 읽는다.
- 2륜·4륜 DiffDrive 컨트롤러 구성을 작성한다.
- 4륜 스키드 조향과 조향식 Ackermann의 기구학 및 구현 대안을 구분한다.
- 직접 Gazebo 시스템 플러그인과 `ros2_control` 제어 방식 중 하나를 선택한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## 제어 경로 두 가지

Harmonic에서 바퀴를 움직이는 방법은 크게 두 가지이다.

| 경로 | 명령 흐름 | 장점 | 적합한 경우 |
|---|---|---|---|
| Gazebo 시스템 플러그인 | ROS `/cmd_vel` → `ros_gz_bridge` → DiffDrive/AckermannSteering 시스템 플러그인 | 설정이 작고 빠르게 실습할 수 있다 | 모델·기구학·브리지 입문 |
| `gz_ros2_control` | ROS 컨트롤러 → 명령 인터페이스 → `GazeboSimSystem` → 조인트 | 수명주기, 인터페이스 점유, 컨트롤러 교체를 사용할 수 있다 | 실제 ROS 제어 구조와 가까운 통합 |

한 모델의 같은 조인트에 두 제어 방식을 동시에 연결하지 않는다. 현재 2륜 `tutorial_bot`은 Xacro 인자로 제어 방식을 택하고, 4륜 로버 예제는 직접 Gazebo 시스템 플러그인을 사용한다.

## 1. 시뮬레이션용 하드웨어 선언하기

`gz_ros2_control`은 URDF의 `<ros2_control>` 블록에 선언한 인터페이스만 컨트롤러에 노출한다.

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

Gazebo 플러그인은 컨트롤러 YAML 위치와 ROS 네임스페이스를 받는다.

```xml
<gazebo>
  <plugin filename="gz_ros2_control-system"
          name="gz_ros2_control::GazeboSimROS2ControlPlugin">
    <parameters>$(arg controller_parameters_file)</parameters>
    <ros><namespace>$(arg ros_namespace)</namespace></ros>
  </plugin>
</gazebo>
```

Harmonic에서는 `gz_ros2_control-system`을 사용한다. Gazebo Classic의 `gazebo_ros2_control`과 다른 플러그인이다.

## 2. 2륜 DiffDrive 컨트롤러 YAML

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
```

`wheel_separation`과 `wheel_radius`는 Xacro 형상과 같아야 한다. 바퀴 반지름이 5% 크게 설정되면 같은 바퀴 회전량으로 계산한 이동 거리도 약 5% 크게 나온다.

Jazzy의 DiffDrive 입력은 `~/cmd_vel`의 `geometry_msgs/msg/TwistStamped`이다. 예전 배포판의 `use_stamped_vel` 파라미터로 타입을 바꾸지 않는다. [Jazzy DiffDrive 공식 문서](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)에서 입력 타입을 확인할 수 있다.

## 3. 컨트롤러 활성화와 인터페이스 확인

통합 launch가 `joint_state_broadcaster`와 `diff_drive_controller`를 활성화한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=false rviz:=false
```

다른 터미널에서 확인한다.

```bash
ros2 control list_controllers
ros2 control list_hardware_components
ros2 control list_hardware_interfaces
```

정상 상태에서는 두 컨트롤러가 `active`이다. `list_hardware_interfaces`에는 바퀴의 `position`, `velocity` 상태와, DiffDrive가 사용 중인 `velocity [claimed]` 명령 인터페이스가 보인다.

launch는 `joint_trajectory_controller`를 미리 불러오되 `inactive`로 둔다. 다음은 DiffDrive와 궤적 컨트롤러를 교대로 켜는 실습이다. 키보드 조종을 종료하고 로봇이 멈춘 뒤 실행한다. 궤적 컨트롤러를 켜는 동안에는 DiffDrive의 `/odom`과 `odom → base_link` 발행도 중단된다.

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
  <figcaption>그림 1. 바퀴 속도는 차체의 선속도와 각속도로 변환되고 수명주기가 인터페이스 소유권을 제한한다.</figcaption>
</figure>

## 계산 예제: 바퀴 속도에서 차체 속도로

<div class="course-worked" data-worked-example="controller-kinematics">
반지름 \(r=0.06\,\mathrm{m}\), 바퀴 간격 \(L=0.38\,\mathrm{m}\), \(\omega_r=8\), \(\omega_l=4\,\mathrm{rad/s}\)이면 \(v=r(\omega_r+\omega_l)/2=0.36\,\mathrm{m/s}\), \(\Omega=r(\omega_r-\omega_l)/L=0.632\,\mathrm{rad/s}\)이다. 이 예제의 DiffDrive는 속도를, 궤적 컨트롤러는 위치를 명령한다. 인터페이스 이름이 달라도 같은 바퀴에 서로 다른 방식으로 명령하지 않도록 한 번에 한 컨트롤러만 활성화한다.
</div>

## 5. 실제 4륜 스키드 조향 DiffDrive 예제

4륜 공통 형상은 `examples/ros2_ws/src/tutorial_bot_description/urdf/macros/rover_components.xacro`에 있다. 최상위 `examples/ros2_ws/src/tutorial_bot_description/urdf/rovers/rover_diff.urdf.xacro`는 같은 바퀴 매크로를 네 번 호출한다.

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

Harmonic DiffDrive 시스템 플러그인은 `<left_joint>`와 `<right_joint>`를 반복해서 받을 수 있다. 같은 편의 앞·뒤 바퀴를 각각 두 번 선언한다.

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

이 방식은 네 바퀴 모두 조향 조인트 없이 고정하고 좌우 속도 차이로 회전한다. 회전 중 횡방향 미끄럼이 필수이므로 타이어 마찰과 바퀴 오도메트리 오차를 실제 관찰로 조정해야 한다.

실행과 키보드 조종은 다음과 같다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
```

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/cmd_vel
```

RViz에서 `/odom`과 `/wheel_odom_path`가 회전 궤적을 그리는지 확인한다.

## 6. 실제 AckermannSteering 예제

Ackermann 모델은 앞바퀴에 z축 조향 조인트를 하나씩 만들고, 각 조향 연결부(knuckle) 아래에 바퀴 조인트를 둔다.

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

실제 최상위 파일 `examples/ros2_ws/src/tutorial_bot_description/urdf/rovers/rover_ackermann.urdf.xacro`는 뒤 좌우 바퀴를 구동 조인트로, 앞 좌우 조인트를 조향 조인트로 지정한다.

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

`wheel_separation`은 구동 바퀴 중심 간격, `kingpin_width`는 실제 조향축 사이 거리, `wheel_base`는 앞·뒤 차축 간 거리이다. 이 모델에서는 앞 조향축이 `y=±0.31 m`에 있으므로 앞의 두 값은 모두 0.62 m이고, 축간 거리는 0.56 m, 바퀴 반지름은 0.10 m이다. Xacro의 조인트 위치를 바꾸면 플러그인의 기하 파라미터도 같은 값으로 바꿔야 한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

`Twist` 타입의 `/cmd_vel`을 보내는 같은 키보드 조종 명령을 사용한다. `linear.x`는 전진 속도(m/s), `angular.z`는 요 각속도(rad/s)이다. 조향각 자체를 보내는 것이 아니다. 플러그인은 두 값으로 회전반경을 계산하므로 전진 속도가 0이면 차동구동처럼 제자리에서 돌 수 없다. `u`, `o`로 전진과 회전을 함께 입력해 앞바퀴 조향을 확인한다.

## 7. Ackermann을 `ros2_control`로 바꾸는 대안

실제 로버 예제는 Harmonic AckermannSteering 시스템 플러그인을 사용한다. 실제 하드웨어와 같은 컨트롤러 관리자 구조가 필요하면 뒤 구동 조인트에는 속도 명령, 앞 조향 조인트에는 위치 명령 인터페이스를 선언하고 Jazzy의 Ackermann 컨트롤러를 선택한다.

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

위 YAML은 제어 방식을 바꿀 때 참고하는 설정 예시이며, 그대로 실행할 수 있는 별도 launch는 제공하지 않는다. [Jazzy Ackermann 컨트롤러 공식 문서](https://control.ros.org/jazzy/doc/ros2_controllers/ackermann_steering_controller/doc/userdoc.html)를 함께 확인한다.

Jazzy 컨트롤러의 기준 속도 입력은 `geometry_msgs/msg/TwistStamped`이고 기본 토픽은 `/<controller_name>/reference`이다. 직접 Gazebo 시스템 플러그인의 입력은 브리지된 `geometry_msgs/msg/Twist`이다. 따라서 제어 방식을 바꿀 때는 플러그인만 바꾸지 말고 URDF 인터페이스, 컨트롤러 타입, 입력 타입·토픽, 오도메트리·TF 소유자를 함께 바꿔야 한다.

!!! note "최상위 Xacro를 분리한 이유"
    `rover_diff.urdf.xacro`와 `rover_ackermann.urdf.xacro`는 공통 형상 매크로만 공유하고 구동 시스템 플러그인은 따로 선언한다. DiffDrive와 AckermannSteering을 한 모델에 동시에 불러오면 같은 바퀴에 두 시스템 플러그인이 명령하므로 올바른 비교가 아니다.

## 문제 해결

- `gz_ros2_control` 패키지를 찾지 못하면 `ros-jazzy-gz-ros2-control` 설치와 `package.xml` 의존성을 확인한다.
- 컨트롤러가 `inactive`에서 멈추면 조인트 이름, 명령 인터페이스, 이미 점유한 컨트롤러를 확인한다.
- `/cmd_vel`을 발행해도 2륜 로봇이 움직이지 않으면 Jazzy DiffDrive가 요구하는 `TwistStamped` 입력과 토픽 이름 재지정을 확인한다.
- 4륜 스키드 조향 로버가 회전하지 않으면 앞·뒤 조인트가 양쪽 목록에 모두 들어갔는지와 횡마찰을 확인한다.
- Ackermann 앞바퀴 방향이 반대면 조향 조인트 z축과 조인트 각도 제한의 부호를 확인한다.
- 오도메트리가 두 번 발행되면 컨트롤러와 Gazebo 플러그인의 오도메트리·TF 발행 노드가 중복되지 않았는지 확인한다.

## 정리

`gz_ros2_control`은 Gazebo 조인트를 ROS 컨트롤러 인터페이스로 노출하고 수명주기와 인터페이스 소유권을 제공한다. 빠른 Gazebo 기구학 실습에는 직접 DiffDrive/AckermannSteering 시스템 플러그인이 적합하고, 컨트롤러 전환과 실제 하드웨어 호환 구조에는 `gz_ros2_control`이 적합하다. 어느 경로를 택하든 형상, 명령 타입, 오도메트리, TF 설정을 함께 맞춰야 한다.

[이전: TF·Joint State·RViz](06-tf-rviz.md) · [다음: 센서 심화](08-advanced-sensors.md)
