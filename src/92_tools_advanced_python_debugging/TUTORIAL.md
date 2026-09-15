# 92. Debugging With Visual Studio Code

권장 학습 순서 **92** · OmniGraph와 확장 개발 · 출처 ID `t170`

같은 Cube 위치 변수를 standalone, Docker, 실행 중인 GUI 세 환경에서 breakpoint로 관찰한다. 제공 run.py는 `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI를 유지한다.

## 이 실습의 의도

작은 USD Cube 생성 과정을 멈춰 보면서 실행 인자, Python 변수, 장면에 기록된 Transform이 같은 값을 가리키는지 추적한다. 복잡한 로봇 제어 없이 standalone 시작과 기존 프로세스 attach의 차이, Docker의 소스 경로 대응을 확인하도록 구성했다. 기본 `run.py`는 Cube와 Kit 업데이트 루프만 만들며 debugger 연결은 별도 설정이고, 강체·충돌·물리 낙하는 구현하지 않는다.

## 실행 후 확인할 것

- **standalone 중단 지점:** `print("breakpoint position:", position)`에 둔 breakpoint에서 실제 실행이 멈추는지 확인한다. 기본값에서는 `position=(0,0,1)`, `cube.GetPath()`는 `/World/DebugCube`이고 Cube 크기는 0.2다.
- **입력에서 장면까지:** `--height 2.0`으로 다시 실행하면 변수의 z와 `/World/DebugCube`의 Translate Z가 모두 2인지 확인한다. Continue 후 Cube가 공중에 고정된 것은 이 장면에 rigid body를 넣지 않았기 때문이다.
- **attach 연결:** `--wait-for-client` 실행이 debugger 연결 후 진행되고, 해당 소스의 breakpoint와 F10 stepping이 동작하는지 본다. Attached 표시만으로 올바른 소스 파일에서 중단된 것을 대신하지 않는다.
- **GUI 내부 스크립트:** GUI에 attach한 뒤 `attached_scene.py`의 print 줄에서 `/World/EditorCube`, 크기 0.5, z=0.5를 확인한다. 이 파일의 Cube는 청록색이며 `run.py`의 `--height`를 사용하지 않는다. 같은 prim이 있는 stage에서 재실행하면 의도적으로 오류를 낸다.
- **수명과 원격 경로:** GUI 기본 실행은 창을 닫을 때까지 유지되고 `--steps`는 `app.update()` 횟수를 제한한다. Docker에서 회색 breakpoint가 보이면 `${workspaceFolder}`와 `/lesson`의 파일 대응을 먼저 확인한다.

## 준비와 standalone 실행

Linux, Isaac Sim 5.1.0, 지원 GPU, VS Code의 Python/Python Debugger 확장이 필요하다. 이 폴더를 VS Code로 연다. Python 인자 도움말은 일반 Python으로도 된다.

```bash
python3 run.py --help
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" run.py --height 1.0
```

실행 횟수를 제한하려면 `--steps 240`을 추가한다. 여기서 한 스텝은 `app.update()` 한 번이며, 물리 시뮬레이션 시간과 같지 않다. GUI에서는 `--frames`가 창을 닫지 않는다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 `--frames 240`회 후 종료한다.

1. 설치 폴더를 VS Code로 열면 제공 `.vscode`의 **Python: Current File**로 standalone을 디버깅할 수 있다. 이 패키지 `run.py`를 열고 `print("breakpoint position:", position)`에 breakpoint를 둔다.
2. F5로 시작하고 멈추면 position의 z=1을 Inspect, F10으로 한 줄씩 진행한다. Debug Console에서 `args.frames`, `cube.GetPath()`를 확인한다.
3. launch args의 `--height`를 2로 바꾸면 breakpoint에서 z=2가 된다. 확장 환경의 코드에 Current File을 사용하지 않는다.

## 이 폴더에서 remote attach

제공 `.vscode/launch.json`에는 attach 세 구성이 있다. Isaac Sim Python에 debugpy가 있는 환경에서 다음을 실행한다. 없으면 공식 문서 방식인 `"$ISAAC_SIM_PATH/python.sh" -m pip install debugpy`로 설치를 준비한다.

```bash
"$ISAAC_SIM_PATH/python.sh" -m debugpy --listen 127.0.0.1:5678 --wait-for-client run.py --height 2.0
```

VS Code에서 **Attach local standalone**을 선택하고 F5. wait-for-client는 debugger 연결 전 script가 시작되지 않게 한다. attach 후 실제 breakpoint에 멈추고 z=2인지 확인한다. Continue한 뒤 GUI 창을 직접 닫으면 루프를 끝내고 finally에서 앱 자원을 정리한다. `--steps`를 지정한 실행은 지정 횟수 후 자동 종료한다.

## Docker

NVIDIA runtime/GPU가 설정된 Isaac Sim 5.1 container에 이 폴더를 `/lesson`로 bind mount하고 포트는 host의 `127.0.0.1:5678`로 게시한다. 기존 container를 사용할 때도 실제 로컬 코드와 mount된 파일이 같아야 한다.

```bash
# 준비된 Isaac Sim container 안에서
cd /isaac-sim
./python.sh -m debugpy --wait-for-client --listen 0.0.0.0:5678 /lesson/run.py --headless --frames 240
```

VS Code의 **Attach Docker**는 localRoot=`${workspaceFolder}`, remoteRoot=`/lesson`로 소스 경로를 대응시킨다. breakpoint가 회색이면 경로 mapping과 같은 파일 버전을 확인한다. container 설치/시작 자체는 별도 필요한 환경이며 여기서 실행하지 않았다.

## 실행 중인 GUI attach

1. Isaac Sim에서 `Window > Extensions`에 `vscode`를 검색하고 **omni.kit.debug.vscode** debugger 확장을 켠다. VS Code interactive code editor extension과 다른 확장이다.
2. debugger Unattached 표시를 확인한다. 기본 host/port는 `127.0.0.1:3000`; 변경 시 `--/exts/omni.kit.debug.python/host=127.0.0.1 --/exts/omni.kit.debug.python/port=3000`과 launch 설정을 맞춘다.
3. VS Code **Attach Isaac Sim 5.1**로 연결한다. Attached 표시를 확인한 뒤 Script Editor에서 이 폴더 `attached_scene.py`를 **파일로 열어 실행**한다. 해당 파일의 print 줄에 둔 breakpoint가 실제로 걸리는지 확인한다.

## 해설/확인

SimulationApp은 Kit 프로세스 자원을 소유하고 반드시 simulator import보다 먼저 시작한다. attach는 기존 프로세스의 Python 실행을 debugger에 연결하는 방식이며 새 앱을 만들지 않는다. `pathMappings`는 원격 filename을 편집기의 동일 소스로 대응시킨다. 한 변수 실험은 height만 바꾸어 입력값→position→USD Transform을 따라가는 것이다. 성공은 프로세스 연결 상태 외에 breakpoint 중단, 변수값, stepping과 실제 Cube 위치 일치다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/tutorial_advanced_python_debugging.html).
