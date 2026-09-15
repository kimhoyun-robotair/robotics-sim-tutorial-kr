# 29. 로봇의 링크·관절·도구 장착점을 USD에 설명하기

## 이번에 배우는 것

**두 링크로 된 작은 로봇에 Robot Schema를 붙이고, 물리 구조와 로봇의 의미를 별도 레이어에 기록합니다.**

USD 장면에는 큐브와 관절이 있어도, 어느 Prim이 로봇의 루트인지 또는 도구를 어디에 붙일지 명확하지 않을 수 있습니다. Robot Schema는 이런 의미를 표시합니다. 한편 실제 링크 연결은 Physics Joint의 body 관계로 표현합니다. 이번 실습은 두 종류의 정보를 파일에서 나눠 읽는 데 초점을 둡니다.

| 기록할 대상 | 적용할 API | 이 실습의 Prim |
|---|---|---|
| 로봇 전체 | Robot API | `/Robot` |
| 구성 링크 | Link API | `/Robot/base_link`, `/Robot/arm_link` |
| 관절 | Joint API | `/Robot/shoulder` |
| 도구 장착점 | Reference Point API | `/Robot/arm_link/ToolMount` |

Prim은 USD 장면의 개별 노드입니다. API를 적용하면 기존 Prim에 관련 속성과 관계를 추가할 수 있습니다.

## 1. 로봇 설명 레이어 생성하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 로봇 모양은 코드에서 만들므로 외부 에셋 다운로드는 필요하지 않습니다. 실행기는 설치에 포함된 `isaacsim.robot.schema` 확장을 활성화합니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 실제 설치 위치로 바꾸세요.

```bash
~/isaacsim/python.sh src/29_python_usd_robot_schema/run.py --steps 120
```

스키마와 보고서를 먼저 저장하고, 생성한 장면을 열어 120번 앱 업데이트 후 종료합니다. **이 횟수는 물리 단계가 아닙니다.** 로봇을 움직이거나 Play를 자동으로 시작하지 않습니다. 장면을 살펴보려면 `--steps 120`을 빼세요. Headless는 생략 시 120번 업데이트합니다.

### 코드에서 볼 부분

`run.py`는 모양·물리 관계를 `robot.usda`에 작성하고, 설명을 위한 새 레이어를 연결합니다.

```python
stage.GetRootLayer().subLayerPaths.append("configuration/robot_schema.usda")
with Usd.EditContext(stage, layer):
    rs.ApplyRobotAPI(robot)
```

`subLayerPaths`는 로봇 파일을 열 때 함께 합성할 파일 목록입니다. `Usd.EditContext` 안에서 작성한 스키마 속성은 `configuration/robot_schema.usda`에 저장됩니다. 따라서 로봇 설명을 고치기 위해 기본 형상 파일을 모두 다시 작성할 필요가 없습니다.

각 링크에는 Link API를 적용하고 로봇의 링크 목록에 순서대로 추가합니다. base_link가 첫 번째입니다. shoulder에는 Joint API를, ToolMount에는 Reference Point API를 적용하고 전방 축을 `Z`로 기록합니다. 전방 축은 장착점이 어느 방향을 향하는지 설명하는 정보이며, shoulder의 회전축 `Y`와는 다른 속성입니다.

### 실행 결과 확인하기

이 폴더의 `output/날짜-시간/`에 다음 파일이 생깁니다.

| 파일 | 읽을 부분 |
|---|---|
| `robot.usda` | 두 큐브의 위치, 강체·충돌 API, shoulder의 body 관계 |
| `configuration/robot_schema.usda` | Robot·Link·Joint·Reference Point API와 namespace |
| `schema_report.json` | 적용 API, 링크·관절 목록, body0·body1 대상 |

보고서의 `links`는 base_link와 arm_link, `joints`는 shoulder를 가리켜야 합니다. `joint_body0`은 base_link, `joint_body1`은 arm_link입니다. `robot_schemas`와 `reference_point_schemas`는 적용된 API 목록을 보여줍니다. Link·Joint API는 보고서의 별도 필드로 저장하지 않으므로 스키마 파일이나 GUI Property에서 확인하세요.

