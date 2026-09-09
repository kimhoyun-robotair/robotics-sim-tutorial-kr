# 설치 가능한 Extension과 OmniGraph 만들기

이 장에서는 앞 장의 낙하 실험을 버튼으로 생성하는 Extension을 설치하고, 물리 시간에 맞춰 콜백을 호출한다. 이어서 OmniGraph를 만들고, Python이 그래프를 작성하는 시점과 그래프가 평가되는 시점을 구분한다.

## 1. Extension의 실제 파일 구조

예제는 [examples/extensions/course.falling_cube](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/extensions/course.falling_cube/config/extension.toml)에 들어 있다. 저장소의 해당 폴더를 그대로 등록한다.

| 저장소 기준 경로 | 내용 |
| --- | --- |
| `examples/extensions/course.falling_cube/config/extension.toml` | 의존성과 Python 모듈 선언 |
| `examples/extensions/course.falling_cube/course/falling_cube/__init__.py` | Extension 클래스 내보내기 |
| `examples/extensions/course.falling_cube/course/falling_cube/scene.py` | 큐브·바닥·중력·조명 작성 |
| `examples/extensions/course.falling_cube/course/falling_cube/extension.py` | 창 생성, 작업 예약, 구독 해제 |

설정 파일의 이름은 **`extension.toml`**이다. `config.toml`로 저장하면 이 구조의 Extension을 찾지 못한다.

```toml
[package]
version = "0.1.0"
title = "Course Falling Cube"
description = "Isaac Sim 5.1: 빈 장면 생성과 Extension 수명 주기 실습"
category = "Simulation"

[dependencies]
"omni.kit.uiapp" = {}
"omni.usd" = {}
"omni.timeline" = {}
"omni.physx" = {}

[[python.module]]
name = "course.falling_cube"
```

의존성에는 실제 사용하는 기능을 선언한다. Python 모듈 이름은 `course/falling_cube` 경로와 대응하며, `__init__.py`에서 클래스를 가져오므로 Kit가 `omni.ext.IExt` 구현을 찾을 수 있다.

## 2. GUI에서 설치하고 실행하기

1. 저장소 루트 터미널에서 `pwd`로 절대 경로를 확인한다. 예를 들어 `/home/user/robotics-sim-tutorial-kr`이다.
2. Isaac Sim의 **Window > Extensions**를 연다.
3. 창 오른쪽 위 설정 메뉴를 열고 **Extension Search Paths**의 `+`를 누른다.
4. `/home/user/robotics-sim-tutorial-kr/examples/extensions`를 추가한다. 등록하는 것은 `config` 폴더가 아니라 `course.falling_cube` 폴더를 담고 있는 **상위 폴더**이다.
5. `Course Falling Cube` 또는 `course.falling_cube`를 검색한다. 기본 목록에 없으면 THIRD PARTY 탭을 확인한다.
6. 활성화 스위치를 켠다. `Course Falling Cube` 창이 나타나야 한다.
7. 현재 작업을 저장하고 **File > New**를 선택한다. Stop 상태에서 **Build in empty stage**를 누른다.
8. `/World/WorkflowDemo/Cube`를 선택하고 `F`로 화면을 맞춘 뒤 Play를 누른다.
9. Console의 Info 필터를 켜거나 실행 터미널에서 `[course] accumulated physics time: ...`를 확인한다. 로그는 누적 물리 시간 약 1초마다 출력된다.
10. Stop을 누르고 Extension을 껐다 켠다. 창이 중복 생성되지 않는지 확인한다. 다시 장면을 생성하려면 File > New를 선택한다.

경로 등록 방법은 NVIDIA의 로컬 Extension 설치 안내를 따른다. [Adding and Updating Extensions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html)

터미널에서 시작할 때만 경로를 추가할 수도 있다. 다음 명령은 저장소 루트에서 **새 앱을 시작**한다.

```bash
"$ISAACSIM_PATH/isaac-sim.sh" \
  --ext-folder "$PWD/examples/extensions" \
  --enable course.falling_cube
```

## 3. 수명 주기를 코드로 읽기

