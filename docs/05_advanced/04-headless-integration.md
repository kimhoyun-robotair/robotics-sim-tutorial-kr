# Headless 통합 테스트

> **목표:** 설치된 package 경로에서 Gazebo server-only stack을 실행하고 정상 동작, 계약 오류, runtime fault, timeout, cleanup을 서로 다른 증거로 판정한다.
> **선행 학습:** [물리와 주기 디버깅](03-physics-debugging.md)

## GUI 없이 무엇을 검증하는가

`gz sim -s`는 GUI client를 띄우지 않고 simulation server만 실행한다. 화면이 없으므로 성공 조건을 눈으로 판단할 수 없다. 대신 실제 Transport와 ROS 2 메시지를 파일로 수집하고 수치 조건을 검사한다.

이 저장소의 nominal scenario는 다음 관측을 한 실행에서 연결한다.

1. 설치된 world와 plugin 공유 라이브러리를 사용한다.
2. Gazebo server와 topic subscriber를 실행한다.
3. `/model/tutorial_bot/cmd_vel`에 전진 명령을 보낸다.
4. plugin distance가 0.1 m 이상 증가하는지 확인한다.
5. Gazebo pose를 ROS `geometry_msgs/msg/PoseArray`로 bridge해 ROS 쪽 변위를 확인한다.
6. 정지 명령과 reset 요청을 보내 distance가 다시 0이 되는지 확인한다.
7. 자신이 시작한 모든 process가 종료됐음을 receipt로 남긴다.

server log의 `PASS` 문자열 하나는 위 조건을 대신하지 못한다. 실행 중인 system에서 얻은 topic 표본과 종료 상태를 함께 보관해야 한다.

## headless world에 필요한 System

GUI가 없더라도 physics와 service 명령을 담당할 world System은 필요하다. 예제 world의 핵심은 다음과 같다.

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

`UserCommands`는 `/world/advanced_diagnostics/control`, `set_pose`, `create`, `remove` 같은 service 실습에 필요하다. `SceneBroadcaster`는 pose 정보를 Transport로 발행해 bridge가 읽을 수 있게 한다.

## 최소 server-only 실행

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash

export GZ_SIM_SYSTEM_PLUGIN_PATH="$PWD/examples/ros2_ws/install/tutorial_bot_plugins/lib"
export GZ_PARTITION="tutorial_headless_$$"
world="$PWD/examples/ros2_ws/install/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"

gz sim -s -r "$world"
```

렌더링 센서가 없는 이 world는 display server가 필요 없다. 카메라를 headless로 함께 시험한다면 CI 환경에 맞는 software rendering 설정이나 virtual display를 별도로 구성하고, 이 검사의 순수 physics 범위와 분리한다.

## readiness 뒤에 명령 보내기

고정된 `sleep 5`는 빠른 host에서는 낭비이고 느린 host에서는 부족할 수 있다. world control service가 discovery될 때까지 제한 시간 안에서 반복 확인한 뒤 simulation을 시작한다.

```bash
for attempt in {1..100}; do
  if gz service -l | grep -q '/world/advanced_diagnostics/control'; then
    break
  fi
  sleep 0.1
done

gz service -s /world/advanced_diagnostics/control \
  --reqtype gz.msgs.WorldControl \
  --reptype gz.msgs.Boolean \
  --timeout 1000 \
  --req 'pause: false'
```

readiness 조건이 끝까지 충족되지 않으면 timeout의 원인을 `server 시작 실패`, `plugin load 실패`, `discovery 지연` 중 하나로 좁힐 수 있도록 server log와 service 목록을 증거에 남긴다.

## 실제 이동과 양쪽 경계 관측

Gazebo 쪽 거리는 Transport subscriber로 수집한다.

```bash
gz topic -e --json-output \
  -t /tutorial_bot/diagnostics/distance \
  > /tmp/tutorial-distance.jsonl &
distance_pid=$!

gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0.5}'
```

ROS 쪽에서는 world pose를 단방향 bridge하고 실제 ROS 메시지를 수집한다. `[` 표시는 Gazebo에서 ROS로만 전달한다는 의미이다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  '/world/advanced_diagnostics/pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V' &
bridge_pid=$!

ros2 topic echo /world/advanced_diagnostics/pose/info \
  geometry_msgs/msg/PoseArray --filter 'len(m.poses) > 0' \
  > /tmp/tutorial-pose.log &
pose_pid=$!
```

검증기는 distance JSON의 마지막 `data`가 0.1 이상인지 확인하고, ROS pose 배열에서 entity별 첫 위치와 이후 위치의 최대 평면 변위를 계산한다. 두 관측을 모두 요구하면 plugin topic만 가짜로 발행하거나 bridge가 끊긴 상태를 성공으로 오판하지 않는다.

reset 전에는 먼저 정지 명령을 보낸다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel \
  -m gz.msgs.Twist -p 'linear: {x: 0}'

gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

reset 응답뿐 아니라 요청 뒤 새로 들어온 distance 표본이 0에 가까운지도 확인해야 한다.

<figure class="course-figure" id="advanced-headless-exit-taxonomy" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/headless-exit-taxonomy.svg" alt="headless checker의 nominal usage missing model missing plugin timeout cleanup 종료 코드를 구분한 도식" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 종료 코드는 원인을 분류하고, scenario·표본·cleanup 파일이 실제 관측을 증명한다.</figcaption>
</figure>

## 소유한 process만 정리하기

테스트 종료 시 `pkill gz`처럼 전역 이름으로 프로세스를 죽이면 사용자의 다른 simulation까지 중단할 수 있다. harness는 각 child를 새 process group으로 시작하고 PID와 `/proc/<pid>/stat`의 시작 tick을 함께 기록한다. cleanup은 자신이 만든 동일 identity만 `INT`, 제한된 대기, `TERM` 순서로 정리한다.

```bash
setsid gz sim -s "$world" > "$evidence/server.log" 2>&1 &
server_pid=$!
server_start_tick=$(awk '{print $22}' "/proc/$server_pid/stat")

cleanup() {
  current_tick=$(awk '{print $22}' "/proc/$server_pid/stat" 2>/dev/null || true)
  if [[ "$current_tick" == "$server_start_tick" ]]; then
    kill -INT -- "-$server_pid" 2>/dev/null || true
  fi
  wait "$server_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
```

실제 checker는 여러 subscriber와 bridge에도 같은 identity 검사를 적용하고 `cleanup.json`에 survivor와 identity mismatch를 기록한다.

## nominal scenario 실행

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
run_dir="$(mktemp -d)"
trap 'rm -rf "$run_dir"' EXIT
TUTORIAL_INSTALL_BASE="$TUTORIAL_INSTALL_BASE" ./scripts/check_advanced_course.sh --scenario nominal --evidence "$run_dir"
python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2])); assert s["status"] == "PASS" and s["plugin_distance"] >= 0.1 and c["status"] == "clean"; print("headless=PASS cleanup=clean")' "$run_dir/scenario.json" "$run_dir/cleanup.json"
```

성공했을 때 `scenario.json`에는 plugin 거리, ROS 변위, reset 결과가 들어 있고 `cleanup.json`에는 survivor 0과 `clean` 상태가 들어 있다.

## 종료 코드 계약

| 종료 | 의미 | 필수 관측 |
| ---: | --- | --- |
| 0 | nominal 성공 | 실제 distance·pose·reset 표본 |
| 64 | 사용법 또는 설치 계약 오류 | 잘못된 인자나 누락된 설치 경로 |
| 20 | 모델 미발견 | `WAITING_FOR_MODEL` 상태 |
| 21 | plugin 누락 | 실제 load 실패 로그 |
| 124 | 내부 deadline | deadline source와 seconds |
| 130 | SIGINT | signal 종료와 survivor 0 |
| 70 | cleanup 실패 | survivor 또는 PID identity 불일치 |

고장 주입은 정상 world 원본을 바꾸지 않고 evidence 디렉터리에 사본을 만든다. 예를 들어 plugin 누락 scenario는 SDF의 library 경로를 존재하지 않는 파일로 바꾸고 실제 `Failed to load system plugin` 로그를 요구한다.

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
| readiness timeout | `server.log`, control service 목록 | server가 떴는지와 partition을 확인한다. |
| distance만 움직임 | `bridge.log`, `ros-pose.log` | bridge 타입과 ROS 환경을 확인한다. |
| ROS pose만 움직임 | plugin load log, distance log | System 경로와 topic 이름을 확인한다. |
| reset 응답은 true인데 값이 큼 | reset 뒤 새 표본 구간 | 다음 `PostUpdate` 적용 여부를 확인한다. |
| cleanup exit 70 | `cleanup.json` | PID 재사용과 process group 등록 시점을 확인한다. |
| plugin-missing이 0 | `scenario.json`의 live sample 필드 | banner가 아니라 실제 load 오류를 검사한다. |

## 출처

- [Gazebo Sim server configuration](https://gazebosim.org/docs/harmonic/server_config/)
- [ros_gz_bridge Jazzy API](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)

[이전: 물리와 주기 디버깅](03-physics-debugging.md) · [다음: CI 재현성](05-ci-reproducibility.md)
