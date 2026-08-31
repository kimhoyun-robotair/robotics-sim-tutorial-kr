# 핵심 시뮬레이션 학습 경로

이 장은 빈 Stage를 만드는 수준에서 시작해 로봇을 가져오고, 물리를 조정하고, 관절을 제어하고, 충돌 회피 동작과 반응형 행동을 만드는 수준까지 이어진다. 아래 순서대로 실습하면 각 파일의 결과가 다음 파일의 전제가 된다.

| 순서 | 문서 | 완주 기준 |
|---:|---|---|
| 1 | [GUI, Stage와 Asset](01-gui-stage-and-assets.md) | GUI에서 장면을 만들고 prim 경로와 reference를 설명할 수 있다. |
| 2 | [Python 워크플로와 Scene API](02-python-workflows-and-scene.md) | Standalone, Script Editor, Extension의 수명 주기를 구분하고 같은 장면을 코드로 만든다. |
| 3 | [물리, 재질, 조명과 센서](03-physics-material-light-sensors.md) | 강체·충돌체·물리 재질을 설정하고 카메라와 접촉 데이터를 읽는다. |
| 4 | [Articulation, Joint와 Controller](04-articulation-joints-controllers.md) | 관절 순서를 확인한 뒤 위치·속도 명령을 안전하게 적용한다. |
| 5 | [로봇 가져오기와 설정](05-robot-import-and-setup.md) | URDF/MJCF 로봇을 SimReady에 가까운 USD 자산으로 정리하고 검증한다. |
| 6 | [모바일 로봇과 매니퓰레이터](06-mobile-and-manipulator.md) | 차동 구동 로봇과 매니퓰레이터를 각각 제어한다. |
| 7 | [Lula, RMPflow와 궤적 생성](07-motion-generation.md) | IK·궤적·전역 경로·반응형 정책의 차이를 알고 적절한 도구를 선택한다. |
| 8 | [Cortex, 디버깅과 프로파일링](08-cortex-debugging-profiling.md) | 행동을 상태와 결정으로 분리하고 물리·Python·성능 문제를 계층별로 진단한다. |

## 이 장에서 사용하는 전제

- 운영체제는 Ubuntu 24.04 LTS이다.
- Isaac Sim 5.1.0을 워크스테이션 방식으로 설치했으며 설치 루트를 `~/isaacsim`이라고 가정한다. 다른 위치에 설치했다면 명령의 경로만 바꾸면 된다.
- 터미널 예제는 Isaac Sim 설치 루트에서 실행한다.
- ROS 2 Jazzy 연동은 별도 ROS 2 장에서 다룬다. 이 장은 ROS 없이도 동작하는 Core API와 로봇 시뮬레이션 자체에 집중한다.
- 5.1 문서에는 기존 Core API와 새 Core Experimental API가 함께 존재한다. 이 장은 공식 튜토리얼 및 5.1 예제와 바로 대조할 수 있도록 안정적으로 널리 쓰이는 `isaacsim.core.api` 계열을 주로 사용하고, 새 프로젝트에서 Experimental API를 평가해야 한다는 점을 별도로 표시한다.

> **버전 주의:** NVIDIA 문서에서 Isaac Sim 5.1.0은 현재 지원이 끝난 릴리스로 표시된다. 이 저장소는 재현성을 위해 5.1.0에 고정한다. 다른 버전에서 실행할 때는 모듈 이름, 자산 경로와 노드 이름을 해당 버전 문서에서 다시 확인해야 한다.

## 예제 실행 표기

다음 표기를 구분한다.

```bash
# Standalone Python 파일을 실행하는 명령
cd ~/isaacsim
./python.sh /절대/경로/example.py
```

```python
# [Script Editor]라고 적힌 코드는 실행 중인 Isaac Sim에서
# Window > Script Editor를 열어 실행한다.
```

독립 실행 파일을 시스템의 `python3`로 실행하지 않는다. Isaac Sim의 `python.sh`가 Kit 플러그인, Python 경로와 네이티브 라이브러리를 맞춘다.

## 매 실습의 공통 확인 순서

1. Output Log에서 첫 번째 오류를 찾는다. 뒤따르는 오류보다 최초 오류가 원인일 가능성이 높다.
2. Stage에서 예상한 prim 경로가 실제로 존재하는지 확인한다.
3. Timeline이 **Play** 상태인지 확인한다.
4. 초기화가 필요한 wrapper는 `World.reset()` 또는 `await World.reset_async()` 뒤에 읽는다.
5. 단위가 맞는지 확인한다. Core 로봇 API의 관절각은 보통 radian이며 USD GUI의 회전 속성은 degree로 보일 수 있다.
6. 재현이 되지 않으면 새 Stage에서 최소 예제로 줄인다.

## 출처

- [Isaac Sim 5.1 문서 홈](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)
- [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- [Python Scripting Concepts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/python_scripting_concepts.html)
- [Release Notes 5.1.0](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)
