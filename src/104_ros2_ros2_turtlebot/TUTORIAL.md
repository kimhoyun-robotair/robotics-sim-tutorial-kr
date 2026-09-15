# 104. TurtleBot URDF를 USD로 가져오고 바퀴 drive 조정하기

권장 학습 순서 **104** · ROS 2 연결과 기본 통신 · 출처 ID `t007`

예상 결과는 ROS TurtleBot3 description에서 생성한 URDF가 USD reference로 열리고, 두 바퀴에 velocity drive가 있으며, Play 시 로봇이 바닥에 내려앉는 것이다. 원문의 URDF Importer GUI를 사용하는 완전한 실습이다. `preprocess_urdf.py`는 xacro 전처리, `inspect_robot.py`는 실제 USD drive 점검을 돕는다.

## 이 실습의 의도

ROS 로봇 description을 시뮬레이터가 사용할 USD articulation으로 가져오고, 움직일 수 있는 base와 두 바퀴 velocity drive를 확인한다. 전처리와 실제 stage 검사를 분리해 URDF 파일 생성 성공, 가져오기 성공, 물리 접지 성공을 각각 판단하도록 구성했다. 로컬 파일은 이 두 보조 스크립트뿐이며 USD 가져오기와 drive 편집은 GUI에서 수행한다. ROS 메시지 발행·구독 그래프나 자율주행은 아직 만들지 않는다.

## 실행 후 확인할 것

- **전처리 결과:** `preprocess_urdf.py` 실행 후 지정한 URDF가 생기고 `expanded robot= ... joints= ...`에 `wheel_left_joint`, `wheel_right_joint`가 포함되는지 확인한다. 출력 파일이 이미 있으면 중단하는 것이 의도된 동작이며, 이 단계는 USD나 로봇 운동을 생성하지 않는다.
- **USD reference와 base:** Import 후 Stage에 TurtleBot mesh가 보이고 References의 Asset Path가 새 `output/import_01` 아래 생성물로 연결되는지 본다. Moveable Base로 가져와 몸체가 world에 고정되지 않았는지 확인한다.
- **drive 수치:** Script Editor에서 `inspect_robot.py`를 실행해 두 wheel 경로에 angular drive가 있고, 설정 후 `stiffness=0.0`, `damping=10000000.0`, 시험 전 `target_velocity=0`인지 출력과 Property를 대조한다. `articulation_roots` 목록도 비어 있지 않은지 직접 확인한다.
- **접지와 정지:** 로봇을 바닥 바로 위에 놓고 Play하면 중력으로 내려와 지지되는지 본다. 속도 목표를 주지 않은 상태에서 스스로 전진하지 않는 것은 정상이다.
- **바퀴 시험:** 아래 선택적 시험에서 한 바퀴에 작은 Target Velocity를 주면 해당 바퀴가 구동되는지 관찰하고, 시험 뒤 0으로 복구한다. 바퀴 회전, 몸체가 움직일 수 있는지, 미끄러짐은 함께 확인하되 ROS topic 수신을 이 실습의 완료 조건으로 두지 않는다.
- **검사 범위:** `inspect_robot.py`는 stage 전체에서 이름이 맞는 wheel을 찾고 angular drive와 개수를 검사한다. 값과 articulation root의 적절성은 출력만 하므로 스크립트가 오류 없이 끝났다는 사실만으로 모든 물리 설정이 맞다고 판단하지 않는다.

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

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 이후 DDS 통신에 사용할 그룹 번호다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. 이 폴더에는 standalone `run.py`가 없으며, `preprocess_urdf.py`는 ROS 설정을 source한 시스템 `python3`에서, `inspect_robot.py`는 열린 Isaac Sim의 Script Editor에서 실행한다. 이 가져오기 단계에서는 외부 ROS 노드와 DDS 통신을 시험하지 않는다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. 이 실습은 가져온 link, joint, articulation root와 drive를 확인하는 단계이며 Action Graph나 메시지 발행 노드를 생성하지 않는다.

## 로봇 파일 준비

TurtleBot3 description과 선택한 ROS 배포판의 `xacro`가 필요하다. 설치 여부는 `command -v xacro`로 확인한다. ROS 설치 환경에서 배포판의 `ros-$ROS_DISTRO-xacro` 패키지를 준비할 수 있다. 이 폴더에 source 로봇이 없다면 다음 명령은 사용자가 upstream 로봇 설명을 가져오는 단계다.

```bash
git clone --branch "$ROS_DISTRO" https://github.com/ROBOTIS-GIT/turtlebot3.git turtlebot3
colcon --log-base output/ros_logs build --base-paths turtlebot3/turtlebot3_description --build-base output/ros_build --install-base output/ros_install
source output/ros_install/setup.bash
python3 preprocess_urdf.py turtlebot3/turtlebot3_description/urdf/turtlebot3_burger.urdf --output turtlebot3/turtlebot3_description/urdf/tb3_burger_processed.urdf
```

