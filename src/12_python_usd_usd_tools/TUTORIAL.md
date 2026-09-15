# 12. 끊어진 USD 참조를 고치고 색 대안 선택하기

## 이번에 배우는 것

**찾을 수 없는 자산 참조를 복구한 뒤, 같은 물체의 빨강·파랑 대안을 선택합니다.**

USD 장면에서 로봇이 보이지 않을 때는 모양 자체가 지워진 것인지, 모양을 가져올 파일을 찾지 못하는 것인지 먼저 구분해야 합니다. 이번에는 존재하지 않는 경로를 참조하는 장면을 일부러 만들고, 참조 경로만 고쳐 큐브를 다시 나타나게 합니다.

복구된 큐브에는 `finish`라는 **Variant Set**이 있습니다. Variant Set은 여러 대안을 묶는 이름이고, `red`와 `blue`는 그 안에서 고를 수 있는 선택지입니다.

| 이번 실습의 데이터 | 의미 |
|---|---|
| `moved_assets/body.usda` | 실제 큐브와 두 색 대안을 담은 자산 파일 |
| `broken.usda` | 없는 `old_assets/body.usda`를 참조하는 장면 |
| `repaired.usda` | 참조 경로를 복구한 새 장면 |
| `/World/Robot/Body` | 복구 후 장면 안에 나타날 큐브의 Prim 경로 |

파일을 가리키는 자산 경로와 장면 안의 요소를 가리키는 Prim 경로는 역할이 다릅니다. 이번 실습에서는 두 경로를 결과 보고서로 함께 확인합니다.

## 1. 먼저 경로 복구 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 있는 환경에서 실행합니다. 아래는 저장소 루트 기준 Linux 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/12_python_usd_usd_tools/run.py --variant red --steps 120
```

스크립트가 자산과 장면을 만들고 복구한 뒤, 앱 업데이트 120회를 진행하고 종료합니다. 복구된 장면을 직접 살펴보려면 `--steps 120`을 빼세요. 창 없이 실행하려면 `--headless`를 추가합니다. Headless에서 단계 수를 생략하면 120회 후 종료합니다.

출력은 이 폴더의 `output/날짜-시간/`에 생깁니다. `--output`으로 직접 지정할 때는 존재하지 않는 새 폴더를 사용하세요.

### 코드에서 볼 부분

먼저 깨진 장면에 다음 참조를 작성합니다.

```python
instance.GetPrim().GetReferences().AddReference("old_assets/body.usda")
```

이 파일은 만들지 않았으므로 참조 경고가 나오는 것이 정상입니다. `/World/Robot`이라는 상위 Prim은 있어도, 외부 파일에서 가져와야 할 자식 `Body`는 나타나지 않습니다.

복구할 때는 기존 내용을 새 레이어로 복사한 뒤 경로를 바꿉니다.

```python
fixed_layer.TransferContent(assembly.GetRootLayer())
UsdUtils.ModifyAssetPaths(fixed_layer, repair)
fixed_layer.Save()
fixed = Usd.Stage.Open(fixed_layer)
```

`repair()`는 `old_assets/`로 시작하는 경로만 `moved_assets/`로 치환합니다. **문자열을 바꾼 것으로 끝내지 않고, 저장한 레이어를 실제로 다시 열어 Body가 있는지 검사**하는 것이 핵심입니다. 원래의 `broken.usda`는 비교 대상으로 남습니다.

### 실행 결과 확인하기

`tools_report.json`에서 다음 값을 확인해 보세요.

| 항목 | 기본 실행의 확인 기준 |
|---|---|
| `broken_has_body` | `false`: 원래 참조로는 Body를 불러오지 못함 |
| `repaired_has_body` | `true`: 새 경로로 Body를 불러옴 |
| `path_changes` | `old_assets/body.usda` → `moved_assets/body.usda` |
| `selection` | `red` |
| `color` | `[1.0, 0.0, 0.0]`, 빨강 RGB |

화면에서는 한 변 0.5 m의 빨간 큐브를 확인합니다. 이 장면에는 낙하를 위한 강체 설정이 없습니다. 앱을 오래 갱신해도 큐브가 떨어지는 실습은 아닙니다.

## 2. 복구된 자산의 Variant 살펴보기

이번에는 `run.py`에서 자산을 만드는 부분을 읽어보세요.

### 코드에서 볼 부분

```python
variants = robot.GetPrim().GetVariantSets().AddVariantSet("finish")
variants.AddVariant(name)
variants.SetVariantSelection(name)
with variants.GetVariantEditContext():
    cube.CreateDisplayColorAttr([color])
