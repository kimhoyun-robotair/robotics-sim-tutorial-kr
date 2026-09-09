# 로봇 가져오기와 설정

가져오기 도구가 오류 없이 끝났다고 시뮬레이션 가능한 로봇이 완성된 것은 아니다. 가져온 뒤 링크 계층, 크기, 충돌 형상, 질량·관성, 관절 축·제한, 드라이브, articulation 루트와 센서 프레임을 검증해야 한다. 이 튜토리얼은 URDF/MJCF 입력을 재사용 가능한 USD 로봇 자산으로 만드는 전체 절차를 다룬다.

## 1. 권장 작업 순서

1. 원본 CAD/URDF/Xacro/MJCF의 경로와 문법을 검사한다.
2. 가져오기 도구로 USD를 생성한다.
3. 시각 형상, 충돌 형상과 물리 계층을 정리한다.
4. Articulation, 관절과 드라이브를 검증한다.
5. 센서, 그리퍼와 말단 프레임을 추가한다.
6. 게인, 마찰과 솔버 설정을 조정한다.
7. 동작 생성에 사용할 XRDF 또는 로봇 설명 파일을 만든다.
8. Asset Validation과 독립 실행 검사로 결과를 확인한다.
9. 다른 장면에서는 완성한 로봇 자산을 참조해 사용한다.

원본 로봇 설명 파일과 생성된 USD를 모두 버전 관리한다. 가져오기 도구 설정과 후처리 스크립트도 함께 기록해야 원본이 바뀌었을 때 재생성할 수 있다.

## 2. 가져오기 전 점검

### 이름과 경로

- 링크, 관절, 메시와 파일 이름에는 USD prim 이름에 부적합한 특수문자를 피한다. 가져오기 도구가 `_`로 바꾸면 ROS 관절 이름과 USD 이름의 대응이 깨질 수 있다.
- `package://`, 상대 경로와 텍스처 URI가 실제 파일을 가리키는지 확인한다.
- 대소문자를 구분하는 Linux에서 파일 이름이 정확한지 확인한다.
- Xacro 매크로는 먼저 펼쳐 실제 URDF를 보관하거나 ROS 2 노드 가져오기 도구를 사용한다.

```bash
# ROS 2 Jazzy 환경에서 Xacro를 명시적으로 URDF로 펼치는 예
source /opt/ros/jazzy/setup.bash
xacro robot.urdf.xacro use_fake_hardware:=true > robot.generated.urdf
check_urdf robot.generated.urdf
```

### 형상과 단위

- 길이가 미터 기준인지 확인한다. 밀리미터 단위의 CAD를 단위 변환 없이 가져오면 로봇이 1000배 크게 만들어질 수 있다.
- 시각 메시는 보기 위한 것이며 충돌 메시는 단순하고 닫힌 형상으로 별도 준비한다.
- 링크 원점, 관성 원점, 시각/충돌 원점과 관절 원점을 구분한다.
- Z축이 위를 향하는 Stage로 변환된 뒤 관절 축이 의도대로인지 확인한다.

### 관성과 관절

- 움직이는 모든 링크에 양의 질량이 있는지 확인한다.
- 관성 행렬가 대칭이고 물리적으로 가능한 양의 값인지 확인한다.
- 관절 제한의 lower < upper, 속도 > 0, 토크·힘 > 0인지 확인한다.
- 연속 회전 관절과 회전 범위가 제한된 관절을 잘못 바꾸지 않는다.
- 연동 관절, 고정 관절 병합과 transmission 설정의 의미가 실제 제어 방식과 맞는지 확인한다.

## 3. URDF를 GUI로 가져오기

1. `Window > Extensions`에서 `isaacsim.asset.importer.urdf`가 활성화되었는지 확인한다.
2. `File > Import`에서 `.urdf`를 선택한다.
3. **USD 출력**을 프로젝트의 쓰기 가능한 폴더로 지정한다.
4. 고정형 로봇 팔은 **Static Base**, AMR·다리형 로봇은 **Moveable Base**를 선택한다.
5. 질량이 없는 링크에만 적용될 기본 밀도를 결정한다. 0이면 물리 엔진 기본 계산을 사용한다.
6. 드라이브 목표를 관절별로 Position, Velocity 또는 None으로 설정한다.
7. 충돌 형상의 원본과 근사 방식을 정한다.
8. 자기 충돌은 충돌 형상이 서로 겹치지 않는 것을 확인하기 전에는 끈다.
9. 가져오기를 누르고 Output Log의 경고를 읽는다.

