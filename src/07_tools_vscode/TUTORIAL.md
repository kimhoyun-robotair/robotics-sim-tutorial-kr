# 07. VS Code의 코드는 어느 Python에서 실행될까요?

## 이번에 배우는 것

**VS Code에서 코드를 실행 중인 Isaac Sim으로 보내고, 같은 연결에서 큐브를 다시 조회하며 실행 위치를 확인합니다.**

04번에서는 앱 안의 Script Editor를 사용했습니다. 이번에는 편집기를 VS Code로 바꾸지만 코드는 여전히 Isaac Sim 앱 안에서 실행합니다. 일반 터미널의 Python 실행과 구분해야 하는 이유를 큐브 하나로 확인해 보세요. (시스템 파이썬이 아니라 Isaac Sim의 내부 파이썬에서 돌아가는 것을 유념하세요!)

| 위치·파일 | 역할 |
|---|---|
| VS Code의 `NVIDIA.isaacsim-vscode-edition` | 파일이나 선택 영역을 Isaac Sim에 보내는 편집기 확장입니다. |
| 앱의 `isaacsim.code_editor.vscode` | 전달된 코드를 실행하는 Isaac Sim 확장입니다. |
| `scene.py` | 활성 Stage에 큐브를 작성하는 로컬 실습 파일입니다. |
| `/World/EditorCube` | 앱에 실제로 생성되는 USD Prim 경로입니다. |
| Isaac Sim VS Code Edition output | 전달한 코드의 출력을 확인하는 패널입니다. |

`scene.py`는 `SimulationApp`을 만들지 않습니다. 연결 대상 앱이 이미 실행 중이며 그 앱의 장면과 Python 상태를 사용합니다.

## 1. 양쪽 확장을 연결하고 파일 실행하기

Isaac Sim 5.1 GUI, 지원 NVIDIA GPU와 VS Code를 준비합니다. Linux에서는 다음으로 앱을 시작하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/isaac-sim.sh
```

1. Isaac Sim에서 **File > New**로 빈 Stage를 엽니다.
2. VS Code의 Extensions에서 [Isaac Sim VS Code Edition](https://marketplace.visualstudio.com/items?itemName=NVIDIA.isaacsim-vscode-edition)을 설치·활성화합니다.
3. Isaac Sim의 **Window > Extensions**에서 `isaacsim.code_editor.vscode`를 검색해 Enabled를 켭니다.
4. **Window > VS Code**로 설치 폴더를 VS Code에서 열 수 있습니다. VS Code에서 이 저장소의 `src/07_tools_vscode/scene.py`를 여세요.
5. VS Code Activity Bar의 Isaac Sim 로고를 누르고 **Commands > Run**을 선택합니다.
6. **Isaac Sim VS Code Edition output**과 Isaac Sim의 Stage를 함께 확인합니다.

이 절차의 Run은 Isaac Sim 전용 명령입니다. 일반 Python 실행 버튼은 같은 앱으로 코드를 전달하는 명령이 아닙니다. 연결 절차는 [공식 5.1 VS Code 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/vscode.html#interactive-scripting)를 따릅니다.

### 코드에서 볼 부분

```python
stage = omni.usd.get_context().get_stage()
path = "/World/EditorCube"
if stage.GetPrimAtPath(path):
    raise RuntimeError(f"{path} already exists; use a new stage or change path")
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.5)
```

`get_stage()`가 가져오는 대상은 VS Code의 파일이 아니라 연결된 Isaac Sim의 현재 장면입니다. `Define()`으로 그 Stage에 큐브를 만들고, `cube`라는 Python 변수로 같은 Prim에 접근합니다. 앞의 경로 검사는 같은 장면에 파일 전체를 반복 실행해 의도치 않게 덮어쓰는 일을 막습니다.

뒤의 `AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))`는 중심 좌표를 설정하고, `CreateDisplayColorAttr()`는 푸른색을 지정합니다. 이 파일은 거리 단위나 강체·충돌 속성을 따로 작성하지 않습니다.

### 실행 결과 확인하기

출력 패널에서 다음 문장을 확인하세요.

```text
created /World/EditorCube size 0.5
```

Isaac Sim Stage에서 같은 경로를 선택하고 `F`로 화면을 맞춥니다. Property의 Size는 0.5, 중심 Z는 0.5여야 합니다. **출력이 도착했다는 사실과 원하는 앱의 Stage가 바뀌었다는 사실을 함께 확인**하세요. 연결 창을 여러 개 열었다면 다른 앱에 코드가 전달될 수 있기 때문입니다.

## 2. 선택한 코드로 같은 변수 다시 읽기

VS Code에서 새 Python 파일이나 빈 편집 영역에 아래 두 줄을 적고, 두 줄만 선택해 Isaac Sim의 **Run selected text**를 실행합니다.

```python
print(cube.GetPath())
print(cube.GetSizeAttr().Get())
```

### 코드에서 볼 부분

이번에는 큐브를 생성하거나 파일을 import하지 않습니다. 첫 실행에서 연결된 앱에 남긴 `cube`를 사용합니다. `GetPath()`는 Prim의 주소, `GetSizeAttr().Get()`은 현재 크기 속성 값을 읽습니다.

VS Code에서 코드 파일을 저장하는 것과 앱에서 실행하는 것도 별개입니다. 편집한 글자를 저장해도 Run으로 보내기 전에는 장면이 바뀌지 않습니다. 반대로 실행해서 바뀐 장면은 USD를 저장해야 디스크에 남습니다.

### 실행 결과 확인하기

출력은 `/World/EditorCube`와 `0.5`여야 합니다. 이것이 후속 실행이 같은 앱의 Python 상태에 접근했다는 관찰 근거입니다. Play를 눌러도 큐브가 떨어지지 않는 것은 강체를 추가하지 않았기 때문입니다.

새 Stage를 열었다면 첫 파일을 다시 실행해 `cube`를 새 Prim에 연결하세요. Python 변수 이름이 남아 있다는 사실만으로 현재 Stage의 객체라고 판단하면 안 됩니다.

## 3. 연결 실행과 디버그 설정 정리

```text
VS Code에서 파일 또는 선택 영역 작성
    → Isaac Sim 전용 Run
    → 연결된 앱의 Python 환경에서 실행
    → Stage 변경 + 전용 output 패널에 출력
