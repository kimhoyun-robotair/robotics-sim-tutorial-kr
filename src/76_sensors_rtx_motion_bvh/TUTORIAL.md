# 76. Motion BVH 설정은 언제 적용해야 할까요?

## 이번에 배우는 것

**같은 이동 표적을 두 번 실행하면서 Motion BVH만 켜고 끄고, 렌더러 설정과 Radar 반환에서 확인할 수 있는 범위를 구분합니다.**

움직이는 상자는 화면의 프레임 사이에서도 위치가 달라집니다. 센서가 노출이나 스캔 동안의 움직임을 다루려면 렌더러에도 시간에 따른 기하 정보가 필요합니다. Motion BVH는 광선과 물체의 교차를 빠르게 찾는 구조에 이런 움직임 정보를 포함하는 기능입니다.

| 비교 조건 | 기본 실행 | 비교 실행 |
|---|---|---|
| 옵션 | 생략 또는 `--motion-bvh` | `--no-motion-bvh` |
| 앱 시작 설정 | `enable_motion_bvh=True` | `enable_motion_bvh=False` |
| 표적 | `(8, 0, 1)` m에서 X 속도 -0.5 m/s | 동일 |
| 수집 | 반환 수, 마지막 유효 점군, 최종 위치 | 동일 |
| 확인할 한계 | Cartesian 점군만 기록 | Doppler 정확도까지 판정할 수 없음 |

## 1. Motion BVH를 켠 기준 결과 만들기

Isaac Sim 5.1.0, 지원 NVIDIA GPU와 RTX 렌더링 환경에서 실행합니다. 아래 명령은 저장소 루트 기준이며 설치 경로가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/76_sensors_rtx_motion_bvh/run.py --steps 240
```

240단계 뒤 이 폴더의 `output/날짜_시간/`에 `points.npy`, `measurements.json`, `scene.usda`를 저장합니다. 터미널의 `Output:` 경로를 기준 결과로 기록하세요. 기본값이 Motion BVH 활성화이므로 별도 켜기 옵션은 필요하지 않습니다.

GUI를 계속 관찰하려면 `--steps`를 생략합니다. 최초 수집 뒤에도 표적은 움직이지만 파일은 다시 쓰지 않습니다. `--headless`를 쓰면 창 없이 유한 실행하며, 단계 수 생략 시 240단계입니다.

### 코드에서 볼 부분

설정이 전달되는 위치가 중요합니다.

```python
parser.add_argument('--motion-bvh',
                    action=argparse.BooleanOptionalAction, default=True)
app = SimulationApp({'headless': args.headless,
                     'enable_motion_bvh': args.motion_bvh})
```

`BooleanOptionalAction`은 하나의 불리언 옵션에서 `--motion-bvh`와 `--no-motion-bvh`를 함께 제공합니다. 파싱된 값은 **앱 생성 시점**에 렌더러 설정으로 들어갑니다. 실행 중에 Python 변수만 바꾸고 이미 만들어진 렌더러가 바뀌었다고 생각하지 마세요. 이 실습은 설정별로 앱을 새로 시작합니다.

### 실행 결과 확인하기

`measurements.json`에서 `motion_bvh=true`, `target_speed_m_s=-0.5`를 확인합니다. `returns_per_frame`에 양수인 항목이 있는지 살펴보고 `points.npy`를 `np.load()`로 열어 비어 있지 않은 배열인지 확인하세요.

`target_final_position`의 X는 초기 8 m보다 작아지는 것이 예상됩니다. 다만 저장 점군은 **마지막으로 비어 있지 않았던 프레임**이고 위치는 수집 종료 때 읽습니다. 마지막 프레임이 비었다면 둘은 같은 시각의 관찰이 아닙니다.

또한 기본 Radar 점군의 기준은 `omni:sensor:WpmDmat:outputFrameOfReference=SENSOR`입니다. 점의 좌표는 m 단위이지만 월드 원점이 아니라 높이 1 m의 센서를 기준으로 합니다. 월드 좌표인 표적 위치와 비교할 때는 좌표 기준과 취득 시점을 모두 맞춰야 합니다.

## 2. 설정을 끈 결과와 비교하기

기준 실행을 종료한 뒤 다음을 실행합니다.

```bash
~/isaacsim/python.sh src/76_sensors_rtx_motion_bvh/run.py --steps 240 --no-motion-bvh
```

출력 자동 경로가 분리되므로 두 실행을 구별할 수 있습니다. 직접 경로를 지정하려면 아직 존재하지 않는 `--output` 경로를 사용하세요. 비교할 때 표적 속도와 단계 수는 바꾸지 않습니다.

### 코드에서 볼 부분

두 실행의 장면은 동일하게 구성됩니다.

```python
PhysxSchema.PhysxRigidBodyAPI.Apply(target.prim).CreateDisableGravityAttr(True)
world.reset()
target.set_linear_velocity(np.array([args.target_speed, 0., 0.]))
```

중력을 끈 것은 수평 이동을 유지하기 위해서입니다. Motion BVH를 껐다고 이 PhysX 속도 명령이 없어지는 것은 아닙니다. 따라서 BVH가 꺼진 화면에서도 표적이 움직일 수 있습니다.

### 실행 결과 확인하기

다음 순서로 비교하면 서로 다른 종류의 증거를 혼동하지 않을 수 있습니다.

1. JSON의 `motion_bvh`가 각각 `true`, `false`인지 확인합니다.
2. `target_speed_m_s`와 반환 이력 길이가 같은지 확인합니다.
3. 최종 물리 위치로 두 실행 모두 표적을 이동시켰는지 확인합니다.
4. 반환 수와 저장 점군을 비교하되, **점 수 차이만으로 Doppler가 맞거나 틀렸다고 판정하지 않습니다.**

BVH를 끈 실행은 Radar의 정상 설정으로 권하는 실행이 아니라 기능의 의존성을 살펴보는 비교 조건입니다. 모든 프레임이 비면 코드가 오류를 내며 점군 파일을 저장하지 않습니다. 이 경우도 반환 실패 조건으로 기록하고 성공한 출력처럼 다루지 마세요.

## 3. 물리 이동과 렌더러의 움직임 처리 정리

```text
PhysX 속도 명령 → 실제 Stage의 표적 이동
                         ↓
