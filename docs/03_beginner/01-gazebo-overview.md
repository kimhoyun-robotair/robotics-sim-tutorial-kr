# Gazebo Sim 개요와 GUI

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Harmonic 이해하기

## 학습 목표

- Server와 GUI의 책임을 구분한다.
- Play, Pause, 한 단계 실행이 simulation time에 미치는 영향을 설명한다.
- Entity Tree와 Component Inspector에서 model, link, pose를 교차 확인한다.
- RTF를 읽고 계산 부하와 simulation 속도의 관계를 설명한다.

## Gazebo는 무엇을 실행하는가

Gazebo Sim은 하나의 프로그램처럼 보이지만, 실행 중에는 Server와 GUI가 역할을 나눠 가진다. Server는 SDF를 읽고 물리·센서·System을 갱신한다. GUI는 Server가 만든 entity와 상태를 화면에 표시하고 사용자 명령을 전달한다. 따라서 GUI 카메라를 움직이는 일과 simulation time을 진행하는 일은 서로 다르다.

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-gazebo-overview.svg" alt="Gazebo Server와 GUI의 상태 및 명령 흐름과 RTF 표시를 설명한 도식" loading="lazy">
  <figcaption>그림 1. Server가 물리와 simulation time을 계산하고, GUI가 상태를 표시하며 조작 명령을 전달한다.</figcaption>
</figure>

`first-world.sdf`에는 Server가 불러올 System이 실제 XML로 선언되어 있다.

```xml
<plugin filename="gz-sim-physics-system"
        name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-user-commands-system"
        name="gz::sim::systems::UserCommands"/>
<plugin filename="gz-sim-scene-broadcaster-system"
        name="gz::sim::systems::SceneBroadcaster"/>
```

- `Physics`는 중력, 관성, 충돌, joint 운동을 계산한다.
- `UserCommands`는 GUI나 service에서 들어오는 생성·이동·삭제 명령을 처리한다.
- `SceneBroadcaster`는 GUI가 장면을 그릴 수 있도록 entity 상태를 전달한다.

## 실행하고 관찰하기

저장소 루트에서 world를 일시 정지 상태로 열고 GUI의 Play를 누른다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

다른 terminal에서는 실행 중인 world가 내보내는 상태 topic을 찾는다.

```bash
gz topic -l | grep '/world/first_world/'
gz topic -e -t /world/first_world/stats -n 1
```

`stats` 메시지에서 `sim_time`, `real_time`, `paused`를 찾을 수 있다. GUI의 Pause를 누른 뒤 같은 명령을 다시 실행하면 `paused: true`가 되고 `sim_time` 증가가 멈춘다.

GUI 없이 Server만 분리해 확인하려면 다음 명령을 사용한다.

```bash
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

Server-only 실행에서도 `/world/first_world/stats`가 발행된다. 이 결과는 물리 계산이 GUI 렌더링과 독립적으로 동작한다는 증거이다.

## GUI에서 확인할 항목

1. Play와 Pause를 번갈아 눌러 simulation time의 변화를 확인한다.
2. Entity Tree에서 `ground`, `training_box`, `beacon`을 찾는다.
3. `training_box`를 펼쳐 `link`, `visual`, `collision`을 확인한다.
4. Component Inspector에서 pose `1.5 0 0.5 0 0 0`과 화면 위치를 연결한다.
5. Translate 도구로 상자를 옮긴 뒤 world를 다시 열어 원래 위치로 돌아오는지 확인한다.

GUI에서 바꾼 pose는 실행 중인 상태만 바꾼다. 재실행해도 같은 결과를 얻으려면 `examples/gazebo/worlds/first-world.sdf`의 `<pose>`를 수정해야 한다.

## RTF 읽기

실시간 계수(Real Time Factor, RTF)는 실제 경과 시간에 대한 simulation time의 비율이다.

\[
\mathrm{RTF}=\frac{\Delta t_{sim}}{\Delta t_{real}} \tag{1}
\]

실제로 5초가 지나는 동안 simulation time이 4초 증가했다면 `RTF = 4 / 5 = 0.8`이다. `RTF ≈ 1.0`이면 실제 시간과 비슷하게 진행하고, `RTF = 0`이면 대개 일시 정지 상태이다. RTF가 낮으면 물리 step, 센서 update rate, 렌더링 해상도, CPU·GPU 부하를 함께 점검한다.

## 예상 관찰

- 재생 중에는 `sim_time`이 증가하고 Pause 상태에서는 멈춘다.
- Entity Tree에 `ground`, `training_box`, `beacon`이 나타난다.
- Pause 상태에서도 GUI 카메라는 이동할 수 있지만 상자의 물리 상태는 변하지 않는다.
- Server-only 모드에서도 world service와 stats topic은 존재한다.

## 문제 해결

- `Unable to find or download file`이 나오면 저장소 루트에서 실행했는지 `pwd`로 확인한다.
- GUI가 뜨지 않으면 `gz sim -s ...`로 Server 시작 여부를 먼저 분리해 확인한다.
- stats topic이 없으면 world 이름이 `first_world`인지 `gz topic -l`에서 다시 확인한다.
- RTF가 계속 낮으면 Pause 여부를 먼저 확인한 뒤 센서·렌더링 부하를 줄여 원인을 분리한다.

[다음: Gazebo GUI 기초](02-gui-basics.md)
