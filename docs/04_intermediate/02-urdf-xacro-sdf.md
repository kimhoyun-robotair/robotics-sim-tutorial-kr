# URDF·Xacro·SDF 구분

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 고급 SDF

## 학습 목표

- URDF, Xacro, SDF가 실제 코드에서 맡는 책임을 구분한다.
- Xacro `include`와 `macro`로 바퀴·센서 구성을 재사용한다.
- 하나의 robot description 원본을 유지한다.
- Xacro를 URDF로 펼치고 SDF 변환 결과까지 검사한다.

## 같은 로봇을 세 관점으로 읽기

| 형식 | 잘 표현하는 것 | 이 저장소의 사용 위치 | 직접 실행하는가 |
|---|---|---|---|
| URDF | ROS link·joint 트리, visual, collision, inertial | Xacro를 펼친 생성물 | `robot_state_publisher`가 읽는다 |
| Xacro | 변수, 수식, 조건, 반복 가능한 macro | 로봇 description의 원본 | 먼저 URDF로 확장한다 |
| SDF | world, physics, sensor, Gazebo System, 상대 frame | world 원본과 Gazebo 내부 모델 | `gz sim`이 읽는다 |

URDF와 SDF 모두 XML이지만 목적이 다르다. 세 파일에 같은 link와 치수를 복사하면 한쪽만 수정되는 순간 모델이 갈라진다. 따라서 이 저장소는 `tutorial_bot.urdf.xacro` 하나를 로봇 원본으로 사용하고, Gazebo 전용 항목은 그 안의 `<gazebo>` 확장으로 연결한다.

## 1. URDF 코드 조각 읽기

URDF의 핵심은 link와 joint로 이루어진 트리이다. 다음 코드는 몸체와 왼쪽 바퀴를 잇는다.

```xml
<link name="base_link">
  <inertial>
    <mass value="5.0"/>
    <inertia ixx="0.0487" ixy="0" ixz="0"
             iyy="0.0904" iyz="0" izz="0.1270"/>
  </inertial>
  <visual><geometry><box size="0.45 0.32 0.12"/></geometry></visual>
  <collision><geometry><box size="0.45 0.32 0.12"/></geometry></collision>
</link>

<link name="left_wheel_link"> ... </link>

<joint name="left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="left_wheel_link"/>
  <origin xyz="0 0.19 -0.06" rpy="0 0 0"/>
  <axis xyz="0 1 0"/>
  <limit effort="5.0" velocity="20.0"/>
</joint>
```

`parent`와 `child`는 TF 트리의 방향을 정하고 `origin`은 parent에서 child joint까지의 고정 변환을 정한다. `continuous` joint의 현재 회전각은 `/joint_states`로 들어오며 `robot_state_publisher`가 바퀴 link TF를 갱신한다.

두 구동 바퀴만으로는 몸체의 세 번째 접촉점이 없으므로 실제 Xacro는 뒤쪽 caster를 추가한다. 이 튜토리얼은 회전 joint가 없는 낮은 마찰의 구형 caster로 단순화한다.

```xml
<link name="caster_link">
  <inertial>
    <mass value="0.08"/>
    <inertia ixx="0.0000392" ixy="0" ixz="0"
             iyy="0.0000392" iyz="0" izz="0.0000392"/>
  </inertial>
  <visual><geometry><sphere radius="0.035"/></geometry></visual>
  <collision><geometry><sphere radius="0.035"/></geometry></collision>
</link>
<joint name="caster_joint" type="fixed">
  <parent link="base_link"/>
  <child link="caster_link"/>
  <origin xyz="-0.17 0 -0.085" rpy="0 0 0"/>
</joint>
<gazebo reference="caster_link"><mu1>0.05</mu1><mu2>0.05</mu2></gazebo>
```

caster는 구동 joint 목록에 넣지 않는다. `mu1`, `mu2`를 낮게 두어 차체 회전을 방해하는 횡마찰을 줄인다.

## 2. Xacro로 반복 제거하기

좌우 바퀴를 복사하지 않고 `side`와 `y_position`을 받는 macro로 만든다. 저장소의 `stage_components.xacro`가 사용하는 방식이다.

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:macro name="stage_wheel" params="side y_position">
    <link name="${side}_wheel_link">
      <visual>
        <origin rpy="1.57079632679 0 0"/>
        <geometry><cylinder radius="0.06" length="0.04"/></geometry>
      </visual>
      <collision>
        <origin rpy="1.57079632679 0 0"/>
        <geometry><cylinder radius="0.06" length="0.04"/></geometry>
      </collision>
    </link>
    <joint name="${side}_wheel_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${side}_wheel_link"/>
      <origin xyz="0 ${y_position} -0.06"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>
