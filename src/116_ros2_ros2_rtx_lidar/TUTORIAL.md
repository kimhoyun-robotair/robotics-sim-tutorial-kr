# 116. 2D·3D RTX LiDAR를 ROS 2와 RViz에서 관찰하기

권장 학습 순서 **116** · ROS 2 연결과 기본 통신 · 출처 ID `t014`

Isaac Sim 5.1 **RTX Lidar Sensors**를 독립 실행 패키지로 재구성했다. 2D 회전형 센서가 `/scan`에 LaserScan을 보내고, 3D 센서가 `/point_cloud`에 PointCloud2를 보낸다. 두 센서와 벽·표적을 코드로 만들므로 TurtleBot이나 창고 자산을 준비하지 않아도 된다. 원문의 로봇 부착, GUI 그래프, 단축 메뉴, 여러 센서 시간 동기화는 아래에서 같은 원리로 실습한다.

## 이 실습의 의도

같은 위치의 2D·3D RTX LiDAR가 주변 기하를 각각 수평 거리 배열과 3D 점군으로 표현하는 차이를 확인한다. 네 벽과 +X 방향 표적은 거리와 단면을 해석할 기준물이며, 두 센서에 별도 Render Product를 붙인다. 기본 실행은 부분 3D 점군과 완성된 2D LaserScan 및 시계를 발행하고, 로봇 이동이나 센서 TF 구성은 포함하지 않는다.

## 실행 후 확인할 것

- Stage의 `/World/Lidar2D`, `/World/Lidar3D`가 같은 위치 (0,0,1) m에 있고 각 Helper가 자기 Render Product를 참조하는지 확인한다. `--profile`은 3D 센서만 바꾸며 2D는 항상 `Example_Rotary_2D`다.
- `/scan`의 타입은 `sensor_msgs/msg/LaserScan`, `/point_cloud`는 `sensor_msgs/msg/PointCloud2`이고 두 메시지의 `header.frame_id`는 `base_scan`이어야 한다. ranges와 점군 width/point_step/data가 채워지고 timestamp가 진행하는지 실제 수신으로 확인한다.
- RViz Fixed Frame=`base_scan`에서 LaserScan은 벽·표적의 수평 단면, PointCloud2는 높이 방향을 포함한 표면을 보여야 한다. +X 표적의 가까운 면은 약 1.5 m이며 개별 광선 표본이 정확히 그 값에 놓일 필요는 없다.
- `/clock`을 수신하고 RViz의 `use_sim_time=true`를 적용한다. `/tf` 발행기는 없는 구성이므로 Fixed Frame=`world`에서 변환 오류가 나는 것은 world 기준 시각화를 아직 구성하지 않았다는 뜻이다.
- LaserScan은 한 회전의 데이터가 준비될 때까지 기다린다. 60 render frame/s 설정과 센서의 완전 스캔 발행 주기는 다르므로 매 프레임 새 LaserScan을 요구하지 않는다.
- 기본 실행과 `--full-scan` 실행의 `/point_cloud` 점 수·수신 간격을 비교한다. 전체 스캔을 누적하는 3D 출력의 차이를 관찰하고, 변경하지 않은 `/scan` 설정과 구분한다. 실제 Hz는 GPU와 센서 프로필에 따라 달라진다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 시뮬레이션 스텝과 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 지정하면 해당 횟수 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1800회를 사용합니다. 이전 `--frames` 옵션은 `--steps` 없는 headless 실행의 횟수만 정하며, GUI 종료에는 영향을 주지 않습니다. `--steps`를 지정하면 `--frames`보다 우선하며 0과 음수는 허용하지 않습니다.

## 준비와 실행

