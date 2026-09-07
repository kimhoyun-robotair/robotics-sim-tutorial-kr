# 자주 쓰는 명령어

Gazebo 명령은 Harmonic, ROS 2 명령은 Jazzy 기준이다. 이 페이지는 필요한 명령을 골라 쓰는 참고 자료다. 서버·브리지·토픽 출력처럼 계속 실행되는 명령은 각각 별도 터미널에서 실행하고 `Ctrl+C`로 종료한다.

## 공통 준비

[설치와 빌드](../02_getting-started/02_installation-jazzy.md)를 마친 뒤 **저장소 최상위**에서 시작한다. 새 터미널을 열 때마다 환경을 다시 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

서로 통신할 Gazebo 터미널에서는 같은 `GZ_PARTITION`을 사용한다. 값을 지정하지 않아도 기본값으로 통신할 수 있지만, 아래 고급 예제를 따라 할 때는 모든 터미널에 같은 값을 넣는다.

```bash
export GZ_PARTITION=tutorial_bot_manual
```

## Gazebo 실행과 파일 검사

| 명령 | 설명 |
| --- | --- |
| `gz --commands` | 설치된 Gazebo 하위 명령을 나열한다. |
| `gz sim <world.sdf>` | GUI와 시뮬레이션 서버를 일시정지 상태로 시작한다. |
| `gz sim -r <world.sdf>` | GUI와 서버를 시작하고 시뮬레이션을 재생한다. |
| `gz sim -s <world.sdf>` | GUI 없이 서버만 시작한다. |
| `gz sim -s -r --iterations 1000 <world.sdf>` | 서버에서 1,000회 계산한 뒤 종료한다. |
| `gz sdf -k <file.sdf>` | SDF 문법과 구조를 검사한다. |
| `gz sdf -p <file.sdf>` | 읽어 들인 SDF를 출력한다. URDF 변환 결과를 확인할 때도 쓴다. |

`<world.sdf>`와 `<file.sdf>`는 실제 경로로 바꾼다. 예를 들어 다음 명령은 저장소의 첫 월드를 실행한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

고급 진단 플러그인을 빌드했다면 설치된 월드를 서버만 실행할 수도 있다. `source`가 플러그인 경로를 설정하므로 현재 디렉터리에 맞춰 검색 경로를 덮어쓸 필요가 없다.

```bash
world="$(ros2 pkg prefix tutorial_bot_gazebo)/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim -s -r "$world"
```

## Gazebo Transport

| 명령 | 설명 |
| --- | --- |
| `gz topic -l` | 현재 통신 그룹의 토픽을 나열한다. |
| `gz topic -i -t <topic>` | 토픽의 발행자와 메시지 타입을 확인한다. |
| `gz topic -e -t <topic>` | 메시지를 계속 출력한다. |
| `gz service -l` | 발견한 서비스를 나열한다. |
| `gz service -i -s <service>` | 요청과 응답 타입을 확인한다. |

고급 진단 월드가 실행 중일 때 아래 명령을 하나씩 사용한다.

```bash
gz topic -i -t /tutorial_bot/diagnostics/distance
gz topic -e --json-output -t /tutorial_bot/diagnostics/distance
```

두 번째 명령의 출력을 `Ctrl+C`로 끝낸 뒤 다음 명령을 실행한다. `--timeout 1000`의 단위는 밀리초다.

