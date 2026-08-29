# ROS 2 Launch 실행

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** URDF·Xacro·SDF

## 학습 목표

- Python launch의 선언 인자와 실행 순서를 읽는다.
- Xacro를 `robot_description` parameter로 생성한다.
- Gazebo, spawn, bridge, controller, RViz, Nav2를 한 명령으로 시작한다.
- 고정 sleep이 아니라 process 성공과 runtime 준비 상태로 다음 단계를 시작한다.

## launch 파일의 역할

launch 파일은 shell 명령의 단순 목록이 아니다. package share에서 리소스를 찾고, 사용자가 준 인자를 검증하고, node의 parameter·remapping을 선언하며, 앞 process의 성공 여부에 따라 다음 process를 시작한다. 실행 순서를 코드에 남기면 여러 terminal에서 수동으로 입력할 때 생기는 순서 차이를 줄일 수 있다.

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

`OpaqueFunction` 안에서는 `LaunchConfiguration(...).perform(context)`로 실제 문자열을 얻어 검사한다. 현재 예제는 world 이름, model 이름, namespace, TF prefix를 정규식으로 제한한다. 사용자 입력을 곧바로 shell command에 붙이지 않고 허용된 형식만 받는 이유는 오타와 command injection을 동시에 막기 위해서이다.

## 2. 설치된 package share 사용하기

source tree 상대 경로 대신 ament index가 알려 주는 설치 경로를 사용한다.

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

이 패턴은 설치 누락을 조기에 드러내고 binary package 또는 다른 workspace overlay에서도 같은 경로 규칙을 유지한다.

## 3. Xacro를 `robot_description`으로 만들기

launch의 `Command` substitution은 Xacro를 실행하고 stdout을 문자열 parameter로 전달한다.

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

`ParameterValue(..., value_type=str)`를 사용하지 않으면 XML 문자열을 YAML scalar로 잘못 해석할 수 있다. `use_sim_time`을 켠 node에는 bridge된 `/clock`이 필요하다.

## 4. Gazebo include와 robot spawn

Harmonic은 `ros_gz_sim`이 제공하는 launch를 include한다.

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

`-s`는 server only, `-r`은 시작 즉시 simulation을 재생한다. GUI를 켤 때는 `-r`만 사용한다.

## 5. 성공 사건 뒤 controller 시작하기

spawn process가 종료 코드 0으로 끝난 뒤 controller manager 준비를 확인하고 spawner를 순서대로 실행한다.

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

단순히 10초를 기다리는 방식은 느린 컴퓨터에서 부족하고 빠른 컴퓨터에서는 불필요하게 오래 기다린다. readiness process는 `/controller_manager/list_controllers` service가 실제로 생길 때까지 확인하며, timeout이 나면 어느 단계가 준비되지 않았는지 남긴다.

<figure class="course-figure" id="intermediate-launch-readiness">
  <img src="../../assets/intermediate/launch-readiness.svg" alt="Gazebo 준비부터 Nav2 활성까지의 launch readiness 의존 그래프" loading="lazy">
  <figcaption>그림 1. launch는 고정 sleep이 아니라 실제 준비 사건으로 다음 process를 시작한다.</figcaption>
</figure>

## 계산 예제: 준비 시간의 상한

<div class="course-worked" data-worked-example="launch-readiness">
단계별 준비 시간을 \(t_g,t_s,t_c,t_b\)라 하면 직렬 임계 경로는 \(T=t_g+t_s+t_c+t_b\)이다. 측정값이 각각 6, 2, 4, 1초라면 13초이다. 모든 단계에 무조건 10초 sleep을 넣은 40초와 달리 readiness 방식은 빠른 환경에서 즉시 진행하고 어느 단계가 timeout인지도 보존한다.
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

별도 terminal에서 핵심 node와 controller를 확인한다.

```bash
ros2 node list
ros2 control list_controllers
ros2 topic hz /clock
ros2 topic echo /odom --once
```

전체 자동 검증은 저장소 루트에서 실행한다.

```bash
./scripts/check_intermediate_launch.sh --launch --nav2 false
```

검증은 entity, controller, `/clock`, sensor, command, odometry 준비 상태를 실제 runtime에서 확인한다. 종료 코드 0이 성공 조건이다.

## 4륜 rover launch와 모드 선택

4륜 예제는 같은 launch에서 Xacro만 선택한다. 실제 파일은 `examples/ros2_ws/src/tutorial_bot_bringup/launch/rover.launch.py`이다.

```python
drive_mode = LaunchConfiguration("drive_mode").perform(context)
if drive_mode not in {"diff", "ackermann"}:
    raise RuntimeError("drive_mode must be either 'diff' or 'ackermann'")

xacro_file = (
    description_share / "urdf" / "rovers" /
    f"rover_{drive_mode}.urdf.xacro"
)
```

다음 두 명령은 각각 4륜 skid-steer DiffDrive와 앞바퀴 조향 Ackermann 모델을 실행한다.

```bash
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=diff
ros2 launch tutorial_bot_bringup rover.launch.py drive_mode:=ackermann
```

두 모드 모두 ROS `/cmd_vel`, `/odom`, `/joint_states`, `/wheel_odom_path`와 RViz 설정을 같은 계약으로 제공한다. 따라서 주행 구조가 달라도 teleop과 궤적 확인 절차를 재사용할 수 있다.

## 문제 해결

- `PackageNotFoundError`가 나오면 `source examples/ros2_ws/install/setup.bash`를 실행한다.
- launch 파일을 수정했는데 반영되지 않으면 `colcon build` 후 설치 공간을 다시 source한다.
- GUI가 없는 환경에서는 `gui:=false rviz:=false`를 사용한다.
- spawn 뒤 stack이 종료되면 spawn process의 첫 오류와 return code를 먼저 확인한다.
- `/clock`이 멈추면 Gazebo가 pause 상태인지, bridge가 실행 중인지 확인한다.
- `drive_mode` 오타는 `diff` 또는 `ackermann` 중 하나로 고친다.

## 정리

Python launch는 Xacro 생성, 설치 리소스 조회, Gazebo 실행, spawn, bridge, controller, RViz, Nav2의 의존 관계를 코드로 표현한다. 인자를 검증하고 실제 준비 사건을 기준으로 다음 단계를 시작해야 실패 원인과 실행 순서를 재현할 수 있다.

[이전: URDF·Xacro·SDF](02-urdf-xacro-sdf.md) · [다음: Robot Spawn](04-spawn-model.md)
