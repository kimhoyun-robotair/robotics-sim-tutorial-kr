# 124. 지도 한 장을 로봇이 달릴 수 있는 3D 공간으로 바꾸기

## 이번에 배우는 것

**점유 지도 PNG의 장애물 픽셀을 충돌 가능한 벽으로 만들고, 같은 지도를 사용하는 Nav2로 Carter를 주행시킵니다.**

지도는 3D 공간을 2D로 줄여 표현합니다. 이번에는 반대로 그 지도에서 장애물의 배치를 읽어 간단한 3D 공간을 만듭니다. 이때 중요한 것은 벽의 외형보다 **픽셀 크기와 원점을 ROS 지도 좌표에 맞추는 일**입니다.

| 입력 또는 구성 | 역할 | 확인할 값 |
|---|---|---|
| `carter_warehouse_navigation.png` | 벽이 될 픽셀 위치 | 이미지 너비·높이 |
| 같은 이름의 YAML | 픽셀의 실제 크기와 지도 원점 | `resolution`, `origin` |
| Block World Generator | 장애물 픽셀을 블록으로 배치 | 충돌 벽과 바닥 |
| Nova Carter + Clock 그래프 | 센서·이동·시뮬레이션 시간 | scan과 지도 정렬, 실제 도착 |

생성기는 로봇이나 Nav2를 자동으로 추가하지 않습니다. 아래에서 장면 생성, 좌표 정렬, 로봇 배치와 주행을 이어서 수행합니다.

## 1. 지도에서 블록 장면 생성하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0**, 지원 GPU를 기준으로 진행합니다. ROS desktop, 초기화된 `rosdep`, `colcon`이 필요합니다. 저장소 루트의 Bash에서 공식 워크스페이스를 준비하세요. 이미 같은 버전을 빌드했다면 clone과 빌드는 생략합니다.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
export LESSON_DIR="$PWD/src/124_ros2_ros2_navigation_block_world"
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-pointcloud-to-laserscan
colcon build
source install/local_setup.bash
cat src/navigation/carter_navigation/maps/carter_warehouse_navigation.yaml
mkdir -p "$LESSON_DIR/output"
```

PNG도 이 `maps` 폴더에 있습니다. 제공된 YAML의 `resolution`은 `0.05`, `origin`은 `[-11.975, -17.975, 0.0]`입니다. 다른 지도를 사용한다면 반드시 그 지도의 값을 읽으세요.

**시스템 ROS를 source하지 않은 새 Bash**에서 앱을 실행합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **Tools > Robotics > Block World Generator**를 엽니다. 메뉴가 없으면 `isaacsim.asset.importer.heightmap` 확장을 켜세요.
2. Cell Size를 YAML과 같은 **0.05 m**로 설정하고 **Load**로 `carter_warehouse_navigation.png`를 엽니다.
3. Visualization에서 이미지를 확인하고 **Generate**를 누릅니다. 생성기는 새 Stage를 만드므로 보존할 기존 작업은 먼저 저장하세요.
4. Stage의 `/World/occupancyMap/occupiedInstances`와 `/World/groundPlane`을 확인합니다. Console의 `Image Size:`는 `(너비, 높이)`이고 `Total blocks drawn:`은 생성한 블록 수입니다.

### 설정에서 볼 부분

설치된 5.1 생성기는 같은 블록 원형을 여러 위치에 배치하는 `PointInstancer`를 사용합니다. 픽셀 첫 채널이 127보다 작은 곳에 높이 2 m의 블록을 놓고 원형에 Collider를 적용합니다. 검은 점이 많은 지도를 넣을수록 블록 수가 늘어나는 이유입니다.

블록 중심의 로컬 XY는 다음처럼 계산됩니다. `r`은 Cell Size, `x`, `y`는 이미지의 열·행 번호입니다.

```text
local_x = (x + 0.5) × r
local_y = -(y + 0.5) × r
```

이미지의 행은 아래로 증가하지만 ROS 지도 y는 위로 증가합니다. 생성기는 왼쪽 위를 기준으로 y를 음수로 만들고, YAML은 왼쪽 아래를 origin으로 사용합니다. 따라서 다음 정렬이 필요합니다.

### 실행 결과 확인하기

먼저 벽과 바닥만 보이는 상태에서 PNG의 큰 방과 통로가 같은 모양인지 확인하세요. 이 결과는 창고의 기하 배치이며 사진 같은 재질이나 선반 세부 모양을 복원한 장면은 아닙니다.

## 2. 좌표를 맞추고 로봇 주행시키기

### 설정에서 볼 부분

PNG 높이를 `H`, YAML origin을 `(ox, oy, θ)`라고 하면 **부모 Xform 하나**에 아래 변환을 적용합니다.

| 부모 변환 | 설정할 값 |
|---|---|
| Translate X | `ox - sin(θ) × H × r` |
| Translate Y | `oy + cos(θ) × H × r` |
| Translate Z | `0` |
| Rotate Z | `θ × 180 / π`도 |

YAML의 θ는 라디안입니다. 기본 지도는 θ=0이므로 X=`-11.975`, Y=`-17.975 + H × 0.05`입니다. `H`는 Console의 Image Size 두 번째 수를 사용하세요.

1. `/World` 아래 빈 Xform `/World/MapPlacement`를 만듭니다.
2. `occupancyMap`과 `groundPlane`을 그 자식으로 옮깁니다. 부모가 아직 항등 변환일 때 옮겨 자식의 기존 로컬 변환을 유지하세요.
3. **MapPlacement에만** 위 XY 이동과 Z 회전을 적용합니다. `occupancyMap` 자체의 기본 Z 오프셋은 유지하고 같은 XY 변환을 자식에도 중복 적용하지 않습니다.
4. Content에서 `Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd`를 추가하여 빈 바닥에 배치합니다. 로봇의 XY 위치와 방향을 기록하세요.
5. **Tools > Robotics > ROS 2 OmniGraphs > Clock**에서 Graph Path를 `/World/ROS_Clock`으로 지정하여 시계 그래프를 만듭니다.
6. **File > Save As**로 튜토리얼의 `output/block_world.usd`에 저장하고 Play합니다.

Clock 그래프는 Play Tick을 발행 노드의 실행 입력에, Simulation Time을 `timeStamp`에 연결합니다. 외부 노드의 `use_sim_time=true`는 이 `/clock` 시간을 사용한다는 뜻입니다.

### 실행 결과 확인하기

워크스페이스를 준비한 ROS 터미널에서 실행하세요.

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /clock --once
ros2 launch carter_navigation carter_navigation.launch.py use_sim_time:=true
```

