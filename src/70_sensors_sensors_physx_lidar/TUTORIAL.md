# 70. 화면에는 보이는데 Lidar에는 안 보이는 물체

## 이번에 배우는 것

**두 상자를 PhysX Lidar로 스캔하고, 충돌 설정을 껐을 때 영상과 거리 측정이 어떻게 달라지는지 확인합니다.**

화면에 물체가 보인다고 모든 센서가 그 물체를 읽는 것은 아닙니다. PhysX Lidar는 광선과 충돌 형상의 교차를 계산합니다. 이번에는 상자의 외형을 유지한 채 collider만 끄는 실험으로, 측정 대상이 무엇인지 분명하게 확인합니다.

| 구성 | 기본 설정 | 역할 |
|---|---|---|
| `/World/Lidar` | `(0,0,1)` m | 거리 측정 원점 |
| `/World/Target0` | `(4,-2,1)` m, 한 변 1 m | y가 음수인 쪽의 첫 대상 |
| `/World/Target1` | `(4,2,1)` m, 한 변 1 m | y가 양수인 쪽의 둘째 대상 |
| 스캔 범위 | 수평 360°, 수직 30° | 광선을 보낼 각도 범위 |
| 각도 간격 | 수평 1°, 수직 2° | 광선 배치의 촘촘함 |
| 거리 범위 | 0.1~20 m | 측정할 최소·최대 거리 |

두 상자에는 `target_0`, `target_1`이라는 class 라벨도 붙입니다. 거리만 읽는 데서 한 걸음 더 나아가 어떤 prim을 맞혔는지 연결해 보겠습니다.

## 1. 두 상자의 거리와 경로 저장하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/70_sensors_sensors_physx_lidar/run.py --steps 240 --output src/70_sensors_sensors_physx_lidar/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 기본 `rotation_rate=0`은 설정된 시야 안의 모든 방향으로 광선을 쏘는 방식입니다. 센서가 작동하지 않는다는 뜻이 아닙니다. 240단계 후 마지막 스캔 버퍼를 저장하고 종료합니다.

출력 폴더는 아직 없는 경로를 사용합니다. 생략하면 이 튜토리얼의 `output/날짜_시간/`에 만듭니다. `--headless`를 추가하면 창 없이 실행할 수 있습니다. `--steps 240`을 빼면 처음 파일을 저장한 뒤 재생을 재개하고 GUI를 계속 열어 두지만 파일은 추가하지 않습니다.

### 실행 결과 확인하기

| 파일 또는 배열 | 확인할 내용 |
|---|---|
| `lidar.npz`의 `depth` | 마지막 거리 버퍼; 단위 m |
| `points` | 센서 원점을 기준으로 한 hit의 상대 xyz, 이 장면에서는 m |
| `azimuth`, `zenith` | 각각 열과 행에 대응하는 광선 각도, rad |
| `hit_prims.json` | 광선이 맞힌 prim 경로 데이터 |
| `scene.usda` | 상자·라벨·센서 설정을 저장한 장면 |

콘솔의 `returns_below_max_range`는 `depth < 20`인 값의 개수입니다. 먼저 최대거리 미만의 반환이 있는지 보고, `hit_prims.json`에서 `/World/Target0`과 `/World/Target1`에 해당하는 경로가 나오는지 확인하세요. 배열의 빈 경로나 최대거리 값까지 물체 검출로 세지 않습니다.

상자 중심은 센서에서 약 `sqrt(4²+2²) = 4.47 m` 떨어져 있지만 Lidar는 **중심이 아니라 앞쪽 표면**을 맞힙니다. 따라서 상자 반환이 모두 4.47 m여야 한다는 기준은 맞지 않습니다. 광선 방향에 따라 맞는 표면 위치도 달라집니다.

## 2. 충돌 형상과 의미 라벨 연결하기

### 코드에서 볼 부분

상자는 `FixedCuboid`로 만들어 움직이지 않는 collider를 갖습니다. 라벨을 붙인 뒤 실험 옵션에 따라 충돌만 끕니다.

