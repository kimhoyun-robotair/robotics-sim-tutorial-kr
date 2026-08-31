# Extension과 OmniGraph 개발

Extension은 지속되는 기능을 담고, OmniGraph는 frame마다 흐르는 data와 execution dependency를 시각화하다. UI·설정·서비스는 Extension에, sensor-to-controller처럼 시간 순서가 중요한 pipeline은 graph에 두면 경계가 선명하다.

## 최소 Python Extension 구조

```text
course.extension/
├── config/extension.toml
└── course/extension/
    ├── __init__.py
    └── extension.py
```

`config/extension.toml`을 작성하다.

```toml
[package]
version = "0.1.0"
title = "Isaac Sim 5.1 Course Extension"
description = "과정용 최소 Extension"
category = "Simulation"

[dependencies]
"omni.kit.uiapp" = {}

[[python.module]]
name = "course.extension"
```

`extension.py`에서 lifecycle을 명시하다.

```python
import omni.ext


class CourseExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:
        self._ext_id = ext_id
        self._subscriptions = []
        print(f"[course] start: {ext_id}")

    def on_shutdown(self) -> None:
        self._subscriptions.clear()
        print("[course] stop")
```

Extension Manager에서 경로를 추가하고 extension을 enable하다. 개발 중 hot reload가 일어나므로 전역 singleton, callback, UI window를 중복 생성하지 않게 하다.

## Python으로 Action Graph를 생성하다

다음 코드는 Script Editor에서 `/ActionGraph`를 만들고 매 simulation tick마다 문자열을 출력하다.

```python
import omni.graph.core as og

keys = og.Controller.Keys
og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("tick", "omni.graph.action.OnTick"),
            ("print", "omni.graph.ui_nodes.PrintText"),
        ],
        keys.SET_VALUES: [
            ("print.inputs:text", "Isaac Sim 5.1 course"),
            ("print.inputs:logLevel", "Warning"),
        ],
        keys.CONNECT: [
            ("tick.outputs:tick", "print.inputs:execIn"),
        ],
    },
)
```

Stage에서 `/ActionGraph`를 선택하고 `Window > Graph Editors > Action Graph`를 열어 node와 edge를 확인하다. 이름 문자열은 extension 버전에 묶이므로 5.1.0에서 node type을 검색해 확인하다.

## graph 설계 규칙

- execution edge로 순서를 명시하고 우연한 node 평가 순서에 의존하지 않다.
- simulation time과 system time을 섞지 않다.
- ROS publisher의 QoS, frame ID, topic namespace를 parameter로 노출하다.
- 같은 graph를 복제할 때 node 안에 절대 prim path를 하드코딩하지 않다.
- 큰 Python 작업을 매 render tick에 실행하지 않고 physics rate 또는 gate node로 주기를 제한하다.

## custom node를 선택하다

단순한 project glue는 Python node가 빠르다. 높은 빈도, 큰 array, 결정적인 latency가 필요한 계산은 C++ node를 고려하다. 그러나 공식 5.1 ROS 2 Custom C++ OmniGraph 예제는 ROS 2 Humble 전용이라고 명시하므로, 이 과정의 Ubuntu 24.04/Jazzy 조합에 그대로 적용되었다고 가정하지 않다. Jazzy에서는 Python node 또는 독립 ROS 2 C++ node를 우선 사용하고 별도 porting test를 수행하다.

## 출처

- [Extension Template Generator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html)
- [Adding and Updating Extensions Guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html)
- [Isaac Sim OmniGraph Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html)
- [OmniGraph via Python Scripting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_scripting.html)
- [Custom Python Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html)
