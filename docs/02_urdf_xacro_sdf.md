# URDF, Xacro, SDF를 한 번에 이해하기

URDF, Xacro, SDF는 로봇과 시뮬레이션 환경을 서로 다른 역할로 표현하는 형식이다. 이 튜토리얼에서는 **Xacro로 URDF를 생성하고**, ROS 2가 그 URDF로 TF를 구성하며, Gazebo Classic 11이 URDF를 내부 SDF 모델로 변환하여 월드에 삽입한다. 조명·지면·물리 엔진과 같은 환경은 SDF 월드로 작성한다.

```mermaid
flowchart LR
  X["Xacro · 작성 원본"] -->|xacro| U["URDF XML"]
  U -->|robot_state_publisher| T["TF tree"]
  U -->|spawn_entity.py| C["Gazebo 내부 SDF model"]
  W["SDF world"] --> G["Gazebo Classic 11"]
  C --> G
```

## 세 형식의 역할

| 형식 | 가장 잘하는 일 | 주의점 | 이 튜토리얼의 사용처 |
| --- | --- | --- | --- |
| URDF | 하나의 로봇을 링크·조인트 트리로 표현하고 ROS 도구와 연동한다 | 반복·조건문이 없고 닫힌 운동학 고리와 월드 표현이 제한적이다 | `robot_description`, TF, RViz RobotModel |
| Xacro | URDF XML에 변수, 수식, 매크로, 불러오기, 조건을 추가한다 | 전개하기 전에는 완전한 URDF가 아니므로 모든 인자 조합을 검사해야 한다 | 바퀴·센서·관성 모델을 재사용 가능한 원본으로 관리한다 |
| SDF | 월드, 물리 계산, 센서, 플러그인, 여러 모델을 풍부하게 표현한다 | `robot_state_publisher`에 그대로 입력할 수 없다 | `empty.world`, `sensor.world`, Gazebo 센서·플러그인 설정 |

다음 원칙을 적용하면 파일의 역할을 나누기 쉽다.

- ROS가 알아야 하는 링크, 조인트, 좌표 관계는 URDF에 둔다.
- 반복되는 형상과 센서 조립 규칙은 Xacro 매크로로 분리한다.
- Gazebo만 알아야 하는 마찰, 센서, 모델 플러그인은 URDF의 `<gazebo>` 확장에 둔다.
- 조명, 지면, 장애물, 물리 계산 간격과 같은 환경은 SDF 월드에 둔다.

## 1. 실제 URDF 코드 읽기

URDF의 최상위 요소는 `<robot>`이며, 그 아래에 물체인 `<link>`와 물체 사이 관계인 `<joint>`를 둔다. 다음은 차체와 바퀴 하나를 가진 최소 모델로, `/tmp/minimal_robot.urdf`에 저장해 검사할 수 있는 전체 XML이다. 오른쪽 바퀴와 구동 플러그인이 없으므로 이 예제는 **구조 검사 연습용**이다. 실제 주행은 다음 장의 완성된 `diffbot`으로 실습한다.

터미널에서 `nano /tmp/minimal_robot.urdf`를 실행하고 아래 XML 전체를 붙여 넣는다. `Ctrl+O`, `Enter`로 저장한 뒤 `Ctrl+X`로 편집기를 닫는다. 다른 텍스트 편집기를 사용해도 된다.

```xml
<?xml version="1.0"?>
<robot name="minimal_robot">
  <!-- 차체: 크기 0.40 × 0.30 × 0.10 m, 질량 4 kg -->
  <link name="base_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.40 0.30 0.10"/>
      </geometry>
      <material name="blue">
        <color rgba="0.12 0.35 0.80 1.0"/>
      </material>
    </visual>

    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.40 0.30 0.10"/>
      </geometry>
    </collision>

    <inertial>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <mass value="4.0"/>
      <inertia ixx="0.033333" ixy="0" ixz="0"
               iyy="0.056667" iyz="0" izz="0.083333"/>
    </inertial>
  </link>

  <!-- 바퀴: 반지름 0.08 m, 폭 0.04 m, 질량 0.5 kg -->
  <link name="left_wheel_link">
    <visual>
      <!-- URDF cylinder의 기본 대칭축 z를 바퀴축 y와 평행하게 맞춘다. -->
      <origin xyz="0 0 0" rpy="1.570796 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
      <material name="black">
        <color rgba="0.05 0.05 0.05 1.0"/>
      </material>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="1.570796 0 0"/>
      <geometry>
        <cylinder radius="0.08" length="0.04"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 0" rpy="1.570796 0 0"/>
      <mass value="0.5"/>
      <inertia ixx="0.000867" ixy="0" ixz="0"
               iyy="0.000867" iyz="0" izz="0.001600"/>
    </inertial>
  </link>

  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel_link"/>
    <origin xyz="0 0.17 -0.05" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="20.0" velocity="30.0"/>
    <dynamics damping="0.05" friction="0.0"/>
  </joint>
</robot>
```

