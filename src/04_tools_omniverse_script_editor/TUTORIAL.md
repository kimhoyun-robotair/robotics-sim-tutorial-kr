# 04. Script Editor의 다른 탭에서 같은 큐브를 바꾸기

## 이번에 배우는 것

**첫 번째 탭에서 만든 큐브를 두 번째 탭에서 수정하며, Python 변수와 USD 장면의 관계를 배웁니다.**

Script Editor는 실행 중인 Isaac Sim 안에서 Python을 실행하는 도구입니다. 탭이 여러 개여도 같은 Python 환경을 공유하므로, 첫 탭에서 만든 `cube` 변수를 다른 탭에서 사용할 수 있습니다. 이번에는 생성과 수정을 두 파일로 나눠 이 성질을 직접 확인합니다.

| 대상 | 역할 | 남아 있는 범위 |
|---|---|---|
| `tab1_create.py` | 큐브를 만들고 `cube` 변수에 연결합니다. | 실행한 앱의 Python 환경입니다. |
| `tab2_resize.py` | 같은 변수로 크기 속성을 수정합니다. | 현재 연결된 큐브에 반영됩니다. |
| `/World/EditorCube` | USD 장면에 존재하는 큐브 Prim입니다. | 해당 Stage에 속합니다. |
| `Size` | 큐브의 한 변 길이를 정하는 속성입니다. | USD에 저장할 수 있습니다. |

이 실습에는 강체와 충돌을 추가하지 않습니다. 화면에서 크기가 바뀌는 USD 편집을 관찰합니다.

## 1. 첫 탭에서 큐브 만들기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. Linux에서는 다음 명령으로 앱을 시작하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 빈 Stage를 엽니다.
2. **Window > Script Editor**를 엽니다.
3. Script Editor의 **File > Open**으로 `src/04_tools_omniverse_script_editor/tab1_create.py`를 열거나 전체 내용을 붙여 넣습니다.
4. **Run**을 누릅니다. Play는 필요하지 않습니다.
5. Stage에서 `/World/EditorCube`를 선택하고 `F`로 화면을 맞춥니다.

### 코드에서 볼 부분

```python
stage = omni.usd.get_context().get_stage()
path = "/World/EditorCube"
if stage.GetPrimAtPath(path):
    raise RuntimeError(f"{path} already exists; use a new stage or change path")
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.5)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
```

`get_stage()`는 지금 GUI에서 열린 장면을 가져옵니다. `UsdGeom.Cube.Define()`은 그 장면의 지정 경로에 Cube 타입의 Prim을 정의합니다. 반환된 `cube`는 그 Prim의 큐브 속성을 편리하게 읽고 쓰는 Python 객체입니다.

`CreateSizeAttr(0.5)`는 크기를, `AddTranslateOp()`는 중심 위치를 작성합니다. 숫자가 모두 0.5라도 한쪽은 한 변의 길이이고 다른 한쪽은 z 좌표입니다. 이 파일은 Stage의 거리 단위를 별도로 바꾸지 않으므로 Property 숫자를 비교할 때는 현재 Stage의 단위 설정도 함께 읽으세요.

### 실행 결과 확인하기

출력 영역에 다음 한 줄이 나타나는지 확인하세요.

```text
created /World/EditorCube size 0.5
```

Property의 Size는 0.5, 위치 Z는 0.5여야 합니다. 색상은 코드의 `[0.15, 0.65, 0.95]`가 지정한 푸른색입니다. Stage에는 큐브가 하나만 있습니다.

## 2. 두 번째 탭에서 크기 바꾸기

1. Script Editor의 **Tab > Add Tab**으로 새 탭을 만듭니다.
2. `tab2_resize.py` 전체를 열거나 붙여 넣습니다.
3. 첫 탭을 다시 실행하지 않고 두 번째 탭의 **Run**을 누릅니다.

### 코드에서 볼 부분

```python
if not cube or not cube.GetPrim().IsValid():
    raise RuntimeError("Run tab1_create.py on the current stage first")
print("before", cube.GetSizeAttr().Get())
cube.GetSizeAttr().Set(1.0)
print("after", cube.GetSizeAttr().Get())
```

