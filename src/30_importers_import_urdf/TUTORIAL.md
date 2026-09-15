# 30. t111 · URDF를 USD articulation으로 가져오기

권장 학습 순서 **30** · 로봇 자산 가져오기와 제작 · 출처 ID `t111`

Isaac Sim **5.1.0**에서 URDF XML을 읽고 실제 USD 로봇으로 변환한다. 기본 `arm.urdf`는 이 패키지에 작성한 2-link/1-joint 예제로 mesh 다운로드가 필요 없다. `--franka`는 설치된 공식 Panda URDF를 가져와 RMPflow target-following까지 실행한다. 다른 로컬 패키지를 먼저 공부할 필요가 없다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.asset.importer.urdf`가 필요하다. Franka 선택 실습에는 설치 extension의 URDF/mesh 및 manipulator controller가 필요하다. 일반 Python은 도움말만 실행한다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/30_importers_import_urdf
"$ISAAC_SIM/python.sh" run.py
"$ISAAC_SIM/python.sh" run.py --franka --output output/franka
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 360회 한도를 사용한다. 실행 중에도 물리·제어가 계속 진행되며, 결과 요약은 실행을 마칠 때 기록한다.

출력 폴더는 새 경로여야 한다. `imported.usda`는 변환된 stage, `report.json`은 실제 joint 이름/위치다. 1축 예제의 목표는 0.5 rad이며 360 step 후 실제 값이 접근했는지 확인한다. 단순히 USD가 생성되었다는 사실과 안정적인 모터 추종은 구분한다.

## 작은 URDF를 읽으며 실습

1. `arm.urdf`의 `base`, `arm` link를 찾는다. 각 link의 `visual`은 표시용, `collision`은 접촉 판정용이며 같은 box 형상을 사용했다. `inertial`에는 질량과 관성 tensor가 있다.
2. `shoulder` joint의 parent/child와 `origin xyz="0 0 0.12"`, Y axis를 읽는다. 위치 단위는 m, revolute limit는 rad다. USD joint 속성 화면의 각도 표시(degree)와 혼동하지 않는다.
3. 기본 실행 후 Stage에서 import된 로봇의 링크와 articulation root를 확인한다. **Viewport eye > Show by type > Physics > Colliders > All**로 collider를 켠다.
4. 로컬 URDF를 복사하고 link의 visual box 폭만 바꾼다. `--urdf /absolute/copy.urdf --output output/visual_change`로 가져와 collider가 그대로인지 본다. collision도 바꾸어야 접촉 형상이 달라진다.

## 공식 Franka를 GUI로 가져오기

1. **Window > Extensions**에서 `isaacsim.asset.importer.urdf`를 찾고 AUTOLOAD 옆 폴더 아이콘으로 설치 위치를 연다. `data/urdf/robots/franka_description/robots/panda_arm_hand.urdf`를 찾는다.
2. **File > Import**에서 해당 URDF를 선택한다. **USD Output**은 이 패키지 `output/gui_franka/` 아래로 지정한다. extension 설치 폴더를 출력으로 쓰지 않는다.
3. **Static Base**, Default Density 비움, **Allow Self-Collision**을 선택한다. joint 설정의 natural frequency를 조금 올려 진동 변화를 시험한다. import 후 원치 않는 collider 중첩도 확인한다.
4. mobile robot은 **Moveable Base**로 바꾸고 wheel은 Velocity drive, steering은 Position drive를 선택한다. Velocity의 stiffness는 0, damping이 속도 추종을 만든다. torque 정책용 quadruped는 leg drive **None**, stiffness/damping=0으로 두고 외부 effort controller를 사용한다.
5. **Robotics Examples > Import Robots**의 Nova Carter/Franka/Kaya/UR10 각각에서 **Load Robot → Configure Drives → Play → Move to Pose**를 수행한다. **Open Source Code**에서 모델별 설정 차이를 확인한다. material 로딩이 완료된 뒤 관찰한다.

## Python import와 task 연결

`URDFParseFile`은 XML을 `_urdf.UrdfRobot`으로 파싱한다. 실행기는 parsed joint의 drive strength/damping을 설정하고 `URDFImportRobot`으로 현재 stage에 가져온다. `fix_base=True`는 베이스 고정, `distance_scale=1`은 m 입력, `density=0`은 제공된 inertia/mass를 우선하는 설정이다. 이 실습의 self-collision은 단순 실험을 위해 꺼져 있으며 GUI 공식 실습의 설정과 차이를 명시한다.

`--franka`는 `FollowTarget` task를 등록한 뒤 `World.reset()`으로 scene을 구성하고 `RMPFlowController.forward()`가 만든 `ArticulationAction`을 실제 로봇에 적용한다. target prim을 움직여 손끝 추종을 관찰한다. task의 observation은 target 위치/방향이며 화면 mesh를 직접 이동시키는 방식이 아니다. `--steps`를 생략하면 창을 닫을 때까지 손끝 추종을 계속한다.

## ROS 2 node import 선택 실습

Linux, ROS 2 Humble workspace, Universal Robots `ur_description`과 의존성이 필요하다. 각 터미널에서 같은 ROS 환경을 source한다.

1. 터미널 1: `ros2 launch ur_description view_ur.launch.py ur_type:=ur10e`를 실행한다.
2. 터미널 2: `ros2 node list`에서 `/robot_state_publisher` 이름을 확인한다.
3. 터미널 3: 같은 ROS 환경에서 Isaac Sim을 열고 `isaacsim.ros2.urdf`를 활성화한다. **File > Import from ROS 2 URDF Node**에서 실제 node 이름과 새 output 폴더를 넣어 Import한다.
4. publisher를 종료한 후 `ur_type:=ur3`으로 다시 실행하고 importer에서 **Refresh**, 다른 output 폴더, Import를 수행한다. XACRO의 ROS-side 확장 결과를 받아오는 방식이다.

ROS 2는 이 패키지가 자동 설치하거나 대신 실행하지 않는다. node 검색 실패는 ROS_DOMAIN_ID와 양쪽 환경을, mesh 누락은 package resource 경로를 확인한다. URDF import 오류는 XML/상대 mesh 경로·출력 쓰기 권한부터 확인한다. 문법과 CLI 도움말은 확인했으며 GPU 물리/RMPflow와 ROS import는 미검증이다.

## 출처

[Isaac Sim 5.1 Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html), [Python](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html#python-script), [ROS 2 node](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html#import-from-ros-2-node). API signature는 설치된 5.1 importer의 `impl/commands.py`와 대조했다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
