# Gazebo Sim 개요와 GUI

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Harmonic 이해하기

## 학습 목표

- Play, Pause, 한 단계 실행의 차이를 설명합니다.
- Entity Tree와 Component Inspector로 world 구성을 확인합니다.
- 모델의 pose와 좌표계를 혼동하지 않습니다.

## 실행

다음 장의 예제를 GUI로 실행합니다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

## GUI에서 확인할 것

- 재생 버튼으로 simulation time이 진행하는지 확인합니다.
- Entity Tree에서 `ground`, `training_box`, `beacon` 모델을 펼칩니다.
- `training_box`를 선택하고 Component Inspector에서 pose와 충돌 구성을 읽습니다.
- Translate/Rotate 도구는 실행 중인 world의 상태를 바꾸므로, 학습용 변경은 SDF 파일에도 반영해야 재현됩니다.

## 동작 원리

실시간 계수(Real Time Factor)는 실제 시간에 대해 시뮬레이션이 진행하는 속도입니다. 값이 낮다고 단순히 GUI가 느린 것은 아닙니다. 물리 계산, 센서, 렌더링, 컴퓨터 자원을 함께 점검해야 합니다.

## 다음 단계

[GUI 기초](02-gui-basics.md)에서 조작을 익힌 뒤, [SDF 기초](03-sdf-basics.md)에서 GUI에 표시되는 entity를 직접 정의합니다.
