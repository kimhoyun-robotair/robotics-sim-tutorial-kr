# ROS 2 Bridge, DDS 도메인과 QoS

이 튜토리얼에서는 Isaac Sim 5.1과 Ubuntu 24.04의 ROS 2 Jazzy를 예측 가능한 방식으로 연결한다. 표준 메시지만 쓸 때의 간단한 경로와 커스텀 인터페이스를 쓸 때의 Python 3.11 경로를 구분한다.

## 1. 어떤 실행 방식을 선택할지 결정한다

| 요구 | `[SIM]` Isaac Sim | `[ROS]` 외부 노드 |
|---|---|---|
| `std_msgs`, `geometry_msgs`, `sensor_msgs`, `nav_msgs` 등 기본 인터페이스 | 시스템 ROS를 불러오지 않고 내장 Jazzy 사용 | `/opt/ros/jazzy` 사용 |
| 사용자 정의 `.msg/.srv/.action`을 Generic OmniGraph 노드에서 사용 | Python 3.11로 빌드한 Jazzy 및 사용자 정의 워크스페이스 환경 로드 | Python 3.12 시스템 Jazzy로 같은 인터페이스를 별도 빌드 |
| Isaac Sim 내부 `rclpy` Python 노드 | Python 3.11 빌드만 import | 외부 노드는 Python 3.12 유지 가능 |

DDS가 프로세스 경계를 연결하므로 외부 노드의 Python 3.12는 문제가 아니다. 그러나 C 확장인 `rclpy`와 생성된 Python 타입 지원 라이브러리는 빌드한 Python 마이너 버전에 종속된다.

## 2. 가장 안전한 기본 실행

먼저 `[SIM]` 새 터미널에서 ROS 환경이 남아 있지 않은지 확인한다.

```bash
# [SIM]
env -i HOME="$HOME" USER="${USER:-}" \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  DISPLAY="${DISPLAY:-}" XAUTHORITY="${XAUTHORITY:-}" \
  WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
  DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
  /bin/bash --noprofile --norc
# 위 명령으로 열린 셸 안에서 다음을 실행한다.
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

cd ~/isaacsim
./isaac-sim.sh --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge
```

이 명령은 현재 사용자의 홈·화면 연결 정보만 보존하고 ROS의 `PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH`를 물려받지 않는 셸을 연다. 창이 하나 더 뜨는 방식은 아니며, 같은 터미널의 프롬프트에서 계속 입력한다. 컨테이너나 원격 GPU 환경은 해당 실행 환경의 GPU 설정도 필요하므로 공식 컨테이너 절차를 사용한다. 셸을 마칠 때는 `exit`를 입력한다. GUI에서 `Window > Extensions`를 열고 `isaacsim.ros2.bridge`가 활성화되었는지 확인한다.

별도 `[ROS]` 터미널을 준비한다.

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

printf 'distro=%s domain=%s rmw=%s python=%s\n' \
  "$ROS_DISTRO" "$ROS_DOMAIN_ID" "$RMW_IMPLEMENTATION" "$(python3 -V)"
```

Ubuntu 24.04의 시스템 Jazzy는 일반적으로 Python 3.12를 사용하고 Isaac Sim 5.1은 Python 3.11을 사용한다. 다음은 의도한 결과이다.

```bash
# [SIM] Isaac Sim Python
~/isaacsim/python.sh -c 'import sys; print(sys.version)'

