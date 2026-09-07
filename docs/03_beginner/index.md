# 초급: Gazebo Sim으로 `tutorial_bot` 시작하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 시작하기

## 목표

초급 과정은 작은 SDF 월드를 켜보는 것부터 시작해, 같은 로봇에 기능을 한 단계씩 더하는 흐름으로 진행한다. GUI와 SDF를 먼저 익히고, Xacro로 차체와 바퀴를 만든 뒤 DiffDrive로 움직인다. 마지막에는 Gazebo Transport와 ROS 2를 연결해 키보드 명령, 바퀴 오도메트리, 센서 데이터를 직접 확인한다.

<figure class="course-figure">
  <img src="../assets/diagrams/beginner-learning-path.svg" alt="Gazebo 개요에서 첫 world 실행까지 이어지는 초급 학습 경로 도식" loading="lazy">
  <figcaption>그림 1. 개념을 읽은 뒤 같은 요소를 코드에서 찾고, 실행 결과를 관찰하는 순서로 진행한다.</figcaption>
</figure>

## 학습 흐름

1. Gazebo 서버, GUI, 시뮬레이션 시간, RTF를 직접 확인해본다.
2. SDF의 `world → model → link` 계층과 시스템 플러그인을 읽는다.
3. URDF와 Xacro로 차체, 좌우 구동 바퀴, 조인트를 단계적으로 구성한다.
4. `gz::sim::systems::DiffDrive`를 붙이고 직진·원호·제자리 회전을 검증한다.
5. `ros_gz_bridge`를 통해 키보드 조종과 바퀴 오도메트리를 ROS 2에 연결한다.
6. RViz의 Odometry와 Path 디스플레이에서 바퀴 회전으로 추정한 주행 궤적을 확인한다.
7. 센서를 추가하고 Fuel 모델까지 월드에 포함한다.

각 단계 Xacro는 앞에서 만든 부품 매크로를 재사용하는 로봇 정의 파일이다.

```xml
<!-- urdf/stages/03-diff-drive.xacro -->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="tutorial_bot">
  <xacro:include filename="../macros/stage_components.xacro"/>
  <xacro:stage_base/>
  <xacro:stage_wheels/>
  <xacro:stage_diff_drive/>
</robot>
```

이러한 학습 구조를 통해 차체만 있는 1단계, 조인트까지 있는 2단계, 구동 플러그인까지 있는 3단계를 서로 비교할 수 있다.

<pre class="course-mermaid">
flowchart TB
    A[Gazebo와 GUI 관찰] --> B[SDF world]
    B --> C[URDF와 Xacro]
    C --> D[바퀴와 joint]
    D --> E[DiffDrive]
    E --> F[Bridge와 teleop]
    F --> G[Odometry와 센서]
</pre>

## 시작 전 확인

[설치 안내](../02_getting-started/02_installation-jazzy.md)를 마친 상태에서 시작한다. 모든 상대 경로는 저장소 루트 기준이다. 새 터미널마다 다음 설정을 불러온다. 다른 위치에 복제했다면 `cd` 경로를 바꾼다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
pwd
```

`pwd`는 `robotics-sim-tutorial-kr`로 끝나는 경로를 출력해야 한다. `source`에 오류가 나면 설치 안내의 빌드를 먼저 마친다. 실행 중인 프로그램은 터미널을 점유하므로 다음 프로그램을 실행할 때는 새 터미널을 연다. `gz topic -e`, `ros2 topic hz`, `tf2_echo`는 계속 출력되므로 확인 후 `Ctrl+C`로 종료한다.

먼저 핵심 파일이 있는지 확인한다.

```bash
test -f examples/gazebo/worlds/first-world.sdf
test -f examples/ros2_ws/src/tutorial_bot_description/urdf/stages/03-diff-drive.xacro
test -f examples/ros2_ws/src/tutorial_bot_bringup/config/bridge.yaml
```

아무 출력 없이 종료 코드가 `0`이면 준비가 끝난 것이다. 빌드가 필요한 장에서는 다음처럼 예제 작업 공간을 먼저 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
cd ../..
```

## 초급 과정의 합격 기준

- GUI의 Entity Tree에 `ground`, `training_box`, `beacon`이 표시된다.
- `gz sdf -k`가 `Valid.`를 출력한다.
- `check_urdf`에서 `base_link`와 좌우 바퀴 링크의 트리를 확인한다.
- DiffDrive에 직진·원호·제자리 회전 명령을 보냈을 때 `/odom`의 위치와 yaw가 예상 방향으로 변한다.
- 키보드 조종 명령이 ROS `/cmd_vel`에서 Gazebo `/model/tutorial_bot/cmd_vel`까지 전달된다.
- RViz에서 `/odom` 표본이 화살표 궤적으로 누적된다.
- LiDAR, 카메라, IMU 메시지의 크기·프레임·주기를 실제 토픽에서 확인한다.

## 막히면

GUI가 열리지 않거나 렌더링이 깨지면 [문제 해결](../02_getting-started/03_troubleshooting.md)을 먼저 확인한다. 상대 경로 오류가 나면 `pwd`로 현재 위치를 확인하고, ROS 패키지를 찾지 못하면 `/opt/ros/jazzy/setup.bash`와 작업 공간의 `install/setup.bash`를 차례로 불러온다.

[다음: Gazebo Sim 개요](01-gazebo-overview.md)
