# 8. Gazebo Classic 11과 ROS 2 Humble 문제 해결

로봇이 보이지 않거나 센서 데이터가 이상할 때는 **실행 상태 → 시뮬레이션 시간 →
로봇 생성 → 토픽·QoS → TF** 순서로 확인한다. 이 순서대로 정상인 부분을 제외하면
화면만 보고 추측하는 것보다 원인을 빨리 찾을 수 있다.

이 장의 명령은 [환경 설정](01_setup.md)을 마치고 `Humble` 브랜치 전체를
빌드한 환경을 기준으로 한다. 센서 토픽을 확인하는 절에서는 차동 구동 예제를
종료하고 `sensors.launch.py`를 실행한다. 예제 실행 파일은 각각 Gazebo를 시작하므로
두 개를 동시에 실행하지 않는다.

## 8.1 먼저 실행 상태부터 확인하기

**터미널 1**에서 기본 로봇을 실행한다. Gazebo와 RViz 창이 열리고 로봇 생성 완료
메시지가 나올 때까지 기다린다. 이 터미널은 실습이 끝날 때까지 켜 둔다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py verbose:=true
```

**터미널 2**에도 같은 환경을 불러온다. 이후 검사 명령은 이 터미널에서 실행한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 node list
ros2 service type /spawn_entity
ros2 topic echo /clock --once
ros2 topic echo /odom --once --field header --qos-reliability best_effort
ros2 topic info /odom --verbose
```

| 확인 항목 | 정상일 때 보이는 내용 |
|---|---|
| 노드 목록 | `/robot_state_publisher`, `/odom_to_path`, `/rviz2` 등 |
| 생성 서비스 자료형 | `gazebo_msgs/srv/SpawnEntity` |
| `/clock` | `clock.sec`, `clock.nanosec`에 시뮬레이션 시각 표시 |
| `/odom` 헤더 | `frame_id: odom`과 시각 표시 |
| `/odom` 상세 정보 | 발행자가 1개 이상이며 자료형은 `nav_msgs/msg/Odometry` |

`--once`는 메시지를 한 번 받은 뒤 종료한다. 데이터가 오지 않으면 계속 기다리므로
10초 정도 지나도 출력이 없으면 `Ctrl+C`로 중단하고 앞 단계부터 점검한다.

주파수와 좌표 변환은 아래 명령을 **하나씩** 실행해 확인한다. 각 명령은 자동으로
끝나지 않으므로 결과가 나오면 `Ctrl+C`로 종료한 뒤 다음 명령을 실행한다.

```bash
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_link --ros-args -p use_sim_time:=true
```

기본 차동 구동 플러그인의 설정은 시뮬레이션 시간 기준 50 Hz다. `ros2 topic hz`가
기본적으로 측정하는 실제 시간과는 다르므로, 시뮬레이션이 느리면 더 낮게 보인다.
TF가 연결되어 있다면 위치와 회전 값이 반복해서 출력된다.

## 8.2 시뮬레이션이 일시 정지되어 있을 때

`pause:=true`로 실행했거나 Gazebo에서 일시 정지를 누르면 물리 계산과 센서 갱신이
멈춘다. 로봇 생성에 성공했더라도 센서 토픽에 새 데이터가 오지 않을 수 있다.

```bash
ros2 service call /unpause_physics std_srvs/srv/Empty "{}"
ros2 topic echo /clock --once
```

서비스 호출이 응답한 뒤 `/clock`을 다시 두세 번 확인한다. 값이 증가해야 시간이
흐르고 있는 것이다. 토픽 목록에 `/clock`이 있다는 사실만으로 판단하지 않는다.

