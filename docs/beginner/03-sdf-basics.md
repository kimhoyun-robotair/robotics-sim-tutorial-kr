# SDF 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo GUI 기초

## 학습 목표

- SDF의 `world`, `model`, `link` 계층을 설명합니다.
- `visual`과 `collision`의 책임을 구분합니다.
- pose와 SI 단위를 올바르게 읽습니다.

## 선행 학습

[Gazebo GUI 기초](02-gui-basics.md)에서 `training_box`를 선택하고 Entity Tree와 Inspector의 이름·pose를 확인합니다.

## 배경 지식

SDF(Simulation Description Format)는 Gazebo가 world와 model을 읽는 XML 형식입니다. `world`는 시뮬레이션 환경 하나를, `model`은 이름 있는 물체 하나를, `link`는 질량과 형상을 가진 강체를 나타냅니다.

`visual`은 화면에 보이는 형상이고, `collision`은 물리 엔진이 충돌을 계산하는 형상입니다. 보이는 형상만 있으면 물체가 서로 통과하고, collision만 있으면 물리적으로 존재하지만 보이지 않습니다.

`<pose>`는 기본적으로 `x y z roll pitch yaw`이며, 위치 단위는 m, 회전 단위는 rad입니다. 예를 들어 `0 0 0.5 0 0 0`은 원점 위 0.5 m에 회전 없이 놓인 상태입니다.

\[
\mathrm{pose}=(x,\ y,\ z,\ \mathrm{roll},\ \mathrm{pitch},\ \mathrm{yaw}) \tag{1}
\]

`training_box`의 `<pose>1.5 0 0.5 0 0 0</pose>`를 대입하면 위치는 `(1.5, 0, 0.5)` m이고 회전은 `(0, 0, 0)` rad입니다. 초급에서는 이 여섯 값의 순서와 단위만 정확히 읽습니다.

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-sdf-hierarchy.svg" alt="SDF의 world model link 계층과 visual collision 및 pose 순서를 설명한 도식" loading="lazy">
  <figcaption>그림 1. SDF는 world, model, link 계층 아래에서 보이는 visual과 물리 collision을 분리합니다.</figcaption>
</figure>

## 예제 파일

다음 파일의 `training_box`는 visual, collision, inertial을 모두 갖는 동적 model입니다.

`examples/gazebo/worlds/first-world.sdf`

반대로 `ground`는 `<static>true</static>`이므로 중력의 영향을 받지 않는 바닥입니다.

다음은 실제 파일에서 역할을 읽는 최소 예입니다.

```xml
<model name="training_box">
  <pose>1.5 0 0.5 0 0 0</pose>
  <link name="link">
    <collision name="collision">...</collision>
    <visual name="visual">...</visual>
  </link>
</model>
```

## 확인

SDF를 실행하기 전에 검사합니다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

`Valid.`가 출력되면 다음 장으로 진행합니다.

## 예상 관찰

- 검사 성공 시 마지막에 `Valid.`가 출력됩니다.
- 파일에서 `ground`, `training_box`, `beacon`이라는 세 model 이름을 찾을 수 있습니다.
- `training_box`에는 `visual`과 `collision`이 모두 있고, `beacon`에는 화면에 보이는 `visual`이 있습니다.
- `training_box`의 x 위치 `1.5`와 `beacon`의 x 위치 `3`이 GUI의 좌우 배치와 대응합니다.

## 문제 해결

- XML 오류의 line 번호로 이동해 시작·종료 태그의 이름과 중첩을 확인합니다.
- `pose` 오류가 나면 값이 정확히 여섯 개인지, 쉼표 대신 공백을 사용했는지 확인합니다.
- `visual`은 보이지만 상자가 바닥을 통과하면 `collision`과 Physics System 선언을 확인합니다.

## 다음 단계

[첫 World](04-first-world.md)에서 이 SDF 파일을 GUI와 headless server로 실행합니다.
