# 용어

## 모델과 기술 형식

| 용어 | 설명 | 작은 예 |
| --- | --- | --- |
| URDF | ROS에서 robot의 link와 joint 구조를 표현하는 XML 형식이다. | `<robot name="tutorial_bot">` |
| Xacro | 매크로, 인자, 수식을 사용해 URDF XML을 생성하는 전처리 도구이다. | `<xacro:wheel prefix="left"/>` |
| SDF | Gazebo world, model, sensor, plugin을 기술하는 XML 형식이다. | `<sdf version="1.10">` |
| world | physics, light, model, world System을 담는 simulation 최상위 환경이다. | `<world name="empty">` |
| model | 하나 이상의 link와 joint로 구성된 독립 entity 묶음이다. | `<model name="rover">` |
| link | 질량·관성·visual·collision을 갖는 강체 단위이다. | `<link name="base_link">` |
| joint | 두 link의 상대 운동을 제한하는 연결이다. | `fixed`, `revolute`, `continuous` |
| visual | 화면 렌더링에 사용하는 형상과 재질이다. | `<visual name="body_visual">` |
| collision | 접촉과 충돌 계산에 사용하는 형상이다. | `<collision name="body_collision">` |
| inertial | 질량, 질량중심, 관성 tensor를 정의한다. | `<mass>4.0</mass>` |

URDF/Xacro는 ROS robot description의 원본으로 사용하고, Gazebo가 실행할 때 SDF로 변환하는 흐름이 일반적이다. world 전체와 Gazebo 전용 System 설정은 SDF가 더 직접적으로 표현한다.

## Gazebo 구조

| 용어 | 설명 | 이 튜토리얼의 예 |
| --- | --- | --- |
| Entity | ECS에서 model, link, sensor 등을 식별하는 정수 ID이다. | `modelEntity_` |
| Component | entity에 연결된 이름·자세·속도 같은 데이터이다. | `components::Pose` |
| System | simulation update에서 component를 읽거나 쓰는 플러그인이다. | `TutorialBotDiagnostics` |
| ECM | Entity와 Component를 조회·생성·제거하는 `EntityComponentManager`이다. | `ecm.EntityByComponents(...)` |
| Gazebo Transport | Gazebo 내부의 topic과 request/reply 통신 계층이다. | `gz::transport::Node` |
| server | physics, System, sensor update를 실행하는 simulation process이다. | `gz sim -s` |
| client | scene을 렌더링하고 GUI plugin을 실행하는 process이다. | `gz sim` GUI |
| simulation time | physics step에 따라 증가하는 world 내부 시간이다. | `UpdateInfo::simTime` |
| wall time | host 운영체제가 측정하는 실제 경과 시간이다. | CI 실행 시간 |
| real-time factor | simulation time 증가율과 wall time 증가율의 비이다. | 목표값 `1.0` |

## ROS 2와 좌표계

| 용어 | 설명 | 이 튜토리얼의 예 |
| --- | --- | --- |
| DDS | ROS 2가 기본적으로 사용하는 통신 미들웨어 계열이다. | topic discovery와 QoS |
| node | publisher, subscriber, service 같은 ROS graph endpoint를 소유하는 실행 단위이다. | `robot_state_publisher` |
| topic | 같은 메시지 타입의 연속 데이터를 비동기로 전달한다. | `/odom`, `/scan` |
| service | request 하나에 response 하나를 돌려주는 RPC 형태이다. | spawn 요청 |
| QoS | history, reliability, durability 같은 ROS 2 전달 정책이다. | sensor data profile |
| bridge | 서로 다른 메시지·통신 계층 사이의 타입과 방향을 변환한다. | `ros_gz_bridge` |
| TF | 시간에 따른 좌표 프레임 관계를 ROS 2 topic으로 전달하는 체계이다. | `odom → base_link` |
| static TF | 실행 중 변하지 않는 frame 관계이다. | `base_link → lidar_link` |
| odometry | 기준 frame에서 추정한 pose와 twist이다. 절대 위치 보장을 뜻하지 않는다. | wheel odom |

## 이름이 비슷해 혼동하기 쉬운 항목

| 항목 A | 항목 B | 차이 |
| --- | --- | --- |
| `base_link` | `base_footprint` | 전자는 robot body frame이고 후자는 지면에 투영한 평면 기준 frame으로 주로 사용한다. |
| visual geometry | collision geometry | 렌더링용과 physics 접촉용이다. 계산 비용 때문에 collision을 더 단순하게 만들 수 있다. |
| Gazebo topic | ROS 2 topic | Transport graph와 DDS graph에 각각 존재한다. 이름이 같아도 bridge 없이는 자동 연결되지 않는다. |
| System reset service | `ISystemReset` | 전자는 사용자 endpoint이고 후자는 Gazebo world reset 생명주기 callback이다. |
| publish period | physics step | 메시지 발행 간격과 물리 적분 간격이다. 같은 값일 필요가 없다. |
| `GZ_SIM_SYSTEM_PLUGIN_PATH` | `GZ_SIM_RESOURCE_PATH` | 전자는 System 공유 라이브러리, 후자는 model·mesh·world 같은 resource 검색 경로이다. |
