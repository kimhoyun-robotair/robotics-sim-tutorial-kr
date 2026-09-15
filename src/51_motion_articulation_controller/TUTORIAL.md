# 51. 원하는 관절에만 목표를 보내려면?

## 이번에 배우는 것

**Franka의 관절을 이름으로 선택해 위치 목표를 보내고, 목표값과 실제 관절값을 구분해서 읽습니다.**

팔을 움직이는 명령과 손가락을 여닫는 명령은 모두 관절 위치로 표현할 수 있습니다. 다만 배열의 숫자만 맞아서는 충분하지 않습니다. **어느 관절에 어느 값을 적용하는지**, 그리고 **그 값의 단위가 무엇인지**도 맞아야 합니다.

| 구분 | 기본 실행 | `--fingers-only` 실행 |
|---|---|---|
| 선택 관절 | 팔 7개와 손가락 2개 | 손가락 2개 |
| 팔 목표 | 코드에 정한 7축 자세 | 새 목표를 보내지 않음 |
| 손가락 목표 | 각각 `--finger-width` | 각각 `--finger-width` |
| 위치 단위 | 팔 rad, 손가락 m | m |
| 결과 파일 | `joints.json`에 선택한 9축 | `joints.json`에 선택한 2축 |

## 1. 먼저 팔과 손가락을 함께 움직이기

Isaac Sim 5.1과 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. 자산 서버 또는 로컬 팩에서 USD와 종속 mesh·재질을 읽을 수 있어야 합니다.

아래는 **저장소 루트**에서 실행하는 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/51_motion_articulation_controller/run.py --steps 600
```

600단계를 진행한 뒤 결과를 저장하고 앱이 종료됩니다. 창 없이 실행하려면 `--headless`를 추가하세요. GUI에서 `--steps`를 생략하면 창을 닫을 때까지 같은 목표를 계속 보냅니다. 결과는 이 폴더의 새 `output/run_*`에 저장되며, 종료 시 표시되는 `Output:` 경로를 확인하세요.

### 코드에서 볼 부분

로봇 USD를 참조한 다음 Python에서 제어할 객체를 만들고 초기화합니다.

```python
robot = world.scene.add(SingleArticulation('/World/panda', name='panda'))
world.reset()
```

USD reference는 장면의 로봇을 가져오고, `SingleArticulation`은 그 로봇의 관절 상태와 명령에 접근하는 역할을 합니다. `world.reset()` 이후에 물리 상태와 관절 인덱스를 읽습니다.

```python
indices = np.array([robot.get_dof_index(name) for name in names])
action = ArticulationAction(joint_positions=targets, joint_indices=indices)
```

`names`는 제어할 관절 이름 목록, `indices`는 그 이름에 대응하는 실제 자유도 인덱스입니다. `targets[0]`은 로봇의 무조건 첫 관절이 아니라 **`indices[0]`이 가리키는 관절의 목표**입니다. 배열의 길이와 순서를 함께 유지해야 합니다.

반복문은 같은 action을 적용하고 `world.step()`을 호출한 다음 실제 관절값을 읽습니다. 시작 위치를 강제로 바꾸는 방식이 아니라, 물리 drive가 목표로 움직이는 과정을 관찰합니다.

### 실행 결과 확인하기

`joints.json`의 같은 인덱스에 있는 값들을 가로로 연결해 읽어 보세요.

| 항목 | 의미 |
|---|---|
| `joint_names`, `joint_indices` | 값이 어느 관절에 속하는지 나타내는 대응표 |
| `initial` | 명령을 보내기 전 상태 |
| `targets` | 반복해서 전달한 고정 목표 |
| `measured` | 마지막으로 읽은 실제 위치 |
| `absolute_error` | `abs(measured - targets)` |

예를 들어 `panda_finger_joint1`의 target이 0.02라면 손가락 하나의 이동 목표는 **2 cm**입니다. 이 숫자를 집게 전체 폭이라고 읽지 마세요. 양쪽 손가락의 이동과 원래 형상을 함께 고려해야 집게 사이 간격을 알 수 있습니다.

초기 오차 `abs(initial - targets)`와 마지막 오차를 비교해 보세요. 마지막 오차가 작아졌다면 실제로 목표에 접근한 근거가 됩니다. 팔의 0.01 rad와 손가락의 0.01 m는 다른 크기이므로 오차 배열 전체에 같은 감각의 기준을 적용하지 않습니다.

## 2. 손가락 관절만 선택해 제어하기

앞 실행을 마친 뒤 아래 명령을 실행하세요.

```bash
~/isaacsim/python.sh src/51_motion_articulation_controller/run.py \
  --fingers-only --finger-width 0.03 --steps 600
