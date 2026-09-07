# GUI 없는 통합 테스트

> **목표:** 설치된 패키지 경로에서 Gazebo 서버 구성을 실행하고 정상 동작, 계약 오류, 실행 중 오류, 시간 초과, 프로세스 정리를 서로 다른 증거로 판정한다.
> **선행 학습:** [물리와 주기 디버깅](03-physics-debugging.md)

## GUI 없이 무엇을 검증하는가

`gz sim -s`는 GUI 클라이언트를 띄우지 않고 시뮬레이션 서버만 실행한다. 화면이 없으므로 성공 조건을 눈으로 판단할 수 없다. 대신 실제 Transport와 ROS 2 메시지를 파일로 수집하고 수치 조건을 검사한다.

이 저장소의 정상 시나리오는 다음 항목을 한 번의 실행에서 확인한다.

1. 설치된 월드와 플러그인 공유 라이브러리를 사용한다.
2. Gazebo 서버와 토픽 구독자를 실행한다.
3. `/model/tutorial_bot/cmd_vel`에 전진 명령을 보낸다.
4. 플러그인 거리가 0.1 m 이상 증가하는지 확인한다.
5. Gazebo 자세를 브리지에서 ROS `geometry_msgs/msg/PoseArray`로 변환해 ROS 쪽 변위를 확인한다.
6. 정지 명령과 초기화 요청을 보내 거리가 다시 0이 되는지 확인한다.
7. 자신이 시작한 모든 프로세스가 종료됐음을 기록으로 남긴다.

서버 로그의 `PASS` 문자열 하나는 위 조건을 대신하지 못한다. 실행 중인 시스템에서 얻은 토픽 표본과 종료 상태를 함께 보관해야 한다.

## GUI 없는 월드에 필요한 시스템

GUI가 없더라도 물리 계산과 서비스 명령을 담당할 월드 시스템은 필요하다. 예제 월드의 핵심은 다음과 같다.

```xml
<world name="advanced_diagnostics">
  <physics name="diagnostics_step" type="ignored">
    <max_step_size>0.001</max_step_size>
    <real_time_factor>1</real_time_factor>
  </physics>

  <plugin filename="gz-sim-physics-system"
          name="gz::sim::systems::Physics"/>
  <plugin filename="gz-sim-user-commands-system"
          name="gz::sim::systems::UserCommands"/>
  <plugin filename="gz-sim-scene-broadcaster-system"
          name="gz::sim::systems::SceneBroadcaster"/>
  <plugin filename="libTutorialBotDiagnosticsSystem.so"
          name="gz::sim::systems::TutorialBotDiagnostics">
    <model_name>tutorial_bot</model_name>
    <publish_period>0.1</publish_period>
  </plugin>
</world>
```

`UserCommands`는 `set_pose`, `create`, `remove`처럼 모델을 다루는 서비스를 제공한다. 일시정지·재생을 바꾸는 `/world/advanced_diagnostics/control`은 시뮬레이션 서버가 제공한다. `SceneBroadcaster`는 자세 정보를 Transport로 발행해 브리지가 읽을 수 있게 한다.

위 블록은 시스템 설정의 발췌다. 실제 `advanced-diagnostics.sdf`에는 무중력 환경과 `VelocityControl`로 움직이는 최소 모델도 들어 있다. 이 모델에는 바퀴와 화면 표시용 형상이 없으므로 주행 물리나 RViz 렌더링 검증에 사용하지 않는다. 이 장에서 확인하는 것은 플러그인의 거리 기록과 메시지 전달이다.

## 1단계: 서버를 일시정지 상태로 실행하기

[고급 과정 개요](index.md)에서 빌드를 마친 뒤, 터미널 A의 저장소 최상위에서 실행한다. `-r`을 생략하면 관찰 준비가 끝날 때까지 시뮬레이션 시간을 멈춰 둘 수 있다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
export GZ_PARTITION=tutorial_bot_headless_manual
world="$(ros2 pkg prefix tutorial_bot_gazebo)/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s "$world"
```

이 월드는 렌더링 센서가 없어 화면 서버가 필요 없다. 카메라나 GPU LiDAR는 별도의 렌더링 환경이 필요하다. 센서의 화면 결과는 [TF·RViz](../04_intermediate/06-tf-rviz.md)와 [센서 심화](../04_intermediate/08-advanced-sensors.md)의 절차로 따로 확인한다.

## 2단계: 서버 준비를 확인하고 실행하기

터미널 B에서 다음 명령을 실행한다. 준비될 때까지 최대 약 10초 동안 확인한다. 서비스를 찾지 못하면 뒤의 재생 요청을 보내지 않는다.

```bash
source /opt/ros/jazzy/setup.bash
export GZ_PARTITION=tutorial_bot_headless_manual

