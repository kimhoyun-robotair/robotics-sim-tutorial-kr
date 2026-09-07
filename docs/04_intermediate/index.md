# 중급 과정: ROS 2 통합

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 초급 프로젝트

## 학습 목표

- 하나의 Xacro 로봇 원본을 Gazebo와 ROS 2에서 함께 사용한다.
- launch, 브리지, TF, `ros2_control`, 센서, 다중 로봇, Nav2를 하나의 실행 흐름으로 연결한다.
- 2륜 차동구동을 기준으로 4륜 스키드 조향과 조향식 Ackermann 구조의 선택 기준을 이해한다.
- 키보드 조종으로 주행하고 바퀴 오도메트리 궤적을 RViz에서 확인한다.
- 저장소의 자동 검증 스크립트로 관찰 결과를 재현한다.

## 학습 흐름

초급에서 만든 로봇에 ROS 2 기능을 하나씩 붙인다. 먼저 로봇 모델을 읽고 실행하는 방법을 익힌 뒤, 통신·좌표계·제어·센서·자율주행 순서로 진행한다. 각 장에는 실행 명령과 확인할 결과를 함께 적었다.

이 과정은 Gazebo Classic이 아니라 **Gazebo Harmonic**과 `ros_gz` 계열 패키지를 사용한다. 로봇 구조의 원본은 URDF/Xacro이고, SDF는 월드와 Gazebo 고유 물리·센서·시스템 플러그인 설정에 사용한다. 같은 로봇을 별도 SDF 원본으로 중복 관리하지 않는다.

[선행 과정: 초급 프로젝트](../03_beginner/11_project-tutorial-bot.md)

<figure class="course-figure" id="intermediate-course-dataflow">
  <img src="../assets/intermediate/course-dataflow.svg" alt="중급 과정의 모델 실행 관측 제어 자율주행 데이터 흐름도" loading="lazy">
  <figcaption>그림 1. 모델, 실행, 관측, 제어, 자율주행이 앞 단계의 출력을 다음 단계의 입력으로 사용한다.</figcaption>
</figure>

## 형식과 실행 계층 한눈에 보기

| 계층 | 주 파일 | 맡는 일 | 대표 도구 |
|---|---|---|---|
| 로봇 구조 | `tutorial_bot.urdf.xacro` | 링크, 조인트, 관성, Gazebo 확장 생성 | `xacro`, `check_urdf` |
| Gazebo 환경 | `training.sdf` | 월드, 물리 설정, 조명, 검사용 구조물, 시스템 플러그인 | `gz sdf`, `gz sim` |
| ROS 실행 | `simulation.launch.py` | 로봇 설명, 생성, 브리지, 컨트롤러, RViz, Nav2 조립 | `ros2 launch` |
| 메시지 연결 | `bridge-intermediate.yaml` | Gazebo Transport와 ROS 2 DDS 사이 타입·방향·QoS 선언 | `ros_gz_bridge` |
| 바퀴 제어 | `controllers.yaml` | 조인트 인터페이스, DiffDrive, 바퀴 오도메트리 | `gz_ros2_control` |

이름만 보고 파일을 선택하지 않는다. 예를 들어 SDF가 로봇도 표현할 수 있지만 이 저장소에서는 로봇 원본을 Xacro 한 곳에 둔다. 반대로 URDF 안에 `<gazebo>` 확장을 넣을 수 있어도 월드 전체의 물리 설정과 검사용 구조물은 SDF에 둔다.

## 과정 구성

1. [고급 SDF](01-advanced-sdf.md): 좌표계, 위치와 자세, 관성, 마찰을 다룬다.
2. [URDF·Xacro·SDF](02-urdf-xacro-sdf.md): 코드 수준에서 세 형식의 책임과 Xacro 재사용을 구분한다.
3. [ROS 2 Launch](03-ros2-launch.md): 설치된 리소스와 준비 이벤트로 실행 순서를 구성한다.
4. [로봇 생성](04-spawn-model.md): `robot_description`을 Gazebo 엔티티로 만든다.
5. [`ros_gz_bridge` 심화](05-bridge-yaml.md): 방향, 타입, QoS, 이름 재지정을 YAML로 관리한다.
6. [TF·Joint State·RViz](06-tf-rviz.md): URDF 기반 TF와 바퀴 오도메트리 궤적을 시각화한다.
7. [`gz_ros2_control`](07-gz-ros2-control.md): 2륜·4륜 DiffDrive와 Ackermann 대안을 비교한다.
8. [센서 심화](08-advanced-sensors.md): 센서 설정과 실제 수신 빈도·노이즈를 교차 검증한다.
9. [다중 로봇](09-multi-robot.md): 엔티티, 네임스페이스, 컨트롤러, TF를 로봇별로 격리한다.
10. [Nav2 연동](10-nav2.md): 지도, 위치 추정, 비용 지도, 컨트롤러를 연결한다.
11. [프로젝트: 자율주행 `tutorial_bot`](11_project-autonomous-bot.md): 전체 스택을 반복 검증한다.

