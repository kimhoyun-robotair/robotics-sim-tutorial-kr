# 52. 세 가지 Mobile Robot Controller

권장 학습 순서 **52** · 로봇 제어와 동작 계획 · 출처 ID `t134`

Jetbot의 차동 구동, Kaya의 전방향 구동, Leatherback의 Ackermann 조향을 실제 robot USD에 적용합니다. 각 controller의 출력 바퀴 속도와 로봇의 측정 포즈를 저장합니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

5.1 Assets의 `Isaac/Robots/NVIDIA/Jetbot/jetbot.usd`, `Isaac/Robots/NVIDIA/Kaya/kaya.usd`, `Isaac/Robots/NVIDIA/Leatherback/leatherback.usd`를 해당 모드별로 읽습니다. `get_assets_root_path()`가 가리키는 서버/로컬 팩에 선택한 USD와 종속 mesh/재질이 있어야 합니다.

터미널에서 이 패키지 폴더(`52_motion_mobile_robot_controllers`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --robot differential --speed 0.3 --turn 1
"$ISAAC_SIM_ROOT/python.sh" run.py --robot holonomic --speed 0.3 --lateral 0.2
"$ISAAC_SIM_ROOT/python.sh" run.py --robot ackermann --speed 1.1 --turn 0.1
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. `--robot differential`로 시작합니다. 반지름 0.03 m, 양 바퀴 간격 0.1125 m인 Jetbot의 왼쪽/오른쪽 wheel target을 `drive.json`에서 확인합니다. 전진 0.3 m/s, yaw 1 rad/s면 오른쪽 바퀴가 더 빨라야 합니다.
2. `--turn 0`으로 바꾸어 양 바퀴 목표 속도가 같은지 확인합니다. 차동 로봇은 옆으로 직접 이동할 수 없으며 제자리 회전은 좌우 바퀴 속도 차이로 만듭니다.
3. Kaya를 실행합니다. `HolonomicController`에 바퀴별 반지름, 중심 위치, quaternion 방향, roller 각도를 제공하고 `[vx, vy, yaw_rate]`를 전달합니다. `--speed 0 --lateral 0.3 --turn 0`을 사용하면 측면 이동 명령을 관찰할 수 있습니다.
4. Leatherback을 실행합니다. `AckermannController`는 wheelbase=1.65 m, track=1.25 m, wheel radius=0.25 m로 좌우 조향각과 네 바퀴 속도를 계산합니다. 안쪽/바깥쪽 바퀴가 서로 다른 원을 따라가므로 각도가 다릅니다.
5. Leatherback의 두 steering 관절에는 position command, 네 wheel 관절에는 velocity command를 **별도의 인덱스 집합**으로 적용합니다. 관절 이름은 코드의 목록과 `get_dof_index()`로 확인합니다.

## 입력을 해석하는 법

차동 구동에서 `ω_R=(2V+ωL)/(2r)`, `ω_L=(2V−ωL)/(2r)`입니다. V는 m/s, yaw ω는 rad/s, 결과는 바퀴 rad/s입니다. linear speed를 그대로 바퀴 회전 속도로 넣으면 반지름이 누락됩니다.

Kaya는 3개의 바퀴가 만드는 평면 속도를 제약식으로 두고 quadratic program을 풀어 필요한 회전 속도를 구합니다. 실제 5.1 `HolonomicController`의 `mecanum_angles`는 내부 degree 기반 회전 함수에 전달되며 공식 Kaya 예제는 90을 사용합니다. 문서의 일부 표에 radian이라고 적힌 것과 다르므로 임의로 π/2로 바꾸지 않습니다. quaternion은 w,x,y,z입니다. USD wheel joint에 `isaacmecanumwheel:radius`와 `isaacmecanumwheel:angle` 속성을 추가하여 형상을 설명하는 native workflow도 있습니다.

Ackermann 입력 순서는 `[steering_angle, steering_velocity, speed, acceleration, dt]`입니다. 이 실습은 steering_velocity/acceleration/dt를 0으로 두어 바로 원하는 속도/각도를 계산합니다. `--speed`는 **차체 m/s**이며 공식 코드의 `1.1 # rad/s` 주석을 그대로 해석하면 안 됩니다. `--turn`의 의미가 차동/Kaya에서는 yaw rad/s, Ackermann에서는 steering rad라는 차이를 옵션 설명에도 표시했습니다.

## OmniGraph로 재현하기

새 Action Graph에 On Playback Tick → 해당 **Differential Controller**, **Holonomic Controller**, **Ackermann Controller**의 exec 연결을 구성하고 출력 wheel velocity를 **Isaac Articulation Controller**의 velocityCommand로 연결합니다. robotPath와 관절 이름 배열을 코드와 동일하게 설정합니다. Ackermann은 steering angle 출력을 steering 관절용 Articulation Controller의 positionCommand로 보내며 wheel 제어용 노드와 분리합니다. Holonomic 노드에는 반지름/위치/방향/roller angle 배열을 바퀴 순서와 동일하게 연결합니다. Python과 그래프를 동시에 실행하지 않습니다.

## 관찰 기준과 한 변수 실험

`drive.json`에 wheel target, 초기/최종 위치, quaternion이 저장됩니다. 목표 바퀴 속도가 합리적이고 로봇 위치가 변하는지 함께 확인합니다. `--turn`의 부호만 바꾸어 회전 방향이 바뀌는지 확인합니다. wheel slip, 마찰, 접촉 안정화 때문에 기구학 계산만으로 정확한 이동 거리를 보장하지 않습니다.

## 문제 해결

로봇이 움직이지 않으면 wheel joint 이름과 velocity 모드, 바닥 접촉을 확인합니다. Kaya가 이상한 방향으로 움직이면 바퀴 순서/좌표계와 quaternion을 확인합니다. Leatherback에서 모든 관절에 같은 position/velocity 배열을 보내면 조향과 구동이 간섭할 수 있으므로 코드의 관절별 action을 유지합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Mobile Robot Controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.
