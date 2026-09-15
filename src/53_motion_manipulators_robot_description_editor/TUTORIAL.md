# 53. 모션 계획기가 이해할 로봇 설명 만들기

## 이번에 배우는 것

**Franka의 제어 관절과 충돌 구를 편집하고, Lula YAML과 XRDF로 내보낸 뒤 다시 읽어 봅니다.**

USD 로봇은 강체·관절·충돌 형상을 가지고 있지만 모션 계획기에는 추가 정보가 필요합니다. 팔과 손가락 중 무엇을 계획할지, 어떤 기본 자세를 선호할지, 링크 외곽을 얼마나 단순한 형상으로 계산할지를 정해야 합니다.

| 편집 대상 | 이번 실습의 선택 | 의미 |
|---|---|---|
| Active Joint | `panda_joint1`~`panda_joint7` | 계획기가 움직일 팔 7축 |
| Fixed Joint | 두 finger 관절 | 계획 중 고정값으로 가정할 손가락 |
| 기본 관절 자세 | 팔의 준비 자세, 열린 손가락 | 계획기의 시작 설정과 자세 기준 |
| Collision Sphere | 링크를 덮는 여러 구 | 빠른 충돌 계산을 위한 형상 근사 |
| 내보내기 | Lula YAML, cuMotion XRDF | 다른 모션 도구가 읽을 파일 |

**여기서 Fixed는 USD 관절 타입을 바꾸는 명령이 아닙니다.** 계획기가 해당 관절을 어떻게 다룰지 정하는 분류입니다.

## 1. 편집할 Franka 장면 준비하기

Isaac Sim 5.1의 GUI와 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. 아래 명령은 **저장소 루트** 기준이며 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
mkdir -p src/53_motion_manipulators_robot_description_editor/output
~/isaacsim/python.sh src/53_motion_manipulators_robot_description_editor/run.py
```

창은 사용자가 닫을 때까지 유지됩니다. 이번 실행은 로봇과 편집 확장을 준비할 뿐 **description 파일을 자동 생성하지 않습니다.** 파일 내보내기까지 GUI에서 진행하세요.

### 코드에서 볼 부분

```python
enable_extension('isaacsim.robot_setup.xrdf_editor')
```

화면의 도구 이름은 Lula Robot Description Editor이며 실제 활성화하는 확장 ID는 `isaacsim.robot_setup.xrdf_editor`입니다. 로봇을 `/World/Franka`에 reference한 뒤 다음 처리를 합니다.

```python
for prim in list(stage.Traverse()):
    if prim.IsInstanceable():
        prim.SetInstanceable(False)
world.reset()
```

공유 인스턴스 상태에서는 링크 내부를 자유롭게 편집하기 어렵기 때문에 현재 stage에서 instanceable 설정을 해제합니다. 원본 로봇 파일을 직접 열어 수정하는 흐름은 아닙니다.

### 실행 결과 확인하기

1. **Tools > Robotics > Lula Robot Description Editor**를 여세요.
2. 재생이 멈춰 있으면 Play하고 **Selection Panel > Select Articulation**에서 `/World/Franka`를 선택합니다.
3. **Select Link** 목록에 `panda_link4` 같은 링크가 나타나는지 확인하세요.

`--headless --steps 120`은 창 초기화 과정을 제한 실행할 때 쓸 수 있지만 GUI 편집을 대신하지 않습니다. 이 프로그램의 `--steps`는 앱 업데이트 횟수입니다. 수동 편집에서는 종료 한도를 생략하세요.

## 2. 관절을 정하고 충돌 구를 내보내기

### 설정에서 볼 부분

먼저 **Set Joint Properties**에서 팔 7축을 Active, 손가락을 Fixed로 두세요. 관절 위치는 다음과 같은 준비 자세에서 시작할 수 있습니다.

```text
panda_joint1~7: [0, -0.7854, 0, -2.3562, 0, 1.5708, 0.7854] rad
두 finger 관절: 각각 0.04 m
```

각 값이 관절 한도 안인지 확인합니다. 팔의 기본 자세는 같은 말단 위치를 만드는 여러 팔 자세 중 무엇을 선호할지 정하는 기준이 됩니다. 손가락은 열린 상태를 가정해 충돌 형상을 덮으면 닫힌 손가락도 그 범위 안에 놓이도록 구성하기 쉽습니다. 가속도·jerk 제한은 확인된 로봇 사양을 기준으로 설정하세요.

이제 링크를 단순한 구 여러 개로 덮습니다.

1. **Select Link**에서 `panda_link4`를 고르세요. **Link Sphere Editor > Add Sphere**로 반지름 0.05 m인 구부터 추가합니다.
2. 구가 링크의 외곽을 덮도록 중심과 반지름을 조절하세요. 구 중심 좌표는 **선택한 링크 원점 기준**으로 기록됩니다.
3. 같은 링크에 두 번째 구를 놓고 **Connect Spheres**로 두 구 사이에 3개를 보간해 보세요. 긴 링크의 중간 빈틈을 메울 수 있습니다.
4. 로봇 표시를 잠시 숨겨 구만 살펴보세요. 구가 너무 작으면 링크 일부가 계산에서 빠지고, 너무 크면 실제로 통과할 공간도 막힙니다.
5. 다른 링크에서는 먼저 해당 링크의 mesh를 선택하고 **Generate Spheres**로 8개 구의 preview를 살펴보세요. mesh가 여러 개라면 각각의 결과를 비교한 뒤 생성합니다. 자동 생성이 잘 안 되는 mesh는 Add/Connect로 보완합니다.
6. 팔의 나머지 링크와 손가락 외곽도 같은 관점으로 확인하세요. 구 개수보다 실제 형상을 얼마나 알맞게 덮는지가 중요합니다.

관절 분류와 구 편집의 배경은 [공식 Robot Description Editor 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html)에 나옵니다. 원문의 Set Joint Properties 일부 표현보다 앞부분의 정의와 실제 UI 의미를 따라 **Active=제어, Fixed=고정 가정**으로 구분하세요.

### 실행 결과 확인하기

1. **Export To File > Export to Lula Robot Description File**에 이 폴더의 `output/franka_description.yaml` **절대 경로**를 지정하고 저장합니다.
2. **Export to cuMotion XRDF**에서는 `output/franka.xrdf`를 별도 파일로 저장하세요.
3. 생성한 YAML을 열어 `cspace`의 관절 이름 7개, `default_q`의 순서, `cspace_to_urdf_rules`의 fixed 값, `collision_spheres`의 링크별 중심·반지름을 확인합니다.
4. **Import From File > Import Lula Robot Description File**로 방금 저장한 YAML을 읽으세요. 관절 선택과 구 위치가 복원되는지 살펴봅니다. Import는 편집기 상태를 바꾸므로 저장을 먼저 마쳐야 합니다.
5. **Import From File > Import XRDF File**로 `output/franka.xrdf`도 다시 읽어 보세요. 이 경로는 XRDF의 collision 그룹 구를 가져오며 tool frame·modifier·self_collision 그룹 전체를 편집 상태로 복원하는 기능은 아닙니다.

구를 화면에서 잘 배치했어도 다른 링크의 좌표로 내보냈다면 움직일 때 틀어질 수 있습니다. 파일의 링크 이름과 GUI에서 선택한 링크를 함께 대조하세요.

## 3. USD와 계획용 형상의 관계 정리

```text
USD: 실제 강체·관절·PhysX collider
URDF: 링크 연결과 관절 운동학
Description: 제어 관절·기본 자세·링크별 충돌 구
    → 계획기가 사용할 로봇 모델
