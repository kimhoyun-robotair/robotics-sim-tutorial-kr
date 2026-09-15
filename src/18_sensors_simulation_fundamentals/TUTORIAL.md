# 18. 같은 큐브가 왜 하나만 바닥을 통과할까요?

## 이번에 배우는 것

**두 강체에서 충돌 설정만 다르게 하고, 낙하 운동과 바닥 접촉이 별개의 기능임을 확인합니다.**

화면에 큐브를 만들었다고 물리가 모두 준비되는 것은 아닙니다. 강체 설정은 물체의 운동을 계산하게 하고, 충돌체 설정은 다른 물체와 닿을 형상을 제공합니다. 이번에는 크기·질량·시작 높이가 같은 큐브 둘을 나란히 놓고 한쪽의 충돌만 끕니다.

| 물체 | X 위치 | 강체 운동 | 충돌 |
|---|---|---|---|
| `/World/WithCollider` | -1 m | 켜짐 | 켜짐 |
| `/World/WithoutCollider` | +1 m | 켜짐 | 꺼짐 |

두 큐브는 한 변 0.5 m, 질량 1 kg이며 중심 높이 2 m에서 시작합니다. 바닥은 Z=0입니다. 충돌이 켜진 큐브가 바닥에 놓이면 중심 높이는 약 0.25 m가 됩니다.

