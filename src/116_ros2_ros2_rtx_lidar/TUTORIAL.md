# 116. 같은 벽을 2D LiDAR와 3D 점군으로 보기

## 이번에 배우는 것

**같은 위치에 둔 2D·3D RTX LiDAR의 출력을 비교하고, 렌더 프레임과 완성된 스캔의 차이를 확인합니다.**

2D LiDAR는 한 평면에서 방향별 거리를 측정합니다. 3D LiDAR는 높이 방향까지 포함한 광선으로 표면을 관찰합니다. 이번에는 네 벽과 표적을 직접 만들어 각 결과가 무엇을 표현하는지 읽습니다.

| 센서 | 기본 프로필 | ROS 출력 |
|---|---|---|
| `/World/Lidar2D` | `Example_Rotary_2D` | `/scan`: LaserScan |
| `/World/Lidar3D` | `Example_Rotary` | `/point_cloud`: PointCloud2 |
| 공통 시간 그래프 | 1/60초 시뮬레이션 간격 | `/clock` |

두 센서는 `(0,0,1)` m에 같은 방향으로 놓이며 메시지 frame은 `base_scan`입니다. 로봇 주행이나 TF 발행은 포함하지 않습니다.

## 1. 두 센서 실행하고 RViz에서 보기

Isaac Sim 5.1, RTX GPU, Ubuntu 24.04의 ROS 2 Jazzy와 RViz2를 준비합니다. 저장소 루트의 Bash에서 실행하세요. Ubuntu 22.04/Humble에서는 `jazzy` 값과 라이브러리·source 경로를 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸입니다. 설치 위치를 맞추고 내부 브리지를 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/116_ros2_ros2_rtx_lidar/run.py
```

GUI는 창을 닫을 때까지 실행합니다. `--steps 1800`은 1800스텝 후 종료하며 `--headless`만 지정하면 같은 기본 한도를 사용합니다. `--frames`는 `--steps`가 없는 headless 실행에만 적용됩니다.

터미널 B에서는 시스템 ROS를 준비합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /scan --once
rviz2 --ros-args -p use_sim_time:=true
```

1. RViz **Global Options > Fixed Frame**을 `base_scan`으로 둡니다.
2. **Add > LaserScan**에서 Topic=`/scan`, Size(m)=`0.03`으로 설정합니다.
3. **Add > PointCloud2**에서 Topic=`/point_cloud`, Style=`Points`, Size(Pixels)=`2`로 설정합니다.
4. 수평 단면과 높이가 있는 표면의 차이를 살펴보세요.

### 실행 결과 확인하기

`/scan`에서 `ranges` 배열이 채워지고 timestamp가 진행하는지 확인합니다. PointCloud2는 `width`, `height`, `point_step`, `data`에 실제 점 데이터가 있어야 합니다. 둘의 `header.frame_id`는 `base_scan`입니다.

LaserScan의 `ranges[i]`는 `angle_min + i × angle_increment` 방향의 거리(m)입니다. 각도 단위는 rad이며 센서 +X가 0, +Z를 축으로 반시계 방향이 양수입니다. 그러므로 배열 첫 항목을 무조건 +X 방향으로 읽지 말고 `angle_min`을 확인하세요. `range_min`~`range_max` 밖의 값과 무한값은 유효한 표면 거리에서 제외합니다.

