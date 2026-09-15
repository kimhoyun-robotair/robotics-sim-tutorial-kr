# 92. 실행 중인 Python에 연결해 큐브 위치 추적하기

## 이번에 배우는 것

**VS Code debugger로 실행을 멈추고, 명령행 높이 값이 Python 변수와 USD 위치로 전달되는 과정을 확인합니다.**

화면에서 큐브가 엉뚱한 위치에 보인다면 입력이 잘못되었는지, 코드가 다른 값을 썼는지 살펴봐야 합니다. **Breakpoint**는 지정한 줄을 실행하기 전에 코드를 멈추는 지점입니다. **Attach**는 이미 실행 중인 Python 프로세스에 debugger를 연결하는 방식입니다.

| 실행 대상 | 연결 설정 | 관찰할 큐브 |
|---|---|---|
| 로컬 `run.py` | Attach local standalone, 포트 5678 | `/World/DebugCube`, 크기 0.2 |
| 기존 Isaac Sim GUI | Attach Isaac Sim 5.1, 포트 3000 | `attached_scene.py`의 `/World/EditorCube` |
| 준비된 Docker | Attach Docker, 포트 5678 | 컨테이너의 `/lesson/run.py` |

`run.py`는 USD 도형과 앱 업데이트 루프를 만듭니다. 강체나 충돌을 추가하지 않아 큐브는 떨어지지 않습니다. 이번 관찰 대상은 낙하가 아니라 **값이 전달되는 경로**입니다.

## 1. 로컬 standalone에 연결하기

Linux, Isaac Sim 5.1, 지원 NVIDIA GPU와 VS Code의 Python/Python Debugger 확장이 필요합니다. 저장소 루트에서 다음으로 이 튜토리얼 폴더를 VS Code에 여세요.

```bash
code src/92_tools_advanced_python_debugging
```

`.vscode/launch.json`을 읽으려면 VS Code의 workspace가 **92번 폴더 자체**여야 합니다. 아래 실행 명령은 저장소 루트의 터미널에서 사용합니다.

```bash
python3 src/92_tools_advanced_python_debugging/run.py --help
~/isaacsim/python.sh -m debugpy --listen 127.0.0.1:5678 \
  --wait-for-client src/92_tools_advanced_python_debugging/run.py --height 1.0
```

Isaac Sim Python에서 `debugpy`를 찾지 못한다면 먼저 `~/isaacsim/python.sh -m pip install debugpy`로 해당 환경에 준비하세요.

1. VS Code에서 `run.py`를 열고 `print("breakpoint position:", position)` 줄에 breakpoint를 둡니다.
2. Run and Debug에서 **Attach local standalone**을 선택하고 F5를 누릅니다.
3. 앱 시작이 진행된 뒤 해당 줄에서 멈추는지 확인합니다.
4. 변수 창이나 Debug Console에서 `args.height`, `position`, `cube.GetPath()`를 확인합니다.
5. F10으로 한 줄 진행하고 Continue로 앱 업데이트를 재개합니다.

`--wait-for-client`는 debugger가 연결되기 전 스크립트를 시작하지 않게 합니다. 연결 전 앱 창이 없는 것은 이 순서의 정상 동작입니다.

### 코드에서 볼 부분

`SimulationApp`을 만든 다음 USD 관련 모듈을 불러오고 위치를 작성합니다.

```python
cube = UsdGeom.Cube.Define(stage, "/World/DebugCube")
cube.CreateSizeAttr(0.2)
position = Gf.Vec3d(0, 0, args.height)
cube.AddTranslateOp().Set(position)
print("breakpoint position:", position)
```

이 print 줄에서 멈추면 바로 앞의 Translate 작성은 이미 끝난 상태입니다. `position[2]`뿐 아니라 다음 표현식도 Debug Console에서 확인해 보세요.

```python
cube.GetPrim().GetAttribute("xformOp:translate").Get()
```

Python 변수와 USD에 실제 저장한 값이 모두 같은 Z를 갖는지 비교할 수 있습니다. 화면은 앱 갱신 전이라 아직 이전 모습일 수 있으므로 Continue 후 Property에서도 Translate Z를 확인하세요.

