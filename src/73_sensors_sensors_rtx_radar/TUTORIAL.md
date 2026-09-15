# 73. 움직이는 표적을 RTX Radar로 읽기

## 이번에 배우는 것

**센서 쪽으로 이동하는 상자를 Radar로 관찰하고, 물리 엔진의 표적 위치와 센서가 반환한 점군을 구분해 읽습니다.**

물체의 위치를 코드로 안다고 해서 Radar가 그 물체를 관측했다고 할 수는 없습니다. 이 실습은 물리 엔진에서 상자를 움직이고, 별도의 RTX 센서 경로에서 실제 반환이 생기는지 확인합니다. 두 결과를 함께 저장하면 장면의 움직임과 센서 데이터가 연결되는 지점을 살펴볼 수 있습니다.

| 항목 | 설정 또는 파일 | 의미 |
|---|---|---|
| 표적 | `/World/Target`, 시작 위치 `(8, 0, 1)` m | 센서 앞의 가로로 넓은 상자 |
| 이동 | X 방향 기본 속도 `-0.5` m/s, 중력 해제 | 센서 쪽으로 수평 접근 |
| Radar | `/World/Radar`, 위치 `(0, 0, 1)` m | 움직이는 표적을 관찰하는 센서 |
| `points.npy` | 마지막 비어 있지 않은 점군 | 센서가 받은 Cartesian 반환 |
| `measurements.json` | 반환 수와 최종 표적 위치 | 수집 이력과 물리 상태 |

## 1. Radar와 표적을 실행하기

Isaac Sim 5.1.0, 지원 NVIDIA GPU와 RTX 렌더링 환경이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/73_sensors_sensors_rtx_radar/run.py --steps 240
```

설치 경로가 다르면 `~/isaacsim`을 바꾸세요. 240단계 뒤 파일을 저장하고 앱이 종료됩니다. `--headless`를 추가해도 센서용 렌더링은 수행합니다. 결과 경로는 터미널의 `Output:`에 표시되고, 기본 위치는 이 폴더의 `output/날짜_시간/`입니다.

움직임을 더 보고 싶으면 `--steps 240`을 생략합니다. 처음 240단계의 결과를 저장한 뒤에도 상자가 계속 이동합니다. **저장된 위치와 열린 화면의 현재 위치는 이후 서로 달라질 수 있습니다.** 파일은 계속 덧붙여 기록하지 않습니다.

### 코드에서 볼 부분

표적은 `DynamicCuboid`로 만들지만 중력을 끕니다. 낙하와 수평 접근을 한꺼번에 관찰하지 않도록 조건을 단순하게 만든 것입니다.

```python
PhysxSchema.PhysxRigidBodyAPI.Apply(target.prim).CreateDisableGravityAttr(True)
world.reset()
target.set_linear_velocity(np.array([args.target_speed, 0., 0.]))
```

속도는 초기화 뒤에 적용합니다. 벡터의 첫 성분이 X축 속도이며, 음수이므로 X=8에서 원점 쪽으로 이동합니다. `target_final_position`은 수집이 끝난 뒤 `target.get_world_pose()`로 읽은 값입니다. 이것은 Radar가 추정한 위치가 아니라 물리 장면의 상태입니다.

## 2. Radar 출력을 배열로 가져오기

72번의 `LidarRtx`와 달리 이 파일은 센서 생성, 렌더 대상 생성, annotator 연결을 직접 작성합니다.

### 코드에서 볼 부분

먼저 코드가 만드는 센서의 경로와 자세를 확인하세요.

```python
success, sensor = omni.kit.commands.execute(
    'IsaacSensorCreateRtxRadar', path='/World/Radar',
    translation=Gf.Vec3d(0, 0, 1),
    orientation=Gf.Quatd(1, 0, 0, 0), force_camera_prim=False,
)
```

회전은 `(w, x, y, z)` 순서의 항등 쿼터니언입니다. `force_camera_prim=False`로 생성한 결과는 `OmniRadar`이고 `OmniSensorGenericRadarWpmDmatAPI`가 적용됩니다. 이 센서가 만들어진 뒤 다음 렌더 연결을 추가합니다.

```python
product = rep.create.render_product(sensor.GetPath(), (1, 1))
annotator = rep.AnnotatorRegistry.get_annotator(
    'IsaacExtractRTXSensorPointCloudNoAccumulator'
)
annotator.attach([product.path])
```

`render product`는 이 센서를 렌더러가 처리할 대상으로 연결합니다. 여기의 `(1, 1)`은 RGB 영상 픽셀 하나가 Radar 측정점 하나라는 뜻이 아닙니다. 점군의 크기는 Radar가 계산한 반환 수로 결정됩니다. 이 연결에서 데이터를 배열로 읽어 주는 부분이 annotator입니다.

반복문은 매번 `world.step(render=True)` 뒤 `annotator.get_data()`를 읽습니다. 다음 부분이 저장 시점을 이해하는 핵심입니다.

```python
counts.append(int(len(points)))
if points.size:
    last_nonempty = points.copy()
