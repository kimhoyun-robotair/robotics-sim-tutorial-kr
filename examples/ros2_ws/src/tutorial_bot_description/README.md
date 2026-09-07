# tutorial_bot_description

ROS 2 Jazzy + Gazebo Harmonic 실습의 URDF/Xacro 원본을 설치하는 `ament_cmake` 패키지이다.

## 파일 구조

| `urdf/` 아래 경로 | 내용 |
|---|---|
| `tutorial_bot.urdf.xacro` | 구동 바퀴 2개, 캐스터, 기본 센서를 갖춘 공통 로봇 |
| `macros/stage_components.xacro` | 몸체·바퀴·구동 매크로 |
| `macros/rover_components.xacro` | 4륜 로버의 공통 차체·바퀴·조향 구조 |
| `sensors/sensor_mounts.xacro` | 센서 장착부와 광학 좌표계 |
| `sensors/lidar.xacro`, `cameras.xacro`, `imu.xacro` | 종류별 센서 매크로 |
| `stages/01-base.xacro`부터 `05-sensor-gallery.xacro` | 몸체 → 바퀴 → 구동 → 기본 센서 → 센서 모음 단계 |
| `rovers/rover_diff.urdf.xacro`, `rover_ackermann.urdf.xacro` | 4륜 스키드 조향과 Ackermann 모델 |

공통 로봇의 `control_backend` 인자로 Gazebo DiffDrive 또는 `gz_ros2_control`을 선택한다. 같은 바퀴에 두 구동 방식을 동시에 적용하지 않는다. 센서 장착 위치와 측정 설정은 별도 매크로로 나누어 다른 로봇에서도 재사용한다.

## 확인

저장소 루트에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
description=examples/ros2_ws/src/tutorial_bot_description
xacro "$description/urdf/tutorial_bot.urdf.xacro" > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf

xacro "$description/urdf/stages/05-sensor-gallery.xacro" > /tmp/sensor_gallery.urdf
check_urdf /tmp/sensor_gallery.urdf
```

빌드 후에는 설치된 리소스 경로를 사용한다.

```bash
cd examples/ros2_ws
colcon build --packages-select tutorial_bot_description
source install/setup.bash
cd ../..
share="$(ros2 pkg prefix --share tutorial_bot_description)"
xacro "$share/urdf/tutorial_bot.urdf.xacro" > /tmp/tutorial_bot.urdf
```

`check_urdf`는 구조와 문법을 검사한다. 실제 물리 동작과 RViz 센서 방향은 [중급 TF 실습](../../../../docs/04_intermediate/06-tf-rviz.md), [센서 실습](../../../../docs/04_intermediate/08-advanced-sensors.md)에서 확인한다.
