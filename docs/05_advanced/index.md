# 고급: Gazebo 확장과 자동 검증

> **난이도:** 고급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [중급 프로젝트](../04_intermediate/11_project-autonomous-bot.md)

## 과정 목표

이 과정은 `tutorial_bot`의 구동을 바꾸지 않는 진단용 System Plugin을 구현하고, 실제 endpoint와 simulation time을 거쳐 CI 증거까지 연결한다. 개념을 읽은 뒤 최소 코드를 만들고, 직접 실행해 관측하며, 고장을 주입하고, 마지막에 자동 gate로 묶는 흐름이다.

과정을 마치면 다음 작업을 수행할 수 있다.

- `Configure`, `PreUpdate`, `PostUpdate`, `Reset`의 역할을 구분한다.
- ECS entity와 component를 simulation update 경계에서 안전하게 읽는다.
- C++17 공유 라이브러리를 등록하고 SDF `<plugin>`에서 로드한다.
- Jazzy vendor package와 Gazebo Harmonic CMake target을 연결한다.
- Transport callback과 simulation thread 사이의 소유권을 분리한다.
- Gazebo Transport와 ROS 2 사이에 `ros_gz_bridge` 경계를 둔다.
- host 속도 대신 simulation time과 실제 표본으로 물리 결과를 비교한다.
- 설치 산출물만으로 headless 정상·fault·timeout·cleanup을 판정한다.
- 같은 source SHA에서 문서와 runtime 증거를 재생성한다.

<figure class="course-figure" id="advanced-course-architecture" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../assets/advanced/course-architecture.svg" alt="ECS System Transport simulation time headless 검사 CI 증거가 이어지는 고급 과정 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. ECS 관측은 Transport와 simulation time 검증을 거쳐 headless·CI 증거로 전달된다.</figcaption>
</figure>

## 만들 결과의 핵심 계약

System Plugin은 다음 SDF 블록으로 world에 삽입된다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <publish_period>0.1</publish_period>
</plugin>
```

플러그인은 다음 상태와 endpoint를 제공한다.

| 구분 | 값 |
| --- | --- |
| 상태 | `WAITING_FOR_MODEL`, `READY`, `DISABLED`, `MODEL_REMOVED`, `INVALID_CONFIG` |
| 거리 topic | `/tutorial_bot/diagnostics/distance` (`gz.msgs.Double`) |
| 상태 topic | `/tutorial_bot/diagnostics/status` (`gz.msgs.StringMsg`) |
| enable topic | `/tutorial_bot/diagnostics/enable` (`gz.msgs.Boolean`) |
| reset service | `/tutorial_bot/diagnostics/reset` (`gz.msgs.Empty` → `gz.msgs.Boolean`) |

## 학습 경로

1. [ECS System Plugin](01-ecs-system-plugin.md)에서 헤더, 소스, CMake, SDF를 구현한다.
2. [Transport 인터페이스](02-transport-interfaces.md)에서 endpoint와 thread mailbox를 시험한다.
3. [물리와 주기 디버깅](03-physics-debugging.md)에서 simulation time 기반 발행을 비교한다.
4. [Headless 통합 테스트](04-headless-integration.md)에서 GUI 없는 실제 stack을 검증한다.
5. [CI 재현성](05-ci-reproducibility.md)에서 플랫폼과 evidence 계약을 workflow로 옮긴다.
6. [Production Stack 프로젝트](06_project-production-stack.md)에서 모든 scenario를 fresh install로 묶는다.

각 장은 설명, 실제 저장소 코드 조각, 실행 명령, 관측 기준, 문제 해결 순서로 구성된다. 명령을 실행했는지만 보지 않고 어떤 topic·service·JSON field가 완료를 증명하는지도 함께 확인한다.

## 시작 전 build

```bash
cd examples/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select \
  tutorial_bot_plugins \
  tutorial_bot_gazebo \
  tutorial_bot_bringup \
  tutorial_bot_tests \
  --cmake-args -DBUILD_TESTING=ON
source install/setup.bash
```

## 설치 산출물 확인

아래 블록은 source workspace의 파일을 읽지 않는다. fresh build 뒤 설정된 `TUTORIAL_INSTALL_BASE` 아래의 설치 결과만 검사한다.

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
printf 'advanced-install=ready\n'
```

예상 출력은 `advanced-install=ready`이다. 앞선 두 파일 검사가 실패하면 출력 전에 종료한다.

## 직접 확인할 첫 명령

```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH="$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib"
world="$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s -r "$world"
```

다른 터미널에서 다음 topic이 나타나면 플러그인 로드와 Transport discovery의 첫 단계가 완료된 것이다.

```bash
gz topic -l | grep /tutorial_bot/diagnostics
gz topic -e -t /tutorial_bot/diagnostics/status
```

## 문제 해결

라이브러리가 없으면 `tutorial_bot_plugins`가 fresh build에 포함됐는지 확인한다. world가 없으면 `tutorial_bot_gazebo`의 install 규칙을 확인한다. `.so`는 있지만 로드되지 않으면 `GZ_SIM_SYSTEM_PLUGIN_PATH`, SDF `filename`, plugin alias를 차례로 비교한다. 이전 install을 덮어쓰며 원인을 찾기보다 새 build·install 디렉터리로 재현한다.

## 출처

- [Gazebo Sim: Create System Plugins](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Transport tutorials](https://gazebosim.org/api/transport/13/tutorials.html)
- [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/)

[선행 과정](../04_intermediate/11_project-autonomous-bot.md) · [다음: ECS System Plugin](01-ecs-system-plugin.md)
