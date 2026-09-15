# 04. Omniverse Script Editor

권장 학습 순서 **04** · Python 실행 환경과 USD 기초 · 출처 ID `t090`

Script Editor의 탭들이 같은 Python 환경을 공유한다는 점을 Cube 생성과 크기 변경으로 확인한다.

## 이 실습의 의도

첫 탭에서 만든 USD 큐브를 두 번째 탭의 `cube` 변수로 그대로 편집하여, Script Editor 탭 사이의 Python 상태 공유를 익힌다. 생성과 변경을 두 파일로 나눈 이유는 다시 장면을 만들지 않고 기존 Prim 속성을 바꿀 수 있음을 보여주기 위해서다. 기본 실습은 실행 중인 GUI에서 도형을 작성·수정하며, 강체나 물리 시뮬레이션은 추가하지 않는다.

## 실행 후 확인할 것

- 새 Stage에서 `tab1_create.py`를 Run한 뒤 Stage의 `/World/EditorCube`를 선택한다. 푸른 큐브가 Z=0.5에 있고 출력이 `created /World/EditorCube size 0.5`인지 확인한다.
- 다른 탭에서 `tab2_resize.py`를 Run하면 같은 큐브의 크기가 커지고 콘솔에 `before 0.5`, `after 1.0`이 나와야 한다. Stage에 큐브가 하나 더 생기는 동작은 이 실습의 목표가 아니다.
- 두 번째 탭에서 재실행하면 이미 변경된 값 때문에 `before`도 `1.0`이다. 첫 실행의 숫자를 기대하려면 새 Stage에서 첫 탭부터 다시 진행한다.
- Play를 눌러도 큐브가 떨어지지 않는 것이 정상이다. Size 속성 편집만 수행했으며 강체·충돌 속성을 붙이지 않았다. 첫 탭 재실행의 `already exists` 오류도 같은 경로의 중복 생성을 막는 보호다.

## 실행 환경

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더를 어디로 복사해도 다른 로컬 튜토리얼 없이 실행한다. 아래처럼 시작한 뒤 **Window > Script Editor**를 연다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Script Editor의 **File > Open**으로 본문의 Python 파일을 열고 **Run**을 누른다. 이 코드는 이미 실행 중인 Kit 안에서 동작하므로 별도의 `SimulationApp`을 만들지 않는다. 일반 시스템 `python3`에서 실행하는 파일이 아니다. Stage는 현재 USD 장면, prim은 장면의 경로로 식별되는 요소다. 같은 파일을 재실행할 때 기존 결과를 삭제하거나 덮어쓰지 않도록 해당 prim이 있으면 에러를 내는 예제를 사용한다.

## 실습

1. 새 Stage에서 `tab1_create.py`를 열고 Run한다. `/World/EditorCube`를 선택해 `F`로 관찰한다.
2. Script Editor의 **Tab** 메뉴로 새 탭을 만들고 `tab2_resize.py`를 연다. 첫 탭의 `cube` 변수를 재import 없이 사용한다.
3. 두 번째 탭을 Run한다. 출력의 before는 `0.5`, after는 `1.0`이고 화면 Cube가 커져야 한다.
4. 새 Stage를 열면 이전 Python 변수는 남아 있어도 그 prim이 현재 Stage에 있다는 뜻은 아니다. 첫 탭을 다시 실행하여 새 prim을 만들어야 한다.

`UsdGeom.Cube`는 typed schema wrapper, `GetSizeAttr().Set`은 USD attribute 편집이다. 변수를 탭에서 공유하는 것은 디스크 모듈 공유와 다르며 앱을 종료하면 사라진다. File > Save As로 작업 코드를 저장하고, 장면 저장은 별도로 수행한다.

한 변수 실험: tab2의 목표 크기 `1.0`만 `0.25`로 바꾼다. 성공은 출력 숫자와 실제 크기 변화가 일치하는 것이다. `NameError: cube`는 tab1을 아직 실행하지 않은 상태다. `already exists`이면 같은 Stage에 두 번째 Cube를 만드는 대신 tab2를 실행한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html).
