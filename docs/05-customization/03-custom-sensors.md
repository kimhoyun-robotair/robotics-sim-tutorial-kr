# 커스텀 센서: 기존 센서 조립부터 Python 센서 개발까지

이 장에서는 로봇에 카메라, RTX LiDAR·Radar, IMU, 접촉, 토크·힘, 근접 센서를 부착하고 데이터를 읽는다. 이어서 기존 센서를 조합하는 경우와 새로운 측정 원리를 Python Extension·OmniGraph로 구현하는 경우를 구분한다. 기준은 Isaac Sim 5.1.0, Ubuntu 24.04, ROS 2 Jazzy이다.

> **5.1에서 사용할 센서 형식**
> 이 장은 `isaacsim.*` 모듈과 5.1 센서 prim을 사용한다. RTX 센서를 `Camera` prim과 JSON `sensorModelConfig`로 구성하던 4.x 방식은 5.0부터 사용 중단 예정(deprecated)으로 표시되었다. 일반 영상 카메라의 `Camera` prim을 뜻하는 것은 아니다. LiDAR는 `OmniLidar`, Radar는 `OmniRadar` prim을 사용한다.

## 1. 센서를 고르는 기준

| 센서 | 측정 대상 | 계산 자원 | 적합한 용도 |
|---|---|---|---|
| 카메라 | RGB, 깊이, 영역 분할, 움직임 벡터 | RTX 렌더링·VRAM | 인지, 보정, 합성 데이터 |
| RTX LiDAR | 광선의 반사점, 거리, 반사 강도, 포인트 클라우드 | RTX 렌더링·VRAM | 2D/3D 지도 작성, 장애물 감지 |
| RTX Radar | 거리·방향·속도 성분과 재질 반응 | RTX 렌더링·VRAM | 악천후 인지, 도플러 계열 실험 |
| IMU | 로컬 좌표계의 가속도, 각속도, 방향 | 물리 | 위치 추정, 상태 추정 |
| 접촉 | 충돌 형상의 영역별 접촉 힘 | 물리 | 발바닥 센서, 범퍼, 그리퍼 접촉 |
| 토크·힘 | 회전 관절 토크 또는 직선 관절 힘 | 물리 | 하중 관찰, 임피던스 제어 |
| 근접 | 부착 prim과 다른 prim의 충돌 관계 | 물리 콜백 | 겹침·충돌 이벤트, 충돌 구역 확인 |

근접 센서는 광학식 거리계가 아니다. 충돌 관계를 콜백으로 기록하는 API 객체이다. 연속 거리 측정이 필요하면 PhysX 레이캐스트, RTX LiDAR 또는 별도 사용자 센서를 사용한다.

## 2. 먼저 측정값 사양을 작성한다

센서를 Stage에 넣기 전에 다음 항목을 YAML로 고정한다.

```yaml
sensor_name: front_camera
prim_path: /World/Robot/base_link/Sensors/front_camera
parent_frame: base_link
sensor_frame: front_camera_link
optical_frame: front_camera_optical_frame
rate_hz: 30.0
latency_s: 0.0
resolution: [1280, 720]
near_far_m: [0.1, 50.0]
noise:
  enabled: false
  seed: 42
ros:
  image_topic: /robot_01/camera/front/image_raw
  info_topic: /robot_01/camera/front/camera_info
  qos: sensor_data
```

설정 기준에는 prim 경로, 부모 프레임, 센서 프레임, 표본 주기, 타임스탬프 기준, 단위, 유효 범위, 잡음 난수 시드, ROS 메시지 형식·토픽·QoS를 넣는다. “30 Hz 카메라”가 촬영 30 Hz인지 ROS 발행 30 Hz인지도 구분한다.

## 3. 센서 장착 구조와 좌표계를 설계한다

로봇 링크 아래에 한 개의 장착 구조 Xform을 두고 센서별 장착부 Xform을 분리한다.

```text
/World/Robot/base_link
└── Sensors
    ├── front_camera_mount
    │   └── Camera
    ├── lidar_mount
    │   └── OmniLidar
    ├── radar_mount
    │   └── OmniRadar
    └── Imu_Sensor
```

- 카메라 API 객체의 쿼터니언은 스칼라 우선 `[w, x, y, z]`이다.
- ROS `geometry_msgs/Quaternion` 필드는 `x, y, z, w` 순서이다.
- USD 카메라는 +Y 위, -Z 앞 좌표계 규칙을 사용한다.
- ROS 카메라 광학 좌표계는 +Z 전방, +X 오른쪽, +Y 아래쪽이다. Camera API의 기본 world 축과 구분한다.
- ROS 발행자의 `frame_id`는 TF에 실제로 존재해야 한다.
- IMU와 접촉 센서는 측정할 강체 또는 충돌 형상 아래에 둔다.

센서 장착 위치와 방향을 나타내는 외부 파라미터는 부모·센서 프레임 사이의 변환 하나로 관리한다. USD 변환과 ROS 정적 TF에 같은 숫자를 따로 손으로 입력하지 말고 보정 설정 파일에서 생성한다.

Stage에서 변환을 확인한다.

```python
import omni.usd
from pxr import Usd, UsdGeom

stage = omni.usd.get_context().get_stage()
path = "/World/Robot/base_link/Sensors/front_camera_mount/Camera"
prim = stage.GetPrimAtPath(path)
assert prim.IsValid(), path

matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
    Usd.TimeCode.Default()
)
print(matrix)
```

물리 센서의 부모를 바꾸거나 센서 prim을 이동할 때는 타임라인을 먼저 멈춘다. IMU와 접촉 센서는 Play에서 동적으로 생성되므로 재생 중 계층을 바꾸면 판독값이 무효가 될 수 있다.