</robot>
```

main Xacro에서는 macro 파일을 include한 뒤 두 번 호출한다.

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="tutorial_bot">
  <xacro:include filename="../macros/stage_components.xacro"/>

  <xacro:stage_base/>
  <xacro:stage_wheel side="left"  y_position="0.19"/>
  <xacro:stage_wheel side="right" y_position="-0.19"/>
</robot>
```

이 방식은 이름 규칙과 형상을 한 곳에서 고친다. Xacro include 경로는 include하는 파일을 기준으로 해석하므로 package 설치 시 `urdf/` 하위 파일도 함께 설치해야 한다.

## 3. 센서 Xacro를 별도 파일로 분리하기

센서 link·joint와 `<gazebo reference="...">` 설정을 별도 macro로 만들면 여러 로봇에서 같은 센서를 재사용할 수 있다. 실제 mount는 `examples/ros2_ws/src/tutorial_bot_description/urdf/sensors/sensor_mounts.xacro`, 2D·3D LiDAR macro는 `examples/ros2_ws/src/tutorial_bot_description/urdf/sensors/lidar.xacro`에 있다. 다음은 실제 macro 구조의 핵심이다.

```xml
<!-- sensor_mounts.xacro: 물리 link와 joint를 담당한다. -->
<xacro:macro name="tutorial_sensor_mounts">
  <link name="lidar_link"> ... </link>
  <joint name="lidar_joint" type="fixed">
    <parent link="base_link"/>
    <child link="lidar_link"/>
    <origin xyz="0.10 0 0.09" rpy="0 0 0"/>
  </joint>
</xacro:macro>

<!-- lidar.xacro: Gazebo sensor 설정을 담당한다. -->
<xacro:macro name="gpu_lidar_2d"
    params="reference sensor_name topic frame_id
            update_rate:=10 samples:=360
            min_angle:=-3.14159265359 max_angle:=3.14159265359
            min_range:=0.12 max_range:=10.0
            range_resolution:=0.01 noise_stddev:=0.01">
  <gazebo reference="${reference}">
    <sensor name="${sensor_name}" type="gpu_lidar">
      <topic>${topic}</topic>
      <gz_frame_id>${frame_id}</gz_frame_id>
      <update_rate>${update_rate}</update_rate>
      <lidar>
        <scan><horizontal>
          <samples>${samples}</samples>
          <min_angle>${min_angle}</min_angle>
          <max_angle>${max_angle}</max_angle>
        </horizontal></scan>
        <range>
          <min>${min_range}</min><max>${max_range}</max>
          <resolution>${range_resolution}</resolution>
        </range>
      </lidar>
    </sensor>
  </gazebo>
</xacro:macro>
```

main Xacro에서는 실제 상대 경로로 include하고 mount와 sensor macro 호출만 남긴다.

```xml
<xacro:include filename="sensors/sensor_mounts.xacro"/>
<xacro:include filename="sensors/lidar.xacro"/>
<xacro:include filename="sensors/cameras.xacro"/>
<xacro:include filename="sensors/imu.xacro"/>

<xacro:tutorial_sensor_mounts/>
<xacro:gpu_lidar_2d reference="lidar_link" sensor_name="lidar"
                     topic="$(arg lidar_topic)"
                     frame_id="$(arg tf_prefix)lidar_link"/>
<xacro:rgbd_camera_sensor reference="camera_link" sensor_name="camera"
                          topic="$(arg camera_topic)"
                          frame_id="$(arg tf_prefix)camera_optical_frame"/>
<xacro:imu_sensor reference="imu_link" sensor_name="imu"
                  topic="$(arg imu_topic)"
                  frame_id="$(arg tf_prefix)imu_link"/>
```

`tutorial_bot.urdf.xacro`가 위 구조를 실제로 사용한다. mount macro와 sensor macro를 분리하되 main에서 같은 link 이름을 `reference`로 연결한다. 이 구조에서는 mount 위치를 바꾸는 작업과 센서 rate·noise를 바꾸는 작업의 책임이 섞이지 않는다.

## 4. Gazebo 확장을 조건부로 선택하기

현재 Xacro는 `control_backend` 인자에 따라 Gazebo DiffDrive System과 `gz_ros2_control` 중 하나만 생성한다.

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
      <odom_publish_frequency>30</odom_publish_frequency>
    </plugin>
  </gazebo>
