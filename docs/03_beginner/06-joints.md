# 2륜과 Caster Wheel 추가하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** [첫 `tutorial_bot`](05-first-robot.md)

## 학습 목표

- link의 parent·child 관계와 joint 자유도(DOF)를 설명한다.
- 원통 바퀴의 길이 축과 joint 회전축을 같은 방향으로 배치한다.
- 좌우 구동 바퀴와 고정식 구형 caster의 역할을 구분한다.
- 2단계 Xacro를 URDF와 SDF로 전개해 link·joint inventory를 확인한다.

## 완성할 기구 구조

<pre class="course-mermaid">
flowchart TD
  B[base_link] --> LJ[left_wheel_joint]
  B --> RJ[right_wheel_joint]
  B --> CJ[caster_joint]
  LJ --> L[left_wheel_link]
  RJ --> R[right_wheel_link]
  CJ --> C[caster_link]
</pre>

URDF 트리는 root link 하나에서 시작한다. 각 joint는 기준이 되는 parent link, 움직이거나 고정되는 child link, 허용할 운동을 정의한다.

| joint 종류 | 허용 운동 | 자유도 | 이 로봇에서의 용도 |
|---|---|---:|---|
| `fixed` | 없음 | 0 | `caster_link`와 sensor link를 차체에 고정한다. |
| `revolute` | 제한된 축 회전 | 1 | 회전 각도 범위가 있는 관절에 쓴다. |
| `continuous` | 제한 없는 축 회전 | 1 | 좌우 구동 바퀴에 쓴다. |

## 재사용 가능한 wheel macro

두 바퀴는 형상과 관성이 같고 이름과 y 위치만 다르다. `stage_components.xacro`는 이를 `side`, `y_position` 매개변수로 만든다.

```xml
<xacro:macro name="stage_wheel" params="side y_position">
  <link name="${side}_wheel_link">
    <xacro:stage_wheel_inertia mass="0.3" radius="0.06" width="0.04"/>
    <visual>
      <origin rpy="1.57079632679 0 0"/>
      <geometry><cylinder radius="0.06" length="0.04"/></geometry>
    </visual>
    <collision>
      <origin rpy="1.57079632679 0 0"/>
      <geometry><cylinder radius="0.06" length="0.04"/></geometry>
    </collision>
  </link>

  <joint name="${side}_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="${side}_wheel_link"/>
    <origin xyz="0 ${y_position} -0.06" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="5.0" velocity="20.0"/>
  </joint>
</xacro:macro>
```

URDF cylinder의 기본 길이 축은 z축이다. visual과 collision에 roll 90°를 적용하면 원통 길이 축이 y축에 놓인다. joint의 `<axis xyz="0 1 0"/>`도 y축이므로 바퀴가 y축 둘레로 굴러 로봇이 x방향으로 이동한다.

<figure markdown="span">
  ![로봇의 전진 x축, 좌우 y축과 바퀴 joint 회전축 관계](../assets/beginner/joint-axis.svg)
  <figcaption>그림 2. 두 바퀴의 joint axis는 y축과 나란하고, 바퀴는 그 축을 중심으로 굴러 x방향으로 이동한다.</figcaption>
</figure>

macro는 다음 두 줄로 좌우 바퀴를 만든다.

```xml
<xacro:stage_wheel side="left"  y_position="0.19"/>
<xacro:stage_wheel side="right" y_position="-0.19"/>
```

전개 후 실제 joint 이름은 `left_wheel_joint`, `right_wheel_joint`가 된다. 다음 장의 DiffDrive plugin은 이 문자열을 그대로 참조하므로 이름을 바꾸면 plugin 설정도 함께 바꿔야 한다.

## Caster Wheel을 구형 접촉으로 근사하기

두 구동 바퀴만으로는 차체의 앞뒤 지지가 부족하다. 이 예제는 차체 뒤쪽에 반지름 0.035 m의 구형 `caster_link`를 두어 세 번째 접점을 만든다.

```xml
<link name="caster_link">
  <inertial>
    <mass value="0.08"/>
    <inertia ixx="0.0000392" ixy="0" ixz="0"
             iyy="0.0000392" iyz="0" izz="0.0000392"/>
  </inertial>
  <visual>
    <geometry><sphere radius="0.035"/></geometry>
    <material name="caster_gray">
      <color rgba="0.35 0.35 0.35 1.0"/>
    </material>
  </visual>
  <collision>
    <geometry><sphere radius="0.035"/></geometry>
  </collision>
</link>

<joint name="caster_joint" type="fixed">
  <parent link="base_link"/>
  <child link="caster_link"/>
  <origin xyz="-0.17 0 -0.085" rpy="0 0 0"/>
</joint>

<gazebo reference="caster_link">
  <mu1>0.05</mu1>
  <mu2>0.05</mu2>
</gazebo>
```