# [ROS] System Python
python3 -c 'import sys; print(sys.version)'
```

## 3. 내장 Jazzy를 명시적으로 선택한다

기본 자동 선택이 실패한 경우에만 새 `[SIM]` 터미널에서 Bridge가 제공하는 Jazzy 라이브러리를 명시한다.

```bash
# [SIM]
export ISAACSIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=17
export LD_LIBRARY_PATH="${ISAACSIM_PATH}/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
"${ISAACSIM_PATH}/isaac-sim.sh"
```

이 블록을 같은 셸에서 반복 실행해 `LD_LIBRARY_PATH`를 계속 중복시키지 않는다. `~/.bashrc`에 시스템 Jazzy의 환경을 자동으로 불러오는 설정이 있다면 `[SIM]` 전용 셸에서는 비활성화하거나 깨끗한 셸을 사용한다.

## 4. `/clock`으로 기본 연결을 확인한다

토픽 목록이 비었다고 즉시 Bridge 고장으로 판단하지 않는다. 발행 노드가 없다면 목록에도 아무것도 나타나지 않을 수 있다.

Isaac Sim에서 `Window > Graph Editors > Action Graph`를 열고 `/World/ROS2Clock` 그래프를 만든다. 다음 노드를 배치한다.

- `On Playback Tick`
- `ROS 2 Context`
- `Isaac Read Simulation Time`
- `ROS 2 Publish Clock`

다음 의미로 연결한다.

```text
On Playback Tick.tick                → ROS 2 Publish Clock.execIn
ROS 2 Context.context                → ROS 2 Publish Clock.context
Isaac Read Simulation Time.simulationTime → ROS 2 Publish Clock.timeStamp
```

`ROS 2 Context`에서 **Use Domain ID Env Var**를 켜거나 도메인 ID를 `17`로 직접 넣는다. Stage를 저장한 뒤 Play한다.

```bash
# [DBG]
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 topic list
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

`rosgraph_msgs/msg/Clock` 메시지가 한 번 출력되면 참여자 탐색, 타입 지원 라이브러리와 기본 데이터 경로가 모두 동작한다.

## 5. `ROS_DOMAIN_ID`를 격리 장치로 사용한다

DDS 도메인이 다른 노드는 같은 네트워크에 있어도 서로 발견하지 않는다. 팀별로 0이 아닌 값을 정하고 `[SIM]`, `[ROS]`, Docker와 원격 머신에 동일하게 적용한다.

```bash
# [SIM], [ROS], [DBG] 모두 동일하게 한다.
export ROS_DOMAIN_ID=17
```

Action Graph의 `ROS 2 Context`가 환경 변수를 읽도록 하지 않고 값 `0`으로 고정되어 있으면 셸의 `17`과 통신하지 못한다. `ros2 topic info -v`에 발행 노드가 0개라면 이를 우선 확인한다.

## 6. QoS는 타입만큼 중요한 연동 규칙이다

ROS 2 통신 끝점은 토픽 이름과 타입이 같아도 일부 QoS 조합이 호환되지 않으면 연결되지 않는다.

| 정책 | 흔한 선택 | 사용 예 |
|---|---|---|
| Reliability | Reliable / Best Effort | 명령은 Reliable, 고율 센서는 Best Effort가 흔하다. |
| Durability | Volatile / Transient Local | 동적 센서는 Volatile, 늦게 온 구독 노드도 받아야 하는 정적 지도는 Transient Local이 흔하다. |
| History | Keep Last | 깊이와 함께 큐 크기를 정한다. |
| Depth | `1`, `5`, `10` | 최신 센서 프레임만 중요하면 작게 둔다. |
| Deadline/Lifespan | 기본값 또는 명시값 | 실시간 연동 규칙이 필요한 경우에만 양쪽을 함께 설계한다. |

Isaac Sim에서는 발행 노드와 구독 노드의 `qosProfile` 입력에 `ROS 2 QoS Profile` 노드를 연결한다. 사용자 프로필을 만들 때는 먼저 `createProfile`을 **Custom**으로 바꾼 뒤 나머지 필드를 수정한다. 5.1 알려진 문제 때문에 이 순서가 중요하다.

센서와 RViz2가 연결되지 않을 때 RViz 표시 항목의 Reliability를 **Best Effort**로 맞춘다. 실제 통신 끝점을 먼저 검사한다.

```bash
# [DBG]
ros2 topic info /front_camera/rgb/image_raw -v
ros2 topic hz /front_camera/rgb/image_raw
ros2 topic bw /front_camera/rgb/image_raw
```

CLI에서 임시 구독 노드 QoS를 바꿔 비교한다.

```bash
# [DBG]
ros2 topic echo /scan sensor_msgs/msg/LaserScan \
  --qos-reliability best_effort \
  --qos-durability volatile \
  --once
```

## 7. 여러 머신과 컨테이너의 참여자 탐색

동일 머신에서는 기본 공유 메모리/Fast DDS 구성을 우선 사용한다. 여러 머신 또는 컨테이너 네트워크를 넘으면 모든 관련 프로세스에 같은 Fast DDS XML과 도메인을 적용한다.

```bash
# [SIM], [ROS] 모두
export ROS_DOMAIN_ID=17
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
export RMW_FASTRTPS_USE_QOS_FROM_XML=1
```

