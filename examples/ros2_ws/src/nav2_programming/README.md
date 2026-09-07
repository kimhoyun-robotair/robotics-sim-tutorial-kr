# Nav2 프로그래밍 실습

시뮬레이션과 Nav2를 먼저 실행하세요. 저장한 지도를 사용하는 경우 RViz에서
**2D Pose Estimate**로 로봇의 현재 위치와 방향을 지정합니다. `map → odom → base_link`
TF가 준비되면 예제가 목표를 보냅니다. 예제는 초기 위치를 임의로 바꾸지 않습니다.

## 목표 한 곳으로 이동하기

```bash
ros2 run nav2_programming navigate_to_pose --ros-args \
  -p use_sim_time:=true -p goal:="[1.0, 0.0, 0.0]"
```

`goal`의 세 값은 지도 좌표계의 `[x(m), y(m), yaw(rad)]`입니다.
실제 지도에서 장애물이 없고 로봇이 통과할 수 있는 지점을 고르세요.
위 좌표는 입력 형식 예시이며 모든 지도에서 안전한 경로를 보장하지 않습니다.

## 여러 지점을 거쳐 이동하기

```bash
ros2 run nav2_programming navigate_through_poses --ros-args \
  -p use_sim_time:=true -p waypoints:="[1.0, 0.0, 0.0, 1.0, 1.0, 1.57]"
```

`waypoints`에는 `x, y, yaw`를 지점 수만큼 반복해서 넣습니다.
이 예제는 순찰을 한 차례 실행한 뒤 끝납니다.

각 지점에서 잠시 멈추려면 같은 좌표를 `follow_waypoints`에 전달하세요.

```bash
ros2 run nav2_programming follow_waypoints --ros-args \
  -p use_sim_time:=true -p waypoints:="[1.0, 0.0, 0.0, 1.0, 1.0, 1.57]"
```

정지 시간은 `simple_rover/config/nav2_params.yaml`의
`waypoint_pause_duration`으로 정하며 단위는 밀리초입니다.

## 결과 확인

성공하면 종료 코드가 0, 거절·실패·시간 초과면 1, Ctrl+C로 중단하면 130입니다.
한 지점으로 이동한 뒤 같은 터미널에서 `echo $?`로 확인할 수 있습니다.
Ctrl+C와 시간 초과 시 진행 중인 Nav2 목표를 취소합니다.
Nav2 준비 대기는 기본 60초, 이동 제한 시간은 실제 경과 시간으로 180초입니다.
Gazebo가 일시 정지되어 있어도 제한 시간은 흐릅니다.

필요하면 `-p startup_timeout_sec:=120.0 -p timeout_sec:=300.0`으로 늘리세요.
`-p frame_id:=map`으로 목표 좌표계를 지정할 수 있으며 기본값은 `map`입니다.
좌표 배열은 소수점이 있는 실수로 입력하세요.

공식 API: [Nav2 Simple Commander](https://docs.nav2.org/jazzy/configuration_and_development/simple_commander_api/simple_commander_api/).

