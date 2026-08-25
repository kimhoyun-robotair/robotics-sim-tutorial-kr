# Gazebo GUI 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Sim 개요

## 학습 목표

- simulation time의 재생, 일시 정지, 한 단계 실행을 구분합니다.
- Entity Tree와 Component Inspector에서 entity 구성을 확인합니다.
- GUI에서 수정한 상태와 SDF 파일의 영속 상태를 구분합니다.

## 선행 학습

[Gazebo Sim 개요](01-gazebo-overview.md)에서 Server, GUI, simulation time의 역할을 확인합니다.

## 실행

저장소 루트에서 첫 world를 GUI로 엽니다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-gui-basics.svg" alt="Gazebo GUI의 Entity Tree와 3D View 및 Component Inspector를 표시한 주석 화면" loading="lazy">
  <figcaption>그림 1. 같은 entity를 Tree에서 선택하고 3D View와 Inspector에서 이름과 pose를 교차 확인합니다.</figcaption>
</figure>

## 실습

### 1. 재생과 일시 정지

재생 버튼을 눌러 상자 `training_box`가 중력에 따라 바닥에 놓이는 것을 확인합니다. 일시 정지 상태에서는 simulation time과 물리 상태가 진행하지 않습니다. 한 단계 실행은 물리 업데이트를 한 번만 진행하므로, 빠른 움직임을 관찰할 때 유용합니다.

### 2. Entity Tree 읽기

왼쪽의 Entity Tree에서 `ground`, `training_box`, `beacon`을 찾습니다. `training_box`를 펼치면 link와 그 아래의 visual, collision 구성을 확인할 수 있습니다.

### 3. Component Inspector 확인

`training_box`를 선택한 뒤 Component Inspector에서 pose를 확인합니다. pose는 `x y z roll pitch yaw` 순서이며, 단위는 m와 rad입니다. 시작 pose `1.5 0 0.5 0 0 0`은 world 원점에서 x축으로 1.5 m, z축으로 0.5 m 이동하고 회전하지 않은 상태입니다. Gazebo와 ROS는 오른손 좌표계를 사용합니다.

### 4. 편집 결과의 저장

Translate 또는 Rotate 도구로 entity를 옮길 수 있습니다. 이 변경은 실행 중인 world 상태이며, SDF 파일을 저장·수정하지 않으면 다음 실행에서 재현되지 않습니다. 학습 예제의 변경은 항상 `examples/gazebo/worlds/first-world.sdf`에 반영합니다.

## 예상 관찰

재생 중에도 `training_box`가 바닥을 통과하지 않고, Entity Tree와 Inspector에서 같은 model 이름을 확인할 수 있으면 정상입니다. 중력과 접촉이 계산된 뒤 z 값은 상자 중심이 바닥 위에 놓이는 값 근처에 머뭅니다. `beacon`은 `<static>true</static>`이므로 재생해도 위치가 바뀌지 않습니다.

## 개념 정리

Entity Tree는 "무엇이 있는가", 3D View는 "어디에 보이는가", Component Inspector는 "어떤 값으로 구성됐는가"에 답합니다. 세 패널의 model 이름을 맞춰 읽으면 다른 entity의 pose를 잘못 기록하는 실수를 줄일 수 있습니다.

## 문제 해결

- 패널이 보이지 않으면 오른쪽 위 플러그인 메뉴에서 Entity Tree 또는 Component Inspector를 다시 엽니다.
- 선택이 어렵다면 Entity Tree에서 `training_box` 이름을 먼저 클릭합니다.
- 이동한 상자가 재실행 뒤 원래 위치로 돌아가면 정상입니다. 영구 변경은 `examples/gazebo/worlds/first-world.sdf`의 `<pose>`에 기록해야 합니다.

## 다음 단계

[SDF 기초](03-sdf-basics.md)에서 방금 확인한 world 요소를 파일 구조와 연결합니다.