```

Collision sphere는 PhysX collider와 별도입니다. 편집기에서 구를 늘렸다고 실제 로봇의 접촉 형상이 바뀌지는 않습니다. 반대로 USD collider가 있어도 Lula에 필요한 구 정보가 저절로 만들어지는 것은 아닙니다.

XRDF는 Lula description보다 넓은 정보를 담을 수 있습니다. 이 편집기는 tool frame이나 modifier를 새로 작성하지 않습니다. 기존 XRDF에 그런 정보가 있다면 먼저 파일을 복사해 보관하고, 내보내기 경로에 그 기존 XRDF를 지정했을 때 나타나는 **Merge With Existing XRDF**를 사용하세요. 저장 전후의 tool frame·modifier가 보존되었는지 텍스트로 대조합니다. self_collision의 ignore는 그 geometry가 collision geometry와 같을 때 보존되므로, import 후 화면에 구가 복원되었다는 사실만으로 모든 설정을 다시 썼다고 판단하지 마세요.

확장 기능이 저장을 도왔다는 사실과 실제 계획기가 그 파일로 동작했다는 사실도 구분해야 합니다.

## 4. 간단한 확인 실험

저장한 구 중 하나를 고르고 **반지름만 10% 키우세요.** 중심과 다른 구는 그대로 둡니다. `output/franka_description_larger.yaml`로 새로 내보내세요.

두 YAML에서 같은 링크의 해당 radius만 달라졌는지 확인합니다. GUI에서는 덮는 공간이 얼마나 넓어졌는지 보세요. 반지름 증가는 장애물과의 여유를 더 크게 잡는 대신 좁은 공간의 통과 가능성을 줄일 수 있습니다. 이 단계에서는 파일과 형상 변화를 확인하며 실제 회피 성능은 후속 모션 실습에서 확인합니다.

## 실행할 때 막히면

- **articulation 목록에 Franka가 없음**: Play 상태와 `/World/Franka`의 로봇 자산 로딩을 확인하세요.
- **링크 내부를 편집할 수 없음**: 다른 방식으로 연 instanceable 자산인지 확인하세요. 이 폴더의 `run.py`로 준비한 새 장면에서 시작합니다.
- **Save가 비활성화됨**: 저장 경로·확장자와 최소 1개의 Active Joint가 있는지 확인하세요.
- **자동 구 생성이 실패함**: mesh가 닫힌 삼각형 표면인지 확인하고, 수동 Add/Connect 방식으로 배치하세요.
- **실행을 끝냈는데 YAML이 없음**: 스크립트는 편집 시작 장면만 준비합니다. GUI Export를 직접 완료해야 합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Lula Robot Description and XRDF Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html)에 대응합니다. Franka 준비 코드는 로컬에서 제공하며 관절 선택, 구 작성, 내보내기와 재가져오기는 사용자가 수행합니다.

`tutorial.json`은 `not_run` 상태입니다. 이번 개정은 준비 코드와 공식 UI 절차를 대조한 것이며 실제 GUI 편집·export나 내보낸 파일을 이용한 모션 계획을 새로 검증하지 않았습니다.
