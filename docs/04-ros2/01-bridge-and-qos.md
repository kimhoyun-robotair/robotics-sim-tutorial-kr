# ROS 2 Bridge, DDS domain과 QoS

이 튜토리얼에서는 Isaac Sim 5.1과 Ubuntu 24.04의 ROS 2 Jazzy를 예측 가능한 방식으로 연결하다. 표준 메시지만 쓸 때의 간단한 경로와 커스텀 인터페이스를 쓸 때의 Python 3.11 경로를 구분하다.

## 1. 어떤 실행 방식을 선택할지 결정하다

| 요구 | `[SIM]` Isaac Sim | `[ROS]` 외부 노드 |
|---|---|---|
| `std_msgs`, `geometry_msgs`, `sensor_msgs`, `nav_msgs` 등 기본 인터페이스 | 시스템 ROS를 source하지 않고 내장 Jazzy 사용 | `/opt/ros/jazzy` 사용 |
| custom `.msg/.srv/.action`을 generic OmniGraph node에서 사용 | Python 3.11로 빌드한 Jazzy 및 custom workspace source | Python 3.12 시스템 Jazzy로 같은 인터페이스를 별도 빌드 |
| Isaac Sim 내부 `rclpy` Python node | Python 3.11 빌드만 import | 외부 노드는 Python 3.12 유지 가능 |

DDS가 프로세스 경계를 연결하므로 외부 노드의 Python 3.12는 문제가 아니다. 그러나 C extension인 `rclpy`와 생성된 Python type support는 빌드한 Python minor version에 종속되다.

## 2. 가장 안전한 기본 실행

먼저 `[SIM]` 새 터미널에서 ROS 환경이 남아 있지 않은지 확인하다.

```bash
# [SIM]
unset ROS_DISTRO AMENT_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

cd ~/isaacsim
./isaac-sim.sh --/isaac/startup/ros_bridge_extension=isaacsim.ros2.bridge
```

`unset`은 이 전용 터미널의 혼합 환경을 피하려는 예시이다. 사용자의 다른 shell 설정 파일을 수정하지 않다. GUI에서 `Window > Extensions`를 열고 `isaacsim.ros2.bridge`가 활성화되었는지 확인하다.

별도 `[ROS]` 터미널을 준비하다.

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

printf 'distro=%s domain=%s rmw=%s python=%s\n' \
  "$ROS_DISTRO" "$ROS_DOMAIN_ID" "$RMW_IMPLEMENTATION" "$(python3 -V)"
```

Ubuntu 24.04의 시스템 Jazzy는 일반적으로 Python 3.12를 사용하고 Isaac Sim 5.1은 Python 3.11을 사용하다. 다음은 의도한 결과이다.

```bash
# [SIM] Isaac Sim Python
~/isaacsim/python.sh -c 'import sys; print(sys.version)'

# [ROS] System Python
python3 -c 'import sys; print(sys.version)'
```

## 3. 내장 Jazzy를 명시적으로 선택하다

기본 자동 선택이 실패한 경우에만 새 `[SIM]` 터미널에서 bridge가 제공하는 Jazzy 라이브러리를 명시하다.

```bash
# [SIM]
export ISAACSIM_PATH="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=17
export LD_LIBRARY_PATH="${ISAACSIM_PATH}/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
"${ISAACSIM_PATH}/isaac-sim.sh"
```

이 블록을 같은 shell에서 반복 실행해 `LD_LIBRARY_PATH`를 계속 중복시키지 않다. `~/.bashrc`에 시스템 Jazzy의 자동 source가 있다면 `[SIM]` 전용 shell에서는 비활성화하거나 깨끗한 shell을 사용하다.

## 4. `/clock`으로 최소 연결을 검증하다

토픽 목록이 비었다고 즉시 bridge 고장으로 판단하지 않다. publisher가 없다면 목록에도 아무것도 나타나지 않을 수 있다.

Isaac Sim에서 `Window > Graph Editors > Action Graph`를 열고 `/World/ROS2Clock` 그래프를 만들다. 다음 노드를 배치하다.

- `On Playback Tick`
- `ROS 2 Context`
- `Isaac Read Simulation Time`
- `ROS 2 Publish Clock`

다음 의미로 연결하다.

```text
On Playback Tick.tick                → ROS 2 Publish Clock.execIn
ROS 2 Context.context                → ROS 2 Publish Clock.context
Isaac Read Simulation Time.time      → ROS 2 Publish Clock.timeStamp
```

`ROS 2 Context`에서 **Use Domain ID Env Var**를 켜거나 domain ID를 `17`로 직접 넣다. Stage를 저장한 뒤 Play하다.

```bash
# [DBG]
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=17
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 topic list
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

