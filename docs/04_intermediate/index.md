# 중급 과정: ROS 2 통합

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 초급 프로젝트

## 학습 목표

- 하나의 Xacro 로봇 원본을 Gazebo와 ROS 2에서 함께 사용한다.
- launch, bridge, TF, `ros2_control`, 센서, 다중 로봇, Nav2를 하나의 실행 흐름으로 연결한다.
- 2륜 차동구동을 기준으로 4륜 skid-steer와 조향식 Ackermann 구조의 선택 기준을 이해한다.
- keyboard teleop으로 주행하고 wheel odometry 궤적을 RViz에서 확인한다.
- 저장소의 자동 검증 스크립트로 관찰 결과를 재현한다.

## 학습 흐름

이 과정은 모델 형식을 먼저 구분한 뒤 실행, 통신, 좌표계, 제어, 센서, 자율주행 순서로 기능을 한 층씩 올린다. 각 장은 **설명 → 실제 코드 → 실행 → 관찰 → 문제 해결** 순서로 구성한다. MOGI-ROS의 주차별 Gazebo 학습 자료에서 이 점진적 흐름만 참고했으며, 예제와 문장은 ROS 2 Jazzy·Gazebo Harmonic 조합에 맞게 독립적으로 작성한다.

이 과정은 Gazebo Classic이 아니라 **Gazebo Harmonic**과 `ros_gz` 계열 패키지를 사용한다. 로봇 구조의 원본은 URDF/Xacro이고, SDF는 world와 Gazebo 고유 물리·센서·System 설정에 사용한다. 같은 로봇을 별도 SDF 원본으로 중복 관리하지 않는다.

[선행 과정: 초급 프로젝트](../03_beginner/11_project-tutorial-bot.md)

<figure class="course-figure" id="intermediate-course-dataflow">
  <img src="../assets/intermediate/course-dataflow.svg" alt="중급 과정의 모델 실행 관측 제어 자율주행 데이터 흐름도" loading="lazy">
  <figcaption>그림 1. 모델, 실행, 관측, 제어, 자율주행이 앞 단계의 출력을 다음 단계의 입력으로 사용한다.</figcaption>
</figure>

## 형식과 실행 계층 한눈에 보기

| 계층 | 주 파일 | 맡는 일 | 대표 도구 |
|---|---|---|---|
| 로봇 구조 | `tutorial_bot.urdf.xacro` | link, joint, 관성, Gazebo 확장 생성 | `xacro`, `check_urdf` |
| Gazebo 환경 | `training.sdf` | world, physics, light, fixture, System | `gz sdf`, `gz sim` |
| ROS 실행 | `simulation.launch.py` | description, spawn, bridge, controller, RViz, Nav2 조립 | `ros2 launch` |
| 메시지 연결 | `bridge-intermediate.yaml` | Gazebo Transport와 ROS 2 DDS 사이 타입·방향·QoS 선언 | `ros_gz_bridge` |
| 바퀴 제어 | `controllers.yaml` | joint interface, DiffDrive, wheel odometry | `gz_ros2_control` |

이름만 보고 파일을 선택하지 않는다. 예를 들어 SDF가 로봇도 표현할 수 있지만 이 저장소에서는 로봇 원본을 Xacro 한 곳에 둔다. 반대로 URDF 안에 `<gazebo>` 확장을 넣을 수 있어도 world 전체의 physics와 fixture는 SDF에 둔다.

## 과정 구성

1. [고급 SDF](01-advanced-sdf.md): frame, pose, 관성, 마찰을 다룬다.
2. [URDF·Xacro·SDF](02-urdf-xacro-sdf.md): 코드 수준에서 세 형식의 책임과 Xacro 재사용을 구분한다.
3. [ROS 2 Launch](03-ros2-launch.md): 설치된 리소스와 준비 이벤트로 실행 순서를 구성한다.
4. [Robot Spawn](04-spawn-model.md): `robot_description`을 Gazebo entity로 만든다.
5. [`ros_gz_bridge` 심화](05-bridge-yaml.md): 방향, 타입, QoS, 이름 재지정을 YAML로 관리한다.
6. [TF·Joint State·RViz](06-tf-rviz.md): URDF 기반 TF와 wheel odometry 궤적을 시각화한다.
7. [`gz_ros2_control`](07-gz-ros2-control.md): 2륜·4륜 DiffDrive와 Ackermann 대안을 비교한다.
8. [센서 심화](08-advanced-sensors.md): 센서 설정과 실제 수신 rate·noise를 교차 검증한다.
9. [다중 로봇](09-multi-robot.md): entity, namespace, controller, TF를 로봇별로 격리한다.
10. [Nav2 연동](10-nav2.md): map, localization, costmap, controller를 연결한다.
11. [프로젝트: 자율주행 `tutorial_bot`](11_project-autonomous-bot.md): 전체 스택을 반복 검증한다.

