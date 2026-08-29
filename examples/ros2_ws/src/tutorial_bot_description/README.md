# tutorial_bot_description

Jazzy + Harmonic 실습에서 사용하는 URDF/Xacro 원본을 설치하는 `ament_cmake` package이다.

## 파일 구조

```text
urdf/
├── tutorial_bot.urdf.xacro
├── macros/
│   ├── stage_components.xacro
│   └── rover_components.xacro
├── sensors/
│   ├── sensor_mounts.xacro
│   ├── lidar.xacro
│   ├── cameras.xacro
│   └── imu.xacro
├── stages/
│   ├── 01-base.xacro
│   ├── 02-wheels-and-joints.xacro
│   ├── 03-diff-drive.xacro
│   ├── 04-sensors-final.xacro
│   └── 05-sensor-gallery.xacro
└── rovers/
    ├── rover_diff.urdf.xacro
    └── rover_ackermann.urdf.xacro
```

`tutorial_bot.urdf.xacro`는 두 구동 바퀴와 fixed caster, 기본 센서, 선택 가능한 주행 backend를 가진 canonical model이다. `stages`는 초급 과정의 누적 학습 단계를 제공한다. `sensors`는 mount와 관측 모델을 분리해 다른 로봇에서도 include할 수 있게 한다.

`rover_components.xacro`는 4륜 rover의 공통 chassis·wheel·steering 요소를 정의한다. `rover_diff.urdf.xacro`와 `rover_ackermann.urdf.xacro`는 각각 skid/differential 방식과 Ackermann 방식의 실행 모델을 조립한다.

## 확인

```bash
source /opt/ros/jazzy/setup.bash
xacro urdf/tutorial_bot.urdf.xacro > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf

xacro urdf/stages/05-sensor-gallery.xacro > /tmp/sensor_gallery.urdf
check_urdf /tmp/sensor_gallery.urdf
```

build 후에는 source tree 대신 installed share directory를 사용한다.

```bash
colcon build --packages-select tutorial_bot_description
source install/setup.bash
share="$(ros2 pkg prefix --share tutorial_bot_description)"
xacro "$share/urdf/tutorial_bot.urdf.xacro" > /tmp/tutorial_bot.urdf
```
