# 103. t086 · CortexWorld를 앱 extension으로 실행하기

권장 학습 순서 **103** · 환경 구축과 로봇 행동 · 출처 ID `t086`

`extension/`에는 `KR Cortex World Lab`이라는 작은 **실제 Kit extension**을 포함했다. LOAD/RESET 비동기 lifecycle, CortexWorld 생성, physics callback, 두 손끝 target 전환을 구현한다. 공식 문서가 설명하는 큰 Franka/UR10 GUI 예제도 아래에서 별도로 실습한다. 외부 standalone process를 GUI 버튼으로 실행하는 방식이 아니다.

## 이 실습의 의도

실행 중인 Isaac Sim 앱 안에서 UI 버튼, 비동기 World 초기화, Cortex physics callback을 연결하는 최소 extension 구조를 배운다. Franka의 두 목표는 y만 다르게 두어 같은 behavior의 command parameter 변경이 실제 손끝 운동으로 이어지는지 확인하도록 했다. 확장을 켜면 UI만 생기고 LOAD NEW WORLD가 장면과 행동을 만드는 구조지만, 현재 로컬 구현에는 아래에 설명한 context reset 결함이 있다. 로컬 목표 전환과 뒤에서 다루는 공식 GUI의 behavior 교체는 별도 관찰 대상이다.

## 실행 후 확인할 것

- **현재 LOAD 제한:** 아래 결함이 남은 로컬 구현은 network 등록 중 `NotImplementedError`로 중단될 수 있다. 창이나 Franka가 보이더라도 로드 완료가 아니다. 수정 후 기대 기준은 `Running: left target` 문구와 `(0.5,0.25,0.5)`를 향하는 실제 손끝 운동이다. 아래 로컬 목표·RESET 확인도 이 초기화가 완료된 상태를 전제로 한다.
- **목표 버튼:** TARGET RIGHT는 `(0.5,-0.25,0.5)`, TARGET LEFT는 `(0.5,0.25,0.5)`를 명령한다. `Goal: [...]` 상태 문구뿐 아니라 손끝의 y 방향 이동도 확인한다. LOAD 전 목표 버튼은 context가 없어 동작하지 않는다.
- **RESET 의미:** 목표를 오른쪽으로 바꾼 뒤 RESET하면 `Reset complete`와 재생 재시작을 확인한다. reset 함수는 목표 값을 왼쪽으로 다시 쓰지 않으므로 마지막으로 선택한 목표를 계속 사용한다. 이미 로드한 상태에서 LOAD를 다시 누르면 같은 reset 경로를 실행한다.
- **비동기 상태:** LOAD/RESET 작업 중 중복 클릭은 pending 작업이 끝날 때까지 무시된다. 새 세션이 아닌 곳에 기존 World가 있으면 `Failed: ... existing World ...`가 나타나는 것은 중복 World 생성을 막는 조건이다.
- **확장 종료:** 초기화가 완료되어 `kr_cortex_step` callback이 등록된 상태에서 확장을 끄면 해당 callback을 제거하고 world를 Pause한다. LOAD가 그 전에 실패한 경우에는 이 정리 분기를 실행하지 않는다. Stage에 Franka와 지면이 남는 것은 정상이며 이 shutdown은 장면 삭제 기능이 아니다.
- **공식 GUI 비교:** Robotics Examples의 Cortex 예제에서는 START 뒤 behavior dropdown을 바꿔 집기/peck 정책 자체가 바뀌는지 별도로 본다. 로컬 LEFT/RIGHT 버튼의 좌표 전환만으로 policy hot swap을 검증한 것은 아니다.

## 현재 코드에서 확인된 제한

`extension/kr_cortex_lab/__init__.py`는 `DfRobotApiContext(robot)`를 직접 생성한다. 설치된 5.1 SDK의 이 클래스에는 `reset()` 구현이 없고, 상속한 `DfLogicalState.reset()`은 `NotImplementedError`를 낸다. `CortexWorld.add_decider_network()`가 즉시 `reset_cortex()`를 호출하면서 이 reset에 도달하므로 LOAD가 정상 완료되려면 reset을 구현한 context가 필요하다. 이는 버튼 사용 순서로 해결되는 정상 대기가 아닌 **별도 코드 수정이 필요한 제한**이다. 이 문서 수정에서는 코드를 변경하거나 GPU 실행으로 재현하지 않았으며, 아래 절차는 의도한 동작을 확인할 기준으로 남긴다.

## 로컬 extension 실행

