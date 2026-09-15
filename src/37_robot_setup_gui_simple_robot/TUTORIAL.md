# 37. 두 바퀴를 joint와 articulation으로 연결하기

권장 학습 순서 **37** · 로봇 자산 가져오기와 제작 · 출처 ID `t121`

공식 Articulate a Basic Robot의 GUI native 실습이다. 로컬 `run.py`는 `/Isaac/Samples/Rigging/MockRobot/mock_robot_no_joints.usd`를 새 편집 layer로 연다. 이 Isaac Sim 5.1 asset이 assets root에 있어야 한다. 별도 로컬 선행 수업 없이 cube와 바퀴에 이미 강체·충돌 속성이 있는 출발점을 사용한다.


## 이 실습의 의도

독립된 몸체·바퀴 강체를 revolute joint로 연결하고, articulation과 속도 제어를 추가하여 움직이는 로봇으로 만드는 수업이다. 먼저 joint가 부품을 붙잡는 역할을 확인하고, 이후 drive와 Action Graph가 바퀴 운동을 만드는 역할을 나누어 관찰한다. `run.py`는 joint 없는 공식 출발 asset을 열 뿐이므로 두 joint·drive·root·graph의 생성과 Play는 사용자가 GUI에서 진행한다.

## 실행 후 확인할 것

- **출발 상태:** 기본 장면을 처음 Play하면 몸체와 바퀴가 따로 떨어질 수 있다. `mock_robot_no_joints.usd`를 연 단계의 의도된 모습이며, `initial_inventory.json`은 이 초기 구조만 기록한다.
- **관절 연결:** GUI 작업 후 `/mock_robot/Joints`의 두 wheel joint가 몸체와 각 바퀴의 실제 강체 prim을 body0/body1으로 가리키는지 본다. axis=Y와 양쪽 local rotation을 확인하고, Play에서 한 부품을 움직여도 나머지가 연결을 유지하는지 확인한다.
- **drive 동작:** 각 Angular Drive의 stiffness=0, damping=10000, target velocity=200 deg/s를 확인한다. 속도 목표가 있는 동안 바퀴가 계속 도는 것이 기대 결과이며, 특정 각도에서 멈추는 위치 제어를 기대하지 않는다.
- **graph 명령:** `/mock_robot/Graphs/Velocity_Controller`를 만든 뒤 `JointCommandArray`의 두 입력을 1.0 rad/s로 주고 한쪽만 -1.0으로 바꿔 상대 회전 방향의 변화를 본다. graph가 매 step 목표를 쓰면 drive Property에서 앞서 넣은 200 deg/s가 계속 유지되는 것은 아니다.
- **완성 구조:** 저장한 stage에서 `/mock_robot`의 articulation root, 두 joint와 graph의 Robot Prim 연결을 함께 확인한다. 실행기 종료나 headless 장면 로드 성공만으로 이 연결·제어 실습이 완료되지는 않는다.

## 실행 환경과 파일

Isaac Sim **5.1.0**, 지원되는 RTX GPU와 GUI가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 설치 디렉터리다. Python CLI 도움말은 일반 Python에서도 열린다. 이 패키지는 자체 코드/설정을 가지며 다른 로컬 튜토리얼을 import하지 않는다.