정지 상태에서 시작하려면 터미널 1의 기존 실행을 `Ctrl+C`로 끝내고 다시 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py pause:=true
```

노드가 준비되면 터미널 2에서 `/unpause_physics`를 호출한다. 반대로 정지할 때는
`/pause_physics`에 같은 `std_srvs/srv/Empty` 요청을 보낸다.

## 8.3 ROS 노드가 서로 다른 시계를 사용할 때

Gazebo 데이터는 `/clock`의 시뮬레이션 시각을 사용한다. 다른 노드가 컴퓨터의 실제
시계를 사용하면 TF를 요청한 시각과 저장된 시각이 크게 달라져
`extrapolation into the past/future` 오류가 날 수 있다.

```bash
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /odom_to_path use_sim_time
ros2 param get /rviz2 use_sim_time
```

세 노드가 실행 중이라면 모두 `Boolean value is: True`여야 한다. `rviz:=false`로
실행했다면 `/rviz2`가 없는 것이 정상이다. 먼저 `ros2 node list`로 실행 여부를 확인한다.
별도로 연 RViz에는 다음과 같이 시뮬레이션 시간 사용을 지정한다.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

시뮬레이션을 초기화하면 시간이 뒤로 돌아간다. `odom_to_path`는 이를 감지해 이전
경로를 지운다. 다른 필터나 추정 노드가 과거 데이터를 계속 보관한다면 해당 노드를
다시 시작해야 할 수 있다.

## 8.4 로봇이 생성되지 않을 때

로봇 생성은 Xacro 전개, 로봇 설명 발행, Gazebo 생성 서비스 호출 순서로 진행된다.
다음 명령으로 어느 단계가 실패하는지 확인한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
xacro src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro > /tmp/diffbot.urdf
check_urdf /tmp/diffbot.urdf
ros2 topic echo /robot_description --once --qos-durability transient_local
ros2 service type /spawn_entity
```

`check_urdf`가 없다면 `sudo apt install liburdfdom-tools`로 설치한다. 이 검사는
링크·조인트 구조가 읽히는지 확인하지만 질량, 마찰, 접촉 안정성까지 보장하지는 않는다.
`/robot_description`은 새 구독자에게도 기존 설명을 전달하도록
`transient_local`로 구독한다.

- Xacro가 실패하면 오류에 나온 파일 경로와 줄 번호, 닫히지 않은 XML 태그를 확인한다.
- 로봇 설명이 없으면 `robot_state_publisher`가 실행됐는지 확인한다.
- `/spawn_entity`가 없으면 Gazebo 서버의 시작 로그와 플러그인 로드 오류를 확인한다.
- 생성 직후 로봇이 튀거나 쓰러지면 양의 질량·관성값, 충돌 형상 겹침, 초기 높이를 확인한다.

초기 높이를 바꿔 비교할 때는 기존 실행을 종료한 뒤 다시 시작한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py z:=0.2 verbose:=true
```

초기 높이는 낙하 후 바닥에 안착하는 데도 영향을 준다. 화면에 잠깐 나타난 것만으로
성공했다고 판단하지 말고 몇 초 뒤에도 자세가 안정적인지 확인한다.

## 8.5 로봇·노드 이름이 충돌할 때

`Entity [diffbot] already exists`는 같은 Gazebo 서버에 이미 `diffbot` 모델이 있다는
뜻이다. 단일 로봇 실습에서는 기존 실행을 종료한 뒤 다시 실행하는 것이 가장 간단하다.
`entity_name`만 바꿔 또 실행해도 ROS 토픽이나 TF 이름은 분리되지 않는다.

Gazebo 서버를 유지한 채 모델만 삭제할 때는 이름을 확인하고 다음 서비스를 호출한다.
이 명령은 `diffbot` 모델을 실제로 제거한다.

```bash
ros2 service call /delete_entity gazebo_msgs/srv/DeleteEntity "{name: diffbot}"
```

여러 로봇을 동시에 사용하는 구성에서는 다음 이름을 함께 분리해야 한다.

- Gazebo 모델 이름인 `entity_name`
- ROS 네임스페이스와 노드 이름
- `/cmd_vel`, `/odom`, `/joint_states` 및 센서 토픽
- `odom`, `base_footprint`, `base_link`, 센서 링크를 포함한 TF 프레임
- 구동 플러그인의 네임스페이스와 프레임 설정

`Ctrl+C`로 종료했는데 Gazebo가 남아 있다면 실행 중인 프로세스를 확인한다.

```bash
ps -eo pid,ppid,args | rg '[g]zserver|[g]zclient'
```

표의 명령줄과 부모 PID를 보고 이 실습에서 시작한 프로세스인지 확인한다. 해당 PID가
예를 들어 `12345`라면 `kill -INT 12345`로 종료를 요청한다. 예제 숫자를 그대로 쓰지
말고 실제 PID로 바꾼다.

## 8.6 토픽은 있는데 데이터가 오지 않을 때: QoS

ROS 2에서는 토픽 이름과 자료형이 같아도 발행자와 구독자의 QoS 설정이 호환되지
않으면 데이터를 받지 못한다. 센서에 따라 기본값이 다를 수 있으므로 실제 설정을 확인한다.

센서를 검사하려면 터미널 1의 기존 실행을 종료한 뒤 다음 예제를 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py sensor_profile:=all
```

터미널 2에서 토픽별 발행자와 구독자의 설정을 확인한다.

