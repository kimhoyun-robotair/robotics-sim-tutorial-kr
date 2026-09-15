# 39. 지게차의 부품을 일곱 가지 운동으로 나누기

## 이번에 배우는 것

**지게차를 여덟 강체와 일곱 가동 관절로 구성하고, 구동·조향·리프트의 역할과 단위를 확인합니다.**

복잡한 외형을 가진 로봇도 먼저 “어떤 부품들이 함께 움직이는가”를 정하면 구조가 보입니다. 차체에 고정된 유리와 지지대는 차체 강체에 묶고, 차체와 상대 운동이 필요한 바퀴와 리프트는 별도 강체로 만듭니다.

| 운동 | 관절 수 | 허용할 방향 | 구동 방식 |
|---|---:|---|---|
| 앞쪽 roller 회전 | 4 | X축 회전 | Drive 없이 접촉에 따라 회전 |
| 리프트 승강 | 1 | Z축 직선 이동 | 위치 목표 |
| 뒷바퀴 회전 | 1 | X축 회전 | 속도 목표 |
| 뒷바퀴 조향 | 1 | Z축 회전 | 위치 목표 |

합계 **7자유도**입니다. 이 실습은 공식 cm 단위 에셋을 사용합니다. 예를 들어 리프트의 목표 `50`은 50 m가 아니라 **50 cm**입니다.

## 1. 출발 장면과 강체 경계 준비하기

Isaac Sim 5.1.0, RTX GPU, GUI와 공식 Forklift 에셋 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/39_robot_setup_rig_mobile_robot/run.py \
  --output src/39_robot_setup_rig_mobile_robot/output/first
```

실행기는 `/Isaac/Samples/Rigging/Forklift/forklift_b_unrigged_cm.usd`를 엽니다. GUI에서 rigging을 직접 진행하며 창은 닫을 때까지 유지됩니다. `output/first/initial_inventory.json`의 `meters_per_unit`이 `0.01`인지 먼저 확인하세요. 편집 대상 layer는 같은 폴더의 로컬 `stage.usda`입니다.

1. 지게차 루트 아래에 `body`, `lift`, `back_wheel`, `back_wheel_swivel` Xform을 준비합니다.
2. 네 roller용으로 `roller_front_left`, `roller_front_right`, `roller_back_left`, `roller_back_right`를 만듭니다.
3. 함께 움직이는 geometry를 해당 Xform 아래로 모읍니다. 차체에 고정된 부품은 `body`, 올라가는 포크 부품은 `lift`, 조향축과 구동 바퀴는 각각 별도 링크에 둡니다.
4. 이 여덟 Xform에 **+ Add > Physics > Rigid Body**를 적용합니다. 자식 geometry를 선택하고 **+ Add > Physics > Collider**를 적용하세요. geometry에 이미 Collider가 있다면 그 설정을 확인합니다. 강체는 부모 Xform에만 두고 자식에 중복 적용하지 않습니다.

### 설정에서 볼 부분

바퀴 링크의 기준점은 회전 중심에 두는 편이 이해하기 쉽습니다. 원본 geometry에 Translate와 Translate:pivot이 따로 있다면 부모 위치를 두 값의 합에 맞추고, 자식 Translate를 pivot의 음수로 보정하는 원문 절차를 참고하세요. **옮기기 전후 화면상의 world 위치가 같아야 합니다.**

Collider는 외형을 그대로 복제할 필요가 없습니다. 눈 모양 메뉴의 **Show By Type > Physics > Colliders > Selected**로 다음을 조사하세요.

- 차체와 리프트: 하나의 Convex Hull이 포크 사이 빈 공간을 막는다면 Convex Decomposition으로 나눕니다.
- Roller와 뒷바퀴: **Create > Shape > Cylinder**로 원기둥을 만든 뒤 해당 바퀴 Xform 아래로 옮기고 중심을 맞춥니다. 원기둥에 **+ Add > Physics > Collider**만 적용하고 시각 표시는 숨기세요. Collider 표시에서 굴러갈 면이 매끈한지 확인합니다.
- 원문 원기둥의 scale은 앞쪽 `(0.16, 0.16, 0.08)`, 뒤쪽 `(0.3, 0.3, 0.1)`, Rotate Y는 90°입니다. 이 값은 생성한 원기둥의 기본 크기와 부모 변환까지 합쳐 해석해야 하므로, 최종 충돌 윤곽을 실제 바퀴에 맞춰 확인합니다.

### 실행 결과 확인하기

Stage에서 각 링크 하나를 선택했을 때 그 링크와 함께 움직일 geometry만 그 아래에 있어야 합니다. `initial_inventory.json`은 **rigging 이전** 목록이므로 여기에 여덟 강체와 일곱 관절이 자동 추가되지는 않습니다. 편집 후 구조는 다음 절의 검사기로 확인합니다.

## 2. 관절·drive를 작성하고 결과 읽기

관절을 만들 때는 두 강체를 선택하고 **Create > Physics > Joints**에서 종류를 고릅니다. 아래 연결의 화살표는 Body0에서 Body1 방향입니다. 네 roller를 제외한 drive 값은 `joint_spec.json`에 정리되어 있습니다.

### 설정에서 볼 부분

| 이름과 연결 | 종류·축 | 범위 | Drive 설정 |
|---|---|---|---|
| `lift_slide`: body → lift | Prismatic, Z | -15~200 cm | target position=-15, stiffness=100000, damping=10000 |
| roller 4개: body → 각 roller | Revolute, X | 자유 회전 | Drive 없음 |
| `rear_drive`: back_wheel_swivel → back_wheel | Revolute, X | 자유 회전 | stiffness=100, damping=10000, target velocity=-200 deg/s |
| `rear_steer`: body → back_wheel_swivel | Revolute, Z | -60~60° | stiffness=100000, damping=100, target position=0 |

리프트 관절에는 **+ Add > Physics > Linear Drive**, 구동·조향 관절에는 **Angular Drive**를 추가한 뒤 표의 값을 입력하세요. 네 roller에는 drive를 추가하지 않습니다.

회전 joint의 pivot은 해당 바퀴 중심에 맞추세요. 동일한 Axis=X여도 양쪽 local frame이 어긋나면 올바른 회전축이 되지 않습니다. 관절마다 Body0/Body1과 local frame을 확인한 뒤 다음 관절로 넘어갑니다.

루트 `SMV_Forklift_B01_01`에 Articulation Root가 있는지 확인하고 없을 때 추가합니다. Self Collision은 끕니다. **Create > Physics > Physics Scene**과 **Create > Physics > Ground Plane**으로 물리 환경과 바닥을 추가하세요. 이미 있다면 중복 생성하지 말고 기존 설정을 확인합니다. cm 장면에서 지구 중력에 해당하는 크기는 **980 stage-unit/s²**입니다.

```text
9.8 m/s² ÷ 0.01 m/stage-unit = 980 stage-unit/s²
```

이제 Play하면 뒷바퀴는 drive로 회전하고, roller는 바닥과의 접촉에 따라 수동으로 굴러야 합니다. 리프트 목표를 -15에서 50으로 바꾸면 지정한 Z축으로 올라가는지 확인한 뒤 초기 목표로 되돌립니다.

### 실행 결과 확인하기

**Window > Script Editor**에서 `inspect_result.py` 전체를 실행하세요. 실제 Stage를 순회해 다음 정보를 출력합니다.

```python
entry = {"path": str(prim.GetPath()), "type": prim.GetTypeName(),
         "body0": [str(x) for x in joint.GetBody0Rel().GetTargets()],
         "body1": [str(x) for x in joint.GetBody1Rel().GetTargets()]}