## 4. 카메라

### 4.1 GUI에서 만든다

1. `Create > Camera`로 카메라 prim을 만든다.
2. Stage에서 카메라를 `front_camera_mount` 아래로 옮긴다.
3. Property의 변환에서 이동량과 방향을 입력한다.
4. Viewport 상단 카메라 아이콘에서 이 카메라를 선택해 시야를 확인한다.
5. 초점 거리, 수평·수직 필름 크기(aperture), 렌더링 거리 범위를 보정 결과와 맞춘다.

카메라 prim만으로 ROS 영상이 생기지는 않는다. 렌더 출력(Render Product)과 annotator 또는 ROS Camera Helper가 필요하다.

### 4.2 기준 장면에서 RGB·깊이를 먼저 확인한다

첫 실습에서는 로봇 장착을 미루고 [camera_imu.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/camera_imu.py)를 실행한다. 빈 장면을 촬영하면 검은 화면이 센서 오류인지 장면 구성 문제인지 구분하기 어렵다. 이 예제는 조명과 빨간 기준 물체를 코드에서 직접 만든다.

```bash
# 저장소 루트에서 실행한다.
"$ISAACSIM_PATH/python.sh" examples/standalone/camera_imu.py \
  --gui --output-dir results/camera_imu
```

실행 파일은 다음 순서로 구성되어 있다.

1. `SimulationApp`을 만든 뒤 Isaac Sim 모듈을 불러온다.
2. `World`를 만들고 물리·렌더링 간격을 각각 1/60초로 고정한다.
3. 바닥과 `DomeLight`를 만든다.
4. 한 변 0.5 m인 빨간 고정 큐브를 `(0, 0, 0.25)`에 놓는다. 윗면은 Z=0.5 m이다.
5. 카메라를 `(0, 0, 3)`에 두고 아래를 보게 한다.
6. `world.reset()` 뒤에 `camera.initialize()`를 호출하고 깊이 annotator를 붙인다.
7. `world.step(render=True)`를 반복하며 초기 준비 시간을 확보한다.
8. 서로 다른 시각의 영상 30개를 검사하고 RGB PNG와 센서 배열을 저장한다.

다음은 실행 파일에서 카메라를 구성하는 부분이다. `Camera` API의 기본 축은 +X 전방·+Z 위쪽이므로 Y축을 +90도로 회전하면 아래를 보게 된다. 쿼터니언의 순서는 `[w, x, y, z]`이다.

```python
from isaacsim.sensors.camera import Camera
from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats

camera = Camera(
    prim_path="/World/Camera",
    position=np.array([0.0, 0.0, 3.0]),
    orientation=euler_angles_to_quats(np.array([0, 90, 0]), degrees=True),
    frequency=30,
    resolution=(640, 480),
)
world.reset()
camera.initialize()
camera.set_clipping_range(0.1, 20.0)
camera.add_distance_to_image_plane_to_frame()
```

`get_depth()`는 영상 평면까지의 깊이를 미터 단위로 반환한다. 화면 중앙의 물체 윗면까지 깊이는 `3.0 - 0.5 = 2.5 m`이어야 한다. `distance_to_camera`는 광선 방향 거리이므로 주변 픽셀에서 같은 값이 아니다. 저장한 `sensor_data.npz`에는 `rgba`, `depth`, `intrinsics`, `camera_position`, `camera_orientation`가 들어 있다. 자세는 `camera_axes="world"`, 쿼터니언은 `wxyz` 기준임을 문자열 필드에도 기록한다.

```python
# 위 실행 파일이 완료된 뒤, NumPy를 사용할 수 있는 Python에서 확인한다.
import numpy as np

saved = np.load("results/camera_imu/sensor_data.npz")
print(saved["rgba"].shape)      # (480, 640, 4)
print(saved["depth"].shape)     # (480, 640)
print(saved["intrinsics"])     # 3 x 3 내부 파라미터 행렬
print(saved["depth"][240, 320]) # 기준 장면에서 약 2.5 m
```

이 검사가 통과하면 카메라를 실제 로봇 링크 아래로 옮기고 월드 위치 `position` 대신 장착부 기준 `translation`을 사용한다. 단순히 prim 경로에 `Robot/base_link`를 적는 것으로 실제 로봇이 생성되는 것은 아니다. 먼저 로봇을 불러오고, 카메라가 차체 안에 들어가지 않는지 GUI에서 확인한다.

### 4.3 내부 파라미터와 렌즈 왜곡을 맞춘다

OpenCV의 핀홀 카메라 보정에서 구한 내부 파라미터 행렬 $K$와 왜곡 계수를 적용할 수 있다. 아래 수치는 1280×720 영상용 예시이므로 실제 카메라 해상도와 보정 결과로 바꿔 사용한다. `camera_imu.py`를 복사한 뒤, 카메라 초기화가 끝나고 영상을 수집하기 전 위치에 이 설정을 넣는다. 프로그램이 종료된 다음에는 `camera`와 `world` 객체를 그대로 사용할 수 없다.

