# 117. Franka 관절 상태 발행과 ROS 명령 수신

권장 학습 순서 **117** · ROS 2 연결과 기본 통신 · 출처 ID `t018`

예상 결과는 `/joint_states`에 실제 Franka 관절 위치가 나타나고, 이 폴더의 `send_command.py`가 첫 번째 관절을 0.3rad로 움직이는 것이다. 공식 GUI/Script Editor 실습을 독립 실행 진입점으로 옮겼고, 외부 isaac_tutorials 패키지 대신 이 폴더에 최소 ROS 노드를 포함했다.

## 이 실습의 의도

Franka의 실제 관절 상태를 ROS로 읽는 방향과 외부 목표 위치를 물리 articulation에 적용하는 방향을 함께 확인한다. 한 관절에 하나의 position만 보내는 최소 송신기를 사용해 관절 이름과 명령 배열의 대응을 쉽게 관찰한다. `run.py`만 실행하면 상태 발행·명령 수신이 준비되며, 0.3 rad 목표나 원위치 복귀는 별도 `send_command.py` 실행으로 요청한다.

## 실행 후 확인할 것

- 콘솔 `actual_joint_names`와 `/joint_states`의 `sensor_msgs/msg/JointState.name` 배열에서 `panda_joint1`을 찾는다. 실제 위치는 같은 인덱스의 position이며 배열의 첫 항목이라고 추측하지 않는다.
- 외부 `ros2 topic echo /joint_states`에서 position·velocity·effort와 진행하는 stamp를 확인한다. 이 값은 명령 송신 내용을 그대로 되돌린 것이 아니라 `/panda`의 상태를 발행한 것이다.
- `send_command.py --joint panda_joint1 --position 0.3 --seconds 10` 실행 중 `/joint_command`가 `sensor_msgs/msg/JointState`로 수신되고 해당 관절 position이 0.3 rad 쪽으로 접근하는지 본다. 콘솔 위치와 viewport의 관절 회전을 함께 확인해야 명령 적용까지 확인한 것이다.
- `send_command.py --position 0.0 --seconds 5`를 실행하면 같은 관절이 0 rad 쪽으로 복귀해야 한다. 송신기 종료 자체는 복귀 명령이 아니며, 목표에 즉시 수치상 완전히 일치할 필요는 없다.
- `/JointGraph`에서 Subscribe의 이름·position 출력이 Actuator로 연결되고 상태 publisher는 playback tick마다 실행되는지 확인한다. 콘솔은 120스텝 간격, 외부 송신기는 약 0.1초 대기 루프이므로 서로 다른 빈도를 구별한다.
- 기본 그래프에는 `/clock`과 TF 발행기가 없다. 이 송신기는 wall-clock으로 동작하며, 짧은 `--headless --steps 120` 실행만으로 외부 DDS 발견·수신·관절 이동까지 확인했다고 판단하지 않는다.

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

## 준비 및 실행