Isaac Sim **5.1.0**과 지원되는 RTX GPU가 필요하다. ROS 2 Humble(Ubuntu 22.04) 또는 Jazzy(Ubuntu 24.04), `sensor_msgs`, RViz2를 준비한다. ROS 2를 source한 셸에서 Isaac Sim을 실행해야 한다. 이 폴더만 복사해도 다른 튜토리얼을 import하지 않는다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ISAAC_SIM=/home/hoyunkim/isaacsim
"$ISAAC_SIM/python.sh" run.py
```

Jazzy 환경에서는 source 경로를 바꾼다. 다른 터미널도 같은 ROS 배포판과 Domain ID를 사용한다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
ros2 topic echo /scan --once
ros2 topic hz /scan
ros2 topic hz /point_cloud
rviz2 --ros-args -p use_sim_time:=true
```

GUI는 기본적으로 창을 닫을 때까지 유지된다. 유한 실행은 `--steps 1800`, 창 없는 실행은 `--headless`를 사용한다. Fast DDS 사용자 설정을 사용하는 환경에서는 `FASTRTPS_DEFAULT_PROFILES_FILE`을 실제 XML 파일의 절대 경로로 지정한 뒤 양쪽 프로세스를 시작한다. 존재하지 않는 파일을 임의로 지정하지 않는다. 단일 호스트의 기본 DDS 설정으로도 본 예제 실행을 먼저 확인할 수 있다.

## RViz 실습과 성공 기준

1. RViz의 **Global Options > Fixed Frame**을 `base_scan`으로 설정한다. 두 센서의 원점은 USD world에서 `(0,0,1)` m이고 메시지는 센서 로컬 좌표로 표현된다. 본 코드는 움직이는 로봇의 TF를 발행하지 않으므로 `world`로 지정하면 변환을 찾지 못한다.
2. **Add > LaserScan**을 선택하고 Topic=`/scan`, Size(m)=`0.03`으로 설정한다. XY 평면에서 주변 네 벽과 +X 방향 큐브 표적의 단면을 관찰한다.
3. **Add > PointCloud2**를 선택하고 Topic=`/point_cloud`, Style=`Points`, Size(Pixels)=`2`로 설정한다. 위아래 방향의 표면도 포함하는 3D 점군이 보여야 한다.
4. 토픽별 메시지의 `header.frame_id`가 `base_scan`인지, timestamp가 증가하는지 확인한다. LaserScan의 `ranges` 배열과 PointCloud2의 width/point_step/data가 실제로 채워지는지 본다.
5. 표적의 가장 가까운 면은 센서 +X 방향 약 1.5 m 위치다. 센서 각도 표본과 표면 교차에 따라 해당 주변 점들이 있는지 확인한다. 화면에 토픽 이름만 보이는 상태는 센서 검증이 아니다.

RViz QoS가 맞지 않으면 Display의 Reliability를 Best Effort로 바꾸어 확인하고 `ros2 topic info -v /scan`으로 publisher의 실제 설정을 읽는다.

## 코드에서 알아야 할 개념

- **RTX LiDAR**는 광선과 렌더 장면의 교차로 거리를 얻는 센서다. 일반 CPU 물리 raycast 센서와 구현 경로가 다르다. 보이는 표면의 재질/기하가 센서 결과에 영향을 준다.
- **USD prim**은 장면 안 객체이며 `/World/Lidar3D`와 `/World/Lidar2D`가 센서 경로다. 바닥·벽도 `UsdGeom.Cube` prim이다. Stage의 단위는 1 m, 위쪽 축은 Z다.
- `omni.kit.commands.execute('IsaacSensorCreateRtxLidar', ...)`는 이름에 해당하는 설정으로 센서를 만든다. `Example_Rotary`는 3D 회전형, `Example_Rotary_2D`는 2D 회전형, `Example_Solid_State`는 solid-state 예시다. `Gf.Quatd(1,0,0,0)`는 `(w,x,y,z)` 순서의 항등 회전이다.
- 각 센서는 **자기 Render Product**를 가져야 한다. `rep.create.render_product(sensor.GetPath(), [1,1])`의 1×1은 카메라 RGB 해상도처럼 점 수를 1로 제한하는 값이 아니다. LiDAR의 광선 패턴은 센서 설정이 정한다.
- **ROS2RtxLidarHelper**는 Render Product와 `type`에 맞춰 센서 후처리/ROS writer를 만든다. 본 코드는 `point_cloud`와 `laser_scan` Helper를 각기 생성한다. `fullScan`은 3D 점군을 한 스캔으로 누적할지 정한다.
- `ROS2Context`는 DDS 통신 영역을 지정한다. `useDomainIDEnvVar=True`이므로 실행 셸의 ROS_DOMAIN_ID를 사용한다. `ROS2PublishClock`은 같은 시뮬레이션의 `/clock`을 발행한다.