`on_startup()`은 장면을 만들지 않고 창과 Stage 이벤트 구독을 준비한다. 버튼을 누르면 `_request_build()`가 비동기 작업을 한 번만 예약한다.

```python
def _request_build(self):
    if self._task is not None and not self._task.done():
        return
    self._task = asyncio.ensure_future(self._build_async())
```

`_build_async()`는 대기 전후로 같은 Stage인지, Stop 상태인지 다시 확인한다. `await`에서 기다리는 동안 사용자가 File > Open이나 Play를 누를 수 있기 때문이다. 검사를 통과하면 장면을 만들고 물리 이벤트를 구독한다.

```python
self._physics_sub = omni.physx.get_physx_interface().subscribe_physics_step_events(
    self._on_physics_step
)
```

전체 파일의 `_on_physics_step(self, dt)`는 Stage가 바뀌었는지, 큐브가 아직 존재하는지 확인한 뒤 `dt`를 누적한다. `dt`는 물리 step의 시간 간격이다. 여기서 파일 저장, 장시간 추론, 대규모 USD 편집을 매번 실행하지 않는다. 제어 명령과 짧은 상태 갱신만 수행하고 무거운 처리는 별도 주기나 작업으로 분리한다.

`on_shutdown()`에서는 다음 대상을 정리한다.

| 대상 | 정리 방법 | 남겨 두면 생기는 문제 |
| --- | --- | --- |
| 비동기 작업 | task 취소, 활성 상태 플래그 해제 | 종료된 창이나 새 Stage를 뒤늦게 변경 |
| 물리 구독 | 보관한 subscription 참조 해제 | 이전 코드가 계속 호출되거나 중복 호출 |
| Stage 이벤트 구독 | 보관한 subscription 참조 해제 | 다음 파일을 열 때 오래된 콜백 실행 |
| UI 창 | `destroy()` 후 참조 해제 | 창 중복과 이전 객체 잔류 |
| Stage 참조 | 자체 참조 해제 | 닫힌 문서에 계속 접근 |

Extension을 끄면 콜백과 창만 사라지고, 만들어진 큐브와 바닥은 남는다. **USD 장면과 Extension 실행 상태가 별개**라는 점을 확인할 수 있다. 예제는 사용자의 앱을 종료하거나 Stage 전체를 지우지 않는다.

코드를 수정하고 저장하면 hot reload가 일어날 수 있다. `on_startup()`을 “앱을 처음 켤 때 딱 한 번 호출하는 함수”로 생각하면 안 된다. 종료·재시작·장면 교체를 정상 동작 경로에 포함한다. [Workflows의 Hot Reloading](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)

## 4. `World`를 사용하는 Extension은 무엇이 달라지는가

이번 예제는 USD와 PhysX 이벤트만 사용하므로 전역 `World` 인스턴스를 만들거나 지울 필요가 없다. 로봇 제어, Core API Task, `World.scene`을 사용할 때는 NVIDIA의 `BaseSample` 또는 Extension Template을 따라 **World의 생성·초기화·정리 책임을 한 곳에 둔다**.

여러 Extension이 같은 앱에서 실행 중인데 무조건 `World.clear_instance()`를 호출하면 다른 기능의 상태까지 끊길 수 있다. 이미 존재하는 World를 가져왔다면 내가 소유한 것인지, 누가 reset하는지 먼저 정한다. 콜백도 고유한 이름을 지정하고 자신이 추가한 것만 제거한다.

```python
# 자신이 소유한 World가 초기화된 뒤 사용하는 패턴이다.
world.add_physics_callback("course_robot_controller", controller_callback)
# 해당 기능을 종료할 때 실행한다.
world.remove_physics_callback("course_robot_controller")
```

이 조각의 `world`와 `controller_callback`은 애플리케이션에서 준비하는 객체이다. 전체 실행 구조는 공식 [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)와 [Extension Template Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html)를 이어서 확인한다.

## 5. OmniGraph는 무엇을 담당하는가

