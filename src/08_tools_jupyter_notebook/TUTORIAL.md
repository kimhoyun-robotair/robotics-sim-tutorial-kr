# 08. Jupyter 커널에 따라 달라지는 시뮬레이션 실행

## 이번에 배우는 것

**Jupyter에서 실행 중인 앱에 연결하는 방식과 노트북이 앱을 직접 시작하는 방식을 구분합니다.**

노트북의 셀은 코드를 적고 실행하는 공간입니다. 실제로 그 코드를 수행하는 Python 환경은 **커널**이 정합니다. Isaac Sim 5.1에는 서로 목적이 다른 두 커널이 있으므로, 코드와 커널을 맞춰 선택해야 합니다.

| 구분 | 실행 중인 GUI에 연결 | 노트북에서 독립 실행 |
|---|---|---|
| 커널 표시 이름 | Omniverse (Python 3) | Isaac Sim Python 3 |
| 실습 파일 | `interactive.py`를 셀에 붙여 넣습니다. | `falling_cube.ipynb`를 엽니다. |
| 앱 시작 | 이미 실행 중인 앱을 사용합니다. | 셀이 `SimulationApp`을 만듭니다. |
| 큐브 | Size 0.5인 Visual 도형입니다. | 한 변 0.2 m인 물리 큐브입니다. |
| 관찰 | GUI의 Prim과 셀 출력입니다. | 낙하 전후 위치입니다. |
| 완료 후 | 앱과 커널을 계속 사용합니다. | 앱을 닫으므로 재실행 전 커널을 재시작합니다. |

05번에서 살펴본 앱 수명과 물리 진행의 차이가 노트북에서도 그대로 나타납니다. 이번 두 예제는 큐브의 크기와 물리 속성도 다릅니다.

## 1. 실행 중인 GUI에 노트북 연결하기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU를 준비합니다. Linux의 앱 시작 명령은 다음과 같습니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 빈 Stage를 엽니다.
2. **Window > Extensions**에서 `isaacsim.code_editor.jupyter`를 활성화합니다. 처음에는 Jupyter 의존성 설치 때문에 시간이 걸릴 수 있습니다. 필요한 패키지를 내려받을 수 있는 네트워크 또는 미리 준비한 패키지 환경을 확인하고 완료를 기다리세요.
3. **Window > Jupyter Notebook**으로 브라우저의 Jupyter를 엽니다.
4. **Omniverse (Python 3)** 커널을 선택해 새 노트북을 만듭니다.
5. `src/08_tools_jupyter_notebook/interactive.py` 전체를 한 셀에 붙여 넣고 Run합니다.

