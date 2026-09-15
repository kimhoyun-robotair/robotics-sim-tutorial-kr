# 44. 닫힌 그리퍼 기구를 articulation으로 표현하기

## 이번에 배우는 것

**Robotiq의 닫힌 연결을 유지하면서 articulation 트리를 구성하고, 시험 하중으로 구동과 접촉을 확인합니다.**

관절을 따라가다가 출발 링크로 돌아오는 기구를 닫힌 고리라고 합니다. Robotiq의 손가락은 이런 연결을 이용해 자세를 유지합니다. 반면 articulation은 트리 구조로 계산하므로, 모든 연결을 같은 articulation 안에 넣을 수는 없습니다. 이번에는 일부 관절을 articulation에서 제외하되 물리 연결 자체는 남깁니다.

| 구성 요소 | 역할 | 준비 방법 |
|---|---|---|
| 2F-85 편집 에셋 | 실제 손가락과 knuckle 기구 | `run.py`로 열기 |
| Exclude From Articulation | 트리 바깥에서 처리할 관절 지정 | 관절 Property 편집 |
| `build_test_rig.py` | 고정 지지대·lift·reach·시험 물체 생성 | Script Editor 실행 |
| Drive와 mimic | 닫힘 운동과 양쪽 연동 | GUI 설정 |

## 1. 닫힌 고리와 관절 방향 살펴보기

Isaac Sim 5.1.0, RTX GPU와 GUI가 필요합니다. 기본 에셋은 `/Isaac/Samples/Rigging/Gripper/Robotiq 2F-85/Robotiq_2F_85_edit.usd`이며 폴더 이름의 공백도 경로에 포함됩니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/44_robot_setup_rig_closed_loop_structures/run.py \
  --output src/44_robot_setup_rig_closed_loop_structures/output/first
