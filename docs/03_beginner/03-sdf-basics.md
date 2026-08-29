# SDF 기초

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Gazebo GUI 기초

## 학습 목표

- SDF의 `world`, `model`, `link` 계층을 설명한다.
- `visual`, `collision`, `inertial`의 책임을 구분한다.
- pose와 SI 단위를 올바르게 읽는다.
- world System plugin과 model plugin의 적용 범위를 구분한다.

## SDF가 표현하는 범위

SDF(Simulation Description Format)는 Gazebo가 world, model, sensor, light, physics, System plugin을 읽는 XML 형식이다. 이 저장소는 `examples/gazebo/worlds/first-world.sdf`에 SDF 1.10을 사용한다.

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

## model을 실제 코드로 읽기

`training_box`의 핵심 정의는 다음과 같다.

```xml
<model name="training_box">
  <pose>1.5 0 0.5 0 0 0</pose>
  <link name="link">
    <inertial>
      <mass>1.0</mass>
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

각 요소는 다음 책임을 가진다.

| 요소 | 시뮬레이션에서 맡는 일 | 없을 때 나타나는 현상 |
|---|---|---|
| `visual` | 화면에 그릴 geometry와 material을 정의한다. | 물리적으로 존재해도 화면에 보이지 않는다. |
| `collision` | 접촉과 충돌에 사용할 단순 geometry를 정의한다. | 다른 물체를 통과한다. |
| `inertial` | 질량, 질량 중심, 관성 모멘트를 정의한다. | 동적 model의 물리 반응이 유효하지 않거나 부자연스럽다. |
| `pose` | 부모 frame을 기준으로 위치와 자세를 정의한다. | 기본값인 원점, 무회전을 사용한다. |

visual은 상세 mesh, collision은 계산이 가벼운 기본 형상을 사용하는 경우가 많다. 두 형상의 크기와 원점이 크게 다르면 화면상 접촉과 실제 충돌이 어긋나므로 Inspector에서 함께 확인해야 한다.

## pose와 단위

`<pose>`의 기본 순서는 `x y z roll pitch yaw`이다. 위치는 m, 각도는 rad, 질량은 kg을 사용한다.

\[
\mathrm{pose}=(x,\ y,\ z,\ \mathrm{roll},\ \mathrm{pitch},\ \mathrm{yaw}) \tag{1}
\]

`1.5 0 0.5 0 0 0`을 대입하면 위치는 `(1.5, 0, 0.5)` m이고 회전은 `(0, 0, 0)` rad이다. yaw를 90° 돌리려면 degree 값 `90`이 아니라 rad 값 약 `1.5708`을 쓴다.

```xml
<pose>1.5 0 0.5 0 0 1.57079632679</pose>
```

## 정적 model과 동적 model

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

`<static>true</static>`인 model은 중력이나 외력으로 움직이지 않는다. `training_box`에는 이 태그가 없으므로 Physics System이 중력과 바닥 접촉을 계산한다.

## world System 읽기

System plugin은 world나 model에 실행 기능을 붙인다. `first-world.sdf`의 world 수준 선언은 다음과 같다.

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

`Physics`는 world 전체의 강체를 갱신한다. `Sensors`는 렌더링 기반 sensor를 갱신하고, `Imu`는 IMU sensor를 처리한다. 이후 로봇에 넣는 DiffDrive는 model 수준 plugin이므로 그 model의 wheel joint만 제어한다.

## 검사와 전개 결과 확인

먼저 SDF가 유효한지 검사한다.

```bash
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
- 전개한 SDF에서 `ground`, `training_box`, `beacon` model을 찾을 수 있다.
- `training_box`에는 visual, collision, inertial이 모두 존재한다.
- `ground`와 `beacon`에는 `<static>true</static>`이 남아 있다.

## 문제 해결

- XML 오류가 나면 표시된 line에서 시작·종료 태그의 이름과 중첩을 확인한다.
- pose 오류가 나면 값이 여섯 개인지, 쉼표 대신 공백을 썼는지 확인한다.
- visual은 보이지만 상자가 바닥을 통과하면 `collision`과 Physics System을 확인한다.
- 검사는 통과하지만 model이 안 보이면 pose의 z 값, geometry 크기, material alpha를 확인한다.

[다음: 첫 World](04-first-world.md)