### 실행 결과 확인하기

기본 입력은 1.0입니다. `args.height`는 1.0, `position`은 `(0,0,1)`, prim 경로는 `/World/DebugCube`여야 합니다. 출력에는 `breakpoint position:`과 위치가 나타납니다.

GUI는 창을 직접 닫을 때까지 유지됩니다. `--steps 240`을 추가하면 `app.update()` 240회 뒤 종료합니다. `--frames`는 `--headless`에서 `--steps`를 생략했을 때의 기본 한도이며, GUI 수명을 제한하지 않습니다. 업데이트 횟수는 물리 시뮬레이션 시간으로 환산할 수 없습니다.

### 설치본의 Current File 설정으로 직접 실행하기

같은 `run.py`를 VS Code가 직접 시작하는 방식도 비교할 수 있습니다. 앞의 standalone을 종료하고 저장소 루트의 터미널에서 경로를 확인한 뒤 설치 폴더를 새 VS Code 창으로 엽니다.

```bash
realpath src/92_tools_advanced_python_debugging/run.py
code -n "$HOME/isaacsim"
```

1. 새 창의 **File > Open File**에서 위 절대 경로의 `run.py`를 엽니다. workspace는 Isaac Sim 설치 폴더로 유지하고, 실행할 편집 탭은 이 튜토리얼의 `run.py`로 둡니다.
2. Run and Debug에서 설치본의 **Python: Current File**을 선택하고 같은 print 줄에 breakpoint를 둡니다.
3. F5를 누르면 `setup_python_env` 작업이 환경 파일을 준비하고 `${file}`인 현재 파일을 Isaac Sim Python으로 시작합니다. 기본 높이 1.0의 변수와 USD 값을 확인하세요.
4. 이 경로를 마친 뒤 제공된 attach 설정을 다시 사용할 때는 VS Code workspace를 92번 폴더로 되돌립니다.

설치본의 `.vscode/launch.json`과 `tasks.json`에 이 구성이 있는 경우에 사용할 수 있습니다. 설정이 없는 설치에서는 앞의 제공 attach 경로를 사용하세요. Current File은 새 독립 프로세스를 시작하므로 `attached_scene.py` 같은 GUI 내부용 파일을 대상으로 선택하지 않습니다.

## 2. 기존 GUI와 Docker의 소스 위치 맞추기

### 설정에서 볼 부분

제공 `launch.json`의 로컬 attach 설정은 다음 주소를 사용합니다.

```json
"connect": {
  "host": "127.0.0.1",
  "port": 5678
}
```

연결 주소는 **어느 프로세스를 디버깅할지** 정합니다. 소스 경로는 **그 프로세스의 코드가 편집기의 어느 파일인지** 정합니다. 접속이 되더라도 소스가 맞지 않으면 원하는 breakpoint에 멈추지 않을 수 있습니다.

기존 GUI는 앞의 standalone을 종료한 뒤 별도로 엽니다.

```bash
realpath src/92_tools_advanced_python_debugging/attached_scene.py
~/isaacsim/isaac-sim.sh
```

첫 번째 명령의 출력 경로를 아래 Script Editor 코드에 사용합니다.

1. Isaac Sim의 **Window > Extensions**에서 `omni.kit.debug.vscode`를 켭니다.
2. debugger 창의 주소를 확인합니다. 5.1 기본 주소는 `127.0.0.1:3000`입니다.
3. VS Code에서 **Attach Isaac Sim 5.1**을 선택합니다.
4. `attached_scene.py`의 마지막 print 줄에 breakpoint를 둡니다.
5. Isaac Sim에서 새 Stage를 준비하고 Script Editor에서 다음을 실행합니다. `script_path`에는 realpath가 출력한 **실제 절대 경로**를 넣으세요.

```python
from pathlib import Path

script_path = "/실제/절대/경로/attached_scene.py"
exec(compile(Path(script_path).read_text(), script_path, "exec"))
```

