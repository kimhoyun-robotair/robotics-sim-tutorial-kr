# 124. ROS 2 Navigation with Block World Generator — 2D 지도를 주행 가능한 3D 공간으로

권장 학습 순서 **124** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t025`

공식 Block World Generator GUI를 이용하여 창고의 점유 PNG를 충돌 가능한 3D 벽으로 바꾸고, Nova Carter와 Clock 그래프를 추가하여 Nav2로 주행한다. 자산과 ROS 노드는 공식 5.1 설치/워크스페이스의 것을 사용한다. 다른 로컬 튜토리얼은 필요 없다.

## 이 실습의 의도

2D 점유 지도의 장애물 픽셀을 충돌 가능한 블록으로 바꿔, 같은 지도로 3D 시뮬레이션 주행을 시험하는 실습이다. PNG의 위쪽 원점과 ROS 지도의 아래쪽 원점을 맞추는 과정이 핵심이며, 벽이 보이는 것과 지도 좌표가 맞는 것은 따로 확인한다. 로컬 자동 실행기는 없고 생성기 GUI 조작, 로봇·Clock 그래프 추가, 외부 Nav2 실행을 사용자가 수행한다. 결과 장면은 지도의 기하 구조를 재현하며 원래 창고의 재질이나 세부 외관까지 복원하지 않는다.

## 실행 후 확인할 것

- **블록 생성:** Generate 후 `/World/occupancyMap/occupiedInstances`와 `/World/groundPlane`이 생기고 PNG의 검은 장애물 위치에 회색 벽이 놓이는지 본다. 블록 prototype의 Collider가 있어야 주행용 장애물로 작동한다.
- **지도 크기와 좌표:** Cell Size가 YAML `resolution`과 같은지, PNG 높이 H와 YAML `origin`으로 계산한 XY 이동·회전이 벽과 바닥에 한 번만 적용됐는지 확인한다. `MapPlacement` 부모를 쓰면 자식에도 같은 변환을 중복 적용하지 않는다.
- **로봇과 시계:** Nova Carter를 빈 바닥에 배치한 후 Play하여 바닥 위에 유지되는지 보고, 외부 ROS 터미널에서 `/clock`의 실제 메시지를 확인한다. 생성기만 실행한 단계에는 로봇 주행이나 ROS 시계가 아직 없다.
- **센서와 지도 정렬:** RViz에서 시작 위치·방향을 설정한 뒤 scan이 지도 벽과 겹치는지 본다. 일정한 거리·회전 오차가 남으면 지도 변환과 해상도를 다시 확인한다.
- **주행과 저장물:** 빈 공간으로 목표를 주어 경로 생성→실제 이동→정지를 확인하고 `output/block_world.usd`를 저장한다. 저장 USD의 로봇은 외부 자산 reference이므로 그 자산 경로도 계속 접근 가능해야 한다.

## 설치와 터미널 준비

이 폴더만 복사해도 실습할 수 있다. 다른 로컬 튜토리얼이나 공통 Python 모듈은 필요 없다. 외부 프로그램인 Isaac Sim 5.1.0, 공식 5.1 자산, ROS 2와 아래 공식 ROS 워크스페이스는 필요하다. 아래 명령은 **Ubuntu 22.04 + Humble**, bash 터미널 기준이다. Ubuntu 24.04에서는 `humble`을 `jazzy`로 바꾼다. Windows는 원문에서도 부분 지원이며 이 실습의 검증 대상으로 삼지 않는다.

ROS 2 desktop이 없으면 [Humble 설치](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) 또는 [Jazzy 설치](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debians.html)를 먼저 수행한다. 다음 명령은 사용자 환경에 의존성을 설치하고 새 워크스페이스를 만드는 준비 절차이며 이 패키지가 자동 실행하지 않는다.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
source /opt/ros/humble/setup.bash
# rosdep을 처음 설치한 컴퓨터에서만 sudo rosdep init 실행
rosdep update
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$HOME/IsaacSim-ros_workspaces-5.1"
cd "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws"
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build
source install/local_setup.bash
```

태그의 확인된 커밋은 `50de00358f220d790d17050c6368cfe9a9cb9f51`이다. 이미 같은 폴더가 있다면 clone을 반복하지 말고 그 폴더의 버전과 빌드 결과를 확인한다. Jazzy에서 `topic_based_ros2_control` rosdep 키가 없으면 공식 설치 문서에 따라 `sudo apt install ros-jazzy-topic-based-ros2-control` 후 재시도한다.

**터미널 A — Isaac Sim:** 일반 `/opt/ros` Python 환경을 source하지 않은 새 터미널에서 실행한다. Isaac Sim은 Python 3.11, Ubuntu의 ROS Python은 3.10/3.12이므로 기본 메시지를 DDS로 교환하는 이 실습은 내부 ROS 라이브러리를 사용한다. 같은 배포판을 A/B 양쪽에서 선택한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
# 새 터미널에서 한 번만 추가한다.
export LD_LIBRARY_PATH="$ISAAC_SIM_PATH/exts/isaacsim.ros2.bridge/$ROS_DISTRO/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