```python
width, height = 1280, 720
camera.set_resolution((width, height))
fx, fy = 910.0, 908.0
cx, cy = 640.5, 359.5
distortion = [0.08, -0.03, 0.0002, -0.0001, 0.004]
pixel_size_m = 3.0e-6

horizontal_aperture = pixel_size_m * width
vertical_aperture = pixel_size_m * height
focal_length = pixel_size_m * (fx + fy) * 0.5

camera.set_horizontal_aperture(horizontal_aperture)
camera.set_vertical_aperture(vertical_aperture)
camera.set_focal_length(focal_length)
camera.set_clipping_range(0.1, 50.0)
camera.set_opencv_pinhole_properties(
    cx=cx, cy=cy, fx=fx, fy=fy, pinhole=distortion
)

# 해상도를 바꾼 뒤 새 크기의 영상이 실제로 도착할 때까지 렌더링한다.
for _ in range(120):
    world.step(render=True)
    rgba = camera.get_rgba()
    if rgba is not None and rgba.shape == (height, width, 4):
        break
else:
    raise RuntimeError("새 해상도의 카메라 영상을 받지 못했습니다.")
```

해상도 변경은 다음 렌더 프레임부터 반영된다. 위 반복문이 끝난 뒤 얻은 새 영상으로 검사를 진행한다. 해상도를 바꾸기 전에 저장한 `rgba`·`depth` 배열을 새 내부 파라미터와 섞어 사용하지 않는다. 깊이 영상이 필요하면 깊이 annotator에서도 새 해상도의 프레임을 받은 뒤 사용한다.

5.1에서는 기본 제공 OpenCV pinhole·fisheye 모델과 `OmniLensDistortion` 스키마를 사용한다. 새 자산에는 이전 투영 속성이나 어안 렌즈 다항식 근사 API를 사용하지 않는다.

보정 결과는 위치를 아는 3D 점을 영상에 투영한 뒤, 실제 관측된 픽셀 위치와 비교해 검증한다. 아래 `world_points`에는 현재 카메라의 시야 안에 배치한 기준점의 월드 좌표를 넣는다. 이 `assert`는 좌표가 유한하고 영상 범위 안에 있는지 확인하는 기초 검사다. 보정 정확도까지 확인하려면 렌더링된 영상에서 기준점을 검출해 재투영 오차를 계산해야 한다.

```python
world_points = np.array([[0.0, 0.0, 0.5], [0.1, 0.1, 0.5]])
pixels = camera.get_image_coords_from_world_points(world_points)
assert np.isfinite(pixels).all()
assert ((pixels[:, 0] >= 0) & (pixels[:, 0] < width)).all()
assert ((pixels[:, 1] >= 0) & (pixels[:, 1] < height)).all()
```

### 4.4 잡음을 별도 처리 단계로 추가한다

잡음 없는 기준값과 잡음을 추가한 출력은 서로 다른 토픽으로 보관한다. 먼저 잡음 없는 센서를 검증한 뒤 난수 시드, 분포, 단위, 적용 순서를 기록한 데이터 변형을 추가한다.

```python
import numpy as np

def add_read_noise(rgb_u8, sigma, seed):
    rng = np.random.default_rng(seed)
    noisy = rgb_u8.astype(np.float32)
    noisy += rng.normal(0.0, sigma, size=noisy.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)

noisy_rgb = add_read_noise(rgba[..., :3], sigma=4.0, seed=42)
```

실시간 GPU 처리 과정에는 Replicator 데이터 변형이나 Warp 커널을 사용한다. 읽기 잡음과 광자 잡음, 노출, 모션 블러, 렌즈 왜곡은 서로 다른 현상이므로 적용 목적을 구분한다. 깊이 데이터에는 거리에 따른 오차와 측정 누락을 별도로 모델링한다.

## 5. RTX LiDAR와 Radar

### 5.1 Isaac Sim 5.1의 센서 Prim과 데이터 흐름

RTX 센서는 GPU에서 렌더링하고 결과를 `GenericModelOutput` AOV에 쓴다.

```text
OmniLidar 또는 OmniRadar
        → Render Product
        → GenericModelOutput AOV
        → RTX Annotator
        → Python / ROS 2 Writer
```

LiDAR에는 `OmniSensorGenericLidarCoreAPI`, Radar에는 `OmniSensorGenericRadarWpmDmatAPI` 스키마가 적용된다. 이전 카메라 prim을 강제로 만드는 `force_camera_prim=True`는 이전 버전에서의 전환 확인 외에는 사용하지 않는다.

### 5.2 여섯 벽으로 둘러싼 장면에서 LiDAR를 확인한다

[rtx_lidar.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/rtx_lidar.py)는 원점에 RTX LiDAR를 놓고 각 축의 ±3 m 위치에 벽을 만든다. 센서와 월드의 원점·방향이 같으므로 좌표 변환을 잘못 적용할 여지가 적다. 벽은 레이더나 카메라와 별개로 LiDAR의 거리 출력 자체를 확인하는 기준이다.

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/rtx_lidar.py \
  --gui --output-dir results/rtx_lidar
```

다음은 `World`와 벽을 만든 이후의 핵심 코드이다. 전체 초기화·반복·종료는 실행 파일을 사용한다.

```python
import numpy as np
from isaacsim.sensors.rtx import LidarRtx

lidar = LidarRtx(
    prim_path="/World/Lidar",
    translation=np.zeros(3),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
)
world.reset()
lidar.initialize()
lidar.attach_annotator("IsaacExtractRTXSensorPointCloudNoAccumulator")

