# 36. 중간 프로젝트 7 — 기록 재생과 통신 검증

[전체 목차](../../README.md) · [이전](35-rosbag-nav2.md)

## 완성할 결과

같은 ROS 실험을 실시간 관찰과 rosbag 재생으로 각각 검사하고, 어떤 결과가 실제 제어 동작을 증명하는지 구분한다. 필수 프로젝트는 자산 없이 실행할 수 있는 33단계 장면을 사용한다. 35단계 Nova Carter Nav2의 기록 분석은 선택 확장이다. 다음 네 결과를 만든다.

| 결과물 | 보여 주는 것 |
|---|---|
| `project7-live.json` | clock·TF·odometry와 실제 명령 단절 정지 |
| `project7-bag/` | 메시지 기록 |
| `project7-replay.json` | 기록된 상태의 재생 수신·형식·시간 증가 |
| `project7-notes.md` | 환경, 검사 결과, 실패와 수정 내역 |

**재생 PASS는 Isaac Sim의 물리 계산이나 actuator가 지금 정상 동작한다는 뜻이 아니다.** 저장된 메시지를 다시 받았다는 뜻이다. 두 검사 결과를 하나로 섞지 않는다.

## 1. 독립된 실행으로 시작한다

GUI의 Carter/Nav2, guard, 키보드 제어, 다른 `/clock` publisher를 종료한다. 29단계의 환경을 적용한 터미널 A에서 원점 장면을 새로 실행한다.

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/07_ros_scene.py --seconds 120 \
  --output artifacts/project7-scene.json
```

터미널 B에서 기록을 시작한다.

```bash
ros2 bag record --use-sim-time -o artifacts/project7-bag \
  /clock /tutorial/odom /tf
```

터미널 C에서 명령 단절 검사를 수행한다.

```bash
python3 scripts/ros_acceptance.py --mode scene --duration 15 \
  --exercise-timeout --output artifacts/project7-live.json
```

검사기는 약 2초간 전진 명령을 발행한 뒤 멈춘다. timeout 정지까지 확인한 후 B에서 Ctrl+C로 기록을 끝낸다. `ros2 bag info artifacts/project7-bag`에서 기록 시간이 최소 15초 이상인지 확인한다. 부족하면 새 폴더 이름으로 다시 기록한다.

## 2. live 결과를 판정한다

```bash
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path("artifacts/project7-live.json").read_text())
assert report["status"] == "PASS", report
for name in ("command_caused_motion", "watchdog_observed_stop", "pose_stable_after_timeout"):
    assert report["checks"][name] is True, name
print("명령 반응과 수신 timeout 정지를 관측했다")
PY
```

수신 개수만 세면 로봇이 가만히 있어도 통과할 수 있다. 따라서 움직임과 명령 단절 후 정지를 따로 검사한다. 이 장면은 기구학 상태를 발행하므로 판정의 범위도 기구학과 통신이다. 바퀴 로봇에 대해서는 별도의 물리 상태·전도 검사와 실제 odometry 기반 주행 시험이 필요하다.

## 3. 시뮬레이터를 종료하고 재생한다

터미널 A의 예제가 `--seconds` 제한으로 종료되거나 창을 닫아 정상 종료될 때까지 기다린다. `/clock`에 활성 publisher가 남지 않았는지 확인한다.

```bash
ros2 topic info /clock --verbose
```

토픽이 없어졌다는 메시지가 나와도 정상이다. **실시간 clock과 bag의 clock을 동시에 발행하지 않는다.** RViz를 새로 실행하고 Fixed Frame을 `odom`, Odometry topic을 `/tutorial/odom`으로 설정한다.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

터미널 C에서 검사기를 먼저 시작한다. 이때 `--exercise-timeout`은 사용하지 않는다.

```bash
python3 scripts/ros_acceptance.py --mode scene --duration 10 \
  --output artifacts/project7-replay.json