이 연결 절차와 커널 구분은 [공식 Jupyter 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/jupyter_notebook.html#interactive-scripting)를 따릅니다.

### 코드에서 볼 부분

```python
stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.5)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
```

`path`는 `/World/EditorCube`입니다. 활성 Stage에 큐브를 만들며 앱 생성이나 `world.step()` 호출은 없습니다. 앞부분에서 같은 Prim이 이미 있는지 검사하므로 같은 셀 전체를 반복 실행하면 중복 생성 오류가 납니다.

새 셀에서 다음 코드를 실행해 보세요.

```python
print(cube.GetPath())
print(cube.GetSizeAttr().Get())
```

첫 셀에서 만든 변수를 다음 셀에서 계속 쓸 수 있습니다. 셀의 위치보다 실제 실행 순서가 중요합니다. 두 번째 셀부터 실행하면 `cube`가 아직 없습니다.

### 실행 결과 확인하기

첫 셀은 `created /World/EditorCube size 0.5`를, 다음 셀은 경로와 `0.5`를 출력해야 합니다. GUI에서 같은 Prim을 선택하고 `F`로 화면을 맞춰 보세요. Property의 Size와 중심 Z는 각각 0.5입니다. 이 파일은 Stage 단위를 별도로 지정하지 않으므로 실제 길이를 해석할 때 현재 Stage 단위를 함께 확인합니다.

Play를 눌러도 큐브는 떨어지지 않습니다. `UsdGeom.Cube`로 외형만 작성했기 때문입니다. 코드·출력을 남기려면 노트북을 저장하고, 장면을 남기려면 Isaac Sim에서 USD를 별도로 저장하세요. 기본 노트북 저장 위치가 설치 확장 폴더일 수 있으므로 본인의 작업 위치를 확인합니다.

이 커널에서는 앱이 업데이트를 맡습니다. 끝나지 않는 반복문이나 긴 동기 대기를 넣으면 GUI도 멈출 수 있습니다. 공식 5.1 연결 커널은 IPython magic·Matplotlib를 지원하지 않으며, 콜백 안의 출력은 노트북 대신 Isaac Sim 터미널로 전달됩니다.

## 2. 노트북에서 앱을 직접 시작하기

이번에는 GUI 연결 실습을 마치고 앱과 연결 노트북을 종료합니다. 독립 노트북 방식은 Isaac Sim 5.1에서 Linux용으로 제공됩니다.

저장소 루트에서 다음 명령을 실행하세요.

```bash
~/isaacsim/jupyter_notebook.sh "$PWD/src/08_tools_jupyter_notebook/falling_cube.ipynb"
```

1. 노트북에서 커널을 **Isaac Sim Python 3**으로 선택합니다. 파일에 기록된 커널 이름이 설치와 다르면 UI에서 다시 선택하세요. 설치 launcher는 `isaac_sim_python3`이라는 이름으로 커널을 등록합니다.
2. **Run All**로 제공 셀을 실행합니다.
3. `before`, `after` 출력과 셀의 완료 여부를 확인합니다.

설치 launcher는 번들 Python에 Jupyter를 설치·갱신한 뒤 그 Python에 연결된 커널을 등록합니다. 준비 단계에서 패키지 다운로드가 필요할 수 있습니다. `ISAAC_JUPYTER_KERNEL` 설정과 `nest_asyncio` 처리는 노트북과 Kit가 사용하는 비동기 실행을 조정합니다. 자세한 구성은 [공식 독립 노트북 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/jupyter_notebook.html#running-standalone-isaac-sim-from-jupyter-notebook)을 참고하세요.

### 코드에서 볼 부분

```python
from isaacsim import SimulationApp
app = SimulationApp({"headless": True})
```

앱 생성 다음에 World와 큐브 API를 가져옵니다. 지면과 한 변 0.2 m인 `DynamicCuboid`를 만든 뒤 `world.reset()`으로 초기화합니다. 이번 큐브는 강체와 충돌을 갖고 있으며 중심 높이는 2 m입니다.

```python
before = cube.get_world_pose()[0].copy()
for _ in range(120):
    world.step(render=False)
after = cube.get_world_pose()[0].copy()
print({"before": before.tolist(), "after": after.tolist()})
assert after[2] < before[2], "Cube did not fall"
```

셀의 반복문이 직접 120번 물리를 진행합니다. `copy()`는 읽은 위치를 그 시점의 별도 배열로 남깁니다. `before[2]`와 `after[2]`는 각각 낙하 전후 z 좌표입니다.

### 실행 결과 확인하기

Headless로 시작하므로 새 창이 나타나지 않는 것이 정상입니다. `before`는 `[0.0, 0.0, 2.0]`, `after`의 z는 더 낮아야 합니다. 충분히 정착하면 큐브 중심은 한 변의 절반인 약 0.1 m입니다.

**자동 검사는 높이가 줄었는지만 확인합니다.** Assertion이 통과했다고 바닥 위 0.1 m에 정착했다는 것까지 검증한 것은 아닙니다. `after`의 실제 값을 함께 읽으세요. 이 노트북은 CSV나 JSON 파일을 별도로 만들지 않습니다.

마지막 `finally`에서 `app.close()`를 호출합니다. 완료한 셀을 다시 실행하려면 커널을 재시작한 뒤 Run All을 사용하세요. 앱 수명을 셀이 직접 관리하기 때문입니다.

## 3. 커널과 앱 수명의 관계 정리

```text
Omniverse 커널: 셀 → 실행 중인 앱의 Stage 편집 → 다음 셀에서 변수 재사용
Isaac Sim 커널: 셀 → 앱 시작 → reset → step 120번 → 위치 출력 → 앱 종료
```

노트북을 저장하면 코드와 저장 시점의 출력이 남습니다. 그것이 현재 앱이 실행 중이라는 뜻은 아닙니다. 커널 상태, 앱 상태, 저장된 출력의 시점을 나누어 생각하면 재실행 오류를 이해하기 쉽습니다.

## 4. 간단한 확인 실험

독립 노트북에서 **`range(120)`만 `range(10)`으로** 바꾸고 커널을 재시작해 실행하세요. 초기 높이와 큐브 크기는 유지합니다.

짧은 진행에서는 `after`의 z가 2 m보다 낮아도 아직 바닥의 0.1 m에는 도달하지 않았을 것으로 예상할 수 있습니다. Assertion 통과와 바닥 정착의 차이가 잘 드러납니다. 실험 후 120으로 복원하고 다시 비교하세요.

## 실행할 때 막히면

- **`No module named isaacsim`**: 독립 노트북의 커널이 일반 Python인지 확인하고 Isaac Sim Python 3을 선택하세요.
- **커널을 찾을 수 없다는 메시지**: 설치의 `jupyter_notebook.sh`로 열고 커널을 다시 선택하세요. 파일의 저장 이름과 실제 등록 이름이 다를 수 있습니다.
- **연결 셀에 `already exists` 오류**: GUI의 File > New 후 생성 셀부터 다시 실행하세요.
- **연결 GUI가 멈춤**: 완료되지 않는 반복문을 셀에 넣었는지 확인하세요. 연결 커널은 앱의 업데이트 시간을 함께 사용합니다.
- **독립 셀을 두 번째 실행할 때 실패함**: 이전 셀이 앱을 닫았습니다. 커널을 재시작한 뒤 처음부터 실행하세요.
- **셀 출력에서 위치가 안 보임**: 실행 중인 커널과 셀 완료 상태를 확인합니다. 연결 성공만으로 낙하 실습이 실행된 것은 아닙니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Jupyter Notebook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/jupyter_notebook.html)에 대응합니다. 연결 방식은 시각적 큐브 작성으로, 독립 방식은 물리 큐브의 전후 위치로 확인합니다.

커널 종류에 따라 실행 위치와 결과가 다르므로 두 실습의 확인 기준도 나눴습니다. `tutorial.json`의 실행 검증 상태는 `not_run`이며, 위 출력과 낙하 높이는 직접 확인할 기대 기준입니다.
