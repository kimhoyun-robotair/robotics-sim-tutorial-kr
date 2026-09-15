# 103. t086 · CortexWorld를 앱 extension으로 실행하기

권장 학습 순서 **103** · 환경 구축과 로봇 행동 · 출처 ID `t086`

`extension/`에는 `KR Cortex World Lab`이라는 작은 **실제 Kit extension**을 포함했다. LOAD/RESET 비동기 lifecycle, CortexWorld 생성, physics callback, 두 손끝 target 전환을 구현한다. 공식 문서가 설명하는 큰 Franka/UR10 GUI 예제도 아래에서 별도로 실습한다. 외부 standalone process를 GUI 버튼으로 실행하는 방식이 아니다.

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
