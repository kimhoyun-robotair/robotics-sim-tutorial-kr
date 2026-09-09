# 13단계. Python 파일에서 Isaac Sim을 시작하고 종료하기

**목표:** 독립 실행 프로그램의 초기화 순서와 종료 처리를 익힌다. 여기부터 터미널 명령과 Script Editor 코드를 분명히 구분한다.

## 터미널 준비

설치 단계에서 정한 경로를 사용한다. `TUTORIAL_ROOT`에는 이 저장소를 내려받은 실제 위치를 넣는다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
cd "$TUTORIAL_ROOT"
test -x "$ISAAC_SIM_PATH/python.sh"
```

마지막 명령은 성공하면 아무것도 출력하지 않는다. 실패하면 Isaac Sim 설치 경로와 압축 해제 상태를 확인한다. ROS 2 환경 변수를 필요로 하지 않는 첫 물리 실습은 별도 터미널에서 시작하면 문제를 찾기 쉽다.

## 앱을 먼저 만들고 모듈을 가져오다

Standalone에서는 아직 Kit가 실행되지 않았다. Kit가 제공하는 `omni.*`나 Isaac Sim의 기능 모듈은 앱 초기화 뒤에 import한다. 표준 라이브러리의 `argparse`, `json`, `pathlib`는 그 전에 import해도 된다. 6.0.1 공식 예제의 시작점은 `from isaacsim import SimulationApp`이다. [공식 Hello World의 Standalone 절](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/core_api_tutorials/tutorial_core_hello_world.html#converting-the-example-to-a-standalone-application)

아래는 **파일로 저장해 실행하는 완전한 최소 예제**이다. 터미널에서 그대로 실행하면 임시 학습 파일을 만든다.

```bash
mkdir -p artifacts
cat > artifacts/minimal_app.py <<'PY'
from isaacsim import SimulationApp

app = SimulationApp({"headless": False})
try:
    import omni.usd
    from pxr import Gf, UsdGeom, UsdLux

    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    cube = UsdGeom.Cube.Define(stage, "/World/Cube")
    cube.CreateSizeAttr(0.5)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.5))
    UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(700.0)
    while app.is_running():
        app.update()
finally:
    app.close()
PY
"$ISAAC_SIM_PATH/python.sh" artifacts/minimal_app.py
```

창을 닫으면 종료한다. 큐브가 시야 밖이면 Stage에서 `/World/Cube`를 선택하고 Viewport 위에서 `F`를 누른다. 이 예제 역시 시각용 큐브이므로 물리 낙하는 다음 프로젝트에서 추가한다.

## 각 줄이 담당하는 일

| 코드 | 의미 | 흔한 실수 |
|---|---|---|
| `SimulationApp(...)` | Kit 앱, Extension, 렌더링 환경을 준비 | 열린 GUI의 Script Editor 안에서 새 앱을 또 만듦 |
| `get_stage()` | 앱이 관리하는 현재 USD Stage를 가져옴 | 외부 Python이 같은 Stage를 자동 공유한다고 생각함 |
| `app.update()` | 앱의 다음 갱신을 처리 | 1회 호출을 물리 1스텝으로 계산 |
| `app.is_running()` | 창 종료 등 앱 상태를 확인 | 사용자가 닫아도 무한 반복 |
| `finally: app.close()` | 예외가 발생해도 종료 처리를 시도 | 결과 writer나 앱을 정리하지 않음 |

`headless=True`는 앱 창을 표시하지 않는 설정이다. 카메라·RTX 센서 작업에서 렌더링까지 끈다는 뜻도, 지원 GPU가 필요 없다는 뜻도 아니다. GPU 요구사항은 설치 단계와 센서 단계의 기준을 따른다.

## 전체 실습 파일로 이동하기

```bash
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py --help
"$ISAAC_SIM_PATH/python.sh" examples/01_drop_cube.py \
  --output artifacts/drop_gui.json
```

두 번째 명령은 시뮬레이션을 실행하고 결과를 저장한 뒤 창을 닫는다. 이 프로그램에는 `try/finally`, 종료 상태 검사, 시간 제한, 콜백 오류 전달이 들어 있다. 앱 초기화 이후 예외가 발생해도 `passed: false` 결과를 남기도록 설계했다. 프로세스 강제 종료나 GPU 드라이버 중단처럼 Python 종료 처리 자체가 실행되지 못하는 상황까지 결과 파일을 보장하지는 않는다.

6.0.1 `SimulationApp.close()`에는 `exit_code` 인자가 있다. 전체 예제는 실패 종료 코드가 앱의 빠른 종료 과정에서 성공으로 바뀌지 않도록 이 값을 전달한다. [공식 SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.simulation_app/docs/index.html)

**예상 결과:** `--help`는 옵션을 출력하고 끝난다. 실제 실행은 파란 큐브와 바닥을 표시하고, 성공 여부와 JSON 경로를 출력한다. 작성 환경에서는 Isaac Sim/GPU 실행을 하지 않았으므로 사용자의 실제 결과로 판단한다.

**완료 기준:** 최소 예제와 낙하 예제를 터미널에서 실행하는 방법을 구분하고, import 순서와 `finally`가 필요한 이유를 설명한다.

**과제:** 최소 예제의 색상을 변경한다. 그다음 `headless=True`와 유한한 반복문을 함께 적용하여 창 없이 자동 종료되는지 확인한다. 무한 루프를 둔 채 창만 숨기지 않는다.

[이전](12-script-editor.md) · [다음: 시간과 반복 실험](14-timing.md) · [학습 목차](../../README.md)
