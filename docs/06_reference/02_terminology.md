# 용어

처음 보는 용어는 한국어 뜻과 함께 읽고, 파일에서 찾을 때는 원래 이름을 사용한다. 예를 들어 링크의 충돌 형상을 수정하려면 XML에서 `<collision>`을 찾는다.

## 로봇과 파일 형식

| 용어 | 뜻 | 예 |
| --- | --- | --- |
| URDF | ROS에서 로봇의 링크와 관절 구조를 표현하는 XML 형식 | `<robot name="tutorial_bot">` |
| Xacro | 반복 정의·인자·수식으로 URDF를 만드는 전처리 도구 | `<xacro:wheel side="left" y_position="0.19"/>` |
| SDF | Gazebo의 월드·모델·센서·플러그인을 정의하는 XML 형식 | `<sdf version="1.10">` |
| 월드(world) | 물리 설정, 조명, 모델을 담는 시뮬레이션 환경 | `<world name="training">` |
| 모델(model) | 링크와 관절로 이루어진 물체 또는 로봇 | `<model name="tutorial_bot">` |
| 링크(link) | 질량·관성·표시 형상·충돌 형상을 갖는 강체 단위 | `base_link` |
| 관절(joint) | 두 링크를 연결하고 상대 운동을 제한하는 요소 | 고정 `fixed`, 회전 `revolute` |
| 표시 형상(visual) | 화면에 그릴 모양과 재질 | `<visual name="body_visual">` |
| 충돌 형상(collision) | 물체 사이의 접촉 계산에 사용할 모양 | `<collision name="body_collision">` |
| 관성(inertial) | 질량·무게중심·회전에 대한 저항을 나타내는 관성 행렬 | `<mass>4.0</mass>` |

이 과정에서는 ROS 로봇 구조를 URDF/Xacro로 관리하고 Gazebo에 넣을 때 SDF로 변환한다. 월드 전체와 Gazebo 전용 설정은 SDF로 작성한다. 순수 Gazebo를 먼저 배우는 초급의 SDF 모델과 ROS 2 통합용 Xacro가 어느 단계의 예제인지 구분한다.

## Gazebo 구조와 시간

| 용어 | 뜻 | 예 |
| --- | --- | --- |
| Entity | 모델·링크·센서 등을 가리키는 정수 식별자 | `modelEntity_` |
| Component | 개체에 붙어 있는 이름·자세·속도 등의 데이터 | `components::Pose` |
| System | 시뮬레이션 갱신 때 데이터를 읽거나 바꾸는 기능 | `TutorialBotDiagnostics` |
| ECS | 개체(Entity), 데이터(Component), 처리 기능(System)을 나누는 구조 | 로봇의 자세를 읽는 진단 플러그인 |
| ECM | 개체와 데이터를 조회·생성·제거하는 관리 객체 | `EntityComponentManager` |
| Gazebo Transport | Gazebo 프로세스 사이에서 토픽과 서비스로 메시지를 주고받는 통신 방식 | `gz::transport::Node` |
| 서버(server) | 물리 계산과 시스템·센서 갱신을 실행하는 프로세스 | `gz sim -s` |
| 클라이언트(client) | 장면을 표시하고 GUI를 실행하는 프로세스 | `gz sim -g` |
| 시뮬레이션 시간 | 가상 세계 안에서 물리 계산에 따라 흐르는 시간 | `UpdateInfo::simTime` |
| 실제 경과 시간(wall time) | 컴퓨터의 시계로 측정한 시간 | 테스트가 실제로 걸린 시간 |
| 실시간 비율(real-time factor) | 실제 1초 동안 시뮬레이션이 진행한 시간의 비율 | `1.0`이면 같은 속도 |

월드의 `real_time_factor`는 목표값이다. 실행 컴퓨터의 처리 속도가 부족하면 실제 비율은 목표보다 낮아질 수 있다. GUI의 초당 프레임 수(FPS)는 화면 갱신 빈도로, 물리 계산 횟수나 센서 발행 주기와 다르다.

## ROS 2와 좌표계

