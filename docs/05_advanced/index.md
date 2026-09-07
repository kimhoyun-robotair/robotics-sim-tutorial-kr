# 고급: Gazebo 확장과 자동 검증

> **난이도:** 고급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [중급 프로젝트](../04_intermediate/11_project-autonomous-bot.md)

## 과정 목표

이 과정에서는 로봇의 이동 거리를 기록하는 C++ 시스템 플러그인을 만든다. 먼저 메시지로 동작을 확인하고, 모델 제거·잘못된 설정 같은 상황도 시험한다. 마지막에는 이 확인 과정을 자동화해 코드를 바꿀 때마다 다시 실행한다.

C++ 클래스·상속과 CMake 빌드를 처음 접한다면 각 장의 코드 조각을 읽기 전에 아래 명령으로 완성된 예제를 먼저 실행해 본다. 본문의 코드는 구조를 설명하기 위한 발췌이며, 빌드에는 `examples/ros2_ws/src/tutorial_bot_plugins/`의 전체 파일을 사용한다.

과정을 마치면 다음 작업을 수행할 수 있다.

- `Configure`, `PreUpdate`, `PostUpdate`, `Reset`의 역할을 구분한다.
- ECS 개체와 컴포넌트를 시뮬레이션 갱신 경계에서 안전하게 읽는다.
- C++17 공유 라이브러리를 등록하고 SDF `<plugin>`에서 로드한다.
- Jazzy의 vendor 패키지로 Harmonic 라이브러리를 CMake에 연결한다.
- Transport 콜백과 시뮬레이션 코드가 각각 어떤 상태를 변경할지 구분한다.
- Gazebo Transport와 ROS 2 사이에 `ros_gz_bridge` 경계를 둔다.
- 실행 컴퓨터 속도 대신 시뮬레이션 시간과 실제 표본으로 물리 결과를 비교한다.
- 설치 산출물만으로 GUI 없는 정상·오류·시간 초과·프로세스 정리를 판정한다.
- 같은 소스 커밋 SHA에서 문서와 실행 증거를 재생성한다.

<figure class="course-figure" id="advanced-course-architecture" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../assets/advanced/course-architecture.svg" alt="ECS 상태 관측, 통신, 가상 시간, 서버 검사, CI 결과가 이어지는 과정 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. ECS에서 읽은 상태를 통신·시간 검사로 확인하고 서버 검사와 CI 결과로 남긴다.</figcaption>
</figure>

## 먼저 알아둘 용어

이 과정에서 **계약**은 메시지 타입·이름·동작 조건처럼 프로그램끼리 지켜야 하는 규칙을 뜻한다. **시나리오**는 특정 입력부터 결과 확인까지의 한 실험이고, **검증 결과**는 그 실험에서 수집한 로그와 JSON 파일이다. **CI**는 저장소에 변경을 올릴 때 빌드와 검사를 자동 실행하는 환경이다.

## 플러그인이 제공할 기능

시스템 플러그인은 다음 SDF 블록으로 월드에 삽입된다.

```xml
<plugin filename="libTutorialBotDiagnosticsSystem.so"
        name="gz::sim::systems::TutorialBotDiagnostics">
  <model_name>tutorial_bot</model_name>
  <publish_period>0.1</publish_period>
</plugin>
```

플러그인은 다음 상태와 통신 지점을 제공한다.

| 구분 | 값 |
| --- | --- |
| 상태 | `WAITING_FOR_MODEL`, `READY`, `DISABLED`, `MODEL_REMOVED`, `INVALID_CONFIG` |
| 거리 토픽 | `/tutorial_bot/diagnostics/distance` (`gz.msgs.Double`) |
| 상태 토픽 | `/tutorial_bot/diagnostics/status` (`gz.msgs.StringMsg`) |
| 활성화 토픽 | `/tutorial_bot/diagnostics/enable` (`gz.msgs.Boolean`) |
| 초기화 서비스 | `/tutorial_bot/diagnostics/reset` (`gz.msgs.Empty` → `gz.msgs.Boolean`) |

## 학습 경로

1. [ECS 시스템 플러그인](01-ecs-system-plugin.md)에서 헤더, 소스, CMake, SDF를 구현한다.
2. [Transport 인터페이스](02-transport-interfaces.md)에서 통신 지점과 스레드 명령 보관함을 시험한다.
3. [물리와 주기 디버깅](03-physics-debugging.md)에서 시뮬레이션 시간 기반 발행을 비교한다.
4. [GUI 없는 통합 테스트](04-headless-integration.md)에서 GUI 없는 실제 통합 구성을 검증한다.
5. [CI 재현성](05-ci-reproducibility.md)에서 플랫폼과 검증 결과 계약을 워크플로로 옮긴다.
6. [시뮬레이션 통합 검증 프로젝트](06_project-production-stack.md)에서 모든 시나리오를 새로 빌드한 설치 결과로 묶는다.