```

출력에는 여기에 Axis, Lower/Upper Limit, linear/angular drive 값이 추가됩니다. 검사기는 Revolute와 Prismatic 관절이 **총 7개인지** 자동 검사합니다. 그러나 일곱 개라는 수만 맞아도 통과할 수 있으므로 연결 대상과 숫자는 위 표 및 `joint_spec.json`과 직접 대조하세요. Script Editor 출력은 파일로 자동 저장되지 않습니다.

Play에서 링크 분리, 바퀴 떨림, 급격한 튀기가 없는지도 확인합니다. 완료 후 Stop하고 Ctrl+S로 로컬 장면을 저장하세요. 완성 비교 에셋은 같은 공식 폴더의 `forklift_b_rigged_cm.usd`입니다.

## 3. 자유도와 단위의 관계 정리

```text
8개 강체 → 7개 관절로 연결 → articulation 구성
          ├─ 4개 수동 회전
          ├─ 구동 바퀴의 속도
          └─ 조향과 리프트의 위치
```

일곱 관절 모두 같은 명령을 받는 구조가 아닙니다. 또한 USD의 회전 값은 degree, 직선 이동은 stage의 길이 단위를 사용합니다. `metersPerUnit`만 0.01에서 1로 바꾸는 것은 완전한 단위 변환이 아닙니다. Geometry, 관절 이동 범위, 중력과 물리 속성까지 일관되게 변환해야 하므로 이번에는 원래 cm 단위를 유지합니다.

## 4. 간단한 확인 실험

같은 출발 상태에서 **`rear_steer`의 Target Position만 0에서 20°로** 바꿔보세요. 뒷바퀴 속도와 리프트 목표는 그대로 둡니다.

먼저 뒷바퀴의 방향이 달라지는지 보고, 이어서 지게차의 이동 경로가 달라지는지 관찰하세요. 조향각은 바퀴 방향의 목표이므로 차체가 순간적으로 20° 회전하는 명령과는 다릅니다.

## 실행할 때 막히면

- **리프트 이동 거리나 낙하 속도가 이상합니다**: `meters_per_unit=0.01`과 cm 기준 목표·중력을 다시 확인하세요.
- **Play 직후 링크가 튑니다**: gain을 키우기 전에 collider의 초기 겹침, joint pivot, Body0/Body1을 확인하세요.
- **관절 7개 검사에 실패합니다**: 출력의 `type`을 세어 roller 네 개, lift, 구동, 조향이 각각 있는지 확인하세요. 검사기는 Stage 전체 관절을 조사합니다.
- **바퀴가 떨리거나 포크에 물체가 들어가지 않습니다**: 바퀴 Collider의 매끈함과 포크의 Convex Hull이 빈 공간을 막는지 확인하세요.
- **장면만 열리고 작업이 끝나지 않습니다**: 관절 제작은 GUI에서 수행합니다. `--steps`는 앱 갱신 한도이며 headless 사용 시 양수가 필요합니다. 재실행에는 새 출력 폴더를 지정하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 5: Rig a Mobile Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html)에 대응합니다. 단위 변경은 원문의 [Converting Asset to a Different Unit](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html#converting-asset-to-a-different-unit)을 참고하세요.

로컬 파일은 출발 장면 준비, 관절 설정표, 결과 조사 도구를 제공합니다. 실제 rigging과 주행은 `tutorial.json`에서 `not_run`으로 남아 있으며 관절 수 검사만으로 운동 안정성을 보장하지 않습니다.