```

이 실행기는 이미 가져온 공식 편집 장면을 엽니다. Onshape 계정이나 CAD 재수입 없이 시작할 수 있습니다. Layers에서 로컬 `stage.usda`를 편집 대상으로 선택하세요. 창은 기본적으로 계속 열려 있으며, 저장은 Ctrl+S로 합니다.

### 설정에서 볼 부분

먼저 finger·knuckle 관절을 선택해 Body0와 Body1을 따라가 보세요. 같은 링크로 돌아오는 경로가 어디인지 확인한 뒤 다음을 적용합니다.

1. `left_inner_knuckle_joint`, `right_inner_knuckle_joint`의 **Physics > Joint > Exclude From Articulation**을 켭니다.
2. 두 관절의 prim과 Body0/Body1 관계는 그대로 유지합니다.
3. `left_outer_finger_joint`, `right_outer_finger_joint`의 limit는 0~180°, `finger_joint`와 `right_outer_knuckle_joint`는 0~75°로 맞춥니다. 나머지 관절의 불필요한 limit도 조사합니다.
4. 가져오기 과정에서 방향이 뒤집힌 관절이 있다면 **양쪽 Local Rotation의 X에 같은 180° offset**을 적용합니다. 원문은 특정 가져오기 결과의 네 관절을 설명하지만 모든 checkpoint에서 네 개를 반드시 수정하라는 뜻은 아닙니다. 현재 관절의 Body0/Body1, 양쪽 Local Rotation과 제한 범위를 먼저 기록하세요. 운동 방향은 2절에서 drive를 준비한 뒤 작은 양의 목표로 점검하고, 방향이 뒤집혔다고 확인한 관절만 Stop 상태에서 보정합니다. 이미 올바른 방향이면 기존 값을 유지합니다.

**관절을 articulation에서 제외하는 것은 관절을 삭제하는 것이 아닙니다.** 트리의 일부로 풀지 않는 연결도 별도 물리 제약으로 남아 기계적 고리를 유지합니다. 삭제하면 경고가 사라지더라도 기구 자체가 달라질 수 있습니다.

### 실행 결과 확인하기

Play에서 관절이 강제로 뒤집히거나 손가락 링크가 분리되는지 살펴보고 Stop하세요. Local Rotation은 양쪽 강체에서 같은 접합 방향을 표현해야 합니다. 한쪽만 보정하면 solver가 두 frame을 맞추려고 링크를 갑자기 움직일 수 있습니다.

`initial_inventory.json`은 장면을 처음 열었을 때의 목록입니다. 이후 Exclude 설정과 시험 장치 추가를 다시 기록하지 않습니다. 변경한 값은 Stage Property와 저장 USD에서 확인합니다.

## 2. 시험 장치를 만들고 집기 조건 조정하기

Stop 상태에서 **Window > Script Editor**를 열고 이 폴더의 **`build_test_rig.py` 전체**를 실행하세요. 이름이 `base_link`이고 RigidBodyAPI가 있는 prim을 정확히 하나 찾아 그리퍼 지지 장치를 만듭니다.

### 코드에서 볼 부분

시험 장치의 연결은 다음과 같습니다.

```text
world ─ Fixed Joint ─ anchor ─ lift(Z) ─ slide ─ reach(X) ─ gripper base
```

Anchor와 Slide는 그리퍼 base의 world transform에서 시작합니다. 따라서 lift와 reach의 축은 초기 base 방향의 영향을 받습니다. 이름이 lift라고 해서 어떤 자세에서도 world Z와 같다고 가정하지 마세요.

```python
joint.CreateLowerLimitAttr(0)
joint.CreateUpperLimitAttr(1)
drive.CreateStiffnessAttr(10000)
drive.CreateDampingAttr(10000)
drive.CreateTargetPositionAttr(0)
```

두 직선 관절은 0~1의 이동 범위와 처음 목표 0, 최대 속도 5를 갖습니다. 스크립트 수치는 **m 단위 장면**을 전제로 하므로 Stage의 단위부터 확인하세요. 이 장면에서 이동 범위의 단위는 m, 최대 속도는 m/s입니다. 물리 scene은 80 Hz로 설정됩니다.

`/TestRig/Load`는 반지름 0.025 m, 높이 0.2 m, 질량 0.2 kg인 원기둥입니다. 중심은 `(0.12, 0, 0)`, 바닥은 z=-0.1에 놓입니다. **스크립트는 손가락 사이 위치를 자동 탐색하지 않습니다.** 실제 fingertip 사이로 하중 위치를 맞춘 뒤 시험합니다.

### 설정에서 볼 부분

**Create > Physics > Physics Material > Rigid Body Material**로 `fingertip_material`을 만들고 Static/Dynamic Friction=0.8, Friction Combine Mode=Max로 설정합니다. 좌우 inner finger의 실제 접촉 pad를 선택한 뒤 Property의 **Physics materials on selected models**에서 이 재질을 연결하세요. Instance proxy라 편집할 수 없다면 해당 reference의 Instanceable을 먼저 해제합니다.

구동 관절 두 개와 outer_finger 관절에 **+ Add > Physics > Angular Drive**를 추가하세요. 그리퍼를 속도 명령으로 닫아보기 위한 출발 설정은 다음과 같습니다.

| 관절 | 설정 | 이유 |
|---|---|---|
| finger_joint, right_outer_knuckle_joint | stiffness=0, damping=5000, maxForce=180 | 위치 복원 대신 속도와 effort 한도로 구동 |
| 같은 구동 관절 | Maximum Joint Velocity=130 deg/s | 관절 속도 제한 |
| 좌우 outer_finger_joint | stiffness=0.05 | 평행 손가락을 위한 약한 spring |

Damping과 Max Force를 넣는 것만으로는 닫기 명령이 생기지 않습니다. 먼저 작은 Target Velocity를 주고 **두 관절이 닫힘 방향으로 움직이는 부호**를 확인하세요. 반대 방향이면 Stop 후 해당 목표 부호를 수정합니다. 관절 축이 다르면 같은 부호가 같은 운동을 뜻하지 않습니다.

한 입력으로 연동하려면 `right_outer_knuckle_joint`의 기존 drive를 제거하거나 비활성화한 뒤 **Mimic Joint**를 적용합니다. Reference Joint는 `finger_joint`, gearing은 -1입니다. 독립 drive와 mimic이 동시에 다른 목표를 요구하지 않도록 구성하세요.

**Window > Graph Editors > Action Graph**에서 완성 checkpoint의 `/World/Gripper_Controller`를 열면 boolean 입력에서 열기·닫기 속도 부호를 선택하는 흐름을 볼 수 있습니다. 자신의 장면에 옮길 때는 robot·joint 경로를 다시 연결해야 합니다. **Open Loop Gripper** 도구의 위치 명령 그래프는 여기의 stiffness=0 속도 구동과 명령 방식이 다릅니다.

### 실행 결과 확인하기

손가락 열기·닫기부터 확인한 뒤, 하중을 잡은 상태에서 lift의 목표를 작은 양수로 바꿔보세요. 원기둥이 바닥에 남는지, 미끄러지는지, 그리퍼와 함께 올라가는지 관찰합니다. Reach도 별도로 작은 목표를 주어 축 방향을 확인합니다.

Collider 표시로 손끝 접촉면을 조사하고 필요하면 Convex Decomposition을 사용하세요. Self Collision을 켤 때는 맞닿는 손가락과 joint로 직접 연결된 body의 충돌 필터도 함께 살펴봅니다. 실습 후 Stop하고 로컬 장면을 저장합니다.

## 3. 기구 연결과 제어 연결 정리

```text
닫힌 기계 연결 → 관절 제약을 유지
articulation 트리 → 일부 관절을 제외해 계산 구조 구성
mimic → 다른 관절의 움직임과 연동
접촉·마찰 → 손가락에서 하중으로 힘 전달
```

네 항목이 함께 맞아야 손가락이 움직이는 것을 넘어 물체를 들어 올릴 수 있습니다. 시험 장치가 생성되었다는 출력이나 controller 입력값만으로 접촉 안정성을 판정할 수는 없습니다.

## 4. 간단한 확인 실험

질량·마찰·drive·목표를 유지하고 Physics Scene의 **Time Steps per Second만 80에서 120으로** 바꿔 같은 집기 동작을 비교해 보세요.

한 단계의 시뮬레이션 시간은 0.0125초에서 약 0.00833초로 줄어듭니다. 하중 미끄러짐과 손가락 떨림이 달라지는지 관찰하되, 120 Hz가 모든 조건에서 성공을 보장한다고 기대하지 마세요. 비교 시 같은 초기 하중 위치로 되돌리는 것이 중요합니다.

## 실행할 때 막히면

- **`/TestRig exists`가 나옵니다**: 시험 장치가 이미 있습니다. 기존 장치를 조사한 뒤 다시 만들 목적일 때만 해당 장치를 제거하세요.
- **base_link 후보가 여러 개입니다**: 다른 로봇이 함께 있거나 예상과 다른 에셋입니다. 기본 checkpoint의 그리퍼 하나로 시작하세요.
- **손가락이 튀거나 고리가 벌어집니다**: 관절을 삭제했는지, 양쪽 local frame과 초기 collider가 맞는지 확인하세요.
- **손가락은 움직이지만 하중이 안 들립니다**: 실제 fingertip 위치, Collider·physics 재질 연결, 속도 부호와 effort 한도를 확인하세요.
- **유한 실행만으로 결과가 안 만들어집니다**: `--steps`는 앱 갱신 한도입니다. Script Editor와 GUI 작업을 대신하지 않으며 headless에는 양수 한도가 필요합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 10: Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)에 대응합니다. CAD 가져오기 후의 공식 checkpoint에서 시작하고, 지지축과 하중은 로컬 `build_test_rig.py`로 생성합니다.

완성 비교 자료는 공식 `/Isaac/Samples/Rigging/Gripper/Robotiq 2F-85_complete/`에 있습니다. `tutorial.json`은 `not_run`이며 실제 폐쇄 기구의 안정성, graph 제어, 하중 집기는 GUI에서 검증할 범위입니다.