`rosgraph_msgs/msg/Clock` 메시지가 한 번 출력되면 discovery, type support와 기본 데이터 경로가 모두 동작하다.

## 5. `ROS_DOMAIN_ID`를 격리 장치로 사용하다

DDS domain이 다른 노드는 같은 네트워크에 있어도 서로 발견하지 않다. 팀별로 0이 아닌 값을 정하고 `[SIM]`, `[ROS]`, Docker와 원격 머신에 동일하게 적용하다.

```bash
# [SIM], [ROS], [DBG] 모두 동일하게 하다.
export ROS_DOMAIN_ID=17
```

Action Graph의 `ROS 2 Context`가 환경 변수를 읽도록 하지 않고 값 `0`으로 고정되어 있으면 shell의 `17`과 통신하지 못하다. `ros2 topic info -v`에 publisher가 0개라면 이를 우선 확인하다.

## 6. QoS는 타입만큼 중요한 계약이다

ROS 2 endpoint는 topic 이름과 type이 같아도 일부 QoS 조합이 호환되지 않으면 연결되지 않다.

| 정책 | 흔한 선택 | 사용 예 |
|---|---|---|
| Reliability | Reliable / Best Effort | command는 Reliable, 고율 sensor는 Best Effort가 흔하다. |
| Durability | Volatile / Transient Local | 동적 sensor는 Volatile, 늦게 온 subscriber도 받아야 하는 정적 map은 Transient Local이 흔하다. |
| History | Keep Last | depth와 함께 queue size를 정하다. |
| Depth | `1`, `5`, `10` | 최신 sensor frame만 중요하면 작게 두다. |
| Deadline/Lifespan | 기본값 또는 명시값 | 실시간 계약이 필요한 경우에만 양쪽을 함께 설계하다. |

Isaac Sim에서는 publisher/subscriber node의 `qosProfile` 입력에 `ROS 2 QoS Profile` node를 연결하다. 사용자 프로필을 만들 때는 먼저 `createProfile`을 **Custom**으로 바꾼 뒤 나머지 필드를 수정하다. 5.1 known issue 때문에 이 순서가 중요하다.

센서와 RViz2가 연결되지 않을 때 RViz display의 Reliability를 **Best Effort**로 맞추다. 실제 endpoint를 먼저 검사하다.

```bash
# [DBG]
ros2 topic info /front_camera/rgb/image_raw -v
ros2 topic hz /front_camera/rgb/image_raw
ros2 topic bw /front_camera/rgb/image_raw
```

CLI에서 임시 subscriber QoS를 바꿔 비교하다.

```bash
# [DBG]
ros2 topic echo /scan sensor_msgs/msg/LaserScan \
  --qos-reliability best_effort \
  --qos-durability volatile \
  --once
```

## 7. 여러 머신과 컨테이너의 discovery

동일 머신에서는 기본 shared-memory/Fast DDS 구성을 우선 사용하다. 여러 머신 또는 container network를 넘으면 모든 관련 프로세스에 같은 Fast DDS XML과 domain을 적용하다.

