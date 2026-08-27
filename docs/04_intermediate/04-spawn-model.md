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

<figure class="course-figure" id="intermediate-spawn-pose">
  <img src="../../assets/intermediate/spawn-pose.svg" alt="world 좌표계에서 로봇의 위치와 yaw로 표현한 spawn pose" loading="lazy">
  <figcaption>그림 1. spawn pose는 world 기준 위치와 yaw이며 entity 이름과 ROS namespace는 별도 계약입니다.</figcaption>
</figure>

## 계산 예제: 바닥과 겹치지 않는 높이

<div class="course-worked" data-worked-example="spawn-pose">
본체 collision 높이가 0.20 m이고 바닥 여유를 0.02 m로 두면 중심의 최소 spawn 높이는 \(z_{min}=0.20/2+0.02=0.12\,\mathrm{m}\)입니다. 따라서 예제의 `-z 0.12`는 collision이 바닥 아래에서 시작하지 않게 합니다. yaw \(\psi\)의 진행 방향은 \((\cos\psi,\sin\psi)\)로 읽습니다.
</div>

## 문제 해결

entity가 나타나지 않으면 `robot_description` 토픽과 spawn 프로세스의 종료 코드를 확인합니다. 바닥에 끼이면 초기 `z`를 collision 높이보다 약간 크게 둡니다.

## 정리

spawn은 Xacro 원본을 Harmonic entity로 만드는 경계이며, 이름·namespace·pose를 명시적으로 관리해야 합니다.

[이전: ROS 2 Launch](03-ros2-launch.md) · [다음: ros_gz_bridge 심화](05-bridge-yaml.md)
