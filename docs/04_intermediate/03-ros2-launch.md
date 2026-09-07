# ROS 2 Launch 실행

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** URDF·Xacro·SDF

## 학습 목표

- Python launch의 선언 인자와 실행 순서를 읽는다.
- Xacro를 `robot_description` 파라미터로 생성한다.
- Gazebo 실행부터 로봇 생성, 통신, 제어, 시각화까지 한 명령으로 시작한다.
- 앞 단계의 종료 코드와 실제 서비스 준비 상태를 확인하고 다음 단계를 시작한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## launch 파일의 역할

launch 파일은 여러 ROS 노드와 Gazebo를 함께 실행하는 설정이다. 설치된 패키지에서 파일을 찾고, 사용자가 준 인자를 검증하고, 노드의 파라미터·이름 재지정을 선언하며, 앞 프로세스의 성공 여부에 따라 다음 프로세스를 시작한다. 실행 순서를 코드에 남기면 여러 터미널에서 수동으로 입력할 때 생기는 순서 차이를 줄일 수 있다.

실행 기준 파일은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`이다.

## 1. 인자 선언과 유효성 검사

파일 끝의 `generate_launch_description()`은 공개 인자를 선언한다.

```python
def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("world", default_value="training"),
            DeclareLaunchArgument("model_name", default_value="tutorial_bot"),
            DeclareLaunchArgument("namespace", default_value="/"),
            DeclareLaunchArgument("tf_prefix", default_value=""),
            DeclareLaunchArgument("gui", default_value="true"),
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("nav2", default_value="true"),
            OpaqueFunction(function=_launch_stack),
        ]
    )
```

`OpaqueFunction` 안에서는 `LaunchConfiguration(...).perform(context)`로 실제 문자열을 얻어 검사한다. 현재 예제는 월드 이름, 모델 이름, 네임스페이스, TF 접두사를 정규식으로 제한한다. 이 단일 로봇 launch는 고정된 브리지·컨트롤러 설정을 사용하므로 `namespace:=/`, 빈 `tf_prefix`만 지원한다. 여러 로봇이나 접두사가 필요한 실습에는 `multi_robot.launch.py`를 사용한다.

## 2. 설치된 패키지 리소스 경로 사용하기

소스 디렉터리 상대 경로 대신 ament index가 알려 주는 설치 경로를 사용한다.

```python
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

gazebo_share = Path(get_package_share_directory("tutorial_bot_gazebo"))
description_share = Path(get_package_share_directory("tutorial_bot_description"))
control_share = Path(get_package_share_directory("tutorial_bot_control"))

world_path = gazebo_share / "worlds" / "training.sdf"
xacro_path = description_share / "urdf" / "tutorial_bot.urdf.xacro"
controller_config = control_share / "config" / "controllers.yaml"
```

설치된 경로를 찾으면 터미널의 현재 디렉터리가 바뀌어도 같은 파일을 읽을 수 있다. 파일을 찾지 못할 때는 해당 패키지의 설치 규칙과 빌드 결과를 확인한다.

## 3. Xacro를 `robot_description`으로 만들기

launch의 `Command`는 Xacro를 실행한 뒤 표준 출력으로 나온 URDF를 파라미터에 넣는다.

```python
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue

robot_description = ParameterValue(
    Command(
        [
            "xacro ", str(xacro_path),
            " control_backend:=gz_ros2_control",
            " controller_parameters_file:=", str(controller_config),
            " model_name:=", model_name,
            " ros_namespace:=", namespace,
            " tf_prefix:=", tf_prefix,
        ]
    ),
    value_type=str,
)

state_publisher = Node(
    package="robot_state_publisher",
    executable="robot_state_publisher",
    namespace=namespace,
    parameters=[{
        "robot_description": robot_description,
        "frame_prefix": tf_prefix,
        "use_sim_time": True,
    }],
)
```

`ParameterValue(..., value_type=str)`를 사용하지 않으면 XML을 문자열이 아닌 다른 YAML 값으로 해석할 수 있다. `use_sim_time`을 켠 노드에는 브리지된 `/clock`이 필요하다.

## 4. Gazebo 포함과 로봇 생성

Harmonic은 `ros_gz_sim`이 제공하는 launch를 포함한다.

```python
gazebo = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        str(Path(get_package_share_directory("ros_gz_sim"))
            / "launch" / "gz_sim.launch.py")
    ),
    launch_arguments={
        "gz_args": f"-s -r {world_path}",
        "on_exit_shutdown": "true",
    }.items(),
)

spawn = Node(
    package="ros_gz_sim",
    executable="create",
    arguments=["-name", model_name, "-topic", "robot_description", "-z", "0.12"],
    output="screen",
)
```

`-s`는 GUI 없이 서버만 실행하고, `-r`은 시작 즉시 시뮬레이션을 재생한다. GUI를 켤 때는 `-r`만 사용한다.

## 5. 로봇 생성이 성공한 뒤 컨트롤러 시작하기

생성 프로세스가 종료 코드 0으로 끝난 뒤 컨트롤러 관리자 준비를 확인하고 spawner를 순서대로 실행한다.

```python
def _after_success(next_action: Action, completed_name: str):
    def transition(event: ProcessExited, _: LaunchContext):
        if event.returncode == 0:
            return [next_action]
        return [EmitEvent(event=Shutdown(
            reason=f"{completed_name} exited with code {event.returncode}."
        ))]
    return transition