`RMW_FASTRTPS_USE_QOS_FROM_XML=1`은 XML QoS를 실제 RMW가 사용하도록 할 때 필요하다. 공식 워크스페이스의 프로필을 먼저 읽고 인터페이스/IP 설정을 자신의 네트워크에 맞춘다. 호스트 네트워크 모드, UDP 멀티캐스트·유니캐스트, 방화벽, VPN과 서로 다른 서브넷은 환경 변수만으로 해결되지 않는다.

```bash
# [DBG] 양쪽 머신에서 수행하다.
ip -br addr
printenv | grep -E '^(ROS_DOMAIN_ID|RMW_IMPLEMENTATION|FASTRTPS|RMW_FASTRTPS)='
ros2 node list
```

## 8. 공식 ROS 워크스페이스를 두 용도로 빌드한다

외부 Jazzy 예제는 시스템 Python 3.12로 일반 빌드한다.

```bash
# [ROS]
cd ~/IsaacSim-ros_workspaces/jazzy_ws
source /opt/ros/jazzy/setup.bash
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --symlink-install
source install/local_setup.bash
```

커스텀 인터페이스를 Isaac Sim 내부에서 import해야 할 때는 NVIDIA가 제공한 Docker 빌드를 별도로 수행한다.

```bash
# 빌드용 터미널
cd ~/IsaacSim-ros_workspaces
./build_ros.sh -d jazzy -v 24.04

# [SIM] 새 터미널: Python 3.11 산출물만 source한다.
source ~/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash
source ~/IsaacSim-ros_workspaces/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
export ROS_DOMAIN_ID=17
~/isaacsim/isaac-sim.sh
```

사용자 정의 패키지를 추가했다면 Python 3.11 쪽과 Python 3.12 쪽에 같은 `.msg/.srv/.action` 정의가 존재해야 한다. 한쪽만 다시 빌드하면 타입 해시 또는 패키지 발견 문제가 생길 수 있다.

ROS launch로 Isaac Sim을 시작할 때 Python 3.12 설치 경로를 Isaac 프로세스에서 제외하고 Python 3.11 환경 설정 파일을 지정한다.

```bash
# [ROS]
ros2 launch isaacsim run_isaacsim.launch.py \
  exclude_install_path:="$HOME/IsaacSim-ros_workspaces/jazzy_ws/install" \
  ros_installation_path:="$HOME/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash"
```

## 9. 계층별 진단 순서

```bash
# [DBG]
ros2 daemon stop
ros2 daemon start
ros2 node list
ros2 topic list -t
ros2 topic info /clock -v
```

1. **프로세스:** Bridge 확장이 로드되었고 Timeline이 Play인지 확인한다.
2. **도메인/RMW:** 양쪽 환경 변수와 Action Graph 컨텍스트를 비교한다.
3. **참여자 탐색:** 같은 머신인지, 방화벽·컨테이너·VPN 경계가 있는지 확인한다.
4. **이름/타입:** 네임스페이스, remap과 메시지 타입을 확인한다.
5. **QoS:** `ros2 topic info -v`의 발행 측이 제공하는 정책과 구독 측이 요구하는 정책을 비교한다.
6. **주기/대역폭:** `topic hz`, `topic bw`로 과부하인지 확인한다.
7. **시간/프레임:** `/clock`, `use_sim_time`, `header.frame_id`, TF를 확인한다.

### 완료 체크포인트

- [ ] `[SIM]`은 Python 3.11, `[ROS]`는 Python 3.12임을 확인했다.
- [ ] 같은 `ROS_DOMAIN_ID`에서 `/clock` 한 메시지를 받았다.
- [ ] 센서 토픽의 실제 QoS를 `ros2 topic info -v`로 기록했다.
- [ ] 사용자 정의 인터페이스가 필요할 때만 Python 3.11 워크스페이스를 빌드했다.
- [ ] 여러 머신에서는 Fast DDS XML과 방화벽까지 점검했다.

## 출처

- [Isaac Sim 5.1 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1 — ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)
- [Isaac Sim 5.1 — ROS 2 Quality of Service](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)
- [Isaac Sim 5.1 — Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)
- [Isaac Sim 5.1 — ROS 2 Launch](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html)
- [Isaac Sim 5.1 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
- [Isaac Sim 5.1 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
