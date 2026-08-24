# 자율주행 `tutorial_bot` 프로젝트

> **난이도:** 중급 프로젝트  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Nav2 연동

## 프로젝트 목표

하나의 Xacro 원본에서 시작한 `tutorial_bot`을 launch, `gz_ros2_control`, TF, LiDAR, odometry, Nav2까지 연결하고 pose goal을 반복해서 달성합니다.

```text
URDF/Xacro → Gazebo Harmonic → ros2_control
       └──── TF·LiDAR·odometry → Nav2 → 속도 명령
```

## 배경 지식

이 프로젝트는 앞선 열 장의 결과를 새 구현 없이 조립합니다. Gazebo Harmonic은 물리와 센서를, ROS 2 Jazzy는 description·TF·controller·navigation을 담당하며 `/clock`을 기준으로 같은 simulation 시간을 사용합니다.

## 예제 파일

- 전체 launch: `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`
- Nav2 설정: `examples/ros2_ws/src/tutorial_bot_bringup/config/nav2_params.yaml`
- 목표 pose: `examples/ros2_ws/src/tutorial_bot_bringup/config/project_goal.yaml`
- RViz 설정: `examples/ros2_ws/src/tutorial_bot_bringup/rviz/tutorial_bot.rviz`

## 실행

GUI로 전체 stack을 시작합니다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py gui:=true rviz:=true nav2:=true
```

재현 가능한 완료 검증은 저장소 루트에서 실행합니다.

```bash
./scripts/check_intermediate_nav2.sh --fresh-build --launch \
  --goal-name project_goal.yaml --repeat 3 \
  --position-tolerance 0.25 --yaw-tolerance 0.20
```

## 완료 조건

- 하나의 launch 명령으로 Gazebo, robot spawn, bridge, controller, RViz, Nav2가 시작됩니다.
- `map → odom → base_link`와 sensor link가 연결됩니다.
- controller와 Nav2 lifecycle node가 활성 상태입니다.
- 세 번의 `NavigateToPose`가 status 4로 성공합니다.
- 매 실행의 위치와 yaw 오차가 지정 허용치 이내입니다.

## 결과 확인

```bash
ros2 action list | grep navigate_to_pose
ros2 run tf2_ros tf2_echo map base_link
ros2 topic echo /scan --once
ros2 control list_controllers
```

## 동작 원리

로봇 구조는 URDF/Xacro가, world와 map은 SDF·map 파일이, 실행 순서는 launch가, 메시지 변환은 `ros_gz`가 담당합니다. 각 책임을 한 원본에만 두어 Gazebo와 ROS 모델의 불일치를 막습니다.

## 문제 해결

실패를 단순 재시작으로 덮지 말고 action status와 최종 pose를 확인합니다. `unreachable_goal.yaml`은 status 6 abort와 이후에도 살아 있는 `/scan`을 확인하는 의도된 fault 예제입니다.

## 정리

이 프로젝트는 Gazebo Classic이 아닌 Harmonic에서 실제 ROS 2 Jazzy 자율주행 데이터 흐름을 끝까지 검증합니다.