OmniGraph는 노드의 데이터와 실행 관계를 Stage에 저장한다. 예를 들어 “시뮬레이션 진행 → 시각 읽기 → ROS 메시지 발행”을 선으로 연결한다. Extension은 그래프를 만드는 UI를 제공할 수도 있고, Python은 손으로 연결한 것과 같은 그래프를 작성할 수도 있다.

그래프를 **생성하는 Python 코드**는 한 번 실행된다. 그래프 노드가 **평가되는 시점**은 연결한 이벤트와 실행 핀에 달려 있다. 코드를 한 번 실행했다고 그래프가 한 번만 동작하는 것은 아니다.

### Python으로 최소 Action Graph 만들기

Stop 상태에서 Script Editor에 다음 전체 코드를 실행한다. **Window > Extensions**에서 `omni.graph.action`과 `omni.graph.ui_nodes`가 활성화되어 있어야 한다.

```python
import omni.graph.core as og
import omni.timeline
import omni.usd

stage = omni.usd.get_context().get_stage()
if stage is None:
    raise RuntimeError("먼저 장면을 연다.")
if not omni.timeline.get_timeline_interface().is_stopped():
    raise RuntimeError("Stop 상태에서 그래프를 만든다.")
graph_path = "/CourseActionGraph"
if stage.GetPrimAtPath(graph_path):
    raise RuntimeError("이미 그래프가 있다. 기존 그래프를 확인한 뒤 삭제하거나 이름을 바꾼다.")

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": graph_path, "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("tick", "omni.graph.action.OnTick"),
            ("print", "omni.graph.ui_nodes.PrintText"),
        ],
        keys.SET_VALUES: [("print.inputs:text", "Course graph is running")],
        keys.CONNECT: [("tick.outputs:tick", "print.inputs:execIn")],
    },
)
```

**Window > Graph Editors > Action Graph**에서 `/CourseActionGraph`를 열고 두 노드와 실행 연결을 확인한다. Play를 눌러 출력을 확인한 뒤 Stop한다. On Tick의 playback 관련 옵션에 따라 정지 중 평가 여부가 달라질 수 있으므로 노드 속성을 확인한다. 매 tick 로그 출력은 학습용이며 실제 제어 그래프에는 넣지 않는다. [OmniGraph via Python](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)

ROS 2 실습에서는 보통 **On Playback Tick**을 시작점으로 사용하고 simulation time을 메시지 timestamp에 연결한다. On Tick, On Playback Tick, physics callback을 같은 주기로 취급하지 않는다. 물리 120 Hz, 렌더링 60 Hz, 카메라 30 Hz 시스템에서는 각각의 실행 주기가 다를 수 있다.

## 6. 다음 실습으로 확장하기

| 필요한 기능 | 구현 위치 | 확인할 결과 |
| --- | --- | --- |
| 카메라 위치를 입력하는 창 | Extension UI | 단위, 범위, 현재 Stage 확인 |
| 카메라 Prim와 Render Product 생성 | 장면 생성 함수 | 유효한 카메라 경로와 해상도 |
| 매 물리 step에 바퀴 명령 계산 | physics callback | Play/Stop/reset 후 중복 호출 없음 |
| 카메라와 시각을 ROS 2로 발행 | Action Graph 또는 Python publisher | timestamp, frame ID, QoS 일치 |
| 100개 설정을 차례로 검증 | standalone | 종료 코드와 결과 파일로 실패 구분 |

Python custom node는 공식 [Custom Python Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html)를 참고한다. C++ 노드는 컴파일 환경과 ABI까지 확인해야 하며, Humble용 ROS 2 C++ 예제가 Jazzy에서 그대로 빌드된다고 가정하지 않는다.

실제 확인 순서는 **활성화 → 빈 장면 생성 → Play → Stop → 파일 교체 → 다시 생성 → 비활성화 → 재활성화**이다. 정적 Python 검사만으로 hot reload나 실제 GUI/물리 이벤트 동작을 통과했다고 판단하지 않는다.

## 출처

- [Adding and Updating Extensions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html)
- [Extension Template Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html)
- [OmniGraph via Python](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)
