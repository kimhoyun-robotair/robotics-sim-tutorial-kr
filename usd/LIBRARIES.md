# USD를 다루는 라이브러리와 실행 환경

[학습 안내](README.md) · 이전: [핵심 개념](CONCEPTS.md) · 다음: [Isaac Sim과 URDF](ISAAC_SIM.md)

## 1. Python에서는 `pxr`부터 시작합니다

OpenUSD의 주 구현은 C++이며 Python 바인딩을 **`pxr` 네임스페이스**로 제공합니다. 설치 패키지 이름 `usd-core`와 import 이름 `pxr`가 다릅니다.

| 모듈 | 맡는 일 | 이 튜토리얼에서 볼 API |
|---|---|---|
| `pxr.Usd` | 합성된 장면 작성·조회 | `Stage`, `Prim`, `EditContext` |
| `pxr.Sdf` | Layer와 경로·자료형 | `Layer`, `Path`, `ValueTypeNames` |
| `pxr.Gf` | 벡터·행렬·쿼터니언 수학 | `Vec3d`, `Vec3f` |
| `pxr.UsdGeom` | 형상·좌표 변환·카메라 | `Xform`, `Cube`, `XformCache` |
| `pxr.UsdShade` | 재질·셰이더 연결과 바인딩 | `Material`, `Shader`, `MaterialBindingAPI` |
| `pxr.UsdLux` | 조명 데이터 | `DistantLight` |
| `pxr.UsdPhysics` | 공통 물리 스키마 | `RigidBodyAPI`, `CollisionAPI`, `MassAPI` |

