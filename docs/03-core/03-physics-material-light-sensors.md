# 물리, 재질, 조명과 센서

이 튜토리얼은 “보기 좋은 장면”과 “물리적으로 의미 있는 장면”을 분리해 설계하는 방법을 다룬다. 강체와 충돌체를 구성하고, 마찰과 반발을 조정하고, 조명·카메라·접촉 센서로 결과를 관측한다.

## 1. Physics Scene과 시간

Stage에는 보통 하나의 Physics Scene prim이 있으며 중력, solver, CPU/GPU dynamics와 CCD 같은 전역 설정을 가진다. GUI에서는 `Create > Physics > Physics Scene`으로 만든다. Core API에서 `World` 또는 `PhysicsContext`를 만들 때도 physics scene이 준비된다.

### timestep을 먼저 고정하기

물리 timestep은 정확도와 비용의 가장 중요한 축이다.

```python
from isaacsim.core.api import World

world = World(
    stage_units_in_meters=1.0,
    physics_dt=1.0 / 120.0,
    rendering_dt=1.0 / 60.0,
)
```

위 설정은 물리를 120 Hz, 렌더를 60 Hz로 진행한다. 빠른 그리퍼, 작은 물체, 강한 joint drive에서 timestep을 줄이면 안정성이 좋아질 수 있지만 계산량은 증가한다. timestep만 줄이고 controller의 `dt`를 그대로 두면 제어 동작이 달라지므로 함께 갱신한다.

## 2. 강체, 충돌체와 질량

### 구성 요소

| 요소 | 질문 | 잘못 설정했을 때 증상 |
|---|---|---|
| Visual geometry | 어떻게 보이는가? | 화면 모양만 이상하다. |
| Collider | 어디에서 접촉하는가? | 통과, 공중 접촉, 떨림이 생긴다. |
| Rigid Body | 힘을 받아 움직이는가? | 중력에 반응하지 않거나 정적 구조가 움직인다. |
| Mass/inertia | 얼마나 움직이기 어려운가? | 비현실적 가속, joint 불안정이 생긴다. |
| Physics material | 마찰·반발이 어떤가? | 미끄러짐, 튐이 현실과 다르다. |

동적 강체는 rigid body root 아래 여러 시각 mesh와 collider를 둘 수 있다. rigid body transform을 움직이면 자식 전체가 움직인다. collider 자식의 local transform은 body 기준 충돌 위치이다.

### Core API로 동적·정적 물체 만들기

```python
import numpy as np
from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid

dynamic_box = world.scene.add(
    DynamicCuboid(
        prim_path="/World/Props/DynamicBox",
        name="dynamic_box",
        position=np.array([0.0, 0.0, 1.5]),
        scale=np.array([0.2, 0.2, 0.2]),
        mass=0.5,
        color=np.array([0.8, 0.1, 0.1]),
    )
)

static_platform = world.scene.add(
    FixedCuboid(
        prim_path="/World/Props/Platform",
        name="platform",
        position=np.array([0.0, 0.0, 0.5]),
        scale=np.array([1.0, 1.0, 0.05]),
        color=np.array([0.2, 0.2, 0.25]),
    )
)
```

### raw USD schema로 의미 확인하기

```python
import omni.usd
from pxr import Gf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, "/World/RawCube")
cube.CreateSizeAttr(0.2)
cube.AddTranslateOp().Set(Gf.Vec3d(0.5, 0.0, 1.0))

prim = cube.GetPrim()
UsdPhysics.CollisionAPI.Apply(prim)
UsdPhysics.RigidBodyAPI.Apply(prim)
mass_api = UsdPhysics.MassAPI.Apply(prim)
mass_api.CreateMassAttr(1.0)
```

Core API는 이처럼 여러 schema를 적용하고 속성을 authoring하는 반복 작업을 묶는다. 복잡한 자산의 특정 속성을 수정할 때는 raw `pxr` API가 더 직접적이다.

## 3. 충돌 approximation 선택

복잡한 visual mesh를 그대로 충돌 계산에 쓰는 것은 비싸고 동적 강체에서 제약이 있다. 목적에 맞는 단순 collider를 별도로 만드는 것이 가장 좋다.

