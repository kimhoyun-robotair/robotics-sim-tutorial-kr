# 163. 낙하 상자 하나를 여러 환경으로 복제하기

## 이번에 배우는 것

**상자가 있는 환경을 네 개로 복제하고, 모든 상자의 위치를 배열 하나로 읽고 바꿉니다.**

병렬 환경에서는 같은 구조를 여러 곳에 만들고 각 환경의 상태를 함께 읽어야 합니다. Cloner는 환경 계층을 복제하고, 여러 Prim을 묶은 view는 그 안의 물체를 한 번에 다룹니다. 이번에는 상자 낙하를 이용해 복제·배치·일괄 관찰을 연결합니다.

| 선택 | 기본값 | 바뀌는 내용 |
|---|---|---|
| `--layout` | `grid` | 격자 또는 일렬 배치 |
| `--count` | `4` | 환경 개수 |
| `--spacing` | `3.0` m | 환경 원점 사이 간격 |
| `--copy` | 꺼짐 | 원본 속성을 물려받는 구조 대신 독립 복사 |
| `--replicate-physics` | 꺼짐 | 물리 환경 생성에 복제 최적화 사용 |

복제되는 환경에는 한 변 0.5 m의 상자 하나가 있고, 지면은 모든 환경이 공유합니다.

## 1. 격자 환경 네 개 실행하기

Isaac Sim 5.1과 지원 GPU·드라이버가 필요합니다. 외부 자산은 사용하지 않습니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/163_motion_cloner/run.py --layout grid --count 4 --steps 240
```

물리 단계 240회를 수행한 뒤 종료합니다. `--steps`를 빼면 창을 닫을 때까지 진행합니다. `--headless`를 추가하면 화면 없이 실행하고, Headless에서 단계 수를 생략하면 600회로 제한합니다.

결과는 이 폴더의 새 `output/run_*`에 저장합니다. 직접 지정하려면 `--output /절대경로/새폴더`를 사용하세요. 기존 폴더는 덮어쓰지 않습니다.

### 코드에서 볼 부분

```python
cloner = GridCloner(spacing=args.spacing)
cloner.define_base_env('/World/envs')
paths = cloner.generate_paths('/World/envs/env', args.count)
```

`define_base_env()`는 환경들이 들어갈 공통 부모를 정하고, `generate_paths()`는 `env_0`부터 순차적인 경로를 만듭니다. 코드에서는 첫 경로 안에 DynamicCuboid를 만든 뒤 그 환경을 나머지 경로로 복제합니다.

```text
/World/envs/env_0/cube  ← 원본
/World/envs/env_1/cube  ← 복제
/World/envs/env_2/cube  ← 복제
/World/envs/env_3/cube  ← 복제
/World/defaultGroundPlane ← 공통 지면
```

### 실행 결과 확인하기

종료 후 `poses.json`을 열어 다음 내용을 확인합니다.

| 필드 | 확인할 내용 |
|---|---|
| `paths` | 환경 경로 네 개 |
| `initial_positions_m` | 일괄 위치 변경과 reset 후의 실제 초기 좌표 |
| `final_positions_m` | 마지막으로 읽은 물리 진행 후 좌표 |
| `copy_from_source` | `--copy` 선택 상태 |
| `replicate_physics` | 물리 복제 옵션 선택 상태 |

상자가 떨어지면 final Z가 initial Z보다 낮아집니다. 충분히 안정된 상자는 한 변 0.5 m이므로 중심 높이가 약 0.25 m입니다. 짧은 실행은 낙하 도중 끝날 수 있으니 모든 결과를 0.25 m와 비교하지 마세요.

`cloned_scene.usda`에는 복제 계층과 충돌 그룹이 남습니다. 실행 중 실제 숫자는 JSON으로, 배치와 공유 관계는 USD로 읽으면 좋습니다.

## 2. 모든 상자의 위치를 배열로 다루기

### 코드에서 볼 부분

```python
boxes = XFormPrim('/World/envs/env_.*/cube', name='all_boxes')
positions, orientations = boxes.get_world_poses()
positions[:, 2] += 1.5
boxes.set_world_poses(positions, orientations)
```

`env_.*`는 여러 환경 경로를 선택합니다. 위치 배열은 `(N, 3)`, 회전 배열은 `(N, 4)`이며 quaternion 순서는 **w, x, y, z**입니다. `positions[:, 2]`는 모든 행의 Z 열이므로 한 줄로 모든 상자를 1.5 m 올립니다.

이후 `world.reset()`을 수행하고 위치를 다시 읽어 초기 기록을 만듭니다. 따라서 initial 값을 소스 생성 높이만 보고 추측하기보다 **reset 이후 실제 배열**에서 확인합니다. 물리 진행은 반복문의 `world.step(render=not args.headless)`가 담당합니다.

일렬 배치는 좌표를 직접 전달합니다.

```bash
~/isaacsim/python.sh src/163_motion_cloner/run.py --layout line --count 4 --steps 240
```

기본 간격 3 m에서 환경 원점은 `(0,0,0)`, `(3,0,0)`, `(6,0,0)`, `(9,0,0)`입니다. GridCloner가 계산하던 배치를 이번에는 `positions` 배열로 지정하는 차이입니다.

### 공유와 물리 복제 구별하기

기본 `copy_from_source=false`에서는 USD Inherits를 사용합니다. 원본 속성을 물려받는 관계입니다. GUI에서 원본 `env_0/cube`의 색을 바꿨을 때 복제본에 전달되는지 확인하고, `--copy`를 추가한 새 실행과 비교하세요. 독립 복사는 이후 원본 변경을 같은 방식으로 전달하지 않습니다.

`--replicate-physics`는 별도 선택입니다. USD 속성의 공유 여부와 달리 PhysX 환경 생성 비용을 줄이는 복제 기능입니다. 물리 형상이나 재질을 실행 중 바꾸는 실험에서는 이 옵션을 끄고 진행하세요. 같은 네 환경에서 이 옵션만 켜려면 다음 명령을 사용합니다.

```bash
~/isaacsim/python.sh src/163_motion_cloner/run.py --headless --count 4 --steps 240 --replicate-physics
```

새 결과의 `replicate_physics`와 환경 경로 수, 초기·최종 Z를 확인하세요. 로봇을 더 만드는 옵션은 `--count`이며 물리 복제 옵션 자체가 개체 수를 늘리지는 않습니다.

```python
cloner.filter_collisions('/physicsScene', '/World/collisionGroups', paths,
                         global_paths=['/World/defaultGroundPlane'])
