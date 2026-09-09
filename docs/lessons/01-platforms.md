# 01. Isaac Sim으로 무엇을 만들 수 있는가

## 목표와 준비

Isaac Sim을 처음 접한다면 프로그램 이름부터 정리한다. 이 단계의 목표는 가상 실험실에서 로봇을 움직일 때 각 프로그램이 맡는 일을 설명하는 것이다. 설치 전에도 읽을 수 있으며, 마지막 코드 확인은 03단계의 설치를 마친 뒤 진행한다.

앞으로 만드는 장면은 바닥, 벽, 상자, 로봇, 센서를 포함한다. 먼저 상자가 바닥 위에 안정적으로 놓이는 작은 장면을 만들고, 이후 로봇과 센서를 하나씩 추가한다. 처음부터 복잡한 창고를 불러오면 화면이 어두운 이유가 조명인지, 자산 다운로드인지, GPU 메모리 부족인지 구분하기 어렵다.

## 플랫폼을 역할로 구분하다

| 이름 | 담당하는 일 | 이 튜토리얼에서 만나는 예 |
| --- | --- | --- |
| OpenUSD | 장면의 객체, 계층, 재질, 참조 관계 등을 표현하는 기술 | 실험실을 `lab.usda`에 저장하다 |
| NVIDIA Omniverse | OpenUSD 기반 3D 애플리케이션을 만드는 기술과 구성 요소 | 여러 도구가 같은 장면 구조를 다루다 |
| Omniverse Kit | Extension을 조합해 애플리케이션을 실행하는 기반 | 메뉴, 창, 렌더러, Python 기능을 로드하다 |
| Isaac Sim | 로봇·센서·물리를 포함한 시뮬레이션 애플리케이션 | 상자 낙하, 로봇 주행, 카메라 데이터 생성 |
| Isaac Lab | Isaac Sim 위에서 로봇 학습 실험을 구성하는 프레임워크 | 여러 환경을 병렬로 실행해 정책을 학습하다 |
| ROS 2 Jazzy | 로봇 프로그램끼리 메시지와 서비스를 주고받는 소프트웨어 기반 | 속도 명령을 보내고 센서 데이터를 받다 |
| Isaac ROS | NVIDIA 가속 기능을 활용하는 ROS 패키지 모음 | 인식·추정 파이프라인을 구성하다 |

OpenUSD 파일을 저장한다고 ROS 노드까지 저장되는 것은 아니다. 마찬가지로 ROS 2를 설치했다고 Isaac Sim의 가상 카메라가 자동으로 생기지 않는다. 장면은 Isaac Sim에서 만들고, 외부 ROS 프로그램과 연결할 때 ROS 2 Bridge를 추가한다. 플랫폼 관계는 [공식 소개](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/index.html)에서 확인할 수 있다.

## GUI, Extension, Python을 구분하다

세 가지는 서로 다른 시뮬레이터가 아니다. 같은 Isaac Sim과 USD 장면을 다루는 작업 방식이다. Extension도 주로 Python으로 작성하므로, “Extension 또는 Python”이라는 표현만으로는 실행 방식을 정확히 구분하기 어렵다.

| 방식 | 시작 지점 | 실행 흐름을 관리하는 쪽 | 적합한 작업 |
| --- | --- | --- | --- |
| GUI | `isaac-sim.sh` 실행 후 메뉴 클릭 | 실행 중인 Kit 앱 | 장면 배치, 속성 확인, 센서 방향 확인 |
| Extension 안의 Python | 실행 중인 앱의 Script Editor 또는 사용자 Extension | Kit 이벤트 루프와 등록한 콜백 | 반복되는 편집 작업, 전용 버튼과 창 만들기 |
| Standalone Python | `python.sh my_script.py` | 사용자가 작성한 프로그램 | 반복 실험, 자동 검증, 데이터 생성 |

