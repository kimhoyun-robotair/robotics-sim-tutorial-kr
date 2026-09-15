# 13. Kit Commands와 Registered Actions: 실행·Undo·Redo

권장 학습 순서 **13** · Python 실행 환경과 USD 기초 · 출처 ID `t177`

## 이 실습의 의도

Cube 색을 바꾸는 작은 작업으로 이름 있는 Action 호출과 되돌릴 수 있는 Command의 역할을 구분한다. 등록한 `make_blue` Action 안에서 `ChangeProperty` Command를 실행하여, 색 변경 뒤 Undo/Redo가 실제 USD 속성을 복원하는지 확인한다. 기본 실행은 빨강→파랑→빨강→파랑을 순서대로 읽어 검사한 뒤 `command_history.json`과 최종 `commands.usda`를 저장한다. Action은 Python 프로세스에 등록되는 기능이고 USD 파일의 일부로 저장되지 않는다.

## 실행 후 확인할 것

- `command_history.json`의 `prim_path`로 실제 생성된 큐브를 찾는다. 생성 명령이 경로를 정하므로 `/World/Cube`라는 고정 경로를 기대하지 않는다.
- 보고서의 `before`, `after_action`, `after_undo`, `after_redo`가 각각 `[1,0,0]`, `[0,0,1]`, `[1,0,0]`, `[0,0,1]`인지 확인한다. 코드는 각 단계의 속성을 다시 읽고 이 순서가 다르면 오류를 낸다.
- 화면과 `commands.usda`에서 최종 큐브는 파란색이어야 한다. 네 상태 변경은 표시용 앱 반복문 전에 연속 수행되므로 중간의 빨강·파랑 전환이 눈에 보이지 않아도 정상이다. 중간 상태의 확인 대상은 JSON이다.
- `--steps` 없는 독립 실행 중 Registered Actions에서 `tutorial.commands.local` / `make_blue`를 찾아본다. 프로세스가 끝나면 해제되며, 저장된 USD만 다시 열어서 Action이 생기지 않는 것이 정상이다.
- 수동 Undo/Redo 실습에서는 `ChangeProperty`가 색을 복원하는지 관찰한다. 직접 USD 값을 `Set`한 모든 작업이 같은 이력을 남긴다고 일반화하지 않으며, Action 등록만으로 Undo가 제공되는 것도 아니다.

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py`을 실행한다. 생성된 Cube는 최종적으로 파란색이며 콘솔/JSON에 네 색 상태가 기록된다.
2. `omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")` 반환의 성공 여부와 실제 생성 경로를 확인한다. 자동 생성 이름을 `/World/Cube`로 단정하지 않는다.
3. 최초 빨강 속성을 만든 후 `get_action_registry()`에 `tutorial.commands.local` / `make_blue` action을 등록한다. action ID는 같은 extension ID 안에서 구분된다.
4. action callback은 현재 색을 `prev`에 넣고 `ChangeProperty`를 실행한다. USD 속성을 직접 `Set`하는 것과 달리 이 변경은 Kit command history를 통해 되돌릴 수 있다.
5. `execute_action`, `omni.kit.undo.undo`, `redo` 후 실제 속성을 다시 읽는다. 예상 네 상태와 다르면 코드가 오류를 발생시키므로 단순 성공 문구 출력으로 판정하지 않는다.
6. 앱 업데이트가 끝나면 `finally`에서 자기 action을 deregister한다. extension에서는 같은 정리를 `on_shutdown`에 둔다.

## GUI에서 명령과 action 찾기

1. GUI에서 **Window > Commands**를 연 뒤 **Search Commands**를 누른다. `CreateMeshPrimCommand`와 `ChangeProperty`를 검색하고 매개변수 문서를 확인한다.
2. GUI로 큐브의 색이나 변환을 한 번 바꾸고 Command History에 어떤 명령이 남는지 본다. 모든 직접 USD 변경이 history에 기록되는 것은 아니다.
3. **Utilities > Registered Actions**를 열어 현재 등록된 action 목록을 살펴본다. 확장에 따라 목록이 달라진다. action을 더블클릭하면 즉시 실행되므로 먼저 이름과 설명을 읽는다.
4. 이 패키지 action을 GUI에서 수동으로 실행하려면 `--steps` 없이 독립 실행하고 해당 앱 창의 Registered Actions에서 `tutorial.commands.local`을 찾는다. 코드가 종료되면 등록이 해제된다.
5. 생성된 `commands.usda`를 나중에 다시 열어도 action이 자동으로 재등록되는 것은 아니다. USD 장면 저장과 Python 확장 수명은 별개다.

## API와 개념 해설

Command는 `do`/`undo` 동작을 포함할 수 있는 단위 작업이다. Action은 함수 호출에 이름을 붙여 UI 버튼·단축키·메뉴 등에서 실행하게 하는 등록 기능이다. Action 자체가 undo를 보장하지 않으며 내부에서 undo 가능한 command를 사용했는지가 중요하다. 명령과 action 목록은 활성 확장이 등록하므로 설치/활성화 상태에 따라 변한다.

`Sdf.Path`는 Prim/속성 경로를 표현한다. `color.GetPath()`는 생성된 Prim의 `primvars:displayColor` 속성 경로이며 `ChangeProperty`가 바로 그 속성을 대상으로 한다. 이 예제의 색은 0~1 선형 RGB 값이다.

## 한 가지 변수 실험과 문제 해결

`make_blue`의 목표 색만 `(0,1,0)`으로 바꾸면 검증의 기대 순서도 **요구한 초록 동작에 맞게** 함께 바꿔야 한다. 변경 전후의 JSON과 undo 결과를 직접 비교한다. 명령을 찾지 못하면 **Window > Extensions**에서 mesh primitive/command 관련 확장 활성 여부를 확인한다. 액션이 안 보이면 독립 프로세스가 이미 종료했는지 확인한다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Commands](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/omniverse_tools.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