## 공통 예제 파일

- 로봇 원본: `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`
- 단계별 Xacro 매크로: `examples/ros2_ws/src/tutorial_bot_description/urdf/macros/stage_components.xacro`
- 단일 로봇 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`
- 다중 로봇 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/multi_robot.launch.py`
- bridge 설정: `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`
- controller 설정: `examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`
- 학습 world: `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`

## 실행 준비

`colcon build`는 source package를 빌드하지만 `package.xml`에 선언한 시스템 의존성을 설치하지 않는다. 저장소 루트에서 다음 순서로 준비한다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build \
  --packages-select tutorial_bot_description tutorial_bot_gazebo \
                    tutorial_bot_control tutorial_bot_bringup \
  --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
cd ../..
```

새 terminal을 열 때마다 `/opt/ros/jazzy/setup.bash`와 `examples/ros2_ws/install/setup.bash`를 다시 source한다.

## 첫 smoke test

설치된 world와 Xacro가 실제로 해석되는지 먼저 확인한다.

```bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/training.sdf"
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"

gz sdf -k "$world"
xacro "$robot" control_backend:=gz_ros2_control \
  controller_parameters_file:="$(ros2 pkg prefix --share tutorial_bot_control)/config/controllers.yaml" \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

`gz sdf -k`와 `check_urdf`가 오류 없이 끝나고 `base_link`, 좌우 바퀴 joint, 센서 link가 출력되면 준비가 끝난 것이다.

## 구조를 따라 계산하기

<div class="course-worked" data-worked-example="course-dataflow">
한 단계의 출력 집합을 \(O_k\), 다음 단계의 필수 입력 집합을 \(I_{k+1}\)라 두면 연결 조건은 \(I_{k+1}\subseteq O_k\)이다. 예를 들어 TF 장의 출력 `odom → base_link`와 `/scan` frame은 Nav2의 입력이다. checker는 단순 실행 문구가 아니라 이 집합을 이루는 topic, frame, controller lifecycle 상태를 실제로 파싱한다.
</div>

## 공통 검증 원칙

- **파일이 존재한다**와 **runtime에서 동작한다**를 구분한다.
- topic 이름만 보지 않고 type, publisher 수, QoS, `frame_id`, timestamp를 함께 본다.
- GUI 화면만 보지 않고 CLI로 같은 관찰값을 확인한다.
- `use_sim_time:=true`를 사용하는 node에는 증가하는 `/clock`이 필요하다.
- robot description의 치수와 controller YAML의 `wheel_radius`, `wheel_separation`을 같은 값으로 유지한다.
- Gazebo entity 이름, ROS namespace, TF prefix는 서로 다른 식별자이다.

## 문제 해결

의존성 오류가 나오면 `examples/ros2_ws`에서 `rosdep check --from-paths src --ignore-src --rosdistro jazzy`를 실행한다. 빌드한 package를 찾지 못하면 현재 shell이 설치 공간을 source했는지 `ros2 pkg prefix tutorial_bot_bringup`으로 확인한다. Gazebo Classic 명령인 `gazebo`나 `ign gazebo` 대신 Harmonic의 `gz sim`과 `ros_gz_*` 도구를 사용한다.

## 정리

중급 과정은 초급 로봇을 다시 작성하지 않는다. 검증된 Xacro 원본 위에 SDF world, launch, bridge, TF, controller, 센서, Nav2를 순서대로 쌓고 각 경계를 코드와 관찰값으로 확인한다.
