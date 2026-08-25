# URDF·Xacro·SDF 구분

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 고급 SDF

## 학습 목표

- URDF, Xacro, SDF의 책임을 구분합니다.
- 하나의 robot description 원본을 유지합니다.
- Xacro를 펼치고 SDF 변환 결과를 검사합니다.

## 배경 지식

URDF는 ROS의 link와 joint 중심 로봇 모델이고, Xacro는 URDF를 변수와 매크로로 생성합니다. SDF는 world, physics, sensor, Gazebo System까지 표현합니다. 이 저장소는 `tutorial_bot.urdf.xacro`를 로봇의 유일한 원본으로 사용하고 Gazebo 확장은 Xacro의 `<gazebo>` 요소로 연결합니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

## 실행

```bash
xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro > /tmp/tutorial_bot.urdf
gz sdf -p /tmp/tutorial_bot.urdf > /tmp/tutorial_bot.sdf
check_urdf /tmp/tutorial_bot.urdf
```

## 결과 확인

```bash
grep -E 'left_wheel_joint|right_wheel_joint|lidar_link' /tmp/tutorial_bot.urdf
grep -E 'gz_ros2_control|sensor' /tmp/tutorial_bot.sdf
```

필수 joint와 sensor가 보이고 명령이 0으로 끝나면 description 변환 경로가 정상입니다.

## 동작 원리

`robot_state_publisher`는 펼쳐진 URDF를 읽어 고정·가동 joint의 TF를 계산합니다. Gazebo Harmonic은 spawn 시 같은 description을 SDF로 변환해 collision, sensor, System 확장을 사용합니다.

<figure class="course-figure" id="intermediate-model-conversion">
  <img src="../../assets/intermediate/model-conversion.svg" alt="Xacro에서 URDF와 SDF로 변환되는 모델 책임 흐름도" loading="lazy">
  <figcaption>그림 1. Xacro 원본을 펼쳐 URDF 구조와 Gazebo SDF 확장으로 전달하는 변환 경로입니다.</figcaption>
</figure>

## 계산 예제: 변환 불변 조건

<div class="course-worked" data-worked-example="model-conversion">
변환 전후 joint 집합을 \(J_X\), \(J_U\), \(J_S\)라 하면 핵심 구조의 합격 조건은 \(\{left\_wheel,right\_wheel,lidar\}\subseteq J_X\cap J_U\cap J_S\)입니다. 위 `grep`은 이 교집합의 이름을 확인하고, `gz sdf -p` 결과에서 sensor와 `gz_ros2_control` 확장이 살아 있는지도 따로 확인합니다.
</div>

## 문제 해결

Xacro 인자 오류가 나면 파일 상단의 `xacro:arg` 이름을 확인합니다. Gazebo Classic 전용 `gazebo_ros` plugin을 추가하지 말고, Harmonic의 `gz_ros2_control`과 `ros_gz` 경로를 사용합니다.

[이전: 고급 SDF](01-advanced-sdf.md)

[다음: ROS 2 Launch](03-ros2-launch.md)

## 정리

URDF/Xacro는 로봇 구조의 원본이고 SDF는 world와 Gazebo 고유 기능을 맡습니다.