이 예제에서 눈여겨볼 부분은 다음과 같다.

- `<visual>`은 RViz와 Gazebo에 그리는 형상을 정의한다. `<material>`의 `rgba`는 빨강·초록·파랑·투명도를 0~1 범위로 표현한다.
- `<collision>`은 접촉 판정에 사용하는 형상을 정의한다. 복잡한 메시 대신 직육면체(`box`), 원기둥(`cylinder`), 구(`sphere`)를 조합하면 물리 계산이 빠르고 안정적이다.
- `<inertial>`은 질량중심, 질량, 관성 텐서를 정의한다. Gazebo에서 움직이는 모든 링크에 물리적으로 타당한 관성을 두는 것을 원칙으로 한다.
- 조인트의 `<origin>`은 부모 프레임에서 본 조인트와 자식 링크의 기준 위치·방향이다. `xyz`의 단위는 m이고 `rpy`의 단위는 rad이다.
- `<axis>`는 조인트 좌표계에서 표현한 운동축이다. `0 1 0`은 바퀴가 로봇의 좌우축인 +y를 중심으로 회전한다는 의미이다.
- `<limit>`의 `effort`와 `velocity`는 최대 힘·토크와 최대 속도를 나타낸다. `continuous` 조인트에는 각도 상·하한이 없지만 이 두 값은 둘 수 있다.

파일을 검사하면 링크 수와 루트 링크, 조인트 연결 관계를 확인할 수 있다.

```bash
source /opt/ros/humble/setup.bash
check_urdf /tmp/minimal_robot.urdf
```

성공하면 `robot name is: minimal_robot`, `Successfully Parsed XML`과 링크 트리가 출력된다. XML 문법 오류뿐 아니라 존재하지 않는 부모·자식 링크와 트리 구조 오류도 이 단계에서 발견할 수 있다.

### 관성값 계산

질량이 \(m\), 변 길이가 \(x,y,z\)인 균일한 직육면체의 중심 관성은 다음과 같다.

\[
I_{xx}=\frac{m}{12}(y^2+z^2),\quad
I_{yy}=\frac{m}{12}(x^2+z^2),\quad
I_{zz}=\frac{m}{12}(x^2+y^2)
\]

질량이 \(m\), 반지름이 \(r\), 길이가 \(l\)이고 대칭축이 해당 좌표계의 +z인 균일한 원기둥의 중심 관성은 다음과 같다.

\[
I_{xx}=I_{yy}=\frac{m}{12}(3r^2+l^2),\quad
I_{zz}=\frac{mr^2}{2}
\]