```

이 호출은 서로 다른 환경 간 충돌을 걸러내면서 공통 지면과의 충돌은 유지하도록 구성합니다. 기본 배치는 멀리 떨어져 있어 필터가 없어도 상자가 서로 닿지 않습니다. 따라서 낙하 화면만으로 충돌 필터의 효과를 입증할 수는 없습니다.

## 3. 복제와 일괄 관찰의 역할 정리

```text
원본 환경 생성 → Cloner로 여러 경로에 복제
             → GridCloner 또는 positions로 배치
             → XFormPrim으로 모든 cube 선택
             → 위치 배열 수정 → reset → 물리 진행 → 최종 배열 기록
```

`--copy`는 USD 변경 전파를, `--replicate-physics`는 물리 환경 생성을, `filter_collisions()`는 환경 사이 접촉 범위를 다룹니다. 옵션 이름이 모두 복제와 관련 있어도 바꾸는 대상은 서로 다릅니다.

## 4. 간단한 확인 실험

일렬 실행에서 `--spacing 3`만 `--spacing 1`로 바꿔 보세요.

- X 좌표가 0, 1, 2, 3 m 간격으로 배치되는지 확인합니다.
- 상자 수와 상자 크기는 유지됩니다.
- 간격이 달라져도 공통 지면 위 안정 높이는 비슷해야 합니다.

이 실험은 배치 옵션을 확인합니다. 1 m 간격에도 상자끼리 닿지 않으므로 충돌 필터 성능 실험으로 해석하지 않습니다.

## 실행할 때 막히면

- **`XFormPrimView` import 오류**: 이 파일은 5.1의 복수 Prim 클래스 `XFormPrim`을 사용합니다. 과거 예제 이름과 섞지 마세요.
- **최종 Z가 0.25 m보다 큼**: 낙하 중 끝났을 수 있습니다. 초기·최종 좌표와 실행 길이를 함께 확인하세요.
- **상자가 지면을 통과함**: 실제 지면 경로가 `global_paths`와 같은지, 충돌 그룹이 올바른지 조사하세요.
- **결과 JSON이 아직 없음**: 루프 종료 후 작성합니다. 유한한 `--steps`를 쓰거나 창을 닫으세요.
- **많은 환경에서 메모리 부족**: `--count 4`로 기본 배치부터 확인하세요. 옵션을 켰다는 사실만으로 특정 성능 향상이 보장되지는 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)에 대응합니다. 원문의 복제·배치·충돌 필터를 독립 실행과 초기·최종 위치 기록으로 연결했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 2026-09-14의 **기본 Headless 60스텝**에서 네 상자 생성과 낙하를 확인한 기록입니다. 최종 Z 약 0.56 m는 그 시점의 관찰값이며 안정 높이가 아닙니다. `tutorial.json`의 `partial_runtime_verified`도 다른 배치·복사·물리 복제 모드나 GUI 조작까지 확인했다는 뜻은 아닙니다.
