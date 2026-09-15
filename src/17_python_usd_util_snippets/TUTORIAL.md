# 17. 같은 점들을 세 방식으로 그리고 저장 결과 비교하기

## 이번에 배우는 것

**같은 위치 데이터를 Points·PointInstancer·DebugDraw로 표현하고, 어떤 표현이 USD 파일에 남는지 확인합니다.**

점처럼 보이는 물체라고 해서 모두 같은 데이터는 아닙니다. 렌더러가 읽는 USD 점을 만들 수도 있고, 작은 큐브를 여러 곳에 배치할 수도 있으며, 뷰포트에 진단용 점만 그릴 수도 있습니다. 이번에는 난수 시드를 고정해 같은 위치 목록을 세 방식으로 그립니다.

| `--mode` | 화면에 그리는 것 | `geometry.usda`에 남는 것 |
|---|---|---|
| `points` | 자홍색 USD Points | 점 위치·너비·색 |
| `instancer` | 청록색 작은 큐브들 | 원형 큐브와 인스턴스 위치 |
| `debug` | 주황색 진단용 점 | DebugDraw 점 자체는 저장되지 않음 |

점의 높이는 사인 함수로 직접 바꿉니다. 중력이나 충돌 때문에 움직이는 장면이 아니므로 물리 시간 대신 **앱 업데이트 인덱스**가 애니메이션의 입력입니다.