### 주요 옵션을 결정하는 법

| 옵션 | 선택 기준 |
|---|---|
| Static/Moveable Base | 고정된 로봇팔인지, 베이스가 움직이는 로봇인지 구분한다. |
| Natural Frequency/Stiffness | 고유 진동수와 감쇠비로 게인을 정할지, 강성과 감쇠를 직접 입력할지 선택한다. |
| Acceleration/Force Drive | 관성을 고려해 가속도로 구동할지, 스프링·댐퍼의 힘으로 구동할지 선택한다. |
| Position/Velocity/None | 해당 관절을 어떤 제어기가 구동하는가? 토크 제어면 None을 고려한다. |
| Ignore Mimic | 원본의 관절 연동 관계를 유지할지 무시할지 선택한다. |
| Collision From Visuals | 충돌 형상이 없을 때만 임시 방편으로 쓴다. |
| Convex Hull/Decomposition | 단순·볼록인가, 오목한 동적 형상인가? |
| Replace Cylinders with Capsules | 더 안정적이고 단순한 바퀴/링크 충돌 형상이 필요한가? |
| Self Collision | 필요한 링크 쌍만 충돌해야 하는가, 초기 겹침이 없는가? |

가져오기 도구에서 지정한 고유 진동수는 강성값으로 변환되어 USD에 저장된다. 공식 문서의 관계는 다음과 같다.

\[
K_p=m_{eq}\omega_n^2,\qquad K_d=2m_{eq}\zeta\omega_n
\]

## 4. URDF를 Python으로 가져오기

다음 코드는 실행 중인 Isaac Sim의 Script Editor 또는 Extension 안에서 사용할 수 있다. Standalone 파일이라면 앞에서 설명한 대로 이 코드의 런타임 모듈을 import하기 전에 `SimulationApp`을 생성해야 한다.

```python
from pathlib import Path

import omni.kit.commands
from isaacsim.asset.importer.urdf import _urdf

urdf_path = Path("/absolute/path/to/robot.generated.urdf")
if not urdf_path.is_file():
    raise FileNotFoundError(urdf_path)

config = _urdf.ImportConfig()
config.convex_decomp = False
config.fix_base = False              # 모바일 로봇 예시
config.make_default_prim = True
config.self_collision = False
config.distance_scale = 1.0
config.density = 0.0

parsed, robot_model = omni.kit.commands.execute(
    "URDFParseFile",
    urdf_path=str(urdf_path),
    import_config=config,
)
if not parsed:
    raise RuntimeError(f"URDF parse 실패: {urdf_path}")

# 필요하면 parsed model의 joint drive를 여기서 로봇별로 조정한다.
for joint_name in robot_model.joints:
    joint = robot_model.joints[joint_name]
    print("parsed joint:", joint_name, joint)

imported, prim_path = omni.kit.commands.execute(
    "URDFImportRobot",
    urdf_robot=robot_model,
    import_config=config,
)
if not imported:
    raise RuntimeError("URDF import 실패")
print("robot prim:", prim_path)
```

별도 USD 파일로 생성해 현재 장면에서 참조하려면 `URDFParseAndImportFile` 명령에 `dest_path`를 지정하는 방식이 좋다. 텍스처가 포함된 자산과 재사용 로봇은 메모리의 Stage에 바로 가져오기보다 파일 자산으로 만든 뒤 참조하는 편이 낫다.

> 가져오기 도구의 Python API와 명령 인자는 버전에 따라 달라질 수 있다. 5.1 프로젝트에서는 5.1 API 문서와 함께 고정하고, 다른 버전으로 옮길 때 가져오기 기본 동작 검사을 먼저 실행한다.

## 5. Xacro와 ROS 2 로봇 설명

Xacro는 매크로 언어이므로 일반 URDF 파일을 가져오는 도구에 바로 전달하지 않는다. 두 방법이 있다.

### 방법 A: 빌드 단계에서 펼치기

```bash
xacro my_robot.urdf.xacro prefix:=sim_ > build/my_robot.urdf
```

이 방법은 생성 URDF가 명시적으로 남고 CI에서 변경 내용과 문법을 검사하기 쉽다.

### 방법 B: ROS 2 노드에서 가져오기

