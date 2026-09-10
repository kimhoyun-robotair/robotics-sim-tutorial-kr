# 고급 SDF와 물리 속성

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** SDF 기초

## 학습 목표

- SDF의 `frame`과 `pose relative_to`를 읽고 좌표 기준을 구분한다.
- `world`, `model`, `link`, `joint`, `sensor`, `plugin`의 책임을 구분한다.
- 충돌 형상, 관성, 마찰이 시뮬레이션 결과에 미치는 영향을 설명한다.
- 로컬 모델과 Fuel 모델의 `<include>` 사용법을 구분한다.

## 실습 전 준비

[중급 실행 준비](index.md#intermediate-setup)를 마쳐야 한다. 새 터미널마다 저장소 루트에서 다음 명령을 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
```

아래 XML·Python·YAML은 설명에 필요한 부분을 발췌한 코드이다. 실행에는 본문에 표시한 저장소 파일을 사용한다. 이전 실습의 Gazebo와 launch는 `Ctrl+C`로 종료한 뒤 새 실습을 시작한다. `ros2 topic hz`와 `tf2_echo`는 계속 실행되므로, 값을 확인한 뒤 `Ctrl+C`로 멈추고 다음 명령을 입력한다.

## SDF 계층과 시스템 플러그인

SDF는 시뮬레이션 환경, 물체, 물리 속성, 센서를 정의하는 XML 형식이다. 저장소의 `training.sdf`는 다음과 같이 월드와 필요한 시스템 플러그인을 선언한다.

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

Physics 시스템 플러그인은 중력·접촉·조인트 운동을 갱신한다. UserCommands 시스템 플러그인은 물체 생성·삭제 서비스를 제공한다. SceneBroadcaster와 Sensors 시스템 플러그인은 GUI와 렌더링 기반 센서에 필요한 장면 정보를 제공하고, Imu 시스템 플러그인은 IMU 센서를 갱신한다. 센서 태그만 추가하고 해당 시스템 플러그인을 월드에서 누락하면 토픽이 생기지 않을 수 있다.

## 물체의 모양과 질량 정의하기

다음은 가로 0.4 m, 세로 0.3 m, 높이 0.2 m인 상자이다. 이 `<model>` 블록을 복사해 시험할 때는 `training.sdf`의 `<world>` 안에 넣는다.

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

`visual`은 표시를, `collision`은 접촉 형상을, `inertial`은 힘과 토크에 대한 반응을 정한다. 복잡한 메시를 화면에 표시하더라도 접촉 계산에는 상자·원기둥처럼 단순한 형상을 사용하면 계산량을 줄일 수 있다. 질량과 관성은 표현하려는 물체의 질량 분포를 기준으로 정한다. 단순화한 충돌 형상에서 관성을 계산했다면 그 근사가 적절한지도 확인한다.

## 위치와 자세의 기준 좌표계

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

`camera_body`의 위치와 자세는 월드가 아니라 `sensor_mount` 기준이다. `attached_to`는 좌표계가 물리적으로 어느 좌표계를 따라가는지, `relative_to`는 위치와 자세 값이 어느 좌표계에서 표현되는지를 나타낸다. 즉, `attached_to`는 무엇을 따라 움직이는지, `relative_to`는 숫자를 어느 좌표계에서 읽는지를 정한다. 위 코드는 좌표 관계를 보여 주는 예시이며, 두 링크를 실제로 고정하려면 별도의 고정 조인트가 필요하다.

## 마찰과 접촉 파라미터

바퀴 충돌 형상에 마찰을 명시하면 구동 방향의 접지력과 횡방향 미끄럼을 조정할 수 있다. 물리 엔진별 상세 태그는 다를 수 있으므로 이 저장소가 사용하는 엔진과 SDF 버전에서 검증해야 한다. 다음은 SDF의 `<ode>` 마찰 항목을 쓰는 예시이다. Harmonic의 기본 물리 엔진은 DART이며, `<ode>` 태그를 적었다고 ODE 엔진으로 바뀌지는 않는다.

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

`mu`와 `mu2`를 무조건 크게 만들면 좋은 모델이 되지 않는다. 4륜 스키드 조향 로버는 회전할 때 바퀴가 횡방향으로 미끄러져야 하므로 횡마찰이 지나치게 크면 회전이 뻣뻣해지고 바퀴 오도메트리 오차도 달라진다.

<figure class="course-figure" id="intermediate-inertia-contact">
  <img src="../../assets/intermediate/inertia-contact.svg" alt="직육면체 관성과 접촉 수직력 마찰력의 관계도" loading="lazy">
  <figcaption>그림 1. 질량과 관성 텐서가 가속을, 충돌 형상과 마찰이 접촉력을 결정한다.</figcaption>
</figure>

## 계산 예제: 관성과 접촉 한계

<div class="course-worked" data-worked-example="inertia-contact" markdown="1">
질량 $m=8\,\mathrm{kg}$, 크기 $a=0.40$, $b=0.30$, $c=0.20\,\mathrm{m}$인 균일 직육면체라면 $I_{xx}=m(b^2+c^2)/12=0.0867\,\mathrm{kg\,m^2}$이다. 마찰계수 $\mu=0.8$이고 평지에서 $N=mg$라면 접선력 한계는 $|F_t|\leq\mu N=62.8\,\mathrm{N}$이다. 충돌 형상 크기만 바꾸고 이 관성을 그대로 두면 회전 응답이 물리 형상과 어긋난다.
</div>

## 모델 재사용

월드에서 외부 모델을 재사용할 때는 `<include>`를 사용한다.

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

`model://` URI는 `GZ_SIM_RESOURCE_PATH`에서 찾고 Fuel URL은 내려받은 파일의 캐시를 사용한다. Gazebo Classic의 `GAZEBO_MODEL_PATH`와 혼동하지 않는다.

## 예제 파일과 실행

실제 Harmonic 월드는 `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf`이다. 로봇 본체의 원본은 이 파일이 아니라 `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`이다.

```bash
gz sdf -k examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
gz sim -s -r examples/ros2_ws/src/tutorial_bot_gazebo/worlds/training.sdf
```

다른 터미널에서 월드 서비스와 모델 목록을 확인한다.

```bash
gz service -l | grep /world/training
gz model --list
```

첫 명령이 오류 없이 끝나고 `/world/training` 서비스가 보이면 월드 구조와 서버 실행이 정상이다. 종료할 때는 서버 터미널에서 `Ctrl+C`를 누른다.

## 문제 해결

- `model://` URI를 찾지 못하면 `printf '%s\n' "$GZ_SIM_RESOURCE_PATH"`로 탐색 경로를 확인한다.
- 위치와 자세가 예상과 다르면 `relative_to` 대상이 같은 범위에 존재하는지 확인한다.
- 물체가 바닥을 통과하면 충돌 형상과 Physics 시스템 플러그인을 확인한다.
- 센서 토픽이 없으면 Sensors 또는 Imu 시스템 플러그인이 월드에 선언됐는지 확인한다.
- 로봇이 튀거나 떨리면 질량이 0에 가깝지 않은지, 관성이 양의 정부호인지, 충돌 형상이 겹친 채 생성되지 않았는지 확인한다.

## 정리

SDF는 Harmonic의 월드와 Gazebo 전용 기능을 표현한다. `frame`과 `relative_to`로 좌표 기준을 분명히 하고, 화면에 그릴 형상, 접촉을 계산할 형상, 질량·관성, 마찰을 각각 확인해야 한다.

[다음: URDF·Xacro·SDF 역할 나누기](02-urdf-xacro-sdf.md)
