# 04. Omniverse Script Editor

권장 학습 순서 **04** · Python 실행 환경과 USD 기초 · 출처 ID `t090`

Script Editor의 탭들이 같은 Python 환경을 공유한다는 점을 Cube 생성과 크기 변경으로 확인한다.

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

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/omniverse_script_editor.html).
