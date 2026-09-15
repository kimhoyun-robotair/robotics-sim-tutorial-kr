# 09. Core API는 USD와 물리 설정을 어떻게 감쌀까요?

## 이번에 배우는 것

**USD 속성을 직접 붙인 큐브와 DynamicCuboid로 만든 큐브를 비교하며, Core API가 줄여 주는 작업을 확인합니다.**

00번에서 외형·강체·충돌을 구분했습니다. 이번에는 필요한 물리 속성을 `pxr`로 하나씩 작성하는 방식과, Isaac Sim의 편의 클래스로 구성하는 방식을 나란히 사용합니다. 두 큐브의 크기·질량·시작 높이를 같게 맞추고 x 위치만 벌립니다.

| 구분 | 직접 작성한 큐브 | Core API 큐브 |
|---|---|---|
| Prim 경로 | `/World/RawCube` | `/World/WrappedCube` |
| 생성 | `UsdGeom.Cube`와 USD Physics API | `DynamicCuboid` |
| 초기 위치 | `(-0.5, 0, 2)` m | `(0.5, 0, 2)` m |
| 한 변·질량 | 0.4 m·1 kg | 0.4 m·1 kg |
| Scene 이름 | `raw` | `wrapped` |
| 관찰값 | `raw_z_m` | `wrapped_z_m` |

Core API를 사용해도 장면은 USD Prim과 속성으로 구성됩니다. 편의 클래스가 어떤 속성을 준비했는지와 실제 낙하 결과를 함께 확인하는 것이 이번 실습의 목표입니다.

## 1. 두 큐브를 같은 조건에서 떨어뜨리기

Isaac Sim 5.1과 지원 GPU·드라이버를 준비하세요. 외부 자산 없이 도형·지면·광원을 코드로 만듭니다. 아래 명령은 저장소 루트 기준입니다.