이미 파일을 가지고 있으면 clone을 생략한다. `colcon`과 description package의 ROS 의존성이 준비되어 있어야 한다. 이미 설치된 description을 사용한다면 build도 생략하고 해당 workspace를 source한다. 전처리 결과를 원본 URDF 폴더에 두면 `../meshes`처럼 상대 경로인 자원을 유지하기 쉽다. package URI를 사용하는 mesh는 ROS package 경로에서 해석하므로 description package와 workspace를 source해야 한다. 위 명령이 경로를 찾지 못하면 `ros2 pkg prefix turtlebot3_description`과 해당 URDF의 mesh filename을 함께 확인한다. `preprocess_urdf.py`는 출력 파일이 존재하면 중단하므로 다시 실행하려면 새로운 출력 이름을 준다.

## GUI 가져오기와 검증

1. Isaac Sim을 ROS 설정을 적용한 터미널에서 열고 **File > New**를 선택한다. Content Browser에서 **Isaac Sim > Environments > Simple_Room > simple_room.usd**를 Stage로 드래그한다. environment prim의 Translate X/Y/Z를 0으로 둔다. 환경을 사용하지 않으면 **Create > Physics > Ground Plane**, **Physics Scene**, **Create > Light > Distant Light**를 직접 만든다.
2. **File > Import**에서 `tb3_burger_processed.urdf`를 선택한다. **Referenced Model**, Links의 **Moveable Base**를 고른다. 고정 베이스로 가져오면 바퀴가 돌아도 몸체가 world에 붙어 움직이지 않는다.
3. **Joints & Drives**에서 `wheel_left_joint`, `wheel_right_joint`의 Target을 **Velocity**로 설정한다. **USD Output**에는 이 폴더 아래 새 디렉터리 `output/import_01`을 지정한다. Import를 누르면 URDF와 같은 이름의 하위 폴더에 USD가 작성된다.
4. 로봇을 선택해 Gizmo로 테이블 밖, 바닥 바로 위에 놓는다. X/Y는 테이블과 겹치지 않게, Z는 바닥보다 수 cm 높게 둔다. Play하여 중력에 의해 내려와 바닥에서 지지되는지 확인한다.
5. Stop 후 Stage Tree에서 두 wheel joint를 찾는다. Property의 Angular Drive에서 **Stiffness=0.0**, **Damping=10000000.0**을 설정한다. 이 값은 공식 실습의 시작값이며 모든 로봇에 적절한 보편값이 아니다.
6. **Window > Script Editor**에서 이 폴더의 `inspect_robot.py` 내용을 붙여 실행한다. 두 wheel 경로, stiffness, damping, target_velocity와 articulation root가 실제로 출력되어야 한다. 두 바퀴가 없으면 스크립트가 오류를 내어 다른 asset을 검사한 사실을 알린다.
7. ROS 없이 drive만 시험하려면 한 바퀴의 Target Velocity를 작은 양수(예: GUI의 30degree/s)로 설정하고 Play한다. Stop 후 0으로 복구한다. 이 단계는 URDF 물리 구성이 맞는지 확인하며 ROS 연결 확인은 아니다.

## 가져온 물리 속성을 이해하기

URDF의 link는 USD rigid body, joint는 몸체 사이 제약으로 표현된다. Importer는 질량·관성·재질을 가능한 범위에서 변환하지만 누락한 물리 값을 자동 추정할 수 있다. **Physics > Rigid Body**가 있는 link를 선택하고 **Add > Physics > Mass**로 질량/관성을 명시할 수 있다. 시각 mesh 크기가 같아도 질량 중심이나 관성이 다르면 회전 응답이 달라진다.

Velocity drive에서 stiffness를 0으로 두는 이유는 위치 목표로 끌어당기는 항을 없애기 위해서다. damping은 속도 오차에 비례한 힘을 만든다. 바퀴가 미끄러지면 wheel collider와 바닥에 Physics Material을 적용하고 Static/Dynamic Friction을 조정한다. 마찰 문제를 큰 모터 gain만으로 해결하지 않는다.

USD reference는 외부 USD를 현재 Stage에 합성하는 연결이다. Stage Tree의 reference 표시와 Property의 **References > Asset Path**로 실제 파일을 찾을 수 있다. 원본 파일을 편집해야 하는 경우에는 먼저 복사해 실습 출력 경로에서 수정한다. 이 패키지는 저장소의 `asset/`을 사용하지 않는다.

## 하나만 바꾸기와 문제 해결

다른 조건을 유지하고 damping만 10000000에서 1000000으로 낮춰 속도 도달 시간과 떨림을 비교한다. 모델이 바닥을 통과하면 Collision과 Physics Scene을 확인한다. import 후 mesh가 없으면 URI/package 경로와 xacro 출력 위치를 확인한다. 두 wheel drive와 움직일 수 있는 base, 접지 상태가 관찰되면 성공이다. ROS topic이 없어도 이 **가져오기 실습**은 정상이며 아직 ROS 그래프를 만들지 않았다.

## 출처와 검증 범위

- [공식 5.1 URDF 가져오기](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html#importing-turtlebot-urdf)
- [공식 5.1 물리 조정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_turtlebot.html#tune-the-robot)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 ROS 환경의 전처리부터 GPU·GUI의 가져오기와 물리 동작까지 실제 통합 실행을 아직 확인하지 않았다는 뜻이다. 앞의 확인 기준을 실제 환경에서 관찰해야 완료한 것이며 외부 ROS 통신은 이 실습 범위에 포함하지 않는다.