RegisterEventHandler(
    OnProcessExit(
        target_action=spawn,
        on_exit=_after_success(controller_manager_ready, "robot spawn"),
    )
)
```

단순히 10초를 기다리는 방식은 느린 컴퓨터에서 부족하고 빠른 컴퓨터에서는 불필요하게 오래 기다린다. 준비 상태 확인 프로세스는 `/controller_manager/list_controllers` 서비스가 실제로 생길 때까지 확인하며, 제한 시간 초과가 나면 어느 단계가 준비되지 않았는지 남긴다.

<figure class="course-figure" id="intermediate-launch-readiness">
  <img src="../../assets/intermediate/launch-readiness.svg" alt="Gazebo 준비부터 Nav2 활성까지의 launch readiness 의존 그래프" loading="lazy">
  <figcaption>그림 1. launch는 고정 대기가 아니라 준비 완료 상태으로 다음 프로세스를 시작한다.</figcaption>
</figure>

## 계산 예제: 준비 시간의 상한

<div class="course-worked" data-worked-example="launch-readiness">
단계별 준비 시간을 \(t_g,t_s,t_c,t_b\)라 하면 직렬 임계 경로는 \(T=t_g+t_s+t_c+t_b\)이다. 측정값이 각각 6, 2, 4, 1초라면 13초이다. 모든 단계에 무조건 10초 고정 대기를 넣은 40초와 달리 준비 상태 확인 방식은 빠른 환경에서 즉시 진행하고 어느 단계가 제한 시간 초과인지도 보존한다.
</div>

## 실행

먼저 launch 인자를 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 launch tutorial_bot_bringup simulation.launch.py --show-args
```

GUI와 Nav2 없이 핵심 스택을 실행한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  nav2:=false gui:=false rviz:=false
```

별도 터미널에서 핵심 노드와 컨트롤러를 확인한다.

```bash
ros2 node list
ros2 control list_controllers
ros2 topic hz /clock
ros2 topic echo /odom --once
```

전체 자동 검증은 저장소 루트에서 실행한다.

```bash
./scripts/check_intermediate_launch.sh --evidence /tmp/tutorial-intermediate-launch --launch --nav2 false
```

검증은 엔티티, 컨트롤러, `/clock`, 센서, 명령, 오도메트리 준비 상태를 실행 중에 확인한다. 종료 코드 0이 성공 조건이다.

## 4륜 로버 launch와 모드 선택

4륜 예제는 별도 launch에서 주행 방식에 맞는 Xacro를 선택한다. 실제 파일은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/rover.launch.py`이다.

```python
drive_mode = LaunchConfiguration("drive_mode").perform(context)
if drive_mode not in {"diff", "ackermann"}:
    raise RuntimeError("drive_mode must be either 'diff' or 'ackermann'")

xacro_file = (
    description_share / "urdf" / "rovers" /
    f"rover_{drive_mode}.urdf.xacro"
)
```

아래에서 한 가지 모드만 실행한다. 다른 모드를 시험할 때는 기존 launch를 `Ctrl+C`로 종료한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

두 모드 모두 ROS `/cmd_vel`, `/odom`, `/joint_states`, `/wheel_odom_path`와 RViz 설정을 같은 토픽 이름으로 제공한다. 따라서 주행 구조가 달라도 키보드 조종과 궤적 확인 절차를 재사용할 수 있다.

## 문제 해결

- `PackageNotFoundError`가 나오면 `source examples/ros2_ws/install/setup.bash`를 실행한다.
- launch 파일을 수정했는데 반영되지 않으면 `colcon build` 후 설치 공간을 다시 source한다.
- GUI가 없는 환경에서는 `gui:=false rviz:=false`를 사용한다.
- 생성 뒤 시스템이 종료되면 생성 프로세스의 첫 오류와 종료 코드를 먼저 확인한다.
- `/clock`이 멈추면 Gazebo가 pause 상태인지, 브리지가 실행 중인지 확인한다.
- `drive_mode` 오타는 `diff` 또는 `ackermann` 중 하나로 고친다.

## 정리

Python launch는 Xacro 생성, 설치 리소스 조회, Gazebo 실행, 로봇 생성, 브리지, 컨트롤러, RViz, Nav2의 의존 관계를 코드로 표현한다. 인자를 검증하고 준비 완료 상태를 기준으로 다음 단계를 시작해야 실패 원인과 실행 순서를 재현할 수 있다.

[이전: URDF·Xacro·SDF](02-urdf-xacro-sdf.md) · [다음: 로봇 생성](04-spawn-model.md)
