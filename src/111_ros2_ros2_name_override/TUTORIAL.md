# 111. NameOverride: USD 이름을 유지하며 ROS 이름 바꾸기

권장 학습 순서 **111** · ROS 2 연결과 기본 통신 · 출처 ID `t019`

예상 결과는 실제 USD의 `panda_joint1` 경로가 유지되고 ROS `/joint_states`에는 `shoulder_pan`이 보이는 것이다. 외부에서 별칭으로 보낸 명령은 Joint Name Resolver를 거쳐 같은 실제 관절을 움직인다. Franka 모델과 ROS 그래프를 이 폴더에서 모두 구성한다.

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

필요한 asset은 Isaac 5.1의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`다. 외부 ROS Python에는 `rclpy`, `sensor_msgs`가 있어야 한다.

1. 터미널 A: `"$ISAAC_SIM/python.sh" run.py`
2. 터미널 B: `ros2 topic echo /joint_states --once`를 실행한다. name 배열에서 첫 관절의 ROS 이름 `shoulder_pan`을 찾는다.
3. 터미널 B: `python3 send_command.py --joint shoulder_pan --position 0.3 --seconds 10`을 실행한다. 첫 관절이 움직이는지 확인한다.
4. `ros2 topic echo /tf --once`에서 `robot_base` frame을 찾는다. 코드는 `/panda/panda_link0`에도 NameOverride를 부여해 TF 이름 변경을 보여 준다.
5. Stage Tree에서 원래 `panda_joint1`, `panda_link0` prim 이름이 그대로인지 확인한다. A 콘솔은 실제 USD joint 경로와 실제 물리 관절 배열을 출력한다.

## GUI로 직접 적용하기

1. 새 Stage에서 위 Franka asset을 연다. `/panda` 대상의 ROS2 Publish Joint State(`/joint_states`), Subscribe Joint State(`/joint_command`), Articulation Controller 그래프를 만든다. Tick은 세 노드 execIn에, Read Simulation Time은 publisher.timeStamp에, Context는 두 ROS 노드 context에 연결한다. Subscriber의 네 출력 이름 배열/position/velocity/effort는 controller의 대응 입력으로 연결한다.
2. Stage Tree의 `panda_joint1` joint prim을 선택한다. Property의 **Add > Isaac > NameOverride**를 누른 뒤 **Name Override**에 `shoulder_pan`을 쓴다. 이미 속성이 있으면 값만 바꾼다.
3. **Isaac Joint Name Resolver** 노드를 추가한다. robotPath=`/panda`로 지정한다. Subscriber.jointNames를 Resolver.jointNames로, Resolver.jointNames를 Controller.jointNames로 연결한다.
4. Tick을 Resolver.execIn에 연결하고 Resolver.execOut을 Controller.execIn에 연결한다. positionCommand/velocityCommand/effortCommand는 Subscriber에서 Controller로 직접 이어 둔다.
5. TF에는 **ROS2 Publish Transform Tree**를 추가하고 targetPrims=`/panda`, topicName=`/tf`를 지정한다. Tick, Context, 시간 입력을 연결한다. `panda_link0` prim의 Name Override를 `robot_base`로 설정한다.
6. 새 이름으로 Save 후 Play한다. 위 ROS 명령으로 이름과 실제 움직임을 확인한다. 실행 중 이름을 변경했다면 Stop/Play로 publisher/resolver를 다시 초기화한다.

## USD/API/ROS 이름의 차이

USD prim 경로는 장면 계층의 주소다. 실제 prim rename을 하면 reference, joint 관계와 그래프 target까지 영향을 받을 수 있다. `prim.CreateAttribute('isaac:nameOverride', Sdf.ValueTypeNames.String).Set(...)`는 주소를 바꾸지 않고 문자열 속성만 추가한다. ROS Joint State/TF publisher가 이 속성을 읽어 외부 이름을 정한다.

외부 이름을 Articulation Controller가 자동으로 실제 이름으로 이해하는 것은 아니다. `IsaacJointNameResolver`는 지정한 articulation 내부에서 alias를 찾고 **실제 joint 이름 배열**을 출력한다. 따라서 상태 발행만 바꾸고 resolver 연결을 빼면, 별칭 명령이 실제 관절에 도달하지 않는 원인을 실험할 수 있다. 이 코드의 resolver execOut 연결은 변환된 이름 준비 후 controller를 실행하기 위한 것이다.

## 한 가지 바꾸기와 문제 해결

`shoulder_pan` 별칭 하나만 `base_rotation`으로 바꾸고 송신기의 `--joint`도 같은 값으로 맞춘다. 두 관절에 같은 별칭을 쓰지 않는다. name 배열은 바뀌었지만 명령이 안 먹으면 Resolver의 robotPath와 jointNames 연결을 확인한다. TF 이름은 대소문자를 구별하므로 RViz Fixed Frame도 출력된 실제 이름으로 맞춘다. `panda_link0`이 없다는 오류는 다른 Franka asset을 사용한 경우이므로 코드가 기대하는 5.1 asset과 Stage 구조를 확인한다.

## 출처와 검증 범위

- [공식 5.1 속성 목적](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_name_override.html#setting-up-the-nameoverride-attribute)
- [공식 5.1 GUI 적용](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_name_override.html#adding-the-isaac-nameoverride-prim-attribute)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
