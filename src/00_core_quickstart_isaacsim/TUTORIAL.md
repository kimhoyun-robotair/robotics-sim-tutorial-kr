# 00. Isaac Sim 기본 사용: 보이는 큐브와 물리 큐브

권장 학습 순서 **00** · 첫 실행과 로봇 만나기 · 출처 ID `t001`

이 패키지는 Isaac Sim 5.1 공식 **Isaac Sim Basic Usage Tutorial**을 세 가지 방식으로 실습한다. GUI에서 직접 만든 장면, Script Editor로 만든 장면, 터미널에서 실행한 장면이 같은 USD/PhysX 데이터를 다룬다는 것을 확인한다. 다른 로컬 튜토리얼이나 공통 모듈을 읽을 필요가 없다.

## 준비와 결과

Isaac Sim **5.1.0**을 설치하고 해당 버전이 지원하는 NVIDIA GPU/드라이버를 준비한다. 아래 명령은 Linux 설치 경로가 `~/isaacsim`인 경우다. Windows에서는 동일한 파일을 설치 폴더의 `python.bat`으로 실행한다. `python3 run.py --help`는 옵션 확인용이며 시뮬레이션 실행에는 설치에 포함된 Python을 사용한다. 기본 도형만 사용하므로 로봇 자산 다운로드는 필요하지 않다.

예상 결과는 노란 큐브가 공중에 남고, 빨간 큐브가 바닥을 통과하며, 청록색과 파란색 큐브는 바닥 위에 멈추는 장면이다. 보라색에 해당하는 원시 USD 큐브는 회전·스케일 변환만 받는다. `heights.csv`에는 계산된 실제 높이가 기록된다.

## 1. 독립 Python 실행

이 패키지 폴더에서 실행한다. 패키지를 다른 곳에 복사해도 같은 명령을 사용할 수 있다.

```bash
python3 run.py --help
~/isaacsim/python.sh run.py
~/isaacsim/python.sh run.py --headless --steps 240 --height 2.0
```

1. `run.py`는 먼저 옵션을 읽고 `SimulationApp`을 만든다. 이후에만 `omni`, `pxr`, Core API를 가져온다.
2. 지면과 평행광을 만들고, 네 가지 큐브를 서로 떨어진 위치에 배치한다. 초기 높이는 중심 기준 1.5 m다.
3. `Visual`은 렌더링만 담당한다. `RigidOnly`는 `RigidPrim`으로 강체 속성만 추가한다. `Converted`에는 `GeometryPrim.apply_collision_apis()`도 추가한다. `Dynamic`은 `DynamicCuboid` 한 번으로 강체와 충돌을 함께 만든다.
4. `RawUsd`에는 `UsdGeom.Cube`와 세 개의 xform 연산을 직접 작성한다. 노란 큐브에도 Core API로 회전과 스케일을 적용해 두 표현을 비교한다.
5. `world.reset()`으로 물리 객체를 초기화한 뒤 1/60초씩 전진한다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 물리를 계속 계산한다. `--steps 240`을 명시하면 물리 시간 4초 후 종료하며, `--headless`에서 생략한 경우도 240스텝으로 끝난다.
6. 출력 경로에 생성된 `initial_scene.usda`를 GUI의 **File > Open**으로 열면 초기 장면을 다시 살펴볼 수 있다. `heights.csv` 마지막 줄에서 `visual_z_m`은 초기 높이, `rigid_only_z_m`은 음수, 나머지 두 높이는 약 0.15 m인지 확인한다. 충돌의 작은 허용 오차는 정상이다. 짧은 `--steps` 값은 아직 낙하 중일 수 있다.

기본 출력은 이 패키지의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있으며 기존 폴더는 덮어쓰지 않는다. CSV의 시간은 벽시계 시간이 아니라 물리 스텝 수 × 1/60초다.

## 2. GUI로 같은 개념 만들기

1. `~/isaacsim/isaac-sim.selector.sh`에서 앱을 시작하고 **File > New**로 빈 Stage를 만든다.
2. **Create > Physics > Ground Plane**, **Create > Lights > Distant Light**를 차례로 선택한다. Light의 Property에서 Intensity를 1000으로 둔다.
3. **Create > Shape > Cube**로 큐브를 만든다. Stage 트리에서 선택하고 Property의 Transform에서 중심 위치 Z를 `1.5`, 모든 Scale을 `0.15`로 지정한다. 기본 USD Cube Size가 2인 경우 실제 한 변은 0.3 m다. Size가 다른 경우 한 변이 0.3 m가 되도록 조정한다.
4. **Play**를 누른다. 큐브가 떠 있는 이유는 아직 강체가 아니기 때문이다. **Stop**을 누른다.
5. 큐브를 선택한 상태에서 Property의 **Add > Physics > Rigid Body with Colliders Preset**을 선택한다. **Play**를 누르면 떨어져 바닥에서 멈춘다.
6. **Stop** 후 `W` 이동, `E` 회전, `R` 스케일 도구를 각각 사용한다. 이동/회전 아이콘을 길게 눌러 Local/World 좌표계를 비교한다. 정확한 값은 Property에 입력하며 파란 초기화 버튼으로 복원한다. `Esc`는 선택 해제다.
7. **File > Save As**로 본인이 정한 새 USD 경로에 저장한다. 기존 장면을 덮어쓰지 않도록 새 이름을 사용한다.

