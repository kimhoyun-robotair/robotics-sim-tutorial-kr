# Isaac Sim 4.x에서 5.1.0으로: 변경 사항과 코드 이관

이 문서는 Ubuntu 24.04 LTS / ROS 2 Jazzy / Isaac Sim 5.1.0에서 이전 예제를 다시 실행할 때 확인할 내용을 정리한다. 버전별 변경 사실과 이 튜토리얼의 점검 방법을 구분한다. NVIDIA 릴리스 노트의 전체 번역이 아니라 설치, 로봇 제어, 센서, ROS 2 실습에 영향을 주는 항목을 골라 설명한 자료이다.

처음 배우는 독자는 [과정 사용법](../course-guide.md)부터 실습하고, 예전 코드에서 오류가 나거나 다른 버전의 결과와 비교할 때 이 문서로 돌아오면 된다. 현재 5.1.0 공식 문서는 지원 종료 버전으로 표시되므로, 출처의 버전 번호를 확인하며 읽는다. 이 브랜치의 실행 기준은 계속 5.1.0이다. [공식 5.1.0 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)

## 1. 4.x를 하나의 버전으로 묶으면 안 되는 이유

4.2와 4.5 사이에도 Extension 이름, 메뉴, 물리 기능이 달라졌다. 따라서 “4.x 코드”라고만 적힌 예제는 작성 당시 버전을 먼저 확인한다.

| 버전 | 해당 버전에서 확인할 변화 | 이 튜토리얼에서 확인할 것 |
| --- | --- | --- |
| 4.2.0 | Kit 106.1.0, RTX tiled rendering, 물리·렌더링 사이 한 프레임 지연 개선 | 이미지와 로봇 자세를 비교할 때 어느 시점의 값인지 함께 기록한다. |
| 4.5.0 | Kit 106.5.0, `isaacsim.*` 이름 체계 도입, URDF/MJCF 가져오기를 `File > Import`로 통합 | 오래된 메뉴 경로와 Python import를 함께 바꾼다. |
| 5.0.0 | Kit 107.3.1, ROS 2 Jazzy 지원, 새로운 로봇·센서 구성 방식 | 4.5 환경을 그대로 복사하기 전에 런타임과 센서 API를 점검한다. |
| 5.1.0 | Kit 107.3.3, 센서·ROS 2 수정과 실행 환경 개선 | 아래의 5.0 대비 변경 사항과 알려진 문제를 확인한다. |

4.0·4.1까지 거슬러 올라가는 코드는 [이전 릴리스 기록](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/archived_release_notes.html)에서 해당 소버전을 따로 확인한다. 위 표의 4.2 변경 사항을 모든 4.x 버전의 기본 동작으로 해석하면 안 된다. 4.5, 5.0, 5.1 항목은 각각 [4.5 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/release_notes.html), [5.0 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/overview/release_notes.html), [5.1 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)를 기준으로 한다.

### 4.5에서 이미 달라진 것

4.5는 이름만 바뀐 버전이 아니다. CPU에서 SDF triangle-mesh collider를 지원하고, mimic joint를 유연한 제약으로 설정할 수 있게 했다. ROS 2 자동 namespace 생성, 4륜 Ackermann Controller, Nav2 waypoint 예제도 이때 추가되었다. Asset Browser가 베타로 제공되고 로봇 예제가 브라우저 형태로 정리되었다. ROS 2 Foxy 지원은 종료되었다. [4.5 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/release_notes.html)

따라서 이전에 “4.5에서 성공한 URDF”가 있다면 원본 파일뿐 아니라 importer 옵션, 선택한 USD variant, collider 방식까지 보관한다. 파일을 다시 가져오는 것과 당시 생성한 USD를 여는 것은 서로 다른 작업이다. 이 튜토리얼에서는 두 결과를 같은 것으로 가정하지 않는다.

## 2. 5.0에서 도입된 변화

아래 기능을 5.1의 신기능으로 소개하지 않는다. 5.1에서 계속 사용하지만 도입 시점은 5.0이다.

