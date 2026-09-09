# 프로젝트 2: 이동 로봇을 가져와 ROS 2로 움직인다

TurtleBot3 Burger를 기준으로 URDF 가져오기, 바퀴 제어, TF와 센서 연결을 순서대로 확인한다. 기준 로봇이 정상적으로 움직인 다음 센서 장착 위치나 외형을 바꾸어 자신의 로봇으로 확장한다. 차체 크기, 질량, 바퀴 치수와 제어기를 동시에 바꾸지 않는다.

## 준비할 것

[Bridge 설치](../04-ros2/01-install-bridge-workspace.md), [시간·TF](../04-ros2/02-time-tf-and-motion.md), [바퀴 제어](../04-ros2/10-control-cookbook.md)를 완료한다. 아래 명령은 이 저장소 루트의 **외부 Jazzy 터미널**에서 실행한다.

```bash
mkdir -p project-2/robot project-2/build project-2/stages project-2/results
source /opt/ros/jazzy/setup.bash
sudo apt install ros-jazzy-xacro liburdfdom-tools
```

## 1단계: 실제 URDF를 준비한다

공식 5.1 튜토리얼은 ROBOTIS의 Jazzy용 TurtleBot3 설명 파일을 사용한다. 아래 커밋은 이번 문서에서 확인한 입력 버전이다. 자산은 별도 프로젝트 폴더에 받고 원본을 직접 편집하지 않는다.

```bash
git clone --branch jazzy --single-branch \
  https://github.com/ROBOTIS-GIT/turtlebot3.git project-2/source_robot
git -C project-2/source_robot checkout --detach \
  0c0be84e3f5c3194fb2adea8426a58a96060eab5
ros2 run xacro xacro \
  project-2/source_robot/turtlebot3_description/urdf/turtlebot3_burger.urdf \
  namespace:='' > project-2/build/turtlebot3_burger.urdf
check_urdf project-2/build/turtlebot3_burger.urdf
```

