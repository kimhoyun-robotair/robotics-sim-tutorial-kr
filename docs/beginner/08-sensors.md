# `tutorial_bot` 센서: LiDAR·RGB-D·IMU

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** DiffDrive

## 학습 목표

- 2차원 LiDAR의 각도 간격, 거리 범위, `inf`를 해석합니다.
- RGB-D Camera의 시야각·해상도·갱신률과 IMU의 역할을 설명합니다.
- Gazebo Transport에서 `LaserScan`, `Image`, `IMU` 메시지를 직접 확인합니다.

## 배경 지식

LiDAR는 여러 방향으로 광선을 쏘아 장애물까지의 거리를 배열로 발행합니다. 이 예제의 LiDAR는 한 바퀴에 360개 측정값을 만들고, 0.12&nbsp;m부터 10.0&nbsp;m까지를 관측합니다. world의 `training_box`는 로봇 전방에 배치해 실제 거리값이 생기도록 했습니다.

RGB-D Camera는 색 픽셀과 깊이 정보를 렌더링합니다. IMU는 로봇의 회전 속도와 선형 가속도를 측정해 자세 변화의 단서를 제공합니다. 그래서 물리 엔진만 필요했던 이전 단계와 달리 Gazebo의 `Sensors` System과 `ogre2` 렌더 엔진이 필요합니다.

> 주의: 이 장은 Gazebo Transport만 사용합니다. ROS 2의 `/scan`·이미지 토픽으로 변환하는 과정은 `ros_gz_bridge` 장에서 다룹니다.

## 예제 파일

로봇의 link, fixed joint, LiDAR, RGB-D Camera, IMU 설정은 하나의 Xacro 원본에 있습니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/stages/04-sensors-final.xacro`

센서 System과 렌더 엔진 설정은 world에 있습니다.

`examples/gazebo/worlds/first-world.sdf`

headless 검증 스크립트는 모델을 spawn하고 두 센서 메시지를 검사합니다.

`scripts/check_sensors.sh`

## 실습

### 1. 센서를 고정 link로 연결하기

`lidar_link`, `camera_link`, `imu_link`는 모두 `base_link`에 fixed joint로 연결됩니다. LiDAR는 로봇 윗면에, Camera는 전방에, IMU는 본체 중심에 배치했습니다. 센서 좌표계가 로봇과 함께 움직이도록 만드는 기본 TF 구조입니다.

<figure class="course-figure" markdown="span">
  ![로봇에서 퍼지는 라이다 광선과 RGB-D 카메라 화면 및 IMU 축](../assets/beginner/sensor-observables.svg)
  <figcaption>그림 4. LiDAR는 10&nbsp;Hz로 360개 거리, RGB-D Camera는 30&nbsp;Hz로 320&nbsp;×&nbsp;240 영상, IMU는 100&nbsp;Hz로 움직임을 관찰합니다.</figcaption>
</figure>

### 2. LiDAR 설정 읽기

Xacro의 `gpu_lidar` sensor는 `-π`와 `π`를 **모두 포함**하는 수평 시야에 360개 sample을 둡니다. 따라서 인접 광선의 각도 간격은 전체 360°를 360으로 나누는 값이 아니라 다음과 같습니다.

\[
\begin{aligned}
\Delta\theta
  &=\frac{\pi-(-\pi)}{360 - 1}=\frac{2\pi}{359}\\
  &\approx 0.01750\,\mathrm{rad}\\
  &\approx 1.0028^\circ
\end{aligned}
\]

양 끝이 같은 방향을 나타내더라도 SDF의 endpoint convention을 그대로 해석해야 합니다. 거리 양자화 해상도는 0.01&nbsp;m이고 Gaussian noise의 표준편차도 0.01&nbsp;m입니다. 0.12&nbsp;m보다 가까운 물체는 유효 측정 범위 밖이고, 10.0&nbsp;m 안에서 광선이 아무것도 만나지 않으면 `ranges` 원소가 `inf`가 될 수 있습니다. `inf`는 오류나 10.0&nbsp;m의 물체가 아니라 “이 광선에는 범위 안의 반환점이 없음”이라는 뜻입니다.

```xml
<sensor name="lidar" type="gpu_lidar">
  <topic>/tutorial_bot/lidar</topic>
  <update_rate>10</update_rate>
  <lidar>...</lidar>
