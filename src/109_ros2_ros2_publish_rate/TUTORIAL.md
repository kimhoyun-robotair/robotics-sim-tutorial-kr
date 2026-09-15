# 109. 센서마다 다른 주기로 메시지 보내기

## 이번에 배우는 것

**한 장면의 시계·IMU·LiDAR·카메라에 서로 다른 발행 간격을 주고, 설정한 간격과 실제 수신 빈도를 구분합니다.**

카메라가 초당 60번 렌더링된다고 RGB와 깊이 정보를 모두 60번 보낼 필요는 없습니다. 필요한 데이터만 적절한 주기로 보내면 수신 측 처리량과 통신량을 줄일 수 있습니다. 이번에는 전체 진행 속도와 개별 발행 간격을 따로 다룹니다.

| 조절 위치 | 설정 | 역할 |
|---|---|---|
| 앱·Timeline | `TARGET_FPS=60` | 전체 진행의 목표 빈도 |
| 일반 Action Graph | Gate의 `step=2` | 실행 신호가 두 번 올 때 한 번 통과 |
| 센서 Helper | `frameSkipCount=3` | 세 프레임을 건너뛰고 네 번째에 발행 |
| 외부 ROS | `ros2 topic hz` | 수신기 시계로 실제 도착 빈도 측정 |

`configure_rates.py`는 공식 장면의 기존 속성을 바꾸는 Script Editor 코드입니다. 장면을 불러오거나 IMU 그래프를 새로 생성하지는 않습니다.

## 1. 다중 센서 장면에 발행 간격 적용하기

Isaac Sim 5.1, 지원 RTX GPU, ROS 2 Humble 또는 Jazzy가 필요합니다. 저장소 루트에서 Bash 터미널 A와 B를 준비하세요. 아래는 Ubuntu 24.04의 Jazzy 기준이며 Ubuntu 22.04/Humble에서는 `jazzy` 값과 라이브러리·source 경로를 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 실행합니다. 설치 위치에 맞게 `ISAAC_SIM`을 바꾸세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

터미널 B에서는 시스템 ROS를 준비합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

1. Content Browser에서 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial_multi_sensor_publish_rates.usd**를 엽니다. 5.1 asset 서버 또는 로컬 asset pack에 접근할 수 있어야 합니다.
2. 아직 Play하지 않은 상태에서 **File > Save As**로 실습용 사본을 저장합니다.
3. **Window > Script Editor**에 `src/109_ros2_ros2_publish_rate/configure_rates.py` 전체를 붙여 넣고 실행합니다.
4. 콘솔의 속성 경로·값과 `Configured target FPS= 60`을 확인합니다. 오류가 없다면 Play하세요.
5. Viewport의 눈 아이콘에서 **Heads Up Display > FPS**를 켭니다. 이 숫자와 ROS 수신 빈도를 함께 관찰합니다.

### 코드에서 볼 부분

```python
TARGET_FPS = 60
RGB_SKIP = 3
LIDAR_SKIP = 11
INFO_SKIP = 5
```

스크립트는 먼저 수정할 **모든 속성 경로가 존재하는지** 확인합니다. 지정한 sample이 아니면 일부만 바꾼 장면을 남기지 않고 경로 오류를 냅니다. 검사 후 RGB·LaserScan·CameraInfo의 skip을 설정하고, 비교에 쓰지 않을 3D 점군·두 번째 카메라·깊이 출력을 비활성화합니다.

```python
stage.SetTimeCodesPerSecond(TARGET_FPS)
timeline.set_target_framerate(TARGET_FPS)
```

USD 시간 코드와 Timeline의 목표 빈도를 함께 설정합니다. 앱 루프의 rate limit도 60으로 설정하지만, **목표를 지정했다고 GPU가 그 처리량을 보장하는 것은 아닙니다.** 이미 재생한 장면에서 목표값을 다시 실험할 때는 장면을 다시 열고 첫 Play 전에 적용하세요.

### 실행 결과 확인하기

터미널 B에서 다음 명령을 하나씩 10초 이상 관찰한 뒤 Ctrl+C로 종료합니다. 동시에 측정하려면 동일한 ROS 환경의 터미널을 추가하세요.

```bash
ros2 topic hz /clock
ros2 topic hz /imu
ros2 topic hz /scan
ros2 topic hz /camera_1/rgb/image_raw
ros2 topic hz /camera_1/rgb/camera_info
```

| 토픽 | 발행 조건 | 기준 진행률이 60일 때 목표 |
|---|---|---|
| `/clock` | 매 프레임 | 약 60 Hz |
| `/imu` | Gate `step=2` | 약 30 Hz |
| `/scan` | skip 11 | 약 5 Hz |
| RGB | skip 3 | 약 15 Hz |
| CameraInfo | skip 5 | 약 10 Hz |

IMU의 30 Hz는 **장면에 Gate `step=2`가 구성되어 있을 때**의 값입니다. 로컬 스크립트는 IMU Gate를 수정하지 않습니다. 다음 절에서 이 연결을 직접 확인하세요. 표의 값은 측정 결과가 아니라 비교 기준입니다.

## 2. IMU Gate와 카메라 Helper 비교하기

**Window > Graph Editors > Action Graph**에서 로봇의 `base_link/imu_link` 아래 IMU 그래프를 엽니다. 아래 구성과 다르면 Stop 상태에서 수정하세요. 기본 `turtlebot_tutorial.usd`부터 구성하는 경우에는 `imu_link`를 선택하고 **Create > Sensors > Imu Sensor**로 `Imu_Sensor`를 먼저 만듭니다.