위 최소 URDF의 숫자는 이 식으로 계산한 값이다. 실제 튜토리얼에서는 숫자를 반복해서 적지 않고 [`common.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/common.xacro)의 `box_inertial`, `cylinder_inertial` 매크로로 계산한다.

!!! danger "관성에 0을 넣지 않는다"
    대각 원소가 0이거나 음수인 관성 텐서는 이 실습의 크기가 있는 강체를 올바르게 표현하지 못한다. 경고만 피하려고 형상과 무관한 극단적으로 작은 값을 넣어도 수치 불안정이 생긴다. 실제 크기와 질량으로 계산한 값을 사용한다.

## 2. 조인트와 좌표계

조인트 타입은 허용할 상대 운동에 따라 선택한다.

| 타입 | 자유도 | 필수 또는 주요 요소 | 대표 사용처 |
| --- | --- | --- | --- |
| `fixed` | 0 | `parent`, `child`, `origin` | `base_footprint` → `base_link`, 센서 마운트 |
| `continuous` | 회전 1, 각도 제한 없음 | `axis`, `effort`, `velocity` | 구동 바퀴 |
| `revolute` | 회전 1, 각도 제한 있음 | `axis`, `lower`, `upper`, `effort`, `velocity` | Ackermann 조향축 |
| `prismatic` | 직선 1 | `axis`, `lower`, `upper`, `effort`, `velocity` | 리프트, 슬라이더 |

조향 조인트는 다음처럼 회전 한계까지 명시한다.

```xml
<joint name="front_left_steering_joint" type="revolute">
  <parent link="base_link"/>
  <child link="front_left_steering_link"/>
  <origin xyz="0.28 0.22 0" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-0.55" upper="0.55" effort="30.0" velocity="2.0"/>
  <dynamics damping="0.2" friction="0.05"/>
</joint>
```

ROS 모바일 로봇은 [REP-103](https://www.ros.org/reps/rep-0103.html)의 오른손 좌표계를 따른다.

- +x는 전방이다.
- +y는 좌측이다.
- +z는 위쪽이다.
- 양의 yaw는 위에서 볼 때 반시계 방향이다.
- 길이는 m, 각도는 rad, 시간은 s를 사용한다.

따라서 `cmd_vel.linear.x > 0`이면 전진하고 `cmd_vel.angular.z > 0`이면 좌회전하도록 바퀴 회전축와 플러그인의 왼쪽·오른쪽 조인트를 배치한다. 로봇이 뒤로 가거나 반대로 회전하면 조종 명령의 부호를 바꾸기 전에 조인트 회전축, 좌우 조인트 이름, 바퀴 회전 방향을 먼저 확인한다.

## 3. Xacro로 반복되는 구조 재사용하기

Xacro는 URDF XML에 변수와 함수 호출에 가까운 기능을 추가한다. 핵심 요소는 속성, 매크로, 불러오기, 매크로 호출이다.

### 속성과 매크로 정의

다음 코드는 [`common.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/common.xacro)의 구성 방식을 축약한 예이다. 매크로 파일은 자체 로봇을 만들지 않고 재사용할 정의만 제공한다.

```xml
<?xml version="1.0"?>
<!-- urdf/common.xacro -->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:property name="PI" value="3.141592653589793"/>

  <xacro:macro name="cylinder_inertial"
               params="mass radius length origin_rpy:='0 0 0'">
    <inertial>
      <origin xyz="0 0 0" rpy="${origin_rpy}"/>
      <mass value="${mass}"/>
      <inertia
        ixx="${mass * (3.0 * radius * radius + length * length) / 12.0}"
        ixy="0" ixz="0"
        iyy="${mass * (3.0 * radius * radius + length * length) / 12.0}"
        iyz="0"
        izz="${mass * radius * radius / 2.0}"/>
    </inertial>
  </xacro:macro>

  <xacro:macro name="simple_wheel"
               params="name parent xyz radius width mass">
    <link name="${name}_link">
      <visual>
        <origin xyz="0 0 0" rpy="${PI / 2.0} 0 0"/>
        <geometry>
          <cylinder radius="${radius}" length="${width}"/>
        </geometry>
      </visual>
      <collision>
        <origin xyz="0 0 0" rpy="${PI / 2.0} 0 0"/>
        <geometry>
          <cylinder radius="${radius}" length="${width}"/>
        </geometry>
      </collision>
      <xacro:cylinder_inertial
        mass="${mass}"
        radius="${radius}"
        length="${width}"
        origin_rpy="${PI / 2.0} 0 0"/>
    </link>

    <joint name="${name}_joint" type="continuous">
      <parent link="${parent}"/>
      <child link="${name}_link"/>
      <origin xyz="${xyz}" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
      <limit effort="20.0" velocity="30.0"/>
      <dynamics damping="0.05" friction="0.0"/>
    </joint>
  </xacro:macro>
</robot>
```

각 문법은 다음 역할을 한다.