```bash
ros2 topic info /scan --verbose
ros2 topic info /points --verbose
ros2 topic info /wheel_odom_path --verbose
```

| 데이터 | 구독자 설정 | 이유 |
|---|---|---|
| 영상·라이다·점군·IMU | Best Effort + Volatile | Reliable과 Best Effort 센서 발행자 모두에서 새 데이터를 받을 수 있음 |
| 오도메트리 입력 | Best Effort + Volatile | 발행자의 신뢰성 설정 차이에 대응 |
| 누적 경로인 Path | Reliable + Transient Local | 호환되는 발행자로부터 늦게 접속해도 최신 전체 경로 수신 |
| `/tf_static` | Reliable + Transient Local | 고정 변환을 나중에 시작한 구독자에게도 전달 |

RViz에서는 표시 항목의 **Topic → Reliability Policy**와 **Durability Policy**를
확인한다. 센서는 `Best Effort`·`Volatile`, 제공된 Path는 `Reliable`·`Transient Local`로
설정한다. `Incompatible QoS` 경고가 있다면 발행자가 제공하는 설정과 비교한다.
큐 크기(depth)가 서로 다르다는 이유만으로 연결이 거부되지는 않는다.

## 8.7 RViz의 좌표 변환·센서 방향 오류

토픽이 갱신되는데 RViz에 표시되지 않으면 메시지의 프레임부터 확인한다.

```bash
ros2 topic echo /scan --once --field header --qos-reliability best_effort
ros2 topic echo /points --once --field header --qos-reliability best_effort
ros2 run tf2_ros tf2_echo odom lidar_2d_link --ros-args -p use_sim_time:=true
```

마지막 명령은 좌표 변환을 확인한 뒤 `Ctrl+C`로 종료한다.

1. 센서 실습의 `sensors.rviz`는 **Fixed Frame**을 `world`로 사용한다.
   주행·경로 실습의 `odom.rviz`는 `odom`을 사용한다. 실행한 설정에 맞는지 확인한다.
2. 센서 메시지의 `header.frame_id`가 실제 센서 좌표계와 같은지 확인한다.
3. `odom → base_footprint → base_link → 센서 링크`가 이어지는지 확인한다.
4. 고정 조인트는 `/tf_static`, 바퀴 등 움직이는 조인트는 `/joint_states`와 `/tf`를 확인한다.
5. 같은 자식 프레임을 두 노드가 동시에 발행하지 않는지 확인한다.

```bash
ros2 run tf2_tools view_frames --ros-args -p use_sim_time:=true
ros2 topic info /tf --verbose
ros2 topic info /tf_static --verbose
```

`view_frames`는 몇 초 동안 TF를 수집한 뒤 현재 폴더에 그림 파일을 만든다.
파일명이 로그에 출력되면 열어서 연결이 끊긴 지점을 찾는다.

메시지의 `frame_id`만 바꾸는 것은 좌표 변환이 아니다. 예를 들어 카메라의 optical
좌표계는 +z가 전방, +x가 오른쪽, +y가 아래쪽이다. 로봇 본체의 +x 전방 좌표계와
그대로 혼용하면 점군이 옆으로 눕거나 바닥을 향할 수 있다. 플러그인이 실제로
내보내는 좌표축을 확인하고 URDF의 고정 회전과 메시지 프레임을 함께 맞춰야 한다.
구체적인 센서별 확인 절차는 [센서 실습](05_sensors.md)을 따른다.

센서 설정의 IMU 표시는 월드 기준 자세를 사용한다. **Fixed Frame**을 임의로
바꾸거나 IMU의 자세를 센서 장착 회전과 중복 적용하면 표시 방향이 틀어질 수 있다.

RobotModel이 비어 있다면 **Description Topic**이 `/robot_description`인지,
해당 토픽의 **Durability Policy**가 `Transient Local`인지 확인한다. 센서가 바닥을
보고 있다면 TF뿐 아니라 Gazebo 속 로봇 자체가 기울어져 있지 않은지도 확인한다.

## 8.8 `/cmd_vel`을 보내도 움직이지 않을 때

키보드 입력 문제를 제외하려면 일정한 속도를 직접 보낸다. 다음 직진·정지 명령은
차동구동 모델과 4륜 Ackermann 센서 모델에서 모두 사용할 수 있다. 다른 조종 노드가
실행 중이면 먼저 정지하고 종료해 명령이 겹치지 않게 한다.

