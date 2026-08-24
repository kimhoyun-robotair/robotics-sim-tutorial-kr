# LiDAR와 Camera를 단 `tutorial_bot`

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** DiffDrive

## 학습 목표

- 2차원 LiDAR의 거리 측정 범위와 scan 해상도를 설정합니다.
- RGB Camera의 시야각·이미지 해상도·클리핑 범위를 설정합니다.
- Gazebo Transport에서 `LaserScan`, `Image` 메시지를 직접 확인합니다.

## 배경 지식

LiDAR는 여러 방향으로 광선을 쏘아 장애물까지의 거리를 배열로 발행합니다. 이 예제의 LiDAR는 한 바퀴에 360개 측정값을 만들고, 0.12 m부터 8.0&nbsp;m까지를 관측합니다. world의 `training_box`는 로봇 전방 1.5 m에 배치해 실제 거리값이 생기도록 했습니다.

Camera는 렌더링된 RGB 픽셀을 발행합니다. 그래서 물리 엔진만 필요했던 이전 단계와 달리 Gazebo의 `Sensors` System과 `ogre2` 렌더 엔진이 필요합니다. `first-world.sdf`의 `training_box`와 `beacon`은 센서가 관측할 대상입니다.

> 주의: 이 장은 Gazebo Transport만 사용합니다. ROS 2의 `/scan`·이미지 토픽으로 변환하는 과정은 `ros_gz_bridge` 장에서 다룹니다.

## 예제 파일

로봇의 link, fixed joint, LiDAR, Camera 설정은 하나의 Xacro 원본에 있습니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

센서 System과 렌더 엔진 설정은 world에 있습니다.

`examples/gazebo/worlds/first-world.sdf`

headless 검증 스크립트는 모델을 spawn하고 두 센서 메시지를 검사합니다.

`scripts/check_sensors.sh`

## 실습

### 1. 센서를 고정 link로 연결하기

`lidar_link`와 `camera_link`는 모두 `base_link`에 fixed joint로 연결됩니다. LiDAR는 로봇 윗면 중앙 근처에, Camera는 전방에 배치했습니다. 센서 좌표계가 로봇과 함께 움직이도록 만드는 기본 TF 구조입니다.

### 2. LiDAR 설정 읽기

Xacro의 `gpu_lidar` sensor는 `-π`부터 `π`까지의 수평 시야를 360개 sample로 나눕니다. `range`의 `min`보다 가까운 물체는 측정하지 않고, `max`보다 먼 물체도 반환하지 않습니다.

```xml
<sensor name="lidar" type="gpu_lidar">
  <topic>/tutorial_bot/lidar</topic>
  <update_rate>10</update_rate>
  <lidar>...</lidar>
</sensor>
```

`gpu_lidar`는 Harmonic에서 GPU LiDAR라는 이름으로 제공되는 렌더링 기반 센서입니다. 실제 센서 plugin은 로봇이 아니라 world의 `gz::sim::systems::Sensors`가 생성하고 갱신합니다.

### 3. Camera 설정 읽기

Camera는 수평 시야각 약 60°, `320 × 240` RGB 이미지를 10 Hz로 발행합니다. `<near>`와 `<far>`는 렌더링에 포함할 거리 범위입니다.

```xml
<sensor name="camera" type="camera">
  <topic>/tutorial_bot/camera/image</topic>
  <camera>...</camera>
</sensor>
```

## 실행

저장소 루트에서 다음을 실행합니다.

```bash
./scripts/check_sensors.sh
```

스크립트는 Xacro를 임시 SDF로 변환하고, headless Gazebo에서 `tutorial_bot`을 spawn합니다. 그 다음 아래 topic과 메시지 형식을 확인합니다.

```text
/tutorial_bot/lidar         gz.msgs.LaserScan
/tutorial_bot/camera/image  gz.msgs.Image
```

정상이라면 다음과 같이 출력됩니다.

```text
LiDAR scan verified: 360 ranges, 172 obstacle readings.
Camera image verified: 320x240.
```

GUI에서 직접 실행한 경우에는 topic 목록과 한 개의 메시지를 다음처럼 확인할 수 있습니다.

```bash
gz topic -l | rg '/tutorial_bot/(lidar|camera)'
gz topic -e -t /tutorial_bot/lidar -n 1
gz topic -e -t /tutorial_bot/camera/image -n 1
```

## 결과 확인

LiDAR 메시지의 `count`가 360이고 `inf`가 아닌 거리값이 하나 이상 있으면, 설정한 한 바퀴 scan 수와 전방 상자 관측을 함께 확인한 것입니다. Camera 메시지의 `width`, `height`가 각각 320, 240이면 설정한 RGB 이미지 크기로 렌더링된 것입니다.

## 동작 원리

`Sensors` System은 world 안의 sensor 요소를 찾아 update rate에 맞게 갱신합니다. LiDAR는 `gz.msgs.LaserScan`의 거리 배열을, Camera는 `gz.msgs.Image`의 픽셀 데이터를 Gazebo Transport topic으로 발행합니다. Camera와 GPU LiDAR는 렌더링을 사용하므로 world에서 `ogre2`를 지정했습니다.

## 자주 발생하는 문제

### topic이 보이지 않습니다

world에 `gz-sim-sensors-system` plugin이 있는지, 그리고 시뮬레이션이 재생 중인지 확인합니다. 센서의 `<topic>`은 모델 spawn 뒤에 생성됩니다.

### headless Camera 초기화 문제

Camera와 GPU LiDAR는 렌더링 기능을 사용합니다. 지원 환경인 amd64 / NVIDIA 환경에서 `gz sim`이 `ogre2` 렌더 엔진을 초기화할 수 있는지 확인하고, server 로그의 rendering 오류를 먼저 읽습니다.

### LiDAR 값이 모두 최대 거리입니다

LiDAR의 수평면에 장애물이 있는지와 `<range><max>`를 확인합니다. 이 예제에서는 전방의 `training_box`를 관측합니다.

## 정리

`tutorial_bot`은 이제 주행 명령뿐 아니라 거리와 RGB 영상도 Gazebo Transport로 발행합니다. IMU와 Contact Sensor는 같은 센서 구조를 확장하는 과제로 남기고, 다음 장에서는 Gazebo Fuel의 모델 URI와 resource path를 다룹니다.