1. 새 Isaac Sim 5.1 세션을 연다. 이 실습은 새 stage를 만들므로 먼저 진행 중인 장면을 Save As한다.
2. `Window > Extensions`의 설정에서 Extension Search Paths에 이 패키지의 **extension 절대 경로**를 추가한다. `KR Cortex World Lab`을 검색하여 활성화한다. manifest는 `extension/config/extension.toml`, Python module은 `kr_cortex_lab`이다.
3. 나타난 `KR Cortex World Lab` 창에서 LOAD NEW WORLD를 누른다. Franka와 ground가 생기고 자동 Play하여 왼쪽 목표로 이동한다. 기존 Core/Cortex World singleton이 있는 세션이면 코드가 오류를 내므로 새 세션에서 실행한다.
4. TARGET RIGHT, TARGET LEFT를 눌러 손끝의 y=−0.25/0.25 전환을 관찰한다. 두 target의 x=0.5, z=0.5는 동일하다.
5. RESET을 누른 뒤 동작 재시작을 확인한다. extension을 꺼서 physics callback이 제거되는지 확인한다. 기존 world 데이터 자체를 자동 삭제하는 기능은 아니다.

## extension API 읽기

`omni.ext.IExt.on_startup()`은 UI를 만들고, callback은 `asyncio.ensure_future()`로 비동기 LOAD를 예약한다. 중복 버튼 클릭은 진행 중 task가 끝날 때까지 무시한다. `create_new_stage_async()` 뒤 `CortexWorld.initialize_simulation_context_async()`로 물리 context를 만들고 `add_robot()`과 `add_decider_network()`를 등록한다.

`DfRobotApiContext`는 robot과 목표를 제공하며 `Reach.step()`은 매 cycle `robot.arm.send_end_effector()`를 보낸다. 물리 callback의 `world.step(False, False)`는 **이미 앱이 진행시킨 물리 step 안에서** Cortex 논리/명령만 처리한다. 여기서 다시 physics를 진행하면 이중 step이 될 수 있다. standalone 방식처럼 또 다른 `SimulationApp`을 생성하지 않는다. shutdown은 작업을 취소하고 자신이 등록한 callback만 제거한다.

## 원문 Franka/Cortex GUI와 hot swap

1. `Window > Examples > Robotics Examples`를 열고 `Cortex > Franka Cortex Examples`를 선택한다. 설치본 파일은 `exts/isaacsim.examples.interactive/isaacsim/examples/interactive/franka_cortex/franka_cortex_extension.py`이다.
2. behavior dropdown에서 block stacking을 선택하고 LOAD, START를 누른다. Diagnostic monitor의 decision stack과 task 진단을 읽는다.
3. 실행 중 dropdown을 peck game 등 다른 behavior로 바꾼다. 새 behavior가 기존 로봇에 적용되는지 확인한다. 본 로컬 extension의 target 변경은 command parameter 변경이며, 이 native dropdown은 **behavior policy hot swap**이라는 차이가 있다.
4. 초기화는 RESET 버튼을 쓴다. Stop 후 Play만 눌러 world reset을 기대하면 원문이 지적하는 상태 불일치가 생길 수 있다.
5. 다른 새 세션에서 `Cortex > UR10 Palletizing`을 열고 LOAD → START PALLETIZING을 누른다. Diagnostics에서 decision stack, attachment, flip 여부를 관찰한다. source는 같은 interactive extension 아래 `ur10_palletizing/ur10_palletizing_extension.py`다.

공식 문서의 `CortexBase.load_world_async()`는 일반 BaseSample의 World를 CortexWorld로 바꾸는 지점이다. 이 작은 extension은 그 lifecycle을 직접 드러내는 학습용 구현이며 네이티브 UI 전체를 복제하지 않았다. 한 변수 실험은 로컬 `set_goal`의 y 값 하나만 바꿔 이동 범위를 비교하는 것이다. 성공은 UI load/reset 및 실제 command 반응이며 창이 뜨는 것만으로 로봇 동작을 검증하지 않는다.

## 독립 실행과 출처

이 폴더만 복사해 사용할 수 있다. Isaac Sim **5.1.0**, 지원 NVIDIA RTX GPU/드라이버와 GUI 세션이 필요하다. NVIDIA asset browser를 사용하는 단계는 5.1 자산 또는 해당 Digital Twin dataset에 접근할 수 있어야 한다. 명시한 extension이 검색되지 않으면 설치/registry 연결 상태부터 확인한다. 이 패키지는 다른 로컬 튜토리얼이나 공통 모듈을 요구하지 않는다.

앱 실행은 `"$HOME/isaacsim/isaac-sim.sh"`로 하고 설치 위치가 다르면 경로를 바꾼다. USD Stage는 전체 장면이고 prim은 장면 트리의 객체다. reference는 외부 USD를 합성하며 transform은 parent 기준의 위치·회전·스케일이다. 저장은 패키지의 새 `output/` 경로에 Save As하고 원본/기존 결과를 덮어쓰지 않는다.

[Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_7_cortex_extension.html)의 하위 workflow를 위 순서에 모았다. 이 문서는 한국어 독립 실습이며 공식 GUI를 실행하는 방식과 로컬 보조 artifact를 구분해 설명한다. 작성 시 로컬 파일/문법만 확인했고 실제 GPU·GUI 상호작용 및 외부 service는 실행하지 않았다. `tutorial.json`의 검증 상태는 `not_run`이다.