`Window > Extensions`에서 `isaacsim.ros2.bridge`를 검색하여 Enabled를 켠다. 5.1 자산 서버에 접근할 수 있어야 기본 장면을 불러올 수 있다. 로컬 자산팩을 쓰는 경우 Content 창에서 그 팩의 `Isaac` 폴더를 사용한다.

**터미널 B 및 이후 모든 ROS 터미널:** 매번 아래를 실행한 뒤 본문 ROS 명령을 실행한다.

```bash
source /opt/ros/humble/setup.bash
source "$HOME/IsaacSim-ros_workspaces-5.1/humble_ws/install/local_setup.bash"
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

같은 컴퓨터에서는 Fast DDS 기본 설정을 쓴다. 다른 컴퓨터/컨테이너라면 위 워크스페이스의 `fastdds.xml` 절대 경로를 `FASTRTPS_DEFAULT_PROFILES_FILE`로 **A와 B 모두** 지정하고 통신 가능한 네트워크를 사용한다. 배포판/Domain ID가 다르면 노드가 발견되지 않는다.

## 지도 파일과 좌표 준비

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-pointcloud-to-laserscan
ros2 pkg prefix carter_navigation
```

입력 파일은 `$HOME/IsaacSim-ros_workspaces-5.1/humble_ws/src/navigation/carter_navigation/maps/carter_warehouse_navigation.png`이며, 같은 디렉터리의 `carter_warehouse_navigation.yaml`을 텍스트 편집기로 연다. `resolution`과 `origin: [x,y,yaw]`를 기록한다. `resolution`은 PNG 픽셀 한 칸의 미터 수다. 아래에서는 YAML 값을 직접 사용하며 임의 기본값을 추측하지 않는다.

- USD의 **Stage**는 장면 전체, **prim**은 그 안에서 `/World/occupancyMap`처럼 경로를 가진 물체/그래프다.
- `UsdGeom.PointInstancer`는 같은 블록 형상을 여러 위치에 효율적으로 배치한다. 5.1 생성기는 검은 픽셀(첫 채널 <127)에 높이 2 m 블록을 놓고 prototype에 `UsdPhysics.CollisionAPI`를 적용한다.
- PNG의 행은 아래로 증가하지만 ROS 지도 y는 위로 증가한다. 생성기는 이미지 왼쪽 위를 `(0,0)`으로 하고 y를 음수로 만든다. YAML origin은 지도 왼쪽 아래다. **맵 원점 정렬을 생략하면 시각적으로 벽이 있어도 Nav2 지도와 좌표가 어긋날 수 있다.**

## 1. 3D 벽 생성

1. 저장하지 않은 다른 작업이 없도록 새 Stage를 연다. 생성기는 새 Stage를 만드는 기능이므로 먼저 저장할 작업이 있으면 저장한다.
2. `Tools > Robotics > Block World Generator`를 연다. 메뉴가 없으면 `Window > Extensions`에서 `isaacsim.asset.importer.heightmap`을 켠다.
3. **Cell Size**를 YAML `resolution` 값으로 설정한다. **Load/Load Image**를 눌러 위 PNG를 선택하고 Visualization을 확인한다.
4. **Generate/Generate Block World**를 눌러 생성한다. Stage에서 `/World/occupancyMap/occupiedInstances`와 `/World/groundPlane`이 보이는지 확인한다. 회색 벽, 바닥, 기본 조명이 만들어진다.
5. 아래 좌표 정렬을 적용한다. 원문에 생략된 5.1 생성기 좌표 처리를 보완한 단계다. PNG 높이를 H(픽셀), Cell Size를 r, YAML origin을 `(ox,oy,θ)`라고 하면 생성된 occupancyMap의 Transform에서 **Translate X = ox - sin(θ)·H·r, Translate Y = oy + cos(θ)·H·r**, Rotate Z = θ의 도 변환값으로 한다. 기존 Translate Z(셀 크기의 절반)는 유지한다. 기본 창고 지도처럼 θ=0이면 X=ox, Y=oy+H·r이다. PNG 높이는 이미지 뷰어의 속성에서 확인한다.
6. 바닥도 같은 XY 회전/이동을 적용해야 한다. 더 쉽게 하려면 `/World` 아래 새 Xform `/World/MapPlacement`를 만들고 `occupancyMap`과 `groundPlane`을 그 아래로 옮긴 뒤 **이 부모 Xform 하나에만** 위 XY 이동과 Z 회전을 적용한다. 자식의 기존 로컬 Transform은 유지한다. 이 방법을 쓰면 5번에서 occupancyMap에 직접 설정했던 XY/회전을 원래 값으로 되돌려 중복 적용을 막는다.

