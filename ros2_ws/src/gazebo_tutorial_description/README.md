# gazebo_tutorial_description

ROS 2 Humble·Gazebo Classic 11 실습용 로봇 모델과 센서 Xacro 매크로를 모은 패키지다.

| 파일 | 모델 |
| --- | --- |
| `urdf/diffbot.urdf.xacro` | 바퀴 두 개와 보조 바퀴를 사용하는 차동 구동 로봇 |
| `urdf/rover_diff.urdf.xacro` | 바퀴 네 개를 사용하는 스키드·차동 구동 차량 |
| `urdf/rover_ackermann.urdf.xacro` | 앞바퀴를 조향하는 Ackermann 차량 |
| `urdf/sensor_bot.urdf.xacro` | IMU·카메라·2D/3D 라이다 실습 로봇 |

## 빌드와 모델 검사

[설치 안내](../../../docs/01_setup.md)를 마친 뒤 실행한다. `check_urdf`는 `liburdfdom-tools` 패키지에 들어 있다.

```bash
source /opt/ros/humble/setup.bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
colcon build --symlink-install --packages-select gazebo_tutorial_description
source install/setup.bash

for model in diffbot rover_diff rover_ackermann sensor_bot; do
  xacro "src/gazebo_tutorial_description/urdf/${model}.urdf.xacro" \
    > "/tmp/${model}.urdf"
  check_urdf "/tmp/${model}.urdf"
done
```

각 모델에서 `Successfully Parsed XML`과 링크 트리가 나오면 URDF 문법 검사를 통과한 것이다. 이 검사는 센서 측정값이나 Gazebo 실행 결과까지 확인하지는 않는다. 실제 실행은 [bringup 패키지](../gazebo_tutorial_bringup/README.md)를 사용한다.

## 센서 재사용

센서 코드는 `urdf/sensors/`에 있다. 다른 로봇에서 사용할 때는 공통 장착 매크로를 **먼저** 가져오고 센서 매크로를 호출한다. 다음 코드는 `base_link`를 이미 정의한 Xacro 안에 넣는 발췌 예제다.

```xml
<xacro:include
  filename="$(find gazebo_tutorial_description)/urdf/sensors/sensor_common.xacro"/>
<xacro:include
  filename="$(find gazebo_tutorial_description)/urdf/sensors/imu_sensor.xacro"/>

<xacro:gazebo_imu_sensor
  prefix="imu" parent="base_link" xyz="0 0 0.10"
  topic="imu/data" update_rate="100.0"/>
```

`prefix`는 링크·관절·플러그인의 이름을 만든다. 같은 센서를 두 개 달려면 `prefix`와 토픽을 각각 다르게 정한다. 카메라는 장착 링크와 광학 프레임을 구분하고, 스테레오는 좌우 렌즈마다 광학 프레임을 사용한다. 전체 구현과 RViz 확인 방법은 [센서 실습](../../../docs/05_sensors.md)에 있다.
