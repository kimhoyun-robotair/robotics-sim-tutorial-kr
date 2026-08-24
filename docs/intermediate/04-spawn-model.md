# Robot Spawn과 위치

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** ROS 2 Launch

## 학습 목표

- `robot_description` 토픽으로 entity를 생성합니다.
- entity 이름, namespace, 초기 pose를 구분합니다.
- spawn 실패가 뒤 단계로 전파되지 않게 합니다.

## 배경 지식

`robot_state_publisher`는 Xacro에서 만든 description을 제공하고, `ros_gz_sim create`가 이를 Gazebo entity로 생성합니다. entity 이름은 Gazebo 내부 식별자이고 ROS namespace는 토픽과 node 범위를 나눕니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`

## 실행

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py world:=sensor-test nav2:=false gui:=false rviz:=false
```

별도 description을 직접 spawn할 때의 핵심 명령은 다음 형태입니다.

```bash
ros2 run ros_gz_sim create -name tutorial_bot -topic robot_description -z 0.12
```

## 결과 확인

```bash
gz model --list
```

목록에 `tutorial_bot`이 한 번 나타나야 합니다. 통합 검증은 spawn 뒤 controller manager 준비까지 확인합니다.

## 동작 원리

초기 `x`, `y`, `z`, yaw는 world frame 기준 spawn pose입니다. 동일 이름의 entity를 두 번 만들면 충돌하므로 다중 로봇에서는 고유 이름과 namespace를 함께 사용합니다.

## 문제 해결

entity가 나타나지 않으면 `robot_description` 토픽과 spawn 프로세스의 종료 코드를 확인합니다. 바닥에 끼이면 초기 `z`를 collision 높이보다 약간 크게 둡니다.

## 정리

spawn은 Xacro 원본을 Harmonic entity로 만드는 경계이며, 이름·namespace·pose를 명시적으로 관리해야 합니다.
