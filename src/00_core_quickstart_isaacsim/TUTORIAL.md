# 00. Visual만 있는 큐브에 물리를 더하면 무엇이 달라질까요?

## 이번에 배우는 것

**같은 큐브에 강체와 충돌 속성을 차례로 추가하며, 화면에 보이는 모양과 물리 동작을 구분합니다.**

큐브가 화면에 나타났다고 중력이나 충돌이 자동으로 적용되지는 않습니다. 외형은 객체의 모양을 정하고, 강체는 중력에 따라 움직일 대상을 정하며, 충돌은 다른 물체와 접촉할 모양을 정합니다. 이 실습은 이 차이를 다섯 큐브로 보여줍니다.

| `run.py`의 Prim 경로 | 색·생성 방식 | 관찰할 동작 |
|---|---|---|
| `/World/Visual` | 노랑, `VisualCuboid` | 회전·스케일이 있어도 공중에 머뭅니다. |
| `/World/RigidOnly` | 빨강, 외형에 `RigidPrim` 추가 | 중력으로 떨어지지만 바닥을 통과합니다. |
| `/World/Converted` | 청록, 강체와 충돌을 순서대로 추가 | 떨어져 바닥에서 멈춥니다. |
| `/World/Dynamic` | 파랑, `DynamicCuboid` | 강체와 충돌을 한 번에 만들어 낙하하며 바닥에서 멈춥니다. |
| `/World/RawUsd` | 보라, `pxr.UsdGeom.Cube` | USD를 직접 작성한 외형이며 공중에 머뭅니다. |

Stage는 장면 전체이고, Prim은 `/World/Visual`처럼 경로로 찾는 장면 요소이자 객체 단위입니다. `VisualCuboid`와 `UsdGeom.Cube`는 접근 방식이 다르지만 둘 다 Stage에 큐브 Prim을 작성합니다.

## 1. 다섯 큐브를 한 번에 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU·드라이버를 준비하세요. 큐브와 지면은 코드로 만들므로 외부 로봇 자산은 필요하지 않습니다. 아래는 저장소 루트에서 실행하는 Linux 명령입니다.