| 용어 | 뜻 | 예 |
| --- | --- | --- |
| DDS | ROS 2가 기본적으로 사용하는 통신 미들웨어 계열 | 노드 간 통신 대상 검색과 메시지 전달 |
| 노드(node) | 발행·구독·서비스 같은 기능을 수행하는 실행 단위 | `robot_state_publisher` |
| 토픽(topic) | 같은 타입의 메시지를 비동기로 전달하는 이름 | `/odom`, `/scan` |
| 서비스(service) | 요청을 보내고 응답을 받는 통신 방식 | 모델 생성 요청 |
| QoS | 메시지 전달 신뢰도·보관 개수·이전 메시지 보존 등을 정하는 정책 | 센서의 `Best Effort` |
| 브리지(bridge) | Gazebo와 ROS 2 사이에서 메시지 타입과 방향을 변환하는 프로그램 | `ros_gz_bridge` |
| 프레임(frame) | 위치와 방향을 표현하는 기준 좌표계 | `base_link`, `lidar_link` |
| TF | 시간에 따른 프레임 사이의 위치·회전 관계 | `odom → base_link` |
| 정적 TF | 실행 중 변하지 않는 프레임 사이의 관계 | `base_link → lidar_link` |
| 주행 추정(odometry) | 기준 좌표계에서 추정한 로봇의 위치·방향·속도 | 바퀴 회전으로 얻는 `/odom` |
| 광학 좌표계(optical frame) | 영상에 쓰는 좌표계. x는 오른쪽, y는 아래, z는 카메라 정면 | `camera_optical_frame` |

일반 로봇 좌표계는 x가 전방, y가 왼쪽, z가 위다. 카메라 광학 좌표계는 축이 다르므로 카메라 영상·점군의 `header.frame_id`와 TF를 함께 맞춰야 한다. 자세한 규칙은 [ROS REP-103](https://www.ros.org/reps/rep-0103.html)을 따른다.

## 검증에 사용하는 용어

| 용어 | 뜻 | 예 |
| --- | --- | --- |
| 계약(contract) | 프로그램 사이에서 지켜야 할 이름·타입·동작 규칙 | 초기화 서비스의 요청은 `gz.msgs.Empty` |
| 시나리오(scenario) | 특정 입력부터 결과 확인까지의 한 실험 | 이동 명령 → 거리 증가 확인 |
| 정상 시나리오(nominal) | 올바른 설정에서 기대 동작을 확인하는 실험 | 빌드한 플러그인을 정상 로드 |
| 오류 주입(fault injection) | 일부러 잘못된 조건을 만들어 오류 처리도 확인하는 방법 | 존재하지 않는 라이브러리 경로 지정 |
| GUI 없는 실행(headless) | 화면 창 없이 서버와 검사를 실행하는 방식 | `gz sim -s` |
| CI | 변경할 때마다 빌드와 테스트를 자동 실행하는 환경 | GitHub Actions |
| 커밋 SHA | 검사에 사용한 소스 버전을 식별하는 값 | `git rev-parse HEAD` |
| 검증 결과(evidence) | 실제 실행에서 수집한 로그·메시지·수치·화면 기록 | `scenario.json`, RViz 화면 |
| 종료 확인 기록 | 검사에서 시작한 프로세스가 모두 끝났는지 남기는 기록 | `cleanup.json` |

## 이름이 비슷한 항목

| 항목 A | 항목 B | 차이 |
| --- | --- | --- |
| `base_link` | `base_footprint` | 로봇 본체의 기준 좌표계와 주로 지면에 투영한 평면 기준 좌표계다. |
| `visual` | `collision` | 화면 표시용 형상과 접촉 계산용 형상이다. 서로 다른 모양을 쓸 수 있다. |
| Gazebo 토픽 | ROS 2 토픽 | 서로 다른 통신망에 있다. 이름이 같아도 브리지 없이 자동 연결되지 않는다. |
| 플러그인 초기화 서비스 | `ISystemReset` | 사용자가 만든 서비스와 Gazebo가 월드를 초기화할 때 호출하는 인터페이스다. |
| 메시지 발행 주기 | 물리 계산 간격 | 데이터를 보내는 주기와 물리 상태를 갱신하는 간격이다. |
| `GZ_SIM_SYSTEM_PLUGIN_PATH` | `GZ_SIM_RESOURCE_PATH` | 시스템 공유 라이브러리 검색 경로와 모델·메시·월드 등의 자료 검색 경로다. |