| approximation | 적합한 경우 | 특징 |
|---|---|---|
| Box/Sphere/Capsule | 바퀴, 링크, 상자, 단순 소품 | 가장 빠르고 안정적이다. |
| Convex Hull | 대체로 볼록한 단일 mesh | 빠르지만 오목한 부분을 메운다. |
| Convex Decomposition | 오목한 동적 물체 | 여러 hull로 근사해 정확도와 비용을 조절한다. |
| Triangle Mesh | 복잡한 정적 환경 | 정적 collider에 주로 사용한다. 동적 body에는 일반적으로 피한다. |
| SDF Mesh | 오목한 동적 형상이 꼭 필요한 경우 | 해상도·메모리 비용과 지원 제약을 검토한다. |

GUI에서 collider를 선택하고 Property의 Collider 설정에서 approximation을 바꾼다. Simulation Debug visualization으로 visual mesh와 collider가 어긋나지 않았는지 확인한다. hull 수가 적을수록 대체로 빠르다.

### 얇은 물체를 통과할 때

1. physics timestep을 줄인다.
2. collider 두께를 현실적으로 만든다.
3. Contact Offset을 너무 작게 두지 않았는지 확인한다.
4. 빠른 물체라면 Physics Scene과 해당 rigid body에서 CCD를 켠다.
5. solver iteration을 무작정 올리기 전에 scale, mass와 속도를 확인한다.

Rest Offset은 충돌 형상의 유효 표면을 조절하고, Contact Offset은 제약 생성을 시작하는 거리를 정한다. Contact Offset을 크게 하면 안정적일 수 있지만 접촉 pair 수와 비용이 늘고 물체가 떠 보일 수 있다.

## 4. 물리 재질과 렌더 재질은 다르다

렌더 재질은 색, roughness, metallic, transparency를 정한다. 물리 재질은 정지 마찰, 동마찰과 restitution을 정한다. 빨간 고무처럼 보인다고 자동으로 마찰이 높아지지 않는다.

GUI에서는 다음 순서로 만든다.

1. `Create > Physics > Physics Material > Rigid Body Material`을 선택한다.
2. `static friction`, `dynamic friction`, `restitution`을 조정한다.
3. collider prim을 선택한다.
4. Property의 Physics Material 영역에서 만든 재질을 할당한다.

Python에서는 다음처럼 적용한다.

```python
from isaacsim.core.api.materials import PhysicsMaterial

rubber = PhysicsMaterial(
    prim_path="/World/PhysicsMaterials/Rubber",
    static_friction=1.0,
    dynamic_friction=0.8,
    restitution=0.05,
)
dynamic_box.apply_physics_material(rubber)
static_platform.apply_physics_material(rubber)
```

정지 마찰은 미끄러지기 시작하는 임계에, 동마찰은 이미 미끄러지는 동안에 영향을 준다. restitution 0은 비탄성에 가깝고 1에 가까울수록 잘 튄다. 두 접촉 재질을 어떤 규칙으로 합치는지(combine mode)도 결과에 영향을 주므로 실측 튜닝에서는 함께 기록한다.

### 마찰 실험

경사로를 10°, 20°, 30°로 바꾸어 상자가 움직이기 시작하는 각도를 기록한다. 질량만 바꿨을 때 마찰 임계가 크게 달라진다면 collider, solver 또는 drive 간섭을 의심한다. 시뮬레이션 물성을 맞출 때는 눈대중 대신 실험 조건과 측정값을 표로 남긴다.

## 5. 조명

조명은 physics에 영향을 주지 않지만 카메라 센서 데이터의 분포를 바꾼다.

| 조명 | 용도 |
|---|---|
| Distant Light | 태양처럼 방향이 거의 일정한 광원 |
| Dome Light | 환경 전체의 배경·간접 조명, HDRI 기반 조명 |
| Sphere/Rect/Disk Light | 실내 전등과 면광원 |