- `<xacro:property>`는 파일 범위에서 재사용할 값을 선언한다. `PI`, 바퀴 반지름·윤거처럼 여러 계산에서 공유하는 값에 주로 사용한다.
- `<xacro:macro>`는 반복할 XML 구조와 입력 파라미터를 선언한다. 위 `simple_wheel`은 링크와 조인트를 항상 한 쌍으로 생성한다.
- `params`는 공백으로 구분한 매크로 파라미터 목록이다. `origin_rpy:='0 0 0'`처럼 기본값도 지정할 수 있다.
- `${...}`는 수식 평가 구문이다. 사칙연산과 전달받은 파라미터를 사용하여 최종 XML 속성값을 만든다.

### 불러오기와 매크로 호출

메인 Xacro에서는 매크로 파일을 불러온 뒤 좌우 바퀴에 서로 다른 값을 전달한다. 다음 코드는 [`diffbot.urdf.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro)에서 실제로 사용하는 패턴이다.

```xml
<?xml version="1.0"?>
<!-- urdf/diffbot.urdf.xacro -->
<robot name="diffbot" xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:include
    filename="$(find gazebo_tutorial_description)/urdf/common.xacro"/>

  <xacro:property name="wheel_radius" value="0.09"/>
  <xacro:property name="wheel_width" value="0.04"/>
  <xacro:property name="wheel_mass" value="0.55"/>
  <xacro:property name="wheel_separation" value="0.36"/>
  <xacro:property name="wheel_x" value="0.075"/>
  <xacro:property name="wheel_z" value="-0.03"/>

  <!-- 이 앞에 base_link 정의를 둔다. -->

  <xacro:simple_wheel
    name="left_wheel"
    parent="base_link"
    xyz="${wheel_x} ${wheel_separation / 2.0} ${wheel_z}"
    radius="${wheel_radius}"
    width="${wheel_width}"
    mass="${wheel_mass}"/>

  <xacro:simple_wheel
    name="right_wheel"
    parent="base_link"
    xyz="${wheel_x} ${-wheel_separation / 2.0} ${wheel_z}"
    radius="${wheel_radius}"
    width="${wheel_width}"
    mass="${wheel_mass}"/>
</robot>
```

`$(find gazebo_tutorial_description)`은 설치된 패키지의 공유 파일 경로를 찾는다. 따라서 다른 패키지에서 불러오더라도 현재 작업 디렉터리에 의존하지 않는다. `left_wheel`과 `right_wheel` 호출은 같은 구조를 재사용하고 y 위치의 부호만 다르게 계산한다. 바퀴 반지름을 바꾸면 형상, 관성, 위치 계산과 구동 플러그인 값을 같은 속성에서 파생하도록 구성하는 편이 좋다.

!!! note "코드 조각과 실제 파일의 차이"
    위 메인 코드는 불러오기와 호출 관계를 강조하려고 `base_link` 본문을 생략한 조각이다. 실행 가능한 전체 모델은 [`diffbot.urdf.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro)에 있고, 실제 공통 매크로는 [`common.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/common.xacro)에 있다.

### 인자와 조건을 활용한 변형 선택

실행 파일에서 선택할 기능에는 속성보다 `<xacro:arg>`가 적합하다. 다음은 저장소의 `sensor_bot.urdf.xacro`가 지원하는 센서 구성을 실제로 바꾸어 보는 실습이다. 아래 명령은 저장소를 빌드한 뒤 실행한다.

```bash
source /opt/ros/humble/setup.bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source install/setup.bash

xacro src/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro \
  sensor_profile:=minimal > /tmp/sensor_bot_minimal.urdf
xacro src/gazebo_tutorial_description/urdf/sensor_bot.urdf.xacro \
  sensor_profile:=cameras > /tmp/sensor_bot_cameras.urdf
check_urdf /tmp/sensor_bot_minimal.urdf
check_urdf /tmp/sensor_bot_cameras.urdf
```

두 결과 모두 앞바퀴가 조향하는 4륜 Ackermann 차체와 IMU를 사용한다. 두 결과를 비교하면 `cameras`에서 카메라 링크와 광학 프레임이 추가된 것을 볼 수 있다. `sensor_profile`은 센서 묶음만 바꾸며 차량의 구동 방식은 바꾸지 않는다.

```bash
rg '<link name=' /tmp/sensor_bot_minimal.urdf
rg '<link name=' /tmp/sensor_bot_cameras.urdf
```

`<xacro:arg>`는 명령행에서 값을 받을 인자를 선언하고, `<xacro:if>`는 조건에 맞을 때만 XML을 생성한다. 반복되는 바퀴·센서는 매크로에 두고, 메인 파일은 매크로를 조립하도록 나누면 어떤 구성이 어떤 링크와 플러그인을 만드는지 파악하기 쉽다.

### Xacro 생성 결과 검사

Xacro 원본이 XML 구문 검사를 통과해도 매크로 호출 뒤에 중복 이름이나 잘못된 부모가 생길 수 있다. Gazebo를 띄우기 전에 완전한 URDF를 만들고 검사한다.

```bash
source /opt/ros/humble/setup.bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source install/setup.bash

xacro \
  src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro \
  > /tmp/diffbot.urdf

check_urdf /tmp/diffbot.urdf
```

`xacro`는 `${...}`, 불러오기, 매크로 호출을 모두 해석하여 표준 URDF만 출력한다. `check_urdf`는 그 결과의 XML과 링크·조인트 트리를 검사한다. 오류가 나면 Gazebo를 실행하기 전에 해당 파일의 이름과 연결 관계를 수정한다.

## 4. URDF의 Gazebo Classic 확장

표준 URDF만으로는 ODE 접촉 물성, Gazebo 재질, 센서, Gazebo 플러그인을 충분히 표현할 수 없다. Gazebo Classic은 이를 위해 `<gazebo>` 확장 블록을 읽는다.

### 특정 링크의 접촉 물성 추가

`reference`가 있는 블록은 이미 정의한 링크 또는 조인트에 Gazebo 전용 속성을 추가한다. 다음 코드는 바퀴 링크의 마찰과 접촉 해석기 파라미터를 설정한다.

```xml
<gazebo reference="left_wheel_link">
  <material>Gazebo/Black</material>
  <mu1>1.2</mu1>
  <mu2>1.2</mu2>
  <kp>1000000.0</kp>
  <kd>10.0</kd>
  <minDepth>0.001</minDepth>
  <maxVel>0.1</maxVel>
</gazebo>
```

| 파라미터 | 의미 | 조정할 때의 관찰점 |
| --- | --- | --- |
| `material` | Gazebo Classic 렌더링 재질이다 | RViz의 URDF 재질과 별개이다 |
| `mu1`, `mu2` | ODE 접촉면의 두 마찰 방향 계수이다 | 너무 낮으면 헛돌고 너무 높으면 급격한 접촉력이 생길 수 있다 |
| `kp` | 접촉을 스프링처럼 처리할 때의 강성이다 | 너무 낮으면 바닥에 깊이 잠기며 너무 높으면 떨림이 생길 수 있다 |
| `kd` | 접촉 감쇠이다 | `kp`와 함께 튜닝하며 반발과 떨림을 줄인다 |
| `minDepth` | 해석기가 유지하려는 최소 접촉 깊이이다 | 접촉한 두 형상이 조금 겹치도록 허용해 떨림을 줄인다 |
| `maxVel` | 접촉 오차 보정 속도의 상한이다 | 큰 값은 튀는 현상을 키울 수 있다 |

이 저장소는 같은 구성을 [`common.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/common.xacro)의 `gazebo_contact`와 `simple_wheel` 매크로에 넣어 모든 바퀴에 일관되게 적용한다.