| 분야 | 5.0의 변화 | 학습에 미치는 영향 |
| --- | --- | --- |
| 개발 | Isaac Sim 코드 공개, Core Experimental API 도입 | 기존 Core API와 실험 API의 클래스·배열 규약을 섞지 않는다. |
| 렌더링 | NuRec 지원 | 기본 USD 씬을 먼저 익히고 별도 과정으로 다룬다. |
| 물리 | 관절 마찰·구동 모델 확장, deformable schema 베타 | 이전 관절 설정의 결과를 다시 측정한다. |
| 로봇 | Robot Wizard, 새 Robot Assembler·Gain Tuner, robot schema, 에셋 재배치 | 예전 로봇 경로와 variant를 재확인한다. |
| 센서 | `OmniLidar` 등 `OmniSensor` prim 지원, OpenCV 렌즈 모델, stereo depth | Camera prim에 LiDAR 설정을 넣던 예제를 이관한다. |
| ROS 2 | Jazzy 지원, 내부 라이브러리 자동 로드, Simulation Control | 외부 ROS 노드와 시뮬레이터 환경을 구분한다. |
| 데이터 | MobilityGen, grasp 데이터 생성, 사건·장면 설명 관련 기능 | 개별 센서 검증을 마친 뒤 데이터 생성을 붙인다. |
| 지원 종료 | ROS 1, 기존 Omniverse Streaming Client | ROS 2와 WebRTC 기반 경로를 사용한다. |