## 3. Script Editor 방식

새 GUI 인스턴스에서 **File > New**, **Window > Script Editor**를 연다. 로컬 `script_editor.py` 내용을 탭에 붙여 넣고 **Run**을 누른다. 이 파일은 이미 실행 중인 앱을 사용하므로 `SimulationApp`을 만들지 않는다. 이어서 **Play**를 누르면 청록색/파란색 큐브만 떨어진다. 같은 Stage에서 재실행하면 중복 생성을 막는 오류가 나므로 **File > New** 후 실행한다.

기존 큐브의 물리/충돌 속성을 직접 분리해 보려면 **Stop** 후 새 탭에서 아래를 실행한다. 기존 노란 큐브가 강체가 되지만 충돌이 없으므로 지면을 통과한다.

```python
from isaacsim.core.prims import RigidPrim
RigidPrim("/World/Quickstart/Visual")
```

다시 **Stop** 후 아래를 실행하고 **Play**한다. 필요하면 Property에서 노란 큐브의 Z를 1.5로 복원한다.

```python
from isaacsim.core.prims import GeometryPrim
GeometryPrim("/World/Quickstart/Visual").apply_collision_apis()
```

Script Editor에서 **Run**은 Python 문장을 한 번 실행한다. GUI의 Play가 이후의 물리 시간을 전진시킨다. 독립 스크립트에서는 `world.step()`을 호출하는 반복문이 이 역할을 맡는다. 공식 페이지의 Extensions 탭도 이 Script Editor 워크플로를 사용한다.

## API와 USD를 읽는 법

| 이름 | 이 실습에서의 의미 |
|---|---|
| Stage / Prim | Stage는 장면 전체이고 Prim은 `/World/Converted`처럼 경로가 있는 객체다. USD 파일은 이 구조와 속성을 저장한다. |
| Schema / API schema | `Cube` 같은 종류와 Rigid Body/Collision 같은 추가 기능을 표현한다. 화면에 보이는 모양만으로 물리 기능을 알 수 없다. |
| `World` | 미터 단위, 물리 시간 간격, 객체 등록, 초기화, 스텝 실행을 관리한다. `scene.add`는 초기화할 객체를 등록한다. |
| `VisualCuboid` / `DynamicCuboid` | 각각 시각적 큐브와 강체·충돌 큐브를 만드는 편의 API다. 색은 이 구현에서 0~1 RGB 값이다. |
| `RigidPrim` / `GeometryPrim` | 이미 존재하는 Prim에 각각 강체와 충돌 기능을 추가하거나 접근한다. 질량과 충돌 표면은 서로 다른 개념이다. |
| `XFormPrim.set_world_poses` | 월드 위치와 **w,x,y,z 순서의 단위 quaternion**을 사용한다. quaternion 성분은 각도값이 아니다. Euler 라디안은 `euler_angles_to_quat`으로 변환한다. |
| `UsdGeom.Xformable` 연산 | `AddTranslateOp`, `AddRotateXYZOp`, `AddScaleOp`는 USD 변환 연산을 작성한다. `RotateXYZ`는 도 단위다. |
| `UsdLux.DistantLight` | 매우 먼 광원처럼 평행광을 만든다. 지면이나 물체가 빛을 반사해야 화면에서 밝기를 볼 수 있다. |

공식 페이지 일부 변환 예제의 `XformPrim` 표기와 회전 배열은 5.1 설치 소스의 API와 일치하지 않는 부분이 있다. 이 구현은 설치된 `XFormPrim`, `set_local_scales`, 단위 quaternion을 사용한다. 공식 예제의 순차적인 기능 추가는 독립 실행에서 동시 비교로 재구성했고, Script Editor 단계에서는 직접 속성을 추가하도록 유지했다.

## 한 가지 변수 실험과 문제 해결

`--height`만 1.5에서 2.0으로 바꾼다. 낙하 시간은 늘어나지만 충돌한 큐브의 최종 중심 높이는 같아야 한다. `RigidOnly`는 계속 떨어져 화면에서 사라지는 것이 의도된 결과다.

`ModuleNotFoundError: isaacsim/omni`이면 시스템 Python 대신 설치 폴더의 `python.sh`를 사용한다. 검은 화면에서는 Light와 카메라 방향을 확인하고 Stage 트리에서 큐브를 선택해 프레임을 맞춘다. GUI에서 움직이지 않으면 Play 상태와 Rigid Body/Collision 속성을 각각 확인한다. `--output` 오류는 새 폴더를 지정해 해결한다. 정적 컴파일과 옵션 도움말 검사는 GPU 실행을 검증하지 않는다.

## 출처

- NVIDIA, Isaac Sim **5.1.0**, [Isaac Sim Basic Usage Tutorial — Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html#tutorial): GUI, Extensions, Standalone Python의 지면/광원/큐브/물리/변환 절차.
- NVIDIA, Isaac Sim **5.1.0**, [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html): GUI 타임라인과 독립 Python 실행의 구분.
- 설치본의 `standalone_examples/tutorials/getting_started.py`와 `exts/isaacsim.core.prims/isaacsim/core/prims/impl/xform_prim.py`를 API 대조에 사용했다. 이 패키지의 코드는 해당 실습을 설명하기 위해 별도로 작성했다.
