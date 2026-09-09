# 프로젝트 3: 창고에서 세 목표를 순서대로 방문한다

이 프로젝트는 공식 Nova Carter 창고 예제로 시작한다. 먼저 같은 장면·지도·센서 설정에서 목표 한 개에 도착한 뒤, 창고에 장애물을 추가하고 직접 만든 지도로 세 목표를 방문한다. 처음부터 차량과 센서를 모두 바꾸면 주행 실패의 원인을 분리하기 어렵다.

## 준비할 것

- [Bridge와 공식 워크스페이스](../04-ros2/01-install-bridge-workspace.md)를 완료한다.
- [Nav2 워크숍](../04-ros2/12-nav2-workshop.md)에서 `/clock`, TF, 점군, 지도 연결을 확인한다.
- Ubuntu 24.04 외부 ROS 터미널에서는 시스템 Jazzy를 사용하고, Isaac Sim 터미널에는 Python 3.12 ROS 환경을 넣지 않는다.
- 공식 워크스페이스는 `IsaacSim-5.1.0` 태그를 사용한다. 커밋은 `50de00358f220d790d17050c6368cfe9a9cb9f51`이다.

이 문서의 상대 경로 명령은 **이 튜토리얼 저장소 루트**에서 실행한다.

```bash
mkdir -p project-3/stages project-3/maps project-3/config project-3/results
source /opt/ros/jazzy/setup.bash
source ~/IsaacSim-ros_workspaces/jazzy_ws/install/local_setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 pkg prefix carter_navigation
```

Isaac Sim 쪽 `ROS_DOMAIN_ID`도 0으로 맞춘다. 다른 실습에서 17이나 42를 썼다면 양쪽 프로세스를 종료한 뒤 같은 값으로 다시 시작한다.

## 1단계: 공식 장면을 그대로 실행한다

1. Isaac Sim에서 `Window > Examples > Robotics Examples`를 연다.
2. 왼쪽 목록에서 `ROS2 > Navigation > Nova Carter`를 선택해 불러온다.
3. 로봇, 바닥, 창고가 모두 보일 때까지 기다린다. 흰 상자만 보이거나 로봇 링크가 빠져 있으면 자산 로딩부터 해결한다.
4. Play한 뒤 외부 ROS 터미널에서 실행한다.

```bash
ros2 launch carter_navigation carter_navigation.launch.py use_sim_time:=true
```

이 명령은 RViz2, Nav2와 점군→LaserScan 변환 노드를 실행한다. 공식 예제는 `/front_3d_lidar/lidar_points`를 받아 `/scan`을 만든다. `/scan` 변환 노드를 별도로 하나 더 띄우지 않는다. 차량의 odometry 토픽은 `/chassis/odom`이다. 토픽·파라미터 이름은 [5.1.0 launch 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/launch/carter_navigation.launch.py)와 [파라미터 소스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/blob/50de00358f220d790d17050c6368cfe9a9cb9f51/jazzy_ws/src/navigation/carter_navigation/params/carter_navigation_params.yaml)를 기준으로 한다.

```bash
ros2 topic echo /clock --once
ros2 topic echo /chassis/odom --once --field header
ros2 topic info /front_3d_lidar/lidar_points -v
ros2 topic echo /scan --once --qos-reliability best_effort --field header
ros2 run tf2_ros tf2_echo base_link front_3d_lidar
```

마지막 명령은 계속 실행되므로 값이 나오는 것을 확인한 뒤 `Ctrl+C`로 종료한다. 센서의 `frame_id`와 위 TF 이름이 실제 출력에서 다른 경우에는 토픽 헤더에 나온 이름을 기준으로 추적한다.

**완료 판정:** 로봇이 가만히 있을 때 점군도 창고 벽에 정렬되어 있고, `/clock`과 센서 타임스탬프가 진행한다. 토픽 이름만 나타나는 상태는 통과가 아니다.

## 2단계: 초기 위치와 목표 한 개를 확인한다

RViz2의 Fixed Frame은 `map`으로 둔다. 공식 초기 위치는 파라미터 파일에 있지만, 로봇을 옮겼다면 자동으로 맞지 않는다.

