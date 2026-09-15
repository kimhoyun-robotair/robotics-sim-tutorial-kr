# 08. Jupyter Notebook

권장 학습 순서 **08** · Python 실행 환경과 USD 기초 · 출처 ID `t089`

두 종류의 notebook 실행을 구별한다. `interactive.py`는 켜진 GUI에 Cube를 추가하고, `falling_cube.ipynb`는 notebook이 직접 앱을 시작하여 낙하 전후 위치를 측정한다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## A. 실행 중인 GUI에 연결

1. `Window > Extensions`에서 `isaacsim.code_editor.jupyter`를 켠다. 첫 활성화 때 Jupyter 의존성을 설치하므로 인터넷이 필요하고 잠시 UI가 멈출 수 있다.
2. `Window > Jupyter Notebook`을 선택하고 브라우저에서 **Omniverse (Python 3)** kernel로 notebook을 만든다.
3. `interactive.py` 전체를 한 셀에 붙여넣고 Run한다. GUI에서 `/World/EditorCube`를 선택해 `F`를 누른다.
4. 새 셀에서 `print(cube.GetSizeAttr().Get())`를 실행한다. `Tab`은 자동완성, `Ctrl+I`는 docstring 표시다. notebook은 Save As로 이 폴더 `output/interactive.ipynb`에 저장한다. 기본 저장 위치는 설치 extension 내부이므로 직접 선택한다.

이 kernel에서는 Kit가 update loop를 소유한다. `while True`/blocking sleep이나 `SimulationApp` 생성 코드를 실행하지 않는다. 이 방식에는 IPython magic과 Matplotlib가 지원되지 않으며 callback 내부 print는 notebook 대신 Isaac Sim 터미널에 나온다.

## B. notebook에서 standalone 실행 (Linux)

GUI와 연결 notebook을 종료한 뒤 다음으로 제공 notebook을 연다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/jupyter_notebook.sh" /absolute/path/to/this-package/falling_cube.ipynb
```

1. kernel을 **Isaac Sim Python 3**으로 선택한다. kernelspec 이름은 설치에 따라 UI에서 다시 선택할 수 있다.
2. Run All을 누른다. `SimulationApp`이 먼저 만들어진 다음 simulator imports가 수행된다.
3. 실제 Cube의 before/after 좌표를 확인한다. 120번 physics step 후 z가 감소해야 한다. `finally`가 앱을 닫는다. 다시 실행하려면 kernel을 재시작한다.

`World`는 physics/scene lifecycle, `DynamicCuboid`는 강체+충돌 Cube다. `world.reset()`은 runtime handle을 초기화하고 `world.step(render=False)`는 렌더 없이 물리를 진행한다. 내부 launcher가 `ISAAC_JUPYTER_KERNEL=1`과 `nest_asyncio`를 설정하여 notebook과 Kit의 asyncio 사용을 조정한다.

한 변수 실험: 시작 높이만 2→3 m로 바꾸고 같은 120 step의 최종 위치를 비교한다. ImportError는 kernel이 일반 Python인지 확인한다. 성공 기준은 GUI의 실제 prim 또는 standalone 낙하 좌표이며 kernel 연결 성공만으로 물리 실행을 판단하지 않는다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/jupyter_notebook.html).
