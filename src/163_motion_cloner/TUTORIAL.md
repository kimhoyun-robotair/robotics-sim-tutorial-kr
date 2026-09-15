# 163. 환경을 복제하는 Cloner

권장 학습 순서 **163** · 병렬 환경과 학습 정책 활용 · 출처 ID `t005`

동일한 낙하 상자를 4개의 환경으로 복제하고 모든 상자의 포즈를 배열 하나로 읽고 수정합니다. 공식 Script Editor 예제를 독립 실행 프로그램으로 옮겼으며, `Cloner`, `GridCloner`, 일괄 포즈 처리, physics replication과 충돌 필터를 모두 실습합니다.

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
4. 상자가 바닥에 떨어진 후 `poses.json`의 초기/최종 z를 비교합니다. 한 변 0.5 m인 상자는 바닥 위에서 중심이 대략 0.25 m에 있어야 합니다. 물리 오차를 고려하여 정확한 문자열 일치 대신 수치와 화면을 비교합니다.
5. `--copy`를 넣어 실행하고 `cloned_scene.usda`에서 inherit 구성이 사라지는지 비교합니다. GUI에서 원본 `env_0/cube`의 displayColor를 수정하면 기본 Inherits 구성은 다른 clone에도 전달됩니다. `--copy` 결과에서는 독립적입니다.
6. `--replicate-physics`로 복제를 반복합니다. `define_base_env('/World/envs')`와 `generate_paths()`를 먼저 호출하여 replication에 필요한 공통 조상과 순차 접미사를 명확히 합니다. 실행 중 마찰/재질/shape 속성을 바꾸는 실험은 replication을 끈 상태로 합니다.

## 개념과 API

USD Stage는 장면 문서이며 prim은 `/World/envs/env_0/cube`처럼 경로로 식별되는 항목입니다. Xform은 위치·회전·크기를 가진 좌표계입니다. **USD Inherits**는 원본의 속성 의견을 공유하지만 일반 복사는 이후 원본 변경을 전달하지 않습니다. `copy_from_source`의 두 모드를 선택하는 이유입니다.

`replicate_physics=True`는 USD 복사와 별도로 PhysX의 파싱/환경 생성을 복제하는 최적화입니다. instanceable mesh와 서로 다른 기능입니다. `filter_collisions('/physicsScene', '/World/collisionGroups', paths, global_paths=[...])`는 서로 다른 환경 간 충돌을 걸러내면서 공통 바닥과의 충돌을 유지합니다. 이 예제는 환경들이 떨어져 있으므로 기본 화면만으로 필터 효과를 입증할 수는 없습니다. 필터 구성을 확인한 뒤 환경 간격을 줄이는 후속 실험이 필요합니다.

5.1 문서 일부는 `XFormPrimView`라는 이전 이름을 보여 줍니다. 설치된 5.1 API의 복수 prim 클래스 `XFormPrim`을 사용합니다. 이 클래스의 정규식과 단일 prim 클래스 `SingleXFormPrim`을 혼동하지 않습니다.

## 관찰 기준과 한 변수 실험

`poses.json`의 paths/초기/최종 위치 행 수가 `--count`와 같고, x/y 배치가 선택한 layout에 맞아야 합니다. `--spacing 3`만 `--spacing 1`로 바꾸어 배열을 더 조밀하게 만듭니다. 로봇 정책 학습은 포함하지 않으며 복제된 환경에서 관측을 모을 기초를 구현합니다.

## 문제 해결

`XFormPrimView` import 오류는 오래된 코드의 클래스 이름을 확인합니다. 환경 안의 shape 속성을 runtime에 바꿔야 한다면 replication을 끕니다. clone 수가 많은 경우 GPU/메모리 제한을 고려해 `--count 4`로 먼저 확인합니다. 바닥이 없다면 global collision 경로와 Stage의 실제 바닥 prim 경로가 같은지 확인합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 제한된 실행 루프와 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