## 1. 먼저 Points로 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 있는 환경에서 저장소 루트 기준으로 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/17_python_usd_util_snippets/run.py --mode points --count 200 --steps 120
```

점 200개의 위치를 120회 갱신한 뒤 마지막 위치와 USD를 저장하고 종료합니다. 창을 계속 보려면 `--steps 120`을 빼세요. 첫 120회의 결과를 저장한 뒤에도 애니메이션은 이어지지만 저장 파일은 더 갱신하지 않습니다.

Points와 Instancer는 `--headless`도 사용할 수 있으며, 단계 수 생략 시 120회 후 종료합니다. DebugDraw는 보이는 뷰포트가 필요하므로 `--headless`와 함께 사용할 수 없습니다.

출력은 이 폴더의 `output/날짜-시간/`에 생깁니다. `--output`을 사용할 때는 새 폴더를 지정하세요.

### 코드에서 볼 부분

위치는 난수 시드 7로 만들고 각 업데이트에서 다음 높이를 사용합니다.

```python
samples = [
    Gf.Vec3f(x, y, z + 0.2 * math.sin(frame / 15 + x))
    for x, y, z in base
]
positions.Set(samples)
app.update()
```

`base`는 움직이기 전 위치 목록입니다. X와 Y는 유지하고 Z에 최대 ±0.2 m 변화를 더합니다. `+ x` 때문에 X 위치에 따라 위아래 움직임의 위상이 달라집니다. 매번 이전 높이에 더하는 것이 아니라 **같은 기준 높이에서 다시 계산**하므로 오차가 누적되는 구조가 아닙니다.

`frame`은 0부터 시작합니다. `--steps 120`의 저장 위치는 마지막 `frame=119`로 계산한 결과입니다. `frame / 15`는 애니메이션 위상을 정하는 식이며 시뮬레이션 시간(초)이라는 뜻은 아닙니다.

### 실행 결과 확인하기

`rendering.json`에서 `mode=points`, `point_count=200`인지 확인하세요. `final_positions`에도 200개의 `[x, y, z]`가 있어야 합니다.

저장한 `geometry.usda`를 새 GUI에서 열면 점의 마지막 배치가 보입니다. 이 코드는 위치를 기본 속성 값으로 갱신하므로, 저장된 파일은 120프레임 애니메이션 전체가 아닌 **마지막 배치의 스냅샷**입니다.

## 2. Instancer·DebugDraw와 카메라 계산 살펴보기

앞의 실행이 끝난 뒤 같은 개수와 길이로 차례로 실행합니다.

```bash
~/isaacsim/python.sh src/17_python_usd_util_snippets/run.py --mode instancer --count 200 --steps 120
~/isaacsim/python.sh src/17_python_usd_util_snippets/run.py --mode debug --count 200 --steps 120
```

### 코드에서 볼 부분

Instancer는 큐브 원형 하나와 각 위치에서 사용할 원형 번호를 연결합니다.

```python
geometry.CreatePrototypesRel().SetTargets([prototype.GetPath()])
geometry.CreateProtoIndicesAttr([0] * args.count)
positions = geometry.CreatePositionsAttr(base)
```

원형 목록의 0번이 작은 큐브이므로 모든 인스턴스가 같은 큐브 모양을 사용합니다. 개별 위치는 따로 갖지만 이 실습에서는 강체·충돌 스키마를 추가하지 않습니다.

DebugDraw는 갱신할 때마다 이전 점을 지우고 새 점을 그립니다.

```python
draw.clear_points()
draw.draw_points(
    [tuple(p) for p in samples],
    [(1, 0.3, 0, 1)] * args.count,
    [5.0] * args.count,
)
```

이 점들은 USD Prim으로 만들어지지 않습니다. 그래서 현재 뷰포트에서 보이더라도 USD 저장 대상은 아닙니다. DebugDraw의 크기 인자를 Points의 월드 너비와 같은 단위로 비교하지 마세요.

### 실행 결과 확인하기

각 실행의 `geometry.usda`를 따로 열어보세요. Points와 Instancer는 마지막 배치가 남지만 Debug 모드의 주황색 점은 나타나지 않아야 합니다. Debug 모드도 `rendering.json`에는 최종 위치를 남기므로 **저장된 숫자와 저장된 화면 요소의 차이**를 확인할 수 있습니다.

보고서에는 카메라 값도 들어 있습니다. 코드는 관찰용 뷰포트와 별도로 `/World/CalibrationCamera`를 만들고 초점거리 35, 가로 aperture 36, 세로 aperture 24를 지정합니다. 가정한 해상도는 960×640입니다.

```text
fx = 960 × 35 / 36 ≈ 933.33 px
fy = 640 × 35 / 24 ≈ 933.33 px
주점 = (960/2, 640/2) = (480, 320) px
```

`focal_x_px`, `focal_y_px`, `principal_point_px`를 위 값과 비교해 보세요. 초점거리와 aperture는 같은 단위 체계이므로 비율을 픽셀 수에 곱합니다. 이 계산은 offset 없는 카메라를 가정합니다. **실제 뷰포트 영상에서 보정값을 추정하거나 센서 프레임을 촬영한 결과는 아닙니다.**

### 현재 뷰포트 카메라와 대조하기

계산용 카메라와 지금 보는 화면의 차이는 GUI의 Script Editor에서 직접 확인할 수 있습니다. 다음 코드는 활성 뷰포트의 해상도를 지정하고 앱 업데이트를 기다린 뒤 실제 카메라 경로와 속성을 읽습니다.

```python
import asyncio
import omni.kit.app
import omni.usd
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdGeom

async def inspect_viewport():
    viewport = get_active_viewport()
    if viewport is None:
        raise RuntimeError("먼저 GUI 뷰포트를 여세요.")
    viewport.set_texture_resolution((960, 640))
    await omni.kit.app.get_app().next_update_async()
    camera = UsdGeom.Camera(
        omni.usd.get_context().get_stage().GetPrimAtPath(viewport.camera_path)
    )
    print("viewport:", viewport.get_texture_resolution(), viewport.camera_path)
    print("lens:", camera.GetFocalLengthAttr().Get(),
          camera.GetHorizontalApertureAttr().Get(), camera.GetVerticalApertureAttr().Get())
    print("clipping:", camera.GetClippingRangeAttr().Get())

