# Gazebo GUI 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Sim 개요

## 학습 목표

- simulation time의 재생, 일시 정지, 한 단계 실행을 구분한다.
- Entity Tree와 Component Inspector에서 같은 entity를 교차 확인한다.
- GUI의 임시 상태와 SDF에 저장한 상태를 구분한다.

## 실행

저장소 루트에서 첫 world를 연다. `-r`을 생략하면 일시 정지 상태로 시작하므로 한 단계 실행을 관찰하기 쉽다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-gui-basics.svg" alt="Gazebo GUI의 Entity Tree와 3D View 및 Component Inspector를 표시한 주석 화면" loading="lazy">
  <figcaption>그림 1. 같은 entity를 Tree에서 선택하고 3D View와 Inspector에서 이름과 pose를 교차 확인한다.</figcaption>
</figure>

## 실습 1: 재생·정지·한 단계 실행

`training_box`는 다음 pose에서 시작한다.

```xml
<model name="training_box">
  <pose>1.5 0 0.5 0 0 0</pose>
  <!-- link 정의는 생략한다. -->
</model>
```

1. Pause 상태에서 `training_box`의 z 값을 기록한다.
2. Step 버튼을 한 번 누르고 z 값이 아주 작게 변하는지 확인한다.
3. Play를 눌러 상자가 바닥에 놓일 때까지 진행한다.
4. Pause를 눌러 simulation time과 pose가 함께 멈추는지 확인한다.

GUI 대신 service로 같은 상태 전이를 재현할 수도 있다.

```bash
# 일시 정지
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'pause: true'

# 물리 update 한 번 실행
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'step: true'

# 다시 재생
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'pause: false'
```

## 실습 2: Entity Tree와 Inspector 연결하기

왼쪽 Entity Tree에서 `training_box`를 펼친다. model 아래의 `link`, 그 아래의 `visual`과 `collision`이 SDF의 다음 계층과 대응한다.

```xml
<model name="training_box">
  <link name="link">
    <collision name="collision"> ... </collision>
    <visual name="visual"> ... </visual>
  </link>
</model>
```

Component Inspector의 pose는 `x y z roll pitch yaw` 순서이고 위치 단위는 m, 회전 단위는 rad이다. `1.5 0 0.5 0 0 0`은 world 원점에서 x축으로 1.5 m, z축으로 0.5 m 이동하고 회전하지 않은 상태이다.

## 실습 3: 임시 변경과 영속 변경 비교하기

Translate 도구로 `training_box`를 x=2.0 m 근처로 옮긴 뒤 Gazebo를 종료하고 다시 실행한다. 모델은 SDF에 적힌 x=1.5 m로 돌아온다.

영속적으로 바꾸려면 다음처럼 원본의 pose를 수정해야 한다.

```xml
<!-- examples/gazebo/worlds/first-world.sdf -->
<model name="training_box">
  <pose>2.0 0 0.5 0 0 0</pose>
  ...
</model>
```

수정 후에는 실행 전에 문법을 검사한다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

## 예상 관찰

- Step 한 번은 물리 update를 한 번만 진행한다.
- Play 상태에서 상자는 바닥 위에 놓이고, `<static>true</static>`인 `beacon`은 움직이지 않는다.
- Entity Tree와 Inspector에서 선택한 model 이름이 일치한다.
- GUI로만 옮긴 pose는 재실행하면 사라지고, SDF에 기록한 pose는 재현된다.

## 문제 해결

- 패널이 보이지 않으면 오른쪽 위 플러그인 메뉴에서 Entity Tree 또는 Component Inspector를 다시 연다.
- 선택이 어렵다면 3D View가 아니라 Entity Tree에서 `training_box`를 먼저 클릭한다.
- control service가 없으면 world가 완전히 시작됐는지와 world 이름을 `gz service -l`로 확인한다.
- 상자가 바닥을 통과하면 collision과 Physics System 선언을 함께 확인한다.

[다음: SDF 기초](03-sdf-basics.md)