좌표가 이미 맞는 이미지/원점 조합이면 offset은 0이다. 실제 지도 벽과 LiDAR가 맞는지는 RViz에서 최종 확인한다.

## 2. 로봇과 ROS 시계 추가

1. Content의 `Isaac Sim > Samples > ROS2 > Robots`에서 **Nova_Carter_ROS.usd**를 드래그한다. 자산 루트 상대 경로는 `Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd`다.
2. 로봇을 바닥의 넓고 빈 공간에 놓고 X/Y/Rotate Z를 기록한다. 바닥에 관통하지 않도록 Z를 맞춘다. 카메라 Top과 Perspective를 번갈아 사용한다. 블록 벽 위에 놓지 않는다.
3. `Tools > Robotics > ROS 2 OmniGraphs > Clock`을 선택하고 Graph Path를 `/World/ROS_Clock`으로 지정해 **OK**를 누른다.
4. `Window > Graph Editors > Action Graph`에서 해당 그래프를 연다. **On Playback Tick**의 tick은 **ROS 2 Publish Clock**의 execIn, **Isaac Read Simulation Time**의 simulationTime은 publisher의 timeStamp, **ROS 2 Context**의 context는 publisher context로 연결된다. topicName은 `clock`이다.
5. `ROS2Context`는 Domain ID를 선택하고 `ROS2PublishClock`은 `/clock`에 `rosgraph_msgs/Clock`을 보낸다. 외부 노드의 `use_sim_time=true`는 이 시계를 사용하겠다는 뜻이다. `/clock` 게시자를 여러 개 만들지 않는다.
6. **File > Save As**로 이 폴더의 새 `output/block_world.usd`에 저장한다. 외부 로봇 reference가 있으므로 USD 하나에 모든 로봇 메시가 내장되는 것은 아니다.

## 3. Nav2로 주행

1. Isaac Sim에서 **Play**를 누른다.
2. ROS 터미널에서 실행한다.

```bash
ros2 topic echo /clock --once
ros2 launch carter_navigation carter_navigation.launch.py use_sim_time:=true
```

3. RViz의 **2D Pose Estimate**로 앞에서 기록한 로봇 위치와 방향을 지정한다. 생성 장면의 시작 위치는 기본 창고 예제와 다르므로 목표보다 초기 위치 설정이 먼저다.
4. LiDAR scan이 지도 벽에 겹치는지 확인한다. 방향이 반대이거나 일정 거리만큼 어긋나면 초기 pose만 반복 조정하지 말고 Cell Size, H, YAML origin 및 MapPlacement 변환을 점검한다.
5. **Navigation2 Goal/2D Goal Pose**로 같은 방 안의 빈 공간을 지정한다. 경로가 표시되고 로봇이 실제로 이동·정지하면 첫 실습 성공이다. 다음 목표는 문을 지나 옆 공간으로 지정한다.

```bash
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo map base_link
```

연속 관측 명령은 Ctrl+C로 종료한다. Nav2 launch 역시 종료 후 다른 실습을 시작한다.

## 확인과 한 변수 실험

성공 기준은 생성된 충돌 벽, 증가하는 `/clock`, 지도와 scan 정렬, 경로를 따른 실제 로봇 이동이다. 점유 픽셀을 블록으로 바꾼 장면은 원래 창고의 사진 사실적 외관을 복원하지 않는다. 지도와 같은 기하 배치를 이용한 주행 실험이다.

한 변수 실험: 원본 PNG를 이 패키지 `output/`에 복사해 흰 영역에 작은 검은 장애물 하나를 추가한다. 같은 해상도로 다시 생성하고, 지도 YAML/PNG도 같은 수정본을 Nav2에 전달한다. 기존 지도만 쓰는 경우에는 센서의 동적 장애물 회피가 어떻게 동작하는지 구분해서 관찰한다.

메뉴 없음은 heightmap/bridge 확장을, 로봇 추락은 바닥 Collider와 Z를, 목표 거절은 지도 빈 공간과 초기 pose를 확인한다. 생성 화면에서 회색 미관측 픽셀은 검은 장애물과 같지 않다. 실제 생성은 5.1의 픽셀 임계값을 따르므로 예상치 못한 벽은 이미지 채널 값을 확인한다.

## 출처와 검증 범위

- [Isaac Sim 5.1 Block World Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation_block_world.html).
- [5.1 Block World Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html#block-world-generator).
- [5.1 Clock shortcut](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html#graph-shortcut).
- [5.1 ROS 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html).

좌표 설명은 설치된 `exts/isaacsim.asset.importer.heightmap/isaacsim/asset/importer/heightmap/block_world.py`의 픽셀→좌표 계산에 대조했다. GPU 장면 생성·DDS·Nav2 실행은 미검증이며 `verification: not_run`이다.