viewport_task = asyncio.ensure_future(inspect_viewport())
viewport_task.add_done_callback(lambda task: task.result())
```

출력 카메라가 `/World/CalibrationCamera`와 다르면 `rendering.json`과 렌즈 값이 달라도 정상입니다. 같은 960×640 크기를 지정했더라도 초점거리와 aperture가 다르면 화각이 달라집니다. 이 단계도 카메라 속성을 읽는 작업이며 촬영 영상으로 보정 오차를 추정하는 작업은 아닙니다.

### 앱 업데이트를 기다리는 별도 예제

새 Isaac Sim 창의 **Window > Script Editor**에서 `pause_after_update.py` 전체를 실행해 보세요.

```python
timeline.play()
await omni.kit.app.get_app().next_update_async()
timeline.pause()
```

Play 후 내 작업을 잠시 양보하고 앱 업데이트를 기다린 뒤 Pause합니다. 출력의 `Paused after one application update`와 현재 타임라인 시간을 확인하세요. 앱 업데이트 한 번이 항상 물리 한 단계인 것은 아닙니다.

`run.py`의 `--zero-delay`는 렌더 완료 대기와 ROS 2 발행 관련 설정을 앱 시작에 전달하는 옵션입니다. 보고서의 `zero_delay_requested`는 이 옵션을 요청했는지만 나타냅니다. 현재 예제에는 센서 지연을 측정하는 장치가 없으므로, 값이 `true`라고 지연이 0으로 측정된 것은 아닙니다.

## 3. 화면 표현과 저장 데이터 정리

```text
같은 위치 목록
    ├─ Points 속성 갱신       → USD에 점 저장
    ├─ Instancer 위치 갱신    → USD에 인스턴스 저장
    └─ DebugDraw 호출        → 현재 뷰포트에 표시

위치 목록 자체 → rendering.json에 별도 저장
```

나중에 장면을 다시 열어야 한다면 USD에 남는 표현이 필요합니다. 지금 실행 중인 알고리즘의 중간 결과만 눈으로 확인하려면 DebugDraw를 사용할 수 있습니다. 표현을 고를 때는 모양뿐 아니라 **다시 열었을 때도 필요한 데이터인지** 생각해 보세요.

## 4. 간단한 확인 실험

Points 모드에서 `--count`만 200에서 2000으로 바꿔 실행합니다.

```bash
~/isaacsim/python.sh src/17_python_usd_util_snippets/run.py --mode points --count 2000 --steps 120
```

`point_count`와 `final_positions` 개수가 2000으로 늘어나는지 확인하세요. 카메라 설정은 그대로이므로 `focal_x_px`와 `principal_point_px`는 변하지 않아야 합니다. 점 수가 늘어 화면 반응이 달라질 수 있지만, 이 스크립트는 FPS를 자동 측정하지 않습니다.

## 실행할 때 막히면

- **DebugDraw가 Headless에서 오류를 냄**: 보이는 뷰포트가 필요한 모드입니다. `--headless`를 빼고 실행하세요.
- **USD를 다시 열었는데 점이 안 보임**: 어떤 모드의 출력인지 `rendering.json`부터 확인하세요. Debug 점은 저장되지 않습니다.
- **카메라 수치가 현재 화면과 맞지 않음**: 계산 대상은 `/World/CalibrationCamera`와 가정한 해상도입니다. 현재 뷰포트 카메라를 측정한 값이 아닙니다.
- **Pause 예제를 일반 Python에서 실행할 수 없음**: `pause_after_update.py`는 이미 실행 중인 앱의 Script Editor용입니다. 독립 실행용 `run.py`와 사용 위치를 구분하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Util Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/util_snippets.html)에 대응합니다. 점 표현·카메라 계산·앱 업데이트 대기를 비교하도록 구성했으며, 위치 애니메이션과 JSON 저장은 로컬 학습용 코드입니다.

현재 `tutorial.json`은 `not_run`입니다. 이번 개정에서는 세 모드의 저장 경로와 카메라 계산을 코드로 확인했습니다. 뷰포트 표현, 렌더 지연, 실제 센서 동기화는 실행해 검증하지 않았습니다.
