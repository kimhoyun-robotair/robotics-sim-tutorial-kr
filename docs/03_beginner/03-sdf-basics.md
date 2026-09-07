# SDF 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo GUI 기초

## 학습 목표

- SDF의 `world`, `model`, `link` 계층을 설명한다.
- `visual`, `collision`, `inertial`의 책임을 구분한다.
- 위치·자세와 SI 단위를 올바르게 읽는다.
- 월드 시스템 플러그인과 모델 플러그인의 적용 범위를 구분한다.

## SDF가 표현하는 범위

SDF(Simulation Description Format)는 Gazebo가 월드, 모델, 센서, 조명, 물리, 시스템 플러그인을 읽는 XML 형식이다. 이 저장소는 `examples/gazebo/worlds/first-world.sdf`에 SDF 1.10을 사용한다.

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="first_world">
    <gravity>0 0 -9.8</gravity>
    <!-- plugin, light, model이 이 안에 들어간다. -->
  </world>
</sdf>
```

`world`는 시뮬레이션 환경 하나를, `model`은 이름 있는 물체 하나를, `link`는 질량과 형상을 가진 강체를 나타낸다.

<figure class="course-figure">
  <img src="../../assets/diagrams/beginner-sdf-hierarchy.svg" alt="SDF의 world model link 계층과 visual collision 및 pose 순서를 설명한 도식" loading="lazy">
  <figcaption>그림 1. SDF는 world, model, link 계층 아래에서 보이는 형상과 물리 형상을 분리한다.</figcaption>
</figure>

## 모델을 실제 코드로 읽기

`training_box`의 핵심 정의는 다음과 같다.

```xml
<model name="training_box">
  <pose>1.5 0 0.5 0 0 0</pose>
  <link name="link">
    <inertial>
      <mass>1.0</mass>
      <inertia>
        <ixx>0.1666666667</ixx><iyy>0.1666666667</iyy><izz>0.1666666667</izz>
        <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
      </inertia>
    </inertial>
    <collision name="collision">
      <geometry>
        <box><size>1 1 1</size></box>
      </geometry>
    </collision>
    <visual name="visual">
      <geometry>
        <box><size>1 1 1</size></box>
      </geometry>
      <material><diffuse>0.8 0.15 0.1 1</diffuse></material>
    </visual>
  </link>
</model>
```

위 코드는 질량 1 kg, 한 변 1 m인 균일한 정육면체의 관성을 직접 적은 예이다. 각 축의 관성은 `m(1²+1²)/12 = 1/6 kg·m²`이다. 원본 `first-world.sdf`도 같은 관성을 사용한다. SDF가 기본값을 채워 문법 검사를 통과하더라도 그 값이 실제 형상에 맞는지는 별도로 확인해야 한다.

각 요소는 다음 역할을 맡는다.

| 요소 | 시뮬레이션에서 맡는 일 | 없을 때 나타나는 현상 |
|---|---|---|
| `visual` | 화면에 그릴 형상과 재질을 정의한다. | 물리적으로 존재해도 화면에 보이지 않는다. |
| `collision` | 접촉과 충돌에 사용할 단순 형상을 정의한다. | 다른 물체를 통과한다. |
| `inertial` | 질량, 질량 중심, 관성 모멘트를 정의한다. | 동적 모델의 물리 반응이 유효하지 않거나 부자연스럽다. |
| `pose` | 부모 프레임을 기준으로 위치와 자세를 정의한다. | 기본값인 원점, 무회전을 사용한다. |

visual은 상세 메시, collision은 계산이 가벼운 기본 형상을 사용하는 경우가 많다. 두 형상의 크기와 원점이 크게 다르면 화면상 접촉과 실제 충돌이 어긋나므로 Inspector에서 함께 확인해야 한다.

## 위치와 회전의 단위

`<pose>`의 기본 순서는 `x y z roll pitch yaw`이다. 위치는 m, 각도는 rad, 질량은 kg을 사용한다.

\[
\mathrm{pose}=(x,\ y,\ z,\ \mathrm{roll},\ \mathrm{pitch},\ \mathrm{yaw}) \tag{1}
\]

`1.5 0 0.5 0 0 0`을 대입하면 위치는 `(1.5, 0, 0.5)` m이고 회전은 `(0, 0, 0)` rad이다. yaw를 90° 돌리려면 도 단위 값 `90`을 라디안으로 환산한 약 `1.5708`을 쓴다.

```xml
<pose>1.5 0 0.5 0 0 1.57079632679</pose>
```

## 정적 모델과 동적 모델

바닥은 다음처럼 정적으로 선언한다.

```xml
<model name="ground">
  <static>true</static>
  <link name="link">
    <collision name="collision">
      <geometry>
        <plane><normal>0 0 1</normal><size>20 20</size></plane>
      </geometry>
    </collision>
    <visual name="visual">
      <geometry>
        <plane><normal>0 0 1</normal><size>20 20</size></plane>
      </geometry>
    </visual>
  </link>
</model>
```

`<static>true</static>`인 모델은 중력이나 외력으로 움직이지 않는다. `training_box`에는 이 태그가 없으므로 Physics 시스템이 중력과 바닥 접촉을 계산한다.

## 월드 시스템 읽기

시스템 플러그인은 월드나 모델에 실행 기능을 붙인다. `first-world.sdf`의 월드 수준 선언은 다음과 같다.

```xml
<plugin filename="gz-sim-physics-system"
        name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
<plugin filename="gz-sim-imu-system"
        name="gz::sim::systems::Imu"/>
```

`Physics`는 월드 전체의 물리법칙을 갱신한다. `Sensors`는 렌더링 기반 센서를 갱신하고, `Imu`는 IMU 센서를 처리한다. 이후 로봇에 넣는 DiffDrive는 모델 수준 플러그인이므로 그 모델의 바퀴 조인트만 제어한다.

## 검사와 전개 결과 확인

저장소 루트에서 SDF가 유효한지 검사한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

도구가 해석한 전체 SDF를 출력하면 생략된 기본값까지 확인할 수 있다.

```bash
gz sdf -p examples/gazebo/worlds/first-world.sdf > /tmp/first-world.expanded.sdf
grep -nE '<world|<model|<link|<visual|<collision' /tmp/first-world.expanded.sdf
```

`-k`의 `Valid.`는 XML과 SDF 구조가 유효하다는 뜻이다. 화면 배치나 물리 값이 의도와 같은지는 실행 관찰로 별도 확인해야 한다.

## 예상 관찰

- 검사 결과에 `Valid.`가 나타난다.
- 전개한 SDF에서 `ground`, `training_box`, `beacon` 모델을 찾을 수 있다.
- `training_box`에는 `visual`, `collision`, `inertial`이 모두 존재한다.
- `ground`와 `beacon`에는 `<static>true</static>`이 남아 있다.

## 문제 해결

- XML 오류가 나면 표시된 줄에서 시작·종료 태그의 이름과 중첩을 확인한다.
- 위치와 자세 오류가 나면 값이 여섯 개인지, 쉼표 대신 공백을 썼는지 확인한다.
- visual은 보이지만 상자가 바닥을 통과하면 `collision`과 Physics 시스템을 확인한다.
- 검사는 통과하지만 모델이 안 보이면 위치와 자세의 z 값, 형상 크기, 재질 alpha를 확인한다.

[다음: 첫 월드](04-first-world.md)