원문의 Python 예제는 Helper 대신 `rep.writers.get('RtxLidarROS2PublishPointCloud')` 또는 `RtxLidarROS2PublishLaserScan`을 만들고 `initialize(topicName=..., frameId=...)`, `attach([product])`를 호출한다. 본 코드는 원문 GUI와 대응하기 쉬운 Helper 방식으로 같은 센서 흐름을 구성했다. 설치된 native 예제는 다음 위치에서 별도로 실행할 수 있다.

```bash
cd "$ISAAC_SIM"
./python.sh standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py
```

native 예제에는 `/Isaac/Environments/Simple_Warehouse/full_warehouse.usd` NVIDIA 자산 접근이 필요하다. 이 패키지의 로컬 실험은 해당 자산을 사용하지 않는다. 프로필 파일을 조사하려면 설치 폴더의 `extsbuild/omni.sensors.nv.common/data/lidar/` 또는 확장 캐시의 `omni.sensors.nv.common` 데이터 위치에서 `Example_Rotary.json`을 찾는다. 설치 배포 방식에 따라 물리적인 경로가 다를 수 있지만 프로필 이름은 코드에 그대로 사용한다.

## 스캔과 프레임은 다르다

시뮬레이션은 60 render frame/s로 설정했다. 회전 속도가 10 Hz인 회전형 센서라면 한 바퀴를 얻는 데 약 6프레임이 필요하다. **LaserScan은 완전한 스캔이 준비된 뒤 발행**된다. 따라서 프레임마다 메시지를 기대하면 안 된다. solid-state는 설정된 전체 방위각을 한 프레임에 완료할 수 있다.

PointCloud2는 부분 스캔을 프레임마다 보내거나 전체 스캔을 누적해 보낼 수 있다.

```bash
"$ISAAC_SIM/python.sh" run.py --full-scan
"$ISAAC_SIM/python.sh" run.py --profile Example_Solid_State
```

변수 하나만 바꾸기: 먼저 기본 실행과 `--full-scan`만 추가한 실행의 `/point_cloud` 수신 빈도와 점 개수를 비교한다. 이후 별도 실험으로 profile만 바꾼다. 2D 센서는 두 경우 모두 Example_Rotary_2D이므로 `/scan` 변화와 혼동하지 않는다. 실제 벽시계 발행 빈도는 GPU 렌더 속도에 영향을 받는다.

## GUI로 로봇에 붙이기와 그래프 재구성