## 2. Stage 계층과 실제 링크 연결 비교하기

단계 수 없이 다시 실행한 창에서 `/Robot`과 자식 Prim들을 펼쳐 보세요.

```bash
~/isaacsim/python.sh src/29_python_usd_robot_schema/run.py
```

두 링크는 USD Stage 트리에서 형제입니다. 그러나 `GenerateRobotLinkTree()`가 읽는 기구학 트리에서는 shoulder가 base_link와 arm_link를 연결합니다. USD의 폴더처럼 보이는 계층과 관절로 이어진 구조가 같을 필요는 없습니다.

### 코드에서 볼 부분

관절의 양쪽 기준점은 각 링크의 좌표로 작성합니다.

```python
joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.2))
joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, -0.2))
```

base_link 중심은 z=0.1 m, arm_link 중심은 z=0.5 m입니다. 따라서 첫 기준점의 월드 높이는 `0.1 + 0.2 = 0.3` m, 둘째도 `0.5 - 0.2 = 0.3` m입니다. 서로 다른 로컬 좌표가 같은 공간상의 연결점을 가리킵니다. shoulder의 회전 제한은 USD 속성에서 -90~90도입니다.

`ToolMount`는 arm_link의 자식으로 z=0.1 m만큼 더 올라간 위치입니다. 링크를 따라 움직일 관심점을 링크 아래에 두면 그 기준이 분명해집니다.

### 실행 결과 확인하기

1. `/Robot`을 선택하고 Property에서 Robot API의 설명, namespace `tutorial_robot`, 링크·관절 대상을 찾으세요.
2. 각 링크와 shoulder에서 해당 Link·Joint API를 확인하세요. 필요하면 **Property > + Add > Edit API Schema**에서 적용된 스키마를 조사할 수 있습니다.
3. ToolMount의 Reference Point 속성에서 설명과 전방 축 `Z`를 확인하세요.
4. 콘솔의 링크 트리가 base_link 아래에 arm_link를 연결하는지 비교하세요.

스키마는 보고할 링크·관절을 지정하는 정보도 제공합니다. 목록의 이름만 보고 연결을 추측하지 말고 실제 Physics Joint의 body 대상과 함께 읽으세요.

### 팔과 그리퍼를 합친 로봇의 트리 읽기

작은 두 링크 모델을 이해했다면 공식 UR10e 자산에서 하위 로봇을 포함하는 방법을 비교할 수 있습니다. 이 선택 실습에는 `/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd`와 해당 자산이 참조하는 Robotiq 그리퍼가 필요합니다.

1. 앞 실행을 종료하고 `~/isaacsim/isaac-sim.sh`로 새 창을 엽니다. **Window > Extensions**에서 `isaacsim.robot.schema`를 켭니다.
2. Content Browser에서 위 UR10e USD를 `/World` 아래로 끌어놓습니다. Stage에서 실제 로봇 경로를 확인하세요.
3. 로봇의 Property > Variants에서 그리퍼를 **Robotiq 2f-140**으로 선택합니다. 선택지가 없다면 다른 UR10e 자산을 연 것인지 경로를 대조합니다.
4. **Window > Script Editor**에서 다음을 실행합니다. 로봇 경로가 다르면 문자열 한 곳을 실제 경로로 바꾸세요.

```python
import omni.usd
from usd.schema.isaac.robot_schema import utils
stage = omni.usd.get_context().get_stage()
robot = stage.GetPrimAtPath("/World/ur10e")
if not robot.IsValid():
    raise RuntimeError("Stage의 실제 UR10e 경로를 확인하세요")
utils.PrintRobotTree(utils.GenerateRobotLinkTree(stage, robot))
```