### 모델 전체에 구동 플러그인 추가

`reference`가 없는 `<gazebo>` 블록은 로봇 모델 전체에 적용할 모델 플러그인을 두는 데 사용한다. 다음 코드는 [`diffbot.urdf.xacro`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro)의 차동구동 설정을 축약한 코드이다.

```xml
<gazebo>
  <plugin name="diffbot_diff_drive" filename="libgazebo_ros_diff_drive.so">
    <ros>
      <namespace>/</namespace>
      <remapping>cmd_vel:=cmd_vel</remapping>
      <remapping>odom:=odom</remapping>
    </ros>
    <update_rate>50.0</update_rate>

    <left_joint>left_wheel_joint</left_joint>
    <right_joint>right_wheel_joint</right_joint>
    <wheel_separation>${wheel_separation}</wheel_separation>
    <wheel_diameter>${2.0 * wheel_radius}</wheel_diameter>

    <max_wheel_torque>20.0</max_wheel_torque>
    <max_wheel_acceleration>5.0</max_wheel_acceleration>
    <odometry_source>0</odometry_source>
    <odometry_frame>odom</odometry_frame>
    <robot_base_frame>base_footprint</robot_base_frame>
    <publish_odom>true</publish_odom>
    <publish_odom_tf>true</publish_odom_tf>
    <publish_wheel_tf>false</publish_wheel_tf>
  </plugin>
</gazebo>
```