1. `2D Pose Estimate`를 누른다.
2. 지도에서 Isaac Sim 로봇의 실제 위치를 클릭하고, 로봇 앞방향으로 드래그한다.
3. LaserScan이 지도 벽에 겹치는지 확인한다. 맞지 않으면 목표를 보내지 않고 위치를 다시 지정한다.
4. `Navigation2 Goal` 또는 `Nav2 Goal` 버튼으로 가까운 빈 공간을 지정한다.
5. 로봇이 정지하고 Nav2가 성공 결과를 반환할 때까지 관찰한다.

```bash
ros2 lifecycle get /amcl
ros2 lifecycle get /controller_server
ros2 run tf2_ros tf2_echo map base_link
ros2 action info /navigate_to_pose
```

`active` 상태를 확인한다. TF가 없으면 지도 위치를 추측해 여러 번 클릭하지 말고 `map → odom`, `odom → base_link`, 센서 연결 중 어느 부분이 빠졌는지 찾는다.

## 3단계: 작업용 창고와 지도를 만든다

1. Nav2 터미널을 종료하고 Isaac Sim을 Stop한다.
2. `File > Save As`로 `project-3/stages/warehouse.usd`에 작업용 장면을 저장한다.
3. 로봇이 없는 통로에 고정 상자 하나를 추가한다. 상자는 바닥 위에 두고 Collider를 적용한다. 이 단계에서는 Rigid Body를 추가하지 않아 상자가 움직이지 않게 한다.
4. 상자를 통과하지 못하는지 collision 표시로 확인한다. 렌더링에만 보이고 충돌 형상이 없는 물체는 물리 검증을 통과한 것이 아니다.
5. 지도 생성용 복사본 `warehouse_mapping.usd`를 따로 저장하고 이 복사본에서만 로봇 prim을 제거한다.
6. `Tools > Robotics > Occupancy Map`에서 창고 prim을 선택하고 `BOUND SELECTION`으로 범위를 잡는다. 공식 Nova Carter 예제의 높이 범위는 0.1~0.62 m이다.
7. `CALCULATE`, `VISUALIZE IMAGE`를 실행한다. 공식 절차에 따라 회전 180도, ROS YAML 좌표계를 선택하고 이미지를 다시 생성한다.
8. 생성된 이미지와 **도구가 계산한 YAML 전체**를 `project-3/maps/warehouse.png`, `warehouse.yaml`로 저장한다.
9. 로봇이 남아 있는 `warehouse.usd`를 다시 연다.

```bash
cat project-3/maps/warehouse.yaml
```

YAML의 `image`는 `warehouse.png`를 가리켜야 한다. `resolution`, `origin`은 예쁜 숫자로 바꾸지 않는다. 창고 모서리 세 곳의 위치를 Stage와 RViz에서 비교해 회전과 축 방향을 확인한다. 실제 조작 순서는 [NVIDIA 5.1.0 점유 지도·Nav2 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)을 따른다.

## 4단계: 새 지도에서 다시 주행한다

Stage를 저장한 뒤 Play한다. 별도 Jazzy 터미널에서 저장소 루트로 이동해 실행한다.

```bash
ros2 launch carter_navigation carter_navigation.launch.py \
  use_sim_time:=true \
  map:="$(realpath project-3/maps/warehouse.yaml)"
```

2단계처럼 초기 위치를 지정하고 가까운 목표를 다시 보낸다. 새로운 상자가 지도와 costmap 양쪽에 나타나야 한다. 상자를 옮긴 후에는 정적 지도를 다시 만들거나, 움직이는 장애물로 취급해 실시간 costmap에 반영되는지 구분해 확인한다.

공식 파라미터가 모든 안전 기능을 켜 둔 구성이라고 가정하지 않는다. 5.1.0 태그의 `collision_monitor.FootprintApproach.min_points`는 `6000000000`으로 설정되어 있어 이 다각형 기반 충돌 정지 기능을 검증된 보호 수단으로 볼 수 없다. 동적 장애물 시험에서는 낮은 속도부터 시작하고 실제 접촉 여부를 별도로 기록한다. 이 값만 임의로 낮춘다고 정지 거리 검증이 끝나는 것도 아니다.

## 5단계: 세 목표를 자동으로 방문한다

먼저 RViz에서 각 목표를 한 번씩 수동으로 성공시킨다. 빈 공간인지, 방향까지 포함해 도달 가능한지 확인한 **자신의 지도 좌표**를 아래 형식으로 저장한다. 다음 좌표는 형식 예시이며 모든 창고에서 안전한 목표가 아니다.