# 실제 파일에서는 초기 준비 후 서로 다른 시각의 30개 출력을 검사한다.
world.step(render=True)
frame = lidar.get_current_frame()
print(frame.keys())
```

`frame`에 키가 있다는 사실만으로 성공으로 판정하지 않는다. `frame["IsaacExtractRTXSensorPointCloudNoAccumulator"]["data"]`가 비어 있지 않고 `(N, 3)` 배열인지, 점이 벽 위에 놓이는지, `rendering_time`이 증가하는지 함께 검사한다. 최초 데이터가 늦게 도착할 수 있으므로 최대 600스텝을 기다리되 그 안에도 충분한 데이터가 없으면 실패한다.

이 코드는 Standalone용이다. Script Editor에서 `omni.kit.app.get_app().update()`를 동기 반복 호출하지 않는다. GUI에서 직접 읽고 싶다면 `async def` 함수 안에서 `await omni.kit.app.get_app().next_update_async()`로 Kit 이벤트 루프에 제어권을 돌려준다.

누적 한 스캔이 필요하면 `IsaacCreateRTXLidarScanBuffer`를 붙인다.

```python
lidar.attach_annotator(
    "IsaacCreateRTXLidarScanBuffer",
    outputDistance=True,
    outputIntensity=True,
    outputTimestamp=True,
)
```

회전 속도가 프레임 주기보다 느릴 때 누적 스캔에는 여러 프레임의 반사점이 섞인다. 센서나 물체가 움직이면 점이 끌리는 것처럼 보일 수 있다. 순간 장애물 감지에는 `NoAccumulator`, 완전한 회전 스캔에는 누적 처리기를 선택한다.

사용자 정의 LiDAR 모델은 5.1 스키마가 적용된 `OmniLidar` USD를 별도 자산으로 작성한다. 기본 센서 Prim은 명령에서 `config=None`으로 만들 수 있다. 광선 발사부 상태 속성은 스키마가 요구하는 `...:s001:...` 같은 인스턴스 접두사를 정확히 사용한다.

### 5.3 Radar를 만든다

5.1의 Radar는 `IsaacSensorCreateRtxRadar` 명령으로 `OmniRadar` prim을 만든다.

```python
import omni
from pxr import Gf

_, radar_prim = omni.kit.commands.execute(
    "IsaacSensorCreateRtxRadar",
    translation=Gf.Vec3d(0.35, 0.0, 0.25),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
    path="OmniRadar",
    parent="/World/Robot/base_link/Sensors/radar_mount",
    visibility=False,
    variant=None,
    force_camera_prim=False,
    **{"omni:sensor:tickRate": 10},
)
assert radar_prim.IsValid()
```

Script Editor에서 명령을 실행한 뒤 Stage의 `OmniRadar`를 선택해 Raw USD Properties와 변환을 GUI로 확인한다. 데이터는 렌더 출력(Render Product)에 `IsaacExtractRTXSensorPointCloudNoAccumulator` annotator를 붙여 읽는다. 이 annotator는 5.1에서 LiDAR와 Radar를 함께 지원한다. 전체 예제는 다음 명령으로 실행한다.

```bash
cd ~/isaacsim
./python.sh standalone_examples/api/isaacsim.util.debug_draw/rtx_radar.py
```

Radar와 LiDAR 반사점은 시각 재질 색만으로 정해지지 않는다. RTX 비시각 재질 속성을 사용하고, 거리를 아는 평면·모서리 표적을 두고, 재질에 따른 반사점을 검증한다.

### 5.4 RTX 보정과 잡음

다음을 실측 사양과 비교한다.

- 장착부 이동량·방향과 ROS TF
- 최소·최대 측정 거리, 수평·수직 시야각(FOV)
- 채널별 고도각·방위각 패턴과 스캔·갱신 주기
- 거리 편향, 각도 편향, 누락, 반사 강도 분포
- 움직이는 목표의 측정 시각과 속도 부호
- 비시각 재질별 반사점

잡음은 annotator 후단에서 추가할 수도 있지만, 재질·다중 경로처럼 광선 생성과 상호작용하는 현상을 단순 가우스 잡음으로 대체했다고 표현하지 않는다.

RTX annotator는 센서 출력 버퍼가 GPU에 있어야 정상 동작한다. 법선 출력을 켜면 VRAM 사용량이 증가한다. 필요한 필드만 활성화한다.

## 6. IMU

### 6.1 GUI와 갱신 주기

1. `Create > Physics > Physics Scene`으로 물리 장면을 만든다.
2. IMU를 붙일 강체 prim을 선택한다.
3. `Create > Sensors > Imu Sensor`를 선택한다.
4. `Imu_Sensor`의 로컬 위치와 방향을 장착부 사양과 맞춘다.
5. Raw USD Properties에서 측정 주기와 가속도·각속도·방향 필터의 크기를 설정한다.

센서의 측정 간격을 물리 계산 간격보다 짧게 설정해도 새로운 물리 상태가 더 자주 계산되지는 않는다. 물리가 60 Hz라면 IMU를 200 Hz로 설정해도 최신 60 Hz 데이터가 반복된다.

### 6.2 Python으로 만들고 읽는다

```python
import numpy as np
from isaacsim.sensors.physics import IMUSensor