## 공통 예제 파일

- 로봇 원본: `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`
- 단계별 Xacro 매크로: `examples/ros2_ws/src/tutorial_bot_description/urdf/macros/stage_components.xacro`
- 단일 로봇 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`
- 다중 로봇 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/multi_robot.launch.py`
- 브리지 설정: `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`
- 컨트롤러 설정: `examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`
- 학습 월드: `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`

## 실행 준비 {#intermediate-setup}

`colcon build`는 소스 패키지를 빌드하지만 `package.xml`에 선언한 시스템 의존성을 설치하지 않는다. 저장소 루트에서 다음 순서로 준비한다.

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

빌드가 끝나면 `Summary: 4 packages finished`를 확인한다. 새 터미널을 열 때마다 **저장소 루트**로 이동하고 다음 두 명령으로 환경을 불러온다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 pkg prefix tutorial_bot_bringup
```

마지막 명령에 `examples/ros2_ws/install/tutorial_bot_bringup` 경로가 나오면 준비된 것이다. 경로를 찾지 못하면 빌드 결과와 현재 작업 디렉터리부터 확인한다.

실습 중 터미널은 역할별로 나눈다. launch나 Gazebo를 실행한 터미널은 그대로 두고, 새 터미널에서 토픽을 조회하거나 키보드 조종을 실행한다. `ros2 topic hz`, `tf2_echo`처럼 끝나지 않는 조회 명령은 몇 개 값을 확인한 뒤 `Ctrl+C`로 종료한다. 다음 실습으로 넘어갈 때는 기존 launch도 종료한다. 같은 로봇과 브리지를 중복 실행하면 TF와 토픽이 섞일 수 있다.

## 먼저 모델 파일 검사하기

설치된 월드와 Xacro가 실제로 해석되는지 먼저 확인한다.

```bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/training.sdf"
robot="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/tutorial_bot.urdf.xacro"

gz sdf -k "$world"
xacro "$robot" control_backend:=gz_ros2_control \
  controller_parameters_file:="$(ros2 pkg prefix --share tutorial_bot_control)/config/controllers.yaml" \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

`gz sdf -k`와 `check_urdf`가 오류 없이 끝나고 `base_link`, 좌우 바퀴 조인트, 센서 링크가 출력되면 준비가 끝난 것이다.

## 다음 단계로 넘어가는 기준

<div class="course-worked" data-worked-example="course-dataflow" markdown="1">
Nav2를 켜기 전에 `/scan` 메시지를 받는지, `/odom`이 갱신되는지, `odom → base_link → lidar_link`가 연결되는지 순서대로 확인한다. 이 셋 중 하나가 준비되지 않았다면 해당 장의 문제 해결 절차로 돌아간다. 예를 들어 `/scan`은 있지만 RViz에 레이저가 보이지 않는다면 센서를 새로 만들기보다 메시지의 `frame_id`, TF, QoS부터 확인한다.
</div>

## 공통 검증 원칙

- **파일이 존재한다**와 **실제로 데이터를 주고받는다**를 구분한다.
- 토픽 이름만 보지 않고 타입, 발행 노드 수, QoS, `frame_id`, 타임스탬프를 함께 본다.
- GUI 화면만 보지 않고 CLI로 같은 관찰값을 확인한다.
- `use_sim_time:=true`를 사용하는 노드에는 증가하는 `/clock`이 필요하다.
- 로봇 설명의 치수와 컨트롤러 YAML의 `wheel_radius`, `wheel_separation`을 같은 값으로 유지한다.
- Gazebo 엔티티 이름, ROS 네임스페이스, TF 접두사는 서로 다른 식별자이다.

## 문제 해결

의존성 오류가 나오면 `examples/ros2_ws`에서 `rosdep check --from-paths src --ignore-src --rosdistro jazzy`를 실행한다. 빌드한 패키지를 찾지 못하면 현재 셸이 설치 공간을 source했는지 `ros2 pkg prefix tutorial_bot_bringup`으로 확인한다. Gazebo Classic 명령인 `gazebo`나 `ign gazebo` 대신 Harmonic의 `gz sim`과 `ros_gz_*` 도구를 사용한다.

## 정리

중급 과정은 초급 로봇을 다시 작성하지 않는다. 검증된 Xacro 원본 위에 SDF 월드, launch, 브리지, TF, 컨트롤러, 센서, Nav2를 순서대로 쌓고 각 경계를 코드와 관찰값으로 확인한다.
