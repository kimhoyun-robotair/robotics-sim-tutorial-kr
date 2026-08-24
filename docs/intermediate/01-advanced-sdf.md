# 고급 SDF와 물리 속성

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** SDF 기초

## 학습 목표

- SDF의 frame과 상대 pose를 읽습니다.
- world, model, link, joint의 역할을 구분합니다.
- collision, inertia, friction이 시뮬레이션 결과에 미치는 영향을 이해합니다.

## 배경 지식

SDF는 Gazebo world와 물리·센서·plugin을 풍부하게 표현합니다. `relative_to`는 pose의 기준 frame을 명시하고, `<include>`는 Fuel 또는 로컬 모델을 재사용합니다. 시각 형상과 collision 형상은 서로 다를 수 있지만, 관성값과 collision을 생략하면 물리 결과를 신뢰하기 어렵습니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`

이 파일은 Harmonic용 SDF world입니다. 로봇 본체의 원본은 이 파일이 아니라 다음 Xacro입니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

## 실행

```bash
gz sdf -k examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
gz sim -s examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
```

## 결과 확인

첫 명령이 오류 없이 끝나면 SDF 구조가 유효합니다. 두 번째 명령은 server를 실행하며, 다른 터미널에서 아래 명령으로 world를 확인할 수 있습니다.

```bash
gz service -l | grep /world/training
```

## 동작 원리

frame은 좌표 기준을 이름으로 분리하고, pose는 그 기준에 대한 위치와 자세를 정합니다. mesh와 material은 표시를, collision과 inertia는 물리를 담당합니다. friction과 joint limit은 접촉 및 운동 범위를 제한합니다.

## 문제 해결

`model://` URI를 찾지 못하면 `GZ_SIM_RESOURCE_PATH`를 확인합니다. Gazebo Classic의 `GAZEBO_MODEL_PATH`와 혼동하지 마십시오. pose가 예상과 다르면 `relative_to` 대상이 같은 scope에 존재하는지 먼저 확인합니다.

[다음: URDF·Xacro·SDF 역할 나누기](02-urdf-xacro-sdf.md)

## 정리

SDF는 Harmonic의 world와 Gazebo 전용 기능의 원본이며, `tutorial_bot`의 중복 로봇 원본은 아닙니다.