wait_for_world() {
  for attempt in {1..100}; do
    if gz service -l | grep -qx '/world/advanced_diagnostics/control'; then
      return 0
    fi
    sleep 0.1
  done
  echo '월드 제어 서비스를 찾지 못했다. 터미널 A의 오류와 GZ_PARTITION을 확인한다.' >&2
  return 1
}

if wait_for_world; then
  gz service -s /world/advanced_diagnostics/control \
    --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
    --timeout 1000 --req 'pause: false'
fi
```

`data: true` 응답이면 재생 요청이 수락된 것이다. 준비에 실패했다면 먼저 터미널 A에서 라이브러리 로드 오류가 있는지 보고 양쪽 `GZ_PARTITION`을 비교한다.

## 3단계: 브리지와 관측 준비하기

터미널 C에서 Gazebo 자세 토픽을 ROS 2로 전달한다. `[`는 Gazebo → ROS 2 단방향 전달을 뜻한다.

```bash
source /opt/ros/jazzy/setup.bash
export GZ_PARTITION=tutorial_bot_headless_manual
ros2 run ros_gz_bridge parameter_bridge \
  '/world/advanced_diagnostics/pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V'
```

터미널 D에서는 이동 전 ROS 자세를 한 번 확인한다. `PoseArray`에는 여러 모델과 링크의 자세가 함께 들어갈 수 있다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /world/advanced_diagnostics/pose/info \
  geometry_msgs/msg/PoseArray --once --filter 'len(m.poses) > 0'
```

출력이 나오지 않으면 터미널 C의 브리지 타입과 토픽 이름을 먼저 확인한다. 메시지를 받았으면 터미널 D를 거리 관측에 사용한다.

```bash
export GZ_PARTITION=tutorial_bot_headless_manual
gz topic -e -t /tutorial_bot/diagnostics/distance
```

## 4단계: 이동, 정지, 거리 초기화하기

터미널 B에서 0.5 m/s의 전진 명령을 보낸다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0.5}'
```

터미널 D에서 거리가 0.1 m 이상으로 증가하는지 본다. 이 속도 명령은 새 명령을 받을 때까지 유지된다. 확인했으면 터미널 B에서 정지시킨다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0}'
```

거리 증가가 멈추면 터미널 D의 출력을 `Ctrl+C`로 끝내고 3단계의 ROS 자세 확인 명령을 다시 실행한다. 이동 전보다 x 위치가 달라져야 한다. 이어서 터미널 B에서 누적 거리를 초기화한다.

```bash
gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

터미널 D에서 거리 출력을 다시 시작해 0으로 돌아왔는지 확인한다. Protobuf는 기본값을 생략하므로 0은 빈 메시지로 보일 수 있다. 초기화 서비스의 `true` 응답과 새 거리 표본을 함께 확인해야 한다.

자동 검사는 이 과정을 로그로 수집한다. `PoseArray`에는 개체 이름이 없으므로 현재 검사는 배열 순서가 유지되는 이 단순 월드에서 각 위치 항목의 변위를 비교한다. 실행 중 모델을 추가·제거하는 일반 월드에서는 이름이나 ID를 보존하는 관측 방식을 사용해야 한다.

<figure class="course-figure" id="advanced-headless-exit-taxonomy" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/headless-exit-taxonomy.svg" alt="서버 검사에서 정상, 설정 오류, 모델과 플러그인 누락, 시간 초과, 종료 실패의 코드를 구분한 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 종료 코드는 원인을 분류하고, 시나리오 결과·메시지 표본·종료 기록이 실제 관측을 보여 준다.</figcaption>
</figure>

## 실행한 프로세스 정리하기

수동 실습이 끝나면 터미널 A·C·D에서 실행 중인 서버, 브리지, 토픽 출력을 각각 `Ctrl+C`로 끝낸다. 자동 검사는 `scripts/check_advanced_headless.sh`가 실행한 프로세스만 정리한다.

스크립트는 PID와 프로세스 시작 시각을 함께 기록한다. 종료 전에 두 값이 같은지 확인해 운영체제가 같은 PID를 다른 프로세스에 재사용한 경우를 구분한다. 종료 신호 뒤에는 제한된 시간 동안 기다리고, 남은 프로세스에 후속 종료 신호를 보낸다. 전체 종료 처리는 해당 스크립트의 `register_process`, `cleanup`과 `scripts/lib/owned_process.sh`를 함께 읽는다.

검증 결과의 `cleanup.json`에서 `status`가 `clean`, `survivors`가 빈 배열, `identity_mismatch`가 `false`인지 확인한다. 짧은 예제로 종료 처리를 다시 작성하기보다 이 기록을 확인하는 편이 전체 프로세스의 종료 여부를 빠짐없이 점검할 수 있다.

## 정상 시나리오 실행

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario nominal --evidence "$run_dir"
python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2])); assert s["status"] == "PASS" and s["plugin_distance"] >= 0.1 and c["status"] == "clean"; print("headless=PASS cleanup=clean")' "$run_dir/scenario.json" "$run_dir/cleanup.json"
```

