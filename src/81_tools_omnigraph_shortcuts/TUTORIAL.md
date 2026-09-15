# 81. Commonly Used Omnigraph Shortcuts

권장 학습 순서 **81** · OmniGraph와 확장 개발 · 출처 ID `t106`

네 종류의 controller shortcut을 생성하고 각 입력이 무엇을 바꾸는지 확인하는 GUI 실습이다. 단축 메뉴는 생성만 도우며 같은 로봇을 이미 제어하는 그래프가 있는지 자동 검사하지 않는다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## A. Joint Position / Joint Velocity

1. 새 Stage에 `Create > Physics > Ground Plane`, Content `Isaac Sim > Robots > FrankaRobotics > FrankaPanda > franka.usd`를 추가한다. 로봇 prim 경로를 `/World/Franka`로 맞춘다.
2. `Tools > Robotics > Omnigraph Controllers > Joint Position Controller`를 선택한다. Robot Prim=`/World/Franka`, Graph Path=`/Graph/arm_position`, Add to Existing Graph=Off, OK.
3. 생성된 그래프의 `JointCommandArray`와 joint name array를 확인한다. Play 후 **panda_joint1에 대응하는 값만 0.2 rad**로 바꾼다. 관절 이름과 배열 인덱스를 확인한 뒤 해당 값만 편집한다.
4. Stop 후 position 그래프를 삭제한다. **Joint Velocity Controller**를 같은 로봇/새 경로 `/Graph/arm_velocity`로 만든다. Play 후 같은 관절에 `0.1 rad/s`를 잠시 주고 곧 0으로 돌린다. 위치 명령은 목표, 속도 명령은 계속 움직이는 명령이라는 차이를 본다.

## B. Differential Controller

1. 새 Stage에 바닥과 Content `Isaac Sim > Robots > NVIDIA > Jetbot > jetbot.usd`를 추가하고 `/World/jetbot`, z=`0.1`로 한다.
2. Differential Controller shortcut에서 Robot Prim=`/World/jetbot`, Graph Path=`/Graph/jetbot_drive`, Wheel Radius=`0.03`, Distance between wheels=`0.1125`, Left Joint Name=`left_wheel_joint`, Right Joint Name=`right_wheel_joint`를 입력한다.
3. Use Keyboard Control=Off로 생성한 뒤 Play하고 DifferentialController의 Desired Linear Velocity=`0.1`, Desired Angular Velocity=`0`을 시험한다. 관찰 후 0으로 돌린다.
4. 기존 그래프를 삭제하고 WASD=On으로 다시 생성한다. Viewport에 focus를 준 뒤 W/A/S/D를 누른다. `ScaleLinear`, `ScaleAngular`의 값은 키의 0/1 입력을 로봇에 맞는 속도로 변환한다. wheel names와 indices를 동시에 다른 순서로 지정하지 않는다.

## C. Open Loop Gripper Controller

1. 새 Stage의 Franka에서 gripper prim `/World/Franka/panda_hand`와 `panda_finger_joint1`, `panda_finger_joint2` 위치를 확인한다.
2. Open Loop Gripper Controller에서 Parent Robot=`/World/Franka`, Gripper Root=`/World/Franka/panda_hand`, Joint Names=`panda_finger_joint1,panda_finger_joint2`, speed=`0.02` m/s, Open Limit=`0.04`, Close Limit=`0.0`, Keyboard=On을 입력한다.
3. Play 후 O=열기, C=닫기, N=정지를 시험한다. finger 하나당 한 개 구동 자유도를 갖는 gripper에 쓰는 controller다.
4. arm position controller와 함께 쓰려면 arm 그래프 joint name/command arrays에서 finger 두 개를 제거한다. 같은 관절을 양쪽 그래프가 제어하면 충돌한다.

## 생성 API와 해설

각 popup의 **Python Script for Graph Generation** 아이콘은 설치된 생성 코드를 연다. `make_graph()`에서 node 생성·값 설정·연결을 찾아 현재 그래프와 대조한다. Add to Existing Graph는 tick을 재사용할 수 있지만 controller를 항상 추가하므로 중복 제어를 막아주지 않는다. 같은 Graph Path가 있으면 숫자를 붙여 새 경로를 만들 수 있다.

USD prim은 로봇/graph의 장면 경로, articulation은 관절 강체 묶음이다. 회전 관절은 rad/rad·s⁻¹, 직선 finger 관절은 m/m·s⁻¹다. Open/Close limit을 비우면 USD joint limit을 쓰고 shortcut은 open 값이 close보다 큰 방향을 가정한다. 손가락마다 다른 속도/한계가 필요하면 생성된 그래프의 speed/limit 입력에 배열을 연결한다.

성공 기준은 지정 관절만 이동, Jetbot 직진/회전, finger 개폐/정지다. 한 변수 실험: ScaleLinear만 절반으로 바꾸어 W 직진 속도 변화를 본다. 메뉴가 없으면 controller 관련 robotics extensions, 움직임이 튀면 중복 graph와 USD에 저장된 초기 drive target을 확인한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_shortcuts.html).