앱 시작의 Motion BVH 설정 → 렌더러가 움직임 정보를 다루는 방식
                         ↓
                   Radar 반환 배열
```

공식 5.1 문서는 Lidar의 motion compensation과 Radar의 Doppler 관련 계산에 Motion BVH가 필요하다고 설명합니다. 반면 이 로컬 코드의 annotator는 일반 Cartesian 점군을 저장합니다. **필요한 설정을 켰는지 확인하는 실습과, 그 물리 효과를 수치로 검증하는 실험은 범위가 다릅니다.**

또한 이 파일은 GPU 메모리나 안정 상태의 렌더 시간을 측정하지 않습니다. 두 앱의 전체 실행 시간을 시계로 재면 초기 자산 로딩과 shader 준비도 포함되므로 그 차이를 곧바로 Motion BVH 비용이라고 부르지 않습니다.

이미 GUI 중심의 장면을 사용하고 있다면 같은 기능을 앱 시작 인자로 켤 수도 있습니다.

```bash
~/isaacsim/isaac-sim.sh --/renderer/raytracingMotion/enabled=true --/renderer/raytracingMotion/enableHydraEngineMasking=true --/renderer/raytracingMotion/enabledForHydraEngines='0,1,2,3,4'
```

이 명령은 기능을 켠 GUI를 열며, 이번 표적이나 출력 파일을 자동으로 만들지는 않습니다. 위의 `run.py`는 `SimulationApp` 옵션으로 이 설정을 전달하는 독립 실행 방식입니다.

## 4. 간단한 확인 실험

이번에는 Motion BVH를 켠 상태에서 표적 속도만 0으로 바꿉니다.

```bash
~/isaacsim/python.sh src/76_sensors_rtx_motion_bvh/run.py --steps 240 --target-speed 0
```

1절의 기준 실행과 비교해 최종 X가 초기 위치에 머무는지 확인하세요. `motion_bvh`는 두 실행 모두 `true`여야 합니다. 이렇게 하면 “BVH를 끈 효과”와 “표적을 정지시킨 효과”를 별도로 관찰할 수 있습니다. 정지 표적에서도 점군이 나올 수 있으며, 반환의 존재 자체가 운동 측정값을 뜻하지는 않습니다.

## 실행할 때 막히면

- **설정을 바꿨는데 JSON 값이 같음**: 기존 파일을 보고 있지 않은지 `Output:` 경로부터 확인하세요. 끄기 옵션은 정확히 `--no-motion-bvh`입니다.
- **BVH를 껐는데 상자가 움직임**: 표적 이동은 PhysX가 진행합니다. 렌더러의 Motion BVH 설정과 이동 명령은 별개입니다.
- **`Radar produced no point cloud`**: RTX GPU, timeline, 표적의 시야 내 위치를 확인하고 기준인 BVH 켜기 실행부터 비교하세요.
- **실행 후반에 반환이 줄어듦**: 음의 X 속도로 계속 이동하면 표적이 센서를 지나갈 수 있습니다. 비교 구간을 동일한 240단계로 유지하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx.html)의 Motion BVH 설명에 대응합니다. 앱 시작 옵션을 실제 코드에 연결하고 동일한 Radar 장면으로 비교하도록 구성했습니다.

이번 문서 개정에서는 코드와 공식 설정을 대조했으며 BVH 켜기/끄기 GPU 실행은 수행하지 않았습니다. `tutorial.json`은 `not_run`입니다. Doppler 오차와 VRAM·성능 차이는 이 실습의 저장 파일만으로 검증되지 않습니다.
