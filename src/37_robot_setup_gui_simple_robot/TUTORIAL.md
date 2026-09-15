# 37. 떨어져 있던 몸체와 바퀴를 어떻게 연결할까요?

## 이번에 배우는 것

**두 회전 관절로 몸체와 바퀴를 연결하고, 속도 명령이 실제 바퀴 운동으로 이어지는 과정을 확인합니다.**

앞의 도형 실습에서는 부품을 로봇처럼 배치해도 따로 떨어졌습니다. 이번에는 부품 사이의 허용 운동을 관절로 정합니다. 바퀴는 몸체에서 떨어지지 않으면서 자기 축 주위로 회전할 수 있어야 합니다.

| 추가할 요소 | 이 로봇에서 하는 일 | 확인할 장소 |
|---|---|---|
| Revolute Joint 두 개 | 바퀴마다 회전 자유도 하나 허용 | 관절의 Body0, Body1, Axis |
| Angular Drive | 허용된 회전축에 속도 목표 부여 | 관절 Property |
| Articulation Root | 연결된 강체를 하나의 물리 트리로 구성 | `/mock_robot` |
| Joint Velocity 그래프 | 재생 중 두 바퀴에 명령 전달 | `JointCommandArray` |

이번 실행기는 **관절 없는 공식 출발 장면**을 엽니다. 관절과 그래프를 추가하는 과정은 직접 진행합니다.

## 1. 출발 장면에서 두 회전 관절 만들기

Isaac Sim 5.1.0, RTX GPU, GUI와 공식 에셋 접근이 필요합니다. 저장소 루트에서 다음을 실행하세요.

```bash
~/isaacsim/python.sh src/37_robot_setup_gui_simple_robot/run.py \
  --output src/37_robot_setup_gui_simple_robot/output/first
```

실행기는 `/Isaac/Samples/Rigging/MockRobot/mock_robot_no_joints.usd` 위에 편집용 `stage.usda`를 만듭니다. 앞 튜토리얼의 결과를 가져올 필요는 없습니다. Play로 세 부품의 분리 낙하를 잠깐 확인한 뒤 Stop하세요.

1. `/mock_robot` 아래에 **Create > Scope**로 `Joints`를 만듭니다.
2. `/mock_robot/body/body`와 `/mock_robot/wheel_left/wheel_left`를 차례로 Ctrl 선택합니다.
3. 우클릭 **Create > Physics > Joints > Revolute Joint**를 선택하고 이름을 `wheel_joint_left`로 바꿉니다.
4. 관절 Property에서 Body0가 몸체 geometry, Body1이 왼쪽 바퀴 geometry인지 확인합니다.
5. **Local Rotation 0의 X=0**, **Local Rotation 1의 X=-90**, **Axis=Y**로 설정합니다.
6. 관절을 `Joints` Scope로 옮기고 오른쪽 바퀴도 같은 방법으로 연결합니다.

### 설정에서 볼 부분

관절을 Stage의 어느 폴더 아래에 놓았는지와 실제 연결 대상은 다릅니다.

```text
wheel_joint_left
  body0 → /mock_robot/body/body
  body1 → /mock_robot/wheel_left/wheel_left
  axis  → Y
```

관절은 `body0/body1`이라는 관계로 두 강체를 가리킵니다. `Joints` Scope는 보기 좋게 정리하는 위치입니다. 관절을 그곳으로 옮긴 뒤에도 두 관계가 맞는지 확인하세요.

또한 Body0와 Body1은 각각 자기 좌표계를 갖습니다. 바퀴가 몸체에 비해 X축으로 90° 돌아가 있으므로 관절의 두 local frame에 보정이 필요합니다. 이 보정 없이 축 이름만 Y로 맞추면 서로 다른 방향을 같은 축이라고 지정할 수 있습니다.

### 실행 결과 확인하기

Play한 뒤 Shift를 누르고 로봇 일부를 드래그해 보세요. 부품이 연결을 유지하면서 바퀴의 회전은 허용되는지 봅니다. 아직 drive를 추가하지 않았으므로 바퀴가 스스로 일정한 속도로 돌아야 하는 단계는 아닙니다.

`initial_inventory.json`은 프로그램이 처음 연 장면을 기록합니다. GUI에서 만든 관절이 이 JSON에 추가되지는 않습니다. 새 관절은 Stage와 저장한 `stage.usda`에서 확인하세요.

## 2. 속도 목표와 제어 그래프 추가하기

관절이 연결을 유지하는 것을 확인했다면 Stop하고 두 관절에 **+ Add > Physics > Angular Drive**를 추가하세요.

### 설정에서 볼 부분

먼저 그래프 없이 다음 값으로 시험합니다.

| Angular Drive 속성 | 값 | 의미 |
|---|---:|---|
| Stiffness | 0 | 특정 각도로 되돌리려는 위치 제어를 사용하지 않음 |
| Damping | 10000 | 목표와 실제 속도의 차이에 반응 |
| Target Velocity | 200 deg/s | USD Property에서 지정하는 각속도 |

