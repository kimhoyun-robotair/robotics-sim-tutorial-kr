# 파이널 프로젝트: 센서로 주변을 보고 목적지까지 이동하는 Rover

앞에서 만든 월드, 로봇 모델, ROS 토픽, 센서와 TF를 하나의 프로젝트로 연결합니다.
처음에는 키보드로 로봇을 움직이고, 센서가 올바른 위치에 보이는지 확인한 뒤,
지도를 만들고 Nav2로 목적지까지 이동시킵니다.

이 프로젝트는 이전에 `kimhoyun-robotair` 가 개발한 **Gazebo_Harmonic_Rover** 리포지터리의
`simple_rover`, `f1tenth_sim`, `nav2_programming`을 **Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic**에 맞게 이식한 코드입니다.
완성된 패키지는 이 저장소의 `examples/ros2_ws/src/`에 있으므로 원본 저장소를 따로 복사할 필요가 없습니다.

## 진행 순서

| 순서 | 실습 | 다음 단계로 넘어가는 기준 |
|---|---|---|
| 1 | [빌드하고 키보드로 움직이기](01_build-and-drive.md) | 로봇이 움직이고 `/odom`이 바뀐다 |
| 2 | [센서와 RViz 확인하기](02_sensors-and-rviz.md) | 라이다와 점군이 월드의 벽 위치에 맞는다 |
| 3 | [지도 작성과 자율주행](03_mapping-and-navigation.md) | 지도를 저장하고 재실행한 뒤 목표 위치까지 이동한다 |
| 4 | [F1Tenth 차량으로 확장하기](04_f1tenth.md) | 전진하면서 조향하고 차동구동과의 차이를 설명한다 |
| 5 | 포팅 내용과 검증 범위 | 원본에서 무엇을 바꿨는지 확인하고 결과를 기록한다 |

## 만들게 될 시스템

Gazebo는 바퀴의 물리 운동과 센서 데이터를 계산합니다. `ros_gz_bridge`는 Gazebo 토픽과 ROS 토픽을 연결합니다.
`robot_state_publisher`는 URDF와 바퀴 관절 상태를 읽어 로봇 내부의 TF를 발행하고,
Gazebo 구동 플러그인은 `odom → base_link`를 발행합니다. 지도 작성 중에는 SLAM이,
저장한 지도로 주행할 때는 AMCL이 `map → odom`을 담당합니다.

| 패키지 | 역할 | 기본 실행 명령 |
|---|---|---|
| `simple_rover` | 바퀴 4개 차동구동, 2D 라이다, RGB-D 카메라, IMU, SLAM/Nav2 설정 | `ros2 launch simple_rover spawn_robot.launch.py` |
| `f1tenth_sim` | 메쉬 기반 Ackermann 조향 차량, 2D 라이다, IMU | `ros2 launch f1tenth_sim spawn_robot.launch.py` |
| `nav2_programming` | 단일 목표, 여러 목표, 경유점 순회 예제 | `ros2 run nav2_programming navigate_to_pose` |

실습은 **한 번에 로봇 하나**를 실행하는 구성입니다. 두 시뮬레이션은 `/cmd_vel`, `/odom`, `/tf` 등 같은 이름을 사용합니다.
차량을 바꿀 때는 먼저 앞서 실행한 launch를 `Ctrl+C`로 종료하세요.

## 제출할 결과

1. Gazebo와 RViz에서 같은 장애물이 같은 위치에 보이는 화면.
2. `/scan`, `/camera/points`, `/imu`, `/odom`의 토픽 타입과 `frame_id` 확인 결과.
3. 직접 저장한 지도 YAML/PGM과 Nav2 목표 도달 결과.
4. 센서 위치 또는 주행 속도를 하나 바꾼 뒤 달라진 결과와 이유.
5. 검증 기록 양식에 따른 실행 환경과 성공/실패 내역.

코드의 정적 검사와 실제 물리·렌더링 검사는 구분합니다. 정적 검사가 통과해도 GPU,
드라이버와 설치된 ROS/Gazebo 패치 버전에 따른 실행 확인은 필요합니다.