```python
import omni.usd
from pxr import Gf, UsdLux

stage = omni.usd.get_context().get_stage()

sun = UsdLux.DistantLight.Define(stage, "/World/Lights/Sun")
sun.CreateIntensityAttr(1000.0)
sun.CreateColorAttr(Gf.Vec3f(1.0, 0.96, 0.9))
sun.CreateAngleAttr(0.5)

fill = UsdLux.SphereLight.Define(stage, "/World/Lights/Fill")
fill.CreateIntensityAttr(15000.0)
fill.CreateRadiusAttr(0.3)
UsdGeom.Xformable(fill.GetPrim()).AddTranslateOp().Set(Gf.Vec3d(1.0, -1.0, 2.0))
```

합성 데이터나 perception 평가에서는 exposure, 광원 위치, 색온도, 그림자와 재질을 실험 설정의 일부로 저장한다. Viewport가 밝다고 별도 render product의 노출도 같다고 가정하지 않는다.

## 6. 카메라 기초

Camera prim은 렌즈와 pose를 표현하고, 실제 영상은 camera에 연결된 **render product**에서 생성한다. `isaacsim.sensors.camera.Camera` wrapper는 render product 초기화와 RGB/depth/annotator 접근을 묶는다.

### GUI에서 확인

1. `Create > Camera`로 카메라를 만든다.
2. Stage에서 Camera를 선택해 frustum을 확인한다.
3. Viewport 위 카메라 아이콘에서 해당 Camera를 선택한다.
4. focal length와 aperture를 바꾸며 field of view 변화를 확인한다.

### Standalone 카메라 예제

```python
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import numpy as np
import isaacsim.core.utils.numpy.rotations as rot_utils

from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.sensors.camera import Camera

try:
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    world.scene.add(
        DynamicCuboid(
            prim_path="/World/Target",
            name="target",
            position=np.array([0.0, 0.0, 0.5]),
            size=0.5,
            color=np.array([0.9, 0.1, 0.1]),
        )
    )

    camera = Camera(
        prim_path="/World/Sensors/Camera",
        position=np.array([2.0, 0.0, 1.5]),
        orientation=rot_utils.euler_angles_to_quats(
            np.array([0.0, 55.0, 180.0]), degrees=True
        ),
        frequency=20,
        resolution=(640, 480),
    )

    world.reset()
    camera.initialize()

    # renderer와 annotator가 채워질 시간을 준다.
    for _ in range(30):
        world.step(render=True)

    rgba = camera.get_rgba()
    assert rgba is not None and rgba.shape[:2] == (480, 640), rgba.shape
    print("RGBA shape:", rgba.shape, "dtype:", rgba.dtype)
finally:
    simulation_app.close()
```

카메라 축 convention 때문에 목표가 보이지 않으면 임의 quaternion을 계속 바꾸기보다 GUI에서 카메라를 배치하고 pose를 읽거나 `set_world_pose`/look-at 유틸리티를 사용한다. ROS optical frame은 또 다른 축 convention을 사용하므로 ROS 변환 장에서 명시적으로 다룬다.

### 카메라 품질 체크리스트

- resolution과 frequency가 요구사항에 맞는가?
- clipping range가 장면 scale을 포함하는가?
- intrinsic matrix와 distortion model이 실제 센서 보정값과 맞는가?
- 첫 프레임이 비어 있을 수 있음을 처리했는가?
- RGB, depth, segmentation이 같은 timestamp/render product 기준인가?
- 5.1의 OpenCV pinhole/fisheye용 native lens distortion schema를 사용하고, 폐기 예정 polynomial 근사 API에 새 코드를 의존하지 않는가?

## 7. 접촉 센서

Contact Sensor는 부모 rigid body의 PhysX Contact Report를 읽고 threshold와 공간 영역으로 필터링한다. 구형 필터 영역은 “그 공간에서 새 충돌을 만드는 것”이 아니라 이미 부모 collider 표면에서 생긴 contact 가운데 센서에 포함할 것을 고른다.

### GUI 구성

1. collider가 적용된 rigid body prim을 선택한다.
2. `Create > Sensors > Contact Sensor`를 누른다.
3. sensor radius, min/max threshold와 sensor period를 설정한다.
4. Play한 뒤 Action Graph의 `Isaac Read Contact Sensor` 노드로 읽는다.

그래프는 `On Playback Tick → Isaac Read Contact Sensor → To String → Print Text`로 연결할 수 있다. 정확히 physics step마다 읽어야 하는 제어라면 `On Physics Step`을 사용하고 graph pipeline 설정을 확인한다.

