# Gazebo GUI 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Sim 개요

## 학습 목표

- 시뮬레이션 시간의 재생, 일시 정지, 한 단계 실행을 구분한다.
- Entity Tree와 Component Inspector에서 같은 개체를 교차 확인한다.
- GUI의 임시 상태와 SDF에 저장한 상태를 구분한다.

## 실행

저장소 루트에서 첫 월드를 연다. `-r`을 생략하면 일시 정지 상태로 시작하므로 한 단계 실행을 관찰하기 쉽다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
gz sim examples/gazebo/worlds/first-world.sdf
```

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-gui-basics.svg" alt="Gazebo GUI의 Entity Tree와 3D View 및 Component Inspector를 표시한 주석 화면" loading="lazy">
  <figcaption>그림 1. 같은 entity를 Tree에서 선택하고 3D View와 Inspector에서 이름과 pose를 교차 확인한다.</figcaption>
</figure>

## 실습 1: 재생·정지·한 단계 실행

`training_box`는 다음 위치와 자세에서 시작한다.

```xml
<model name="training_box">
  <pose>1.5 0 0.5 0 0 0</pose>
  <!-- link 정의는 생략한다. -->
</model>
```

상자는 높이가 1 m이고 중심이 z=0.5 m이므로 처음부터 바닥에 닿아 있다. 한 단계 실행을 확인할 때는 낙하량이 아니라 시간을 관찰한다.

1. 일시 정지 상태에서 GUI의 시뮬레이션 시간을 기록한다.
2. Step의 단계 수를 1로 두고 버튼을 한 번 누른다. 시간은 0.001초만 진행하고 다시 멈춰야 한다.
3. 낙하를 보고 싶다면 정지 상태에서 `training_box`를 선택하고 Translate 도구의 z축 화살표로 바닥에서 들어 올린다.
4. Play를 눌러 상자가 바닥으로 떨어지는지 확인한 뒤 Pause를 누른다.

새 터미널에서 서비스로도 같은 동작을 실행할 수 있다. 각 명령의 `data: true`는 요청을 받아들였다는 뜻이다.

```bash
# 일시 정지
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'pause: true'

# 물리 계산 한 번 실행
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'step: true'

# 다시 재생
gz service -s /world/first_world/control \
  --reqtype gz.msgs.WorldControl --reptype gz.msgs.Boolean \
  --timeout 1000 --req 'pause: false'
```

## 실습 2: Entity Tree와 Inspector 연결하기

Entity Tree 패널에서 `training_box`를 펼친다. 모델 아래의 `link`, 그 아래의 `visual`과 `collision`이 SDF의 다음 계층과 대응한다.

```xml
<model name="training_box">
  <link name="link">
    <collision name="collision"> ... </collision>
    <visual name="visual"> ... </visual>
  </link>
</model>
```

SDF의 `<pose>`는 `x y z roll pitch yaw` 순서이며 위치는 m, 회전은 rad 단위이다. Component Inspector에서 같은 위치를 확인하되 회전값을 입력할 때는 GUI에 표시된 단위도 확인한다. `1.5 0 0.5 0 0 0`은 월드 원점에서 x축으로 1.5 m, z축으로 0.5 m 이동하고 회전하지 않은 상태이다.

## 실습 3: 임시 변경과 파일에 저장한 변경 비교하기

Translate 도구로 `training_box`를 x=2.0 m 근처로 옮긴 뒤 Gazebo를 종료하고 다시 실행한다. 모델은 SDF에 적힌 x=1.5 m로 돌아온다.

재실행 후에도 유지하려면 다음처럼 원본의 위치와 자세를 수정해야 한다.

```xml
<!-- examples/gazebo/worlds/first-world.sdf -->
<model name="training_box">
  <pose>2.0 0 0.5 0 0 0</pose>
  ...
</model>
```

코드의 `...`는 생략 표시이므로 파일에 붙여 넣지 않는다. 기존 `<pose>` 한 줄만 수정한 뒤 문법을 검사한다. 다음 장은 원래 위치를 사용하므로 실험을 마치면 x 값을 `1.5`로 되돌린다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

## 예상 관찰

- Step의 단계 수가 1이면 물리 계산을 한 번만 진행한다.
- Play 상태에서 상자는 바닥 위에 놓이고, `<static>true</static>`인 `beacon`은 움직이지 않는다.
- Entity Tree와 Inspector에서 선택한 모델 이름이 일치한다.
- GUI로만 옮긴 위치와 자세는 재실행하면 사라지고, SDF에 기록한 위치와 자세는 재현된다.

## 문제 해결

- 패널이 보이지 않으면 오른쪽 위 플러그인 메뉴에서 Entity Tree 또는 Component Inspector를 다시 연다.
- 선택이 어렵다면 3D View가 아니라 Entity Tree에서 `training_box`를 먼저 클릭한다.
- 월드 제어 서비스가 없으면 월드가 완전히 시작됐는지와 월드 이름을 `gz service -l`로 확인한다.
- 상자가 바닥을 통과하면 collision과 Physics 시스템 선언을 함께 확인한다.

[다음: SDF 기초](03-sdf-basics.md)