```bash
~/isaacsim/python.sh src/00_core_quickstart_isaacsim/run.py --steps 240
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. Windows에서는 설치의 `python.bat`을 사용합니다. 240 step이 끝나면 앱이 종료됩니다. 창을 계속 보려면 `--steps 240`을 빼고, 창 없이 실행하려면 `--headless`를 추가하세요. Headless에서는 Default Step이 240으로 지정되어 있습니다.

### 코드에서 볼 부분

먼저 `SimulationApp`으로 앱을 시작한 뒤 `omni`, `pxr`, Core API를 가져옵니다. 이 모듈들은 실행 중인 앱의 확장을 사용합니다. `World`는 길이를 미터로, 물리 간격을 1/60초로 설정합니다.

청록 큐브를 만드는 부분은 외형과 두 물리 기능을 분리해 보여줍니다.

```python
converted = world.scene.add(
    RigidPrim("/World/Converted", name="converted", masses=np.array([1.0]))
)
GeometryPrim("/World/Converted").apply_collision_apis()
```

이 앞에서 같은 경로에 `VisualCuboid`를 생성했습니다. `RigidPrim`이 새 큐브를 하나 더 만드는 것이 아니라, 이미 있는 큐브에 강체 기능을 추가합니다. 질량 배열의 `1.0`은 kg 단위이며, 충돌 기능은 그 아래 줄에서 별도로 붙입니다. 빨간 큐브에는 마지막 줄에 해당하는 처리가 없습니다.

노란 큐브의 `visual`과 `core_transform`도 같은 `/World/Visual`에 접근하는 두 Python 변수입니다. `XFormPrim.set_world_poses()`는 위치와 `[w, x, y, z]` 쿼터니언을 받고, `set_local_scales()`는 축별 배율을 받습니다. 코드의 `euler_angles_to_quat()`는 Z축 `π/4` 라디안 회전을 쿼터니언으로 바꿉니다.

보라 큐브에는 USD 변환 연산을 직접 작성합니다.

```python
raw.AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 1.0))
raw.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, 45.0))
raw.AddScaleOp().Set(Gf.Vec3f(1.0, 1.5, 0.5))
```

여기의 `RotateXYZ`는 **도 단위**입니다. 앞의 `π/4` 라디안과 이곳의 45도는 같은 회전입니다. 스케일 `[1, 1.5, 0.5]`는 y 길이를 1.5배, z 길이를 절반으로 만듭니다. 회전이나 크기를 바꾸는 작업만으로 중력과 물리 모델이 적용되지는 않습니다.

### 실행 결과 확인하기

기본 중심 높이는 1.5 m입니다. 빨간 큐브가 바닥 아래로 사라지는 것이 정상적인 동작입니다. 종료 후 이 폴더의 `output/날짜-시간/`을 열어 보세요.

| 파일·열 | 읽는 방법 |
|---|---|
| `initial_scene.usda` | `world.reset()`과 낙하 전에 저장한 장면입니다. GUI에서 열면 초기 설정을 조사할 수 있습니다. |
| `heights.csv`의 `visual_z_m` | 기본값 1.5 m를 유지하는지 확인합니다. |
| `rigid_only_z_m` | 계속 감소해 음수가 되는지 확인합니다. |
| `converted_z_m`, `dynamic_z_m` | 충분히 실행하면 약 0.15 m로 정착하는지 확인합니다. |
| `step`, `time_s` | 240단계 완료 시 마지막 행은 240과 4.0초입니다. |

청록·파랑 큐브의 한 변은 0.3 m라서 바닥 위 중심은 약 0.15 m입니다. `RawUsd`의 높이는 CSV에 기록하지 않으며, 시작 위치도 고정된 Z=1 m입니다. `--height`가 모든 도형의 높이를 바꾸는 것은 아닙니다.

## 2. GUI와 Script Editor에서 속성 추가하기

독립 실행을 종료한 뒤 `~/isaacsim/isaac-sim.sh`로 새 창을 여세요. 다음 두 방법은 각각 **File > New**로 빈 장면을 준비하고 시작합니다.

### GUI에서 볼 부분

1. **Create > Physics > Ground Plane**, **Create > Lights > Distant Light**를 추가합니다. 광원 Intensity를 1000으로 지정하세요.
2. **Create > Shape > Cube**로 큐브를 만듭니다. Property에서 중심 Z=1.5, 실제 한 변=0.3 m가 되도록 Size와 Scale을 맞춥니다. Size가 2라면 각 Scale은 0.15입니다.
3. **Play**를 눌러 공중에 머무는지 보고 **Stop**을 누릅니다.
4. 큐브를 선택해 Property의 **Add > Physics > Rigid Body with Colliders Preset**을 적용합니다. 다시 Play하면 낙하해 바닥과 접촉하는지 확인하세요.
5. Stop 후 `W` 이동, `E` 회전, `R` 스케일 도구를 사용해 보세요. 이동·회전 아이콘을 길게 누르면 Local/World 좌표 기준을 비교할 수 있습니다. 정확한 값은 Property에 입력하고 파란 초기화 버튼으로 복원합니다. `Esc`는 선택 해제입니다.
6. 장면을 남기려면 **File > Save As**로 새 USD 이름을 지정합니다.

### Script Editor 코드에서 볼 부분

빈 장면에서 **Window > Script Editor**를 열고 이 폴더의 `script_editor.py` 전체를 실행합니다. 이 파일은 `/World/Quickstart` 아래에 네 큐브를 만들며, 독립 실행의 별도 빨간 큐브는 포함하지 않습니다. **Run**으로 장면을 작성한 다음 **Play**로 물리를 진행하세요.

처음에는 청록·파랑만 떨어집니다. Stop 후 새 탭에서 노란 큐브에 강체만 추가해 보세요.

```python
from isaacsim.core.prims import RigidPrim
RigidPrim("/World/Quickstart/Visual")
```

Play하면 노란 큐브도 떨어지지만 지면을 통과합니다. 다시 Stop하고, 필요하면 Property에서 중심 Z를 1.5로 복원한 뒤 충돌을 추가합니다.

```python
from isaacsim.core.prims import GeometryPrim
GeometryPrim("/World/Quickstart/Visual").apply_collision_apis()
```

### 실행 결과 확인하기

이제 Play하면 노란 큐브가 지면에서 멈추는지 확인하세요. **강체 추가 전 → 강체만 추가 → 충돌까지 추가**의 세 상태를 같은 큐브에서 비교한 것입니다. Script Editor는 CSV를 저장하지 않으므로 화면과 Property가 관찰 대상입니다. 이 파일의 RawUsd 큐브에는 별도 보라색 설정이 없으므로 경로로 구분하세요.

## 3. 외형·물리·실행 방식 정리

```text
외형만 작성 → 보이지만 중력으로 움직이지 않음
외형 + 강체 → 중력으로 움직임
외형 + 강체 + 충돌 → 중력으로 움직이고 바닥과 접촉
```

GUI의 Preset과 Python의 `DynamicCuboid`는 강체·충돌을 함께 준비하는 편리한 방법입니다. 속성을 나눠 추가하면 바닥을 통과하는 이유도 설명할 수 있습니다. 물리 진행은 독립 실행에서 `world.step()`이, Script Editor 실습에서는 앱의 Play가 맡습니다.

## 4. 간단한 확인 실험

독립 실행의 시작 높이만 1.5에서 2.0 m로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/00_core_quickstart_isaacsim/run.py --steps 240 --height 2.0
```

`visual_z_m`은 2.0 m를 유지하고, 청록·파랑은 낙하 시간이 길어져도 최종 중심 높이는 약 0.15 m입니다. 첫 실행과 CSV의 중간 행을 비교하면 낙하 과정의 차이가 보입니다. RawUsd는 여전히 Z=1 m에 있습니다.

## 실행할 때 막히면

- **빨간 큐브만 사라짐**: 충돌이 없는 강체의 예상 결과입니다. `rigid_only_z_m`으로 계속 낙하하는지 확인하세요.
- **Script Editor에 `already exists` 오류**: 같은 장면에 예제가 남아 있습니다. File > New 후 파일 전체를 다시 실행하세요.
- **Run 후 큐브가 움직이지 않음**: Script Editor는 장면을 작성합니다. 물리 관찰에는 Play가 필요합니다.
- **출력 경로 오류**: `--output`으로 지정한 폴더는 새 경로여야 합니다. 생략하면 실행별 폴더를 만듭니다.
- **모듈 import 실패**: 설치의 `python.sh`를 사용하고 `SimulationApp`보다 앞에 `omni`·`pxr` import를 옮기지 마세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Isaac Sim Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)에 대응합니다. GUI의 생성·변환·물리 속성 추가를 Python과 비교하도록 구성했습니다. 실행 방식의 배경은 [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)를 참고하세요.

다섯개의 큐브 비교와 CSV는 이 폴더의 실습 구성입니다. 변환 API는 제공 코드의 `XFormPrim`, `set_local_scales`, 단위 쿼터니언 표현을 기준으로 읽으세요. `tutorial.json`의 실행 상태는 `not_run`이며, 위 값은 실행 시 확인할 기준입니다.