1. 현재 장면에서 Stop한다. **Create > Xform**으로 `/World/Robot`을 만들고 그 아래 `/World/Robot/base_scan` Xform을 만든다. base_scan의 Translate를 `(0,0,1)`로 설정한다. 이는 로봇 스캐너 부착 위치를 나타내는 간단한 mount다.
2. **Create > Sensors > RTX Lidar > NVIDIA > Example Rotary 2D**를 선택한다. 생성된 센서 prim을 base_scan 아래로 드래그하고 Translate/Rotate를 모두 0으로 만든다. **Example Rotary**도 같은 방식으로 추가한다. 실제 TurtleBot 장면이라면 부모 경로는 `/World/turtlebot3_burger/base_scan`이다.
3. **Window > Graph Editors > Action Graph**에서 새 그래프를 만든다. **On Playback Tick → Isaac Run One Simulation Frame → Isaac Create Render Product**로 실행 포트를 연결한다. Render Product 노드를 두 개 만들어 각각 2D/3D 센서를 cameraPrim으로 지정한다.
4. **ROS2 Context**와 **ROS2 RTX Lidar Helper** 두 개를 추가한다. 각 Render의 execOut/renderProductPath를 해당 Helper에 연결하고 Context의 context도 연결한다. 2D Helper=`type: laser_scan`, `topicName: manual_scan`, `frameId: base_scan`; 3D Helper=`type: point_cloud`, `topicName: manual_cloud`, 같은 frameId를 넣는다.
5. 3D Helper의 **Publish Full Scan**을 켜고 끈 두 실행을 비교한다. 원래 코드 그래프와 구별되는 manual 토픽을 사용하므로 여러 publisher가 같은 토픽을 보내는 혼선을 피한다.
6. 단축 메뉴는 **Tools > Robotics > ROS 2 OmniGraphs > RTX Lidar**다. Graph Path=`/World/ShortcutLidar`, Lidar Prim=방금 만든 3D 센서, Frame ID=`base_scan`, Node Namespace=`shortcut`을 넣고 Point Cloud를 선택한다. 기존 그래프에 추가할 때만 **Add to an existing graph?**를 켠다.

RTX LiDAR가 실행 중일 때 창을 다시 docking하면 충돌할 수 있다는 5.1 공식 주의사항이 있다. 위 GUI 배치 변경과 그래프 편집 전에는 Stop 또는 Pause한다.

## 여러 센서를 같이 보기

RGB 카메라·depth·LiDAR를 한 RViz에 표시하려면 (1) 일치하는 timestamp 기준, (2) `/clock`, (3) 모든 frame을 잇는 TF가 필요하다. Camera의 frameId는 예를 들어 `front_rgb`, namespace는 `front/rgb`, topic은 `image_raw`처럼 센서/데이터 종류를 나타낼 수 있다. LiDAR는 `base_scan`, `/scan`, `/point_cloud`를 사용한다. frameId는 nodeNamespace가 자동으로 붙는 토픽 이름과 다르다.

원문 전체 조합은 Content Browser의 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd**에서 볼 수 있다. 해당 자산과 NVIDIA ROS 2 워크스페이스가 준비되었다면 아래에서 실제 워크스페이스 경로를 넣는다.

```bash
rviz2 -d /absolute/path/to/humble_ws/src/isaac_tutorials/rviz2/camera_lidar.rviz
ros2 param set /rviz use_sim_time true
```

단일 LiDAR native 예제의 RViz 설정은 같은 폴더의 `rtx_lidar.rviz`다. `/rviz` 노드 이름이 다르면 `ros2 node list`로 찾고 그 이름에 파라미터를 설정한다. 이 외부 자산 실습은 본 코드의 기본 실행 조건이 아니다.

## 문제 해결·출처

토픽이 없으면 Bridge 로드, Play 상태, ROS_DOMAIN_ID부터 확인한다. LaserScan이 늦게 시작하면 전체 회전이 완료될 때까지 기다린다. 점군이 보이지 않으면 Fixed Frame=`base_scan`과 QoS를 확인한다. 센서 생성 오류는 RTX 지원 GPU/드라이버와 프로필 이름을 확인한다. WSL의 일부 대역폭이 큰 토픽은 Windows RViz에서 제대로 보이지 않을 수 있다.

[Isaac Sim 5.1 RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html), [ROS 2 Bridge 그래프](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html#adding-a-rtx-lidar-ros-2-bridge), [Python 센서 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html#rtx-lidar-script-sample), [여러 센서의 시간·frame](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html#multiple-sensors-in-rviz2).

로컬 코드와 해설은 새로 작성했으며 5.1 설치 예제·노드 스키마를 대조했다. 실제 GPU 센서와 ROS 수신 검증 상태는 `tutorial.json`에서 확인한다.
