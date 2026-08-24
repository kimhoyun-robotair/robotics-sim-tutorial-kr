# SDF 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo GUI 기초

## 학습 목표

- SDF의 `world`, `model`, `link` 계층을 설명합니다.
- `visual`과 `collision`의 책임을 구분합니다.
- pose와 SI 단위를 올바르게 읽습니다.

## 배경 지식

SDF(Simulation Description Format)는 Gazebo가 world와 model을 읽는 XML 형식입니다. `world`는 시뮬레이션 환경 하나를, `model`은 이름 있는 물체 하나를, `link`는 질량과 형상을 가진 강체를 나타냅니다.

`visual`은 화면에 보이는 형상이고, `collision`은 물리 엔진이 충돌을 계산하는 형상입니다. 보이는 형상만 있으면 물체가 서로 통과하고, collision만 있으면 물리적으로 존재하지만 보이지 않습니다.

`<pose>`는 기본적으로 `x y z roll pitch yaw`이며, 위치 단위는 m, 회전 단위는 rad입니다. 예를 들어 `0 0 0.5 0 0 0`은 원점 위 0.5 m에 회전 없이 놓인 상태입니다.

## 예제 파일

다음 파일의 `training_box`는 visual, collision, inertial을 모두 갖는 동적 model입니다.

`examples/gazebo/worlds/first-world.sdf`

반대로 `ground`는 `<static>true</static>`이므로 중력의 영향을 받지 않는 바닥입니다.

## 확인

SDF를 실행하기 전에 검사합니다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

`Valid.`가 출력되면 다음 장으로 진행합니다.

## 다음 단계

[첫 World](04-first-world.md)에서 이 SDF 파일을 GUI와 headless server로 실행합니다.
