# Isaac Sim 5.1.0에서 6.0.1로 옮기기

이 문서는 기존 5.1.0 예제와 USD 자산을 6.0.1로 옮길 때 바꿔야 하는 부분을 설명한다. 설치와 GUI 첫 사용은 본 튜토리얼 순서를 따른다. 여기서는 **어떤 부분이 달라졌는지, 왜 수정하는지, 수정 뒤 무엇을 검사하는지**에 집중한다. 문서는 2026-09-09에 확인한 NVIDIA의 버전 고정 문서를 기준으로 작성했다.

> 검증 범위: 아래 API 이름과 연결 관계는 공식 6.0.1 문서와 대조했다. 이 문서를 작성한 환경에서는 Isaac Sim 6.0.1과 RTX GPU로 실행하지 못했다. 따라서 실제 렌더링, 관절 안정성, 센서 시간 동기화가 검증되었다고 주장하지 않는다. 각 절의 실행 검사는 해당 조합을 설치한 장비에서 수행하고 결과를 남겨야 한다.

## 1. 누적 변경과 6.0.1 패치를 구분한다

| 기준 버전 | Kit SDK | 읽는 목적 |
|---|---|---|
| 5.1.0 | 107.3.3 | 이전 환경의 기준점을 확인한다 |
| 6.0.0 GA | 110.1.1 | 6.0 계열에 들어오면서 바뀐 구조와 API를 확인한다 |
| 6.0.1 GA | 110.1.2 | 6.0.0 이후 수정된 항목을 확인한다 |

6.0.1의 패치 목록만 읽으면 5.1.0에서 건너오는 데 필요한 변경을 놓친다. 반대로 6.0.0 Early Developer Release에 나온 임시 API 이름을 최종 이름으로 사용해서도 안 된다. 예를 들어 초기 릴리스 기록의 `isaacsim.sensors.experimental.camera`와 달리 최종 카메라 이관 문서는 `isaacsim.sensors.experimental.rtx`를 지정한다. 버전별 기록과 최종 이관 문서를 함께 확인한다. [5.1.0 릴리스 기록](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html), [6.0.1 릴리스 기록](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/release_notes.html), [카메라 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_camera_to_experimental_rtx.html)

6.0.1 패치에서 이 튜토리얼과 직접 연결되는 항목을 추리면 다음과 같다. 아래 검사는 패치가 적용되었는지 숫자로 판단하기 위한 **본 튜토리얼의 회귀검사 제안**이다.

| 6.0.1 수정 항목 | 튜토리얼에서 확인할 결과 |
|---|---|
| 자산 변환·가져오기·내보내기 도구 업데이트 | 다시 가져온 자산의 링크·관절·material을 기존 결과와 비교한다 |
| 차동구동 GUI shortcut의 좌우 순서와 관절 인덱스 0 처리 수정 | 직진 명령에서 두 바퀴가 같은 방향으로 회전하는지 확인한다 |
| ROS 동적 메시지 배열과 IPC 버퍼 해제 관련 누수 수정 | 동일 메시지를 반복 발행하면서 프로세스 메모리 증가를 기록한다 |
| RTX point cloud의 Cartesian 데이터 전달 수정 | 정면 평면의 좌표와 거리 분포를 확인한다 |
| `SimulationApp`의 `sync_loads` 설정 경로 수정 | 자산 로딩 완료 뒤 검사와 제어를 시작하는지 확인한다 |
| NuRec utilities 및 SPG teleoperation 경로 보강 | 해당 고급 실습을 선택하면 render 사전 조건과 저장 프레임을 별도로 확인한다 |

이 표는 전체 패치 목록의 번역이 아니다. 나머지 extension 버전과 수정 내역은 [6.0.1 공식 릴리스 기록](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/release_notes.html)에서 확인한다. 특정 수정이 들어갔다는 사실만으로 모든 장면의 블랙아웃이나 물리 불안정이 해결된다고 판단하지 않는다.

## 2. 이관 전에 기존 실습의 기준을 남긴다

기존 결과를 기록하지 않으면 “잘 보인다”와 “동일하게 동작한다”를 구분하기 어렵다. 아래 표는 새 작업 디렉터리에서 준비할 자료이다. 이 저장소 작업을 위해 다른 브랜치를 수정하거나 실행할 필요는 없다. 이미 보유한 결과만 비교 자료로 사용한다.