| 파라미터 | 역할 |
| --- | --- |
| `left_joint`, `right_joint` | 플러그인이 속도를 적용할 바퀴 조인트 이름이다. URDF 이름과 한 글자까지 같아야 한다 |
| `wheel_separation` | 좌우 바퀴 접촉 중심 사이 거리이다. 단위는 m이다 |
| `wheel_diameter` | 구동 바퀴 지름이다. 단위는 m이며 형상 반지름의 두 배와 일치해야 한다 |
| `update_rate` | 플러그인 갱신 주파수이다. 단위는 Hz이다 |
| `max_wheel_torque` | 바퀴 조인트에 적용할 최대 토크이다 |
| `max_wheel_acceleration` | 바퀴 속도 변화율 상한이다 |
| `odometry_source` | `0`은 바퀴 회전량 적분, `1`은 Gazebo 월드 기준 위치·자세를 사용한다. 이 튜토리얼은 휠 오도메트리 확인을 위해 `0`을 사용한다 |
| `odometry_frame` | `nav_msgs/Odometry.header.frame_id`와 odom TF의 부모 프레임이다 |
| `robot_base_frame` | odom TF의 자식 프레임이다 |
| `publish_odom`, `publish_odom_tf` | 오도메트리 메시지와 TF 발행 여부이다 |
| `publish_wheel_tf` | 플러그인의 바퀴 TF 발행 여부이다. `robot_state_publisher`와 중복되지 않도록 `false`로 둔다 |

`filename`은 ROS 2 Humble과 Gazebo Classic 11의 `libgazebo_ros_diff_drive.so`를 사용한다. Gazebo Harmonic용 시스템 플러그인은 이름과 설정 형식이 달라 그대로 사용할 수 없다.

Gazebo가 URDF를 SDF로 변환할 때 특정 고정 조인트와 자식 링크를 병합하지 않고 남겨 두려면 다음 확장을 추가한다.

```xml
<gazebo reference="camera_mount_joint">
  <preserveFixedJoint>true</preserveFixedJoint>
</gazebo>
```

ROS의 `robot_state_publisher`는 원래 URDF를 사용하므로 Gazebo 내부에서 링크를 병합해도 URDF에 있는 고정 TF는 발행한다. 이 옵션은 Gazebo 플러그인이 병합 전 링크·조인트를 직접 찾아야 하는 경우에 검토한다. 단순 장식 링크까지 모두 보존하면 시뮬레이션 모델이 불필요하게 복잡해질 수 있다.

## 5. SDF 월드와 Gazebo 실행 조건

SDF는 `<world>` 안에 물리 설정, 플러그인, 조명, 모델을 함께 둘 수 있다. 다음 예제는 ODE 물리 설정, 지면, 조명, 고정된 장애물을 포함한 전체 SDF 월드이다. `nano /tmp/tutorial.world`로 아래 내용을 저장한다. 외부 모델 다운로드 없이 열 수 있도록 지면과 조명을 파일 안에 직접 정의한다.