```

이번 `names`는 `panda_finger_joint1`, `panda_finger_joint2` 두 개입니다. 목표 배열도 `[0.03, 0.03]`으로 짧아지며 실제 DOF 인덱스는 이름으로 다시 구합니다. 팔 자리에 0을 채워 넣는 대신, 명령 대상에서 팔을 제외합니다. **0도 유효한 위치 목표**이므로 “값이 0이면 제어하지 않는다”는 가정에 기대지 않는 방식입니다.

### 코드에서 볼 부분

부분 제어의 핵심은 적용할 자유도를 지정하는 것입니다.

```text
손가락 이름 2개 → 실제 인덱스 2개 → 위치 목표 2개
    → apply_action() → 선택한 손가락의 상태 2개 기록
```

이 모드는 팔에 새 목표를 보내지 않습니다. 그렇다고 팔에 중력이나 기존 drive의 영향이 없어지는 것은 아니므로 “팔을 잠그는 옵션”으로 이해하면 안 됩니다.

### 실행 결과 확인하기

새 결과 파일의 모든 배열이 두 손가락 순서로 기록됐는지 확인하세요. 화면에서 움직이는 방향도 함께 봅니다. 이 JSON은 초기와 최종 상태만 저장하므로 중간에 목표를 얼마나 넘었는지, 언제 수렴했는지는 알 수 없습니다. 그런 응답을 보려면 GUI에서 움직임을 관찰하거나 실행 길이가 다른 결과를 비교해야 합니다.

같은 동작을 OmniGraph로 구성할 때도 관절 선택이 핵심입니다. 다음 비교는 스크립트 실행을 종료한 뒤 새 Isaac Sim 세션에서 진행하세요.

1. 새 stage에 같은 Franka USD를 `/World/panda`로 reference하고 Physics Scene을 추가합니다.
2. **Window > Graph Editors > Action Graph**에서 그래프를 만들고 **On Playback Tick → Articulation Controller**의 실행 포트를 연결하세요. 설치 5.1의 노드 타입 이름은 `IsaacArticulationController`입니다.
3. controller의 `robotPath`를 `/World/panda`로 지정하고 `targetPrim`은 비웁니다.
4. `jointNames`에는 두 finger 이름, `positionCommand`에는 `[0.03, 0.03]`을 넣습니다. 필요한 배열은 **Construct Array** 노드로 만들고 `jointIndices`, velocity/effort command는 비웁니다.
5. Play하여 손가락 움직임을 확인하세요. `positionCommand`만 `[0.01, 0.01]`로 바꾸면 두 관절의 새 목표가 됩니다.

배열 포트의 역할은 [공식 Articulation Controller 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html)에서 함께 확인할 수 있습니다. Python의 이름·목표 대응을 그래프 포트로 표현한 것입니다.

## 3. 명령과 상태의 차이 정리

```text
ArticulationAction: 어디로 가야 하는가?
    → apply_action(): drive에 목표 전달
    → world.step(): 힘과 제약에 따라 물리 진행
    → get_joint_positions(): 지금 어디에 있는가?
```

목표 전달은 움직임의 시작이고, `measured`는 결과입니다. `set_joint_positions()`로 실제 상태를 바로 설정하면 이 사이의 추종 과정을 건너뜁니다. 이번 실습에서 목표와 측정값을 나눠 저장하는 이유가 여기에 있습니다.

또한 Python API의 회전 관절 위치는 rad입니다. USD Property의 각도 표시가 degree라면 `180도 = π rad`로 변환해서 비교하세요. 손가락처럼 미끄러지는 관절은 길이 단위를 사용합니다.

## 4. 간단한 확인 실험

2절의 명령에서 **`--finger-width`만 0.03에서 0.01로** 바꿔 보세요. 같은 600단계를 실행하고 두 결과의 `targets`와 `measured`를 비교합니다.

각 손가락 목표는 2 cm 줄어듭니다. 실제 측정값도 함께 줄고 화면의 집게 간격이 좁아지는지 확인하세요. `absolute_error`가 작아도 어느 관절의 값인지 확인하지 않으면 잘못된 관절을 정확히 움직인 결과를 놓칠 수 있습니다.

## 실행할 때 막히면

- **관절 이름을 찾지 못함**: 코드가 기대하는 Franka 5.1 USD인지 확인하세요. 다른 로봇에서는 이름과 자유도 구성이 달라집니다.
- **물리 초기화 관련 오류**: 관절 인덱스와 상태를 읽는 코드가 `world.reset()` 뒤에 있는지 확인하세요.
- **손가락 폭 오류**: `--finger-width`는 손가락 하나의 이동량이며 0~0.04 m만 허용합니다.
- **목표와 측정값 차이가 큼**: 짧은 실행인지 확인하고, 지속되면 관절 drive의 stiffness/damping과 접촉 상태를 살펴보세요.
- **JSON이 아직 없음**: 결과는 반복문이 끝날 때 저장됩니다. 유한 `--steps`를 지정하면 저장 시점을 분명히 할 수 있습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Articulation Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/articulation_controller.html)에 대응합니다. 로컬 실습은 관절 이름 선택, 부분 위치 명령, 초기·최종 상태 비교에 집중합니다.

`tutorial.json`은 `not_run` 상태입니다. 이번 개정은 코드와 문서 대조이며, 실제 팔·손가락 추종이나 OmniGraph 조작을 새로 실행해 확인한 것은 아닙니다.
