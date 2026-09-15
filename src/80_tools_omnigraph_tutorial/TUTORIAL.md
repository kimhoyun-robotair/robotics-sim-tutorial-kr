# 80. Isaac Sim Omnigraph Tutorial

권장 학습 순서 **80** · OmniGraph와 확장 개발 · 출처 ID `t109`

Jetbot의 바퀴 속도를 계산하는 Differential Controller와 물리에 적용하는 Articulation Controller를 직접 연결한다. 뒤에서는 같은 그래프를 WASD shortcut으로 생성한다.

## 이 실습의 의도

Jetbot의 선속도·각속도를 좌우 바퀴 명령으로 바꾸는 계산과, 그 명령을 실제 관절에 적용하는 실행을 두 controller로 나누어 이해한다. 먼저 tick·데이터·관절 이름을 직접 연결한 뒤 WASD shortcut이 만든 그래프와 비교하여 자동 생성된 연결도 읽을 수 있게 하는 실습이다. 제공된 자동 실행 파일이나 로봇 장면은 없으므로 GUI에서 Jetbot 자산을 불러오고 그래프를 구성한 뒤 Play와 속도 입력까지 수행해야 주행을 관찰할 수 있다.

## 실행 후 확인할 것

- Stage에서 `/World/jetbot`이 바닥 위에 착지하고 `left_wheel_joint`, `right_wheel_joint`가 있는지 확인한다. Action Graph의 jointNames 배열이 이 좌·우 순서와 맞아야 계산된 두 속도가 올바른 바퀴에 전달된다.
- tick이 Differential Controller와 Articulation Controller의 `execIn` 양쪽으로 연결되고, `velocityCommand` 출력이 Articulation Controller 입력으로 이어지는지 확인한다. 노드가 나열되어 있는 상태만으로 제어가 실행되지는 않는다.
- Play 중 linear=`0.1`, angular=`0`에서는 두 바퀴의 명령이 같은 방향이고 본체가 직진하는지 본다. linear=`0`, angular=`0.2`에서는 반대 방향의 바퀴 명령과 본체의 제자리 회전을 확인한 뒤 두 입력을 0으로 되돌린다.
- WASD 단계에서는 수동 그래프를 제거한 뒤 생성된 그래프의 실제 경로와 관절 대상을 확인한다. Viewport에 focus를 주고 W/S의 전후 이동, A/D의 회전이 나타나는지 보며, 같은 바퀴에 명령하는 다른 그래프가 남아 있지 않은지 확인한다.
- wheelRadius만 두 배로 바꾼 비교에서는 같은 선속도 입력에 대한 계산된 바퀴 각속도가 절반으로 바뀌는지 본다. USD의 실제 바퀴 크기를 바꾸는 실험이 아니므로 입력 반지름을 잘못 주면 주행 속도도 목표와 달라질 수 있다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 1. Jetbot 장면

1. `File > New`, `Create > Physics > Ground Plane`으로 바닥을 만든다.
2. Content의 `Isaac Sim > Robots > NVIDIA > Jetbot > jetbot.usd`를 드래그한다. prim 경로를 `/World/jetbot`, 위치를 `(0,0,0.1)` m로 맞춘다. 공식 5.1 자산 접근이 필요하다.
3. Play로 바닥에 착지하는지 확인하고 Stop한다. Stage의 `jetbot/chassis` 아래 `left_wheel_joint`, `right_wheel_joint`를 확인한다.

## 2. 그래프 수동 생성

1. `Window > Graph Editors > Action Graph > New Action Graph`를 연다.
2. **Articulation Controller**, **Differential Controller**, **On Playback Tick**, **Constant Token** 2개, **Make Array**를 추가한다.
3. Articulation Controller의 robotPath를 `/World/jetbot`으로 하거나 targetPrim에 그 로봇을 지정한다. 5.1 UI에 usePath가 있으면 경로 방식에 맞춰 켠다.
4. Differential Controller의 wheelDistance=`0.1125`, wheelRadius=`0.03`, maxAngularSpeed=`0.2`로 설정한다.
5. Token 두 개의 값은 `left_wheel_joint`, `right_wheel_joint`다. Make Array는 입력 2개, arraySize=2, 타입 `token[]`으로 설정한다. 왼쪽 이름→input0, 오른쪽→input1, array→Articulation Controller의 jointNames로 연결한다.
6. On Playback Tick의 tick을 **Differential Controller execIn**과 **Articulation Controller execIn** 양쪽에 연결한다. 5.1 Differential Controller에는 execOut 포트가 없다. Differential Controller의 velocityCommand→Articulation Controller velocityCommand도 연결한다.
7. Play 중 Desired Linear Velocity=`0.1`, Desired Angular Velocity=`0`으로 바꾸면 직진한다. linear=`0`, angular=`0.2`는 제자리 회전이다. 관찰 후 둘 다 0으로 돌린다.

## 3. WASD shortcut

1. Stop하고 앞의 그래프를 삭제한다. 한 로봇 바퀴에 두 controller가 명령하지 않게 한다.
2. `Tools > Robotics > Omnigraph Controllers > Differential Controller`를 연다.
3. Robot Prim/Articulation Root=`/World/jetbot`, Graph Path=`/Graph/differential_controller`, wheel distance=`0.1125`, radius=`0.03`, Use Keyboard Control (WASD)=On으로 한다. 이름을 명시한다면 left/right 순서를 맞춘다.
4. OK 후 `/Graph/differential_controller`를 열어 생성 결과를 비교한다. Play 후 Viewport를 클릭하여 키보드 focus를 주고 W/A/S/D로 이동한다.

## API/물리 해설과 확인

Articulation은 관절로 연결된 강체 집합이다. Differential Controller는 선속도 v(m/s), 각속도 ω(rad/s)를 `(v−ωL/2)/r`, `(v+ωL/2)/r`의 좌/우 바퀴 각속도로 바꾼다. radius는 바퀴 반지름, distance는 좌우 바퀴 사이 거리다. Articulation Controller는 이 결과를 지정한 joint names의 velocity target에 쓴다. execution 선은 계산 순서, token/velocity 선은 데이터다.

한 변수 실험: 같은 v 명령에서 wheelRadius만 두 배로 하면 계산된 각속도가 절반이 되는지 Property에서 본다. 실제 자산 크기는 바뀌지 않으므로 잘못된 radius 입력은 속도 오차를 만든다. 움직이지 않으면 Play, robot prim, 관절 이름 순서, 바닥/충돌, 중복 controller를 확인한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html).