```xml
<?xml version="1.0"?>
<sdf version="1.6">
  <world name="tutorial_world">
    <physics name="ode_physics" type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_update_rate>1000</real_time_update_rate>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <light name="sun" type="directional">
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
      <cast_shadows>true</cast_shadows>
    </light>
    <model name="ground_plane">
      <static>true</static>
      <link name="ground">
        <collision name="ground_collision">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
        </collision>
        <visual name="ground_visual">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <material><ambient>0.6 0.6 0.6 1</ambient></material>
        </visual>
      </link>
    </model>

    <model name="tutorial_obstacle">
      <static>true</static>
      <pose>1.5 0 0.25 0 0 0</pose>
      <link name="box_link">
        <collision name="box_collision">
          <geometry>
            <box>
              <size>0.5 0.5 0.5</size>
            </box>
          </geometry>
        </collision>
        <visual name="box_visual">
          <geometry>
            <box>
              <size>0.5 0.5 0.5</size>
            </box>
          </geometry>
          <material>
            <ambient>0.8 0.2 0.1 1</ambient>
            <diffuse>0.8 0.2 0.1 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
```

SDF의 `<pose>`는 `x y z roll pitch yaw` 순서이고 단위는 m와 rad이다. `tutorial_obstacle`의 중심을 z=0.25 m에 두었으므로 높이 0.5 m인 직육면체의 바닥이 지면에 닿는다.

| 요소 | 역할 |
| --- | --- |
| `max_step_size` | 물리 적분 한 단계의 시뮬레이션 시간이다 |
| `real_time_update_rate` | 초당 목표 물리 계산 갱신 횟수이다 |
| `real_time_factor` | 시뮬레이션 시간과 실제 시간의 목표 비율이다 |
| `<include><uri>model://...` | Gazebo 모델 검색 경로에서 기존 모델을 불러온다 |
| `<static>true</static>` | 중력과 충돌력으로 움직이지 않는 환경 모델로 만든다 |

`max_step_size × real_time_update_rate`는 이론적인 최대 실시간 계수와 관계가 있다. 위 설정은 0.001 s를 초당 1000번 적분하므로 목표 1.0과 맞는다. 센서와 복잡한 충돌 형상이 많아 계산량이 커지면 실제 ROS 토픽 `/performance_metrics` 또는 Gazebo GUI의 실시간 계수는 목표보다 낮아질 수 있다.

이 저장소의 실제 월드는 [`empty.world`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_bringup/worlds/empty.world)와 [`sensor.world`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_bringup/worlds/sensor.world)에서 확인할 수 있다. [`simulation.launch.py`](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/ros2_ws/src/gazebo_tutorial_bringup/launch/simulation.launch.py)는 공식 `gazebo_ros/gazebo.launch.py`를 불러와 서버를 실행한다. `libgazebo_ros_init.so`와 `libgazebo_ros_factory.so`는 **서버용 SystemPlugin**이다. 전자는 ROS 연결·시뮬레이션 시계를, 후자는 모델 생성·삭제 서비스를 준비한다. 월드의 `<plugin>`에 넣지 않고 `gazebo_ros` 실행 파일이 `gzserver -s ...` 방식으로 불러오도록 한다.

작성한 월드를 검사한 뒤 ROS 연동을 포함해 실행한다. 이미 Gazebo가 실행 중이면 먼저 종료한다.

```bash
source /opt/ros/humble/setup.bash
gz sdf -k /tmp/tutorial.world
ros2 launch gazebo_ros gazebo.launch.py world:=/tmp/tutorial.world
```

검사가 성공하고 회색 바닥 위에 붉은 상자가 나타나면 정상이다. 이 예제는 환경만 정의하므로 로봇은 아직 나타나지 않는다. 창을 확인한 뒤 `Ctrl+C`로 종료한다.

저장소에서 제공하는 센서 실습 월드도 같은 도구로 검사할 수 있다.

```bash
gz sdf -k \
  ~/robotics-sim-tutorial-kr/ros2_ws/src/gazebo_tutorial_bringup/worlds/sensor.world
```

여기서 `gz sdf`는 Gazebo Classic의 SDF 검사·변환 명령이다. `gz sim`은 Gazebo Harmonic 계열 실행 명령이므로 이 튜토리얼에서 사용하지 않는다.

## 6. URDF에서 SDF로 변환한 결과 확인

Gazebo가 내부적으로 URDF를 변환한 SDF를 직접 출력하면 고정 조인트 병합, `<gazebo>` 확장 반영, 플러그인 파라미터 이름 문제를 찾기 쉽다.

