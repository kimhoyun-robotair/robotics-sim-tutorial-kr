# 163. 환경을 복제하는 Cloner

권장 학습 순서 **163** · 병렬 환경과 학습 정책 활용 · 출처 ID `t005`

동일한 낙하 상자를 4개의 환경으로 복제하고 모든 상자의 포즈를 배열 하나로 읽고 수정합니다. 공식 Script Editor 예제를 독립 실행 프로그램으로 옮겼으며, `Cloner`, `GridCloner`, 일괄 포즈 처리, physics replication과 충돌 필터를 모두 실습합니다.

## 이 실습의 의도

낙하 상자 하나를 환경 단위로 복제하고 모든 상자의 위치를 한 배열로 읽고 바꾸는 흐름을 익힙니다. 기본은 파란 상자 네 개를 격자에 놓고 공통 바닥은 공유하며, `--layout line`, `--copy`, `--replicate-physics`로 배치·USD 속성 공유·물리 생성 방식을 각각 비교합니다. 이 코드는 실제 물리 step을 진행하지만 기본 환경 간격이 넓어서 화면의 낙하만으로 환경 간 충돌 필터의 효과나 복제 성능 향상까지 입증할 수는 없습니다.

## 실행 후 확인할 것

- **복제된 대상:** Stage에서 `/World/envs/env_0`부터 요청한 개수의 환경까지 각 `cube`가 하나씩 있는지 확인합니다. 기본 상자는 한 변 0.5 m이고 바닥 `/World/defaultGroundPlane`은 환경 밖에서 공유됩니다.
- **배치와 기록 수:** 실행 종료 후 `poses.json`의 `paths`, `initial_positions_m`, `final_positions_m` 행 수가 모두 `--count`인지 확인합니다. line 모드의 X 간격은 `--spacing`, Y는 0이며 grid 모드는 격자 배치입니다. 초기 배열은 코드에서 일괄 Z 이동을 적용하고 `world.reset()`한 뒤 읽은 값입니다.
- **낙하와 접촉:** 충분히 진행했을 때 final Z가 initial Z보다 낮아지고, 바닥에서 안정된 상자 중심이 대략 0.25 m인지 화면과 숫자로 확인합니다. 짧은 `--steps`는 낙하 중에 끝날 수 있습니다. [RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 60스텝 final Z 약 0.56 m는 해당 시점의 예이며 접촉 안정 높이나 모든 실행의 정답이 아닙니다.
- **복사 방식:** 기본 `copy_from_source=false`와 `--copy` 실행의 `cloned_scene.usda` 구성을 비교합니다. 기본 Inherits에서는 원본 cube 색 수정이 clone에 전달되는지, copy 모드에서는 독립적으로 남는지 관찰합니다.
- **물리 복제·충돌 범위:** `poses.json`에서 요청한 `replicate_physics`가 기록됐는지 확인하고, Stage의 `/World/collisionGroups`가 환경별 그룹과 공통 바닥을 참조하는지 봅니다. 이 플래그의 기록만으로 물리 성능이나 환경 간 충돌 차이를 검증한 것은 아닙니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

외부 로봇 자산은 필요 없습니다.

터미널에서 이 패키지 폴더(`163_motion_cloner`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --layout grid --count 4
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --layout line --count 4
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --replicate-physics --count 16
```

`--steps`는 물리 스텝 수(USD 전용 예제에서는 화면 업데이트 수)입니다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 계속됩니다. `--steps 600`처럼 양수를 지정하면 해당 횟수 후 종료하며, `--headless`에서 생략하면 기존 기본값인 600회로 제한됩니다. 각 실행 결과는 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. 기본 실행 후 Stage에서 `/World/envs/env_0`부터 `env_3`까지 펼칩니다. 각 환경에는 `cube` 하나가 있습니다. 바닥과 PhysicsScene은 환경 밖에서 공유됩니다.
2. `GridCloner(spacing=3)`는 환경 원점을 격자로 배치합니다. `--layout line`에서는 `Cloner.clone(positions=...)`에 `[0,0,0]`, `[3,0,0]`, `[6,0,0]`, `[9,0,0]`을 직접 전달합니다.
3. 코드의 `XFormPrim('/World/envs/env_.*/cube')`가 네 상자를 하나의 view로 잡는 부분을 찾습니다. `get_world_poses()`의 위치 배열은 `(N,3)`, 회전 배열은 `(N,4)`이며 quaternion 순서는 **w,x,y,z**입니다. 모든 z에 1.5 m를 더한 뒤 `set_world_poses()`로 적용합니다.
4. 상자가 바닥에 떨어져 안정될 만큼 진행한 후 `poses.json`의 초기/최종 z를 비교합니다. 안정된 한 변 0.5 m 상자는 바닥 위에서 중심이 대략 0.25 m에 있어야 하며, 짧은 실행은 그 높이에 도달하기 전에 끝날 수 있습니다. 물리 오차를 고려하여 정확한 문자열 일치 대신 수치와 화면을 비교합니다.
5. `--copy`를 넣어 실행하고 `cloned_scene.usda`에서 inherit 구성이 사라지는지 비교합니다. GUI에서 원본 `env_0/cube`의 displayColor를 수정하면 기본 Inherits 구성은 다른 clone에도 전달됩니다. `--copy` 결과에서는 독립적입니다.
6. `--replicate-physics`로 복제를 반복합니다. `define_base_env('/World/envs')`와 `generate_paths()`를 먼저 호출하여 replication에 필요한 공통 조상과 순차 접미사를 명확히 합니다. 실행 중 마찰/재질/shape 속성을 바꾸는 실험은 replication을 끈 상태로 합니다.

## 개념과 API

USD Stage는 장면 문서이며 prim은 `/World/envs/env_0/cube`처럼 경로로 식별되는 항목입니다. Xform은 위치·회전·크기를 가진 좌표계입니다. **USD Inherits**는 원본의 속성 의견을 공유하지만 일반 복사는 이후 원본 변경을 전달하지 않습니다. `copy_from_source`의 두 모드를 선택하는 이유입니다.

`replicate_physics=True`는 USD 복사와 별도로 PhysX의 파싱/환경 생성을 복제하는 최적화입니다. instanceable mesh와 서로 다른 기능입니다. `filter_collisions('/physicsScene', '/World/collisionGroups', paths, global_paths=[...])`는 서로 다른 환경 간 충돌을 걸러내면서 공통 바닥과의 충돌을 유지합니다. 이 예제는 환경들이 떨어져 있으므로 기본 화면만으로 필터 효과를 입증할 수는 없습니다. 필터 구성을 확인한 뒤 환경 간격을 줄이는 후속 실험이 필요합니다.

5.1 문서 일부는 `XFormPrimView`라는 이전 이름을 보여 줍니다. 설치된 5.1 API의 복수 prim 클래스 `XFormPrim`을 사용합니다. 이 클래스의 정규식과 단일 prim 클래스 `SingleXFormPrim`을 혼동하지 않습니다.

## 한 변수 실험

`--spacing 3`만 `--spacing 1`로 바꾸어 배열을 더 조밀하게 만듭니다. 로봇 정책 학습은 포함하지 않으며 복제된 환경에서 관측을 모을 기초를 구현합니다.

## 문제 해결

`XFormPrimView` import 오류는 오래된 코드의 클래스 이름을 확인합니다. 환경 안의 shape 속성을 runtime에 바꿔야 한다면 replication을 끕니다. clone 수가 많은 경우 GPU/메모리 제한을 고려해 `--count 4`로 먼저 확인합니다. 바닥이 없다면 global collision 경로와 Stage의 실제 바닥 prim 경로가 같은지 확인합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 앞의 **실행 후 확인할 것** 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 제한된 실행 루프와 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