```bash
cd src/37_robot_setup_gui_simple_robot
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

기본 실행은 창을 계속 열어 두므로 아래 GUI 실습을 수행하고 **Ctrl+S**로 로컬 root layer를 저장한 뒤 창을 닫는다. `output/first/stage.usda`와 `initial_inventory.json`이 생긴다. 기존 output은 덮어쓰지 않으므로 다음 실행은 `output/second`처럼 새 경로를 쓴다. 저장한 실습을 다시 열려면 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다. 재개 시에도 새 로컬 layer가 이전 결과를 참조한다.

GPU/UI 자동 점검을 위한 한정 실행은 `--headless --steps 120 --output output/check`다. 이는 장면 로드 확인만 하며 GUI 작업이나 로봇 동작의 성공을 증명하지 않는다. 패키지 작성 과정에서는 문법·CLI를 확인했으며 GPU와 실제 GUI 조작은 미검증이다.


## 단계별 실습

1. Stage에서 `mock_robot` 아래 body와 두 wheel을 확인한다. 각 geometry의 Property에 Rigid Body/Collider가 있어야 한다. 먼저 Play/Stop을 해 세 물체가 따로 떨어지는 출발 상태를 확인한다.
2. `/mock_robot/Joints` Scope를 만든다. `/mock_robot/body/body`와 `/mock_robot/wheel_left/wheel_left`를 이 순서로 Ctrl 선택하고 우클릭 **Create → Physics → Joints → Revolute Joint**. 이름을 `wheel_joint_left`로 정하고 Joints로 옮긴다.
3. joint Property의 body0/body1이 위 두 **강체 prim**인지 확인한다. **Local Rotation 0의 X=0**, **Local Rotation 1의 X=-90**, **Axis=Y**로 설정한다. cylinder의 부모가 X축으로 90도 회전했기 때문에 두 body의 local frame을 맞추는 것이다. wheel_right에도 같은 절차를 반복한다.
4. Play 후 Shift+드래그로 한 부분을 잡아 움직여 연결된 나머지 부품이 따라오는지 본다. joint pivot이 wheel 중심인지 확인한다. 강체가 순간이동하면 body target과 local frame을 먼저 수정한다.
5. 두 joint를 선택하고 **+ Add → Physics → Angular Drive**. stiffness=0, damping=10000, target velocity=200으로 둔다. **USD drive Property의 angular velocity는 deg/s**다. 원문 중 rad/s 표기와 혼동하지 않는다. API/Articulation Controller에서 200 rad/s를 보내는 것과 다르다.
6. `/mock_robot`에 **+ Add → Physics → Articulation Root**를 추가한다. 이 로봇은 floating base이므로 root rigid body 또는 그 ancestor를 사용한다. fixed-base 로봇은 world와 연결된 fixed joint에 root를 두는 경우가 일반적이다.
7. `/mock_robot/Graphs` Scope를 만든다. **Tools → Robotics → Omnigraph Controllers → Joint Velocity**를 열어 Robot Prim=/mock_robot, Graph Path=/mock_robot/Graphs/Velocity_Controller를 지정한다.
8. Play하고 Graph의 `JointCommandArray` input0/input1을 각각 1.0으로 둔다. 이 값은 **rad/s**다. 두 바퀴의 움직임을 보고 하나만 -1.0으로 바꾼다. 생성 graph가 값을 매 step 덮어쓰므로 이후 명령은 drive UI와 graph 중 어느 경로에서 오는지 구분한다.
9. Stop 후 root layer를 저장한다. 비교 asset `/Isaac/Samples/Rigging/MockRobot/mock_robot_rigged.usd`의 body target, joint axis, drive와 articulation root를 대조한다.

## USD/API 해설과 실패 원인

Joint는 장면 트리의 parent-child 위치가 아니라 **body0/body1 relationship**으로 두 강체를 연결한다. Scope로 옮겨도 연결은 유지된다. Revolute는 한 회전 자유도만 허용한다. Drive는 허용된 자유도에 힘/토크를 만들어 목표에 접근시킨다. `ArticulationRootAPI`는 연결된 물리 트리를 solver에 묶어 주며, Action Graph의 articulation controller가 매 frame 관절 명령을 적용한다.

속도 제어는 stiffness=0, 양의 damping이 핵심이다. position control은 위치 오차에 대응하는 stiffness가 필요하다. 각도를 바꿀 때 deg↔rad는 π/180을 사용한다. 한 변수 실험으로 input1만 부호를 바꾸고 나머지는 유지한다. 로봇이 분해되면 body target 누락, 진동하면 frame 불일치나 collider 겹침, 제어가 안 되면 articulation root와 graph의 Robot Prim을 확인한다.

## 출처

- [Isaac Sim 5.1 Tutorial 3: Articulate a Basic Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_simple_robot.html)
- 로컬 설명/코드는 해당 버전의 실제 GUI 작업을 재구성한 실습이며 NVIDIA 문서 전문을 복제하지 않는다.