## 1. 먼저 두 큐브 떨어뜨리기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음 명령을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/18_sensors_simulation_fundamentals/run.py --steps 240
```

240번의 물리 단계를 기록하고 종료합니다. 물리 간격이 1/60초이므로 시뮬레이션 속 경과 시간은 약 4초입니다. 앱 시작과 렌더링을 포함한 실제 대기 시간은 이와 다를 수 있습니다.

창을 계속 보려면 `--steps 240`을 빼세요. 첫 240단계만 파일에 기록한 뒤에도 물리는 계속 진행합니다. `--headless`를 추가하면 창 없이 실행하며, 단계 수를 생략한 경우에도 240단계 후 종료합니다.

결과는 이 폴더의 `output/날짜_시간/`에 생깁니다. `--output`을 지정할 때는 존재하지 않는 새 폴더를 사용하세요.

### 코드에서 볼 부분

두 큐브 모두 `DynamicCuboid`로 만듭니다. 그다음 오른쪽 큐브에만 다음 변경을 적용합니다.

```python
UsdPhysics.CollisionAPI(without_collision.prim).GetCollisionEnabledAttr().Set(False)
```

이 줄은 충돌을 비활성화합니다. RigidBodyAPI를 제거하거나 중력을 끄는 코드가 아닙니다. 따라서 오른쪽 큐브도 떨어지지만, 바닥과의 접촉으로 멈추지는 않습니다.

이후 `world.reset()`으로 물리를 초기화하고 반복문에서 진행합니다.

```python
world.step(render=True)
```

한 단계가 끝난 뒤 `world.current_time`과 두 큐브의 월드 Z 위치를 같은 행에 저장합니다. 그래서 같은 행의 높이는 같은 관찰 시점끼리 비교할 수 있습니다.

### 실행 결과 확인하기

`fall.json`은 다음 항목을 가진 행들의 목록입니다.

| 항목 | 의미 | 충분히 진행한 기본 실행의 확인 기준 |
|---|---|---|
| `time_s` | 물리 경과 시간, 초 | 마지막 값 약 4.0 |
| `with_collider_z` | 왼쪽 큐브 중심 높이, m | 바닥 위 약 0.25 부근 |
| `without_collider_z` | 오른쪽 큐브 중심 높이, m | 0 아래로 계속 감소 |

처음에는 두 큐브가 함께 떨어지므로 높이가 비슷할 수 있습니다. 왼쪽 큐브가 바닥에 닿은 뒤 두 값이 갈라지는 구간을 찾아보세요. 오른쪽 큐브가 화면 아래로 사라져도 JSON에서는 계속 높이를 읽을 수 있습니다.

## 2. 장면의 물리 설정 따라가기

이번에는 `--steps` 없이 실행해 창을 유지하고 두 큐브의 속성을 살펴봅니다.

### 설정에서 볼 부분

1. Stage에서 `/World/WithCollider`를 선택합니다.
2. Property에서 Rigid Body와 Collision 관련 속성을 확인합니다.
3. `/World/WithoutCollider`를 선택해 Collision Enabled 값이 꺼져 있는지 비교합니다.
4. 뷰포트의 눈 아이콘에서 **Show By Type > Physics > Colliders**의 표시를 켜 충돌 형상을 확인합니다.

USD의 **스키마(schema)**는 Prim에 어떤 속성과 역할을 사용할 수 있는지 정의합니다. `Apply()`는 API 스키마를 붙이고, `Create...Attr()`는 속성을 만들며, `Get...Attr().Set(...)`은 해당 값을 바꿉니다. 이 실습에서는 두 큐브에 충돌 API가 있어도 오른쪽은 Enabled 값이 다릅니다.

### 코드에서 볼 부분

빠르게 이동하는 충돌체를 위한 `--ccd` 옵션도 준비되어 있습니다.

```python
PhysxSchema.PhysxSceneAPI.Apply(scene).CreateEnableCCDAttr(True)
PhysxSchema.PhysxRigidBodyAPI.Apply(with_collision.prim).CreateEnableCCDAttr(True)
```

CCD는 물리 단계 사이의 이동 경로를 고려해 빠른 물체가 얇은 충돌체를 건너뛰는 문제를 줄이는 기능입니다. 이 코드는 Physics Scene과 충돌이 켜진 강체 **두 곳**에 설정합니다. 충돌을 끈 큐브에 충돌을 다시 추가하는 기능은 아닙니다.

기본 바닥만으로는 CCD의 효과가 눈에 띄지 않을 수 있습니다. `--ccd`를 사용한 결과가 같아도 설정이 무의미하다는 뜻은 아닙니다. 얇은 플랫폼과 높은 낙하 위치를 별도로 준비해야 관통 조건을 비교할 수 있습니다.

### 실행 결과 확인하기

`scene.usda`에서 두 Prim의 물리 설정을 확인하고, 운동 이력은 `fall.json`으로 읽으세요. USD를 내보냈다는 사실만으로 시간에 따른 낙하 궤적 전체가 저장되지는 않습니다.

### 새 GUI에서 계층·CCD·형상 근사 비교하기

다음은 기본 두 큐브와 별도로 만드는 수동 장면입니다. 먼저 `run.py`를 종료하고 `~/isaacsim/isaac-sim.sh`로 새 GUI를 여세요. 실행 중인 World의 장면을 File > New로 바꾸면 기존 Python 반복문이 이전 물체를 계속 읽을 수 있습니다.

1. **File > New**, **Create > Physics > Ground Plane**으로 바닥을 준비합니다. **Create > Xform**으로 부모를 만들고 Z=10으로 옮깁니다. 부모에 **Add > Physics > Rigid Body**를 붙이고, 그 아래 Cube를 넣어 local Translate를 `(0, 0, 0.5)`로 설정하세요. Play하면 부모의 월드 위치는 변하지만 자식의 local 위치는 유지되는지 봅니다. Stop한 뒤 Cube에 Collider를 추가하면 바닥 접촉까지 생깁니다.
2. CCD를 비교하려면 별도 Cube 플랫폼을 Z=3, Scale=`(2, 2, 0.01)`로 만들고 Collider만 붙입니다. 낙하 강체의 시작 높이를 Z=80으로 높여 얇은 플랫폼을 건너뛰는지 관찰하세요. Stop한 뒤 Physics Scene과 낙하 강체의 CCD를 모두 켜고 같은 조건을 반복합니다. 관통 여부는 물리 간격과 속도에도 달려 있으므로 관통이 반드시 나타난다고 가정하지 않습니다.
3. 다시 별도 장면에서 Torus를 Z=3, Scale=`(5, 5, 5)`로 만들고 **Rigid Body With Colliders Preset**을 적용합니다. **Show By Type > Physics > Colliders > Selected**를 켜 Convex Hull이 구멍을 덮는지 봅니다. Stop 상태에서 approximation만 **Convex Decomposition**으로 바꾸어 여러 볼록 조각이 원래의 빈 영역을 어떻게 표현하는지 비교하세요.

각 장면은 별도 이름으로 저장합니다. 이 수동 실험의 결과는 기본 `fall.json`에 기록되지 않습니다.

### 접촉과 관절의 추가 설정 읽기

Collider의 Advanced에서 **Rest Offset**과 **Contact Offset**도 확인해 보세요. Rest Offset은 정착할 때의 접촉 표면 간격에 영향을 주고, Contact Offset은 접촉 후보를 미리 생성할 거리입니다. 같은 값이 아니므로 둘을 함께 바꾸기보다 하나씩 비교합니다. **Create > Physics > Physics Material**에서 만든 재질을 Collider에 할당하면 마찰과 반발을 비교할 수 있습니다. 시각 재질에 색만 바꾸는 작업과 구분하세요.

관절을 살펴보려면 두 강체를 차례로 선택한 뒤 **Create > Physics > Joints > Revolute Joint**로 연결하고 body0/body1, 두 local frame, axis와 limit를 읽습니다. **Add > Physics > Angular Drive**의 목표와 limit는 역할이 다릅니다. Articulation root는 이런 연결을 로봇의 관절 구조로 다루는 설정입니다. Physics Scene·Articulation Root·Joint에 **Add > Physics > Residual Reporting**을 적용하면 Simulation Data Visualizer에서 제약 계산의 residual도 볼 수 있습니다. 숫자가 작다는 것만으로 현실 모델 오차까지 작다고 결론 내리지는 않습니다.

## 3. 강체·충돌·시간 단계 정리

```text
화면 형상 → 어떤 모양으로 보일지
강체 설정 → 힘과 중력으로 어떻게 움직일지
충돌 설정 → 다른 물체에 어디서 막힐지
물리 단계 → 이 상태를 언제 다음 상태로 계산할지
```

`physics_dt`와 `rendering_dt`는 각각 물리 계산과 렌더링의 시간 간격입니다. 이 실습은 둘 다 1/60초로 두지만, 항상 같은 값이어야 하는 것은 아닙니다. 화면 프레임 수와 물리 계산 횟수를 같은 것으로 가정하지 말고, 운동 비교에는 기록된 `time_s`를 사용하세요.

GUI에서는 Root Layer의 **Timecodes per second**와 Physics Scene의 **Simulation Steps per Second**를 구분해 읽습니다. 예를 들어 물리 100 Hz와 화면 30 Hz에서는 한 화면 프레임에 포함되는 물리 단계 수가 일정하지 않을 수 있습니다. 물리 이벤트에 맞춘 Action Graph를 만들 때는 On Physics Step과 그래프의 `PipelineStageOnDemand` 설정을 함께 확인해야 합니다.

## 4. 간단한 확인 실험

초기 높이만 2 m에서 4 m로 바꿔 실행합니다.

```bash
~/isaacsim/python.sh src/18_sensors_simulation_fundamentals/run.py --height 4 --steps 240
```

왼쪽 큐브가 바닥에 닿는 시점은 늦어지지만, 정착한 중심 높이는 여전히 약 0.25 m여야 합니다. 바닥과 큐브 크기는 바꾸지 않았기 때문입니다.

낙하 시작 높이에서 큐브 반 높이를 뺀 거리를 `d`라고 하면, 공기저항 없는 낙하 시간은 대략 `sqrt(2d/9.81)`입니다. 2 m 시작에서는 약 0.60초, 4 m 시작에서는 약 0.87초가 기준입니다. 실제 접촉 시점은 이산적인 물리 간격과 접촉 설정의 영향을 받으므로 정확히 같은 숫자를 요구하지 말고 JSON의 높이 변화 시점과 비교하세요.

## 실행할 때 막히면

- **오른쪽 큐브가 바닥을 통과함**: 의도한 비교 결과입니다. 왼쪽 큐브까지 통과하는지 구분하세요.
- **두 높이가 아직 비슷함**: 너무 짧은 `--steps`일 수 있습니다. 바닥 접촉 이후까지 기록해 보세요.
- **왼쪽 큐브도 바닥에 멈추지 않음**: Collision Enabled와 바닥의 충돌 설정, Stage 단위를 확인하세요. 오른쪽 큐브의 값을 잘못 바꾸지 않았는지도 봅니다.
- **계속 진행한 화면이 파일과 다름**: 단계 수를 생략하면 최초 240단계 이후도 진행하지만 파일은 추가 기록하지 않습니다. 비교할 때 명시적으로 같은 `--steps`를 사용하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)에 대응합니다. 원문의 물리 스키마·충돌·시간 개념을 두 큐브의 낙하로 비교합니다. Torus 형상 관찰은 후속 수동 작업이며, 기본 코드에는 얇은 플랫폼·관절·센서가 없습니다.

`tutorial.json`의 검증 상태는 `not_run`입니다. 이번 문서 개정에서는 설정과 기록 순서를 코드로 대조했으며 물리 시뮬레이션을 새로 실행하지 않았습니다. 낙하 시간 계산은 결과를 해석할 근사 기준입니다.
