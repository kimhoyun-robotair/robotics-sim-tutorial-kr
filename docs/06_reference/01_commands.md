# 자주 쓰는 명령어

이 페이지의 Gazebo 명령은 Harmonic의 `gz` CLI, ROS 명령은 Jazzy 기준이다. 먼저 두 환경을 source한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

## Gazebo 실행과 파일 검사

| 명령 | 설명 |
| --- | --- |
| `gz --commands` | 설치된 Gazebo Tools 하위 명령을 나열한다. |
| `gz sim <world.sdf>` | GUI client와 simulation server를 실행한다. |
| `gz sim -s <world.sdf>` | GUI 없이 server만 실행한다. |
| `gz sim -s -r <world.sdf>` | server-only로 시작하고 즉시 simulation을 진행한다. |
| `gz sim -s -r --iterations 1000 <world.sdf>` | 정해진 update 수만 실행하고 종료한다. |
| `gz sdf -k <file.sdf>` | SDF 문법과 의미를 검사한다. |
| `gz sdf -p <file.sdf>` | include와 기본값이 반영된 SDF를 출력한다. |

world를 server-only로 실행하는 기본 형태는 다음과 같다.

```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PWD/install/tutorial_bot_plugins/lib"
export GZ_PARTITION="tutorial_manual_$$"
gz sim -s -r install/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf
```

## Gazebo Transport

| 명령 | 설명 |
| --- | --- |
| `gz topic -l` | 현재 partition에서 발견한 topic을 나열한다. |
| `gz topic -i -t <topic>` | topic의 publisher와 메시지 타입을 확인한다. |
| `gz topic -e -t <topic>` | 메시지를 계속 출력한다. |
| `gz service -l` | 발견한 service를 나열한다. |
| `gz service -i -s <service>` | request와 response 타입을 확인한다. |

```bash
gz topic -i -t /tutorial_bot/diagnostics/distance
gz topic -e --json-output -t /tutorial_bot/diagnostics/distance

gz topic -t /tutorial_bot/diagnostics/enable \
  -m gz.msgs.Boolean -p 'data: false'

gz service -s /tutorial_bot/diagnostics/reset \
  --reqtype gz.msgs.Empty --reptype gz.msgs.Boolean \
  --timeout 1000 --req ''
```

`gz topic -l` 결과가 터미널마다 다르면 `GZ_PARTITION` 값이 같은지 먼저 확인한다.

## ROS 2 graph와 메시지

| 명령 | 설명 |
| --- | --- |
| `ros2 pkg list` | source된 ROS 2 package를 나열한다. |
| `ros2 node list` | ROS graph의 node를 나열한다. |
| `ros2 topic list -t` | ROS topic과 타입을 함께 나열한다. |
| `ros2 topic info -v <topic>` | publisher, subscriber, QoS를 확인한다. |
| `ros2 topic echo <topic>` | ROS 메시지를 출력한다. |
| `ros2 service list -t` | ROS service와 타입을 나열한다. |
| `ros2 run tf2_tools view_frames` | 현재 TF tree를 PDF와 YAML로 기록한다. |

```bash
ros2 topic list -t | sort
ros2 topic info -v /odom
ros2 topic hz /scan
ros2 topic echo /imu --once
```

## ros_gz_bridge

bridge 문자열의 기본 형태는 `/topic@ROS_TYPE@GZ_TYPE`이다. `[`는 Gazebo→ROS, `]`는 ROS→Gazebo 단방향을 나타낸다.

```bash
# Gazebo distance를 ROS 2로 전달한다.
ros2 run ros_gz_bridge parameter_bridge \
  '/tutorial_bot/diagnostics/distance@std_msgs/msg/Float64[gz.msgs.Double'

# ROS 2 cmd_vel을 Gazebo로 전달한다.
ros2 run ros_gz_bridge parameter_bridge \
  '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist'
```

여러 mapping을 반복해서 사용할 때에는 YAML 설정 파일과 launch를 사용한다.

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:="$(ros2 pkg prefix tutorial_bot_bringup)/share/tutorial_bot_bringup/config/bridge.yaml"
```

## build와 test

```bash
cd examples/ros2_ws
colcon build --symlink-install \
  --packages-select tutorial_bot_plugins tutorial_bot_gazebo
source install/setup.bash

colcon test --packages-select tutorial_bot_plugins
colcon test-result --verbose
```

build 문제를 좁힐 때에는 한 package만 선택하고 CMake 출력을 직접 보이게 한다.

```bash
colcon build \
  --packages-select tutorial_bot_plugins \
  --event-handlers console_direct+
```

## TF와 RViz 확인

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_monitor odom base_link
rviz2 -d "$(ros2 pkg prefix tutorial_bot_bringup)/share/tutorial_bot_bringup/rviz/tutorial_bot.rviz"
```

RViz에서 데이터가 보이지 않으면 topic 존재 여부, 메시지 타입, QoS, `Fixed Frame`, TF 연결 순서로 확인한다.
