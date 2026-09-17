# USD를 Isaac Sim에서 실행하기

[USD 학습 안내](README.md) · [핵심 개념](CONCEPTS.md) · [라이브러리](LIBRARIES.md)

**USD는 장면과 물리 설정을 기록하고, Isaac Sim은 그 데이터를 읽어 시뮬레이션한다.**
USD 파일을 생성하거나 여는 것만으로 시간이 흐르거나 물체가 낙하하지 않는다.
Isaac Sim 5.1은 USD를 공통 장면 표현으로 사용하고, PhysX로 물리를 계산한다.
([Isaac Sim 소개](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html))

## 1. 세 종류의 Python API를 구분하기

| 도구 | 담당하는 일 | 이번 예제 |
|---|---|---|
| `pxr.UsdGeom`, `pxr.UsdPhysics` | USD Prim과 속성 작성 | 큐브 모양, 강체, 충돌, 질량 설정 |
| `omni.usd` | 실행 중인 Kit 앱의 USD 컨텍스트에 접근 | `get_context().get_stage()`로 현재 Stage 얻기 |
| `isaacsim.core.api.World` | 물리 초기화와 실행, 등록된 객체 관리 | `reset()`과 `step()` |
| `isaacsim.core.prims.RigidPrim` | USD Prim에 대응하는 강체의 상태 접근 | 시뮬레이션 중 위치·속도 읽기 |

`World` Python 객체와 `/World` USD Prim은 다르다. 전자는 실행 관리자이고,
후자는 예제에서 장면 객체를 묶기 위해 만든 `Xform` Prim의 경로다.
`RigidPrim("/World/FallingCube")`도 큐브를 복제하지 않는다. 이미 존재하는 Prim에 접근한다.
([Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html),
[Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html))

Standalone Python에서는 `SimulationApp`을 먼저 생성하고 그 뒤 `omni`, Core API, `pxr`를 import한다.
**이미 실행 중인 Script Editor에서는 `SimulationApp`을 또 만들지 않는다.**
아래 파일은 터미널에서 실행하는 Standalone용이다.
([Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html))

## 2. 모양·강체·충돌체는 서로 다른 정보다

| USD 정의 | 의미 |
|---|---|
| `UsdGeom.Cube.Define(...)` | 큐브 형상과 크기를 정의한다. 이것만으로는 낙하하지 않는다. |
| `UsdPhysics.RigidBodyAPI.Apply(prim)` | 해당 Prim을 강체로 설정한다. 기본 동적 강체는 중력 등의 영향을 받는다. |
| `UsdPhysics.CollisionAPI.Apply(prim)` | 해당 형상을 충돌 계산에 사용한다. |
| `UsdPhysics.MassAPI.Apply(prim)` | 질량·밀도·관성 등의 정보를 작성할 수 있게 한다. |