```bash
gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: false'

gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

초기화 응답은 `data: true`여야 한다. 거리 0은 Protobuf 기본값 생략 때문에 JSON에서 `{}`로 출력될 수 있다. 토픽 목록이 터미널마다 다르면 `echo "$GZ_PARTITION"`으로 통신 그룹 이름부터 비교한다.

## ROS 2 노드와 메시지

| 명령 | 설명 |
| --- | --- |
| `ros2 pkg list` | 환경에 등록된 패키지를 나열한다. |
| `ros2 node list` | 실행 중인 ROS 노드를 나열한다. |
| `ros2 topic list -t` | 토픽과 메시지 타입을 함께 나열한다. |
| `ros2 topic info -v <topic>` | 발행자·구독자 수와 QoS를 확인한다. |
| `ros2 topic echo <topic> --once` | 메시지를 한 번 받은 뒤 종료한다. |
| `ros2 service list -t` | 서비스와 타입을 나열한다. |
| `ros2 run tf2_tools view_frames` | TF 연결을 PDF와 YAML로 저장한다. |

센서 데이터를 받을 때는 발행자의 QoS에 맞춘다. 다음 명령은 최신 센서 데이터를 우선하는 `best_effort` 정책으로 한 번 수신한다.

```bash
ros2 topic info -v /scan
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 topic echo /imu --once --qos-reliability best_effort
```

`ros2 topic hz /scan`은 수신 빈도를 계속 출력한다. 메시지가 오지 않으면 토픽 이름·타입·QoS와 시뮬레이션 재생 상태를 확인한다.

## ROS 2와 Gazebo 연결하기

브리지 문자열의 기본 형태는 `/topic@ROS_TYPE@GZ_TYPE`이다. 두 번째 `@`를 `[`로 바꾸면 Gazebo → ROS 2, `]`로 바꾸면 ROS 2 → Gazebo 단방향이 된다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  '/tutorial_bot/diagnostics/distance@std_msgs/msg/Float64[gz.msgs.Double'
```

이 명령은 계속 실행된다. 별도 터미널에서 `ros2 topic echo /tutorial_bot/diagnostics/distance --once`로 수신을 확인한다.

`tutorial_bot`은 ROS의 `/cmd_vel`과 Gazebo의 `/model/tutorial_bot/cmd_vel`처럼 양쪽 토픽 이름이 다르다. 이 경우에는 저장소의 YAML 설정을 사용한다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$(ros2 pkg prefix tutorial_bot_bringup)/share/tutorial_bot_bringup/config/bridge.yaml"
```

통합 실행 파일이 이미 브리지를 시작했다면 같은 설정의 브리지를 추가로 실행하지 않는다. 이름·방향을 직접 설정하는 방법은 [브리지 YAML](../04_intermediate/05-bridge-yaml.md)을 참고한다.

## 빌드와 테스트

저장소 최상위에서 시작한다. `--packages-up-to`는 대상 패키지와 같은 작업 공간의 의존 패키지를 함께 빌드한다.

```bash
cd examples/ros2_ws
colcon build --symlink-install \
  --packages-up-to tutorial_bot_plugins tutorial_bot_gazebo \
  --cmake-args -DBUILD_TESTING=ON
source install/setup.bash

colcon test --packages-select tutorial_bot_plugins
colcon test-result --verbose
cd ../..
```

빌드 오류를 자세히 보려면 같은 작업 공간에서 `--event-handlers console_direct+`를 추가한다. 테스트 성공 여부는 `colcon test-result`까지 확인한다.

## TF와 RViz 확인

먼저 통합 시뮬레이션을 실행한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  world:=training gui:=true rviz:=true nav2:=false
```

별도 터미널에서 TF를 확인한다. 두 명령은 각각 계속 실행되므로 하나씩 실행하고 `Ctrl+C`로 끝낸다.

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

```bash
ros2 run tf2_ros tf2_echo base_link lidar_link
```

| RViz 증상 | 확인할 항목 |
| --- | --- |
| 로봇과 센서가 모두 안 보임 | `Fixed Frame=odom`, `/clock`, `use_sim_time`, `odom → base_link` TF |
| LiDAR가 안 보임 | `/scan`의 `header.frame_id`, 해당 TF, LaserScan의 `Best Effort` |
| 카메라 점군이 옆으로 돌아감 | 센서의 광학 좌표계, `header.frame_id`, `base_link → camera_optical_frame` TF |
| 로봇 바퀴만 누락됨 | `/joint_states`, URDF 관절 이름, `robot_state_publisher` |
| Nav2를 끈 상태에서 Map 경고 | `/map` 발행자가 없는 단계인지 확인하고 Map 표시를 끈다. |

센서가 토픽에 나타나는 것만으로 렌더링이 올바르다고 판단하지 않는다. [TF·RViz](../04_intermediate/06-tf-rviz.md)와 [센서 심화](../04_intermediate/08-advanced-sensors.md)에서 좌표축, 실제 장애물 위치, 영상·점군의 방향을 함께 확인한다.

## 공식 참고 자료

- [ros_gz_bridge Jazzy: 토픽 변환과 QoS](https://docs.ros.org/en/jazzy/p/ros_gz_bridge/)
- [Gazebo Harmonic과 ROS 2 설치 조합](https://gazebosim.org/docs/harmonic/ros_installation/)
