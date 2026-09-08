# gazebo_tutorial_description

ROS 2 Humble·Gazebo Classic 11 실습용 로봇 모델과 센서 Xacro 매크로를 모은 패키지다.

| 파일 | 모델 |
| --- | --- |
| `urdf/diffbot.urdf.xacro` | 바퀴 두 개와 보조 바퀴를 사용하는 차동 구동 로봇 |
| `urdf/rover_diff.urdf.xacro` | 바퀴 네 개를 사용하는 스키드·차동 구동 차량 |
| `urdf/rover_ackermann.urdf.xacro` | 앞바퀴를 조향하는 Ackermann 차량 |
| `urdf/sensor_bot.urdf.xacro` | 기존 4륜 Ackermann 차량에 IMU·카메라·2D/3D 라이다를 장착한 센서 실습 차량 |

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

## 센서 차량의 기반 모델

`rover_ackermann.urdf.xacro`와 `sensor_bot.urdf.xacro`는 `urdf/macros/ackermann_rover.xacro`를 함께 사용한다. 차체 크기 0.72 × 0.50 × 0.16 m, 바퀴 반지름 0.16 m, 축거 0.56 m, 윤거 0.62 m는 두 모델이 같다. 앞바퀴 두 개로 조향하고 뒷바퀴 두 개로 구동한다.

센서 차량의 `all`, `cameras`, `lidars`, `minimal` 프로필은 같은 4륜 구조를 사용한다. IMU는 항상 켜지고, 나머지 센서와 해당 지지대만 프로필에 따라 달라진다. 카메라는 차체 앞쪽, 라이다는 차체와 바퀴보다 높은 곳에 장착했다. 센서 위치가 달라져도 광학 프레임, 스테레오 간격, 카메라 보정값은 센서 매크로에서 함께 유지한다.

| 센서 | `base_link` 기준 위치 `(x, y, z)` [m] |
| --- | --- |
| IMU | `(-0.14, 0.12, 0.09)` |
| 단안 카메라 | `(0.40, -0.13, 0.15)` |
| 스테레오 카메라 중심 | `(0.40, 0, 0.27)` |
| RGB-D 카메라 | `(0.40, 0.13, 0.15)` |
| 어안 카메라 | `(0.10, -0.17, 0.34)` |
| 2D 라이다 | `(0.20, 0, 0.42)` |
| 3D 라이다 | `(-0.15, 0, 0.54)` |

`base_link`는 지면에서 0.24 m 위에 있다. 센서와 지지대의 질량·관성도 모델에 포함한다. 지지대는 기존 센서 장착부와 마찬가지로 충돌 형상을 생략했다. 따라서 이 모델로 장착부 자체의 라이다 가림 현상이나 센서 충돌을 분석하지는 않는다.

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