`compile`에 파일 경로를 넘기면 실행 코드의 파일 이름이 편집기의 실제 파일과 대응합니다. 내용을 이름 없는 편집 버퍼에 붙여 넣어 실행할 때 생길 수 있는 경로 혼동을 줄이는 방법입니다.

### 실행 결과 확인하기

이번 파일에서는 `/World/EditorCube`, 크기 0.5, 위치 `(0,0,0.5)`를 확인하세요. 색은 청록색입니다. `run.py`의 `--height` 인자를 사용하지 않으므로 앞 실험의 높이가 여기로 전달되지는 않습니다.

Docker에서는 NVIDIA GPU runtime을 갖춘 Isaac Sim 5.1 컨테이너에 **92번 폴더 전체를 `/lesson`으로 bind mount**하고 포트 5678을 host의 `127.0.0.1:5678`로 연결해 둡니다. 준비된 컨테이너 안에서 실행하세요.

```bash
cd /isaac-sim
./python.sh -m debugpy --listen 0.0.0.0:5678 --wait-for-client \
  /lesson/run.py --headless --frames 240
```

VS Code의 **Attach Docker**는 다음 대응을 사용합니다.

```json
"pathMappings": [
  {
    "localRoot": "${workspaceFolder}",
    "remoteRoot": "/lesson"
  }
]
```

따라서 host에서 92번 폴더를 workspace로 열어야 컨테이너의 `/lesson/run.py`와 정확히 대응합니다. 연결 후 같은 print 줄에서 실제로 멈추고 변수를 읽어보세요. 컨테이너 설치·시작 자체는 이 폴더의 실행 파일이 자동으로 처리하지 않습니다.

## 3. 연결과 값 전달 정리

```text
debugger 주소 → 디버깅할 프로세스 선택
소스 경로     → 그 프로세스의 코드를 편집기 파일에 대응
breakpoint    → 원하는 실행 줄에서 멈춤
--height      → args.height → position → USD Translate → 화면
```

**Attached 표시는 연결의 확인이고, breakpoint에서 읽은 변수와 USD 값은 코드 실행의 확인입니다.** 화면 문제를 추적할 때는 이 두 확인을 이어서 수행하세요.

## 4. 간단한 확인 실험

로컬 standalone 명령의 **`--height 1.0`만 `--height 2.0`으로** 바꾸어 다시 실행하고 attach합니다.

같은 breakpoint에서 `args.height`, `position[2]`와 USD Translate Z가 모두 2.0이어야 합니다. Continue 후 화면에서도 큐브가 높아집니다. Size는 계속 0.2입니다. 값이 변수까지는 바뀌었는데 화면이 그대로라면 잘못된 prim을 보고 있는지 또는 실행을 아직 재개하지 않았는지 확인하세요.

## 실행할 때 막히면

- **`debugpy` 모듈을 찾지 못함:** debugger를 실행하는 Isaac Sim Python 환경에 준비했는지 확인하세요.
- **접속 거부 또는 포트 충돌:** 실행 대상이 5678 standalone인지 3000 GUI인지 구분하고 같은 포트를 쓰는 이전 실험을 종료하세요.
- **breakpoint가 회색이거나 멈추지 않음:** 실행 파일과 편집 파일의 절대 경로, Docker의 `pathMappings`를 대조하세요.
- **`EditorCube already exists`:** `attached_scene.py`는 중복 경로를 막습니다. 새 Stage에서 다시 실행하세요.
- **GUI가 breakpoint에서 멎어 보임:** 앱을 진행시키는 Python 실행을 멈춘 상태일 수 있습니다. Continue 후 다시 관찰하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Debugging With Visual Studio Code](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html)에 대응합니다. 로컬 launch 설정, 큐브 소스와 설치된 debugger의 기본 포트를 대조했습니다.

이번 개정에서는 인자 도움말과 파일·설정 연결을 확인했습니다. 실제 debugger 접속, breakpoint 중단, Docker 및 GUI 실행은 검증하지 않았으며 `tutorial.json`의 상태는 `not_run`입니다.
