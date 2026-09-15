# 09. Core API: 원시 USD를 감싸는 로봇용 도구

권장 학습 순서 **09** · Python 실행 환경과 USD 기초 · 출처 ID `t093`

## 이 실습의 의도

원시 USD/Physics API로 속성을 하나씩 붙인 큐브와 `DynamicCuboid`로 만든 큐브가 같은 종류의 물리 결과를 내는지 비교한다. 두 큐브의 한 변·질량·시작 높이를 0.4 m·1 kg·2 m로 맞추고 위치만 벌려, Core API가 장면과 물리 설정을 감싸는 편의 도구라는 점에 집중한다. 기본 실행은 실제 스키마 목록, 초기 장면, 매 스텝의 높이를 각각 `schemas.json`, `scene.usda`, `heights.csv`로 남긴다.

## 실행 후 확인할 것

- Stage에서 X=−0.5 m의 `/World/RawCube`와 X=+0.5 m의 `/World/WrappedCube`를 구분한다. 색 대신 Prim 경로로 확인하고 두 큐브가 모두 낙하하는지 본다.
- `schemas.json`에서 두 경로에 `PhysicsRigidBodyAPI`, `PhysicsCollisionAPI`, `PhysicsMassAPI`가 있는지 확인한다. 편의 API가 추가 스키마를 붙일 수 있으므로 전체 목록이 완전히 같을 필요는 없다.
- 충분히 실행한 `heights.csv`의 `raw_z_m`, `wrapped_z_m`이 모두 약 0.2 m로 정착하는지 확인한다. 초기 낙하 추이도 함께 비교하며 수치가 모든 스텝에서 완전히 일치해야 한다고 가정하지 않는다. 짧은 `--steps`는 접촉 전일 수 있다.
- `scene.usda`는 reset과 낙하 이전에 저장한 장면이다. 재개방했을 때 큐브가 높이 2 m에 있어도 정상이며, Property의 강체·충돌·질량 설정과 CSV의 실행 결과를 구분해서 읽는다.
- 종료 시 `Scene registry: raw wrapped` 출력이 나오는지 보고 코드의 `get_object("raw")`와 Prim 경로 `/World/RawCube`를 대응시킨다. Python Scene의 등록 이름과 USD Stage 주소는 서로 다른 조회 기준이다.

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py`을 실행한다. 두 큐브가 동시에 낙하한다. 각 큐브는 X=−0.5 m와 +0.5 m에 놓이며 원시 큐브에는 별도 색을 지정하지 않는다.
2. `run.py`에서 `/World/RawCube`에 `UsdGeom.Cube`, `RigidBodyAPI`, `CollisionAPI`, `MassAPI`를 적용하는 부분을 읽는다. 원시 API는 필요한 속성을 각각 작성한다.
3. `/World/WrappedCube`의 `DynamicCuboid(size=0.4, mass=1.0)`가 같은 기능을 짧게 구성하는지 비교한다.
4. `World.scene.add`는 Python 객체를 등록한다. 원시 USD Prim은 이미 장면에 존재하지만 `RigidPrim` view를 등록해야 이 실습에서 reset 이후의 물리 상태를 일관되게 읽을 수 있다.
5. `schemas.json`에서 두 Prim에 `PhysicsRigidBodyAPI`, `PhysicsCollisionAPI`, 질량 관련 API가 있는지 확인한다. 편의 API는 재질·PhysX 관련 속성을 더 만들 수 있으므로 목록이 완전히 같아야 하는 것은 아니다.
6. 충분한 스텝 후 두 높이가 모두 약 0.2 m에 도달하는지 CSV 마지막 줄을 확인한다. 초기 한 변이 0.4 m이므로 중심은 지면보다 절반 높이에 있다.
7. GUI의 **File > Open**으로 `scene.usda`를 열고 Stage의 두 Prim을 선택한다. Property에서 Rigid Body, Collision, Mass 속성을 비교한다.

## 다섯 이름을 구분하기

| 이름 | 이 코드에서 맡은 역할 |
|---|---|
| Application | `SimulationApp`: Kit, 창, 렌더링과 확장 수명 관리 |
| Simulation | 물리 엔진이 시간에 따라 상태를 갱신하는 실행 |
| World | 시간 간격, reset/step, Scene을 함께 관리하는 Core 객체 |
| Scene | `world.scene`: Python 객체의 이름과 핸들을 등록하는 관리 객체 |
| Stage | `omni.usd.get_context().get_stage()`: Prim·계층·속성이 존재하는 USD 장면 |

`UsdPhysics.Scene`은 위 Python Scene과 또 다르다. Stage 안에 존재하는 물리 설정 Prim으로 중력 방향·크기를 저장한다. 단위를 m로 설정했으므로 중력은 9.81 m/s²다. `PhysxSceneAPI`는 이 물리 Prim에 CCD 같은 PhysX 전용 속성을 더한다.

5.1 문서는 Core Experimental API의 도입도 안내한다. 이 패키지는 해당 페이지의 현행 Core API 예제를 재현하기 위해 `isaacsim.core.api`와 `isaacsim.core.prims`를 사용한다. 실험 API로 조용히 치환하지 않았다.

## 한 가지 변수 실험과 문제 해결

`run.py`에서 원시 큐브의 `CreateMassAttr(1.0)`만 2.0으로 바꾸고 새 출력 디렉터리에서 비교한다. 공기저항을 넣지 않은 자유낙하에서는 질량이 낙하 가속도를 바꾸지 않는다. 소스 수정 전후의 물리 설정을 같은 조건으로 유지한다.

한 큐브만 바닥을 통과하면 CollisionAPI 누락을 확인한다. 두 큐브가 모두 멈춰 있으면 Play/reset과 rigid-body 적용을 확인한다. Prim 경로와 Scene의 객체 이름은 다르므로 `/World/RawCube` 대신 `raw`를 `get_object`에 넣는다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

Python 구문 컴파일과 일반 Python의 `--help`는 앱 없이 확인할 수 있다. 이 검사는 GPU, 자산 로딩, GUI 표현, 물리 결과의 실제 실행 검증을 대신하지 않는다. `tutorial.json`의 verification이 `not_run`이면 해당 시뮬레이터 실행은 아직 검증되지 않은 상태다.
