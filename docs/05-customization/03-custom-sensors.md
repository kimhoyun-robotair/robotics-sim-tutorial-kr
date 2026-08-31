# 커스텀 센서: 기존 센서 조립부터 Python 센서 개발까지

이 장에서는 robot에 camera, RTX LiDAR·Radar, IMU, contact, effort, proximity sensor를 부착하고 데이터를 읽는다. 이어서 기존 sensor를 조합하는 경우와 새로운 측정 원리를 Python Extension·OmniGraph로 구현하는 경우를 구분한다. 기준은 Isaac Sim 5.1.0, Ubuntu 24.04, ROS 2 Jazzy이다.

> **5.1 버전 경계**  
> 이 장은 `isaacsim.*` 모듈과 5.1 sensor prim을 사용한다. 4.5 이전 RTX sensor의 `Camera` prim + JSON `sensorModelConfig` 방식은 5.0부터 deprecated이다. LiDAR는 `OmniLidar`, Radar는 `OmniRadar` prim을 사용한다.

## 1. sensor를 고르는 기준

| sensor | 측정 대상 | 계산 자원 | 적합한 용도 |
|---|---|---|---|
| Camera | RGB, depth, segmentation, motion vector | RTX render·VRAM | perception, calibration, synthetic data |
| RTX LiDAR | ray return, range, intensity, point cloud | RTX render·VRAM | 2D/3D mapping, obstacle detection |
| RTX Radar | range·방향·속도 성분과 material 반응 | RTX render·VRAM | 악천후 perception, Doppler 계열 실험 |
| IMU | local acceleration, angular velocity, orientation | physics | localization, state estimation |
| Contact | collider의 영역별 contact force | physics | foot pad, bumper, gripper contact |
| Effort | revolute joint torque 또는 prismatic joint force | physics | load monitoring, impedance control |
| Proximity | 부착 prim과 다른 prim의 collision 관계 | physics callback | overlap·충돌 event, safety zone prototype |

Proximity Sensor는 광학식 거리계가 아니다. 충돌 관계를 callback으로 기록하는 wrapper이다. 연속 거리 ray가 필요하면 PhysX ray query, RTX LiDAR 또는 별도 custom sensor를 사용한다.

## 2. 먼저 measurement contract를 작성한다

sensor를 Stage에 넣기 전에 다음 항목을 YAML로 고정한다.

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

contract에는 prim path, parent frame, sensor frame, sample rate, timestamp 기준, 단위, 유효 범위, noise seed, ROS type·topic·QoS를 넣는다. “30 Hz camera”가 capture 30 Hz인지 ROS publish 30 Hz인지도 구분한다.

## 3. sensor rig와 좌표계를 설계한다

robot link 아래에 한 개의 rig Xform을 두고 sensor별 mount Xform을 분리한다.

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

- Camera wrapper의 quaternion은 scalar-first `[w, x, y, z]`이다.
- ROS `geometry_msgs/Quaternion` 필드는 `x, y, z, w` 순서이다.
- USD Camera는 +Y up, -Z forward convention을 사용한다.
- Camera API의 optical 좌표는 +Z forward, +X right, +Y down이다.
- ROS publisher의 `frame_id`는 TF에 실제로 존재해야 한다.
- IMU와 contact sensor는 측정할 rigid body 또는 collider 아래에 둔다.

extrinsic은 `$T_{parent}^{sensor}$` 한 개를 원본으로 관리한다. USD transform과 ROS static TF에 같은 숫자를 따로 손으로 입력하지 말고 calibration manifest에서 생성한다.

Stage에서 transform을 확인한다.

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

physics sensor의 parent를 바꾸거나 sensor prim을 이동할 때는 타임라인을 먼저 멈춘다. IMU와 contact sensor는 Play에서 동적으로 생성되므로 재생 중 계층을 바꾸면 reading이 무효가 될 수 있다.

## 4. Camera

### 4.1 GUI에서 만든다

1. `Create > Camera`로 Camera prim을 만든다.
2. Stage에서 camera를 `front_camera_mount` 아래로 옮긴다.
3. Property의 Transform에서 translation과 orientation을 입력한다.
4. viewport 상단 camera 아이콘에서 이 camera를 선택해 시야를 확인한다.
5. focal length, aperture, clipping range를 calibration 사양과 맞춘다.

