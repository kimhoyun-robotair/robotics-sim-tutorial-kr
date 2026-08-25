# ROS 2 Launch 실행

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** URDF·Xacro·SDF

## 학습 목표

- Python launch의 선언 인자와 실행 순서를 읽습니다.
- Gazebo, spawn, bridge, controller, RViz, Nav2를 한 명령으로 시작합니다.
- 설치된 package share의 리소스를 사용합니다.

## 배경 지식

launch 파일은 단순 명령 모음이 아니라 프로세스 의존 관계를 표현합니다. 이 예제는 spawn 성공 뒤 controller 준비를 이어 실행하고, 리소스가 없거나 인자가 잘못되면 조기에 실패합니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`

## 실행

워크스페이스를 source한 터미널에서 실행합니다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py nav2:=false gui:=false rviz:=false
```

전체 자동 검증은 저장소 루트에서 실행합니다.

```bash
./scripts/check_intermediate_launch.sh --launch --nav2 false
```

## 결과 확인

검증은 entity, controller, `/clock`, 센서, 명령과 odometry 준비 상태를 실제 런타임에서 확인합니다. 종료 코드 0이 성공 조건입니다.

## 동작 원리

launch는 설치된 `tutorial_bot_gazebo`, `tutorial_bot_description`, `tutorial_bot_control`, `tutorial_bot_bringup` share를 조회합니다. source tree의 우연한 상대 경로가 아니라 설치 결과를 소비하므로 배포 형태도 검증됩니다.

<figure class="course-figure" id="intermediate-launch-readiness">
  <img src="../../assets/intermediate/launch-readiness.svg" alt="Gazebo 준비부터 Nav2 활성까지의 launch readiness 의존 그래프" loading="lazy">
  <figcaption>그림 1. launch는 고정 sleep이 아니라 실제 준비 사건으로 다음 프로세스를 시작합니다.</figcaption>
</figure>

## 계산 예제: 준비 시간의 상한

<div class="course-worked" data-worked-example="launch-readiness">
단계별 준비 시간을 \(t_g,t_s,t_c,t_b\)라 하면 직렬 임계 경로는 \(T=t_g+t_s+t_c+t_b\)입니다. 측정값이 각각 6, 2, 4, 1초라면 13초입니다. 모든 단계에 무조건 10초 sleep을 넣은 40초와 달리 readiness 방식은 빠른 환경에서 즉시 진행하고, 어느 단계가 timeout인지도 보존합니다.
</div>

현재 runtime 계약은 `check_intermediate_launch.sh`가 entity, controller, `/clock`, sensor, command와 odometry를 각각 파싱해 모두 관측된 경우에만 종료 코드 0을 냅니다.

## 문제 해결

`PackageNotFoundError`가 나오면 `source examples/ros2_ws/install/setup.bash`를 실행합니다. GUI가 없는 환경에서는 `gui:=false rviz:=false`로 시작합니다.

## 정리

한 launch 명령이 Harmonic과 ROS 2 Jazzy의 실행 순서 및 실패 전파를 담당합니다.