예를 들어 바닥과 상자를 한 번 배치할 때는 GUI로 크기를 직접 확인하기 좋다. 같은 규격의 상자 20개를 배치하려면 짧은 Python 반복문이 편하다. 배치 버튼을 동료에게 제공하려면 Extension으로 묶고, 배치를 100회 바꾸어 실험하려면 Standalone 스크립트를 작성한다. 기능을 나눈 이유는 이러한 사용 상황과 프로그램의 실행 주기가 다르기 때문이다. [공식 작업 방식 설명](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/workflows.html)

## 실제로 같은 장면을 조회하다

설치 후 Isaac Sim에서 `File > New`를 선택한다. `Create > Shape > Cube`로 상자를 추가한다. 메뉴에 `Shapes`로 표시되는 경우 그 안의 `Cube`를 선택한다. 오른쪽 Stage에서 만들어진 객체를 선택해 경로를 확인한다. 여기서는 `/World/Cube`라고 가정한다.

`Window > Script Editor`를 열고 다음 코드를 붙여 넣은 뒤 `Run`을 누른다. 이 코드는 **Isaac Sim 안에서** 실행한다. Ubuntu 터미널의 일반 `python3`에 붙여 넣지 않는다.

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
assert stage is not None, "File > New로 장면을 먼저 만든다."
prim = stage.GetPrimAtPath("/World/Cube")
assert prim.IsValid(), "Stage에 표시된 Cube 경로를 확인한다."
print("객체 경로:", prim.GetPath())
print("객체 종류:", prim.GetTypeName())
print("작성 중인 파일:", stage.GetRootLayer().identifier)
```

`prim`은 장면 안의 한 객체를 가리킨다. `stage`는 여러 파일과 참조를 합성해서 보는 전체 장면이다. GUI로 만든 상자를 Python에서 찾았으므로, 두 방식이 같은 데이터를 다룬다는 것을 확인한 셈이다. 이때 Script Editor 안에서 `SimulationApp()`을 새로 생성하지 않는다. 앱은 이미 실행 중이다.

Standalone은 앱을 먼저 시작한다. 다음은 구조를 읽기 위한 작은 예이다. 03단계 이후 원하는 파일에 저장해 `"$ISAAC_SIM_PATH/python.sh" 파일경로.py`로 실행할 수 있다.

```python
from isaacsim import SimulationApp

app = SimulationApp({"headless": False})
try:
    import omni.usd
    from pxr import UsdGeom

    omni.usd.get_context().new_stage()
    stage = omni.usd.get_context().get_stage()
    UsdGeom.Cube.Define(stage, "/World/ExampleCube").CreateSizeAttr(0.4)
    print("Standalone에서 만든 객체:", stage.GetPrimAtPath("/World/ExampleCube"))
    while app.is_running():
        app.update()
finally:
    app.close()
```

이 예는 객체 생성과 앱 수명만 보여 준다. 조명·카메라 배치·물리를 설정하지 않으므로 화면만으로 설치나 렌더링의 성공 여부를 판단하지 않는다. 앱 창을 닫으면 반복문이 끝나고 자원을 정리한다.

## 예상 결과와 실패 시 확인

GUI에서 만든 상자의 경로와 종류가 Script Editor 출력에 표시되어야 한다. `ModuleNotFoundError: omni`가 발생하면 실행 위치가 잘못되었는지 확인한다. 일반 Python은 Isaac Sim Extension 검색 경로를 자동으로 구성하지 않는다. 객체를 못 찾으면 `/World/Cube`를 임의로 반복해서 만들기 전에 Stage에 실제로 표시된 경로를 읽는다.

## 작은 과제

“상자 위치를 직접 조정한다”, “매번 같은 장면을 생성한다”, “연구실 전용 로봇 배치 버튼을 만든다”에 각각 적합한 작업 방식을 적는다. 한 과제에 두 방식을 함께 써도 좋지만, 어느 부분에서 전환하는지 설명한다.

## 공식 6.0.1 자료

- [What Is Isaac Sim?](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/index.html)
- [Workflows](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/workflows.html)
- [Python Scripting and Tutorials](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/python_scripting/index.html)

다음: [02. 설치 전 점검](02-preflight.md)
