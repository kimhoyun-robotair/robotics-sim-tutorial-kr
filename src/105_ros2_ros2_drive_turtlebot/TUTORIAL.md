# 105. TurtleBot: Twist에서 바퀴 속도까지

권장 학습 순서 **105** · ROS 2 연결과 기본 통신 · 출처 ID `t008`

예상 결과는 외부 `/cmd_vel` 메시지에 따라 TurtleBot이 바닥 위에서 이동하고, 0 명령을 보내면 정지하는 것이다. `run.py`는 공식 TurtleBot3 asset과 같은 제어 노드로 평평한 테스트 장면을 만든다. 공식 Simple Room 환경 대신 평면을 사용하여 제어 연결을 보기 쉽게 한 변형이다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 물리와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 명시하면 해당 스텝 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 3600스텝으로 종료하며, `--steps 0`과 음수는 허용하지 않습니다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. Standalone `run.py`는 이 확장을 직접 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## 실행

이 실습에는 Isaac 5.1 asset root의 `Isaac/Robots/Turtlebot/Turtlebot3/turtlebot3_burger.usd`가 필요하다. 인터넷 또는 설치한 로컬 asset pack에서 접근할 수 있어야 한다. 직접 가져온 로봇은 `--robot-usd /absolute/path/turtlebot.usd`로 넣을 수 있다. 이 경우 이름이 `wheel_left_joint`, `wheel_right_joint`인 두 바퀴를 가지고 있어야 한다.

1. 터미널 A에서 `"$ISAAC_SIM/python.sh" run.py`을 실행한다. 바닥과 로봇을 보고 콘솔의 실제 joint names를 확인한다.
2. 터미널 B에서 `ros2 topic info /cmd_vel -v`로 Isaac의 subscriber를 확인한다.
3. 전진 명령을 반복 발행한다.

   ```bash
   ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}"
   ```

4. Ctrl+C로 위 발행을 끝내도 마지막 속도가 유지된다. 다음 명령으로 정지시킨다.

   ```bash
   ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
   ```

5. 제자리 회전을 보려면 `linear.x=0.0`, `angular.z=0.5`로 바꾼다. 콘솔의 `wheel_commands_rad_s`가 좌우 반대 부호이고 `position_m`은 대체로 유지되는지 확인한다. 실물 제어용 watchdog은 이 교육 그래프에 없으며 마지막 명령 유지가 공식 실습의 동작이다.

## GUI로 노드 연결을 직접 보기

`run.py` 실행 창에서 **Window > Graph Editors > Action Graph**를 열고 `/DriveGraph`를 선택한다. 직접 구성하려면 새 Stage에 위 TurtleBot USD와 **Create > Physics > Ground Plane**, Physics Scene, 조명을 추가하고 아래 표대로 연결한다.

| 출발 출력 | 도착 입력 | 이유 |
|---|---|---|
| Tick.tick | Twist.execIn, Differential.execIn, Actuator.execIn | 새 메시지가 없어도 마지막 명령으로 매 프레임 제어 |
| Context.context | Twist.context | 같은 DDS 도메인 사용 |
| Twist.linearVelocity | BreakVector3(tuple) → x → Differential.linearVelocity | 전진 속도 m/s 추출 |
| Twist.angularVelocity | BreakVector3(tuple) → z → Differential.angularVelocity | 회전 속도 rad/s 추출 |
| Differential.velocityCommand | Actuator.velocityCommand | 두 바퀴의 각속도를 joint drive에 전달 |

Differential의 wheelRadius=0.025m, wheelDistance=0.16m, maxLinearSpeed=0.22m/s, maxAngularSpeed=1rad/s다. Actuator는 `robotPath=/World/turtlebot3_burger`, `jointNames=[wheel_left_joint, wheel_right_joint]`이다. GUI에서 이름 배열은 **Constant Token** 두 개와 **Make Array**로 만들 수 있다. Constant String은 token 배열 대신 쓸 수 없다.

Articulation Root는 로봇의 링크·관절을 하나의 물리 계통으로 묶는 API다. 이 코드는 공식 절차처럼 `/World/turtlebot3_burger`에 하나만 둔다. 직접 가져온 asset에 `/base_footprint` Root가 있다면 그곳의 **Physics > Articulation Root**를 제거하고 부모 로봇에 추가한다. 원본 asset을 고치는 대신 현재 Stage의 reference 위에 수정값을 기록한다.

## 계산과 API 해설

왼쪽 바퀴는 `(v - ω·L/2)/r`, 오른쪽은 `(v + ω·L/2)/r`이다. 예를 들어 v=0.2, ω=0이면 두 바퀴 모두 약 8rad/s다. 메시지의 x·z를 잘못 연결하면 이 대칭이 깨진다. `DifferentialController`는 이 변환과 속도 제한을 처리하고 `IsaacArticulationController`는 실제 joint drive에 명령한다. `SingleArticulation.get_world_pose()`는 물리 시뮬레이션 결과를 읽는다.

이 Stage의 단위는 1m이므로 입력에 추가 단위 변환이 없다. cm 단위 Stage를 사용한다면 공식 **Scale To/From Stage Unit** 노드를 linear 쪽에 추가한다. 각속도는 rad/s이며 GUI USD 각도 표시는 degree일 수 있다.

## 하나만 바꾸기·문제 해결

`angular.z`만 0에서 0.5로 바꾸어 바퀴 속도 차이를 확인한다. 로봇이 움직이지 않으면 Play, 실제 관절 이름, Articulation Root, 바퀴 접지와 마찰을 순서대로 본다. 속도 drive는 stiffness=0, damping>0이어야 한다. 테이블 위보다 바닥에서 실험한다. 키보드 패키지가 준비되어 있으면 `ros2 run teleop_twist_keyboard teleop_twist_keyboard`로 같은 `/cmd_vel`을 조작할 수 있다. asset을 못 읽는 오류는 로컬 USD 경로로 해결하고, 에셋 접근 실패를 DDS 문제로 혼동하지 않는다.

## 출처와 검증 범위

- [공식 5.1 제어 개념](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html#driving-the-robot)
- [공식 5.1 그래프](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html#building-the-graph)
- [공식 5.1 노드 해설](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html#graph-explained)
- [공식 5.1 ROS 확인](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_drive_turtlebot.html#verifying-ros-connections)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