```bash
ros2 topic pub --rate 10 --times 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.15}, angular: {z: 0.0}}"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

첫 명령은 전진 명령을 20번 보낸 뒤 끝난다. **명령 발행이 끝나는 것과 로봇이
정지하는 것은 다르므로 두 번째 정지 명령도 실행한다.** 이어서 상태를 확인한다.

```bash
ros2 topic info /cmd_vel --verbose
ros2 topic echo /odom --once --field pose.pose --qos-reliability best_effort
ros2 topic echo /joint_states --once --qos-reliability best_effort
```

| 증상 | 확인할 부분 |
|---|---|
| `/cmd_vel` 구독자가 0개 | 구동 플러그인 로드, 토픽 이름, 네임스페이스 |
| 구독자는 있지만 바퀴가 안 돎 | 조인트 이름, 구동 플러그인 파라미터, 일시 정지 여부 |
| 바퀴는 도는데 차체가 안 움직임 | 바닥 접촉, 마찰, 충돌 형상, 토크 한도 |
| Ackermann 로버·센서 차량이 안 꺾임 | `linear.x`도 0보다 크게 보냈는지, 조향 조인트 축·한도, 축간거리, 좌우 바퀴 간격 |
| Ackermann `/odom`이 없음 | `/ackermann_odom` 노드와 두 뒷바퀴·두 앞 조향 조인트의 상태 |

Ackermann 차량에서는 `angular.z`가 각속도(rad/s)가 아닌 조향 목표각(rad)이다. 예를 들어 `{linear: {x: 0.15}, angular: {z: 0.20}}`은 천천히 전진하면서 왼쪽으로 도는 명령이다. `linear.x: 0.0`인 채 조향각만 주면 바퀴 방향은 바뀌어도 제자리 회전하지 않는다.

## 8.9 플러그인이 로드되지 않을 때

`Failed to load plugin ... .so`가 나오면 파일 경로와 연결된 라이브러리를 확인한다.
실행 중인 시뮬레이션을 종료한 뒤 같은 Humble 환경에서 다시 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
plugin_prefix="$(ros2 pkg prefix gazebo_tutorial_plugins)"
ls -l "${plugin_prefix}/lib/libground_truth_path_plugin.so"
ldd "${plugin_prefix}/lib/libground_truth_path_plugin.so"
```

`ldd` 출력에 `not found`가 있으면 해당 의존성을 설치한다. 다른 ROS 배포판이나
Gazebo 버전에서 만든 `.so`를 복사했다면 Humble·Gazebo 11 환경에서 다시 빌드한다.

이 패키지는 `package.xml`에서 `plugin_path="${prefix}/../../lib"`를 내보낸다.
`${prefix}`는 설치된 패키지의 **share 폴더**이며, `gazebo_ros` 실행 파일이 이 경로를
읽어 Gazebo의 검색 경로에 추가한다. 부모 터미널의 `GAZEBO_PLUGIN_PATH`만 보고
실패라고 판단하지 않는다. 자세한 설명은 [플러그인 개발](07_custom_plugin.md)의
검색 경로 절을 참고한다.

설정이 의심되면 Xacro를 전개한 URDF와 Gazebo가 읽을 SDF를 대조한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
xacro src/gazebo_tutorial_description/urdf/diffbot.urdf.xacro > /tmp/diffbot.urdf
rg -n -A35 -B3 'libgazebo_ros_diff_drive.so' /tmp/diffbot.urdf
gz sdf -p /tmp/diffbot.urdf > /tmp/diffbot.sdf
rg -n -A35 -B3 'libgazebo_ros_diff_drive.so' /tmp/diffbot.sdf
```

두 결과에서 조인트 이름, 바퀴 간격·지름, 토픽 이름 재지정 설정이 같은지 확인한다.
`gz sdf` 변환 단계에서 나온 경고도 함께 읽는다.

### CI에서 ROS 환경을 읽다가 실패할 때

Bash의 `set -u`가 켜진 상태에서 ROS 환경을 읽으면 환경 스크립트의 미정의 변수 때문에
`unbound variable`로 종료될 수 있다. 자동 검사에서는 환경을 먼저 읽고 `-u`를 켠다.

```bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
set -u
ros2 pkg prefix gazebo_tutorial_description
```

## 8.10 화면 없이 검사할 때

원격 서버나 CI에서는 Gazebo와 RViz 창을 끄고 서버만 실행할 수 있다.
기존 실행을 종료한 뒤 터미널 1에서 시작한다.

```bash
ros2 launch gazebo_tutorial_bringup diffbot.launch.py \
  gui:=false rviz:=false verbose:=true
