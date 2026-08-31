# 프로젝트 3: 커스텀 창고의 RTX LiDAR 자율주행

## 목표

모듈형 warehouse environment를 USD로 만들고 커스텀 이동 로봇에 RTX LiDAR를 장착하다. ROS 2로 point cloud/scan, TF, odometry를 publish하고 map을 생성한 뒤 Nav2 goal을 수행하다.

## scene 요구사항

- 통로 폭이 다른 aisle 세 개와 dead end, glass/metal/cardboard material을 포함하다.
- visual mesh와 navigation/collision geometry를 분리하다.
- 고정 obstacle과 움직이는 obstacle을 각각 포함하다.
- environment layer와 robot/session layer를 분리하다.

## 1단계: environment를 검증하다

Content Browser에서 asset을 reference로 배치하고 모든 path를 project 기준 상대 path로 정리하다. static collider가 triangle mesh를 무분별하게 사용하지 않게 하다. Physics Debug Window 또는 `Visibility Menu(눈 아이콘) > Show by Type > Physics > Simulation Data Visualizer`로 collision을 확인하다.

occupancy map을 생성할 높이 구간을 정하고 origin·resolution을 기록하다. map image만 남기지 말고 YAML의 resolution과 origin이 USD meter 좌표와 일치하는지 landmark 세 점으로 확인하다.

## 2단계: RTX LiDAR를 장착하다

sensor prim을 `base_link` 아래 고정 transform으로 두고 configuration profile을 선택하다. render product와 ROS 2 RTX LiDAR helper를 연결하다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic hz /robot1/scan
ros2 topic echo /robot1/scan --once
ros2 run tf2_ros tf2_echo robot1/base_link robot1/lidar_link
```

range minimum/maximum, horizontal FOV, rotation/firing rate, output frame, QoS를 manifest에 남기다. point cloud와 LaserScan을 동시에 만들 때 중복 계산·publish cost를 측정하다.

## 3단계: Nav2를 연결하다

```bash
source /opt/ros/jazzy/setup.bash
source project-3/ros2_ws/install/setup.bash
ros2 launch project3_nav bringup.launch.py \
  use_sim_time:=true \
  namespace:=robot1 \
  map:=project-3/maps/warehouse.yaml
```

goal 전송 전 확인하다.

```bash
ros2 param get /robot1/controller_server use_sim_time
ros2 topic echo /clock --once
ros2 run tf2_tools view_frames
```

초기 pose와 goal을 보내는 test node는 wall time 대신 ROS clock을 사용하다. simulation pause 후 resume할 때 timeout 처리도 확인하다.

## 시험 시나리오

| 시나리오 | 측정값 | 성공 기준 예시 |
| --- | --- | --- |
| 직선 통로 | path length, lateral error | collision 없이 goal 도달하다. |
| 좁은 회전 | clearance, recovery count | footprint를 침범하지 않다. |
| dead end | replanning time | 제한 시간 안에 탈출하다. |
| 동적 obstacle | stop distance | contact 없이 정지·재계획하다. |
| sensor noise | success rate | seed 20개 중 목표 비율을 넘다. |

기준 숫자는 robot 속도와 크기에 맞게 사용자가 사전에 정하다. 성공한 run만 골라 보고하지 않고 모든 seed를 기록하다.

## 완료 조건

- 세 개 goal을 순차 수행하는 launch/test가 한 명령으로 실행되다.
- map↔odom↔base_link↔lidar frame이 올바르게 연결되다.
- real-time factor, LiDAR publish rate, CPU/GPU memory를 함께 보고하다.
- 한 가지 failure를 재현하고 parameter 변경 전후를 비교하다.

## 확장 과제

두 robot을 namespace로 분리해 같은 warehouse에서 navigation하다. Block World Generator 또는 procedural scene variant를 사용해 layout을 바꾸고 regression suite를 실행하다.

## 출처

- [RTX Lidar Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_lidar.html)
- [ROS 2 RTX Lidar Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtx_lidar.html)
- [ROS 2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_navigation.html)
- [Multiple Robot ROS2 Navigation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_multi_navigation.html)
- [Mapping](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html)