</sensor>
```

`gpu_lidar`는 Harmonic에서 GPU LiDAR라는 이름으로 제공되는 렌더링 기반 센서입니다. 실제 센서 plugin은 로봇이 아니라 world의 `gz::sim::systems::Sensors`가 생성하고 갱신합니다.

### 3. RGB-D Camera 설정 읽기

Camera는 수평 시야각 `1.047 rad`(약 60°), `320 × 240` 해상도로 RGB와 depth 관찰값을 30 Hz로 갱신합니다. `<near>0.1</near>`와 `<far>10.0</far>`는 렌더링에 포함할 거리 범위입니다. 해상도는 한 프레임의 픽셀 수, HFOV는 좌우로 보이는 폭, update rate는 초당 새 프레임 수를 각각 결정합니다.

```xml
<sensor name="camera" type="rgbd_camera">
  <topic>/tutorial_bot/camera/image</topic>
  <update_rate>30</update_rate>
  <camera>...</camera>
</sensor>
```

### 4. IMU 설정 읽기

IMU는 100 Hz로 각속도와 선형 가속도를 발행합니다. 각 축에는 평균 0, 표준편차 `0.001`인 Gaussian noise가 설정되어 있습니다. 정지 상태에서도 아주 작은 값이 흔들릴 수 있으므로 한 샘플이 정확히 0인지보다 메시지가 이어지고 변화 방향이 물리적으로 맞는지를 봅니다.

### 5. topic과 메시지 anatomy

topic은 메시지가 흐르는 주소이고 type은 그 메시지의 구조입니다. `gz topic -i`로 둘을 함께 확인합니다.

| Gazebo topic | type | 먼저 볼 필드 |
|---|---|---|
| `/tutorial_bot/lidar` | `gz.msgs.LaserScan` | `count`, `angle_min`, `angle_max`, `range_min`, `range_max`, `ranges` |
| `/tutorial_bot/camera/image` | `gz.msgs.Image` | `width`, `height`, `pixel_format_type`, `data` |
| `/tutorial_bot/imu` | `gz.msgs.IMU` | `angular_velocity`, `linear_acceleration` |

## 실행

저장소 루트에서 다음을 실행합니다.

```bash
source /opt/ros/jazzy/setup.zsh
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/04-sensors-final.xacro"
xacro "$stage" > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
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
gz topic -l | rg '/tutorial_bot/(lidar|camera|imu)'
gz topic -e -t /tutorial_bot/lidar -n 1
gz topic -e -t /tutorial_bot/camera/image -n 1
gz topic -e -t /tutorial_bot/imu -n 1
```

## 결과 확인

LiDAR 메시지의 `count`가 360이고 metadata가 `-π..π`, `0.12..10.0 m`이며 `inf`가 아닌 거리값이 하나 이상 있으면 scan 설정과 장애물 관측을 함께 확인한 것입니다. Camera의 `width`, `height`가 320, 240이고 IMU에 각속도와 선형 가속도가 있으면 세 센서 경로가 살아 있습니다. 여러 메시지의 simulation timestamp 간격은 각각 약 0.1&nbsp;s, 0.033&nbsp;s, 0.01&nbsp;s여야 합니다.

## 동작 원리

`Sensors` System은 world 안의 sensor 요소를 찾아 update rate에 맞게 갱신합니다. LiDAR는 거리 배열을, Camera는 픽셀과 깊이 데이터를, IMU는 관성 관찰값을 Gazebo Transport topic으로 발행합니다. Camera와 GPU LiDAR는 렌더링을 사용하므로 world에서 `ogre2`를 지정했습니다.

## 자주 발생하는 문제

### topic이 보이지 않습니다

world에 `gz-sim-sensors-system` plugin이 있는지, 그리고 시뮬레이션이 재생 중인지 확인합니다. 센서의 `<topic>`은 모델 spawn 뒤에 생성됩니다.

### headless Camera 초기화 문제

Camera와 GPU LiDAR는 렌더링 기능을 사용합니다. 지원 환경인 amd64 / NVIDIA 환경에서 `gz sim`이 `ogre2` 렌더 엔진을 초기화할 수 있는지 확인하고, server 로그의 rendering 오류를 먼저 읽습니다.

### LiDAR 값이 모두 최대 거리입니다

LiDAR의 수평면에 장애물이 있는지와 `<range><max>`를 확인합니다. 이 예제에서는 전방의 `training_box`를 관측합니다.

## 정리

`tutorial_bot`은 이제 주행 명령뿐 아니라 거리, RGB-D 영상, 관성 관찰값도 Gazebo Transport로 발행합니다. 다음 장에서는 Gazebo Fuel의 model URI와 resource path를 다룹니다.

[이전: DiffDrive](07-diff-drive.md) · [다음: Gazebo Fuel](09-gazebo-fuel.md)
