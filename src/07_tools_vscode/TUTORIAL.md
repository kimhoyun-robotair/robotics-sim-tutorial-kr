# 07. Visual Studio Code (VS Code)

권장 학습 순서 **07** · Python 실행 환경과 USD 기초 · 출처 ID `t088`

VS Code에서 열린 파일을 실행 중인 Isaac Sim으로 보내 파란 Cube를 만든다. 공식 IDE 연결 기능의 실습이며 코드는 이 폴더에 들어 있다.

## 이 실습의 의도

VS Code의 Isaac Sim 전용 Run 명령이 실행 중인 GUI의 Kit Python 환경에서 코드를 수행한다는 것을 확인한다. `scene.py`는 큐브 하나와 `cube` 변수를 만들고, 이어서 선택 영역을 실행해 같은 앱의 장면과 변수에 다시 접근하도록 구성했다. 기본 실습의 결과는 활성 Stage의 USD 도형과 VS Code 출력이며, 별도 standalone 앱이나 물리 시뮬레이션을 시작하지 않는다.

## 실행 후 확인할 것

- VS Code의 전용 Run을 누른 뒤 Isaac Sim Stage에 `/World/EditorCube`가 생겼는지 확인한다. Prim을 선택해 `F`를 누르면 푸른 큐브가 보이고 Property의 Size는 0.5, 위치 Z는 0.5여야 한다.
- **Isaac Sim VS Code Edition output**에 `created /World/EditorCube size 0.5`가 출력되는지 확인한다. 로컬 터미널에서 파일 실행이 끝났다는 메시지보다 실제 연결된 Stage와 출력을 함께 확인하는 것이 기준이다.
- 같은 연결에서 `print(cube.GetPath())`를 **Run selected text**로 실행했을 때 `/World/EditorCube`가 출력되어야 한다. 이로써 후속 실행이 기존 Python 상태에 접근함을 확인한다.
- Play를 눌러도 큐브는 낙하하지 않는다. `scene.py`는 USD 도형만 만들며 강체·충돌을 추가하지 않는다. 같은 Stage에서 전체 파일을 다시 실행할 때의 `already exists` 오류는 중복 생성 보호이므로 새 Stage에서 실험을 반복한다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 연결과 실행

1. VS Code를 설치하고 Extensions에서 **Isaac Sim VS Code Edition**(`NVIDIA.isaacsim-vscode-edition`)을 설치·활성화한다. Python 파일 편집/디버깅에는 Microsoft Python/Python Debugger 확장도 사용한다.
2. Isaac Sim의 `Window > Extensions`에서 **isaacsim.code_editor.vscode**를 검색해 Enabled를 켠다. `Window > VS Code`는 설치 폴더를 VS Code로 여는 메뉴다.
3. VS Code에서 이 폴더의 `scene.py`를 연다. Activity Bar의 Isaac Sim 로고를 눌러 **Commands > Run**을 선택한다. 일반 Python 실행 버튼과 구분한다.
4. Isaac Sim Stage에서 `/World/EditorCube`를 선택해 `F`를 누른다. VS Code의 **Isaac Sim VS Code Edition output**에 크기 `0.5`가 출력되는지 확인한다.
5. 편집기의 새 파일/선택 영역에 `print(cube.GetPath())`를 적고 **Run selected text**로 실행한다. 같은 실행 중인 Kit에 변수가 남아 있음을 관찰한다.

## API와 VS Code 설정

`omni.usd.get_context().get_stage()`는 활성 USD Stage를 가져온다. `UsdGeom.Cube.Define`은 USD Cube prim을 만들고 `AddTranslateOp`는 미터 단위 위치 변환을 추가한다. geometry를 만들었다고 물리 Rigid Body가 자동 추가되는 것은 아니다.

Isaac Sim 설치의 `.vscode/launch.json`에는 **Python: Current File**(standalone), **Python: Attach**(실행 중인 앱), Linux 앱 시작 구성이 있다. `settings.json`의 interpreter/`python.analysis.extraPaths`는 Kit Python 및 extension import 경로를 알려준다. `tasks.json`의 `setup_python_env`는 `setup_python_env.sh`를 source한 환경을 디버거 env 파일에 저장한다. interactive 연결에는 그 standalone task를 실행할 필요가 없다. extension 안에서 실행할 코드를 Current File로 실행하면 Kit context가 없다.

한 변수 실험: 새로운 Stage에서 `CreateSizeAttr(0.5)`만 `1.0`으로 변경하여 Run한다. 관찰 기준은 실제 Cube 크기와 output 값이다. 서버 미연결이면 양쪽 확장 활성 상태와 VS Code 연결 주소를 확인한다. `already exists`는 재실행 보호이므로 새 Stage에서 다시 시도한다.

- [공식 VS Code 확장](https://marketplace.visualstudio.com/items?itemName=NVIDIA.isaacsim-vscode-edition).

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/vscode.html).