| 남길 항목 | 예시 | 비교 이유 |
|---|---|---|
| 자산 식별 정보 | USD 경로, 해시, variant 선택 | 이름이 같은 다른 모델을 비교하는 일을 막는다 |
| 초기 상태 | 링크 pose, joint 이름과 순서 | 제어 배열의 잘못된 인덱스를 찾아낸다 |
| 카메라 | 해상도, K 행렬, pose, 샘플 이미지 | 방향·단위·광학 설정의 변화를 구분한다 |
| LiDAR | profile, scan rate, 점 수, 거리 범위 | 부분 scan과 완전한 scan을 구분한다 |
| 실행 시간 | physics dt, sensor rate, ROS timestamp | 속도와 시간 기준의 변화를 구분한다 |
| 검증 결과 | 시작 10초 정지, 저속 이동, 재시작 | 초기 침투·폭주·reset 오류를 찾는다 |

기존 코드를 복사한 **별도 이관 작업 폴더** 안에서 다음 명령으로 후보를 찾는다. 결과를 보고 파일별로 수정하며, 문자열 전체 치환은 사용하지 않는다.

```bash
# 현재 폴더에 있는 코드와 설정만 읽는다.
rg -n 'isaacsim\.sensors\.(camera|rtx|physics)|IsaacSensorCreate|get_current_frame' .
rg -n 'isaacsim\.ros2\.bridge|ROS2PublishTransformTree|ROS2PublishJointState' .
rg -n 'simulation_length|sdg_scheduler|surface_gripper\._surface_gripper' .
```

모듈 이름, 객체 생성, 데이터 반환형이 함께 바뀌므로 import만 바꾸면 충분하지 않다. 이관 순서는 실행 환경 → 자산 → 단일 센서 → ROS 연결 → 제어 → 데이터 생성으로 잡는다. 한 번에 모두 바꾸지 않으면 실패한 지점을 빠르게 좁힐 수 있다.

## 3. Python 환경과 ROS extension을 정리한다

6.0 계열의 Python 3.12 환경에서는 Ubuntu 24.04의 시스템 Jazzy를 source한 터미널에서 Isaac Sim을 실행하는 흐름을 사용한다. 내장 Jazzy 라이브러리는 ROS가 설치되지 않은 구성 등을 위한 별도 선택지이다. 본 튜토리얼의 기본 환경에서는 시스템 Jazzy의 환경 설정을 먼저 불러온다. [ROS 설치 및 라이브러리 선택](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html)

```bash
# 새 터미널에서 실행한다. ISAAC_SIM_ROOT는 설치 폴더의 절대 경로로 바꾼다.
export ISAAC_SIM_ROOT="$HOME/isaacsim-6.0.1"
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=31
"$ISAAC_SIM_ROOT/isaac-sim.sh"
```

예전 터미널에서 5.1 라이브러리 경로를 계속 이어 붙이지 않는다. 특히 `LD_LIBRARY_PATH`를 복사하기 전에 어떤 라이브러리를 선택한 구성인지 확인한다. 내장 모드를 별도로 선택할 경우 새 경로는 `exts/isaacsim.ros2.core/jazzy/lib`이며, 시스템 source 방식과 절차를 혼합하지 않는다. [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html)

| 6.0의 extension | 맡은 역할 |
|---|---|
| `isaacsim.ros2.core` | ROS 라이브러리와 메시지 처리 기반 |
| `isaacsim.ros2.nodes` | ROS OmniGraph 노드 |
| `isaacsim.ros2.ui` | GUI 도구 |
| `isaacsim.ros2.examples` | 예제와 데모 |

기존의 큰 bridge extension을 역할별로 나누었다. GUI를 쓰지 않는 실행에서도 메시지 기반과 필요한 노드를 선택할 수 있는 구조이다. 옛 설정의 `bridge`를 모든 줄에서 `core`로 치환하면 노드와 GUI 의존성이 빠질 수 있다. [ROS extension 구조 변경](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/release_notes.html)

예를 들어 ROS Action Graph를 제공하는 사용자 extension의 의존성은 다음처럼 의도를 드러낸다. GUI 도구를 실제로 사용하는 extension이라면 `isaacsim.ros2.ui`도 추가한다.

```toml
# config/extension.toml의 관련 부분만 나타낸다.
[dependencies]
"isaacsim.ros2.core" = {}
"isaacsim.ros2.nodes" = {}
```

