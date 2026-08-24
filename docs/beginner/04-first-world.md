# 첫 World 실행하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** SDF 기초

## 학습 목표

- 중력·충돌을 가진 정적 바닥과 동적 상자를 구분합니다.
- GUI 없이 server를 시작해 예제를 검증합니다.

## 배경 지식

이 장은 [SDF 기초](03-sdf-basics.md)의 요소를 사용해 실제 world를 실행합니다. 예제의 상자는 `z=0.5`에서 시작해 바닥 위에 놓입니다.

## 실습

이번 장에서 사용하는 파일은 다음입니다.

`examples/gazebo/worlds/first-world.sdf`

먼저 SDF 문법과 의미를 검사합니다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

GUI를 열어 world를 확인합니다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

서버만 실행하려면 다음을 사용합니다. 종료는 `Ctrl+C`입니다.

```bash
gz sim -s examples/gazebo/worlds/first-world.sdf
```

## 결과 확인

GUI에는 큰 바닥, 빨간 상자 `training_box`, 파란 원통 `beacon`이 보입니다. 재생하면 상자는 중력으로 바닥 위에 머뭅니다. 상자에 collision이 없다면 바닥을 통과하고, 바닥이 static이 아니면 바닥도 중력의 영향을 받습니다.

## 동작 원리

World 안의 Physics System이 중력과 접촉을 계산하고, SceneBroadcaster System이 GUI에 entity 상태를 전달합니다. 이 예제는 외부 모델·mesh를 사용하지 않아 resource path 설정 없이 재현됩니다.

## 자주 발생하는 문제

- `gz sdf -k`가 실패하면 오류에 표시된 XML 요소와 닫는 태그부터 확인합니다.
- server는 시작하지만 GUI가 열리지 않으면 [문제 해결](../getting-started/troubleshooting.md)의 GUI 항목을 확인합니다.
- 실행 위치가 저장소 루트가 아니면 상대 경로가 달라집니다. `pwd`를 실행해 확인하세요.

## 정리

첫 world는 SDF로 정의했고, visual과 collision의 역할을 분리했습니다. 다음 단계에서는 [첫 Robot](05-first-robot.md)에서 URDF/Xacro의 `tutorial_bot` 원본을 만듭니다.
