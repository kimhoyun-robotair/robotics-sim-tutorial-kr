# ROS 2 Jazzy 연동 학습 경로

이 장에서는 Isaac Sim 5.1의 Stage를 ROS 2 Jazzy 그래프에 연결하다. 목표는 토픽 하나를 보이게 만드는 데 그치지 않고 시간, 좌표계, QoS와 제어 주기를 일관되게 설계하는 것이다.

## 최종 구성

```mermaid
flowchart LR
    subgraph SIM["Isaac Sim 5.1 · Python 3.11"]
        USD["USD + PhysX"] --> OG["Action Graph"]
        OG --> BR["ROS 2 Bridge"]
    end
    subgraph DDS["DDS domain"]
        NET["topics · services · actions"]
    end
    subgraph ROS["ROS 2 Jazzy · Python 3.12"]
        RV["RViz2"]
        NAV["Nav2"]
        MOVE["MoveIt 2"]
        APP["사용자 노드"]
    end
    BR <--> NET
    NET <--> RV
    NET <--> NAV
    NET <--> MOVE
    NET <--> APP
```

두 Python 버전이 다르더라도 서로 다른 프로세스가 DDS로 직렬화된 메시지를 교환하는 것은 정상이다. 문제는 Python 3.12용 `rclpy` 바이너리를 Isaac Sim의 Python 3.11 프로세스에 직접 import할 때 생기다. 이 경계를 학습 내내 유지하다.

## 문서 순서와 산출물

| 순서 | 문서 | 산출물 |
|---:|---|---|
| 1 | `01-bridge-and-qos` | `/clock`을 주고받는 동일 DDS domain |
| 2 | `02-time-tf-and-motion` | `map → odom → base_link → sensor` TF tree와 이동 명령 |
| 3 | `03-sensors-and-action-graph` | camera, LiDAR, IMU, joint state 토픽 |
| 4 | `04-nav2-moveit-and-sim-control` | Nav2 또는 MoveIt 2 시나리오와 자동화된 reset |
| 5 | `05-custom-messages-and-debugging` | 사용자 인터페이스의 이중 빌드와 재현 가능한 진단 기록 |

## 세 터미널을 계속 분리하다

```text
[SIM] Isaac Sim 실행과 python.sh       Python 3.11
[ROS] /opt/ros/jazzy와 외부 ROS 노드  Python 3.12
[DBG] ros2 topic/TF/QoS 진단           Python 3.12
```

`[SIM]`에 시스템 Jazzy를 무조건 source하거나, `[ROS]`에서 Isaac Sim의 `python.sh`를 사용하는 식으로 섞지 않다. 커스텀 메시지를 Isaac Sim 내부에서 import해야 할 때만 공식 Python 3.11 워크스페이스 절차를 따르다.

## 연동 전에 고정할 계약

다음 표를 프로젝트의 `ros_contract.md`에 적어 두면 대부분의 통합 오류를 조기에 찾을 수 있다.

| 항목 | 예시 | 확인 방법 |
|---|---|---|
| Domain | `ROS_DOMAIN_ID=17` | 양쪽 `printenv` |
| RMW | `rmw_fastrtps_cpp` | `echo $RMW_IMPLEMENTATION` |
| 시간 | simulation time | `/clock`, `use_sim_time` |
| 기준 좌표 | REP-103, Z-up | `view_frames`, RViz axes |
| TF 소유권 | localization이 `map→odom`, simulator가 `odom→base_link` | `/tf` publisher 수 검사 |
| 명령 토픽 | `/cmd_vel`, `geometry_msgs/msg/Twist` | `ros2 topic info -v` |
| sensor QoS | Sensor Data, Best Effort | publisher/subscriber QoS 비교 |
| reset 의미 | 동일 Stage, 시간 0, robot pose 초기화 | reset 뒤 `/clock`, pose 검사 |

## 수료 조건

- [ ] 내장 Jazzy와 외부 Jazzy의 역할을 설명하다.
- [ ] `/clock`을 기준으로 모든 ROS 노드가 simulation time을 사용하게 하다.
- [ ] TF의 각 edge에 publisher가 정확히 하나만 존재하게 하다.
- [ ] `cmd_vel`, joint command와 sensor topic의 QoS를 검사하다.
- [ ] RViz2에서 camera, LaserScan/PointCloud2, IMU와 robot model을 검증하다.
- [ ] Nav2 또는 MoveIt 2를 실행하고 정지·reset 후 다시 성공시키다.
- [ ] custom message와 custom OmniGraph node의 ABI 경계를 설명하다.
- [ ] 통합 실패를 domain, discovery, type, QoS, time, frame, rate 순으로 진단하다.

## 출처

- [Isaac Sim 5.1 — ROS 2](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/ros2_landing_page.html)
- [Isaac Sim 5.1 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1 — ROS 2 Reference Architecture](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/ros2_reference_architecture.html)
- [Isaac Sim 5.1 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