검사할 때는 앱이 실행된 것만 확인하지 않는다. Extension 창에서 필요한 모듈이 활성화되었는지 확인한 뒤, simulation을 Play하고 `ros2 topic list`로 예상 topic이 보이는지 확인한다. 토픽이 보여도 데이터가 없으면 발행 노드의 실행 연결과 QoS를 확인한다. [ROS 실행 구조](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/ros2_reference_architecture.html)

## 4. 카메라: USD 구성과 프레임 수집을 나눈다

새 API는 카메라 prim을 구성하는 `RtxCamera`와 이미지를 가져오는 `CameraSensor`를 구분한다. 위치는 `(1, 3)`, quaternion은 `(1, 4)` 형태로 전달한다. 이름이 복수형이라고 한 객체에서 여러 카메라를 임의로 생성하는 뜻은 아니며 이 경우 `N=1`이다. `tick_rate`는 Hz이고, 요청한 annotator별로 `get_data()`를 호출한다. [카메라 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_camera_to_experimental_rtx.html)

다음은 변경 지점을 비교하는 **부분 코드**이다. 이전 코드는 5.1 API를 알아보기 위한 자료로만 읽는다. standalone에서는 `SimulationApp`을 먼저 생성하고, GUI Script Editor에서는 이미 실행 중인 앱 안에 작성한다. 두 방식을 같은 파일에 중복 적용하지 않는다.

```python
# 이전 방식: 5.1 API 비교용이다.
from isaacsim.sensors.camera import Camera

old_camera = Camera(
    prim_path="/World/InspectionCamera",
    frequency=20,
    resolution=(800, 600),
    translation=[0.0, 0.0, 2.0],
)
old_camera.initialize()
```

```python
# 새 방식: 실행 중인 6.0.1 앱에서 구성한다.
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera

camera_prim = RtxCamera(
    "/World/InspectionCamera",
    translations=[[0.0, 0.0, 2.0]],
    orientations=[[1.0, 0.0, 0.0, 0.0]],
    tick_rate=20.0,
)
camera_reader = CameraSensor(
    camera_prim,
    resolution=(600, 800),  # 새 API: (height, width)
    annotators=["rgb", "distance_to_image_plane"],
)
# Play하고 렌더링이 진행된 뒤에 읽는다.
pixels, rgb_metadata = camera_reader.get_data("rgb")
depth, depth_metadata = camera_reader.get_data("distance_to_image_plane")
```

같은 가로 800×세로 600 영상을 유지하려면 기존 `(width, height)`를 새 `CameraSensor`의 `(height, width)` 순서로 바꾼다. `rep.create.render_product()`는 여전히 `(width, height)`를 사용하므로 두 함수의 인수를 혼동하지 않는다.

이 예제의 identity quaternion은 카메라의 기본 광축을 유지한다. 임의의 로봇 정면을 바라보게 하는 회전값은 아니다. 카메라 앞에 표적과 조명을 둔 센서 실습 장면에서 pose를 맞춘 뒤 데이터를 읽는다. 비어 있는 초기 배열을 검은 이미지로 저장해서는 안 된다.

본 튜토리얼의 비교 검사는 다음 순서로 진행한다.

1. 동일한 크기의 표적을 두고 해상도, optical pose, clipping 범위를 기록한다.
2. 처음 유효한 프레임이 나올 때까지 제한 시간 안에서 app update를 진행한다.
3. RGB 전체가 같은 값인지와 표적이 차지한 영역을 확인한다. 검정색 물체와 초기화 실패를 구분한다.
4. depth의 무한대·NaN을 분리하고, 표적 영역의 유효 거리만 비교한다. 배경의 invalid depth를 임의로 정상 거리로 바꾸지 않는다.
5. reset 후에도 프레임과 timestamp가 다시 증가하는지 확인한다.

## 5. RTX LiDAR: 클래스 이름과 scan 주기를 함께 바꾼다

`LidarRtx`에서 `Lidar`와 `LidarSensor` 조합으로 옮긴다. 생성 명령에 넘기던 `parent`와 상대 path를 합쳐 전체 prim path를 지정하고, local transform은 `translations`로 전달한다. 시각화는 writer로 연결하며, 원시 Generic Model Output은 전용 parser로 해석한다. [RTX 센서 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_rtx_to_experimental_rtx.html)

```python
# 이전 방식: 비교용이다.
from isaacsim.sensors.rtx import LidarRtx

old_lidar = LidarRtx(
    prim_path="/World/TestLidar",
    config_file_name="Example_Rotary",
)
old_frame = old_lidar.get_current_frame()
```