```python
sem = Semantics.SemanticsAPI.Apply(cube.prim, 'Semantics')
sem.CreateSemanticTypeAttr('class')
sem.CreateSemanticDataAttr(f'target_{i}')
if args.no_colliders:
    UsdPhysics.CollisionAPI(cube.prim).GetCollisionEnabledAttr().Set(False)
```

라벨은 “이 대상이 무엇인가”를 설명하는 데이터이고 collider는 “광선이 맞는 표면이 있는가”를 결정합니다. class 문자열이 있어도 collider가 꺼지면 이 PhysX 센서는 상자를 맞히지 못합니다. 위 코드는 시각적 mesh를 삭제하거나 숨기지는 않습니다.

센서 생성에서 눈여겨볼 값은 다음과 같습니다.

```python
success, sensor = omni.kit.commands.execute(
    'RangeSensorCreateLidar', path='/World/Lidar',
    translation=Gf.Vec3d(0,0,1), min_range=.1, max_range=20,
    horizontal_fov=360, vertical_fov=30,
    horizontal_resolution=1, vertical_resolution=2,
    rotation_rate=args.rotation_rate,
    draw_lines=True, high_lod=True, enable_semantics=True,
)
```

FOV는 전체 시야, resolution은 여기서 각도 간격이며 단위는 도입니다. 숫자가 작을수록 각도 사이를 더 촘촘하게 샘플링합니다. `draw_lines=True`는 광선을 화면에 그리게 하고 `enable_semantics=True`는 맞힌 대상 정보를 읽는 흐름에 사용합니다.

생성할 때의 degree 단위와 읽은 `azimuth`·`zenith`의 rad 단위는 다릅니다. 예를 들어 90°는 읽기 배열에서 약 π/2 rad에 해당합니다. `points`도 월드 좌표라고 가정하지 말고 센서 원점과 장면 변환을 함께 확인하세요.

```python
depth = np.asarray(interface.get_linear_depth_data(path))
points = np.asarray(interface.get_point_cloud_data(path))
prims = interface.get_prim_data(path)
```

거리·점군·대상 경로는 같은 센서 경로에서 읽습니다. `get_prim_data()` 결과를 임의의 정수 class ID로 해석하지 마세요. 저장된 경로를 Stage의 prim과 연결한 뒤 그 prim의 class 라벨을 확인합니다.

### 회전 설정에서 볼 부분

`--rotation-rate 1`은 초당 한 바퀴의 회전 스캔입니다. 기본 0과 달리 한 순간에 일부 방향을 훑으므로, 짧은 구간의 마지막 버퍼에 두 상자가 모두 들어 있을 것을 전제하면 안 됩니다. 비교할 때는 회전율뿐 아니라 관찰 시간과 저장된 버퍼 범위도 함께 기록해야 합니다.

### 부모에 센서를 붙여 보기

장면에 고정한 센서를 로봇에 붙일 때는 부모 기준 transform을 이해해야 합니다. 1절 실행을 종료한 뒤 새 Isaac Sim 창에서 저장된 `output/base/scene.usda`를 열어 다음 GUI 비교를 진행하세요. 이 경로는 해당 튜토리얼 폴더 기준입니다.

1. Pause한 뒤 `/World/SensorMount`라는 Xform을 만들고 `/World/Lidar`를 그 아래로 옮깁니다.
2. Lidar의 local translate를 `(0.5, 0.5, 0)`으로 설정하세요. 부모를 움직였을 때 이 상대 배치를 유지하는지 살펴봅니다.
3. Play하고 부모 위치를 바꾸며 상자를 맞히는 광선 방향과 거리가 달라지는지 확인하세요. Python 읽기를 새 장면에 적용한다면 센서 경로도 `/World/SensorMount/Lidar`로 맞춰야 합니다. 이 편집은 화면에서 transform을 관찰하는 비교이며 기존 NPZ는 갱신되지 않습니다.

