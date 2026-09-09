# 프로젝트 1: 재현 가능한 USD 물리 실험실

## 목표

GUI에서 만든 장면을 USD 레이어로 나누고, 독립 Python 프로그램에서 같은 장면의 물리 상태를 검사한다. 형상과 물리 설정, 실험 조건을 따로 저장하면 무엇을 바꾸었는지 비교하기 쉽다.

## 시작 전에 실행할 기준 예제

아직 자기 장면이 없다면 이 저장소의 [hello_stage.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/hello_stage.py)를 먼저 실행한다. 저장소 루트에서 다음을 입력한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py \
  --gui --output-dir project-1/results/baseline
```

이 예제는 한 변이 0.2 m인 큐브를 떨어뜨리고, 최종 높이·속도·초기화 후 재실행을 물리 상태 API로 확인한다. 통과 결과 파일을 읽고, GUI에서 낙하와 정지를 확인한다. 물리 검사 통과가 카메라 렌더링 검사를 대신하지는 않는다.

## 요구사항

- 바닥, 질량이 다른 동적 큐브 세 개, 고정 장애물, 조명, 카메라를 포함한다.
- 물체 형상, 물리 설정, 실험 조건을 세 레이어로 나눈다.
- 물리 240 step 뒤 큐브가 바닥 위에서 안정되었는지 위치와 속도로 확인한다.
- Stage의 길이 단위, 위쪽 축, `timeCodesPerSecond`를 README에 기록한다.

## 1단계: 레이어 역할을 정한다

```text
lab_root.usda
  subLayers = [
    @layers/overrides.usda@,
    @layers/physics.usda@,
    @layers/geometry.usda@
  ]
```

`geometry.usda`는 물체 구조와 모양을, `physics.usda`는 질량·충돌·물리 재질을, `overrides.usda`는 초기 위치와 실험 조건을 기록한다. 같은 속성에 여러 정의가 있으면 sublayer 목록의 앞쪽 레이어가 더 강하므로 위 순서를 사용한다. 여기서 `overrides.usda`는 파일로 저장하는 일반 sublayer이며, USD Stage가 별도로 가질 수 있는 익명 session layer와 다르다. Layers 패널에서 편집 대상을 바꿀 때 현재 선택한 레이어를 확인한다.

## 2단계: GUI 기본 동작 확인

1. 새 Stage에 Physics Scene과 Ground Plane을 만든다.
2. 큐브 세 개를 만들고 Rigid Body, Collider, Mass를 적용한다.
3. 큐브가 서로 겹치지 않게 배치하고 2초 동안 재생한다.
4. 충돌 형상 표시와 Physics Inspector로 바닥과 큐브의 충돌 형상을 확인한다.
5. 모든 레이어를 저장하고 Isaac Sim을 다시 시작한 뒤 최상위 Stage 파일을 열어 같은 장면이 나타나는지 확인한다.

## 3단계: 저장한 장면에서 물리 상태를 검사한다

먼저 세 큐브의 경로를 `/World/Cubes/CubeA`, `/World/Cubes/CubeB`, `/World/Cubes/CubeC`로 맞춘다. 각 큐브는 Collider와 Rigid Body를 가진 실제 강체여야 한다. 각 변이 0.2 m이고 바닥 높이가 0이라면 안정된 중심 높이는 약 0.1 m이다.

`project-1/tests` 폴더를 만들고 `hello_stage.py`와 같은 폴더의 `smoke_common.py`를 함께 복사한다. 예제 파일 이름은 `test_stage.py`로 바꾼다. 공통 실행 도우미도 같은 폴더에 있어야 import가 된다.

```bash
mkdir -p project-1/tests
cp examples/standalone/hello_stage.py project-1/tests/test_stage.py
cp examples/standalone/smoke_common.py project-1/tests/smoke_common.py
```

검증 코드는 복사한 파일에서 수정한다. 직접 큐브를 생성하는 부분 대신 저장한 장면을 열고 기존 큐브를 물리 API로 등록한다. `SimulationApp` 생성·종료와 결과 저장은 기존 예제 구조를 유지한다.

```python
# SimulationApp 생성 뒤의 본문 조각이다.
from isaacsim.core.api import World
from isaacsim.core.prims import SingleRigidPrim
from isaacsim.core.utils.stage import open_stage, is_stage_loading

if not open_stage("/absolute/path/to/lab_root.usda"):
    raise RuntimeError("Stage를 열지 못했다")
while is_stage_loading():
    simulation_app.update()
world = World(stage_units_in_meters=1.0, physics_dt=1/60)
bodies = []
for name in ("CubeA", "CubeB", "CubeC"):
    bodies.append(world.scene.add(SingleRigidPrim(
        prim_path=f"/World/Cubes/{name}", name=name,
    )))
world.reset()
for step in range(240):
    world.step(render=False)
    for body in bodies:
        position, orientation = body.get_world_pose()
        velocity = body.get_linear_velocity()
        # 실제 물리 상태를 대상으로 수치가 유한한지 검사한다.
        if not np.isfinite(np.r_[position, orientation, velocity]).all():
            raise RuntimeError(f"강체 상태에 NaN/Inf가 있다: {body.name}")
        if position[2] < -0.02:
            raise RuntimeError(f"바닥을 통과했다: {body.name}")
```

위 코드는 기존 스크립트의 `numpy as np`와 실행 환경을 사용하는 수정 예시이다. 최종 60개 물리 step에서 높이 오차와 속도가 기준 이하인지도 `hello_stage.py`처럼 검사한다. 마지막 위치 하나만 확인하면 순간적으로 안정돼 보이는 진동을 놓친다. Fabric이나 물리 설정에 따라 USD의 `xformOp`가 매 step 갱신되지 않을 수 있으므로 `UsdGeom.Xformable`의 저장된 변환만 읽어 물리 통과를 판정하지 않는다.

## 완료 조건

```bash
"$ISAACSIM_PATH/python.sh" project-1/tests/test_stage.py
```

- 검사 종료 코드가 0이고 결과 JSON에 실패가 없다.
- root 파일과 상대 참조 레이어 폴더를 함께 옮겨도 장면이 열린다. root 파일 하나만 복사하는 시험과 구분한다.
- 특정 레이어를 Mute했을 때 무엇이 사라지는지 설명한다.
- 질량 또는 마찰계수 하나를 바꾼 실험의 위치·속도 결과를 별도 파일로 저장해 비교한다.

## 확장 과제

Variant Set으로 `low_friction`과 `high_friction` 조건을 전환한다. 무거운 시각 자산을 Payload로 나누었다면 물리 검사에 필요한 충돌 형상은 유지하고, 시각 자산을 불러오는 경우와 제외하는 경우의 로딩 시간을 비교한다.

## 출처

- [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