```bash
# [SIM], [ROS] 모두
export ROS_DOMAIN_ID=17
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
export RMW_FASTRTPS_USE_QOS_FROM_XML=1
```

`RMW_FASTRTPS_USE_QOS_FROM_XML=1`은 XML QoS를 실제 RMW가 사용하도록 할 때 필요하다. 공식 workspace의 프로필을 먼저 읽고 인터페이스/IP 설정을 자신의 네트워크에 맞추다. host networking, UDP multicast/unicast, 방화벽, VPN과 서로 다른 subnet은 환경 변수만으로 해결되지 않다.

```bash
# [DBG] 양쪽 머신에서 수행하다.
ip -br addr
printenv | grep -E '^(ROS_DOMAIN_ID|RMW_IMPLEMENTATION|FASTRTPS|RMW_FASTRTPS)='
ros2 node list
```

## 8. 공식 ROS workspace를 두 용도로 빌드하다

외부 Jazzy 예제는 시스템 Python 3.12로 일반 빌드하다.

```bash
# [ROS]
cd ~/IsaacSim-ros_workspaces/jazzy_ws
source /opt/ros/jazzy/setup.bash
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --symlink-install
source install/local_setup.bash
```

커스텀 인터페이스를 Isaac Sim 내부에서 import해야 할 때는 NVIDIA가 제공한 Docker build를 별도로 수행하다.

```bash
# 빌드용 터미널
cd ~/IsaacSim-ros_workspaces
./build_ros.sh -d jazzy -v 24.04

# [SIM] 새 터미널: Python 3.11 산출물만 source하다.
source ~/IsaacSim-ros_workspaces/build_ws/jazzy/jazzy_ws/install/local_setup.bash
source ~/IsaacSim-ros_workspaces/build_ws/jazzy/isaac_sim_ros_ws/install/local_setup.bash
export ROS_DOMAIN_ID=17
~/isaacsim/isaac-sim.sh
```

custom package를 추가했다면 Python 3.11 쪽과 Python 3.12 쪽에 같은 `.msg/.srv/.action` 정의가 존재해야 하다. 한쪽만 다시 빌드하면 type hash 또는 package 발견 문제가 생길 수 있다.

ROS launch로 Isaac Sim을 시작할 때 Python 3.12 install 경로를 Isaac 프로세스에서 제외하고 Python 3.11 setup을 지정하다.

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

1. **프로세스:** bridge extension이 로드되었고 Timeline이 Play인지 확인하다.
2. **domain/RMW:** 양쪽 환경 변수와 Action Graph context를 비교하다.
3. **discovery:** 같은 머신인지, 방화벽·container·VPN 경계가 있는지 확인하다.
4. **이름/type:** namespace, remap과 message type을 확인하다.
5. **QoS:** `ros2 topic info -v`의 offered/requested 정책을 비교하다.
6. **rate/bandwidth:** `topic hz`, `topic bw`로 과부하인지 확인하다.
7. **time/frame:** `/clock`, `use_sim_time`, `header.frame_id`, TF를 확인하다.

### 완료 체크포인트

- [ ] `[SIM]`은 Python 3.11, `[ROS]`는 Python 3.12임을 확인했다.
- [ ] 같은 `ROS_DOMAIN_ID`에서 `/clock` 한 메시지를 받았다.
- [ ] sensor topic의 실제 QoS를 `ros2 topic info -v`로 기록했다.
- [ ] custom interface가 필요할 때만 Python 3.11 workspace를 빌드했다.
- [ ] 여러 머신에서는 Fast DDS XML과 방화벽까지 점검했다.

## 출처

- [Isaac Sim 5.1 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1 — ROS 2 Clock](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_clock.html)
- [Isaac Sim 5.1 — ROS 2 Quality of Service](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)
- [Isaac Sim 5.1 — Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)
- [Isaac Sim 5.1 — ROS 2 Launch](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_launch.html)
- [Isaac Sim 5.1 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
- [Isaac Sim 5.1 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
