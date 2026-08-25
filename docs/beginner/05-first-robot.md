# Xacro로 `tutorial_bot` 만들기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 첫 World

## 학습 목표

- URDF와 Xacro의 역할을 구분합니다.
- `tutorial_bot`의 첫 base link를 Xacro로 관리합니다.
- 생성된 URDF가 올바른 링크 구조인지 검사합니다.

## 배경 지식

URDF는 ROS 2에서 robot description을 표현하는 XML 형식입니다. Xacro는 URDF를 생성할 때 반복되는 값과 구조를 정리하는 매크로 언어입니다. 이 저장소에서는 Xacro를 로봇 형상의 원본으로 사용합니다.

Gazebo에 필요한 world, physics, sensor와 plugin 설정은 이후 SDF에 추가합니다. 같은 로봇을 별도의 SDF 원본으로 다시 작성하지 않습니다.

## 예제 파일

이번 장의 원본은 다음 파일입니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/stages/01-base.xacro`

`base_link`는 0.45 m × 0.32 m × 0.12 m 직육면체 몸체입니다. visual과 collision을 같은 단순 형상으로 시작하고, 관성은 질량 5 kg에 맞는 직육면체 근사값을 사용합니다.

## 실행

저장소 루트에서 Xacro를 URDF로 확장한 뒤 구조를 검사합니다.

```bash
source /opt/ros/jazzy/setup.zsh
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/01-base.xacro"
xacro "$stage" > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

Bash를 사용한다면 첫 줄을 `source /opt/ros/jazzy/setup.bash`로 바꿉니다.

## 결과 확인

`check_urdf` 출력에 `root Link: base_link`가 보이고 오류가 없으면 Xacro가 올바른 단일 link URDF를 만들었습니다.

## ROS 2 package 확인

Xacro 파일은 실제 ROS 2 package에도 설치됩니다. 현재 PC처럼 여러 Python 설치가 공존하면 ROS 2 Jazzy가 사용하는 시스템 Python을 명시해 빌드합니다.

```bash
cd examples/ros2_ws
colcon build --packages-select tutorial_bot_description --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.zsh
ros2 pkg prefix tutorial_bot_description
```

마지막 명령이 `install/tutorial_bot_description` 경로를 출력하면 package resource 설치까지 완료된 것입니다.

## 동작 원리

Xacro 파일의 `box_inertia` 매크로는 직육면체의 질량과 크기에서 관성 텐서를 계산합니다. 이 값은 이후 Gazebo가 로봇의 가속과 충돌을 계산할 때 사용합니다. 초급 확장 단계에서는 같은 Xacro 원본에 바퀴 link와 revolute joint를 더해 `tutorial_bot`을 이동 가능한 로봇으로 발전시킵니다.

## 정리

이 장에서는 `tutorial_bot`의 base link와 관성 값을 Xacro 원본으로 만들었습니다. 바퀴와 관절은 초급 확장 단계에서 같은 Xacro 파일에 추가합니다.

## 다음 단계

[바퀴와 Joint](06-joints.md)에서 좌우 바퀴 link와 continuous joint를 추가합니다.
