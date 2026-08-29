# gazebo_tutorial_description

튜토리얼에서 사용하는 URDF/Xacro 로봇과 재사용 가능한 Gazebo Classic 센서 macro를 모은
description 패키지이다.

| 최상위 Xacro | 모델 |
| --- | --- |
| `urdf/diffbot.urdf.xacro` | 2륜 differential drive + caster |
| `urdf/rover_diff.urdf.xacro` | 4륜 skid/differential rover |
| `urdf/rover_ackermann.urdf.xacro` | 4륜 Ackermann rover |
| `urdf/sensor_bot.urdf.xacro` | IMU·카메라·2D/3D LiDAR 실습 로봇 |

센서 구현은 `urdf/sensors/` 아래의 종류별 Xacro 파일로 분리한다. 최상위 로봇은 필요한
파일을 include하고 `prefix`, parent link, pose, topic, 측정 범위를 전달하여 같은 macro를
다른 로봇에서도 재사용한다.

```xml
<xacro:include
  filename="$(find gazebo_tutorial_description)/urdf/sensors/imu_sensor.xacro"/>

<xacro:gazebo_imu_sensor
  prefix="imu" parent="base_link" xyz="0 0 0.10"
  topic="imu/data" update_rate="100.0"/>
```

빌드한 뒤 모든 최상위 모델을 전개하고 URDF tree를 검사한다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select gazebo_tutorial_description
source install/setup.bash

for model in diffbot rover_diff rover_ackermann sensor_bot; do
  xacro src/gazebo_tutorial_description/urdf/${model}.urdf.xacro \
    > /tmp/${model}.urdf
  check_urdf /tmp/${model}.urdf
done
```