```

터미널 2에서 `/clock`, `/odom`, TF를 확인하고 8.8절의 전진·정지 명령 전후 위치를
비교한다. 프로세스가 살아 있다는 사실만으로 센서나 주행이 정상이라고 판단하지 않는다.

RGB·RGB-D·어안 카메라는 Gazebo 창을 꺼도 서버 안에서 영상을 렌더링한다.
디스플레이가 없는 환경에서 OGRE가 화면을 만들지 못한다면 Xvfb를 사용할 수 있다.

```bash
sudo apt install -y xvfb xauth
xvfb-run -a ros2 launch gazebo_tutorial_bringup sensors.launch.py \
  gui:=false rviz:=false sensor_profile:=cameras
```

이 명령도 계속 실행되므로 실습이 끝나면 `Ctrl+C`로 종료한다. 영상 없이 라이다와
IMU를 먼저 검사하려면 별도로 다음 구성을 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup sensors.launch.py \
  gui:=false rviz:=false sensor_profile:=lidars
```

## 8.11 시뮬레이션이 느릴 때

실시간 비율(RTF)은 시뮬레이션 시간이 실제 시간보다 얼마나 빨리 흐르는지 나타낸다.
RTF가 0.5라면 실제 2초 동안 시뮬레이션에서 1초가 흐른다. 다음 명령을 각각 실행하고
출력 확인 후 `Ctrl+C`로 종료한다.

```bash
gz stats -p
ros2 topic hz /camera/image_raw
ros2 topic hz /points
```

| 부하가 큰 부분 | 줄여 볼 설정 | 변경 후 다시 확인할 점 |
|---|---|---|
| RGB-D·스테레오·어안 카메라 | 해상도와 `update_rate` | 영상 크기와 CameraInfo가 일치하는지, 필요한 움직임을 관측할 수 있는지 |
| 3D 라이다 | 수평·수직 샘플 수 | 시야각과 각도 간격이 실습에 충분한지 |
| RViz 점군 | 보관 시간(Decay Time), 대기열 크기 | 원본 센서 속도와 화면 표시 속도를 구분했는지 |
| Gazebo·RViz 창 | `gui:=false rviz:=false` | 카메라 렌더링은 여전히 필요한지 |
| 센서 수 | `sensor_profile:=minimal`부터 시작 | 추가한 센서 때문에 느려지는지 |
| 물리 계산 | `real_time_update_rate`, 반복 계산 횟수 | 접촉 안정성과 주행 결과가 유지되는지 |

`max_step_size`를 크게 하면 바퀴 접촉이나 빠른 운동을 놓칠 수 있다. 속도뿐 아니라
주행 경로, 차체 자세, 센서 측정값도 변경 전후에 비교한다. 계산 결과의 재현성은
물리 엔진, 센서 노이즈, 병렬 처리 등에도 영향을 받으므로 RTF만으로 판단하지 않는다.

경로 표시가 너무 길다면 기존 실행을 종료하고 기록 개수를 줄여 다시 실행한다.

```bash
ros2 launch gazebo_tutorial_bringup rover_diff.launch.py max_points:=500
```

## 8.12 문제를 재현할 수 있게 기록하기

다음 정보를 모으면 다른 사람이 같은 증상을 재현하기 쉽다.

- Ubuntu·ROS 2·Gazebo의 버전과 사용한 커밋
- 실행 명령과 바꾼 인자, 수정한 모델·월드
- 최초 오류 이전부터 포함한 실행 로그
- `ros2 node list`, `ros2 topic list`, 문제 토픽의 `--verbose` 출력
- `view_frames` 결과와 RViz의 Fixed Frame
- 화면 사용 여부, 센서 구성, RTF

터미널 2에서 버전과 현재 커밋을 확인한다.

```bash
cd ~/robotics-sim-tutorial-kr
cat /etc/os-release
printenv ROS_DISTRO
gazebo --version
git rev-parse HEAD
git status --short
```

로그를 남겨 다시 실행할 때는 터미널 1의 기존 실행을 종료한 뒤 다음처럼 시작한다.

```bash
set -o pipefail
ros2 launch gazebo_tutorial_bringup diffbot.launch.py verbose:=true \
  2>&1 | tee /tmp/diffbot-debug.log
```

문제를 재현한 뒤 `Ctrl+C`로 종료한다. `/tmp/diffbot-debug.log`에는 표준 출력과 오류가
함께 저장된다. 증상이 나타난 마지막 한 줄뿐 아니라 앞선 플러그인·Xacro 오류도 확인한다.