1. ROS 2 Jazzy 작업 공간의 `install/setup.bash`를 `source`로 불러온다.
2. `robot_state_publisher`가 `robot_description`을 제공하도록 실행한다.
3. 같은 환경에서 Isaac Sim을 시작하고 ROS 2 Bridge를 켠다.
4. `isaacsim.ros2.urdf` Extension을 활성화한다.
5. `File > Import from ROS 2 URDF Node`에서 노드 이름과 출력 디렉터리를 지정한다.

ROS 노드 가져오기 도구는 로봇 설명이 실행 시 생성되는 패키지에 편리하지만, 최종 생성 USD와 실행할 때 전달한 launch 인자를 반드시 기록한다.

## 6. MJCF 가져오기

GUI에서는 `File > Import`에서 MJCF XML을 선택한다. Extension ID는 `isaacsim.asset.importer.mjcf`이다. 다음은 공식 5.1 명령 흐름을 단순화한 예이다.

```python
from pathlib import Path
import omni.kit.commands

mjcf_path = Path("/absolute/path/to/robot.xml")
if not mjcf_path.is_file():
    raise FileNotFoundError(mjcf_path)

ok, config = omni.kit.commands.execute("MJCFCreateImportConfig")
if not ok:
    raise RuntimeError("MJCF import config 생성 실패")

config.set_fix_base(False)
config.set_import_inertia_tensor(True)
config.set_self_collision(False)
config.set_convex_decomp(False)
config.set_make_default_prim(True)

ok, _ = omni.kit.commands.execute(
    "MJCFCreateAsset",
    mjcf_path=str(mjcf_path),
    import_config=config,
    prim_path="/World/Robot",
)
if not ok:
    raise RuntimeError("MJCF import 실패")
```

MJCF의 body, site, actuator와 기본값 상속 관계가 USD로 어떻게 매핑되었는지 점검한다. `merge_fixed_joints`, `import_sites`, `override_com`, `override_inertia` 같은 옵션은 연결 구조와 동역학을 바꾸므로 기본값을 무심코 쓰지 않는다.

## 7. 가져온 직후 10분 검사

### 1단계: 눈으로 보기

1. Stage에서 로봇 루트와 모든 링크/관절이 예상한 계층에 있는지 확인한다.
2. `F`로 초점을 맞추고 크기를 확인한다.
3. Viewport의 물리 시각화에서 Colliders를 모두 표시한다.
4. 충돌 형상이 시각 메시에서 크게 벗어나거나 서로 파고들지 않는지 확인한다.
5. 질량 중심과 관절 프레임 시각화을 켠다.

### 2단계: Play하기

1. 고정형 로봇은 베이스가 떨어지지 않아야 한다.
2. 이동형 로봇은 바닥 위에서 자연스럽게 지지되어야 한다.
3. 아무 명령 없이 관절이 갑자기 튀거나 제한 밖으로 가지 않아야 한다.
4. 자기 충돌을 켤 필요가 있다면 링크 쌍별로 천천히 검증한다.

### 3단계: 관절 정보 출력하기

Script Editor에서 로봇 prim 경로를 맞추어 실행한다.

```python
import asyncio
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation


async def inspect_robot():
    world = World.instance() or World()
    await world.initialize_simulation_context_async()

    robot = SingleArticulation(
        prim_path="/World/Robot",
        name="imported_robot",
    )
    await world.reset_async()
    robot.initialize()

    print("num_dof:", robot.num_dof)
    print("dof_names:", list(robot.dof_names))
    print("dof_properties:\n", robot.dof_properties)
    print("q:", robot.get_joint_positions())


asyncio.ensure_future(inspect_robot())
```

DOF 개수·이름·순서가 제어기와 ROS 관절 목록의 기대와 같은지 확인한다. `dof_properties`의 제한, 최대 속도, 최대 토크·힘, 강성과 감쇠를 원본과 비교한다.

## 8. 로봇 설정 공식 학습 흐름을 실제 자산에 적용하기

Isaac Sim 5.1 로봇 설정 튜토리얼 13개는 다음 작업 흐름으로 이해하면 된다.