Play하면 바퀴가 회전하는지 확인하고 Stop하세요. **USD의 Angular Drive 속도는 deg/s이고 Articulation Controller 명령은 rad/s입니다.** 200 deg/s는 약 3.49 rad/s이므로 숫자 200을 두 입력에 그대로 옮기면 전혀 다른 속도가 됩니다.

이제 그래프로 명령을 보내보세요.

1. `/mock_robot`에 **+ Add > Physics > Articulation Root**를 적용합니다.
2. 그 아래 `Graphs` Scope를 만듭니다.
3. **Tools > Robotics > Omnigraph Controllers > Joint Velocity**를 엽니다.
4. Robot Prim을 `/mock_robot`, Graph Path를 `/mock_robot/Graphs/Velocity_Controller`로 지정하고 생성합니다.
5. 그래프 아래 `JointCommandArray`에서 `input0`과 `input1`을 각각 `1.0`으로 설정하고 Play합니다.

Articulation은 연결된 강체와 관절을 물리 solver가 함께 다룰 트리로 묶습니다. 이 로봇처럼 바닥에 고정하지 않은 구조에서는 `/mock_robot`이 강체들의 상위 prim이므로 여기에 root를 둡니다. 그래프의 Robot Prim도 이 구조를 찾아야 합니다.

### 실행 결과 확인하기

두 바퀴가 명령에 반응하는지 확인하세요. `1.0`은 각각 **1 rad/s**, 약 57.3 deg/s입니다. 그래프는 재생 중 목표를 계속 쓰므로 앞서 Property에 넣은 200 deg/s가 최종 명령으로 유지될 것이라고 기대하지 마세요.

완성했다면 Stop 후 Ctrl+S로 로컬 layer를 저장하고 창을 닫습니다. 결과는 지정한 `output/first/stage.usda`입니다. `--steps`를 생략한 GUI는 계속 열려 있으며, 양수를 지정하면 그 횟수의 앱 갱신 후 닫힙니다. Headless에는 양수 `--steps`가 필요하지만 GUI 제작 과정까지 수행해 주지는 않습니다.

## 3. 연결과 제어의 흐름 정리

```text
관절 Body0/Body1 → 어떤 부품이 이어지는지
관절 local frame와 Axis → 어떤 방향의 운동을 허용하는지
Drive → 그 자유도를 목표 속도로 움직이는 힘/토크
Articulation + 그래프 → 로봇의 관절을 찾아 매번 명령 전달
```

바퀴가 안 움직일 때는 이 흐름을 역으로 추적해 보세요. 그래프에 숫자가 있다고 연결이 자동으로 생기는 것은 아니며, 관절이 있어도 drive에 유효한 목표가 없으면 능동적으로 돌지 않을 수 있습니다.

## 4. 간단한 확인 실험

그래프의 **`input1`만 1.0에서 -1.0으로** 바꿔보세요. `input0`, drive gain, 관절 축은 그대로 둡니다.

먼저 두 바퀴의 상대 회전 방향이 바뀌는지 보고, 이어서 로봇의 이동 방향을 관찰하세요. 회전 부호가 차체의 어느 이동 방향에 대응하는지는 각 바퀴의 관절 축과 배치에 달려 있습니다. 화면만 보고 좌우 입력을 추측하지 말고 그래프의 관절 이름 또는 인덱스 연결도 확인해 보세요.

## 실행할 때 막히면

- **Play 직후 부품이 분리됩니다**: 관절의 Body0/Body1이 부모 Xform이 아니라 실제 강체 geometry를 가리키는지 확인하세요.
- **바퀴가 순간적으로 틀어집니다**: joint pivot과 양쪽 local rotation을 확인하세요. 초기 collider 겹침도 함께 살펴보세요.
- **그래프 입력을 바꿔도 반응이 없습니다**: Play 상태, `/mock_robot`의 Articulation Root, 그래프 Robot Prim 순서로 확인하세요.
- **저장 또는 재실행에서 막힙니다**: Layers에서 로컬 `stage.usda`를 편집 대상으로 선택하세요. 재실행 출력은 `output/second`처럼 존재하지 않는 폴더를 사용합니다. 저장한 결과는 `--stage`로 지정할 수 있습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 3: Articulate a Basic Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_simple_robot.html)을 기반으로 합니다. 공식 페이지의 단위 주의사항에 따라 USD Property와 articulation 명령을 구분했습니다.

로컬 실행기는 원본을 sublayer로 합성한 편집 장면과 초기 목록을 준비합니다. 관절·drive·그래프 제작과 운동 관찰은 GUI 실습입니다. `tutorial.json`은 `not_run`이며, 장면 로드만으로 완성 로봇의 동작을 검증했다고 해석하지 않습니다.