```

빈 프레임은 반환 수 0으로 기록하되, 앞서 받은 유효 점군을 지우지 않습니다. `copy()`는 이후 센서 갱신과 별개로 그 배열을 보관하기 위한 복사입니다. 수집 구간 내내 반환이 없으면 `last_nonempty`가 만들어지지 않아 오류로 종료합니다.

### 실행 결과 확인하기

| 결과 | 확인할 내용 | 해석할 때 주의할 점 |
|---|---|---|
| `returns_per_frame` | 240개 항목 중 양수가 있는지 | 마지막 값이 0이어도 이전 점군을 저장할 수 있습니다. |
| `target_final_position` | X가 시작값 8보다 작아졌는지 | 센서 측정이 아닌 물리 상태입니다. |
| `target_speed_m_s` | 기본 `-0.5` | 입력한 속도이며 측정된 Doppler 값이 아닙니다. |
| `motion_bvh` | `true` | 앱을 시작할 때 활성화한 설정입니다. |
| `points.npy` | 비어 있지 않은 점 배열 | 마지막 유효 프레임이며 최종 표적 위치와 취득 시각이 다를 수 있습니다. |

`scene.usda`도 함께 내보냅니다. 점군을 뷰포트에 그리는 코드는 없으므로, 점 표시가 없을 때는 먼저 출력 배열을 확인하세요. `points.npy`는 NumPy의 `np.load()`로 열 수 있습니다.

점군은 m 단위의 좌표입니다. 이 기본 Radar의 `omni:sensor:WpmDmat:outputFrameOfReference`는 `SENSOR`이므로 센서 위치가 원점입니다. 반면 `target_final_position`은 월드 좌표입니다. 센서가 높이 1 m에 있으므로 Z값을 그대로 비교하지 말고, 센서 자세에 따른 좌표 변환과 취득 시점 차이를 함께 고려하세요. Lidar의 같은 목적 속성과 달리 Radar에서는 `WpmDmat` 이름을 사용합니다.

## 3. 움직임과 측정값의 관계 정리

```text
설정한 X 속도 → PhysX가 표적을 이동 → 마지막 물리 위치 저장
                           ↓ RTX 렌더링
                    Radar 반환 → 프레임별 점 수와 유효 점군 저장
```

240단계의 물리 시간은 설정상 4초입니다. 등속 운동만 생각하면 X 변화량은 `-0.5 × 4 = -2 m`이므로 최종 X는 약 6 m가 예상됩니다. 실제 값은 초기화와 물리 접촉 등의 영향을 받을 수 있으므로 JSON에서 확인하세요.

앱은 `enable_motion_bvh=True`로 시작합니다. Motion BVH는 렌더러가 시간에 따른 기하 변화도 다루게 하는 구조이며 Radar의 움직임 관련 계산에 필요합니다. 그러나 이 실습이 저장하는 일반 점군에는 검증된 Doppler 속도 필드가 없습니다. **점이 나왔다는 결과와 속도를 정확히 측정했다는 결론은 구별해야 합니다.**

## 4. 간단한 확인 실험

표적 속도만 0으로 바꾸어 실행해 보세요.

```bash
~/isaacsim/python.sh src/73_sensors_sensors_rtx_radar/run.py --steps 240 --target-speed 0
```

기본 실행과 최종 X, 프레임별 반환 수, 저장 점군을 비교합니다. 정지 실행에서는 X가 초기 8 m 부근에 머무는지 확인하세요. 두 실행에 모두 점이 있어도 파일에 속도 추정값이 없으므로 Doppler 성능 비교로 해석하지 않습니다. 이 실험이 알려 주는 것은 표적의 이동 조건과 반환의 존재·분포가 어떻게 연결되는지입니다.

## 실행할 때 막히면

- **`RTX radar creation failed`**: `isaacsim.sensors.rtx`를 사용할 수 있는 5.1 설치인지 확인하세요. 이 파일은 일반 Python이나 Script Editor 전체 붙여넣기용이 아닙니다.
- **`Radar produced no point cloud`**: RTX GPU와 timeline 재생, 표적의 시야 내 위치를 확인하세요. 매우 짧은 실행은 렌더 준비만 진행할 수 있습니다.
- **오래 실행할수록 표적이 사라짐**: 표적은 계속 X 방향으로 이동합니다. 센서를 지나갈 만큼 오래 실행한 장면과 처음 240단계의 저장 구간을 구분하세요.
- **출력 폴더 충돌**: 직접 `--output`을 지정했다면 아직 없는 경로를 쓰세요. 기본 자동 경로는 실행마다 분리됩니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Radar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_radar.html)에 대응합니다. `OmniRadar`와 render product 연결에 로컬 이동 표적과 NumPy 저장을 더했습니다. Radar 원시 버퍼의 Doppler 해석과 실측 센서 성능 평가는 포함하지 않습니다.

이번 개정은 코드와 공식 자료의 대조이며 Radar GPU 실행은 수행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다. 본문의 값은 실행 후 확인할 기준입니다.