| 단계 | 적용할 작업 | 산출물/검증 |
|---:|---|---|
| 1. Stage 설정 | Z축 위쪽, 미터 단위, 기본 prim, 레이어 구조를 정한다. | 빈 로봇 자산의 기본 구조 |
| 2. 간단한 로봇 조립 | 시각, 충돌 형상, 강체, 질량, 물리 재질을 구성한다. | 물리 링크 자산 |
| 3. 관절 구조 구성 | 관절, 드라이브와 articulation 루트를 구성한다. | 제어 가능한 articulation |
| 4. 카메라와 센서 추가 | 센서 prim과 고정 프레임을 링크 아래 배치한다. | 센서 포함 로봇 |
| 5. 이동로봇 설정 | 이동 가능한 베이스, 바퀴 축, 속도 드라이브와 마찰을 맞춘다. | AMR 베이스 |
| 6. 매니퓰레이터 조립 | 로봇팔과 그리퍼 자산을 Robot Assembler 등으로 결합한다. | 조립된 매니퓰레이터 |
| 7. 매니퓰레이터 조정 | 솔버, 그리퍼 마찰, 힘·토크 제한, 연동, 게인을 조정한다. | 안정적으로 움직이는 매니퓰레이터 |
| 8. 로봇 설정 파일 생성 | Lula 로봇 설명 파일/XRDF의 관절 공간, 충돌 구, 말단 프레임을 설정한다. | 동작 생성용 설정 파일 |
| 9. 집기와 놓기 | 목표, 제어기와 그리퍼를 통합한다. | 집기부터 놓기까지 전체 동작 확인 |
| 10. 폐루프 기구 구성 | 닫힌 고리를 만드는 관절의 구속 조건을 올바르게 분리한다. | 안정적인 폐루프 기구 |
| 11. 관절 게인 조정 | 계단 입력 응답으로 Kp/Kd와 토크·힘을 조정한다. | 검증된 드라이브 매개변수 |
| 12. 자산 최적화 | 메시, 충돌 형상, 레이어와 instanceability를 최적화한다. | 배포 가능한 경량 자산 |
| 13. 다리형 로봇 설정 | 베이스가 움직이는 articulation, 접촉, 관절 순서와 정책의 구동기 설정을 맞춘다. | 학습 정책으로 제어할 다리형 로봇 자산 |

각 튜토리얼의 숫자를 그대로 복사하기보다 자신의 로봇 질량, 감속비, 적재물과 접촉 재질에 맞춰 측정하고 조정한다.

## 9. 로봇 설정 도구 선택

| 도구 | 역할 | 사용할 때 |
|---|---|---|
| Robot Wizard (Beta) | 로봇 설정 과정을 안내한다. | 처음 물리 구조를 설정할 때 누락을 줄인다. |
| Robot Assembler | 독립 articulation/자산을 고정 관계로 조립한다. | 로봇 팔+그리퍼, 베이스+센서 지지대 |
| Merge Mesh Utility | 많은 메시를 병합한다. | 그리기 호출 수와 계층을 줄이고 일부 개별 편집 기능을 포기할 수 있을 때 |
| Gain Tuner | 관절 계단 입력 응답과 게인을 조정한다. | 가져오기 직후 또는 적재물 변경 후 |
| Grasp Editor | 그리퍼 파지 자세를 작성한다. | 집기 동작을 구성할 때 |
| Lula Robot Description/XRDF Editor | 충돌 구와 동작 생성 설정을 만든다. | RMPflow, RRT, IK를 사용자 로봇에 쓸 때 |
| Asset Validation | 스키마와 자산 구조 문제를 검사한다. | 배포하거나 커밋하기 전 |

Robot Assembler로 결합한 로봇 팔+그리퍼를 동작 생성 알고리즘에서 쓸 때는 알고리즘이 읽는 URDF/XRDF에도 같은 운동학 연결과 말단 프레임 오프셋이 있어야 한다. Stage만 조립하고 Lula 로봇 설명 파일은 로봇 팔 단독으로 남기면 목표 자세와 충돌 구가 어긋난다.

## 10. 매니퓰레이터 설정 핵심

1. 베이스 고정과 articulation 루트를 확인한다.
2. 로봇 팔 관절 토크·힘·속도 제한을 제조사 또는 구동기 모델에 맞춘다.
3. 그리퍼 손가락 끝에 별도 물리 재질을 적용한다.
4. 연동 관절의 주 관절과 배율·오프셋을 확인한다.
5. 로봇 팔과 그리퍼의 충돌 형상이 기본 자세에서 겹치지 않게 한다.
6. 말단 프레임을 실제 TCP에 둔다.
7. 대표 적재물과 최악 자세에서 게인을 시험한다.
8. 필요한 경우 솔버의 위치·속도 반복 횟수을 올리되 성능을 측정한다.

공식 UR10e+2F-140 예제의 솔버 수치나 마찰 1.0은 해당 실습의 시작점이지 모든 로봇의 정답이 아니다.