imu = IMUSensor(
    prim_path="/World/Robot/base_link/Imu_Sensor",
    name="base_imu",
    frequency=60,
    translation=np.array([0.0, 0.0, 0.15]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    linear_acceleration_filter_size=10,
    angular_velocity_filter_size=10,
    orientation_filter_size=10,
)

# World를 reset하고 Play/step한 뒤 읽는다.
reading = imu.get_current_frame(read_gravity=True)
print(reading)
```

필터에 사용하는 표본 수를 늘리면 출력은 부드러워지지만 지연도 커진다. 잡음을 추가하는 것과 필터를 적용하는 것은 별도 단계다. 실제 IMU를 모사할 때는 축 정렬 오차, 배율 오차, 백색 잡음, 편향과 시간에 따른 편향 변화, 포화, 타임스탬프 오프셋을 필요에 따라 추가한다. 정지 상태에서는 각속도가 0에 가까워야 한다. 중력을 포함해 읽는다면 가속도 벡터의 크기는 Stage의 중력 크기와 비슷해야 한다.

## 7. 접촉 센서

접촉 센서는 PhysX가 계산한 접촉 정보 중 센서가 붙은 물체와 지정한 구면 영역의 접촉만 읽는다. 센서가 붙는 부모에는 충돌 형상이 필요하다.

### 7.1 GUI

1. 충돌 형상이 있는 발바닥, 범퍼 또는 그리퍼 패드 Prim을 선택한다.
2. `Create > Sensors > Contact Sensor`를 선택한다.
3. `radius`, 최소·최대 임곗값, 센서 측정 주기를 설정한다.
4. Action Graph에 `Isaac Read Contact Sensor`를 넣고 센서 prim을 지정한다.
5. `Isaac xPrim Radius Visualizer`로 필터 영역을 확인한다.

`radius`는 이미 발생한 접촉 중 센서가 읽을 구면 영역을 정한다. 새 충돌 형상을 만드는 속성은 아니다.

### 7.2 Python

```python
import numpy as np
from isaacsim.sensors.physics import ContactSensor

contact = ContactSensor(
    prim_path="/World/Robot/left_foot/Contact_Sensor",
    name="left_foot_contact",
    frequency=120,
    translation=np.array([0.0, 0.0, -0.03]),
    min_threshold=1.0,
    max_threshold=5000.0,
    radius=0.06,
)

frame = contact.get_current_frame()
print(frame)
```

질량을 아는 물체를 센서 위에 올려 정지시킨 뒤 $F \approx mg$인지 확인한다. 접촉하지 않는 상태에서는 접촉을 잘못 검출하지 않는지도 검사한다. 임곗값과 포화 범위는 실제 센서 사양서에 맞춘다.

## 8. 관절 힘·토크(Effort) 센서

Effort 센서는 회전 관절의 토크 또는 직선 관절의 힘을 읽는다. prim 경로는 링크가 아니라 측정할 관절을 가리킨다.

```python
from isaacsim.sensors.physics.scripts.effort_sensor import EffortSensor

effort = EffortSensor(
    prim_path="/World/Robot/arm/joints/joint_3",
    sensor_period=0.01,
    use_latest_data=False,
    enabled=True,
)

reading = effort.get_sensor_reading(use_latest_data=True)
assert reading.is_valid
print("time=", reading.time, "effort=", reading.value)
```

GUI에서는 Physics Inspector로 관절을 움직이고 드라이브 목표와 측정된 힘·토크를 함께 관찰한다. 하중이 없는 상태에서 영점 오프셋을 확인한 뒤, 길이를 아는 레버에 질량을 아는 추를 달아 측정 토크를 비교한다. 드라이브가 가하는 힘·토크, 중력 보상, 외부 접촉의 영향을 나누어 시험한다.

## 9. 근접 센서

5.1 근접 센서는 `isaacsim.sensors.physx` Extension의 충돌 콜백 API 객체이다.

```python
from isaacsim.core.utils.extensions import enable_extension

enable_extension("isaacsim.sensors.physx")
simulation_app.update()

from isaacsim.sensors.physx import ProximitySensor, register_sensor

sensor = ProximitySensor(robot_bumper_prim)
register_sensor(sensor)

def on_physics_step(_step_size):
    data = sensor.get_data()
    for other_path, event in data.items():
        print(other_path, event["distance"], event["duration"])

world.add_physics_callback("read_bumper_proximity", on_physics_step)
```

Extension 종료 때 콜백을 제거하고 `clear_sensors()`를 호출한다. 충돌 레이어와 충돌 형상이 맞지 않으면 데이터가 비어 있다. 거리계처럼 사용하려면 물체 사이 거리를 알고 있는 장면에서 출력의 의미를 먼저 확인하고, 필요한 측정이 충돌 이벤트가 아니라면 다른 센서로 바꾼다.

## 10. 기존 센서 조합과 새로운 측정 모델 구분

### 10.1 기존 센서 조합

기존 센서의 장착 구조나 데이터 처리 방법을 바꾸는 예는 다음과 같다.

- RGB + 깊이 + IMU를 하나의 장치 USD로 조립한다.
- LiDAR 포인트 클라우드에서 특정 각도 구간만 자른다.
- 접촉 힘과 관절 토크·힘을 합쳐 파지 상태를 만든다.
- 카메라 영상에 잡음·지연·누락을 추가한다.
- 용도에 맞는 ROS 메시지 형식과 토픽을 정한다.

요구사항을 만족하는 기본 센서가 있다면 먼저 이를 조합한다. 기존 물리·렌더링 구현을 사용하면서 원본 측정값과 후처리 결과를 비교하기 쉽다.

### 10.2 새로운 측정 모델 구현

다음 조건이면 Python Extension 또는 사용자 정의 OmniGraph 노드를 만든다.

- 기존 센서가 지원하지 않는 측정 방정식이 필요하다.
- 이전 측정 상태를 기억하면서 물리 계산 주기에 맞춰 새 값을 생성해야 한다.
- 시간에 따른 편향 변화, 히스테리시스, 응답 지연 같은 내부 상태가 필요하다.
- 여러 prim의 값을 한 장치 상태로 결합해야 한다.
- GUI와 창 없는 실행에서 같은 초기화·갱신·종료 처리를 재사용해야 한다.

## 11. IMU 후처리를 Python Extension으로 만든다

이 예제는 6절에서 만든 IMU의 측정값을 물리 계산 주기마다 읽고, 새로운 타임스탬프의 유효한 값에만 잡음을 추가한다. Extension을 켤 때 콜백을 등록하고, 시뮬레이션이 초기화되거나 종료될 때 이전 표본을 정리하는 흐름을 익힌다. 위치를 수치 미분해 새로운 가속도 센서를 만드는 예제는 아니다.

### 11.1 파일 구조

```text
custom.motion.sensor/
├── config/extension.toml
└── custom/motion/sensor/
    ├── __init__.py
    ├── extension.py
    ├── registry.py
    └── ogn/python/nodes/
        ├── OgnReadMotionSensor.ogn
        └── OgnReadMotionSensor.py
```

`extension.toml`의 핵심이다.

```toml
[package]
version = "0.1.0"
title = "Custom Motion Sensor"

[dependencies]
"isaacsim.core.api" = {}
"isaacsim.sensors.physics" = {}
"omni.physx" = {}

[[python.module]]
name = "custom.motion.sensor"
```

`registry.py`는 Extension이 만든 최신 표본을 OmniGraph 노드와 공유하는 공간이다.

```python
LATEST = {}
```

`extension.py`에서는 물리 계산 이벤트를 구독해 IMU를 읽고, 종료할 때 구독과 저장된 표본을 정리한다.

```python
import numpy as np
import omni.ext
import omni.physx
from isaacsim.sensors.physics import _sensor
from .registry import LATEST


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # 6절에서 실제 강체에 붙인 IMU의 경로이다.
        self._path = "/World/Robot/base_link/Imu_Sensor"
        self._interface = _sensor.acquire_imu_sensor_interface()
        self._last_time = None
        self._noise_std = 0.0  # 기준 검사가 끝난 뒤에만 잡음을 추가한다.
        self._rng = np.random.default_rng(42)
        self._subscription = omni.physx.get_physx_interface().subscribe_physics_step_events(
            self._on_physics_step
        )

    def _on_physics_step(self, dt):
        reading = self._interface.get_sensor_reading(
            self._path, use_latest_data=True, read_gravity=False
        )
        if not reading.is_valid or dt <= 0:
            LATEST.clear()
            self._last_time = None
            return
        if self._last_time is not None:
            if reading.time == self._last_time:
                return
            if reading.time < self._last_time:
                # Stop/Reset 후 이전 실행의 값이나 난수 상태를 재사용하지 않는다.
                LATEST.clear()
                self._rng = np.random.default_rng(42)
        self._last_time = reading.time
        acceleration = np.array([reading.lin_acc_x, reading.lin_acc_y, reading.lin_acc_z])
        if not np.isfinite(acceleration).all():
            LATEST.clear()
            return
        LATEST["base_accel"] = {
            "time": float(reading.time),
            "value": acceleration + self._rng.normal(0, self._noise_std, size=3),
            "frame_id": "imu_link",  # 실제 IMU 축과 같은 TF 프레임을 별도로 발행한다.
        }

    def on_shutdown(self):
        self._subscription = None
        LATEST.clear()
```

이 예제는 **기존 IMU 측정값을 가공하는 확장 기능**이다. 새로운 물리 센서를 구현한 것은 아니다. `read_gravity=False`이므로 정지 상태의 선가속도는 0 근처이고, 출력 축은 IMU의 로컬 좌표계이다. 센서 원점이 회전 중심에서 떨어져 있으면 회전에 따른 가속도도 포함된다.

USD의 `ComputeLocalToWorldTransform()` 결과를 두 번 차분해 가속도를 구하지 않는다. USD에 기록된 값이 매 물리 계산 단계의 상태와 동기화된다는 보장이 없고, 두 번의 수치 차분은 작은 위치 오차를 큰 잡음으로 확대한다. 물리량을 읽는 목적이라면 IMU API 또는 초기화된 물리 객체 API를 사용한다. 수치 차분 센서를 별도로 연구할 때에는 그 한계와 좌표 변환을 명시해야 한다.

## 12. OmniGraph 노드에서 측정값 읽기

처음에는 `.ogn` 스키마에서 벡터를 X·Y·Z 각각의 실수 포트로 나누면 자료형과 연결을 확인하기 쉽다.

```json
{
  "ReadMotionSensor": {
    "version": 1,
    "language": "python",
    "uiName": "Read Custom Motion Sensor",
    "categories": ["Robotics"],
    "inputs": {
      "execIn": {"type": "execution"},
      "sensorName": {"type": "string", "default": "base_accel"}
    },
    "outputs": {
      "execOut": {"type": "execution"},
      "time": {"type": "double"},
      "x": {"type": "double"},
      "y": {"type": "double"},
      "z": {"type": "double"},
      "frameId": {"type": "string"},
      "valid": {"type": "bool"}
    }
  }
}
```

Python `compute()`는 공유 공간의 최신 표본을 읽고 즉시 반환한다. 여기서 오래 걸리는 계산이나 대기를 수행하면 그래프 실행이 막힐 수 있다.

```python
import omni.graph.core as og

from custom.motion.sensor.registry import LATEST


class OgnReadMotionSensor:
    @staticmethod
    def compute(db):
        sample = LATEST.get(db.inputs.sensorName)
        db.outputs.valid = sample is not None
        if sample is None:
            return True

        value = sample["value"]
        db.outputs.time = sample["time"]
        db.outputs.x = float(value[0])
        db.outputs.y = float(value[1])
        db.outputs.z = float(value[2])
        db.outputs.frameId = sample["frame_id"]
        db.outputs.execOut = og.ExecutionAttributeState.ENABLED
        return True
```

Extension Manager의 검색 경로에 프로젝트 루트를 추가하고 Extension을 활성화한다. Action Graph에서 사용자 정의 노드를 `On Physics Step` 또는 필요한 발행자와 연결한다. 초기화, Stop·Play, Stage 다시 불러오기를 각각 시험한다.

## 13. ROS 2 발행 설정

| 데이터 | 권장 ROS 메시지 형식 | 반드시 정할 항목 |
|---|---|---|
| RGB·깊이 | `sensor_msgs/msg/Image` | 인코딩, 영상 너비·높이, 촬영 타임스탬프, 광학 프레임 |
| 카메라 보정 | `sensor_msgs/msg/CameraInfo` | K·D 행렬, 왜곡 모델, 영상과 같은 프레임·타임스탬프 |
| 평면 LiDAR | `sensor_msgs/msg/LaserScan` | 각도·거리 단위, 스캔 시간, 센서 프레임 |
| 3D LiDAR·Radar 반사점 | `sensor_msgs/msg/PointCloud2` | 필드 이름·단위·프레임을 문서화한다 |
| IMU | `sensor_msgs/msg/Imu` | 공분산, 로컬 프레임, 중력 포함 여부 |
| 관절 토크·힘 | `sensor_msgs/msg/JointState` 또는 사용자 정의 | 관절 이름과 토크·힘 단위 |
| 접촉/근접 이벤트 | 사용자 정의 메시지 권장 | 임곗값, 물체 경로, 접촉 시간, 힘의 정의 |
| 가속도 후처리 출력 | `geometry_msgs/msg/AccelStamped` | 프레임, 단위, 타임스탬프 |

Radar 검출 결과는 제품마다 필요한 필드가 다르므로 사용할 메시지 형식을 명확히 정한다. `PointCloud2`를 쓰면 `range`, `azimuth`, `elevation`, `radial_velocity`, `rcs` 같은 필드의 단위와 의미를 별도 문서에 고정한다.

Action Graph 발행자는 다음 규칙을 지킨다.

1. `Isaac Read Simulation Time`을 메시지 헤더의 타임스탬프에 연결한다.
2. 센서 촬영 시각을 사용하고 ROS 전송 시각으로 대체하지 않는다.
3. `frameId`가 `/tf` 또는 `/tf_static`에 존재하게 한다.
4. 영상·포인트 클라우드에는 센서 데이터 QoS를 사용하고 구독자의 설정과 호환되는지 확인한다.
5. Camera Helper처럼 `frameSkipCount`를 제공하는 노드에서 값을 N으로 설정하면 N개를 건너뛰고 N+1번째 프레임을 발행한다.
6. 원본 센서 주기보다 빠른 발행자는 새 데이터를 만들지 못한다.

ROS 터미널에서 메시지 형식과 출력 주기를 확인한다.

```bash
source /opt/ros/jazzy/setup.bash

ros2 topic list -t | sort
ros2 topic info /robot_01/camera/front/image_raw --verbose
ros2 topic hz /robot_01/camera/front/image_raw --window 100
ros2 topic bw /robot_01/camera/front/image_raw
ros2 topic echo /robot_01/imu/data --once \
  --qos-reliability best_effort
ros2 run tf2_ros tf2_echo base_link front_camera_optical_frame
```

`sensor_msgs/msg/Imu`에서 공분산 행렬의 값이 모두 `0`이면 공분산을 알 수 없다는 뜻이다. 해당 측정값 자체를 제공하지 않는 경우에는 그 공분산 행렬의 첫 번째 원소를 `-1`로 설정한다. 예를 들어 자세를 추정하지 않는 IMU라면 `orientation_covariance[0] = -1`로 표시한다. 잡음 모델을 적용했다면 실제 출력의 통계에 맞는 공분산을 제공한다. 자세한 규약은 [ROS 2 Jazzy의 Imu 메시지 정의](https://docs.ros.org/en/jazzy/p/sensor_msgs/msg/Imu.html)를 참고한다.

## 14. 자동 검증 시험

### 14.1 공통 주기·타임스탬프 검사

```python
import numpy as np

def assert_rate(stamps, expected_hz, relative_tolerance=0.05):
    stamps = np.asarray(stamps, dtype=np.float64)
    delta = np.diff(stamps)
    assert len(delta) >= 10
    assert np.all(delta > 0.0), "timestamp must be monotonic"
    measured = 1.0 / np.mean(delta)
    error = abs(measured - expected_hz) / expected_hz
    assert error <= relative_tolerance, (measured, expected_hz)

def assert_finite(name, data):
    array = np.asarray(data)
    assert array.size > 0, name
    assert np.isfinite(array).all(), name
```

### 14.2 센서별 기준값을 아는 시험 장면

| 센서 | 고정 시험 상황 | 합격 조건 예 |
|---|---|---|
| 카메라 | 3D 위치를 아는 마커 보드 | 재투영 오차의 RMS가 허용 픽셀 수 이내이다 |
| 깊이 | 2 m 앞의 평면 | 중앙 관심 영역의 깊이 중앙값이 2 m의 허용 오차 이내이다 |
| LiDAR | 1·3·5 m 거리의 평면 | 거리 편향과 누락이 사양 이내이다 |
| Radar | 고정·일정 속도 목표 | 거리와 방사 방향 속도의 부호·오차가 맞다 |
| IMU | 정지 후 일정 회전 | 정지 편향과 각속도가 맞다 |
| 접촉 | 질량을 아는 하중과 무접촉 상태 | $mg$와 임곗값·히스테리시스가 맞다 |
| 힘·토크 | 길이를 아는 레버와 질량을 아는 추 | 계산한 토크와 측정값·오프셋이 맞다 |
| 근접 | 겹침 진입·이탈 | 이벤트 경로와 지속 시간이 맞다 |
| 사용자 정의 | 고정된 궤적과 난수 시드 | 기준 기록과 허용 오차 안에서 일치한다 |

잡음 시험은 한 프레임 값을 비교하지 않고 충분한 표본의 평균·표준편차·자기상관·누락 주기를 비교한다. 같은 난수 시드로 다시 실행했을 때 결과가 재현되는지도 검사한다.

## 15. 성능과 VRAM

카메라와 RTX 센서는 먼저 GPU 병목을 의심한다. 물리 센서와 Python 사용자 센서는 콜백 수와 CPU 병목을 먼저 본다.

```bash
nvidia-smi dmon -s pucm
ros2 topic hz /robot_01/lidar/points --window 100
ros2 topic bw /robot_01/lidar/points
```

최적화 순서는 다음과 같다.

1. 사용하지 않는 센서, annotator, writer를 끈다.
2. 카메라 해상도와 RTX 부가 데이터 출력을 줄인다.
3. 법선·재질 ID·물체 ID는 필요한 경우에만 켠다.
4. 같은 카메라에 렌더 출력(Render Product)을 불필요하게 중복 생성하지 않는다.
5. `frameSkipCount`로 ROS 발행 주기를 낮춘다.
6. GPU 데이터를 매 프레임 CPU의 NumPy 배열로 복사하지 않는다.
7. 여러 물리 센서는 한 콜백에서 모아 읽는다.
8. GUI와 화면 없이 실행하는 모드의 실시간 계수(RTF), GPU 메모리, 토픽 주기를 같은 시험 상황에서 비교한다.

RTX annotator는 `GenericModelOutput` GPU 버퍼를 요구한다. GPU 출력 설정을 끄면 annotator가 정상 동작하지 않을 수 있다. LiDAR 법선 출력은 VRAM과 실행 시간을 늘린다는 5.1 경고가 있다.

## 16. 오류 진단

| 증상 | 원인 후보 | 우선 검사 |
|---|---|---|
| 카메라 영상이 없다 | 렌더 출력(Render Product)·timeline·방향 | Viewport를 카메라로 바꾸고 `get_rgba()` 배열 형태를 본다 |
| 깊이 영상이 두 색으로만 보인다 | 무한대 깊이 값이 표시 범위를 넓힘 | 관심 영역의 실제 깊이 값과 카메라 거리 범위를 확인한다 |
| RTX 점이 없다 | 이전 Camera Prim 방식·AOV·GPU 버퍼·timeline | prim 자료형, annotator, Play 상태를 본다 |
| LiDAR 점이 끌린다 | 누적 스캔과 움직이는 목표 | NoAccumulator 결과와 비교한다 |
| Radar 반사점이 비현실적이다 | 모델·재질·FOV 불일치 | 위치·재질을 아는 표적과 비시각 재질을 본다 |
| IMU가 반복값만 낸다 | 센서 주기가 물리 주기보다 빠름 | 물리 계산 간격과 센서 측정 주기를 비교한다 |
| IMU 측정값이 유효하지 않다 | 강체 부모를 Play 중 변경 | Stop 후 계층을 고치고 다시 Play한다 |
| 접촉 측정값이 유효하지 않다 | 충돌 형상·접촉 정보 없음 | 부모 충돌 형상과 임곗값을 본다 |
| 힘·토크 측정값이 유효하지 않다 | 링크 경로를 지정함 | 실제 관절 prim 경로를 지정한다 |
| 근접 데이터가 비어 있다 | 충돌 없음·Extension 미등록 | 충돌 형상/필터와 `register_sensor`를 본다 |
| 사용자 정의 센서가 이전 장면의 값을 출력한다 | 구독·등록 목록 정리 누락 | 종료/초기화 경로를 시험한다 |
| ROS에서만 보이지 않는다 | QoS·프레임·Bridge·발행 실행 조건 | `topic info --verbose`, TF, 주기를 본다 |

## 17. 완료 체크리스트

- [ ] 센서 prim이 올바른 강체·충돌 형상·장착부 아래에 있다.
- [ ] 외부 파라미터, 쿼터니언 성분 순서, ROS 광학 프레임을 검증했다.
- [ ] 물리 계산·촬영·발행 주기를 각각 측정했다.
- [ ] 보정 설정 파일과 잡음 난수 시드를 버전 관리에 포함했다.
- [ ] 기준값과 잡음을 추가한 출력을 분리했다.
- [ ] RTX 센서가 `OmniLidar`·`OmniRadar` 5.1 방식을 사용한다.
- [ ] 사용자 정의 Extension이 초기화·종료에서 콜백을 정리한다.
- [ ] ROS 메시지 형식, 프레임, 타임스탬프, QoS, 공분산 설정을 검증했다.
- [ ] 화면 없이 실행하는 모드 검증 시험과 성능 기준을 통과했다.

## 출처

- [Isaac Sim 5.1 — Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [Isaac Sim 5.1 — Camera Python API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.camera/docs/index.html)
- [Isaac Sim 5.1 — RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [Isaac Sim 5.1 — RTX Radar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_radar.html)
- [Isaac Sim 5.1 — RTX Sensor Annotators](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_annotators.html)
- [Isaac Sim 5.1 — RTX Sensor Non-Visual Materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html)
- [Isaac Sim 5.1 — IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
- [Isaac Sim 5.1 — Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)
- [Isaac Sim 5.1 — Effort Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html)
- [Isaac Sim 5.1 — Proximity Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_proximity.html)
- [Isaac Sim 5.1 — Custom Python Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html)
- [Isaac Sim 5.1 — Extension Templates](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/templates_index.html)
- [Isaac Sim 5.1 — Add Noise to Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html)
- [Isaac Sim 5.1 — Publishing Camera's Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html)
- [Isaac Sim 5.1 — ROS2 Setting Publish Rates](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html)
