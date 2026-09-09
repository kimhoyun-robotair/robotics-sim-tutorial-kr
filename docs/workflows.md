# GUI·Extension·Standalone Python 참고서

처음 학습한다면 [11단계](lessons/11-workflows.md)부터 [18단계](lessons/18-omnigraph.md)까지 순서대로 진행한다. 이 문서는 작업 방식과 구현 선택을 빠르게 다시 찾기 위한 참고서이다.

## 세 방식이 함께 쓰이는 이유

Isaac Sim은 Kit 기반 앱이며, 여러 Extension이 창·물리·렌더링·센서 기능을 제공한다. 사용자는 GUI로 그 기능을 조작하거나 Python API를 직접 호출한다. Standalone Python도 앱을 시작한 뒤 같은 Extension과 USD를 사용한다. 즉 “GUI용 Isaac Sim”, “Extension용 Isaac Sim”, “Python용 Isaac Sim”이라는 서로 다른 시뮬레이터가 있는 것은 아니다. [공식 6.0.1 Workflows](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/workflows.html)

| 질문 | GUI / Script Editor | Extension | Standalone Python |
|---|---|---|---|
| 언제 선택하는가 | 처음 보는 장면을 확인하거나 짧게 실험할 때 | 같은 조작을 버튼·패널로 반복할 때 | 실험을 여러 번 실행하고 결과를 비교할 때 |
| 누가 앱을 시작하는가 | 사용자가 `isaac-sim.sh` 실행 | 실행 중인 Kit가 기능을 로드 | Python 파일의 `SimulationApp` |
| 누가 다음 화면을 처리하는가 | Kit | Kit | `app.update()` 등 작성한 루프 |
| 물리 상태는 언제 읽는가 | Play 이후 적절한 이벤트 시점 | 물리 이벤트 콜백 | 물리 이벤트 또는 수동 stepping 이후 |
| 오래 걸리는 작업은 어떻게 처리하는가 | 짧은 코드와 비동기 작업 | 비동기 작업·진행 UI·취소 | 반복문·실행 제한·오류 종료 |
| 코드를 어디에 보관하는가 | 스크립트 파일 | manifest와 모듈 | 스크립트와 설정 |
| 결과 장면은 어떻게 공유하는가 | USD로 저장 | 생성된 USD와 Extension을 각각 제공 | USD·JSON·이미지 등 필요한 결과 저장 |

## 같은 기능을 옮기는 구체적인 순서

예를 들어 로봇 주변에 장애물을 배치하는 기능은 아래 순서로 발전시킨다.

1. GUI로 큐브 하나의 크기와 위치를 확인한다.
2. Script Editor에서 `UsdGeom.Cube.Define()`과 변환값으로 같은 장면을 재현한다.
3. 장면 작성 부분을 `create_scene()` 함수로 옮긴다.
4. Extension 버튼이 그 함수를 호출하게 한다. UI는 입력과 오류 문구만 담당한다.
5. 반복 실험에서는 앱 초기화 후 같은 로직을 호출하고, 결과를 JSON으로 기록한다.

이 저장소의 두 장면 예제는 초보자가 파일 하나씩 읽을 수 있도록 자체적으로 작성되어 있다. 실제 프로젝트에서 둘을 함께 유지한다면 장면 로직을 별도 모듈로 묶는 편이 변경 누락을 줄인다.

## 코드가 실행되는 위치에 따라 달라지는 부분

**Script Editor 또는 Extension 내부:** 앱이 이미 있으므로 현재 context에 접근한다.

```python
import omni.usd
stage = omni.usd.get_context().get_stage()
```

**Standalone:** 앱을 먼저 만들고 Kit 의존 모듈을 import한다.

```python
from isaacsim import SimulationApp
app = SimulationApp({"headless": True})
try:
    import omni.usd
    stage = omni.usd.get_context().get_stage()
    app.update()
finally:
    app.close()
```

**저장한 결과만 분석하는 시스템 Python:** Isaac Sim 모듈 없이 JSON을 읽는다.

```python
import json
from pathlib import Path
result = json.loads(Path("artifacts/drop_cube.json").read_text())
print(result["passed"])
```

Standalone의 headless 실행은 GUI 창을 숨긴다. 카메라 영상을 계산하려면 렌더러, Render Product, 센서 갱신이 여전히 필요하다. UI가 없는 환경에서 `get_active_viewport()`가 항상 객체를 반환한다고 가정하지 않는다.

## 6.0.1 API를 사용할 때 확인할 사항

| 항목 | 이 튜토리얼의 사용 방식 |
|---|---|
| 앱 실행 | `from isaacsim import SimulationApp` |
| 강체 상태 | `isaacsim.core.experimental.prims.RigidPrim` |
| 반환값 | Warp 배열을 `.numpy()`로 변환하고 한 개의 물체도 `[0]` 선택 |
| 물리 이벤트 | `SimulationEvent.PHYSICS_POST_STEP` |
| PhysX 주기 | `PhysxScene.set_steps_per_second()` |
| 중복 실행 | 전용 Prim 경로와 소유 표식 확인 후 생성·초기화 |
| 종료 | 자신이 등록한 콜백, 작업, UI만 정리 |

Core Experimental API는 기존 Core API의 개편으로, 6.0.1 공식 튜토리얼에서 사용한다. 패키지 이름의 `experimental`을 지우거나 오래된 API와 반환값을 혼용하지 않는다. [공식 Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/core_api_overview.html), [공식 RigidPrim API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.core.experimental.prims/docs/index.html)

## 검증은 실행 방식과 별개의 작업이다

GUI에서 정상처럼 보여도 실제 샘플이 갱신되지 않을 수 있다. 반대로 물리 좌표가 정상이어도 카메라가 물체 내부에 있거나 조명이 없어 검은 영상이 나올 수 있다. 따라서 장면 구조, 물리 상태, 렌더 결과를 각각 확인한다. 낙하 프로젝트는 물리 수치와 정착 상태를 검사하며, 영상 픽셀과 센서 발행 검사는 후속 프로젝트에서 수행한다.

이 저장소를 작성한 환경에는 Isaac Sim 6.0.1과 실제 RTX GPU 런타임이 없어 GPU 실행 완료를 주장하지 않는다. 제공된 코드의 정적 검사와 공식 API 대조가 실제 장비에서의 실행 결과를 대신하지는 않는다. 각 프로젝트의 완료 기준을 실행하고 결과 파일을 보관한다.

[학습 목차](../README.md)