Camera prim만으로 ROS image가 생기지는 않는다. render product와 annotator 또는 ROS Camera Helper가 필요하다.

### 4.2 Python으로 만들고 읽는다

다음은 Isaac Sim Standalone script의 핵심이다. `SimulationApp`을 먼저 만든 뒤 Isaac 모듈을 import한다.

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np
from isaacsim.core.api import World
from isaacsim.sensors.camera import Camera

world = World(stage_units_in_meters=1.0)
camera = Camera(
    prim_path="/World/Robot/base_link/Sensors/front_camera_mount/Camera",
    name="front_camera",
    frequency=30,
    resolution=(1280, 720),
    translation=np.array([0.20, 0.0, 0.35]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
)

world.reset()
camera.initialize()
camera.add_distance_to_image_plane_to_frame()

for _ in range(10):
    world.step(render=True)

rgba = camera.get_rgba()
depth = camera.get_depth()
K = camera.get_intrinsics_matrix()

assert rgba.shape == (720, 1280, 4)
assert depth.shape == (720, 1280)
assert np.isfinite(K).all()
print("K=", K)

simulation_app.close()
```

`frequency`와 `dt`를 동시에 주지 않는다. 이미 만든 render product를 공유할 때는 서로 다른 Camera wrapper가 같은 render product의 camera와 resolution을 서로 덮어쓰지 않게 한다.

### 4.3 intrinsic과 lens distortion을 맞춘다

OpenCV pinhole calibration의 $K$와 distortion coefficient를 적용할 수 있다.

```python
width, height = 1280, 720
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
```

5.1에서는 native OpenCV pinhole·fisheye model과 `OmniLensDistortion` schema를 사용한다. 이전 projection attribute나 fisheye polynomial 근사 API를 새 asset의 원본으로 삼지 않는다.

calibration acceptance test는 알려진 3D 점을 image에 projection하고 측정 pixel과 비교한다.

```python
world_points = np.array([[2.0, 0.0, 0.5], [3.0, 0.2, 1.0]])
pixels = camera.get_image_coords_from_world_points(world_points)
assert np.isfinite(pixels).all()
assert ((pixels[:, 0] >= 0) & (pixels[:, 0] < width)).all()
assert ((pixels[:, 1] >= 0) & (pixels[:, 1] < height)).all()
```

### 4.4 noise를 별도 layer로 둔다

ground truth와 noisy output을 같은 topic으로 덮어쓰지 않는다. 먼저 noise 없는 sensor를 검증한 뒤 seed, 분포, 단위, 적용 순서를 기록한 augmentation을 추가한다.

```python
import numpy as np

def add_read_noise(rgb_u8, sigma, seed):
    rng = np.random.default_rng(seed)
    noisy = rgb_u8.astype(np.float32)
    noisy += rng.normal(0.0, sigma, size=noisy.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)

noisy_rgb = add_read_noise(rgba[..., :3], sigma=4.0, seed=42)
```

실시간 GPU pipeline에는 Replicator augmentation이나 Warp kernel을 사용한다. camera noise에는 read/shot noise, exposure, motion blur, lens distortion을 구분하고, depth에는 range-dependent noise와 dropout을 별도로 모델링한다.

## 5. RTX LiDAR와 Radar

### 5.1 5.1 prim과 data pipeline

RTX sensor는 GPU에서 render하고 결과를 `GenericModelOutput` AOV에 쓴다.

```text
OmniLidar 또는 OmniRadar
        → Render Product
        → GenericModelOutput AOV
        → RTX Annotator
        → Python / ROS 2 Writer
```

LiDAR에는 `OmniSensorGenericLidarCoreAPI`, Radar에는 `OmniSensorGenericRadarWpmDmatAPI` schema가 적용된다. old Camera prim을 강제로 만드는 `force_camera_prim=True`는 migration 확인 외에는 사용하지 않는다.

### 5.2 LiDAR를 만들고 읽는다

상위 `LidarRtx` wrapper는 prim, render product, annotator를 함께 관리한다.

```python
import numpy as np
import omni
from isaacsim.sensors.rtx import LidarRtx

lidar = LidarRtx(
    prim_path="/World/Robot/base_link/Sensors/lidar_mount/OmniLidar",
    translation=np.array([0.0, 0.0, 0.4]),
    orientation=np.array([1.0, 0.0, 0.0, 0.0]),
    config_file_name="Example_Rotary",
    **{"omni:sensor:Core:scanRateBaseHz": 20},
)
lidar.initialize()
lidar.attach_annotator("IsaacExtractRTXSensorPointCloudNoAccumulator")

timeline = omni.timeline.get_timeline_interface()
timeline.play()

for _ in range(20):
    omni.kit.app.get_app().update()

frame = lidar.get_current_frame()
assert "IsaacExtractRTXSensorPointCloudNoAccumulator" in frame
print(frame.keys())
```

누적 한 scan이 필요하면 `IsaacCreateRTXLidarScanBuffer`를 붙인다.

```python
lidar.attach_annotator(
    "IsaacCreateRTXLidarScanBuffer",
    outputDistance=True,
    outputIntensity=True,
    outputTimestamp=True,
)
```

회전 속도가 frame rate보다 느릴 때 accumulated scan에는 여러 frame의 return이 섞인다. sensor나 물체가 움직이면 point가 끌리는 것처럼 보일 수 있다. 순간 obstacle detection에는 `NoAccumulator`, 완전한 회전 scan에는 accumulator를 선택한다.

custom LiDAR model은 5.1 schema가 적용된 `OmniLidar` USD를 별도 asset으로 authoring한다. 간단한 generic prim은 command에서 `config=None`으로 만들 수 있다. emitter state attribute는 schema가 요구하는 `...:s001:...` 같은 instance prefix를 정확히 사용한다.

### 5.3 Radar를 만든다

5.1의 Radar는 `IsaacSensorCreateRtxRadar` command로 `OmniRadar` prim을 만든다.

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

Script Editor에서 command를 실행한 뒤 Stage의 `OmniRadar`를 선택해 Raw USD Properties와 transform을 GUI로 확인한다. data는 render product에 `IsaacExtractRTXSensorPointCloudNoAccumulator` annotator를 붙여 읽는다. 이 annotator는 5.1에서 LiDAR와 Radar를 함께 지원한다. 전체 예제는 다음 명령으로 실행한다.

```bash
cd ~/isaacsim
./python.sh standalone_examples/api/isaacsim.util.debug_draw/rtx_radar.py
```

Radar와 LiDAR return은 visual material 색만으로 정해지지 않는다. RTX non-visual material attribute를 사용하고, 알려진 거리의 plane·corner target과 material별 return을 검증한다.

### 5.4 RTX calibration과 noise

다음을 실측 사양과 비교한다.

- mount translation·orientation과 ROS TF
- min/max range, horizontal·vertical FOV
- channel/elevation/azimuth pattern과 scan/tick rate
- range bias, angular bias, dropout, intensity 분포
- moving target의 timestamp와 velocity 부호
- non-visual material별 return

noise는 annotator 후단에서 추가할 수도 있지만, material·multipath처럼 ray 생성과 상호작용하는 현상을 단순 Gaussian noise로 대체했다고 표현하지 않는다.

RTX annotator는 sensor output buffer가 GPU에 있어야 정상 동작한다. normal output을 켜면 VRAM 사용량이 증가한다. 필요한 field만 활성화한다.

## 6. IMU

### 6.1 GUI와 update rate

1. `Create > Physics > Physics Scene`으로 physics scene을 만든다.
2. IMU를 붙일 rigid body prim을 선택한다.
3. `Create > Sensors > Imu Sensor`를 선택한다.
4. `Imu_Sensor`의 local transform을 mount 사양과 맞춘다.
5. Raw USD Properties에서 sensor period와 세 filter width를 설정한다.

sensor period가 physics delta보다 작아도 새로운 physics sample이 더 생기지는 않는다. physics가 60 Hz라면 IMU를 200 Hz로 설정해도 최신 60 Hz data가 반복된다.

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

filter width를 키우면 부드러워지지만 latency도 커진다. noise와 filter를 혼동하지 않는다. IMU model에는 axis misalignment, scale factor, white noise, bias, bias random walk, saturation, timestamp offset을 선택적으로 추가한다. stationary test에서는 angular velocity가 0에 가깝고, gravity를 읽도록 했다면 acceleration norm이 stage gravity에 가까워야 한다.

## 7. Contact Sensor

Contact Sensor는 PhysX Contact Report를 특정 parent와 선택적 구면 영역으로 filter한다. sensor가 붙는 parent에는 collider가 필요하다.

### 7.1 GUI

1. collider가 있는 foot, bumper 또는 gripper pad prim을 선택한다.
2. `Create > Sensors > Contact Sensor`를 선택한다.
3. `radius`, min/max threshold, sensor period를 설정한다.
4. Action Graph에 `Isaac Read Contact Sensor`를 넣고 sensor prim을 지정한다.
5. `Isaac xPrim Radius Visualizer`로 filter 영역을 확인한다.

구면 radius는 실제 collision volume을 새로 만드는 것이 아니라 이미 발생한 contact를 filter하는 영역이다.

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

known mass를 sensor 위에 정적으로 올려 $F \approx mg$를 확인하고, no-contact 상태에서 false positive가 없는지 검사한다. threshold와 saturation은 실제 sensor datasheet에 맞춘다.

## 8. Effort Sensor

Effort Sensor는 revolute joint에서 torque, prismatic joint에서 force magnitude를 읽는다. prim path는 link가 아니라 측정할 joint를 가리킨다.

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

GUI에서는 Physics Inspector로 joint를 움직이고 drive target과 measured effort를 함께 관찰한다. calibration은 무부하 zero offset과 알려진 lever arm·weight로 수행한다. drive가 만드는 effort, gravity compensation, external contact를 구분해 시험한다.

## 9. Proximity Sensor

5.1 Proximity Sensor는 `isaacsim.sensors.physx` extension의 collision callback wrapper이다.

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

extension 종료 때 callback을 제거하고 `clear_sensors()`를 호출한다. collision layer와 collider가 맞지 않으면 data가 비어 있다. 거리계처럼 사용하려면 알려진 separation에서 의미를 먼저 확인하고, 필요한 측정이 collision event가 아니라면 다른 sensor로 바꾼다.

## 10. 기존 sensor 조합과 진짜 custom sensor를 구분한다

### 10.1 기존 sensor 조합

다음은 custom **rig 또는 pipeline**이지 새로운 물리 sensor가 아니다.

- RGB + depth + IMU를 하나의 device USD로 조립한다.
- LiDAR point cloud에서 특정 sector만 자른다.
- contact force와 joint effort를 합쳐 grasp state를 만든다.
- camera image에 noise·latency·dropout을 추가한다.
- ROS message format과 topic을 custom하게 만든다.

가능하면 검증된 built-in sensor를 조합한다. physics·render 구현을 다시 만들 필요가 없고, ground truth와 noisy output을 나란히 유지하기 쉽다.

### 10.2 진짜 custom sensor

다음 조건이면 Python Extension 또는 custom OmniGraph node를 만든다.

- 새로운 measurement equation이 필요하다.
- physics step과 정확히 동기화된 stateful sampling이 필요하다.
- bias drift, hysteresis, dead time 같은 내부 상태가 필요하다.
- 여러 prim의 값을 한 device state로 결합해야 한다.
- GUI와 headless에서 재사용할 lifecycle이 필요하다.

## 11. Python Extension으로 custom accelerometer를 만든다

예제는 rigid body의 world position을 physics step마다 미분하고, 일정 주기로 sampling해 noise를 더한다. 실제 제품은 PhysX velocity API를 직접 읽는 편이 더 정확하지만, 여기서는 lifecycle·rate·state 설계에 집중한다.

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
"omni.physx" = {}

[[python.module]]
name = "custom.motion.sensor"
```

`registry.py`는 Extension과 OGN 사이의 작은 data contract이다.

```python
LATEST = {}
```

`extension.py`의 핵심은 physics subscription과 정리이다.

```python
import numpy as np
import omni.ext
import omni.physx
import omni.usd
from pxr import Usd, UsdGeom

from .registry import LATEST


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._path = "/World/Robot/base_link"
        self._period = 1.0 / 100.0
        self._elapsed = 0.0
        self._time = 0.0
        self._last_position = None
        self._last_velocity = None
        self._rng = np.random.default_rng(42)
        self._subscription = (
            omni.physx.get_physx_interface()
            .subscribe_physics_step_events(self._on_physics_step)
        )

    def _position(self):
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(self._path)
        if not prim.IsValid():
            return None
        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        return np.asarray(matrix.ExtractTranslation(), dtype=np.float64)

    def _on_physics_step(self, dt):
        position = self._position()
        if position is None or dt <= 0.0:
            return

        if self._last_position is None:
            self._last_position = position
            self._last_velocity = np.zeros(3)
            return

        velocity = (position - self._last_position) / dt
        acceleration = (velocity - self._last_velocity) / dt
        self._last_position = position
        self._last_velocity = velocity
        self._elapsed += dt
        self._time += dt

        if self._elapsed + 1e-12 < self._period:
            return
        self._elapsed %= self._period

        noisy = acceleration + self._rng.normal(0.0, 0.02, size=3)
        LATEST["base_accel"] = {
            "time": self._time,
            "value": noisy,
            "frame_id": "base_link",
        }

    def on_shutdown(self):
        self._subscription = None
        LATEST.clear()
```

핵심 원칙은 다음과 같다.

- render update가 아니라 physics step에서 sampling한다.
- sample accumulator로 physics rate와 sensor rate를 분리한다.
- noise RNG seed를 manifest에 기록한다.
- stage가 바뀌어 prim path가 무효가 되는 경우를 처리한다.
- shutdown에서 subscription과 shared state를 정리한다.
- reset·time jump 때 이전 position·velocity·bias state도 reset한다.

## 12. OmniGraph node로 노출한다

`.ogn` schema는 scalar port로 시작하면 type 문제를 줄일 수 있다.

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

Python compute는 shared sample을 읽고 즉시 반환한다. 여기서 block이나 sleep을 하지 않는다.

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

Extension Manager의 search path에 project root를 추가하고 extension을 활성화한다. Action Graph에서 custom node를 `On Physics Step` 또는 필요한 publisher와 연결한다. reset, stop/play, stage reload를 각각 시험한다.

## 13. ROS 2 publish contract

| data | 권장 ROS type | 필수 계약 |
|---|---|---|
| RGB/depth | `sensor_msgs/msg/Image` | encoding, width/height, capture timestamp, optical frame |
| camera calibration | `sensor_msgs/msg/CameraInfo` | K, D, distortion model, image와 같은 frame/time |
| planar LiDAR | `sensor_msgs/msg/LaserScan` | angle/range 단위, scan time, sensor frame |
| 3D LiDAR/Radar points | `sensor_msgs/msg/PointCloud2` | field 이름·단위·frame을 문서화한다 |
| IMU | `sensor_msgs/msg/Imu` | covariance, local frame, gravity 포함 여부 |
| joint effort | `sensor_msgs/msg/JointState` 또는 custom | joint name과 effort 단위 |
| contact/proximity event | custom msg 권장 | threshold, object path, duration, force 의미 |
| custom acceleration | `geometry_msgs/msg/AccelStamped` | frame, unit, timestamp |

Radar detection에는 모든 제품을 포괄하는 단일 표준 message가 없다. `PointCloud2`를 쓰면 `range`, `azimuth`, `elevation`, `radial_velocity`, `rcs` 같은 field의 단위와 의미를 별도 문서에 고정한다.

Action Graph publisher는 다음 규칙을 지킨다.

1. `Isaac Read Simulation Time`을 header timestamp에 연결한다.
2. sensor capture 시각을 사용하고 ROS 전송 시각으로 대체하지 않는다.
3. `frameId`가 `/tf` 또는 `/tf_static`에 존재하게 한다.
4. image·point cloud에는 Sensor Data QoS를 사용하고 subscriber와 일치시킨다.
5. `frameSkipCount=N`은 N개를 건너뛰고 N+1번째 frame을 발행한다.
6. source sensor rate보다 빠른 publisher는 새 data를 만들지 못한다.

ROS 측에서 contract를 검증한다.

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

covariance를 모델링하지 않았다면 0 행렬로 “완벽한 측정”을 표현하지 않는다. ROS message 규약에 따라 unknown을 명시하고, noise model을 넣은 뒤 통계에 맞는 covariance를 제공한다.

## 14. 자동 acceptance test

### 14.1 공통 rate·timestamp 검사

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

### 14.2 sensor별 ground-truth scenario

| sensor | 고정 scenario | 합격 조건 예 |
|---|---|---|
| Camera | 알려진 3D marker board | reprojection RMS가 허용 pixel 이내이다 |
| Depth | 정면 plane 2 m | 중앙 ROI median이 2 m 허용 오차 이내이다 |
| LiDAR | 1·3·5 m plane | range bias와 dropout이 사양 이내이다 |
| Radar | 고정·일정 속도 target | range와 radial velocity 부호·오차가 맞다 |
| IMU | 정지 후 일정 회전 | stationary bias와 angular velocity가 맞다 |
| Contact | known mass와 no-contact | $mg$와 threshold/hysteresis가 맞다 |
| Effort | known lever arm·mass | expected torque와 offset이 맞다 |
| Proximity | overlap 진입·이탈 | event path와 duration이 맞다 |
| Custom | fixed trajectory·seed | golden trace와 tolerance 안에서 일치한다 |

noise test는 한 frame 값을 비교하지 않고 충분한 sample의 mean, standard deviation, autocorrelation, dropout rate를 비교한다. 같은 seed에서 replay가 재현되는지도 검사한다.

## 15. 성능과 VRAM

camera와 RTX sensor는 먼저 GPU 병목을 의심한다. physics sensor와 Python custom sensor는 callback 수와 CPU 병목을 먼저 본다.

```bash
nvidia-smi dmon -s pucm
ros2 topic hz /robot_01/lidar/points --window 100
ros2 topic bw /robot_01/lidar/points
```

최적화 순서는 다음과 같다.

1. 사용하지 않는 sensor, annotator, writer를 끈다.
2. camera resolution과 RTX auxiliary output을 줄인다.
3. normal·material ID·object ID처럼 필요할 때만 field를 켠다.
4. 같은 camera에 render product를 불필요하게 중복 생성하지 않는다.
5. `frameSkipCount`로 ROS publish rate를 낮춘다.
6. GPU data를 매 frame CPU numpy로 복사하지 않는다.
7. 여러 physics sensor는 한 callback에서 batch로 읽는다.
8. GUI와 headless의 RTF, GPU memory, topic rate를 같은 scenario에서 비교한다.

RTX annotator는 `GenericModelOutput` GPU buffer를 요구한다. GPU output setting을 끄면 annotator가 정상 동작하지 않을 수 있다. LiDAR normal output은 VRAM과 실행 시간을 늘린다는 5.1 경고가 있다.

## 16. failure diagnosis

| 증상 | 원인 후보 | 우선 검사 |
|---|---|---|
| Camera image가 없다 | render product·timeline·orientation | viewport를 camera로 바꾸고 `get_rgba()` shape를 본다 |
| depth가 두 색으로만 보인다 | infinite depth가 display 범위를 늘림 | numeric depth ROI와 clipping range를 본다 |
| RTX point가 없다 | old Camera workflow·AOV·GPU buffer·timeline | prim type, annotator, Play 상태를 본다 |
| LiDAR point가 끌린다 | accumulated scan과 움직이는 target | NoAccumulator 결과와 비교한다 |
| Radar return이 비현실적이다 | model·material·FOV 불일치 | known target와 non-visual material을 본다 |
| IMU가 반복값만 낸다 | sensor rate가 physics rate보다 빠름 | physics delta와 sensor period를 비교한다 |
| IMU reading이 invalid이다 | rigid body parent를 Play 중 변경 | Stop 후 계층을 고치고 다시 Play한다 |
| Contact가 invalid이다 | collider·Contact Report 없음 | parent collider와 threshold를 본다 |
| Effort가 invalid이다 | link path를 지정함 | 실제 joint prim path를 지정한다 |
| Proximity data가 비어 있다 | collision 없음·extension 미등록 | collider/filter와 `register_sensor`를 본다 |
| custom 값이 과거 stage 것이다 | subscription·registry 정리 누락 | shutdown/reset path를 시험한다 |
| ROS에서만 보이지 않는다 | QoS·frame·bridge·publish gate | `topic info --verbose`, TF, rate를 본다 |

## 17. 완료 체크리스트

- [ ] sensor prim이 올바른 rigid body·collider·mount 아래에 있다.
- [ ] extrinsic, quaternion order, ROS optical frame을 검증했다.
- [ ] physics/capture/publish rate를 각각 측정했다.
- [ ] calibration manifest와 noise seed를 version control에 넣었다.
- [ ] ground truth와 noisy output을 분리했다.
- [ ] RTX sensor가 `OmniLidar`·`OmniRadar` 5.1 workflow를 사용한다.
- [ ] custom Extension이 reset·shutdown에서 callback을 정리한다.
- [ ] ROS type, frame, timestamp, QoS, covariance contract를 검증했다.
- [ ] headless acceptance test와 성능 기준을 통과했다.

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