## 11. 이동형/다리형 설정 핵심

### 이동형

- 바퀴 관절 축과 바퀴 반지름를 실제 충돌 형상 기준으로 측정한다.
- 바퀴 드라이브는 속도 모드라면 강성 0, 감쇠 > 0으로 시작한다.
- 좌우 바퀴 이름과 제어기 순서를 고정한다.
- 캐스터의 충돌 형상과 마찰이 베이스를 끌지 않는지 확인한다.
- 차체 루트를 월드 좌표계에 고정하지 않는다.

### 다리형

- 학습·배포 정책이 사용하는 관절 이름 순서와 `dof_names`가 정확히 같아야 한다.
- 구동기 Kp/Kd, 토크·힘/속도 제한과 동작 크기를 정책 설정과 맞춘다.
- 발의 충돌 형상과 접촉 재질을 검증한다.
- 베이스와 링크 질량·관성이 원본 모델과 같아야 한다.
- 자기 충돌 필터를 정책 학습 환경과 일치시킨다.

## 12. 자산 계층과 레이어 전략

한 파일에 모든 변경을 넣지 않는다. 예를 들어 다음처럼 분리할 수 있다.

```text
my_robot/
  my_robot.usd                    # 다른 장면에서 참조할 파일
  configuration/
    my_robot_base.usd             # 계층과 참조
    my_robot_physics.usd          # 강체·관절·드라이브·재질의 변경값
    my_robot_sensors.usd          # 카메라·IMU·LiDAR prim
  meshes/
    visual/
    collision/
  materials/
  config/
    robot_descriptor.yaml
    robot.xrdf
    motion_policy.yaml
  source/
    my_robot.urdf.xacro
    my_robot.generated.urdf
```

가져오기 도구가 생성한 베이스 레이어를 직접 손으로 대량 수정하면 다시 가져올 때 수정 내용이 사라질 수 있다. 후처리한 속성은 우선순위가 높은 레이어에서 덮어쓰거나 스크립트로 재현한다.

## 13. 기본 동작 자동 검사 설계

최소한 다음 조건을 자동으로 검사한다.

```python
q = robot.get_joint_positions()
qd = robot.get_joint_velocities()

assert robot.num_dof == EXPECTED_DOF
assert list(robot.dof_names) == EXPECTED_DOF_NAMES
assert np.all(np.isfinite(q))
assert np.all(np.isfinite(qd))
assert np.max(np.abs(qd)) < 100.0
```

여기에 다음 실행 조건를 추가한다.

- 초기화를 10회 반복해 자세가 같은지 확인한다.
- 각 관절을 제한 중앙 근처에서 작은 스텝으로 왕복한다.
- 이동형 베이스를 1 m 직진·90° 회전해 오차를 측정한다.
- 그리퍼가 알려진 크기·질량의 물체를 일정 시간 유지하는지 확인한다.
- 카메라/IMU/접촉 센서가 예상 주파수와 배열 형태로 값을 내는지 확인한다.
- headless 실행에서도 동일한 물리 결과 범위에 드는지 확인한다.

## 14. 검증 체크포인트

- [ ] 원본 로봇 설명 파일과 생성된 USD, 가져오기 도구 설정을 함께 보관한다.
- [ ] 크기, 충돌 형상, 질량/관성, 관절 축/제한, 드라이브 순서로 검사했다.
- [ ] 고정형과 이동형 베이스 옵션을 올바르게 골랐다.
- [ ] `dof_names`를 제어기 및 ROS 관절 목록와 비교했다.
- [ ] 사용자 정의 end-effector를 조립한 뒤 URDF/XRDF도 함께 갱신했다.
- [ ] 자산을 독립 Stage와 headless 기본 동작 검사에서 검증했다.
- [ ] 장면에서는 로봇 자산을 복사하지 않고 참조한다.

## 출처

- [Importers and Exporters](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/importers_exporters.html)
- [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [MJCF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_mjcf.html)
- [Robot Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/index.html)
- [Robot Wizard](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/robot_wizard.html)
- [Robot Setup Tutorials Series](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/index.html)
- [Tutorial 2: Assemble a Simple Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_assemble_robot.html)
- [Tutorial 5: Rig a Mobile Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html)
- [Tutorial 7: Configure a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html)
- [Tutorial 10: Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Tutorial 13: Rigging a Legged Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_rig_legged_robot.html)
- [Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_validation.html)
- [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)