```json
[
  {"x": -5.0, "y": -1.0, "yaw": 0.0},
  {"x": -5.0, "y": -3.0, "yaw": 1.5708},
  {"x": -6.0, "y": -1.0, "yaw": 3.1416}
]
```

파일 이름은 `project-3/config/goals.json`으로 한다. `x`, `y`는 m, `yaw`는 rad이다. [send_nav_goals.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/ros2/send_nav_goals.py)는 앞 목표의 **실제 action 성공 결과**를 받은 뒤 다음 목표를 보낸다. 거부·실패·시간 초과가 발생하면 나머지를 보내지 않고 결과를 저장한다.

```bash
source /opt/ros/jazzy/setup.bash
python3 examples/ros2/send_nav_goals.py project-3/config/goals.json \
  --timeout 180 \
  --output project-3/results/navigation.json
```

이 명령은 Nav2와 시뮬레이터가 이미 실행 중인 상태에서 사용한다. 목표 타임스탬프는 `/clock`을 사용하고, 시험 전체가 끝없이 멈추지 않도록 제한 시간은 실제 시각으로 잰다. 오랫동안 Pause하면 시간 초과로 종료되는 것이 의도한 동작이다. 취소가 확인되지 않았다는 메시지가 나오면 Isaac Sim을 Pause하고 확인한다.

**완료 판정:** JSON에 세 결과가 모두 있고 `succeeded`가 모두 `true`이다. 이것은 목표 도달 판정이며 충돌이 없었다는 증거와는 별개이다. 접촉 로그와 영상을 함께 기록한다.

## 6단계: 조건 하나씩 바꾸고 실패를 기록한다

| 시험 | 바꾸는 조건 | 관찰할 결과 |
|---|---|---|
| 반복 주행 | 같은 시작 위치에서 3회 | 목표별 성공, 실제 소요 시간, 도착 오차 |
| 통로 장애물 | 상자 하나 추가 | 지도·costmap 반영과 재계획 여부 |
| 명령 중단 | 명령 발행을 중단 | 실제 바퀴가 멈추기까지 걸린 시간 |
| Pause/재개 | 2초 Pause 후 Play | 오래된 명령, TF 시간 오류 유무 |
| 장면 다시 열기 | Stop 후 저장본 재열기 | 초기 위치와 센서 토픽 복구 |

센서 노이즈, 유리 재질, 다중 로봇은 이 다섯 시험을 통과한 뒤 추가한다. 시험 실패를 숨기지 말고 당시 Stage, 지도, 파라미터, 목표와 로그를 함께 보관한다.

## 자주 막히는 부분

| 증상 | 확인 순서 |
|---|---|
| `/scan`이 없다 | 원본 `/front_3d_lidar/lidar_points` → 변환 노드 → 센서 TF 순서로 확인한다. |
| `/odom`만 기다리다가 멈춘다 | Nova Carter는 `/chassis/odom`을 사용한다. 커스텀 로봇의 이름과 구분한다. |
| 지도가 반대로 보인다 | 이미지 회전과 YAML을 한 쌍으로 다시 내보낸다. |
| 목표를 받지만 움직이지 않는다 | Nav2 lifecycle, `/cmd_vel` 타입·구독자, 바퀴 제어를 확인한다. |
| 검은 영상 때문에 센서 실패로 보인다 | 공식 장면에서 일부 Hawk 카메라는 성능 때문에 꺼져 있다. 점군부터 확인한다. |
| Stop 후 TF가 계속 오래된 값을 사용한다 | 기존 목표를 취소하고 Nav2를 종료한 뒤 장면과 Nav2를 순서대로 다시 시작한다. |

이 문서와 스크립트는 실행 방법과 판정 기준을 제공한다. 실제 GPU·Isaac Sim·ROS 환경에서 생성한 결과가 없다면 프로젝트를 실행 통과로 기록하지 않는다.

## 다음 확장

차량을 바꿀 때는 [이동 로봇 프로젝트](02-custom-mobile-robot.md)의 구동·TF 실습을 먼저 끝낸다. 같은 지도를 사용하는 두 대의 로봇으로 확장할 때는 [공식 다중 로봇 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html)처럼 토픽과 TF 이름을 모두 분리한다.

## 출처

- [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [ROS 2 RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html)
- [ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)
- [Mapping](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html)