```bash
~/isaacsim/python.sh src/09_python_usd_core_api_overview/run.py --steps 120
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 120단계를 마치면 앱이 종료됩니다. `--steps`를 빼면 GUI를 계속 열어 두고, `--headless`를 추가하면 창 없이 실행합니다. Headless에서 단계 수를 생략하면 120단계입니다.

### 코드에서 볼 부분

```python
raw_cube = UsdGeom.Cube.Define(stage, "/World/RawCube")
raw_cube.CreateSizeAttr(0.4)
raw_cube.AddTranslateOp().Set(Gf.Vec3d(-0.5, 0, 2))
UsdPhysics.RigidBodyAPI.Apply(raw_cube.GetPrim())
UsdPhysics.CollisionAPI.Apply(raw_cube.GetPrim())
UsdPhysics.MassAPI.Apply(raw_cube.GetPrim()).CreateMassAttr(1.0)
```

앞의 세 줄은 모양과 위치를 작성합니다. 뒤의 세 줄은 같은 Prim에 강체·충돌·질량 기능을 붙입니다. USD에서 **스키마**는 객체의 종류나 사용할 수 있는 속성을 정의합니다. `Cube`는 종류를 정하는 스키마이고 `RigidBodyAPI` 등은 기능을 추가하는 API 스키마입니다.

오른쪽 큐브는 다음 구성으로 같은 기본 조건을 준비합니다.

```python
wrapped = world.scene.add(
    DynamicCuboid(
        prim_path="/World/WrappedCube", name="wrapped",
        position=np.array([0.5, 0, 2]), size=0.4, mass=1.0,
    )
)
```

외형과 물리 기능을 직접 세 줄로 추가하는 부분이 생성자 안에 들어 있습니다. 왼쪽 큐브는 이미 USD에 존재하므로, 상태 관찰용 `RigidPrim`을 Scene에 등록합니다.

```python
raw = world.scene.add(RigidPrim("/World/RawCube", name="raw"))
```

이 등록은 두 번째 큐브 생성이 아닙니다. 기존 Prim을 Python 객체로 다루고, `world.reset()` 때 물리 핸들을 초기화하기 위한 연결입니다.

### 실행 결과 확인하기

색을 기준으로 구분하지 말고 Stage의 두 경로를 선택해 확인하세요. 두 큐브가 함께 낙하하고 충분히 진행하면 중심 높이가 약 **0.4 ÷ 2 = 0.2 m**가 되는지 봅니다.

결과는 이 폴더의 `output/날짜-시간/`에 저장됩니다.

| 파일 | 저장 시점·내용 | 확인할 부분 |
|---|---|---|
| `schemas.json` | 초기 장면의 적용 스키마 목록 | 두 Prim의 강체·충돌·질량 스키마입니다. |
| `scene.usda` | reset과 낙하 전의 루트 레이어 | 큐브 중심 높이 2 m와 물리 속성입니다. |
| `heights.csv` | 각 `world.step()` 이후 상태 | `step`, `raw_z_m`, `wrapped_z_m`입니다. |

120단계는 물리 시간 약 2초입니다. 두 높이의 전체 추이를 비교하되 매 단계 소수점 값이 완전히 같아야 한다고 가정하지 마세요. 편의 API가 추가로 준비하는 재질·PhysX 설정이 있을 수 있습니다.

## 2. 스키마 목록과 두 가지 Scene 읽기

첫 실행이 끝나면 `schemas.json`을 텍스트 편집기로 엽니다. 다음 세 이름을 두 큐브의 목록에서 찾아보세요.

- `PhysicsRigidBodyAPI`: 움직이는 강체로 다룹니다.
- `PhysicsCollisionAPI`: 접촉을 계산할 충돌 형상을 사용합니다.
- `PhysicsMassAPI`: 질량 관련 속성을 설정합니다.

전체 목록이 일치하는지보다 **같은 물리 역할이 준비되어 있는지** 먼저 확인하세요. GUI의 File > Open으로 `scene.usda`를 열어 각 Prim의 Property에서도 대응하는 설정을 볼 수 있습니다.

### 코드에서 볼 부분

```python
physics = world.get_physics_context().prim_path
scene = UsdPhysics.Scene.Get(stage, physics)
scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
scene.CreateGravityMagnitudeAttr(9.81)
PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateEnableCCDAttr(True)
```

여기의 `scene`은 Stage 안의 **물리 설정 Prim**입니다. Z 음의 방향으로 9.81 m/s²의 중력을 작성하고 PhysX 전용 CCD 설정을 켭니다. CCD는 빠른 이동에서 접촉을 놓치는 일을 줄이기 위한 연속 충돌 검출 설정입니다.

반면 `world.scene`은 Python 객체를 이름으로 관리하는 곳입니다. 종료 직전 다음 조회가 이 차이를 보여줍니다.

```python
world.scene.get_object("raw").name
world.scene.get_object("wrapped").name
```

Stage 경로 `/World/RawCube` 대신 등록 이름 `raw`를 사용합니다. USD 경로와 Scene 등록 이름을 혼동하면 객체가 화면에 있어도 Python 조회에 실패할 수 있습니다.

### 실행 결과 확인하기

터미널의 `Scene registry: raw wrapped`를 확인하세요. 이는 Python 등록 이름을 읽은 결과입니다. `schemas.json`의 키는 `/World/RawCube`, `/World/WrappedCube`이며 같은 객체를 USD 주소로 나타냅니다.

저장한 `scene.usda`를 열었을 때 큐브가 공중에 있는 것도 예상한 결과입니다. 그 파일은 초기 구성을 저장했고 실제 낙하 높이는 CSV에 기록했기 때문입니다.

## 3. Application·World·Scene·Stage 정리

| 이름 | 이번 실습에서 연결되는 대상 |
|---|---|
| Application | `SimulationApp`이 관리하는 Kit 앱·확장·창입니다. |
| World | 시간 간격·초기화·물리 진행을 관리합니다. |
| Python Scene | `raw`, `wrapped`라는 이름으로 객체를 등록합니다. |
| USD Stage | `/World/RawCube` 같은 Prim과 속성을 담습니다. |
| USD Physics Scene | Stage 안에서 중력 등 물리 설정을 담는 Prim입니다. |

**Core API는 USD를 별개의 장면 형식으로 바꾸는 도구가 아닙니다.** 반복되는 속성 작성과 객체 초기화·관찰을 Python에서 다루기 쉽게 묶습니다. 두 큐브가 같은 종류의 낙하를 하는 이유를 스키마와 출력 높이 양쪽에서 설명해 보세요.

## 4. 간단한 확인 실험

`run.py`의 원시 큐브 질량 한 곳만 `CreateMassAttr(1.0)`에서 `CreateMassAttr(2.0)`으로 바꿔 같은 120단계를 실행합니다. 오른쪽 큐브의 `mass=1.0`은 유지하세요.

공기저항을 추가하지 않은 자유낙하에서 질량을 두 배로 했다고 낙하 가속도가 두 배가 되지는 않습니다. 접촉 전 CSV의 두 높이를 비교하고, 충분히 진행한 정착 높이가 여전히 약 0.2 m인지 봅니다. 질량 값 자체는 `scene.usda`나 GUI Property에서 확인하세요. 스키마 이름 목록에는 질량 숫자가 기록되지 않습니다.

## 실행할 때 막히면

- **한 큐브만 바닥을 통과함**: 해당 Prim에 `PhysicsCollisionAPI`가 있는지 확인하세요. 외형과 강체만으로 접촉이 생기지는 않습니다.
- **`get_object()`로 찾지 못함**: USD 경로가 아니라 `raw` 또는 `wrapped`를 사용해야 합니다.
- **저장 장면과 마지막 CSV 높이가 다름**: `scene.usda`는 낙하 전 장면입니다. 실제 시간별 결과는 CSV를 읽으세요.
- **두 큐브 모두 움직이지 않음**: 실행 중 타임라인을 멈췄는지 확인하고 프로그램을 다시 실행해 reset부터 진행합니다.
- **출력 경로 중복 오류**: `--output`에 새 폴더를 지정하거나 옵션을 생략하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)에 대응합니다. 여기서는 `isaacsim.core.api`와 `isaacsim.core.prims`를 사용해 원시 USD 작성과 Core 래퍼의 관계를 비교합니다. 공식 페이지에서 소개하는 다른 API 계열로 전환하는 실습은 포함하지 않습니다.

스키마 목록·초기 장면·높이 CSV는 이 폴더의 비교 자료입니다. `tutorial.json`의 실행 검증 상태는 `not_run`이며, 수치와 화면은 위 절차로 확인할 기대 기준입니다.