```python
# 새 방식: 지면 위에 있는 표적 장면에서 생성한다.
from isaacsim.sensors.experimental.rtx import (
    Lidar,
    LidarSensor,
    parse_generic_model_output_data,
)

scan_device = Lidar.create(
    "/World/TestLidar",
    config="Example_Rotary",
    translations=[[0.0, 0.0, 1.2]],
    tick_rate=10.0,
)
scan_reader = LidarSensor(scan_device, annotators=["generic-model-output"])
scan_reader.attach_writer("draw-point-cloud")
# Play하고 센서 출력이 준비된 뒤 실행한다.
scan_buffer, scan_metadata = scan_reader.get_data("generic-model-output")
scan_record = parse_generic_model_output_data(scan_buffer)
```

**`tick_rate`를 임의로 30 Hz로 높이지 않는다.** `OmniLidar`의 `omni:sensor:tickRate`는 profile의 `omni:sensor:Core:scanRateBaseHz`와 일치해야 한다. `Example_Rotary`는 10 Hz이다. 두 값이 다르면 완전한 scan을 기대한 코드가 부분 scan을 받을 수 있으며, 오류 로그가 없을 수도 있다. [Multi-Tick Rendering](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html)

이미 만들어진 센서는 Play 전에 USD 값을 읽어 비교한다. 아래는 센서 경로가 맞는지까지 확인하는 읽기 전용 검사이다.

```python
import math
import omni.usd

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/TestLidar")
assert prim.IsValid(), "LiDAR prim 경로를 확인한다."
tick_hz = prim.GetAttribute("omni:sensor:tickRate").Get()
scan_hz = prim.GetAttribute("omni:sensor:Core:scanRateBaseHz").Get()
assert tick_hz is not None and scan_hz is not None
assert tick_hz > 0 and math.isclose(tick_hz, scan_hz, rel_tol=1e-6), (
    f"센서 tick={tick_hz}, profile scan={scan_hz}가 일치해야 한다."
)
```

본 튜토리얼에서는 정지 센서 앞에 벽을 하나 두고 먼저 거리와 scan 범위를 확인한다. 이후 이동을 추가한다. 점 수가 줄었을 때 시각화 점 크기만 키우면 누락 원인을 숨기게 된다. 회전 완료 여부, 누적 옵션, tick/scan 일치, render 실행 순서부터 확인한다.

Radar를 추가할 때에는 별도의 실습 환경을 구성한다. 새 클래스는 `Radar`/`RadarSensor`이며 Motion BVH가 필요하다. 기존 Ultrasonic 계열은 `Acoustic`/`AcousticSensor` 이름으로 옮겨졌으므로 LiDAR 이름만 바꿔 재사용하지 않는다. [RTX 센서 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_rtx_to_experimental_rtx.html)

## 6. IMU와 물리 센서: 생성 객체와 측정값을 구분한다

물리 센서는 `isaacsim.sensors.experimental.physics`를 사용한다. `IMU.create()`가 prim을 구성하고 `IMUSensor`가 측정값을 읽는다. 기존 command 기반 생성과 별도 Backend reader 대신 이 조합을 사용한다. `get_current_frame()` 대신 `get_data()`를 호출한다. [물리 센서 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_physics_to_experimental_physics.html)

```python
# 이전 패턴: command로 부모 아래에 IMU를 만들던 코드이다.
import omni.kit.commands

old_result = omni.kit.commands.execute(
    "IsaacSensorCreateImuSensor",
    parent="/World/Robot/base_link",
    path="/imu",
)
```

```python
# 새 패턴: base_link가 이미 존재하는 rigid body여야 한다.
from isaacsim.sensors.experimental.physics import IMU, IMUSensor

imu_config = IMU.create(
    "/World/Robot/base_link/imu",
    translations=[[0.03, 0.0, 0.04]],
    orientations=[[1.0, 0.0, 0.0, 0.0]],
)
imu_reader = IMUSensor(imu_config)
# 물리 step이 진행된 뒤 읽는다.
imu_sample = imu_reader.get_data(read_gravity=True)
```

`positions`는 world 기준, `translations`는 부모 기준이다. 둘을 동시에 전달하면 안 된다. sensor prim만 만들었다고 차체가 rigid body가 되는 것도 아니다. 물리 부모를 먼저 완성한다. [물리 센서 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_physics_to_experimental_physics.html)