PointCloud2의 `data`는 바이트 배열입니다. `fields`에 기록된 x·y·z의 자료형과 offset, `point_step`의 점당 바이트 수를 사용해 읽어야 합니다. `width×height`는 점 수이고 `data`의 바이트 수는 `row_step×height`입니다. 이 두 크기를 같은 숫자로 기대하지 마세요. 각 필드의 규약은 Jazzy의 [LaserScan](https://raw.githubusercontent.com/ros2/common_interfaces/jazzy/sensor_msgs/msg/LaserScan.msg)과 [PointCloud2](https://raw.githubusercontent.com/ros2/common_interfaces/jazzy/sensor_msgs/msg/PointCloud2.msg) 정의에서 확인할 수 있습니다.

표적은 `(2,0,1)` m 중심에 x 방향 크기 1 m로 생성됩니다. 따라서 센서 +X 방향에서 가까운 면은 **약 1.5 m**입니다. 해당 방향 근처에 점들이 있는지 관찰하세요. 광선이 표면을 비스듬히 만나거나 각도 표본이 정확히 +X가 아니면 개별 range가 꼭 1.5일 필요는 없습니다.

이 코드는 TF를 만들지 않으므로 Fixed Frame을 `world`로 바꾸면 필요한 변환이 없습니다. 센서 로컬 좌표에서 측정값을 먼저 이해하는 구성입니다.

## 2. 센서 프로필과 발행 Helper 읽기

### 코드에서 볼 부분

```python
ok, sensor = omni.kit.commands.execute(
    'IsaacSensorCreateRtxLidar', path='/World/' + name, parent=None,
    config=profile, translation=(0,0,1), orientation=Gf.Quatd(1,0,0,0))
```

프로필은 광선의 방향과 스캔 방식 같은 센서 설정을 정합니다. `Gf.Quatd(1,0,0,0)`은 w/x/y/z 순서의 항등 회전입니다. 센서 생성에 실패하면 정상 출력처럼 진행하지 않고 오류를 냅니다.

각 센서에는 별도 Render Product를 붙입니다.

```python
rep.create.render_product(sensor.GetPath(), [1,1], name=name)
```

여기서 1×1은 일반 RGB 이미지의 해상도처럼 LiDAR 점 수를 1개로 제한하는 뜻이 아닙니다. 측정 광선 패턴은 센서 프로필이 정합니다. 센서마다 독립적인 렌더 출처를 두고 Helper가 올바른 출처를 읽게 합니다.

`/World/LidarGraph`의 Cloud Helper는 `type=point_cloud`, Scan Helper는 `type=laser_scan`입니다. 두 Helper에 Tick과 ROS2 Context를 연결합니다. `--full-scan` 옵션은 Cloud의 `fullScan` 입력에만 연결되며 2D 센서는 그대로입니다.

### 프레임과 스캔에서 볼 부분

```text
여러 렌더 프레임의 광선 측정 → 한 회전의 스캔 완성
         ├─ 부분 PointCloud2로 보내기
         └─ 모아 두었다가 전체 스캔으로 보내기
```

회전 센서의 한 바퀴가 여러 렌더 프레임에 걸칠 수 있습니다. 예를 들어 **회전 속도가 10 Hz인 센서**를 60 render frame/s로 처리한다면 한 바퀴에 약 6프레임이 필요합니다. 이는 계산 예시이며 선택한 프로필의 회전 속도는 별도로 확인해야 합니다.

LaserScan은 완성된 스캔을 기다립니다. 반면 3D 점군은 기본적으로 부분 결과를 보내고 `--full-scan`이면 누적된 결과를 사용합니다. 시뮬레이션이 60번 렌더링된다는 이유로 LaserScan도 60개여야 한다고 판단하면 안 됩니다.

### GUI에서 같은 연결 확인하기

Stop한 상태에서 **Window > Graph Editors > Action Graph**로 `/World/LidarGraph`를 여세요. Cloud와 Scan의 `renderProductPath`가 서로 다른 센서를 가리키는지 확인합니다.

센서를 로봇에 부착하는 구조를 연습하려면 새 Xform `/World/Robot/base_scan`을 만들고 센서를 그 아래 놓을 수 있습니다. 부모의 높이를 1 m로 정했다면 자식 센서의 로컬 Translate는 0으로 맞춥니다. 같은 높이를 양쪽에 넣으면 최종 높이가 2 m가 됩니다.

새 발행기는 **Tools > Robotics > ROS 2 OmniGraphs > RTX Lidar**에서 센서 prim, Graph Path, Frame ID와 Point Cloud 또는 Laser Scan을 지정해 만들 수 있습니다. 기존 실행과 함께 비교할 때는 `manual_scan` 같은 별도 토픽을 사용하세요. 창 배치 변경은 RTX LiDAR가 실행 중일 때 하지 말고 Pause 또는 Stop 후 진행합니다.

노드를 직접 놓는 경우에는 새 그래프에서 **Tick → Isaac Run One Simulation Frame → Isaac Create Render Product**로 연결합니다. 센서마다 Render 노드를 두고 `cameraPrim`에 실제 센서 prim을 지정하세요. Render의 `execOut`과 `renderProductPath`를 해당 ROS2 RTX Lidar Helper에, ROS2 Context를 두 Helper의 `context`에 연결합니다. 2D Helper는 `laser_scan/manual_scan`, 3D Helper는 `point_cloud/manual_cloud`를 type/topic으로 지정하면 기존 토픽과 구분해 확인할 수 있습니다.

### Python writer와 여러 센서로 확장하기

로컬 앱을 닫은 뒤 설치 예제를 다음처럼 실행하면 Helper 대신 `rep.writers.get()`과 `writer.attach()`로 연결하는 경로를 비교할 수 있습니다.

```bash
"$ISAAC_SIM/python.sh" "$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py"
```

이 예제는 `/Isaac/Environments/Simple_Warehouse/full_warehouse.usd`를 불러옵니다. 자산 접근을 준비하고 `/point_cloud`, `/scan`의 실제 출력을 확인하세요. 로컬 CLI 옵션이 있는 파일은 아니며 GUI 창을 닫아 종료합니다.

카메라와 LiDAR를 한 RViz에 함께 놓을 때는 두 토픽이 있다는 것만으로 충분하지 않습니다. 각 센서의 frame을 TF로 연결하고 동일한 시뮬레이션 시각을 사용해야 합니다. 통합 장면을 확인하려면 Content Browser의 `Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd`를 열고 카메라·LiDAR의 `header.frame_id`, `/tf`, `/clock`을 대조하세요. RViz의 Fixed Frame에는 실제 공통 부모 frame을 선택합니다. 이 별도 장면의 로봇 TF는 현재 로컬 코드에 자동 추가되지 않습니다.

## 3. 같은 표면의 두 표현 정리

| 비교점 | LaserScan | PointCloud2 |
|---|---|---|
| 기본 형태 | 각도에 대응하는 거리 배열 | 3차원 점 배열 |
| 장면에서 보이는 부분 | 센서 평면의 단면 | 높이까지 포함한 표면 |
| 시간 해석 | 스캔 완료를 기다림 | 부분 또는 전체 누적 선택 |

두 센서가 같은 `base_scan` frame을 쓰는 것은 이 예제에서 원점과 방향을 같게 설정했기 때문입니다. 서로 다른 위치에 장착한 센서라면 frame을 구분하고 TF로 연결해야 합니다. 토픽 namespace와 공간 좌표계 이름은 같은 역할이 아닙니다.

## 4. 간단한 확인 실험

기본 실행을 종료하고 **`--full-scan`만 추가**해 보세요.

```bash
"$ISAAC_SIM/python.sh" src/116_ros2_ros2_rtx_lidar/run.py --full-scan
```

`/point_cloud`의 한 메시지에 담긴 점 수(`width×height`)와 수신 간격을 이전 실행과 비교합니다. 부분 스캔을 모으므로 보통 한 메시지의 범위가 넓어지고 발행 간격도 달라집니다. `/scan`의 센서와 설정은 바꾸지 않았습니다. 두 토픽을 함께 관찰해 어떤 출력에 옵션이 적용되는지 확인하세요.

## 실행할 때 막히면

- **LaserScan만 늦게 나옴**: 센서의 완전한 스캔이 준비될 때까지 기다리세요. 앱 시작 직후 짧은 관찰로 실패를 단정하지 않습니다.
- **점군이 RViz에 안 보임**: Fixed Frame=`base_scan`과 publisher QoS를 확인하세요. `ros2 topic info -v /point_cloud`로 정책을 읽습니다.
- **센서 생성 실패**: RTX 지원 GPU·드라이버와 프로필 이름을 확인하세요. `--profile`은 `Example_Rotary`, `Example_Solid_State`만 지원하며 3D 센서에만 적용됩니다.
- **받는 Hz가 예상보다 낮음**: 프로필의 스캔 주기와 GPU 렌더 처리량을 함께 확인하세요. `ros2 topic hz`는 벽시계 수신률입니다.
- **UI를 옮기는 중 충돌**: 5.1 공식 문서는 LiDAR 실행 중 창 docking을 피하도록 안내합니다. 다시 실행해 Pause 후 창을 배치하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html)에 대응합니다. 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 TurtleBot·창고 대신 직접 만든 표적 장면과 두 센서를 사용합니다. Helper의 부분·전체 스캔 분기는 설치된 5.1 코드와 대조했습니다. `tutorial.json`은 `verification: not_run`이며 실제 RTX 거리값·점군·DDS 수신을 이번 문서 개정에서 측정한 것은 아닙니다.