이 파일에는 `cube`를 새로 만드는 코드도, `UsdGeom`을 다시 import하는 코드도 없습니다. 첫 번째 탭의 변수를 그대로 사용합니다. `GetSizeAttr()`로 속성에 접근한 뒤 `Get()`으로 값을 읽고 `Set()`으로 변경합니다.

**같은 Prim의 속성을 바꾸므로 큐브 개수는 늘지 않습니다.** 위치를 변경하는 문장도 없어서 중심 Z는 0.5를 유지합니다. 크기만 두 배가 되어 중심을 기준으로 양쪽으로 커집니다.

### 실행 결과 확인하기

첫 실행에서는 다음 출력과 화면의 크기 변화를 함께 확인합니다.

```text
before 0.5
after 1.0
```

두 번째 탭을 다시 실행하면 `before`도 1.0입니다. `Set(1.0)`은 현재 크기에 1을 더하는 명령이 아니라 크기를 1.0으로 지정하는 명령이기 때문입니다. Play를 눌러도 큐브가 떨어지지 않는 것은 외형만 만든 이 실습의 정상 동작입니다.

## 3. 변수·탭·Stage의 관계 정리

```text
첫 탭의 cube 변수 ─┐
                  ├→ /World/EditorCube 하나 → Size 속성 읽기·쓰기
둘째 탭의 cube 사용┘
```

탭은 코드를 나눠 적는 공간이고, Stage는 장면 데이터입니다. **File > New로 장면을 바꾸는 일과 Python 환경을 새로 만드는 일은 다릅니다.** 새 Stage를 열어도 이전 변수 이름이 남을 수 있지만, 그것이 새 장면의 큐브를 뜻하지는 않습니다. 새 장면에서는 첫 탭을 실행해 `cube`를 다시 연결하세요.

Script Editor의 파일 저장은 Python 코드를 저장합니다. 장면을 남기려면 앱의 **File > Save As**로 USD도 따로 저장해야 합니다. 앱을 종료하면 실행 중에 만든 Python 변수는 사라집니다.

## 4. 간단한 확인 실험

두 번째 탭에서 다음 줄의 값 하나만 바꾸세요.

```python
cube.GetSizeAttr().Set(0.25)
```

현재 크기가 1.0이라면 `before 1.0`, `after 0.25`가 출력되고 한 변이 1/4로 줄어듭니다. 중심 위치와 Prim 개수는 그대로인지 확인하세요. 첫 탭을 다시 실행할 필요 없이 기존 객체를 편집한다는 점을 확인하는 실험입니다.

## 실행할 때 막히면

- **`NameError: cube`**: 현재 Python 환경에서 첫 탭을 아직 실행하지 않았습니다. `tab1_create.py`부터 실행하세요.
- **`already exists` 오류**: 현재 Stage에 큐브가 이미 있습니다. 크기 변경에는 둘째 탭을 쓰고, 처음부터 반복하려면 File > New 후 첫 탭을 실행합니다.
- **새 Stage에서 둘째 탭이 실패함**: 이전 `cube`가 유효하지 않을 수 있습니다. 첫 탭을 실행해 새 Stage의 Prim에 연결하세요.
- **터미널 실행에서 `omni` import 오류**: 이 파일은 실행 중인 Isaac Sim의 Script Editor용입니다. 앱 안에서 실행하세요.
- **크기는 바뀌었지만 화면에서 찾기 어려움**: Stage에서 정확한 경로를 선택하고 `F`로 맞춘 뒤 Property의 Size를 읽으세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Omniverse Script Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html)에 대응합니다. 원문에서 설명하는 탭 간 환경 공유를 큐브 생성·수정·재실행으로 확인하도록 구성했습니다.

출력 파일을 자동으로 만들거나 물리를 진행하는 코드는 없습니다. 위 출력과 Property 값은 GUI에서 확인할 기준이며, `tutorial.json`의 실행 검증 상태는 `not_run`입니다.