```

실제 코드에서는 이 흐름을 `red`와 `blue`에 대해 반복합니다. 먼저 대안을 추가하고 그 대안을 선택한 다음, **선택한 대안 안에 색 값을 작성**합니다. 따라서 `finish`를 바꾸면 같은 큐브의 색만 바뀝니다.

`GetVariantEditContext()` 밖에서 더 강한 색 값을 따로 작성하면, 대안을 바꿔도 그 값이 계속 보일 수 있습니다. Variant를 사용할 때는 값뿐 아니라 어느 대안과 레이어에 작성하는지도 살펴야 합니다.

### 실행 결과 확인하기

1. 앞의 앱이 종료되었다면 `~/isaacsim/isaac-sim.sh`로 새 창을 열고, **File > Open**으로 출력의 `repaired.usda`를 엽니다.
2. Stage에서 `/World/Robot`을 선택하고 Property의 `finish` 선택을 확인합니다.
3. `red`와 `blue`를 번갈아 선택해 위치와 크기는 유지되고 색만 달라지는지 봅니다.
4. GUI 변경을 보존하려면 **File > Save As**로 새 이름을 사용합니다. 이미 생성된 `tools_report.json`은 GUI 변경에 맞춰 갱신되지 않습니다.

### 같은 작업을 USD 도구에서 해 보기

**Window > Extensions**에서 `omni.kit.window.usd_paths`, `omni.kit.variant.presenter`, `omni.kit.variant.editor`를 활성화합니다. 설치된 5.1의 메뉴는 각각 **Window > USD Paths**, **Tools > Variants > Variant Presenter**, **Tools > Variants > Variant Editor**입니다.

1. `broken.usda`를 열고 **File > Save As**로 같은 출력 폴더에 `gui_repaired.usda`를 만듭니다. 상대 참조가 같은 위치에서 해석되도록 저장 폴더를 유지합니다.
2. USD Paths에서 `old_assets/`를 찾아 `moved_assets/`로 치환하고 저장합니다. 파일을 다시 열어 `/World/Robot/Body`가 실제로 나타나는지 확인하세요.
3. `/World/Robot`을 선택하고 Variant Presenter에서 `finish` 그룹의 `red`와 `blue`를 번갈아 고릅니다. 이미 있는 대안을 보여 주는 도구의 역할을 확인합니다.
4. Variant Editor에서 같은 Prim의 `finish`에 `green`을 추가하고 선택합니다. **Add Prim**으로 `/World/Robot/Body`를 넣고, 그 카드의 **Add Property**에서 `primvars:displayColor`를 추가합니다. **Variant Editor 안의 속성 편집란**에서 색을 `(0, 1, 0)`으로 바꾸고 저장하세요. **Add Prims/Properties to All Variants** 옵션은 끕니다. 일반 Property 창에서 색만 바꾸면 현재 레이어에 별도의 override를 쓸 수 있습니다.
5. `red`로 돌아오면 빨강, `green`에서는 초록인지 비교합니다. 모든 선택에서 초록이면 Variant 바깥 레이어에 더 강한 색 값을 작성했는지 확인하세요.

원래 보고서의 `variants`는 스크립트가 만든 두 선택지만 기록합니다. GUI에서 추가한 `green`의 확인 대상은 수정한 USD와 화면입니다. 도구가 설치되어 있지 않다면 기본 API 실습까지 완료할 수 있으며, GUI 단계는 도구를 사용할 수 있는 환경에서 별도로 수행합니다.

## 3. 경로 복구와 대안 선택 정리

```text
broken.usda
    → old_assets/body.usda를 찾지 못함 → Body 없음

repaired.usda
    → moved_assets/body.usda를 불러옴 → Body 있음
    → finish 선택                   → 빨강 또는 파랑
```

상대 자산 경로는 그 경로를 작성한 레이어 위치를 기준으로 해석됩니다. 그래서 결과를 다른 곳으로 옮길 때도 `repaired.usda`와 `moved_assets/`의 상대 위치를 함께 유지해야 합니다. 터미널의 현재 폴더만 바꿔서는 잘못 작성된 참조가 복구되지 않습니다.

**먼저 자산이 들어오는지 확인하고, 그다음 어떤 대안이 선택됐는지 확인하세요.** 두 문제를 분리하면 “물체가 없다”와 “색이 다르다”를 다른 원인으로 조사할 수 있습니다.

## 4. 간단한 확인 실험

같은 명령에서 `--variant`만 `blue`로 바꿔 실행해 보세요.

```bash
~/isaacsim/python.sh src/12_python_usd_usd_tools/run.py --variant blue --steps 120
```

새 보고서의 `selection`은 `blue`, `color`는 `[0.0, 0.0, 1.0]`이어야 합니다. 반면 `path_changes`와 Body 복구 여부는 빨강 실행과 같아야 합니다. `variants` 목록의 순서는 비교 기준이 아닙니다.

## 실행할 때 막히면

- **`old_assets/body.usda` 참조 경고**: 복구 전 장면이 의도적으로 내는 경고입니다. 최종 `repaired_has_body`까지 확인하세요.
- **복구된 파일에서도 큐브가 없음**: `moved_assets/body.usda`가 함께 있는지 확인하세요. 결과 USD 하나만 옮기면 참조가 다시 끊어질 수 있습니다.
- **대안을 바꿔도 색이 같음**: `/World/Robot`의 `finish`를 선택했는지 확인하고, Body에 별도의 색 override를 작성했다면 그 레이어를 조사하세요.
- **출력 폴더가 이미 있다는 오류**: `--output`에 새 경로를 쓰거나 옵션을 생략하세요. 이전 결과는 자동으로 덮어쓰지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [USD Tools](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/usd_tools.html)에 대응합니다. 도구의 대상인 자산 경로와 Variant를 로컬 API 실습으로 구성했습니다. GUI에서 새 Variant를 만드는 작업은 기본 스크립트에 포함되지 않습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 과거 코드의 기본 빨강 모드를 Headless 2회 업데이트로 실행한 참고 기록입니다. 현재 코드의 재실행, 파랑 모드와 GUI 도구 조작은 확인하지 않았습니다. 위 색과 복구 여부는 실행 후 대조할 기준입니다.