본 튜토리얼에서는 정지한 차체부터 검사한다. 중력 포함 여부와 센서 축 정의를 기록한 뒤 각속도가 거의 0인지 확인한다. 가속도 성분의 부호는 센서 좌표계에 따라 해석한다. 무조건 `(0, 0, 9.81)`을 정답으로 고정하지 않는다. 다음으로 한 축 회전과 직선 가속을 따로 명령한다. 이 과정에서 생기는 물리적 변화와 임의로 추가한 노이즈를 구분한다.

## 7. Multi-Tick: 화면 프레임과 센서 프레임을 구분한다

6.0부터 센서마다 렌더링 주기를 설정하는 multi-tick이 기본 활성화된다. `tickRate=0`은 정지라는 뜻이 아니라 매 프레임 실행하는 autotrigger이다. 실행 루프, 물리 시간, 렌더러의 센서 스케줄링을 같은 것으로 가정하지 않는다. ROS와 센서 timestamp는 `SimulationManager.get_simulation_time()` 또는 `IsaacReadSimulationTime` 등 물리 기준 시간을 사용한다. [Multi-Tick Rendering](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html)

```python
# 6.0.1 앱 안에서 읽기 전용으로 확인한다.
import omni.timeline
from isaacsim.core.simulation_manager import SimulationManager

physics_seconds = SimulationManager.get_simulation_time()
ui_seconds = omni.timeline.get_timeline_interface().get_current_time()
print({"physics_seconds": physics_seconds, "timeline_seconds": ui_seconds})
# ui_seconds를 이미지나 TF의 timestamp로 대신 사용하지 않는다.
```

본 튜토리얼에서는 먼저 물리·렌더링 설정을 고정하고 센서 하나의 timestamp 간격을 측정한다. 예를 들어 카메라 20 Hz는 시뮬레이션 시간으로 약 0.05초 간격을 기대한다. 처리 속도가 실시간보다 느리면 터미널의 wall-clock 측정과 다를 수 있다. 앱 update 횟수만 세어 센서 누락이라고 판정하지 않는다.