파일 확장자가 `.urdf`여도 안에 Xacro 태그가 있으면 먼저 전개해야 한다. 이 입력은 [ROBOTIS의 고정 버전 파일](https://github.com/ROBOTIS-GIT/turtlebot3/blob/0c0be84e3f5c3194fb2adea8426a58a96060eab5/turtlebot3_description/urdf/turtlebot3_burger.urdf)에서 확인할 수 있다.

Isaac Sim 터미널에 시스템 ROS를 source하지 않아도 mesh를 찾도록, 이 실습용 출력의 `package://` 경로를 실제 파일 경로로 바꾼다.

```bash
python3 - <<'PY'
from pathlib import Path

urdf = Path('project-2/build/turtlebot3_burger.urdf')
package = Path('project-2/source_robot/turtlebot3_description').resolve()
text = urdf.read_text().replace('package://turtlebot3_description/', str(package) + '/')
urdf.write_text(text)
print(urdf.resolve())
PY
```

이 출력 URDF에는 현재 컴퓨터의 절대 경로가 들어간다. 다른 컴퓨터에서 실행할 때는 위 전개 명령부터 다시 실행한다. USD 변환이 끝났다고 mesh 파일을 지우지 않는다.

## 2단계: 이동 가능한 로봇으로 가져온다

1. Isaac Sim에서 새 Stage를 연다.
2. Ground Plane과 Physics Scene, 조명을 추가한다. [첫 물리 장면](../02-getting-started/05-first-scene-and-physics.md)을 그대로 사용해도 된다.
3. `File > Import`에서 방금 만든 URDF를 고른다.
4. `Referenced Model`을 선택하고, Links에서 `Moveable Base`를 선택한다.
5. `wheel_left_joint`, `wheel_right_joint`를 `Velocity`로 설정한다.
6. 출력 USD를 `project-2/robot`에 저장하고 가져온다.
7. 바퀴가 바닥 안에 파묻히지 않게 로봇을 조금 위에 배치한다.
8. Play한 뒤 로봇이 바닥에 내려앉고 안정되는지 먼저 관찰한다. 아직 ROS 명령은 보내지 않는다.

입력 옵션과 바퀴 관절 이름은 [NVIDIA 5.1.0 TurtleBot 가져오기 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html)을 따른다. 관절 속도 제어에서는 stiffness를 0으로 두고, damping·최대 힘은 실제 로봇 크기와 물리 시간 간격에 맞춰 확인한다. 큰 gain을 그대로 복사해 진동을 억지로 가리지 않는다.

**완료 판정:** 10초 동안 명령 없이 차체가 기울어지거나 링크가 분리되지 않는다. 바퀴와 바닥의 충돌 형상이 맞고, Stage 저장 후 다시 열어도 같은 상태이다.

## 3단계: 바퀴 명령을 연결한다

[제어 실습](../04-ros2/10-control-cookbook.md)의 TurtleBot 그래프를 만든다. 화면에서 직접 노드를 연결하거나 공식 그래프 생성 메뉴를 사용한 뒤 다음 값은 반드시 확인한다.

| 항목 | 이 실습의 설정 |
|---|---|
| 명령 입력 | `/cmd_vel_safe`, `geometry_msgs/msg/Twist` |
| 바퀴 이름 순서 | `wheel_left_joint`, `wheel_right_joint` |
| 바퀴 반지름·간격 | 가져온 URDF의 collision 크기와 관절 중심에서 확인 |
| 제어 대상 | 실제 articulation root prim |
| 시간 | simulation time, 전역 `/clock` 하나 |
| Domain ID | Isaac Sim과 외부 ROS 모두 0 |

차동 구동에서 바퀴 속도는 `ωL=(v-ωL_sep/2)/r`, `ωR=(v+ωL_sep/2)/r`로 구한다. 여기서 차체 회전 속도는 `ω`, 바퀴 간격은 `L_sep`, 바퀴 반지름은 `r`이다. 좌우 관절 이름이 뒤바뀌면 직진은 돼도 회전 방향이 거꾸로 나타날 수 있다.

Stage를 저장한 뒤 Play한다. 별도 Jazzy 터미널에서 [속도 중계 노드](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/ros2/safe_cmd_vel.py)를 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
python3 examples/ros2/safe_cmd_vel.py
```

다른 Jazzy 터미널에서 짧게 전진 명령을 보낸다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
timeout 2 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.10}, angular: {z: 0.0}}'
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'
```

`timeout`의 종료 코드 124는 지정한 2초가 끝났다는 뜻이다. 중계 노드는 입력이 끊기면 0 명령을 반복하지만, 중계 프로세스 자체가 종료되는 경우까지 보호하지는 않는다. 시뮬레이터의 수신 타임아웃과 실제 바퀴 정지 시험을 최종 단계에 포함한다.

## 4단계: odometry와 TF를 연결한다

[TF·odometry 실습](../04-ros2/02-time-tf-and-motion.md)을 따라 구동 확인과 별개로 그래프를 만든다.

| 발행 값 | 담당 |
|---|---|
| `/odom` | `Isaac Compute Odometry`의 결과를 `ROS 2 Publish Odometry`로 전달 |
| `odom → base_link` | 동일한 odometry 결과를 Raw Transform publisher로 전달 |
| 로봇 내부 TF | Isaac Transform Tree 또는 `robot_state_publisher` 중 하나 |
| `/joint_states` | 관절 이름과 상태를 Joint State publisher로 전달 |

이 단계에는 AMCL이 없으므로 `map` 프레임도 필요 없다. RViz2의 Fixed Frame은 `odom`으로 둔다. `map → odom`을 근거 없이 static TF로 추가해 오류를 숨기지 않는다.

```bash
ros2 topic echo /odom --once
ros2 topic echo /joint_states --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_tools view_frames
```

URDF의 `base_footprint`를 odometry 자식 프레임으로 사용하는 구성이라면 관련 설정을 모두 그 이름으로 맞춘다. 같은 변환을 Isaac Sim과 외부 노드가 동시에 발행하지 않게 한다.

**완료 판정:** 직진하면 odometry의 전방 위치가 늘어나고 회전하면 yaw가 바뀐다. 바퀴가 멈춘 상태에서 RViz 로봇이 다른 위치로 반복해서 튀지 않는다.

## 5단계: 센서 하나를 추가한다

처음에는 IMU 또는 RGB 카메라 하나를 선택한다. [센서 토픽 실습](../04-ros2/11-sensor-topic-cookbook.md)을 따라 차체 아래에 센서 prim을 배치하고 **로컬 위치**를 설정한다. 센서 장착용 Xform에 불필요한 Rigid Body를 붙이지 않는다.

카메라를 선택했다면 다음을 확인한다.

```bash
ros2 topic info /camera/color/image_raw -v
ros2 topic echo /camera/color/camera_info --once
ros2 run tf2_ros tf2_echo base_link camera_color_optical_frame
```

카메라를 검증한 뒤 LiDAR를 추가한다. 센서 수가 늘어날 때마다 렌더링 부하와 메시지 주기를 다시 측정한다. `/clock`과 데이터 타임스탬프도 함께 확인한다.

## 6단계: 변경 전후를 비교한다

| 조건 | 기록할 값 |
|---|---|
| 명령 없음, 10초 | 차체 기울기, 바닥 통과, 관절 진동 |
| 0.1 m/s 직진, 2초 | 실제 이동 거리와 odometry의 차이 |
| 작은 제자리 회전 | 좌우 바퀴 부호와 yaw 증가 방향 |
| 명령 중단 | 0 명령 도착 시각과 실제 정지 시각 |
| 저장·다시 열기 | prim 경로, 그래프 입력, TF 복구 여부 |

위 조건을 통과한 뒤 상부 외형 또는 센서 위치 하나만 바꾸고 동일한 시험을 반복한다. 새 차체를 Xacro로 만드는 확장은 [커스텀 로봇 장](../05-customization/01-custom-robot.md)을 따른다. 질량·관성·collision을 변경한 버전은 별도 USD로 저장해 기준 버전과 비교한다.

두 로봇으로 확장할 때는 토픽뿐 아니라 TF 이름도 분리한다. 한 대가 성공하기 전에 네임스페이스를 추가하지 않는다. 최종 산출물은 변환 입력 URDF, USD, Action Graph가 포함된 Stage, 실행 명령과 측정 결과이다.

## 출처

- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [URDF Import: TurtleBot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html)
- [Driving TurtleBot using ROS 2 Messages](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html)
- [Automatic ROS 2 Namespace Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_auto_namespace.html)