각 장은 설명, 실제 저장소 코드 조각, 실행 명령, 관측 기준, 문제 해결 순서로 구성된다. 명령을 실행했는지만 보지 않고 어떤 토픽·서비스·JSON 필드가 완료를 증명하는지도 함께 확인한다.

## 1단계: 예제 빌드와 공통 경로 설정

[설치 장](../02_getting-started/02_installation-jazzy.md)의 의존성 설치를 마친 뒤 저장소 최상위에서 실행한다. 새 터미널에서도 명령을 이어서 쓸 수 있도록, 이 장 이후의 상대 경로는 모두 저장소 최상위를 기준으로 한다.

```bash
export TUTORIAL_REPO="$PWD"
source /opt/ros/jazzy/setup.bash
cd "$TUTORIAL_REPO/examples/ros2_ws"
colcon build --packages-up-to \
  tutorial_bot_plugins \
  tutorial_bot_gazebo \
  tutorial_bot_bringup \
  tutorial_bot_tests \
  --cmake-args -DBUILD_TESTING=ON
source install/setup.bash
export TUTORIAL_INSTALL_BASE="$PWD/install"
cd "$TUTORIAL_REPO"
```

`--packages-up-to`는 나열한 패키지뿐 아니라 같은 작업 공간에 있는 의존 패키지도 함께 빌드한다. `Summary:`에 실패가 없어야 다음 단계로 넘어간다. `TUTORIAL_INSTALL_BASE`는 기본 분리 설치 방식의 `install` 디렉터리이며, 이 예제에서는 `--merge-install`을 사용하지 않는다.

## 2단계: 설치 파일 확인

아래 블록은 소스 작업 공간의 파일을 읽지 않는다. 새 빌드 뒤 설정된 `TUTORIAL_INSTALL_BASE` 아래의 설치 결과만 검사한다.

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so" || exit 1
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf" || exit 1
printf 'advanced-install=ready\n'
```

예상 출력은 `advanced-install=ready`이다. 앞선 두 파일 검사가 실패하면 출력 전에 종료한다.

## 3단계: 서버 실행과 상태 확인

터미널 A에서 실행한다. `GZ_PARTITION`은 서로 통신할 Gazebo 프로세스를 묶는 이름이다. 아래 실습을 진행하는 모든 터미널에서 같은 문자열을 쓴다.

```bash
export GZ_PARTITION=tutorial_bot_advanced_manual
world="$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s -r "$world"
```

터미널 B에서는 저장소 최상위에서 환경을 다시 불러온 뒤 확인한다. 환경 변수는 새 터미널에 자동으로 전달되지 않는다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
export TUTORIAL_INSTALL_BASE="$PWD/examples/ros2_ws/install"
export GZ_PARTITION=tutorial_bot_advanced_manual
gz topic -l | grep /tutorial_bot/diagnostics
gz topic -e -t /tutorial_bot/diagnostics/status
```

`data: "READY"`가 반복되면 모델을 찾고 상태를 발행한 것이다. 출력은 `Ctrl+C`로 끝낸다. 이후 실습 명령을 실행할 때 서버는 켜 둔다. 장을 마치면 터미널 A에서도 `Ctrl+C`로 서버를 종료한다.

자동 검사 명령은 저장소 최상위에서 실행한다. 새 터미널에서는 위의 환경 설정과 `TUTORIAL_INSTALL_BASE` 설정을 먼저 반복한다. 별도의 임시 설치 경로로 빌드했다면 해당 경로의 `setup.bash`와 `TUTORIAL_INSTALL_BASE`를 사용한다.

## 문제 해결

라이브러리가 없으면 `tutorial_bot_plugins`가 새 빌드에 포함됐는지 확인한다. 월드가 없으면 `tutorial_bot_gazebo`의 설치 규칙을 확인한다. `.so`는 있지만 로드되지 않으면 `GZ_SIM_SYSTEM_PLUGIN_PATH`, SDF `filename`, 플러그인 별칭을 차례로 비교한다. 이전 설치를 덮어쓰며 원인을 찾기보다 새 빌드·설치 디렉터리로 재현한다.

## 출처

- [Gazebo Sim: Create System Plugins](https://gazebosim.org/api/sim/8/createsystemplugins.html)
- [Gazebo Transport tutorials](https://gazebosim.org/api/transport/13/tutorials.html)
- [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/)

[선행 과정](../04_intermediate/11_project-autonomous-bot.md) · [다음: ECS 시스템 플러그인](01-ecs-system-plugin.md)
