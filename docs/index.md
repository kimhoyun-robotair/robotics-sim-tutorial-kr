# ROS 2 Humble × Gazebo Classic 11

이 과정의 목표는 “Gazebo 창에 로봇이 보인다”보다 한 단계 더 구체적입니다. 학습을 마치면 직접 만든 URDF/Xacro 로봇이 물리적으로 안정되게 움직이고, ROS 2 토픽과 TF가 연결되며, 센서 데이터와 wheel odometry 궤적을 RViz에서 스스로 검증할 수 있어야 합니다.

## 완성할 시스템

```mermaid
flowchart TB
  K["keyboard teleop"] -->|/cmd_vel| G["Gazebo drive plugin"]
  G -->|"/odom + odom→base_footprint"| R["ROS 2 / RViz"]
  U["URDF + Xacro"] --> S["spawn_entity"]
  S --> G
  Z["Gazebo sensors"] -->|"Image · IMU · Scan · PointCloud2"| R
  P["custom ModelPlugin"] -->|/ground_truth_path| R
```

## 과정에서 지키는 기준

- 모든 명령은 Ubuntu 22.04와 ROS 2 Humble을 기준으로 설명합니다.
- `gazebo`라는 명령을 쓰는 **Gazebo Classic 11**을 사용합니다. `gz sim`을 쓰는 새 Gazebo와 플러그인·launch 형식이 다릅니다.
- 모델에는 `visual`뿐 아니라 `collision`, `inertial`, joint limit와 마찰을 함께 정의합니다.
- “토픽이 존재한다”와 “RViz에서 올바른 frame으로 보인다”를 구분해 검증합니다.
- Gazebo의 simulation time을 사용하는 모든 ROS 노드에 `use_sim_time:=true`를 적용합니다.
- wheel odometry와 ground truth를 서로 다른 값으로 취급합니다. 전자는 바퀴 운동학 추정, 후자는 시뮬레이터가 아는 실제 pose입니다.

## 권장 학습 순서

| 단계 | 문서 | 완료 기준 |
| --- | --- | --- |
| 1 | [환경 구성](01_setup.md) | Gazebo 11과 ROS 패키지 버전을 확인한다 |
| 2 | [URDF·Xacro·SDF](02_urdf_xacro_sdf.md) | 세 형식의 책임과 변환 경계를 설명한다 |
| 3 | [2륜 로봇](03_diffbot.md) | 사각형으로 주행하고 `/wheel_odom_path`를 본다 |
| 4 | [4륜 rover](04_rover.md) | skid와 Ackermann 궤적 차이를 비교한다 |
| 5 | [센서](05_sensors.md) | 각 메시지를 RViz에서 올바른 frame으로 본다 |
| 6 | [TF와 RViz](06_tf_rviz.md) | TF tree와 동적/정적 변환의 출처를 찾는다 |
| 7 | [커스텀 플러그인](07_custom_plugin.md) | 직접 빌드한 `.so`가 Path를 publish한다 |
| 8 | [디버깅](08_debugging.md) | 시간·QoS·TF·물리 문제를 분리 진단한다 |

각 장의 명령은 저장소를 `Humble` 브랜치로 clone하고 `ros2_ws`를 빌드했다는 전제로 작성되어 있습니다. 처음이라면 환경 구성부터 순서대로 진행하세요.

!!! warning "Gazebo Classic의 수명"
    Gazebo Classic은 2025년 1월에 공식 지원이 종료되었습니다. 이 튜토리얼은 ROS 2 Humble 기반의 기존 시스템을 재현하고 유지보수하는 데 초점을 둡니다. 새 제품을 시작한다면 최신 ROS 2와 새 Gazebo의 지원 조합도 검토하세요.