```

2초 안에 터미널 B에서 기록을 재생한다.

```bash
ros2 bag play artifacts/project7-bag
```

이번 bag에는 `/clock`이 이미 들어 있으므로 `--clock`을 추가하지 않는다. 기록된 clock 자체를 재생하는 방법이다. `/clock`을 기록하지 않은 다른 bag에서는 `--clock`으로 player가 생성하는 시간을 사용할 수 있으나, 그 경우 기록 시간과 메시지 header 시간의 관계를 따로 확인해야 한다. 본 프로젝트에서는 두 방식을 섞지 않는다. [ROS 공식 rosbag2](https://github.com/ros2/rosbag2)

기록을 15초 이상 남기고 검사기를 10초 실행하는 이유는 검사 종료 시점에도 재생 odometry가 최근 메시지여야 하기 때문이다. 재생이 끝난 뒤 한참 지나 검사기가 종료되면 `odometry_recent`가 실패하는 것이 맞다.

## 4. live와 replay 보고서를 비교한다

```bash
python3 - <<'PY'
import json
from pathlib import Path
for mode in ("live", "replay"):
    data = json.loads(Path(f"artifacts/project7-{mode}.json").read_text())
    print(mode, data["status"], data.get("counts", {}))
    for name, passed in data.get("checks", {}).items():
        if not passed:
            print("실패:", name)
PY
```

두 결과의 메시지 개수가 완전히 같을 필요는 없다. 검사 시작 시점과 관찰 시간이 다르다. 필수 조건은 각 실행의 수신 여부, 시간 증가, 유한한 pose·정규화된 quaternion·속도 제한 검사가 통과하는 것이다. live 결과에만 명령·정지 검사가 있는지 확인한다.

의도적인 실패도 하나 수행한다. bag 재생이 끝난 상태에서 `--duration 8`로 검사기만 실행하면 FAIL이어야 한다. 이전 PASS JSON이 남아 있어도 새 실행의 결과로 덮어쓰며, 스크립트 종료 코드도 1이 된다. 로그 없이 예전 PASS 파일만 보는 검증 절차는 만들지 않는다.

## 5. 선택 확장: Nova Carter 기록을 분석한다

35단계의 Carter/Nav2를 다시 실행하고, 목표 하나를 수행하는 동안 기록한다. 직육면체용 `/tutorial/odom` 대신 실제 Carter 토픽을 사용한다.

```bash
ros2 bag record --use-sim-time -o artifacts/carter-goal-bag \
  /clock /tf /tf_static /chassis/odom /scan \
  /front_3d_lidar/lidar_points /tutorial/nav2_cmd_vel_safe
```

기록을 끝낸 뒤 Nav2·guard·Isaac Sim을 종료한다. 재생할 때는 관찰용 메시지만 선택한다. 기록에 들어 있는 속도 명령을 실행 중인 로봇에 다시 보내지 않도록 토픽 목록을 명시한다.

```bash
ros2 bag play artifacts/carter-goal-bag --topics \
  /clock /tf /tf_static /chassis/odom /scan /front_3d_lidar/lidar_points
```

RViz에서 `map`까지 포함한 좌표 변환이 필요한 경우 기록된 TF와 사용한 정적 지도를 함께 준비한다. 지도 이미지는 bag의 경로만으로 자동 로딩되지 않는다. 처음에는 Fixed Frame `odom`에서 센서와 odometry를 비교한다. 이 저장소의 `ros_acceptance.py --mode scene`은 `tutorial_base`와 `/tutorial/odom`을 검사하므로 Carter 기록에 그대로 적용하지 않는다.

Nav2를 bag 데이터에 연결해 계획·위치 추정을 오프라인 평가하는 확장은 가능하지만, bag 재생은 새 제어 명령에 맞춰 센서 결과를 바꾸지 않는다. 따라서 기록으로 목표 도달 제어를 다시 검증했다고 결론 내리지 않는다. 실시간 Nav2 목표 도달 결과는 35단계의 별도 실행에서 기록한다. [NVIDIA ROS 연결 구조](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/ros2_reference_architecture.html)

## 완료 기준과 과제

메모에 Ubuntu·ROS·Isaac Sim 버전, Domain ID, 사용 파일, 실제 실행한 명령, live/replay 결과를 적는다. `FAIL`이면 실패 키와 원인도 그대로 남긴다. clock이 역행하면 다른 clock publisher나 loop 재생을, TF가 누락되면 frame 이름과 `/tf_static` QoS를, 대용량 점군에서 수신이 끊기면 처리량·VRAM·기록 장치 속도를 점검한다.

과제로 `ros2 bag play artifacts/project7-bag --rate 0.5`를 실행한다. 벽시계 기준 움직임은 느려져도 기록된 header 시간과 TF의 관계는 유지되는지 관찰한다. 실행하지 못한 GPU·ROS 검사는 결과표에 **미실행**으로 남긴다.
