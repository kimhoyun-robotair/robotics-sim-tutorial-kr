# Gazebo Sim 개요와 GUI

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo Harmonic 이해하기

## 학습 목표

- Play, Pause, 한 단계 실행의 차이를 설명합니다.
- Entity Tree와 Component Inspector로 world 구성을 확인합니다.
- 모델의 pose와 좌표계를 혼동하지 않습니다.

## 선행 학습

[Gazebo Harmonic 소개](../getting-started/gazebo-harmonic.md)를 읽고 `gz sim --versions`가 실행되는 환경을 준비합니다. 실습은 저장소 루트에서 진행합니다.

## 실행

다음 장의 예제를 GUI로 실행합니다.

```bash
gz sim examples/gazebo/worlds/first-world.sdf
```

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-gazebo-overview.svg" alt="Gazebo Server와 GUI의 상태 및 명령 흐름과 RTF 표시를 설명한 도식" loading="lazy">
  <figcaption>그림 1. Server는 물리와 simulation time을 계산하고 GUI는 상태를 보여 주며 명령을 전달합니다.</figcaption>
</figure>

## GUI에서 확인할 것

- 재생 버튼으로 simulation time이 진행하는지 확인합니다.
- Entity Tree에서 `ground`, `training_box`, `beacon` 모델을 펼칩니다.
- `training_box`를 선택하고 Component Inspector에서 pose와 충돌 구성을 읽습니다.
- Translate/Rotate 도구는 실행 중인 world의 상태를 바꾸므로, 학습용 변경은 SDF 파일에도 반영해야 재현됩니다.

## 개념: Server와 GUI

한 번의 `gz sim` 명령이 두 역할을 함께 시작합니다. Server는 `examples/gazebo/worlds/first-world.sdf`를 읽고 물리 상태를 계산합니다. GUI는 그 상태를 3D 화면과 패널에 표시하고 Play·Pause 같은 사용자 명령을 Server에 전달합니다. 따라서 GUI 창을 움직이는 것과 simulation time이 진행하는 것은 서로 다른 일입니다.

## RTF 읽기

실시간 계수(Real Time Factor, RTF)는 실제 경과 시간에 대한 simulation time의 비율입니다.

\[
\mathrm{RTF}=\frac{\Delta t_{sim}}{\Delta t_{real}} \tag{1}
\]

예를 들어 실제로 5초가 지나는 동안 simulation time이 4초 증가했다면 `RTF = 4 / 5 = 0.8`입니다. `RTF ≈ 1.0`이면 실제 시간과 비슷하게 진행하고, `RTF = 0`이면 보통 일시 정지 상태입니다. 값이 낮을 때는 GUI만 탓하지 말고 물리 계산, 센서, 렌더링, 컴퓨터 자원을 함께 점검합니다.

## 예상 관찰

- GUI 상단 제어 영역에 Play·Pause가 보이고 재생할 때 simulation time이 증가합니다.
- Entity Tree에 `ground`, `training_box`, `beacon`이 표시됩니다.
- Pause를 누르면 화면 카메라는 조작할 수 있어도 물리 상태와 simulation time은 멈춥니다.
- RTF는 부하에 따라 조금 변할 수 있으므로 정확히 `1.0`이어야 하는 합격 조건은 아닙니다.

## 문제 해결

- `Unable to find or download file`이 나오면 저장소 루트에서 명령을 실행했는지 `pwd`로 확인합니다.
- GUI 창이 뜨지 않으면 `gz sim -s examples/gazebo/worlds/first-world.sdf`로 Server가 시작되는지 분리해서 확인하고 [문제 해결](../getting-started/troubleshooting.md)을 참고합니다.
- RTF가 계속 낮으면 일시 정지 여부를 먼저 확인한 뒤 센서·렌더링 부하를 줄여 원인을 나눠 봅니다.

## 다음 단계

[GUI 기초](02-gui-basics.md)에서 조작을 익힌 뒤, [SDF 기초](03-sdf-basics.md)에서 GUI에 표시되는 entity를 직접 정의합니다.