기본 launch는 방금 사용한 기본 창고 지도를 읽습니다. 다른 PNG를 생성기에 넣었다면 그 PNG와 짝인 YAML의 절대 경로를 `map:=...`으로 전달하세요.

RViz에서 먼저 **2D Pose Estimate**로 실제 배치한 로봇의 위치와 방향을 지정합니다. scan이 벽에 겹친 뒤 **Navigation2 Goal / 2D Goal Pose**로 같은 방 안의 빈 공간을 목표로 주세요. 경로 표시와 함께 Isaac Sim 로봇의 이동·정지를 확인합니다. 실습 종료 시 Nav2는 Ctrl+C, 시뮬레이터는 창 닫기로 종료하세요.

저장 USD는 외부 Carter 자산을 참조합니다. USD 파일 하나를 옮겼다고 로봇 메시까지 모두 함께 복사되는 것은 아닙니다.

## 3. 이미지와 지도 좌표의 관계 정리

```text
검은 픽셀 → 로컬 XY의 충돌 블록
          → MapPlacement의 이동·회전 → ROS 지도 좌표의 벽
같은 PNG + YAML → Nav2 지도 ────────→ LiDAR 관측과 비교
```

예를 들어 높이 200픽셀, 해상도 0.05 m, origin `(0,0,0)`인 지도라면 세로 길이는 10 m입니다. 생성기의 위쪽을 Y=10 m로 옮겨야 아래쪽이 ROS의 Y=0 m에 놓입니다. 이 예의 200을 실제 창고 이미지 높이로 대신 쓰지는 마세요.

**초기 pose는 로봇의 위치추정을 맞추고, MapPlacement는 환경 자체의 좌표를 맞춥니다.** 두 작업을 구분하면 벽 전체가 어긋나는 문제를 로봇 위치만 바꿔 해결하려는 시행착오를 줄일 수 있습니다.

## 4. 간단한 확인 실험

기본 지도와 다른 값은 유지하고, 복사한 PNG의 빈 공간에 **검은 장애물 하나만** 추가해 보세요. 같은 `resolution`과 `origin`을 가진 새 YAML이 수정 PNG를 가리키게 합니다.

새 PNG로 블록 장면을 다시 생성하고 같은 좌표 정렬을 적용한 뒤, Nav2에도 새 YAML을 전달합니다. 추가한 위치에 충돌 블록이 생기고 경로가 그 공간을 피하는지 확인하세요. 원래 지도만 계속 사용하면 정적 지도에 기록된 장애물과 센서로만 발견한 장애물을 비교하는 다른 실험이 됩니다.

## 실행할 때 막히면

- **Jazzy 빌드 준비에서 `topic_based_ros2_control` rosdep 오류**: 공식 설치 안내에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control`을 실행한 뒤 rosdep 명령을 다시 수행하세요.
- **Generate 후 로봇이 사라짐**: 생성기가 새 Stage를 만드는 동작입니다. 블록 생성 뒤 로봇과 Clock을 추가하세요.
- **로봇이 떨어짐**: groundPlane 존재와 충돌 설정, 로봇의 시작 높이를 확인하세요.
- **scan이 일정 거리만큼 어긋남**: PNG 높이 H, origin, 부모 변환의 중복 적용을 확인하세요.
- **벽 크기 자체가 다름**: Cell Size와 YAML `resolution`을 맞추세요.
- **미관측 영역이 예상과 다르게 생성됨**: 생성기의 픽셀 임계값과 Nav2 YAML의 점유 판정은 같은 설정이 아닙니다. 입력 픽셀 값을 확인하세요.

Ubuntu 22.04/Humble에서는 위 환경과 워크스페이스 경로의 `jazzy`를 `humble`로 함께 변경합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Navigation with Block World Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation_block_world.html)에 대응합니다. [Mapping과 Block World Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html#block-world-generator), [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)를 함께 참고하세요.

픽셀 좌표와 Collider 설명은 설치된 `isaacsim.asset.importer.heightmap`의 `block_world.py`와 대조했습니다. 좌표 정렬식은 그 구현에서 유도한 보완 설명입니다. 장면 생성·DDS·Nav2 도착은 이번 개정에서 실행하지 않았으며 `tutorial.json`은 `verification: not_run`입니다.