출력에서 팔의 `wrist_3_link` 아래에 그리퍼 base와 손가락 링크들이 이어지는지 확인하세요. `/World/ur10e`의 Robot Links/Joints 목록에는 하위 로봇 `ee_link`가 포함됩니다. 부모 로봇의 목록에 **하위 Robot root를 넣는 방법**과 필요한 하위 링크·관절을 직접 나열하는 방법으로 조합을 표현할 수 있습니다. Scene 트리에서 그리퍼가 자식이라는 사실만으로 보고 목록까지 자동 구성되었다고 가정하지 마세요.

이 조회는 USD의 구조를 읽으므로 물리 Play가 필요하지 않습니다. 두 링크 실습의 별도 레이어 원리와 마찬가지로 자산을 편집하려면 새 로컬 사본이나 편집 layer를 사용합니다.

## 3. 구조와 설명의 차이 정리

```text
robot.usda
  Cube 링크 위치 + Physics Joint body 관계
         +
configuration/robot_schema.usda
  로봇 루트 + 보고 목록 + namespace + 장착점 의미
         ↓
합성된 Stage에서 로봇 구조와 설명을 함께 조회
```

레이어를 나눠도 최종 Stage에서는 두 정보가 합쳐집니다. 반대로 `robot.usda`만 다른 폴더로 옮기면 상대경로의 스키마 파일을 찾지 못할 수 있습니다. 로봇 파일과 `configuration/` 폴더를 한 묶음으로 보관하세요.

## 4. 간단한 확인 실험

두 링크 모델의 `run.py`를 단계 수 없이 다시 실행한 창에서 `/Robot`의 namespace만 `tutorial_robot`에서 `robot_b`로 바꿔 보세요. 선택 실습의 UR10e 장면이 아니라 처음 만든 `/Robot`에서 비교합니다. 링크 경로나 body 관계는 건드리지 않습니다.

그런 다음 **Window > Script Editor**에서 현재 Stage의 트리를 다시 읽으세요.

```python
import omni.usd
from usd.schema.isaac.robot_schema import utils
stage = omni.usd.get_context().get_stage()
utils.PrintRobotTree(utils.GenerateRobotLinkTree(stage, stage.GetPrimAtPath("/Robot")))
```

namespace는 로봇 구성 요소를 식별하는 메타데이터이므로 링크 연결은 그대로여야 합니다. 저장된 `schema_report.json`은 실행 시작 시 만든 보고서라 GUI 편집을 자동 반영하지 않습니다. 이번 비교는 현재 Stage의 Property와 새 콘솔 출력을 사용하세요.

## 실행할 때 막히면

- **로봇이 가만히 있음**: 이 코드는 구조 작성과 조회를 수행합니다. `app.update()`만으로 물리 Play를 시작하지 않으며 자동 관절 제어도 없습니다.
- **Robot Schema import 오류**: 확장 이름은 `isaacsim.robot.schema`이고 코드의 Python import 경로는 `usd.schema.isaac.robot_schema`입니다. 5.1 설치와 활성화를 확인하세요.
- **다시 연 파일에서 스키마가 사라짐**: `configuration/robot_schema.usda`의 상대경로와 파일 존재 여부를 확인하세요.
- **트리가 비거나 링크가 빠짐**: Robot·Link API, 링크 target, shoulder의 body0·body1이 유효한 Prim을 가리키는지 차례대로 보세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Robot Schema](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html)에 대응합니다. 공식 문서의 네 API와 별도 레이어 작성 방식을 두 링크의 로컬 예제로 구성했습니다. 5.1 문서에서 Robot Schema는 experimental로 안내합니다.

기본 실행은 두 링크의 스키마 작성이며, UR10e·그리퍼 조합은 공식 자산을 별도로 여는 선택적 GUI 조사입니다. 실제 관절 제어는 포함하지 않습니다. `tutorial.json`의 검증 상태는 `not_run`입니다. 레이어·관절 기준점·보고서 설명은 코드에 따른 확인 기준이며, 두 실습의 GUI 표시와 트리 출력은 미검증입니다.
