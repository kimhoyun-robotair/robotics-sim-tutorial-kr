# 05. Python 실행 방식: 내 반복문과 앱의 이벤트 루프

권장 학습 순서 **05** · Python 실행 환경과 USD 기초 · 출처 ID `t092`

## 이 실습의 의도

같은 0.4 m 낙하 큐브를 독립 Python과 Script Editor로 실행하여 누가 물리 시간을 전진시키는지 구분한다. 독립 실행은 자신의 `world.step()` 반복문을 사용하고, 대화형 실행은 앱의 이벤트 루프에 제어를 양보하면서 콜백으로 관찰한다. 원문 개념을 확인하도록 추가한 이 예제는 독립 실행의 `timeline.csv`와 대화형 실행의 높이 목록을 남기며, 두 방식의 앱 생성·초기화·종료 책임을 비교한다.

## 실행 후 확인할 것

- 독립 실행에서 `/World/FallingCube`가 Z=2 m에서 내려와 충분한 물리 시간 후 중심 높이 약 0.2 m에 놓이는지 확인한다. 강체와 충돌이 모두 있는 큐브이므로 공중에 계속 머무는 장면이 목표는 아니다.
- `--steps 120`을 끝까지 실행한 `timeline.csv`의 `loop_iteration`, `physics_callbacks`, `simulated_time_s`를 비교한다. 기본 1/60초 간격에서 반복과 콜백이 120회이고 누적 물리 시간이 약 2초인지 확인한다. 이 시간은 앱 시작이나 렌더링에 걸린 실제 시간이 아니다.
- Script Editor 실행은 물리 콜백으로 `(dt, 높이)`를 수집해 콘솔의 `Interactive callback samples`로 출력하고 타임라인을 일시정지해야 한다. 종료 판단은 앱 업데이트 120회가 아니라 물리 관찰이 120개 이상 모였는지에 따른다.
- 대화형 task가 기다리는 동안 GUI가 반응하는지 확인한다. 수동 Pause를 누르면 샘플 수집이 멈춰 출력이 아직 나오지 않을 수 있으며, Play를 재개하면 이어진다. 이 경로는 CSV를 만들거나 GUI 앱을 닫지 않는다.

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 순서대로 실습

1. 이 폴더에서 `~/isaacsim/python.sh run.py`를 실행한다. 화면이 필요 없으면 `--headless`를 추가한다.
2. `run.py`의 `SimulationApp` 생성 전후 import를 비교한다. 옵션 읽기는 앱 없이 가능하지만 `omni`와 Core API는 Kit가 로드되어야 한다.
3. `World`가 미터 단위 장면과 1/60초 물리 간격을 만들고, 지면과 높이 2 m의 큐브를 등록하는 부분을 찾는다.
4. `world.reset()` 후 물리 콜백을 등록한다. 별도로 `--steps 120`을 지정해 실행하고 콜백의 `dt`를 누적한 시간이 약 2초인지 `timeline.csv`에서 확인한다. 실제 실행에 걸리는 벽시계 시간과 구분한다.
5. GUI를 새로 실행하고 **File > New > Window > Script Editor** 순서로 작업 공간을 연다. `script_editor.py` 전체를 붙여 넣어 실행한다. 초기화는 `await reset_async()`로 진행한다.
6. 자동으로 재생되어 120개 이상의 물리 콜백을 수집하고 멈추는지 확인한다. 앱 업데이트 한 번에 여러 물리 단계가 진행되면 정확히 120개보다 많을 수 있다. 스크립트가 앱의 `next_update_async()`에 제어를 양보하기 때문에 UI도 계속 반응한다.
7. 콜백 수집 후에는 `remove_physics_callback`으로 자기 콜백만 제거한다. 대화형 실습 재실행은 새 GUI 인스턴스에서 한다.

## API와 개념 해설

`Stage`는 객체와 속성을 담는 USD 문서다. `/World/FallingCube`는 객체의 Prim 경로다. `DynamicCuboid`는 시각 도형에 질량·강체·충돌을 함께 만든다. `World`는 초기화, 물리 시간, 객체 등록을 관리한다. 독립 Python에서 `world.step()`은 물리를 전진시킨다. 대화형 Python에서는 이미 돌아가는 Kit 앱이 스텝을 발생시키므로 콜백에 관찰 동작을 넣는다.

`asyncio.ensure_future`는 앱의 비동기 루프에 일을 예약한다. `await`를 제거하고 긴 반복문을 Script Editor에서 돌리면 앱이 다른 일을 처리할 기회를 잃는다. 비동기 task의 오류는 완료 콜백에서 `task.result()`로 노출한다. 대화형 창에 독립 `run.py`를 붙여 넣어 앱을 중복 생성하지 않는다.

## 한 가지 변수 실험

`--steps 120`으로 제한해 실행한 뒤 `--steps 60`으로 바꾼다. 독립 실행의 물리 시간이 절반이 되는지 CSV로 확인한다. 큐브는 이미 지면에 도달했을 수 있으므로 최종 높이만으로 시간 차이를 판단하지 않는다.

## 문제 해결

`World already exists` 오류는 이전 실습의 World가 살아 있는 경우다. 새 GUI 인스턴스를 연다. Script Editor를 수동 Pause한 경우 콜백 120개를 기다리는 task는 아직 종료하지 않으므로 Play를 다시 누른다. `timeline.csv`의 헤더만 있으면 앱 창을 너무 일찍 닫았는지 확인한다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Python Scripting Concepts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