```

설치 폴더의 `.vscode` 설정은 다른 실행 경로도 제공합니다.

| 설정 | 쓰임새 |
|---|---|
| `launch.json`의 Python: Current File | 독립 실행 파일을 새 Python 프로세스에서 디버깅합니다. |
| Python: Attach | 실행 중인 앱에 디버거를 연결합니다. |
| `settings.json`의 interpreter·`python.analysis.extraPaths` | 편집기가 Python과 확장 import 경로를 찾도록 돕습니다. |
| `tasks.json`의 `setup_python_env` | 독립 실행 디버거에 필요한 환경 파일을 준비합니다. |

이번 `scene.py`에는 현재 앱의 Stage가 필요하므로 **Isaac Sim 전용 연결 실행**을 사용합니다. 코드 자동완성에 오류 표시가 없다는 것만으로 앱에 연결됐다고 판단할 수는 없습니다. 설치 설정의 구분은 [공식 구성 파일 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/vscode.html#vs-code-configuration-files)을 참고하세요.

## 4. 간단한 확인 실험

Isaac Sim에서 새 Stage를 열고 `scene.py`의 `CreateSizeAttr(0.5)`만 `CreateSizeAttr(1.0)`으로 바꾼 뒤 파일 전체를 전용 Run으로 실행하세요.

출력 크기와 Property의 Size가 모두 1.0인지 확인합니다. 중심 Z는 그대로 0.5이며 큐브 한 변만 두 배가 됩니다. VS Code에서 수정한 코드가 실제 연결된 Stage에 반영되는 경로를 확인하는 실험입니다. 마치면 크기 값을 0.5로 복원할 수 있습니다.

## 실행할 때 막히면

- **연결되지 않거나 출력이 없음**: VS Code 확장과 Isaac Sim 확장이 모두 활성화됐는지, 연결 주소가 실행 중인 앱을 가리키는지 확인하세요.
- **`No module named omni`**: 일반 Python 실행 버튼을 사용했는지 확인하고 Isaac Sim 로고 아래의 Run을 사용하세요.
- **`already exists` 오류**: 현재 Stage에 큐브가 있습니다. 조회에는 선택 영역 실행을 사용하고 생성 실험은 새 Stage에서 반복합니다.
- **`NameError: cube`**: 그 연결에서 `scene.py`를 먼저 실행하세요. 앱을 재시작하거나 연결 대상이 바뀌면 이전 변수는 사용할 수 없습니다.
- **코드는 저장했는데 큐브가 그대로임**: 편집기 저장 후 전용 Run을 눌렀는지 확인하고, 출력 패널의 최신 숫자를 읽으세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Visual Studio Code (VS Code)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/vscode.html)에 대응합니다. 원문의 연결 실행을 큐브 작성과 후속 변수 조회로 확인합니다. 별도의 디버거 연결이나 독립 앱 시작은 이번 파일의 동작에 포함되지 않습니다.

결과는 활성 Stage와 전용 output 패널에서 확인합니다. `tutorial.json`의 실행 검증 상태는 `not_run`이며, 연결 성공·화면 변화는 위 절차에 따라 직접 확인할 기준입니다.