IMU 그래프가 없다면 `/World/turtlebot3_burger/base_link/imu_link/ROS_IMU`에 새 Action Graph를 만듭니다. **On Playback Tick**, **Isaac Simulation Gate**, **Isaac Read IMU**, **ROS2 Publish IMU**, **ROS2 Context**, **Isaac Read Simulation Time**을 추가한 뒤 아래의 실행·데이터 연결을 구성하세요. 센서 prim을 만드는 것만으로 이 읽기·발행 노드가 생기지는 않습니다.

### 설정에서 볼 부분

```text
Tick.tick → Gate.execIn
Gate.execOut → ReadIMU.execIn
ReadIMU.execOut → PublishIMU.execIn
```

Gate의 `step`은 2, ReadIMU의 `imuPrim`은 `/World/turtlebot3_burger/base_link/imu_link/Imu_Sensor`입니다. ReadIMU의 `linearAcceleration`, `angularVelocity`, `orientation`을 발행기의 같은 입력에 연결합니다. ROS2 Context와 Isaac Read Simulation Time도 발행기에 연결하고 `frameId=imu_link`, `topicName=/imu`로 지정합니다.

Gate 뒤에 읽기와 발행을 함께 두는 이유는 **그 주기에 사용할 센서값을 읽은 뒤 보내기 위해서**입니다. 실행 포트를 연결하지 않고 숫자만 채우면 언제 처리해야 할지 정해지지 않습니다.

카메라 그래프 `/World/ActionGraph_camera`에서는 직접 만든 Gate 대신 Helper의 `frameSkipCount`를 확인하세요. Helper가 렌더 후처리 파이프라인에 필요한 Gate를 구성합니다. 로컬 스크립트의 대상은 다음과 같습니다.

| 노드 | 변경 |
|---|---|
| `ros2_camera_helper` | RGB skip 3 |
| `ros2_camera_info_helper` | CameraInfo skip 5 |
| `ros2_camera_helper_02` | 깊이 출력 비활성화 |
| `isaac_create_render_product_01` | 두 번째 카메라 비활성화 |
| `base_scan/ROS_LidarRTX/LaserScanPublish` | LaserScan skip 11 |
| `base_scan/ROS_LidarRTX/PointCloudPublish` | 점군 출력 비활성화 |

설정 콘솔은 “요청값이 속성에 들어갔다”는 증거입니다. 실제 이미지가 도착하는지는 ROS 수신으로 따로 확인합니다.

## 3. 간격과 빈도의 관계 정리

```text
일반 Gate:       발행 기회 ≈ 기준 빈도 / step
센서 frame skip: 발행 기회 ≈ 기준 빈도 / (frameSkipCount + 1)
```

`step=3`과 `frameSkipCount=3`은 다릅니다. 앞의 것은 세 번마다 한 번, 뒤의 것은 네 번마다 한 번입니다. 같은 숫자를 넣고 같은 결과를 기대하면 비교가 어긋납니다.

또한 `ros2 topic hz`는 **벽시계 시간당 수신 횟수**를 보여 줍니다. 시뮬레이션 시간이 느리게 진행되면 설정상 15 Hz인 RGB가 실제로는 더 낮게 측정될 수 있습니다. LiDAR는 센서 자체의 스캔 완료 조건도 만족해야 합니다. 그래서 FPS, 토픽별 수신 Hz, 설정한 분모를 함께 기록해야 원인을 구분할 수 있습니다.

## 4. 간단한 확인 실험

프로그램은 그대로 두고 `configure_rates.py`의 **`RGB_SKIP`만 3에서 7로 바꿔 보세요.** 장면을 다시 열고 첫 Play 전에 변경한 스크립트를 실행합니다.

RGB의 발행 기회는 기준 빈도의 1/4에서 1/8로 줄어듭니다. 기준이 60이면 목표는 15 Hz에서 7.5 Hz가 됩니다. `/camera_1/rgb/image_raw`의 수신률을 이전 기록과 비교하고, CameraInfo의 skip 5는 유지되는지 확인하세요. 관찰을 마치면 원래 값 3으로 되돌릴 수 있습니다.

## 실행할 때 막히면

- **`Expected official scenario attribute is missing`**: 기본 TurtleBot 장면과 multi-sensor 장면을 혼동했는지 확인하세요. 실제 노드 경로를 확인하지 않고 오류 검사를 지우지 않습니다.
- **IMU만 예상과 다름**: `configure_rates.py`가 IMU를 만들지 않는다는 점을 기억하세요. 센서 prim, Gate `step=2`, 읽기→발행 연결을 확인합니다.
- **토픽 이름은 있지만 `hz` 출력이 없음**: `ros2 topic info -v 토픽명`으로 QoS를 읽고 수신기의 정책과 비교하세요. 미수신을 단순히 성능 0 Hz라고 기록하지 않습니다.
- **모든 토픽이 비슷한 비율로 느림**: HUD FPS와 GPU 부하를 먼저 확인하세요. 개별 skip과 전체 진행 속도의 문제를 나누어 봅니다.
- **값을 바꿔도 이전 주기가 유지됨**: 장면을 다시 로드하고 Helper가 초기화되기 전 설정했는지 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [ROS2 Setting Publish Rates](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html)에 대응합니다. 실행 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 다중 센서 장면에 적용할 설정을 로컬 스크립트로 묶었습니다. 설치된 5.1 Helper 코드의 `frameSkipCount + 1` 처리와 대조했으며, 표의 Hz는 실제 측정값이 아닙니다. `tutorial.json`의 `verification: not_run`처럼 GPU·ROS 수신 측정은 별도로 수행해야 합니다.