```bash
source /opt/ros/humble/setup.bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source install/setup.bash

# 1) Xacro를 표준 URDF로 전개한다.
xacro \
  src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro \
  > /tmp/diffbot.urdf

# 2) ROS 관점의 링크·조인트 트리를 검사한다.
check_urdf /tmp/diffbot.urdf

# 3) Gazebo Classic의 URDF 변환기로 SDF를 출력한다.
gz sdf -p /tmp/diffbot.urdf > /tmp/diffbot.sdf

# 4) 출력된 SDF 자체도 검사한다.
gz sdf -k /tmp/diffbot.sdf

# 5) 변환 뒤 남은 link, joint, plugin 이름을 확인한다.
rg -n '<(link|joint|plugin) ' /tmp/diffbot.sdf
```

`gz sdf -p` 결과에서는 다음 항목을 확인한다.

- `left_wheel_joint`와 `right_wheel_joint`가 남아 있는지 확인한다.
- `libgazebo_ros_diff_drive.so` 플러그인과 바퀴 형상 값이 들어갔는지 확인한다.
- 보존하지 않은 고정 조인트의 자식 링크가 부모로 합쳐졌는지 확인한다.
- 센서의 위치·방향과 프레임 이름이 의도한 링크 기준으로 변환되었는지 확인한다.
- 변환 경고가 나오면 출력 파일만 보지 말고 터미널의 경고도 함께 확인한다.

URDF는 트리 기반 표현이고 SDF는 더 풍부한 모델 표현이므로 변환 결과가 원본 XML과 한 줄씩 같지는 않다. 중요한 기준은 ROS의 TF 구조와 Gazebo 내부 물리·플러그인 참조가 각각 의도대로 유지되는가이다.

## 7. 생성 과정의 데이터 흐름

통합 실행 파일에서는 다음 순서로 데이터가 흐른다.

1. 실행 파일이 Xacro 파일과 인자를 읽어 완전한 URDF 문자열을 만든다.
2. `robot_state_publisher`가 문자열을 `robot_description` 파라미터로 받는다.
3. `robot_state_publisher`가 발행한 `/robot_description`에서 `spawn_entity.py`가 XML을 받아 Gazebo의 모델 생성 서비스로 보낸다.
4. Gazebo가 URDF를 내부 SDF 모델로 변환하고 `<gazebo>` 센서와 플러그인을 로드한다.
5. 고정 조인트는 `/tf_static`에 나타나고, 움직이는 조인트는 `/joint_states`와 `robot_state_publisher`를 거쳐 `/tf`에 나타난다.
6. 구동 플러그인이 `/cmd_vel`을 받아 바퀴 조인트에 힘과 속도를 적용하고 `/odom`과 `odom→base_footprint`를 발행한다.

Gazebo에는 모델이 있는데 RViz RobotModel이 비어 있다면 생성 자체보다 `robot_description` 또는 TF를 먼저 확인한다. 반대로 RViz 모델은 정상인데 Gazebo에서 바퀴가 빠지거나 떨린다면 충돌 형상, 관성, 조인트, 접촉 설정, 플러그인을 확인한다.

## 8. 작성 직후 확인할 항목

- 모든 움직이는 링크에 크기·질량에 맞는 관성을 넣었는지 확인한다.
- 표시 형상과 충돌 형상의 위치와 크기가 의도대로 일치하는지 확인한다.
- 부모→자식 `origin`과 조인트 `axis`가 REP-103 관례에 맞는지 확인한다.
- 구동 바퀴는 `continuous`, 조향은 각도 한계가 있는 `revolute`인지 확인한다.
- 바퀴가 지면에 닿고 차체 충돌 형상은 지면보다 충분히 높은지 확인한다.
- 왼쪽·오른쪽 조인트 이름이 구동 플러그인 설정과 한 글자까지 같은지 확인한다.
- 바퀴 반지름과 중심 간격이 형상과 플러그인에서 같은 속성으로 파생되는지 확인한다.
- 재사용 요소가 별도 Xacro 매크로에 있고 메인 파일은 불러오기와 조립을 담당하는지 확인한다.
- 지원하는 모든 Xacro 구성을 전개하고 `check_urdf`로 검사했는지 확인한다.
- `gz sdf -p`와 `gz sdf -k`로 Gazebo가 실제로 읽을 구조까지 확인했는지 확인한다.
