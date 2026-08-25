# Xacro로 `tutorial_bot` <span class="course-nowrap">만들기</span>

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [첫 World](04-first-world.md)

## 학습 목표

- URDF, Xacro, SDF가 맡는 일을 구분합니다.
- 설치된 1단계 Xacro에서 `base_link`를 생성하고 검사합니다.
- 모델의 질량과 크기로 직육면체 관성 모멘트를 계산합니다.

## 하나의 로봇, 세 가지 표현

<figure markdown="span">
  ![Xacro 원본이 URDF를 거쳐 Gazebo의 SDF 모델로 변환되는 흐름](../assets/beginner/robot-format-flow.svg)
  <figcaption>그림 1. 이 과정에서는 Xacro 하나를 원본으로 유지하고, 도구가 URDF와 SDF를 차례로 생성합니다.</figcaption>
</figure>

- **URDF**는 link와 joint로 ROS 로봇의 구조를 표현하는 XML 형식입니다.
- **Xacro**는 치수, 공식, 반복 구조를 재사용해 URDF를 생성합니다.
- **SDF**는 Gazebo가 world, physics, sensor, system plugin까지 실행할 때 사용하는 형식입니다.

따라서 세 파일을 따로 고치는 것이 아닙니다. 이 저장소의 Xacro를 `xacro`가 URDF로 확장하고, Gazebo가 이를 SDF로 변환합니다.

## 설치된 1단계 모델 실행

먼저 description package를 빌드했다면, 저장소 위치가 아니라 설치 공간에서 단계 파일을 찾습니다.

```bash
source /opt/ros/jazzy/setup.zsh
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/01-base.xacro"
xacro "$stage" > /tmp/tutorial_bot-stage-01.urdf
check_urdf /tmp/tutorial_bot-stage-01.urdf
gz sdf -p /tmp/tutorial_bot-stage-01.urdf > /tmp/tutorial_bot-stage-01.sdf
gz sdf -k /tmp/tutorial_bot-stage-01.sdf
```

Bash에서는 첫 줄의 `setup.zsh`를 `setup.bash`로 바꿉니다. `check_urdf`가 `root Link: base_link`를 출력하고 SDF 검사가 조용히 끝나면 성공입니다. 1단계 inventory에는 `base_link` 하나만 있으며, 바퀴나 센서는 아직 없습니다.

!!! tip "설치 공간이 없다면"
    저장소 루트의 `examples/ros2_ws`에서 `colcon build --packages-select tutorial_bot_description`을 실행하고 `install/setup.zsh`를 source합니다.

## 직육면체 몸체와 관성

`base_link`는 질량 $m=5.0\,\mathrm{kg}$, 크기 $x=0.45\,\mathrm{m}$, $y=0.32\,\mathrm{m}$, $z=0.12\,\mathrm{m}$인 직육면체입니다. 중심을 지나는 각 축의 관성 모멘트는 다음과 같습니다.

\[
I_{xx}=\frac{m(y^2+z^2)}{12}
\]

\[
I_{yy}=\frac{m(x^2+z^2)}{12}
\]

\[
I_{zz}=\frac{m(x^2+y^2)}{12}
\]

값을 대입하면 $I_{xx}=0.0487$, $I_{yy}=0.0904$, $I_{zz}=0.1270\,\mathrm{kg\,m^2}$입니다. 길이가 가장 넓게 퍼진 x-y 평면에 수직인 z축의 값이 가장 큽니다.

??? note "계산을 한 줄씩 보기"
    예를 들어 $I_{xx}=5.0(0.32^2+0.12^2)/12=0.048666\ldots$입니다. Xacro의 `stage_box_inertia` 매크로도 같은 식을 계산하며, 문서에서는 소수 넷째 자리로 반올림했습니다.

관성이 없거나 실제 크기와 크게 다르면 Gazebo에서 가속과 충돌 반응이 부자연스러워집니다. visual은 보이는 모양, collision은 접촉에 쓰는 모양, inertial은 힘에 대한 반응을 맡습니다.

## 문제 해결

- `package 'tutorial_bot_description' not found`: workspace를 빌드한 뒤 그 workspace의 `install/setup.zsh`를 source합니다.
- `xacro: command not found`: `sudo apt install ros-jazzy-xacro`를 확인합니다.
- 1단계에 바퀴나 센서가 보임: canonical 최종 Xacro가 아니라 반드시 `01-base.xacro` 경로인지 확인합니다.

## 다음 단계

[바퀴와 Joint](06-joints.md)에서 parent/child 관계와 회전축을 추가합니다.
