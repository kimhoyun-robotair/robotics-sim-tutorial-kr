# 고급 SDF와 물리 속성

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** SDF 기초

## 학습 목표

- SDF의 `frame`과 `relative_to` pose를 코드에서 읽는다.
- `world`, `model`, `link`, `joint`, `sensor`, `plugin`의 책임을 구분한다.
- collision, inertia, friction이 시뮬레이션 결과에 미치는 영향을 설명한다.
- 로컬 model과 Fuel model의 `<include>` 사용법을 구분한다.

## SDF 계층과 System

SDF는 Gazebo world와 물리·센서·System을 풍부하게 표현하는 XML 형식이다. 저장소의 `training.sdf`는 다음과 같이 world와 필요한 System을 선언한다.

```xml
<?xml version="1.0"?>
<sdf version="1.10">
  <world name="training">
    <gravity>0 0 -9.80665</gravity>
    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"
            name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system"
            name="gz::sim::systems::Imu"/>
  </world>
</sdf>
```

Physics System은 중력·접촉·joint dynamics를 갱신한다. UserCommands System은 spawn·remove 같은 entity 변경 서비스를 제공한다. SceneBroadcaster와 Sensors System은 GUI와 렌더링 기반 센서에 필요한 scene 정보를 제공하고, Imu System은 IMU sensor를 갱신한다. 센서 태그만 추가하고 해당 System을 world에서 누락하면 topic이 생기지 않을 수 있다.

## model, link, visual, collision, inertial

동적 물체 하나를 표현하는 최소 구조는 다음과 같다.

```xml
<model name="crate">
  <pose>1 0 0.25 0 0 0</pose>
  <link name="body">
    <inertial>
      <mass>8.0</mass>
      <inertia>
        <ixx>0.0867</ixx><iyy>0.1333</iyy><izz>0.1667</izz>
        <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
      </inertia>
    </inertial>
    <collision name="collision">
      <geometry><box><size>0.4 0.3 0.2</size></box></geometry>
    </collision>
    <visual name="visual">
      <geometry><box><size>0.4 0.3 0.2</size></box></geometry>
      <material><diffuse>0.1 0.35 0.8 1</diffuse></material>
    </visual>
  </link>
</model>
```

`visual`은 표시를, `collision`은 접촉 형상을, `inertial`은 힘과 토크에 대한 반응을 정한다. 복잡한 mesh를 visual로 사용하더라도 collision은 box·cylinder 같은 단순 형상으로 근사하면 계산량을 줄일 수 있다. 이때 질량과 관성은 **collision에 사용한 실제 물리 형상**과 일치시킨다.

## frame과 상대 pose

숫자만 있는 `<pose>`는 기준 좌표계를 놓치기 쉽다. `relative_to`를 사용하면 의도를 이름으로 드러낼 수 있다.

```xml
<model name="inspection_cell">
  <pose>2 1 0 0 0 0.7854</pose>

  <frame name="sensor_mount" attached_to="base">
    <pose relative_to="base">0.25 0 0.18 0 0 0</pose>
  </frame>

  <link name="base">
    <pose relative_to="__model__">0 0 0.1 0 0 0</pose>
  </link>

  <link name="camera_body">
    <pose relative_to="sensor_mount">0.03 0 0 0 0 0</pose>
  </link>
</model>
```

`camera_body`의 pose는 world가 아니라 `sensor_mount` 기준이다. `attached_to`는 frame이 물리적으로 어느 frame을 따라가는지, `relative_to`는 pose 값이 어느 frame에서 표현되는지를 나타낸다. 두 속성은 같은 질문에 답하지 않는다.

## 마찰과 접촉 파라미터

바퀴 collision에 마찰을 명시하면 구동 방향의 grip과 횡방향 미끄럼을 조정할 수 있다. 물리 엔진별 상세 태그는 다를 수 있으므로 이 저장소가 사용하는 엔진과 SDF 버전에서 검증해야 한다. ODE 계열 접촉 예시는 다음과 같다.

