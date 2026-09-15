# 29. Robot Schema: 링크·관절·관심점을 별도 레이어로 기록

권장 학습 순서 **29** · 로봇 자산 가져오기와 제작 · 출처 ID `t176`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 120단계를 사용합니다. 스키마와 USD 결과를 먼저 저장하고, 생성한 Stage를 GUI에서 계속 관찰·편집할 수 있습니다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 예상 결과

두 링크와 한 관절로 된 로컬 USD에 Isaac Robot/Link/Joint/ReferencePoint API를 적용한다. 스키마는 `configuration/robot_schema.usda`에 따로 작성한다. `robot.usda`를 재개방하고 실제 링크 트리를 파싱해 콘솔과 `schema_report.json`에서 구조를 확인한다. **이 패키지는 구조 작성/검사 실습이며 구동되는 로봇 제어 예제가 아니다.**

## 순서대로 실습

1. `~/isaacsim/python.sh run.py`을 실행한다. 필요한 `isaacsim.robot.schema`는 5.1 설치에서 활성화한다. 로봇 자산 다운로드는 필요하지 않다.
2. `robot.usda`에서 `/Robot/base_link`, `/Robot/arm_link`, `/Robot/shoulder`, `/Robot/arm_link/ToolMount`를 찾는다. 각 링크는 실제 Cube와 rigid body/collision 스키마를 가진다.
3. RevoluteJoint의 body0/body1 관계는 각각 base/arm을 가리킨다. localPos0와 localPos1은 연결되는 양쪽 링크 좌표에서 관절 위치를 나타낸다. 여기서 USD Joint limit는 도 단위로 ±90이다.
4. root의 subLayerPaths에 `configuration/robot_schema.usda`가 있는지 확인한다. `Usd.EditContext` 안에서 API를 적용했으므로 스키마 의견이 별도 파일에 남는다.
5. Robot API의 ordered links는 base_link부터 시작하고 joints는 shoulder를 가리킨다. Link API를 링크 모두에, Joint API를 관절에, ReferencePoint API를 ToolMount에 붙인다.
6. 보고서에서 네 종류의 AppliedSchemas와 실제 relationship target을 확인한다. 콘솔 트리가 base_link 아래 arm_link로 출력되는지 확인한다.
7. GUI **File > Open**으로 robot 파일을 연다. root 선택 후 **Property > + Add > Edit API Schema**에서 RobotAPI를 검색한다. 링크/관절/관심점도 같은 방법으로 해당 API를 검사한다. API 속성 섹션은 보라색으로 표시된다.
8. Robot Links/Joints의 **+ Add Target**으로 대상을 편집할 수 있다. 이 실습에서는 base 링크가 첫 번째이고 각 target Prim이 유효해야 한다. 수정은 출력 파일 복사본에서 수행한다.

## 각 API의 의미

| API | 역할 |
|---|---|
| Robot API | 로봇 설명, 메시지 namespace, 보고할 링크·관절의 순서와 구성 |
| Link API | 보고 대상 링크 표시와 name override. 모든 링크가 반드시 rigid body여야 하는 것은 아님 |
| Joint API | 관절 표시, name override, 다자유도 상태를 평탄한 배열로 보고할 때의 DOF offset |
| Reference Point API | 센서·도구 장착점 같은 관심점의 설명과 forward axis |

Robot Links/Joints 목록은 보고에 필요한 일부만 담을 수 있다. 전체 기구학 연결은 Physics Joint의 body 관계로 정의된다. 링크 계층이 USD 부모/자식 트리와 항상 같은 것은 아니다. 닫힌 루프의 Joint는 “Exclude from Articulation” 정책을 명시하지 않으면 tree 파싱에서 임의로 끊길 수 있다. 이 5.1 Robot Schema는 공식 문서에서도 experimental로 설명한다.

## 로봇 조합: 원문의 UR10e + 그리퍼 예제

이 후속 단계는 NVIDIA 자산 루트의 `/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd`와 Robotiq 자산 접근이 필요하다. 새 GUI의 Content Browser에서 UR10e를 드래그하고 Property의 gripper variant에서 **Robotiq 2f-140**을 선택한다. 실제 prim 경로를 Stage에서 확인한다. Script Editor에서 다음을 실행한다.

```python
import omni.usd
from usd.schema.isaac.robot_schema import utils
stage = omni.usd.get_context().get_stage()
robot = stage.GetPrimAtPath("/World/ur10e")
if not robot.IsValid():
    raise RuntimeError("Stage에서 실제 UR10e 경로를 확인하세요")
tree = utils.GenerateRobotLinkTree(stage, robot)
utils.PrintRobotTree(tree)
```

UR10e의 wrist 링크 아래 그리퍼 링크들이 포함되는지 확인한다. 부모 Robot의 링크/관절 목록에 하위 Robot root를 추가하거나 필요한 하위 링크·관절을 직접 나열하면 조합을 표현할 수 있다. `GetAllRobotLinks`, `GetAllRobotJoints`, `GetJointBodyRelationship`, `GetJointPose`, `GetLinksFromJoint`는 전체 구성과 연결을 조사하는 보조 함수다.

## 한 가지 변수 실험과 문제 해결

출력 스키마 레이어 복사본에서 `isaac:namespace`만 바꾸고 링크 tree가 변하지 않는지 확인한다. namespace는 메시지 식별 메타데이터이고 기구학 관계가 아니다. tree가 비면 links target과 root의 Robot API를 확인한다. schema가 사라지면 configuration 레이어 상대경로가 유지되었는지 확인한다. import 경로는 확장 이름과 달리 5.1 호환을 위해 `usd.schema.isaac.robot_schema`를 사용한다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Robot Schema](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