</xacro:if>
```

초급에서는 직접 Gazebo System과 `ros_gz_bridge`를 사용하고, 중급 launch는 `control_backend:=gz_ros2_control`을 전달해 ROS controller를 사용한다. 두 backend를 동시에 넣으면 같은 joint에 서로 다른 제어기가 명령하므로 피해야 한다.

## 5. SDF 변환 결과 읽기

Gazebo는 spawn된 URDF를 내부적으로 SDF entity로 변환한다. 변환 결과의 일부는 다음 형태가 된다.

```xml
<sdf version="1.11">
  <model name="tutorial_bot">
    <link name="base_link">...</link>
    <joint name="left_wheel_joint" type="revolute">...</joint>
    <plugin filename="gz_ros2_control-system"
            name="gz_ros2_control::GazeboSimROS2ControlPlugin">
      <parameters>.../controllers.yaml</parameters>
    </plugin>
  </model>
</sdf>
```

변환된 SDF를 새 원본으로 편집하지 않는다. Xacro를 고친 뒤 매번 URDF와 SDF를 다시 생성한다.

<figure class="course-figure" id="intermediate-model-conversion">
  <img src="../../assets/intermediate/model-conversion.svg" alt="Xacro에서 URDF와 SDF로 변환되는 모델 책임 흐름도" loading="lazy">
  <figcaption>그림 1. Xacro 원본을 URDF로 펼친 뒤 ROS 구조와 Gazebo SDF 확장으로 전달한다.</figcaption>
</figure>

## 실행과 결과 확인

저장소 루트에서 두 backend를 각각 펼쳐 검사한다.

```bash
robot=examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro
control=examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml

xacro "$robot" control_backend:=gazebo_diff_drive > /tmp/tutorial_bot-direct.urdf
check_urdf /tmp/tutorial_bot-direct.urdf
gz sdf -p /tmp/tutorial_bot-direct.urdf > /tmp/tutorial_bot-direct.sdf

xacro "$robot" control_backend:=gz_ros2_control \
  controller_parameters_file:="$PWD/$control" > /tmp/tutorial_bot-control.urdf
check_urdf /tmp/tutorial_bot-control.urdf
gz sdf -p /tmp/tutorial_bot-control.urdf > /tmp/tutorial_bot-control.sdf
```

생성물이 서로 다른 backend를 정확히 하나씩 포함하는지 확인한다.

```bash
grep -c 'gz::sim::systems::DiffDrive' /tmp/tutorial_bot-direct.sdf
grep -c 'GazeboSimROS2ControlPlugin' /tmp/tutorial_bot-control.sdf
grep -E 'left_wheel_joint|right_wheel_joint|lidar_link' /tmp/tutorial_bot-control.urdf
```

앞의 두 명령이 각각 `1`을 출력하고 필수 joint·link가 보이면 변환 경로가 정상이다.

## 계산 예제: 변환 불변 조건

<div class="course-worked" data-worked-example="model-conversion">
변환 전후 joint 집합을 \(J_X\), \(J_U\), \(J_S\)라 하면 핵심 구조의 합격 조건은 \(\{left\_wheel,right\_wheel,lidar\}\subseteq J_X\cap J_U\cap J_S\)이다. 이름만 같은지 확인하는 것으로 끝내지 않고 SDF 결과에서 sensor와 선택한 control plugin이 정확히 하나만 남았는지도 확인한다.
</div>

## 문제 해결

- `unknown macro name` 오류가 나면 include가 macro 호출보다 앞에 있는지 확인한다.
- `No such file or directory`가 나오면 상대 include 경로와 package 설치 규칙을 확인한다.
- Xacro 인자 오류가 나면 파일 상단의 `xacro:arg` 이름과 전달 형식을 확인한다.
- 변환 결과에 두 control plugin이 모두 있으면 조건문과 `control_backend` 값을 확인한다.
- Gazebo Classic용 `gazebo_ros` 또는 `gazebo_ros2_control` 예제를 섞지 않는다. Harmonic에서는 `ros_gz`와 `gz_ros2_control`을 사용한다.

## 정리

URDF는 ROS 로봇 트리, Xacro는 그 트리를 재사용 가능하게 생성하는 원본, SDF는 world와 Gazebo 고유 실행 기능을 맡는다. link·joint·센서 이름을 macro 인자로 연결하고 변환 결과까지 검사하면 세 표현 사이의 불일치를 줄일 수 있다.

[이전: 고급 SDF](01-advanced-sdf.md) · [다음: ROS 2 Launch](03-ros2-launch.md)