```xml
<collision name="wheel_collision">
  <geometry><cylinder><radius>0.06</radius><length>0.04</length></cylinder></geometry>
  <surface>
    <friction>
      <ode>
        <mu>1.0</mu>
        <mu2>0.6</mu2>
        <fdir1>1 0 0</fdir1>
      </ode>
    </friction>
  </surface>
</collision>
```

`mu`와 `mu2`를 무조건 크게 만들면 좋은 모델이 되지 않는다. 4륜 skid-steer 로버는 회전할 때 바퀴가 횡방향으로 미끄러져야 하므로 횡마찰이 지나치게 크면 회전이 뻣뻣해지고 wheel odometry 오차도 달라진다.

<figure class="course-figure" id="intermediate-inertia-contact">
  <img src="../../assets/intermediate/inertia-contact.svg" alt="직육면체 관성과 접촉 수직력 마찰력의 관계도" loading="lazy">
  <figcaption>그림 1. 질량과 관성 텐서가 가속을, collision과 마찰이 접촉력을 결정한다.</figcaption>
</figure>

## 계산 예제: 관성과 접촉 한계

<div class="course-worked" data-worked-example="inertia-contact">
질량 \(m=8\,\mathrm{kg}\), 크기 \(a=0.40\), \(b=0.30\), \(c=0.20\,\mathrm{m}\)인 균일 직육면체라면 \(I_{xx}=m(b^2+c^2)/12=0.0867\,\mathrm{kg\,m^2}\)이다. 마찰계수 \(\mu=0.8\)이고 평지에서 \(N=mg\)라면 접선력 한계는 \(|F_t|\leq\mu N=62.8\,\mathrm{N}\)이다. collision 크기만 바꾸고 이 관성을 그대로 두면 회전 응답이 물리 형상과 어긋난다.
</div>

## model 재사용

world에서 외부 model을 재사용할 때는 `<include>`를 사용한다.

```xml
<!-- 로컬 resource path에서 찾는다. -->
<include>
  <uri>model://warehouse_shelf</uri>
  <name>shelf_a</name>
  <pose>2 1 0 0 0 1.5708</pose>
</include>

<!-- Fuel URL을 직접 사용할 수도 있다. -->
<include>
  <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke</uri>
  <name>fuel_coke</name>
  <static>true</static>
</include>
```

`model://` URI는 `GZ_SIM_RESOURCE_PATH`에서 찾고 Fuel URL은 download cache를 사용한다. Gazebo Classic의 `GAZEBO_MODEL_PATH`와 혼동하지 않는다.

## 예제 파일과 실행

실제 Harmonic world는 `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`이다. 로봇 본체의 원본은 이 파일이 아니라 `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`이다.

```bash
gz sdf -k examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
gz sim -s -r examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
```

다른 terminal에서 world service와 model 목록을 확인한다.

```bash
gz service -l | grep /world/training
gz model --list
```

첫 명령이 오류 없이 끝나고 `/world/training` service가 보이면 world 구조와 server 실행이 정상이다. 종료할 때는 server terminal에서 `Ctrl+C`를 누른다.

## 문제 해결

- `model://` URI를 찾지 못하면 `printf '%s\n' "$GZ_SIM_RESOURCE_PATH"`로 탐색 경로를 확인한다.
- pose가 예상과 다르면 `relative_to` 대상이 같은 scope에 존재하는지 확인한다.
- 물체가 바닥을 통과하면 collision과 Physics System을 확인한다.
- 센서 topic이 없으면 Sensors 또는 Imu System이 world에 선언됐는지 확인한다.
- 로봇이 튀거나 떨리면 질량이 0에 가깝지 않은지, inertia가 양의 정부호인지, collision이 겹친 채 spawn되지 않았는지 확인한다.

## 정리

SDF는 Harmonic의 world와 Gazebo 전용 기능을 표현한다. `frame`과 `relative_to`로 좌표 기준을 분명히 하고, visual·collision·inertial·friction을 각각 표시·접촉·동역학 책임에 맞게 설정해야 재현 가능한 물리 결과를 얻는다.

[다음: URDF·Xacro·SDF 역할 나누기](02-urdf-xacro-sdf.md)
