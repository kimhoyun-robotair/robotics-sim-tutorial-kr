# 바퀴와 Joint 추가하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 첫 `tutorial_bot`

## 학습 목표

- link와 joint가 로봇의 강체 구조를 어떻게 연결하는지 설명합니다.
- `tutorial_bot`에 좌우 바퀴 link와 continuous joint를 추가합니다.
- joint axis와 joint limit을 목적에 맞게 선택합니다.

## 배경 지식

Joint는 parent link와 child link의 상대 운동을 정의합니다. `fixed` joint는 상대 운동을 허용하지 않고, `revolute` joint는 제한된 범위 안에서 한 축 회전을 허용합니다. 바퀴처럼 회전 범위가 제한되지 않는 구조에는 `continuous` joint를 사용합니다.

이번 바퀴 joint의 axis는 `0 1 0`입니다. 즉, 각 바퀴의 축은 robot의 y축 방향이고 바퀴는 그 축을 중심으로 회전합니다. `continuous` joint에는 upper/lower limit을 넣지 않습니다. 회전 각도를 제한해야 하는 arm 또는 lidar tilt joint에는 `revolute` joint와 limit을 사용합니다.

## 예제 파일

이번 장에서 수정하는 Xacro 원본은 다음입니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/stages/02-wheels-and-joints.xacro`

이 파일의 `wheel` 매크로는 왼쪽과 오른쪽에 같은 원통 link를 만들고, y 위치만 다르게 지정합니다. 바퀴의 질량은 0.3 kg, 반지름은 0.06 m, 폭은 0.04 m입니다.

## 실행

Xacro를 다시 확장한 뒤 두 child link와 두 joint가 생성됐는지 확인합니다.

```bash
source /opt/ros/jazzy/setup.zsh
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/02-wheels-and-joints.xacro"
xacro "$stage" > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
```

## 결과 확인

출력에 다음 구조가 나타나면 정상입니다.

```text
root Link: base_link has 2 child(ren)
    child(1): left_wheel_link
    child(2): right_wheel_link
```

생성된 URDF를 Gazebo가 읽을 수 있는 SDF로 변환해도 됩니다.

```bash
gz sdf -p /tmp/tutorial_bot.urdf > /tmp/tutorial_bot.sdf
gz sdf -k /tmp/tutorial_bot.sdf
```

## 동작 원리

바퀴 geometry는 URDF cylinder의 기본 축인 z축을 x축으로 90° 회전해 y축을 따라 놓습니다. joint axis도 y축으로 맞추므로, visual·collision·관성·joint가 같은 물리적 바퀴를 설명합니다.

## 정리

`tutorial_bot`은 이제 base link, left wheel, right wheel로 구성됩니다. 다음 단계에서는 [DiffDrive](07-diff-drive.md)를 연결해 속도 명령으로 로봇을 움직입니다.