### Python wrapper 예제

다음은 이미 `/World/Cube`에 collider가 있는 상태에서 실행하는 핵심 부분이다.

```python
import numpy as np
from isaacsim.sensors.physics import ContactSensor

contact = ContactSensor(
    prim_path="/World/Cube/Contact_Sensor",
    name="cube_contact",
    frequency=60,
    translation=np.array([0.0, 0.0, 0.0]),
    min_threshold=0.0,
    max_threshold=1.0e6,
    radius=-1.0,  # 부모 전체 접촉을 대상으로 한다.
)

# Play/reset 뒤 physics step을 진행한 다음 읽는다.
frame = contact.get_current_frame()
print("contact:", frame.get("in_contact"), "force:", frame.get("force"))
```

또는 저수준 interface를 사용한다.

```python
from isaacsim.sensors.physics import _sensor

interface = _sensor.acquire_contact_sensor_interface()
reading = interface.get_sensor_reading(
    "/World/Cube/Contact_Sensor", use_latest_data=True
)
if reading.is_valid:
    print(reading.time, reading.in_contact, reading.value)
```

sensor frequency는 physics frequency보다 높일 수 없다. `frequency`와 `dt`를 동시에 주지 않으며, `translation`과 `position`도 동시에 주지 않는다. Contact Sensor는 Play 시 동적으로 준비되므로 실행 중에 prim을 다른 rigid body 아래로 옮기면 무효화된다. 계층을 바꿀 때는 Stop한 뒤 수정하고 다시 시작한다.

## 8. 관절 힘, Effort와 IMU로 확장

접촉 외에도 물리 기반 센서를 사용할 수 있다.

- `get_applied_joint_efforts()`는 사용자가 명령한 effort를 읽는다.
- `get_measured_joint_efforts()`는 motion axis 방향의 측정 성분을 읽는다.
- `get_measured_joint_forces()`는 joint별 6D spatial force를 반환하며 fixed joint를 force/torque sensor처럼 활용할 수 있다.
- `isaacsim.sensors.physics.EffortSensor`는 joint effort의 sampling을 추상화한다.
- IMU는 linear acceleration과 angular velocity를 제공한다. 실제 센서와 비교하려면 bias, noise, bandwidth와 frame을 별도로 모델링한다.

명령 effort와 측정 force는 같은 값이 아니다. 중력, 접촉, 관성, constraint 반력이 측정 force에 함께 나타날 수 있다.

## 9. 안정성 진단 순서

물체가 폭발하거나 떨릴 때 solver iteration부터 크게 올리지 않는다.

1. stage 단위와 자산 크기를 확인한다.
2. collider가 겹친 초기 pose인지 visualization으로 확인한다.
3. 0 또는 극단적인 mass, 잘못된 inertia가 있는지 확인한다.
4. joint limit와 drive target이 충돌하지 않는지 확인한다.
5. contact/rest offset과 얇은 형상을 확인한다.
6. timestep을 줄여 현상이 사라지는지 비교한다.
7. CCD, solver iteration과 stabilization을 필요한 곳에만 적용한다.
8. Physics residual reporting과 Simulation Data Visualizer로 constraint 수렴을 관찰한다.

## 10. 검증 체크포인트

- [ ] rigid body와 collider의 역할을 각각 설명할 수 있다.
- [ ] 동적 mesh에 무조건 triangle mesh collider를 쓰지 않는 이유를 안다.
- [ ] 렌더 재질과 물리 재질을 별도로 설정했다.
- [ ] 카메라의 RGBA 배열 크기를 코드로 검증했다.
- [ ] 접촉 센서 부모에 collider가 있고 Play 뒤 유효한 값을 읽었다.
- [ ] sensor frequency가 physics frequency를 넘지 않도록 설정했다.

## 출처

- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Physics and PhysX Limitations](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/physics_resources.html)
- [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Simulation Data Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/ext_isaacsim_inspect_physics.html)
- [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [Camera Python API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.sensors.camera/docs/index.html)
- [Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)
- [Articulation Joint Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html)
- [Effort Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_effort.html)
- [IMU Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_imu.html)
