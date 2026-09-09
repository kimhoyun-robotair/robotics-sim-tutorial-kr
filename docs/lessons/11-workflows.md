# 11단계. GUI, Extension, Python의 관계를 이해하기

**목표:** 같은 큐브를 세 가지 방식으로 만들 수 있는 이유와, 지금 작업에 맞는 방식을 설명한다. 앞 단계에서 Stage, Prim, 좌표계, 저장을 익힌 상태로 진행한다.

## 이름부터 구분하기

GUI는 마우스와 패널로 작업하는 **사용 방법**이다. Extension은 Kit에 기능을 추가하는 **배포와 실행 단위**이다. Python은 그 기능이나 자동화 코드를 작성하는 **언어**이다. 따라서 Extension과 Python은 서로 반대되는 선택지가 아니다. Python으로 Extension을 만들 수도 있고, 열린 앱 안의 Script Editor에서 Python을 실행할 수도 있다. Standalone Python은 Python 파일이 Isaac Sim 앱을 시작하고 종료까지 관리하는 작업 방식이다.

NVIDIA는 GUI, Extension, Standalone Python을 세 가지 주요 workflow로 설명한다. 같은 Stage를 공유하더라도 입력을 받는 방식과 앱 실행을 관리하는 주체가 다르다. [공식 6.0.1 Workflows](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/workflows.html)

| 구분 | 실행을 시작하는 곳 | 앱과 반복 실행을 관리하는 주체 | 잘 맞는 작업 | 저장해야 할 것 |
|---|---|---|---|---|
| GUI | `isaac-sim.sh`, 메뉴와 버튼 | Kit 앱 | 모양·좌표·충돌체를 눈으로 확인 | USD와 필요한 asset |
| Script Editor | 실행 중인 앱의 Run 버튼 | Kit 앱 | 짧은 실험, 속성 확인, GUI 작업 자동화 | `.py`와 결과 USD |
| Extension | Extension Manager의 활성화 버튼 | Kit 앱이 시작·종료 함수를 호출 | 재사용 패널, 이벤트에 반응하는 도구 | manifest와 Python 패키지 |
| Standalone Python | `python.sh 파일.py` | 작성한 Python 코드 | 일정한 조건의 반복 실험, 결과 수집 | `.py`, 설정, JSON·이미지 등 결과 |

## 왜 나누어 두었는가

로봇의 충돌체가 바퀴를 가리는지 확인할 때는 Viewport가 편하다. 같은 로봇 100개를 배치하려면 코드가 편하다. 배치 개수를 동료가 버튼으로 바꾸게 하려면 Extension이 편하다. 세 방식이 같은 USD와 API를 사용하므로 장면을 처음부터 다시 구현하지 않고 작업 방식을 바꿀 수 있다.

Extension은 필요한 의존성만 선언해 활성화할 수 있게 한다. 예를 들어 장면 생성 로직과 UI를 분리하면, GUI 도구와 서버 작업에서 같은 로직을 사용할 수 있다. 다만 UI를 직접 호출하는 코드를 그대로 headless 환경에 복사하면 창이나 Viewport가 없어서 실패할 수 있다. 장면 생성, UI 표시, 결과 저장을 함수로 분리하는 이유가 여기에 있다.

## 같은 큐브를 두 방식으로 만들다

1. 새 Stage를 만들고 Stop 상태인지 확인한다.
2. GUI에서 `Create > Shape > Cube`로 큐브를 추가한다.
3. Stage에서 큐브를 선택하고 Property에서 크기와 이동값을 확인한다.
4. 큐브 이름과 Prim 경로를 기록한다. 파일 경로와 Prim 경로는 다른 값이다.
5. Script Editor에서 아래 코드를 실행한다. 기존 큐브와 다른 경로를 사용한다.

```python
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, "/World/CompareCube")
cube.CreateSizeAttr(0.4)
UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(1.0, 0.0, 0.5))
print(cube.GetPrim().GetPath())
```

6. `/World/CompareCube`를 Stage에서 선택한다. Property의 Size와 Translate 값이 코드와 일치하는지 확인한다.

`Define`은 같은 경로의 Prim을 다시 가져올 수도 있다. 따라서 이 예제를 두 번 실행해도 큐브가 두 개 생기지 않는다. 하지만 `AddTranslateOp()`처럼 변환 연산을 추가하는 코드는 기존 연산과 충돌할 수 있으므로, 이미 있는 Prim을 수정할 때는 위와 같이 `XformCommonAPI.SetTranslate()`를 사용하거나 먼저 구조를 확인한다.

## API도 층이 있다

| 계층 | 예시 | 역할 |
|---|---|---|
| OpenUSD | `UsdGeom.Cube`, `UsdPhysics.MassAPI` | 장면 구조와 속성을 구체적으로 작성 |
| Kit | `omni.usd`, `omni.ui`, `omni.timeline` | 현재 Stage, 창, 앱 이벤트를 다룸 |
| Isaac Sim Core | `RigidPrim`, `SimulationManager` | 로봇·강체 상태와 시뮬레이션 흐름을 다룸 |
| 기능별 Extension | ROS 2, 카메라, RTX 센서 | 필요한 센서와 통신 기능을 제공 |

6.0.1의 공식 Hello World는 `isaacsim.core.experimental` 아래의 Prim wrapper를 사용한다. `experimental`은 실제 패키지 이름이며, 바뀔 수 있는 API라는 점을 버전 고정으로 관리한다. 오래된 `World` 중심 예제를 이름만 바꿔 붙여 넣지 말고 초기화·반환값·이벤트를 함께 확인한다. [공식 Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/core_api_overview.html)

## 예상 결과와 진단

- Stage에 GUI 큐브와 `/World/CompareCube`가 함께 보인다. 코드가 만든 큐브도 GUI로 선택하고 수정할 수 있다.
- `No module named omni`가 나오면 시스템 터미널에서 실행한 것은 아닌지 확인한다. 위 코드는 Isaac Sim 내부 Script Editor용이다.
- 큐브가 안 보이면 Stage에서 해당 Prim을 선택하고 Viewport 위에서 `F`를 누른다. 숨김, 잘못된 크기, 조명 순서로 확인한다.

**완료 기준:** “Extension도 Python으로 작성할 수 있으며, standalone에서는 앱 수명주기를 직접 관리한다”를 설명하고 같은 Prim을 GUI와 코드 양쪽에서 확인한다.

**과제:** 장면 배치, 로봇 충돌 검사, 100회 성능 측정, 센서 설정 패널에 어떤 방식을 쓸지 한 줄씩 정리한다. 더 자세한 비교는 [작업 방식 참고서](../workflows.md)를 읽는다.

[다음: Script Editor](12-script-editor.md) · [학습 목차](../../README.md)