RTX Radar의 tick 제약과 Radar/LiDAR 조합의 알려진 문제는 [multi-tick 문서의 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html#known-issues)를 별도로 확인한다. LiDAR에서 통과한 주기 설정을 모든 RTX 센서에 그대로 적용하지 않는다.

## 8. ROS Action Graph: 상태 계산과 메시지 발행을 나눈다

5.1까지의 TF와 JointState publisher는 직접 prim을 받아 상태를 해석하는 구성을 사용한다. 6.0에서는 전용 source node가 만든 값을 publisher로 전달한다. publisher의 직접 prim 입력은 deprecated이며, 단순히 기존 포트를 연결해 둔 장면은 새 방식으로 정리한다. [ROS OmniGraph 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ros2_omnigraph_migration.html)

| 이전 구성 | 6.0.1 구성 |
|---|---|
| TF publisher에 `targetPrims` 지정 | `Isaac Compute Transform Tree`에 prim을 지정하고 결과를 TF publisher로 전달한다 |
| JointState publisher에 로봇 prim 지정 | `Isaac Read Joint State`에 articulation root를 지정하고 결과를 전달한다 |

### 8.1 TF 연결을 바꾼다

Action Graph에 `Isaac Compute Transform Tree`를 추가한다. `targetPrims`에 로봇 prim을 지정하고 필요한 경우 `parentPrim`을 지정한다. 그다음 아래 동일 이름 포트를 연결한다.

| Compute Transform Tree 출력 | Publish Transform Tree 입력 |
|---|---|
| `execOut` | `execIn` |
| `parentFrames` | `parentFrames` |
| `childFrames` | `childFrames` |
| `translations` | `translations` |
| `orientations` | `orientations` |

### 8.2 JointState 연결을 바꾼다

`isaacsim.sensors.physics.nodes`의 `Isaac Read Joint State`를 추가하고 `prim`에 articulation root를 지정한다. publisher의 ROS Context, topic, namespace 등 통신 설정도 확인한다.

| Read Joint State 출력 | Publish Joint State 입력 |
|---|---|
| `execOut` | `execIn` |
| `jointNames` | `jointNames` |
| `jointPositions` | `jointPositions` |
| `jointVelocities` | `jointVelocities` |
| `jointEfforts` | `jointEfforts` |
| `jointDofTypes` | `jointDofTypes` |
| `stageMetersPerUnit` | `stageMetersPerUnit` |
| `sensorTime` | `sensorTime` |

포트 이름과 연결은 [공식 ROS 이관 표](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ros2_omnigraph_migration.html)를 기준으로 한다. 다음은 본 튜토리얼의 실행 검사 예이다. topic과 frame 이름은 실제 장면에 맞게 바꾼다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=31
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo base_link camera_link
```

`name`과 `position` 배열 길이가 같아야 한다. joint 순서가 바뀌어도 이름 기준으로 제어값을 대응해야 한다. TF는 같은 child frame을 서로 다른 publisher가 중복 발행하는지 확인한다. Play, Stop, Play 후에도 시간과 상태가 다시 갱신되어야 한다. topic이 있다는 사실만으로 graph 이관이 완료되었다고 판단하지 않는다.

## 9. 자산 구조와 물리 엔진 변경을 따로 검증한다

6.0의 Asset Structure 3.0은 geometry, material, instance, 로봇 구조, 공통 물리, 엔진별 설정을 분리한다. 재가져오기로 없어지기 쉬운 센서·ROS 변경은 별도 계층에서 관리한다. `physics`에는 공유 설정을, `physx`와 `mujoco`에는 해당 엔진의 설정을 배치한다. [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/asset_structure.html)

| 바꿀 내용 | 확인할 계층 |
|---|---|
| mesh 형상 | geometry |
| material 연결과 collider 표현 | material·instance |
| 링크 구성과 변환 | base |
| 질량·관절 등 공통 물리 | physics |
| PhysX 전용 solver·mimic 설정 | physx |
| MuJoCo 전용 값 | mujoco |
| 센서와 ROS 기능 추가 | 별도 feature layer |

아래는 본 튜토리얼에서 선택한 관리 방식의 예이다. NVIDIA importer가 언제나 이 파일명을 만든다는 뜻은 아니다. 재가져온 원본과 사용자 센서 설정을 분리한다.

```usda
#usda 1.0
(
    subLayers = [
        @./overrides/sensors.usda@,
        @./imported/robot.usd@
    ]
)
```

앞쪽 sublayer가 더 강한 의견을 제공한다. 파일이 실제로 존재하는지, 합성된 Stage의 경로가 override 경로와 일치하는지 확인한다. 자산을 flatten해서 한 파일로 만들기 전에 원본 연결과 layer별 수정 위치를 이해한다.

Newton은 6.0에 추가된 **experimental 선택지**이며 기본 PhysX와 별개로 검사한다. backend는 simulation 시작 전에 선택하고 한 번에 하나만 활성화한다. 동일한 USD라도 합성 오류, articulation 밖의 joint, 음수 collider scale 등은 Newton에서 별도 문제를 낼 수 있다. [Newton Physics Backend](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/newton_physics.html)

본 튜토리얼의 기본 이관은 PhysX에서 끝낸다. 그 뒤 별도 비교 실행에서 Newton을 선택한다. 실행 파일이 제공되는 설치에서는 다음처럼 시작할 수 있다.

```bash
"$ISAAC_SIM_ROOT/isaac-sim.newton.sh"
```

엔진을 바꾼 직후 관절 gain까지 한꺼번에 조정하지 않는다. 동일 초기 상태의 정지 시험을 먼저 수행한다. 관절 각도·차체 높이·접촉 상태를 기록한 다음 저속 명령을 적용한다. 파일을 읽을 수 있다는 사실과 동역학이 같다는 사실은 별개이므로, 기존 gain이 그대로 적합하다고 가정하지 않는다.

## 10. IRA: 데이터 생성 설정 자체를 이관한다

Replicator Agent의 0.x 설정은 1.x에서 그대로 동작하지 않는다. `scene`과 `global`의 기존 필드, 외부 command 파일, actor 구성 방식이 달라진다. simulation 길이도 프레임 수에서 초 단위로 바뀐다. 다음은 **변경 위치만 설명하는 설정 조각**이며 완전한 IRA pipeline 설정이 아니다. 실제 실습은 설치된 1.x 샘플 설정에서 시작한다. [IRA 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ext_isaacsim_replicator_agent_migration_guide.html)

```yaml
# 이전 0.x 설정의 일부이다.
global:
  seed: 42
  simulation_length: 900
scene:
  asset_path: /absolute/path/warehouse.usd
```

```yaml
# 1.x 설정의 해당 부분이다. 아래 필드는 공식 샘플의 올바른 위치에 넣는다.
seed: 42
simulation_duration: 30.0
environment:
  base_stage_asset_path: /absolute/path/warehouse.usd
```

기존의 900프레임을 그대로 900초로 옮기면 의도보다 긴 실행이 된다. 위 비교는 기존 30 FPS 기준 900프레임을 30초로 환산한다. 캐릭터·로봇은 named groups, 행동은 YAML routines/triggers 또는 지원하는 behavior tree 구성으로 옮긴다. 설정의 extension version도 설치된 샘플을 기준으로 확인한다. [IRA 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ext_isaacsim_replicator_agent_migration_guide.html)

본 튜토리얼에서는 전체 데이터를 생성하기 전에 짧게 실행해 본다. actor 수, actor 이름, writer 대상 센서, 출력 파일 수, simulation duration을 확인한다. random seed만 같다고 이전 버전과 픽셀·물리 궤적이 완전히 같다고 가정하지 않는다. 반복 가능성은 같은 환경에서 별도로 측정한다.

## 11. MobilityGen: 기존 녹화 파일을 변환한다

5.x 녹화 상태는 `state/common/*.npy`에 Python dict를 저장한다. 6.0은 이름이 붙은 NumPy array를 담은 `.npz`를 사용하며 기존 녹화는 변환해야 재생할 수 있다. 공식 도구는 대상 위치를 직접 변환하므로 먼저 복사본을 준비한다. [MobilityGen 녹화 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/mobility_gen_recordings_migration.html)

```bash
# 아래 두 경로를 본인의 녹화 폴더와 새 복사본 경로로 수정한다.
# 새 경로는 아직 존재하지 않는 이름을 사용한다.
set -e
test ! -e ./recordings_migration_copy
cp -a ./recordings_5x ./recordings_migration_copy
"$ISAAC_SIM_ROOT/python.sh" \
  "$ISAAC_SIM_ROOT/standalone_examples/replicator/mobility_gen/migrate_recordings.py" \
  ./recordings_migration_copy --recursive
```

본 튜토리얼에서는 파일 확장자만 확인하지 않는다. 변환 후 reader가 읽은 step 수, 첫 pose, 마지막 pose, 센서 출력 연결을 확인한다. 0 step이면 정상 재생이 아니다. 원본은 검사 완료 전까지 보존한다. 기존 녹화가 신뢰할 수 있는 본인의 데이터인지도 확인한 뒤 처리한다.

## 12. Surface Gripper: compiled binding의 import를 바꾼다

Surface Gripper의 compiled module은 `bindings` 하위로 이동했다. 인터페이스 획득과 상태 조회 방식은 유지되므로 존재하지 않는 예전 submodule 경로만 바꿀 수 있다. [Surface Gripper 이관](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/surface_gripper_bindings_import.html)

```python
# 이전 import: 6.0의 새 코드에서는 사용하지 않는다.
import isaacsim.robot.surface_gripper._surface_gripper as old_grip
```

```python
# 새 import: 실행 중인 앱에서 해당 extension을 활성화한 뒤 사용한다.
from isaacsim.robot.surface_gripper import _surface_gripper as grip_api

grip_interface = grip_api.acquire_surface_gripper_interface()
# /World/PickCell/Grip은 실습에서 이미 구성한 surface gripper 경로이다.
status = grip_interface.get_gripper_status("/World/PickCell/Grip")
print(status)
```

필요한 symbol만 가져오려면 `isaacsim.robot.surface_gripper.bindings._surface_gripper` 경로를 사용한다. import가 성공한 뒤에는 실제 물체의 접촉·흡착·해제를 확인한다. import 수정 자체가 접촉 거리, 힘 한계, 물체 질량의 검증을 대신하지 않는다.

## 13. 알려진 문제를 회피하고 이관 결과를 기록한다

공식 문서는 VRAM 초과 해상도의 OOM, 일부 멀티 GPU 구성의 viewport 블랙아웃, 낮은 해상도에서 DLSS에 따른 SDG 경계 왜곡, material 로딩 대기, Replicator async 토글에 따른 프레임 누락을 안내한다. URDF에서 같은 material 이름을 재사용하면 색상이 합쳐질 수도 있다. [Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)

SDG 실습에서 해당 문제가 나타나면 다음 설정을 개별적으로 검토한다. 모든 오류를 숨기거나 모든 장면에 무조건 적용하는 설정 묶음으로 사용하지 않는다.

```python
# 저해상도 SDG에서 DLSS 경계 왜곡을 점검할 때 적용한다.
import carb.settings
carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)
```

```bash
# 정지/재시작을 포함한 Replicator에서 async 토글 문제가 확인될 때 사용한다.
"$ISAAC_SIM_ROOT/isaac-sim.sh" \
  --/exts/isaacsim.core.throttling/enable_async=false
```

material 변경 직후 수집에는 공식 문서가 안내하는 `rt_subframes`를 확인한다. 검은 화면이면 센서 배열과 viewport를 따로 검사한다. 화면만 검은 현상과 실제 저장 이미지가 검은 현상은 원인이 다를 수 있다. [Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)

다음 표는 본 튜토리얼의 이관 완료 조건이다. 각 항목에 **통과 / 실패 / 미실행**과 증거 파일을 기록한다. 미실행은 통과로 간주하지 않는다.

| 검사 | 통과 기준 | 남길 증거 |
|---|---|---|
| 실행 환경 | 6.0.1 앱과 의도한 Jazzy 라이브러리가 로드된다 | 시작 로그, Python·ROS 환경 |
| 자산 합성 | 필요한 링크와 관절이 있고 누락된 reference가 없다 | Stage 경로, variant, 경고 로그 |
| 정지 물리 | 정지 명령에서 차체 높이와 관절 상태가 허용 범위 안에 있다 | 상태 시계열, collider 화면 |
| 저속 제어 | 이름 기준 관절 대응과 회전 방향이 맞다 | 명령·측정값 기록 |
| 카메라 | 유효한 프레임, 맞는 광축, 기대한 표적과 거리 | RGB·depth·pose |
| LiDAR | tick/scan 일치, 유효 거리와 필요한 scan 범위 | 센서 속성, 점 수와 범위 |
| IMU | 중력·축 정의와 측정값 변화가 일치한다 | 정지·회전 구간의 측정값 |
| ROS | 시간 증가, TF 연결, JointState 배열 대응이 맞다 | topic 출력, TF 결과 |
| reset | Stop/Play와 재시작 후 데이터·제어가 복구된다 | 전후 로그 |
| 데이터 생성 | 실제 저장 파일과 설정한 센서·duration이 일치한다 | 출력 manifest와 샘플 |

정적 문법 검사와 공식 문서 대조는 실행 검사의 준비 단계이다. GPU에서 얻은 이미지와 물리 로그가 없는 상태에서는 렌더링·붕괴·노이즈·블랙아웃이 없다고 보증하지 않는다. 실패하면 마지막으로 통과한 단일 센서·단일 로봇 장면으로 범위를 좁히고, 문제를 재현하는 작은 장면을 저장한다.

## 부록: 공식 출처와 확인할 범위

| 공식 문서 | 이 가이드에서 사용한 범위 |
|---|---|
| [5.1.0 Release Notes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html) | 비교 기준 Kit 버전 |
| [6.0.1 Release Notes](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/release_notes.html) | GA·패치 계보, 패치 핵심, ROS extension 분리 |
| [6.0 Migration Guides](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/index.html) | 이관 문서 전체 목차 |
| [ROS Installation](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_ros.html) | 시스템 Jazzy와 내부 라이브러리 선택 |
| [ROS Reference Architecture](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/ros2_reference_architecture.html) | simulation 실행과 ROS 노드 작동 관계 |
| [Camera Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_camera_to_experimental_rtx.html) | authoring/runtime 분리, 배열 인수, 데이터 반환 |
| [RTX Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_rtx_to_experimental_rtx.html) | LiDAR·Radar·Acoustic API 변경 |
| [Physics Sensor Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_physics_to_experimental_physics.html) | IMU 생성과 측정 API |
| [Multi-Tick Rendering](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_multitick_rendering.html) | 센서 rate, scanRate 일치, 물리 시간 기준 |
| [ROS OmniGraph Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ros2_omnigraph_migration.html) | TF·JointState source/publisher 포트 연결 |
| [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/asset_structure.html) | 공통 구조와 엔진·기능별 layer 구분 |
| [Newton Physics](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/newton_physics.html) | experimental backend 선택과 호환성 범위 |
| [IRA Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/ext_isaacsim_replicator_agent_migration_guide.html) | 설정 구조와 시간 단위 변경 |
| [MobilityGen Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/mobility_gen_recordings_migration.html) | 녹화 상태 포맷과 변환 도구 |
| [Surface Gripper Migration](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/surface_gripper_bindings_import.html) | compiled binding import 변경 |
| [Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html) | 렌더링·메모리·SDG 관련 알려진 제약 |

[튜토리얼 처음으로 돌아가다](../README.md)