저장소 최상위에서 실행하고 `TUTORIAL_INSTALL_BASE`는 개요에서 빌드한 설치 경로로 지정한다. 성공하면 `scenario.json`에 `plugin_distance`, `ros_planar_displacement`, `post_reset_distance`가 기록된다. `cleanup.json`에는 빈 `survivors` 배열과 `clean` 상태가 들어 있다.

## 종료 코드 계약

| 종료 | 의미 | 필수 관측 |
| ---: | --- | --- |
| 0 | 정상 성공 | 실제 거리·자세·초기화 표본 |
| 64 | 사용법 또는 설치 계약 오류 | 잘못된 인자나 누락된 설치 경로 |
| 20 | 모델 미발견 | `WAITING_FOR_MODEL` 상태 |
| 21 | 플러그인 누락 | 실제 라이브러리 로드 실패 로그 |
| 124 | 내부 제한 시간 | 제한 시간을 정한 위치와 시간(초) |
| 130 | SIGINT | 신호로 종료됐다는 기록과 남은 프로세스 0개 |
| 70 | 프로세스 정리 실패 | 남은 프로세스 또는 PID 식별 정보 불일치 |

고장 주입은 정상 월드 원본을 바꾸지 않고 검증 결과 디렉터리에 사본을 만든다. 예를 들어 플러그인 누락 시나리오는 SDF의 라이브러리 경로를 존재하지 않는 파일로 바꾸고 실제 `Failed to load system plugin` 로그를 요구한다.

```bash
run_dir="$(mktemp -d)"
set +e
./scripts/check_advanced_course.sh \
  --scenario plugin-missing \
  --install-base "$TUTORIAL_INSTALL_BASE" \
  --evidence "$run_dir"
code=$?
set -e

test "$code" -eq 21
grep 'Failed to load system plugin' "$run_dir/server.log"
```

## 문제 해결

| 증상 | 먼저 볼 증거 | 판정 |
| --- | --- | --- |
| 준비 상태 확인 시간 초과 | `server.log`, 월드 제어 서비스 목록 | 서버가 떴는지와 통신 그룹을 확인한다. |
| 거리만 움직임 | `bridge.log`, `ros-pose.log` | 브리지 타입과 ROS 환경을 확인한다. |
| ROS 자세만 움직임 | 플러그인 로드 로그, 거리 로그 | 시스템 경로와 토픽 이름을 확인한다. |
| 초기화 응답은 true인데 값이 큼 | 초기화 뒤 새 표본 구간 | 다음 `PostUpdate` 적용 여부를 확인한다. |
| 프로세스 정리 종료 코드 70 | `cleanup.json` | PID 재사용과 프로세스 그룹 등록 시점을 확인한다. |
| `plugin-missing`이 종료 코드 0 반환 | `scenario.json`의 실측 표본 필드 | 실제 라이브러리 로드 오류를 검사한다. |

## 출처

- [Gazebo Sim UserCommands API](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1UserCommands.html)
- [Gazebo Sim server configuration](https://gazebosim.org/docs/harmonic/server_config/)
- [ros_gz_bridge Jazzy API](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)

[이전: 물리와 주기 디버깅](03-physics-debugging.md) · [다음: CI 재현성](05-ci-reproducibility.md)