새 센서는 **Create > Sensors > PhysX Lidar > Rotating**으로 만들 수 있으며 Physics Scene과 대상 collider가 필요합니다. 이동 로봇에 붙이는 원문 실습은 별도 새 stage에서 5.1 Assets의 `Isaac/Robots/NVIDIA/Carter/carter_v1.usd`를 직접 열어 진행합니다. Lidar를 `/carter/chassis_link` 아래에 놓고 local translate `(-0.06, 0, 0.38)`, drawLines=True, rotationRate=0으로 맞추세요. `chassis_link/left_wheel`과 `right_wheel` drive의 Target Velocity를 각각 100으로 설정한 뒤 Play하면 부모와 센서가 함께 이동하는지 볼 수 있습니다. 이 추가 실습에는 Carter 자산이 필요하며 기본 두 상자 실습에는 필요하지 않습니다. [공식 부착 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lidar.html#attach-a-lidar-to-a-moving-robot)를 참고하세요.

## 3. 외형과 충돌체의 역할 정리

```text
시각 mesh + 재질 → 화면에서 보이는 상자
collider + 광선 방향 → PhysX Lidar의 표면 교차와 거리
맞힌 prim 경로 + class 라벨 → 반환이 어느 대상인지 해석
```

PhysX Lidar는 충돌 형상으로 기하학적 거리를 읽습니다. 렌더링상 투명한 물체라도 collider가 있으면 검출할 수 있습니다. 이 실습의 거리에서 재질에 따른 투과나 반사 강도까지 추론하지 마세요. 여기서 검증할 관계는 **충돌체의 존재와 거리 반환의 관계**입니다.

## 4. 간단한 확인 실험

상자 두 개의 collider만 끄세요.

```bash
~/isaacsim/python.sh src/70_sensors_sensors_physx_lidar/run.py --steps 240 --no-colliders --output src/70_sensors_sensors_physx_lidar/output/no-colliders
```

화면에는 같은 위치의 두 상자가 남아 있어야 합니다. 반면 `hit_prims.json`에서 두 상자 경로의 반환이 사라지고 해당 방향에 유효한 표면 거리가 없어지는지 확인하세요. 센서 버퍼 자체는 계속 존재할 수 있으므로 **파일이 생겼는지가 아니라 두 대상의 hit가 바뀌었는지** 비교합니다.

## 실행할 때 막히면

- **`No PhysX lidar depth buffer`**: `isaacsim.sensors.physx` 확장과 물리 재생, 충분한 단계 수를 확인하세요.
- **상자는 보이는데 hit가 없음**: `--no-colliders` 사용 여부와 두 상자의 Collision Enabled를 확인하세요. 시각적 외형만으로 검출을 판단하지 않습니다.
- **rotation rate가 0이라 센서가 멈춘 것 같음**: 0은 전 방향 동시 스캔입니다. 그려진 광선과 저장 거리로 동작을 확인하세요.
- **회전 모드에서 한 대상만 보임**: 마지막 버퍼가 포함하는 방향과 회전 시간을 확인하세요. 결과는 전 실행의 누적 점군이 아닙니다.
- **점군을 다른 장면에 겹치니 위치가 어긋남**: 센서의 위치·회전과 데이터 좌표계를 함께 확인하세요. 센서 원점의 `(0,0,1)` m 이동을 월드 원점과 혼동하지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [PhysX SDK Lidar](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physx_lidar.html)에 대응합니다. 공식 거리·대상 정보 읽기를 두 개의 로컬 상자와 collider 비교 옵션으로 구성했습니다.

이번 개정에서는 센서 설정·라벨·저장 범위와 공식 충돌 조건을 대조했습니다. 실제 점군 생성이나 collider 비교를 실행하지 않았으며 `tutorial.json`은 `not_run`입니다. 코드의 자동 오류 검사는 빈 거리 버퍼를 확인하므로, 두 대상 검출은 출력 파일에서 별도로 확인해야 합니다.