자주 사용하는 모듈의 역할은 [NVIDIA OpenUSD Modules](https://docs.nvidia.com/learn-openusd/latest/stage-setting/usd-modules.html), 스키마 구분은 [Schemas](https://docs.nvidia.com/learn-openusd/latest/scene-description-blueprints/schemas.html)를 참고하세요. 재질과 조명은 해당 데이터를 해석할 렌더러가 필요합니다.

처음에는 `Usd`로 Stage/Prim을 다루고, 형상은 `UsdGeom`, 물리는 `UsdPhysics`처럼 분야별 API를 추가하면 됩니다. `Sdf`로 저수준 Prim 명세를 직접 조립하는 방법부터 익힐 필요는 없습니다.

`cube.GetPrim()`은 `UsdGeom.Cube`가 감싼 같은 Prim을 가져옵니다. 새로운 큐브를 만드는 호출이 아닙니다. `CreateSizeAttr()`는 속성 작성용, `GetSizeAttr()`는 속성 접근용이며, 마지막의 `.Set(value)`와 `.Get()`이 실제 값 쓰기·읽기입니다.

## 2. 일반 Python: GPU 없이 USD 파일 작성하기

예제 **01–03은 `usd-core`만 사용**합니다. Isaac Sim, ROS 2, GPU, Nucleus 서버가 필요하지 않습니다. 저장소 루트에서 Ubuntu의 Python 3.12로 별도 가상환경을 만드세요.

```bash
python3.12 -m venv .venvs/usd-tutorial
.venvs/usd-tutorial/bin/python -m pip install "usd-core==25.5.1"
.venvs/usd-tutorial/bin/python -c 'from pxr import Usd; print(Usd.GetVersion())'
.venvs/usd-tutorial/bin/python usd/01_stage_prims.py
```

여기서 `25.5.1`은 예제 재현을 위한 PyPI 패키지 버전이고, `Usd.GetVersion()`은 `(0, 25, 5)`를 출력합니다. **Isaac Sim의 제품 버전 5.1과 OpenUSD 버전은 별개**입니다. `venv` 모듈이 없는 Ubuntu 환경에서는 배포판의 `python3.12-venv` 패키지를 먼저 준비하세요. Windows에서는 생성한 가상환경의 `Scripts/python.exe`를 사용합니다.

NVIDIA도 `usd-core`를 통한 Python 환경 구성을 안내합니다. 이 패키지로 USD 데이터 API를 실행할 수 있으며, `usdview` GUI나 Isaac Sim 앱은 별도로 준비합니다. [NVIDIA Python·usdview 설치 안내](https://docs.nvidia.com/learn-openusd/latest/usdview-install-instructions.html)

## 3. Isaac Sim 5.1: 앱이 실행 환경을 제공합니다

| 모듈·도구 | 언제 사용하나요? |
|---|---|
| `isaacsim.SimulationApp` | Standalone Python에서 Kit 앱 시작·업데이트·종료 |
| `omni.usd` | 실행 중인 Kit의 USD context와 현재 Stage 접근 |
| `isaacsim.core.api.World` | 시뮬레이션 초기화와 물리·렌더링 step 관리 |
| `isaacsim.core.prims` | 기존 Prim의 pose·강체 상태 등을 편리하게 제어 |
| `pxr.PhysxSchema` | PhysX 전용 물리 설정. Isaac Sim에 포함된 확장 사용 |

Isaac Sim 5.1에서는 **앱 생성 후 `omni`, `pxr`, Core API를 import**하는 실행 순서를 사용합니다. `04_isaacsim_physics.py`가 이 방식입니다. 일반 가상환경에 설치한 `usd-core`에는 `omni.usd`, Isaac Sim의 Core API와 PhysX 전용 확장이 들어 있지 않습니다. [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html), [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)

```bash
# 위 가상환경을 활성화하지 않은 터미널에서 실행합니다.
export ISAAC_SIM_PATH="$HOME/isaacsim"  # 자신의 Isaac Sim 5.1 설치 위치
"$ISAAC_SIM_PATH/python.sh" usd/04_isaacsim_physics.py --headless --steps 240
```

Isaac Sim에 포함된 Python에는 별도의 `usd-core`를 덧씌우지 마세요. 앱과 함께 제공된 USD 라이브러리 조합을 사용합니다. Script Editor에서는 앱이 이미 실행 중이므로 `SimulationApp`을 다시 만들지 않습니다. 자세한 실행 흐름과 물리 결과는 [Isaac Sim 예제 안내](ISAAC_SIM.md)에 있습니다.

## 4. 파일을 조사하는 도구

- **텍스트 편집기**: 이 실습의 `.usda`를 열어 Prim 정의, `subLayers`, `references`, `over`를 확인합니다.
- **usdview**: Prim 계층·속성·합성 출처 등을 탐색하는 OpenUSD 도구입니다. NVIDIA의 별도 라이브러리/도구 배포 또는 OpenUSD 빌드로 준비합니다.
- **Isaac Sim GUI**: 생성한 파일을 열어 Stage와 Property를 확인하고, 물리 데이터가 있는 장면은 Play로 실행합니다.

조회할 때는 “이 값은 어느 Prim의 속성인가?”, “어느 Layer에서 왔는가?”, “현재 Edit Target은 어디인가?”를 순서대로 확인하세요.

## 출처 및 더 읽기

- [NVIDIA OpenUSD 개발자 허브](https://developer.nvidia.com/openusd): 라이브러리·도구 다운로드와 학습 자료.
- [NVIDIA OpenUSD Modules](https://docs.nvidia.com/learn-openusd/latest/stage-setting/usd-modules.html): 모듈 구분과 Python 사용법.
- [NVIDIA Installing usdview and Setting Up Python](https://docs.nvidia.com/learn-openusd/latest/usdview-install-instructions.html): 운영체제별 도구·가상환경 설정.
- [OpenUSD Python API](https://openusd.org/release/api/index.html): 전체 API 참조. C++ 클래스 `UsdStage`는 Python에서 주로 `Usd.Stage`처럼 표시됩니다.
- [Isaac Sim 5.1 Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html): 앱 초기화와 Standalone Python.
- [Isaac Sim 5.1 Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html): 시뮬레이터 안에서 USD 사용하기.
- [저장소 Python API 사전](../api/INDEX.md): 개별 API의 인자와 사용 예를 한국어로 더 찾아보기.