변경 사실의 출처는 [5.0 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/overview/release_notes.html)이며, 오른쪽 열은 이 과정의 진행 원칙이다. Apache 2.0 공개 범위와 별도 구성 요소의 라이선스는 [공식 소스 저장소](https://github.com/isaac-sim/IsaacSim)를 확인한다.

## 3. 5.1에서 추가·수정·제거된 것

| 구분 | 5.0 대비 5.1의 변화 |
| --- | --- |
| 실행 환경 | Compatibility Checker를 설치 구성에 통합하고 DGX Spark를 지원한다. |
| 컨테이너 | 여러 아키텍처를 지원하며 기본 사용자가 root가 아니다. |
| 로봇 | Schunk 그리퍼·손, Booster T1을 추가하고 G1 손 variant를 갱신한다. |
| 물리 | articulation 접촉을 마지막에 푸는 기능으로 그리퍼 관통 문제를 개선하고 deformable 상호작용 회귀를 수정한다. |
| 센서 추가 | RTX Object ID, USD 기반 비시각 재질, IMU 장치 측 처리를 지원한다. |
| 센서 수정 | 생성 pose, IMU·contact 방향, LiDAR 반환 timestamp, OpenCV `imageSize`를 수정한다. |
| ROS 2 수정 | `CameraInfo`의 `fy`, 중복·누락 timestamp, 메시지 처리·메모리를 개선한다. |
| ROS 2 확장 | Simulation Interfaces 1.1.0의 world 관련 서비스를 추가한다. |
| 데이터 생성 | Object SDG writer trigger를 수정하고 Actor SDG NavMesh API를 갱신한다. |
| 제거·변경 | 이전 RTX point extraction 노드를 대체하고 기본 CSV 재질 매핑 사용을 중단한다. |
| 기본값 | MotionBVH는 5.0의 기본 ON에서 OFF로 바뀌며 ROS Bridge 라이브러리 설정은 `system_default`이다. |
| 향후 제거 예고 | 폐기 예정 Extension 전체 제거 시점은 다음 주요 버전 6.0으로 안내한다. |

위 항목의 근거는 [5.1 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)이다. 버그 수정은 모든 로봇·GPU 조합의 성공을 보장하지 않는다. 특히 이전 버전의 잘못된 값에 맞추어 보정 코드를 넣었다면, 수정된 결과에 보정이 이중으로 적용되는지 점검한다.

### 설치 경로와 컨테이너 사용자도 확인한다

Omniverse Launcher에서 설치하는 예전 안내는 그대로 따라가지 않는다. NVIDIA는 4.5를 Launcher로 배포하는 마지막 Isaac Sim 버전으로 안내하고, Launcher·Nucleus Workstation·Nucleus Cache의 종료 시점을 2025년 10월 1일로 명시했다. 5.1 설치는 [이 과정의 설치 장](../02-getting-started/02-workstation-installation.md)을 따른다. [4.5 다운로드 안내](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/download.html)

기존 Docker 실행 파일에 `/root` 경로가 고정되어 있다면 현재 사용자의 홈·권한과 volume mount를 다시 확인한다. 컨테이너 안에서 `id`와 `pwd`로 실행 계정을 확인하고, 출력 디렉터리에 작은 파일을 생성할 수 있는지 먼저 시험한다. ROS bag과 이미지 저장이 끝난 뒤에 권한 오류를 발견하지 않도록 하기 위한 절차이다.

## 4. Python과 ROS 2 ABI: 패키지를 복사해서 해결하지 않는다

ABI는 컴파일된 모듈이 런타임과 맞물리는 규약이다. Python 소스 파일의 문법이 맞아도, 다른 Python 버전용 `rclpy` 공유 라이브러리는 그대로 불러올 수 없다.

| 실행 환경 | Python | 확인할 점 |
| --- | --- | --- |
| Isaac Sim 4.5 | 3.10 | 과거 가상환경을 5.1에 재사용하지 않는다. |
| Isaac Sim 5.0 / 5.1 | 3.11 | Isaac Sim 내부에서 불러오는 바이너리 모듈이 맞아야 한다. |
| Ubuntu 24.04의 기본 ROS 2 Jazzy | 3.12 | 외부 노드는 이 환경에서 실행한다. |

버전 근거: [4.5 Python 설치](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/install_python.html), [5.0 Python 설치](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/installation/install_python.html), [5.1 ROS 2 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html).

### 두 터미널의 역할

일반 메시지로 통신하는 경우 DDS가 프로세스 사이의 전송을 담당하므로 양쪽 Python 버전이 같을 필요는 없다. 하지만 Isaac Sim 내부에서 custom 메시지를 import한다면 3.11용 빌드가, 외부 Jazzy 노드에는 3.12용 빌드가 필요하다. [5.1 ROS 2 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

터미널 A는 ROS setup을 source하지 않은 환경에서 연다. 아래 진단 결과의 `PYTHONPATH`에 `/opt/ros/jazzy` 또는 외부 workspace의 Python 3.12 경로가 남아 있다면 [Bridge 설치 장](../04-ros2/01-install-bridge-workspace.md)에 따라 실행 환경부터 정리한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
"$ISAACSIM_PATH/python.sh" - <<'PY'
import os
import sys
import sysconfig

print("Isaac Python:", sys.version.split()[0])
print("확장 모듈 ABI:", sysconfig.get_config_var("SOABI"))
print("ROS_DISTRO:", os.environ.get("ROS_DISTRO", "<미설정>"))
print("PYTHONPATH:", os.environ.get("PYTHONPATH", "<미설정>"))
assert sys.version_info[:2] == (3, 11)
PY
"$ISAACSIM_PATH/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

터미널 B는 외부 ROS 2 노드용이다.

```bash
source /opt/ros/jazzy/setup.bash
python3 - <<'PY'
import sys
import rclpy

print("외부 ROS Python:", sys.version.split()[0])
print("rclpy 위치:", rclpy.__file__)
assert sys.version_info[:2] == (3, 12)
PY
ros2 doctor --report
```

3.12용 `.so` 파일 이름을 3.11처럼 바꾸거나, 시스템 `python3` 링크를 바꾸는 방식으로 맞추지 않는다. 학습용 기본 경로는 각각의 런타임을 유지하는 것이다.

## 5. Extension·import·OmniGraph 이름을 함께 바꾼다

이름 변경의 출발점은 4.5이다. 기능을 분리해 필요한 Extension만 조합할 수 있도록 한 변화이므로 `omni.isaac` 문자열 전체를 `isaacsim`으로 치환하는 방식은 맞지 않는다. [Extension 이름 변경 안내](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/extensions_renaming.html)

| 4.2 예제에서 보이는 이름 | 5.1에서 사용하는 이름 |
| --- | --- |
| `omni.isaac.core`의 `World` | `isaacsim.core.api.World` |
| `omni.isaac.core.utils` | `isaacsim.core.utils` |
| `omni.isaac.sensor`의 `Camera` | `isaacsim.sensors.camera.Camera` |
| `omni.isaac.sensor`의 `LidarRtx` | `isaacsim.sensors.rtx.LidarRtx` |
| `omni.isaac.ros2_bridge` | `isaacsim.ros2.bridge` |
| `omni.isaac.core_nodes.IsaacReadSimulationTime` | `isaacsim.core.nodes.IsaacReadSimulationTime` |

아래 “이전” 블록은 비교용이며 5.1 실행 예제가 아니다.

```python
# 이전: 4.2 계열 코드의 import 부분
from omni.isaac.core import World
from omni.isaac.sensor import Camera, LidarRtx
from omni.isaac.core.utils.extensions import enable_extension

enable_extension("omni.isaac.ros2_bridge")
```

```python
# 변경: 5.1 Script Editor에서 실행하는 import 확인
from isaacsim.core.api import World
from isaacsim.sensors.camera import Camera
from isaacsim.sensors.rtx import LidarRtx
from isaacsim.core.utils.extensions import enable_extension

enable_extension("isaacsim.ros2.bridge")
print(World.__module__, Camera.__module__, LidarRtx.__module__)
```

Standalone 파일에서는 위 import보다 먼저 `from isaacsim import SimulationApp`와 `SimulationApp(...)` 생성이 있어야 한다. GUI의 Script Editor는 이미 앱이 실행 중이므로 다시 생성하지 않는다. 실행 문맥의 차이는 [Python 실행 방식](../06-developer/01-python-workflows.md)에서 이어서 다룬다.

Extension을 직접 작성했다면 `extension.toml`의 `[dependencies]`, Python import, OmniGraph 노드 type, 설정 경로까지 확인한다. USD reference 안의 노드는 최상위 씬만 저장해도 원본 reference 파일이 재귀적으로 바뀌지는 않는다. [Extension 이름 변경 안내](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/extensions_renaming.html)

```bash
# 자신의 프로젝트 루트에서 실행하는 검색이다. 자동 치환하지 않는다.
rg -n 'omni\.isaac\.(core|sensor|ros2_bridge|core_nodes)' \
  --glob '*.py' --glob '*.toml' --glob '*.kit' --glob '*.usda' .
```

구 문서의 제거 예정 시점과 현재 릴리스의 안내가 다를 수 있다. 특히 4.5 이름 변경 문서의 “5.0 제거 예정” 문장을 근거로 5.1에 모든 호환 Extension이 없다고 단정하지 않는다. 새 코드는 위 이름으로 작성하고 실제 포함 여부는 설치된 Extension 목록과 현재 릴리스 기록으로 확인한다.

## 6. RTX LiDAR 이관: prim, annotator, 시간의 세 가지 변화

### 6.1 Camera prim + JSON에서 OmniLidar로

4.5까지의 예제는 Camera prim에 LiDAR용 설정을 넣는 방식을 사용한다. 5.0부터 이 방식은 폐기 예정이며 `OmniLidar` prim과 USD 속성을 사용하는 경로가 기본이다. 예전 JSON 설정을 보유했다면 제공되는 변환 도구의 인자부터 확인한다. [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)

```bash
"$ISAACSIM_PATH/python.sh" \
  "$ISAACSIM_PATH/tools/isaacsim.sensors.rtx/convert_lidar_json_to_usda.py" \
  --help
```

출력 파일을 만든 뒤에는 scan rate, emitter 수, 채널별 elevation, 최소·최대 거리를 원본과 대조한다. 변환이 끝났다는 사실만으로 실제 센서와 동일한 측정 모델이라고 판단하지 않는다.

### 6.2 노드 제거와 annotator 이름을 구분한다

5.1에서는 `IsaacExtractRTXSensorPointCloud` **노드**가 제거되었지만, `IsaacExtractRTXSensorPointCloudNoAccumulator` **annotator**는 제공한다. 이 annotator가 내부에서 `IsaacCreateRTXLidarScanBuffer` 노드의 프레임별 출력 기능을 사용한다. [RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)

| 원하는 출력 | 5.1에서 선택할 것 |
| --- | --- |
| 프레임별 3D 포인트 클라우드 | `IsaacExtractRTXSensorPointCloudNoAccumulator` |
| 스캔 누적과 timestamp 등 부가 정보 | `IsaacCreateRTXLidarScanBuffer` |
| ScanBuffer로 프레임별 출력과 부가 정보 받기 | `enablePerFrameOutput=True` |
| 수평 2D LiDAR의 거리 스캔 | `IsaacComputeRTXLidarFlatScan` |

노드의 입력 이름은 [ScanBuffer API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.rtx/docs/ogn/OgnIsaacCreateRTXLidarScanBuffer.html)를 기준으로 한다. 3D LiDAR에 FlatScan을 붙이는 것으로 올바른 2D 스캔이 생기는 것은 아니다.

아래는 이미 만들고 초기화한 `lidar` 객체에 붙이는 코드 조각이다. 객체 생성과 실행 루프 전체는 센서 실습에서 구성한다. 기존 `add_*_data_to_frame()` 호출을 그대로 이어 붙이지 않는다.

```python
# 변경 전: 구버전 예제의 데이터 요청 방식, 비교용
lidar.add_point_cloud_data_to_frame()
lidar.add_range_data_to_frame()
```

```python
# 변경 후: Isaac Sim 5.1, 초기화한 LidarRtx 객체에 한 번 호출
lidar.attach_annotator(
    "IsaacCreateRTXLidarScanBuffer",
    enablePerFrameOutput=True,
    outputTimestamp=True,
    outputDistance=True,
)

# Play 후 앱을 여러 프레임 갱신한 다음 구조부터 확인한다.
sample = lidar.get_current_frame()
print("frame 항목:", sorted(sample))
print("연결한 annotator:", sorted(lidar.get_annotators()))
```

`attach_annotator()`의 옵션과 `get_current_frame()` 반환 구조는 [LidarRtx API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.rtx/docs/index.html)를 기준으로 한다. 예전 코드의 `frame["point_cloud"]` 같은 키가 계속 존재한다고 가정하지 말고 출력 구조를 먼저 확인한다. 반환된 센서 배열을 다음 프레임 이후에도 보관하려면 복사 여부와 메모리 위치를 확인한다.

### 6.3 점이 끌려 보일 때, 노이즈와 시간 누적을 구분한다

누적 스캔에는 여러 프레임의 측정이 들어간다. 센서나 물체가 움직이는 동안 쌓인 점은 현재 형상 뒤에 남은 것처럼 보일 수 있다. 또한 RTX 센서의 내부 timestamp와 ROS `/clock`을 같은 시간축으로 가정해서는 안 된다. RTX annotator 수집은 Play 상태와 앱 update가 필요하며 `rep.orchestrator.step()`만으로 대체하지 않는다. [RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)

이 과정에서는 먼저 정지한 센서와 정지한 벽으로 검증한 뒤, 센서 이동과 물체 이동을 하나씩 추가한다. 각 실험에 프레임별 출력인지 누적 출력인지 기록한다. 같은 움직임을 주었는데 버전별 결과가 달라졌다면 MotionBVH 기본값도 비교 항목에 넣는다. 설정을 바꿀 때에는 이전 측정과 결과 파일을 따로 보관한다.

## 7. ROS 2 Simulation Control과 CameraInfo 이관

### 서비스 이름은 실행 중인 시스템에서 확인한다

5.1의 world 조회·불러오기·내리기 서비스는 Simulation Interfaces 1.1.0 기준이다. 이 기능을 쓰는 외부 workspace도 해당 인터페이스 정의를 갖추어야 한다. 기본 ROS Bridge만 켰다고 모든 Simulation Control 서비스가 나타나는 것은 아니다. [ROS 2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)

시뮬레이터 실행 터미널에서 시작한다.

```bash
"$ISAACSIM_PATH/isaac-sim.sh" \
  --enable isaacsim.ros2.bridge \
  --/isaac/startup/ros_sim_control_extension=true
```

외부 Jazzy 터미널에서 **조회만** 먼저 수행한다.

```bash
source /opt/ros/jazzy/setup.bash
# 필요하면 simulation_interfaces 1.1.0을 빌드한 외부 workspace도 source한다.
ros2 interface show simulation_interfaces/srv/GetCurrentWorld
ros2 service list -t
ros2 action list -t
ros2 service call /get_current_world \
  simulation_interfaces/srv/GetCurrentWorld '{}'
```

서비스가 보이지 않으면 Extension 로드 로그, ROS domain, 인터페이스 버전을 차례로 확인한다. 이름만 예전 스크립트에서 복사해 반복 호출하지 않는다. `LoadWorld`·`UnloadWorld`를 시험할 때에는 먼저 씬을 저장하고 정지 또는 일시정지한 상태에서 수행한다. 이 호출은 현재 씬과 배치한 entity를 바꾸므로 조회 단계와 구분한다. [ROS 2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)

### CameraInfo의 숫자를 실제 카메라 설정과 맞춘다

과거 출력에 맞추어 `fy = fx`를 강제로 넣은 외부 코드는 제거 여부를 검토한다. `fx`와 `fy`가 다르다는 사실만으로 오류라고 판단해서는 안 된다. 해상도, 렌즈 설정, 영상과 CameraInfo의 `frame_id` 및 timestamp를 함께 비교한다.

```bash
# /camera/camera_info는 현재 실습의 실제 topic 이름으로 바꾼다.
ros2 topic info /camera/camera_info -v
ros2 topic echo /camera/camera_info --once
```

같은 물체를 영상의 중앙과 가장자리로 옮겨 보고, 알려진 3D 좌표를 CameraInfo로 투영한 위치가 영상과 맞는지 비교한다. 이 점검은 단순히 토픽이 발행되는지만 확인하는 것보다 렌즈 모델·좌표계 오류를 찾는 데 유용하다. 카메라 설정과 메시지 연결은 [ROS 2 Cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html)에서 확인한다.

## 8. 5.1에서도 남아 있는 문제와 재현 조건

아래는 [5.1 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)에 명시된 항목 중 이 과정과 관련된 것이다. 오른쪽 열의 비교 실험은 원인 구분을 위한 학습용 절차이다.

| 증상·조건 | 공식 문서에 명시된 문제 | 이 과정의 확인 방법 |
| --- | --- | --- |
| 다중 GPU에서 render product 생성 | 주 viewport가 검게 변해도 센서 출력은 유지될 수 있다. | 단일 GPU로 같은 씬을 실행하고 저장 영상도 확인한다. |
| 해상도가 VRAM 한계를 넘음 | 메모리 부족 뒤 해상도를 줄이는 과정에서도 충돌할 수 있다. | 낮은 해상도로 새로 실행하고 센서를 하나씩 추가한다. |
| 낮은 해상도의 SDG 영상 | DLSS Performance에서 경계·투명도 오류가 발생할 수 있다. | Quality와 원본 영상을 비교한다. |
| 깊이 영상의 불필요한 노이즈 | anti-aliasing의 영향을 받을 수 있다. | Algorithm을 None으로 바꾸어 같은 장면을 비교한다. |
| Replicator 수집 중 프레임 누락 | timeline 정지 시 throttling의 async rendering 전환이 원인일 수 있다. | 아래 플래그를 적용하고 예상·실제 파일 수를 비교한다. |
| World와 OmniGraph 함께 사용 | graph를 World 초기화 전에 구성해야 한다. | 생성 순서를 확인한다. |
| 일부 장시간 ROS 샘플 | Carter navigation·Franka joint-state 예제에 메모리 누수가 보고되어 있다. | 실행 시간에 따른 메모리 증가를 기록한다. |
| Blackwell의 Franka 서랍 예제 | 기본 설정에서 실패하는 문제가 보고되어 있다. | 해당 예제의 물리 주기 지침을 별도로 적용한다. |

```python
# Script Editor: SDG 영상 비교를 위한 DLSS Quality 설정
import carb.settings

carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
```

```bash
# Replicator 프레임 누락 재현 시에만 비교 적용한다.
"$ISAACSIM_PATH/isaac-sim.sh" \
  --/exts/isaacsim.core.throttling/enable_async=false
```

모든 문제에 위 설정을 한꺼번에 적용하면 어떤 변경이 효과가 있었는지 알기 어렵다. 문제가 없는 기준 씬을 저장하고 한 항목씩 바꾼다. RGB 품질을 위한 설정과 수치 깊이 검증에 필요한 설정도 따로 기록한다.

## 9. 로봇과 센서의 버전 이관을 승인하기 전

다음은 이 튜토리얼의 검증 절차이다. 특정 하드웨어에서 직접 실행하지 않은 결과를 “검증 완료”로 기록하지 않는다.

1. **환경을 기록한다.** Ubuntu, Isaac Sim, Python, GPU, 드라이버, 활성 Extension을 남긴다. 요구사항 충족 여부와 씬별 성능 검증은 별개이다.
2. **로봇만 실행한다.** 센서·ROS·제어기를 제거한 복사 씬에서 바닥 접촉, 관절 축, 초기 관절 위치, mass·inertia, self-collision을 확인한다.
3. **짧은 명령 하나를 준다.** 정지 → 작은 관절 이동 → 정지 순서로 시험한다. 기준 자세를 유지하는지, 관절 제한을 넘는지, 불필요한 진동이 생기는지 기록한다.
4. **센서를 하나씩 붙인다.** RGB, depth, IMU, LiDAR를 순서대로 추가한다. GUI 표시와 실제 출력 데이터를 각각 확인한다.
5. **재시작을 시험한다.** Play/Pause/Stop/Reset 후 토픽, timestamp, 센서 pose, 구독 객체가 정상적으로 재개되는지 확인한다.
6. **고정된 조건으로 비교한다.** 같은 USD, 시작 자세, 명령, 기간에서 프레임 수·포인트 수·궤적·메모리를 비교한다. 렌더링 출력이 버전 사이에서 픽셀 단위로 같아야 한다는 기준은 두지 않는다.
7. **최종 프로젝트를 실행한다.** 개별 센서를 통과한 뒤 모든 센서를 결합하고, 로그와 결과 파일을 보관한다.

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used \
  --format=csv
lsb_release -ds
"$ISAACSIM_PATH/python.sh" -c 'import sys; print(sys.version)'
```

아래 기록 양식은 값의 누락을 줄이기 위한 예시이다. 실행 전에는 결과 칸을 비워 두고, 실행 후 관찰한 수치를 적는다.

| 기록 항목 | 기록 예시·방법 |
| --- | --- |
| 버전 | Isaac Sim 5.1.0 / Python 3.11 / Jazzy |
| 입력 | USD 경로, 초기 자세, seed, 명령 파일 |
| 시간 | physics/render 주기, 총 시뮬레이션 시간 |
| 센서 | 해상도·주기, LiDAR profile·누적 방식 |
| 렌더링 | GPU 선택, DLSS·AA, MotionBVH |
| 관찰 결과 | 자세 변화, 접촉·진동, 영상, 포인트 수, 누락 프레임 |
| 증거 | 실행 로그, 영상·배열, ROS bag 경로 |
| 결론 | 통과 / 실패 / 실행하지 못함과 이유 |

5.1 x86_64 요구사항에는 Ubuntu 24.04와 RT Core가 있는 GPU가 포함되며, 공식 표의 드라이버는 테스트된 버전이다. aarch64 지원은 DGX Spark 조건을 별도로 확인해야 한다. 본 과정의 x86_64 명령을 모든 ARM 장치에 적용하지 않는다. [5.1 요구사항](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)

## 출처

- [4.2 및 이전 릴리스 기록](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/archived_release_notes.html)
- [4.5 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/release_notes.html)
- [4.5 Extension 이름 변경](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/overview/extensions_renaming.html)
- [5.0 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/overview/release_notes.html)
- [5.1 릴리스 노트](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)
- [5.1 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
- [5.1 ROS 2 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [5.1 RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [5.1 RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)
- [5.1 ROS 2 Simulation Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_simulation_control.html)