Isaac 5.1 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`에 접근해야 한다. 외부 터미널에는 ROS의 `rclpy`, `sensor_msgs`가 있어야 한다. Python으로 ROS 패키지를 임의 설치하지 말고 선택한 ROS 배포판을 source한다.

1. 터미널 A: `"$ISAAC_SIM/python.sh" run.py`
2. 터미널 B: `ros2 topic echo /joint_states --once`로 관절 목록, position, velocity, effort 배열을 확인한다.
3. 터미널 B: `python3 send_command.py --joint panda_joint1 --position 0.3 --seconds 10`
4. 다른 ROS 터미널에서 `ros2 topic echo /joint_states`를 실행한다. name 배열에서 `panda_joint1`을 찾고 같은 인덱스의 position이 목표로 접근하는지와 viewport의 회전을 함께 확인한다. 인덱스를 확인한 뒤에는 `ros2 topic echo /joint_states --field position`으로 위치 배열만 관찰할 수도 있다.
5. `python3 send_command.py --position 0.0 --seconds 5`로 복귀한다. GUI 창을 직접 닫으면 시뮬레이션이 종료된다. `--steps N`을 명시한 경우에는 N스텝에 도달해도 종료된다. `--headless --steps 120`은 짧은 환경 점검에 사용할 수 있지만 DDS 명령 수신 테스트는 충분한 실행 시간이 필요하다.

## GUI 실습과 Script Editor에서 같은 구조 만들기

1. **File > New** 후 Content Browser의 위 Franka asset을 열어 `/panda`를 찾는다. 장면 경로가 다르면 아래 대상 경로도 함께 바꾼다.
2. **Window > Graph Editors > Action Graph**에서 새 그래프를 만든다. Tick, ROS2 Context, Read Simulation Time, ROS2 Publish Joint State, ROS2 Subscribe Joint State, Articulation Controller를 놓는다.
3. Tick.tick을 Publish/Subscribe/Controller의 execIn에 각각 연결한다. Context.context는 Publish와 Subscribe의 context에 연결한다.
4. Time.simulationTime을 Publish.timeStamp에 연결한다. Publish의 targetPrim은 `/panda`, topicName은 `/joint_states`다.
5. Subscribe의 topicName은 `/joint_command`다. jointNames/positionCommand/velocityCommand/effortCommand 출력을 같은 이름의 Controller 입력으로 연결한다. Controller.robotPath는 `/panda`다.
6. Play 전에 장면을 새 파일로 저장하고 위 발행 명령으로 시험한다. **Tools > Robotics > ROS 2 OmniGraphs > JointStates**를 사용하면 Graph Path, articulation prim, Publisher/Subscriber, Articulation Controller 선택으로 자동 생성할 수 있다.
7. Script Editor 방식은 `run.py`의 `nodes`, `links`, `values`와 `og.Controller.edit` 부분을 이미 열린 Franka Stage에서 실행하는 것이다. `SimulationApp`이나 `World.step` 루프를 GUI Script Editor 안에서 새로 만들지 않는다. `import omni.graph.core as og; keys=og.Controller.Keys`도 함께 실행하고, 이미 있는 `/JointGraph` 이름은 새 이름으로 바꾼다.

## API와 제어 모드 해설

`og.Controller.edit`의 CREATE_NODES는 연산 종류, CONNECT는 실행·데이터 연결, SET_VALUES는 토픽과 대상 경로를 작성한다. USD의 reference는 Franka asset을 현재 장면에 불러오며, Articulation Root는 각 관절이 속하는 물리 계통을 지정한다. 고정 베이스 로봇에서는 world에 고정된 root joint 쪽 API가 사용될 수 있으므로 `/panda` 아래 실제 API를 Property에서 확인한다.

`JointState.name`은 prim 경로가 아니라 joint 이름 배열이다. position은 rad, velocity는 rad/s, effort는 회전관절의 경우 N·m이다. `send_command.py`는 하나의 이름과 하나의 position만 넣고 다른 배열은 비워 불필요한 제어 모드를 지정하지 않는다. `node.create_publisher`와 `pub.publish`는 시뮬레이션 API가 아닌 실제 ROS 송신 API다.

한 관절에 position·velocity·effort 목표를 서로 충돌하게 주지 않는다. 위치 drive는 충분한 stiffness와 damping, 속도 drive는 stiffness=0과 damping>0을 쓴다. 여러 관절을 서로 다른 모드로 제어하려면 위치 관절과 속도 관절의 메시지를 나누거나, 하나의 메시지에서 사용하지 않는 모드 항목을 `float('nan')`으로 채운다. 예를 들어 `name=['arm_joint','wheel_joint']`, `position=[0.2,nan]`, `velocity=[nan,2.0]`이다. 이 예의 이름은 설명용이며 Franka에 wheel_joint가 있다고 가정하지 않는다.

## 한 가지 바꾸기와 문제 해결

`--position 0.1`만 바꾸어 작은 목표에서 응답을 비교한다. 관절 이름이 틀리면 ROS 메시지를 받아도 적용할 대상이 없다. `actual_joint_names`와 `/joint_states.name`을 비교한다. 토픽은 보이지만 로봇이 움직이지 않으면 Controller target, Play, drive gain을 확인한다. `use_sim_time=True`인 외부 노드를 추가한다면 `/clock` 발행 그래프도 같은 Stage에 추가해야 한다. 이 명령 송신기는 기본 wall-clock 반복으로 해당 의존성을 만들지 않는다.

## 출처와 검증 범위

- [공식 5.1 UI 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html#add-joint-states-in-ui)
- [공식 5.1 Python 구성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html#add-joint-states-in-extension)
- [공식 5.1 제어 모드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html#position-and-velocity-control-modes)
- [공식 5.1 메뉴 shortcut](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_manipulation.html#graph-shortcut)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 위의 확인 항목을 실제 환경에서 관찰해야 완료한 것이다.