이 caster는 조향축과 회전축을 수학적으로 엄밀하게 모델링한 실제 캐스터는 아니고, 그냥 구를 `fixed` joint로 붙인 튜토리얼용 근사이다. `mu1`, `mu2`를 낮춰 회전할 때 caster 마찰력이 차체를 과도하게 붙잡지 않도록 한다. caster는 DiffDrive의 구동 joint 목록에 넣지 않는다.

이 caster의 바닥 접점도 맞춰져 있다. 구동 바퀴 중심은 z=-0.06 m이고 반지름은 0.06 m이므로 바닥점은 z=-0.12 m이다. caster 중심은 z=-0.085 m이고 반지름은 0.035 m이므로 바닥점도 z=-0.12 m이다.

구의 중심 관성은 모든 축에서 같다.

\[
I=\frac{2}{5}mr^2
=\frac{2}{5}(0.08)(0.035)^2
=0.0000392\;\mathrm{kg\,m^2}
\]

## 2단계 Xacro 조립 구조

`02-wheels-and-joints.xacro`는 base와 `stage_wheels`를 조립한다. `stage_wheels` 안에는 좌우 wheel과 caster가 함께 들어 있다.

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="tutorial_bot">
  <xacro:include filename="../macros/stage_components.xacro"/>
  <xacro:stage_base/>
  <xacro:stage_wheels/>
</robot>
```

설치된 2단계 모델을 전개하고 검사한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
stage="$(ros2 pkg prefix --share tutorial_bot_description)/urdf/stages/02-wheels-and-joints.xacro"
xacro "$stage" > /tmp/tutorial_bot-stage-02.urdf
check_urdf /tmp/tutorial_bot-stage-02.urdf
gz sdf -p /tmp/tutorial_bot-stage-02.urdf > /tmp/tutorial_bot-stage-02.sdf
gz sdf -k /tmp/tutorial_bot-stage-02.sdf
```

정상 inventory는 link 4개와 joint 3개이다.

```bash
grep -o '<link name="[^"]*"' /tmp/tutorial_bot-stage-02.urdf
grep -o '<joint name="[^"]*"' /tmp/tutorial_bot-stage-02.urdf
```

```text
link: base_link, left_wheel_link, right_wheel_link, caster_link
joint: left_wheel_joint, right_wheel_joint, caster_joint
```

`check_urdf`의 tree에는 `base_link` 아래에 세 child가 나타난다. DiffDrive plugin과 sensor는 2단계에 없어야 한다.

## 바퀴 관성 확인

바퀴 하나는 질량 $m=0.3\,\mathrm{kg}$, 반지름 $r=0.06\,\mathrm{m}$, 폭 $w=0.04\,\mathrm{m}$인 실린더이다. y축이 회전축이므로 다음 값을 사용한다.

\[
I_{yy}=\frac{mr^2}{2}=0.000540\;\mathrm{kg\,m^2}
\]

\[
I_{xx}=I_{zz}=\frac{m(3r^2+w^2)}{12}=0.000310\;\mathrm{kg\,m^2}
\]

??? note "왜 회전축의 관성식이 다른가"
    질량이 회전축에서 얼마나 멀리 분포하는지가 관성을 정한다. 실린더 중심축인 y축 둘레 회전에는 반지름만 관여하고, x·z축 둘레 회전에는 반지름과 폭이 함께 관여한다.

전개된 URDF의 값과 식이 일치하는지 확인한다.

```bash
grep -A5 '<link name="left_wheel_link"' /tmp/tutorial_bot-stage-02.urdf
```

## 문제 해결

- `joint xml is not initialized correctly`가 나오면 parent·child 이름이 실제 link 이름과 같은지 확인한다.
- 바퀴가 차체 안쪽에 있으면 joint origin의 y 값이 왼쪽 `+0.19`, 오른쪽 `-0.19`인지 확인한다.
- 바퀴가 다른 축으로 회전하면 cylinder의 `rpy`와 joint `axis`를 함께 확인한다.
- caster가 바닥에 닿지 않으면 caster 중심 z와 반지름의 합이 wheel 바닥점과 같은지 계산한다.
- 회전할 때 caster가 끌리며 튀면 `mu1`, `mu2`가 낮은 값으로 SDF에 변환됐는지 확인한다.

[다음: DiffDrive](07-diff-drive.md)