API schema는 기존 Prim에 역할을 추가한다. 큐브 하나에 위 세 물리 API를 함께 적용할 수 있다.
반대로 이번 바닥은 `CollisionAPI`만 적용하고 강체를 적용하지 않아 정적 충돌체로 쓴다.
`MassAPI`의 질량을 1 kg으로 쓰고 관성을 생략하면, 이 예제에서는 엔진이 충돌 형상으로 관성을 계산한다.
([USD Physics Schema](https://openusd.org/release/api/usd_physics_page_front.html))

`UsdPhysics`는 공통 물리 데이터 표현이고 `PhysxSchema`는 PhysX 전용 설정을 추가하는 NVIDIA schema다.
서로 다른 시뮬레이터가 모든 확장과 설정을 동일하게 지원한다고 가정하면 안 된다.
([Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html))

## 3. 실습: USD로 작성한 큐브를 떨어뜨리기

파일: [04_isaacsim_physics.py](04_isaacsim_physics.py)

필요한 환경은 **Isaac Sim 5.1.0과 해당 버전이 실행되는 GPU·드라이버**다.
ROS나 다운로드한 로봇·환경 자산은 필요하지 않다. 큐브·바닥·조명을 코드로 만든다.
Isaac Sim 전용 Python을 사용하며, 일반 Python의 `usd-core`만으로는 이 실습을 실행할 수 없다.

저장소 루트에서 실행한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 usd/04_isaacsim_physics.py --help

# GUI: 스텝 제한이 없으면 창을 닫을 때까지 유지한다.
"$ISAAC_SIM_PATH/python.sh" usd/04_isaacsim_physics.py

# GUI 없이 물리 240스텝을 진행하고 종료한다. --steps 생략 시에도 240회다.
"$ISAAC_SIM_PATH/python.sh" usd/04_isaacsim_physics.py --headless --steps 240

# 원하는 새 출력 디렉터리를 지정할 수도 있다. 이미 있으면 거부한다.
"$ISAAC_SIM_PATH/python.sh" usd/04_isaacsim_physics.py --headless --output /tmp/usd-fall-new
```

`--steps`에는 양수를 넣는다. GUI에서도 지정하면 해당 스텝 수 후 종료한다.
GUI에서 Pause를 누르면 스텝 수를 늘리지 않고 화면을 유지한다.
Windows에서는 설치 디렉터리의 `python.bat`와 해당 경로 표기법을 사용한다.

### 코드에서 따라갈 흐름

1. `World`가 물리 장면과 1/60초 실행 간격을 준비한다. 길이는 m, 질량은 kg, 위쪽은 Z다.
2. `pxr`로 한 변 0.5 m인 큐브를 중심 높이 2 m에 만들고 강체·충돌·질량을 기록한다.
3. 윗면 높이가 0 m인 고정 바닥을 만들고 조명과 시점을 준비한다.
4. **실행 전** root layer를 `initial_scene.usda`로 저장한다.
5. `world.reset()`으로 물리 핸들을 준비한 뒤 `world.step()`으로 시간을 진행한다.
6. `RigidPrim`으로 실제 위치와 속도를 읽어 CSV에 쓴다. 종료 시 `finally`에서 앱을 닫는다.

### 결과를 읽는 방법

기본 출력은 `outputs/usd/04_isaacsim_physics/<실행시각>/`에 저장된다.

| 파일 | 확인할 내용 |
|---|---|
| `initial_scene.usda` | 텍스트 편집기로 `Cube`, `apiSchemas`, `physics:mass`, `xformOp:translate`를 찾는다. |
| `heights.csv` | `step`, `time_s`, 중심 높이 `z_m`, 수직 속도 `vz_m_s`를 확인한다. |

정상적인 240스텝 실행에서는 큐브가 낙하한 뒤 **중심 높이 약 0.25 m**에서 멈춘다.
바닥 윗면 0 m에 큐브의 반높이 0.25 m를 더한 값이다. 수직 속도는 0에 가까워진다.
접촉 계산에는 작은 수치 오차가 있으므로 마지막 자릿수의 정확한 일치를 요구하지 않는다.

`reset()`도 초기화를 위해 내부 물리 스텝을 진행할 수 있다. 따라서 CSV의 `step=0`은
**우리 루프가 시작되기 전의 측정값**이며 `time_s=0`, `z_m=2`를 보장하지 않는다.
`time_s`는 `world.current_time`을 그대로 기록하므로 `step / 60`과 시작 오프셋이 있을 수 있다.
`--steps 1`처럼 짧게 실행하면 아직 공중에 있는 것이 정상이다.

저장한 USD에는 **낙하 전 설계값**이 남는다. 측정 CSV는 시간에 따른 실행 결과다.
이 스크립트는 낙하 애니메이션을 USD time sample로 기록하지 않는다.
이번 장면은 모든 데이터를 root layer에 직접 작성했으므로 이 layer의 저장으로 충분하지만,
외부 reference·sublayer를 쓰는 일반 장면에서는 해당 의존 파일도 함께 관리해야 한다.

## 4. URDF와 USD는 무엇이 다른가?

| 관점 | URDF | USD / USD Physics |
|---|---|---|
| 주된 대상 | ROS에서 사용하는 로봇 모델 | 로봇·환경·조명·재질 등을 포함하는 장면과 자산 |
| 연결 구조 | link를 joint의 parent/child로 연결하는 운동학 트리 | Prim 계층과 물리 joint 관계를 따로 표현 |
| 외형과 물리 | visual, collision, inertial 정보 표현 | geometry와 물리 schema로 역할을 나누어 표현 |
| 장면 구성 | 로봇 XML과 참조 mesh 중심 | Layer, Reference, Payload, Variant로 자산과 수정 사항을 합성 |
| 실행 | URDF 자체는 시뮬레이터가 아님 | USD 자체도 시뮬레이터가 아니며 Isaac Sim 등이 실행 |

**USD의 Prim 부모·자식 관계가 곧 로봇 관절 연결을 뜻하지는 않는다.**
예를 들어 `/Robot/base`와 `/Robot/arm`을 형제 Prim으로 배치하고, 별도의 joint Prim의
`physics:body0`·`physics:body1` Relationship으로 연결할 수 있다.
USD 계층은 여전히 트리지만, 물리 연결은 이 관계들로 표현한다.
폐루프가 있는 모델은 엔진의 articulation 제약에 맞춘 추가 구성이 필요하다.
([USD Physics Schema](https://openusd.org/release/api/usd_physics_page_front.html))

Isaac Sim의 URDF Importer는 로봇 모델을 USD로 변환한다. 변환 뒤에는 다음을 확인한다.

- mesh 경로와 크기, 링크·관절 이름: 이름에 포함된 특수 문자는 변환 과정에서 바뀔 수 있다.
- 질량·관성·충돌 형상: 누락된 질량의 기본값과 충돌 근사 설정에 따라 결과가 달라질 수 있다.
- 고정/이동 베이스, 관절 축·한계, drive 강성·감쇠와 제어 방식.

따라서 **URDF → USD → URDF의 무손실 왕복을 전제로 하지 않는다**는 것이 이 튜토리얼의 작업 원칙이다.
5.1의 USD to URDF Exporter도 운동학 폐루프를 지원하지 않고, 한 링크만 연결된 joint에 제약이 있다.
센서·렌더링·OmniGraph 같은 USD 장면 설정은 URDF 로봇 모델과 별도로 관리한다.
([URDF Importer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html),
[USD to URDF Exporter](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_omni_exporter_urdf.html))

## 5. 로봇 자산이 커지면 파일을 어떻게 나눌까?

NVIDIA의 Asset Structure 안내는 원본 형상, 시뮬레이션용 구조, 물리·센서·제어 기능을 나눈다.
원본을 다시 가져와도 이후의 물리 조정과 센서 설정을 보존하기 위한 구성이다.

| 역할 | 공식 안내의 파일 예시 |
|---|---|
| 원본 구조·부품·재질 | `asset_base.usd`, `parts.usd`, `materials.usd` |
| 정리·최적화한 구조 | `asset_sim_optimized.usd` |
| 물리·센서·제어·ROS 기능 | `asset_physics.usd`, `asset_sensors.usd`, `asset_control.usd`, `asset_ros.usd` |
| 합성한 최종 자산 | `asset.usd` |

해당 안내는 최적화 자산을 sublayer로, 물리 설정을 default Prim의 reference로,
센서·제어 같은 선택 기능을 payload로 연결하고 variant로 구성을 선택하는 패턴을 설명한다.
이는 **Isaac Sim 자산 제작을 위한 구성 예시**이며 모든 USD 파일의 필수 구조는 아니다.
큐브 실습에서는 한 layer부터 이해하고, 재사용할 로봇이 생겼을 때 분리하면 된다.
([Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html))

## 출처 및 더 읽기

Isaac Sim 항목은 **5.1.0 문서**를 기준으로 요약했다. 아래는 원문의 더 자세한 설명과 실습이다.

- [NVIDIA OpenUSD 개발자 허브](https://developer.nvidia.com/openusd): USD 학습 과정·도구·기술 자료의 출발점.
- [Isaac Sim 5.1 소개](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html): USD, PhysX, Kit의 역할.
- [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html): `SimulationApp`과 import 순서, Standalone 실행.
- [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html): `World`, `Scene`, 초기화와 물리 스텝.
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html): 물리 schema, 시간, 충돌과 재질.
- [USD Physics Schema](https://openusd.org/release/api/usd_physics_page_front.html): 공식 5.1 물리 문서에서 연결하는 OpenUSD 공통 물리 규약.
- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html): 변환 옵션, 이름 규칙, 관절 drive.
- [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html): 실제 로봇 변환 절차.
- [USD to URDF Exporter](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_omni_exporter_urdf.html): 내보내기와 변환 제약.
- [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html): 재사용 가능한 로봇 자산의 파일 구성.
