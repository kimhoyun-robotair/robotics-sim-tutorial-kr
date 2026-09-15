# 81. 자주 쓰는 제어 그래프를 단축 메뉴로 만들기

## 이번에 배우는 것

**네 가지 controller shortcut을 사용하고, 각 그래프가 요구하는 명령의 단위와 제어 대상을 구분합니다.**

단축 메뉴는 로봇 이름을 입력하면 노드와 연결을 만들어 줍니다. 편리하지만 어떤 관절에 어떤 값이 전달되는지 읽을 수 있어야 결과를 고칠 수 있습니다. 이번에는 Franka의 팔, Jetbot의 바퀴, Franka의 손가락을 차례로 다룹니다.

| Shortcut | 제어할 대상 | 이번에 넣을 명령 |
|---|---|---|
| Joint Position Controller | Franka의 회전 관절 | 목표 각도 `0.2 rad` |
| Joint Velocity Controller | 같은 회전 관절 | 각속도 `0.1 rad/s` |
| Differential Controller | Jetbot의 두 바퀴 | 몸체 선속도 `0.1 m/s` |
| Open Loop Gripper Controller | 두 손가락의 직선 관절 | 열림 `0.04 m`, 닫힘 `0 m` |

숫자가 비슷해도 위치, 속도, 길이는 다른 물리량입니다. 그래프 생성 뒤에는 명령 배열과 관절 이름 배열의 같은 인덱스가 대응하는지 확인합니다.

## 1. Franka의 위치 명령과 속도 명령 비교하기

Isaac Sim 5.1.0 GUI와 지원 NVIDIA GPU가 필요합니다. 이 폴더는 GUI 절차만 제공하며 로봇은 공식 Content 자산에서 불러옵니다. 저장소 루트에서 다음으로 시작하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 새 장면을 열고 **Create > Physics > Ground Plane**을 만듭니다.
2. Content Browser에서 `Isaac Sim/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 추가합니다. 로봇 경로를 `/World/Franka`로 맞춥니다.
3. **Tools > Robotics > Omnigraph Controllers > Joint Position Controller**를 엽니다.
4. Robot Prim=`/World/Franka`, Graph Path=`/Graph/arm_position`, Add to Existing Graph=Off로 생성합니다.
5. Action Graph에서 `JointNameArray`와 `JointCommandArray`를 찾아 `panda_joint1`에 해당하는 인덱스를 확인합니다.

### 설정에서 볼 부분

관절 이름 배열에서 `panda_joint1`이 i번째라면 명령 배열에서도 i번째 값을 바꿉니다. “첫 관절이니 무조건 첫 항목”으로 짐작하지 말고 실제 배열을 보세요. 생성된 그래프에 손가락 관절까지 들어 있을 수 있습니다.

Play한 뒤 해당 위치 목표만 `0.2` rad로 바꿉니다. 다른 값은 유지하고 그 관절이 목표 각도 쪽으로 움직이는지 확인하세요. USD에 초기 drive target이 저장되어 있으면 Play 직후에도 움직일 수 있으므로, 직접 값을 바꾼 시점의 반응을 따로 관찰합니다.

### 실행 결과 확인하기

Stop한 뒤 position 그래프를 삭제합니다. Stage에서 `panda_joint1` 관절 Prim을 찾아 Property의 **Angular Drive > Stiffness를 0, Damping을 100**으로 설정합니다. 다른 관절의 drive는 유지하세요. 위치로 되돌리는 스프링 항을 끄고 속도 오차에 반응하는 항을 남기는 설정입니다. 이 조건은 [공식 5.1 관절 제어 API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.manipulators/docs/index.html)의 속도 제어 조건과 같습니다.

같은 로봇에서 **Joint Velocity Controller**를 `/Graph/arm_velocity`에 새로 만드세요. Shortcut은 명령 연결을 생성하지만 기존 drive의 Stiffness를 자동으로 0으로 바꾸지 않습니다. Play하고 같은 관절에 해당하는 속도만 `0.1` rad/s로 설정했다가 곧 `0`으로 돌립니다.

| 명령 | 기대하는 관찰 | 값을 유지하면 |
|---|---|---|
| 위치 0.2 rad | 지정한 자세로 이동 | 그 자세를 목표로 유지합니다. |
| 속도 0.1 rad/s | 시간이 지나며 각도가 변화 | 관절 제한 등에 도달하기 전까지 계속 움직입니다. |
| 속도 0 rad/s | 정지 방향의 반응 | 새 목표 위치를 지정하는 것은 아닙니다. |

위치 그래프와 속도 그래프를 동시에 남겨 비교하지 마세요. 같은 관절에 서로 다른 명령을 쓰면 지금 보고 있는 반응의 원인이 불명확해집니다.

## 2. 바퀴와 그리퍼용 그래프 만들기

### 설정에서 볼 부분: Jetbot

새 Stage에 바닥과 `Isaac Sim/Robots/NVIDIA/Jetbot/jetbot.usd`를 추가하고 `/World/jetbot`, Z=`0.1` m로 놓습니다. **Differential Controller** shortcut에 다음을 입력하세요.

| 입력 | 값 |
|---|---|
| Robot Prim / Graph Path | `/World/jetbot` / `/Graph/jetbot_drive` |
| Wheel Radius / Distance between wheels | `0.03` / `0.1125` m |
| Left Joint Name | `left_wheel_joint` |
| Right Joint Name | `right_wheel_joint` |
| Use Keyboard Control | 처음에는 Off |

생성 그래프의 `ArrayNames`를 열어 input0=`left_wheel_joint`, input1=`right_wheel_joint`인지 확인하고 다르면 맞춥니다. 설치된 5.1 생성 코드가 좌·우 입력을 반대 순서로 배열에 넣을 수 있으므로 실제 연결까지 확인하는 단계입니다.

Play한 뒤 DifferentialController의 Desired Linear Velocity=`0.1`, Desired Angular Velocity=`0`으로 직진을 봅니다. 관찰 후 0으로 되돌리고 Stop합니다. 바퀴에 입력한 값은 몸체 선속도이며 그래프가 이를 바퀴 각속도로 변환합니다.

이 그래프를 삭제하고 같은 입력에서 WASD를 켜 다시 생성하세요. 이름 배열 순서를 확인한 뒤 `ScaleLinear=0.1`, `ScaleAngular=0.2`로 설정합니다. Play하고 뷰포트를 클릭해 W/A/S/D를 누릅니다. 배율은 키의 눌림 값을 실제 이동 속도로 바꾸는 값입니다.

Stop하고 **File > Save As**로 이 튜토리얼 폴더에 `jetbot_keyboard.usda`를 저장하세요. 그리퍼를 새 장면에서 실습한 뒤 4절에서 이 파일을 다시 엽니다.

### 설정에서 볼 부분: Franka 그리퍼

새 Stage에 다시 Franka를 넣습니다. **Open Loop Gripper Controller**에 아래 값을 입력하세요.

| 입력 | 값 | 의미 |
|---|---|---|
| Parent Robot | `/World/Franka` | 관절 제어 대상 로봇 |
| Gripper Root Prim | `/World/Franka/panda_hand` | 손가락이 속한 부분 |
| Graph Path | `/Graph/gripper` | 생성할 그래프 주소 |
| Joint Names | `panda_finger_joint1,panda_finger_joint2` | 제어할 두 직선 관절 |
| Gripper Speed | `0.001` m/실행 | 매 그래프 평가에서 손가락 목표 위치에 더할 거리 |
| Open Limit / Close Limit | `0.04` / `0.0` m | 각 관절의 열림·닫힘 위치 |
| Use Keyboard Control | On | O/C/N 입력 사용 |

Play 후 뷰포트에 초점을 주고 **O=열기, C=닫기, N=정지**를 시험합니다. 열림 값 0.04 m는 각 손가락 관절 위치입니다. 두 손가락 사이의 전체 간격을 그대로 0.04 m라고 해석하지 않습니다.

설치된 5.1의 이 Gripper 노드는 Speed에 시간 간격을 곱하지 않고, 실행될 때마다 목표 위치에 그 값을 더하거나 뺍니다. 따라서 `0.001`이면 1회에 1 mm씩 목표를 바꿉니다. 0에서 0.04 m까지는 목표 갱신 약 40회가 필요하며 실제 손가락은 drive 응답에 따라 뒤따릅니다. 공식 소개 페이지의 m/s 표기와 달리 이 구현의 UI tooltip과 노드 정의는 **distance per frame**입니다. 여기의 숫자를 초당 속도로 해석하지 마세요.

### 실행 결과 확인하기

바퀴에서는 몸체 이동과 좌우 속도를, 그리퍼에서는 두 finger joint의 위치를 봅니다. 이 GUI 실습은 결과 파일을 자동 기록하지 않으므로 필요한 장면은 **File > Save As**로 저장하세요. 마친 뒤 Stop합니다.

각 팝업의 **Python Script for Graph Generation** 아이콘을 열면 실제 생성 코드를 볼 수 있습니다. `make_graph()`에서 로봇 경로, 이름 배열, 명령 배열, 실행 연결을 찾아 방금 만든 그래프와 대조해 보세요.

## 3. 단축 메뉴가 만들어 주는 것 정리

```text
팝업 입력 → 노드·배열·연결 생성
               ↓
Play + 명령값 또는 키 입력 → controller 실행 → 관절 동작
```

Shortcut은 생성 작업을 돕습니다. 이미 다른 그래프가 같은 로봇을 제어하는지까지 검사하지는 않습니다. Add to Existing Graph를 켜면 기존 tick을 재사용할 수 있지만 새로운 controller도 추가되므로 중복 제어 여부는 직접 확인해야 합니다.

팔과 그리퍼를 함께 사용한다면 팔 그래프의 이름·명령 배열에서 두 finger를 제외하여 각 관절의 담당 그래프를 정하세요. 손가락별 속도나 한계가 다른 경우에는 팝업의 공통값 대신 생성된 그래프의 배열 연결을 수정해야 합니다.

## 4. 간단한 확인 실험

**File > Open**으로 2절에서 저장한 `jetbot_keyboard.usda`를 엽니다. **ScaleLinear만 0.1에서 0.05로** 줄여 보세요. ScaleAngular와 바퀴 치수는 유지합니다.

Play하고 뷰포트에서 W를 누를 때 Desired Linear Velocity 입력이 `0.05 m/s`로 바뀌는지 확인합니다. 가감속과 미끄러짐 영향이 작다면 같은 시간 동안 움직인 거리도 줄어드는 것이 예상됩니다. A/D의 회전 명령 배율은 바꾸지 않았으므로 그대로여야 합니다. 화면만 보지 말고 `SpeedLinear` 출력과 controller 입력도 함께 확인하세요.

## 실행할 때 막히면

- **메뉴가 없음**: Extensions에서 `isaacsim.robot.manipulators.ui` 또는 `isaacsim.robot.wheeled_robots.ui`의 활성 상태를 확인하세요.
- **예상하지 않은 관절이 움직임**: 이름 배열과 명령 배열의 인덱스를 대조하고, 다른 그래프와 초기 drive target을 확인하세요.
- **속도를 주어도 팔이 원래 각도 근처에서 멈춤**: `panda_joint1`의 위치 drive Stiffness가 남아 있을 수 있습니다. Stop한 뒤 1절의 속도 제어 설정을 확인하세요.
- **회전 방향이 뒤바뀜**: Jetbot의 생성된 이름 배열이 왼쪽·오른쪽 출력 순서와 맞는지 확인하세요.
- **O/C가 손가락에 전달되지 않음**: Play, 키보드 초점, gripper root와 두 관절 이름을 확인하세요. 회전 관절의 rad 값과 finger의 m 값을 섞지 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Commonly Used Omnigraph Shortcuts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_shortcuts.html)에 대응합니다. 네 단축 메뉴를 각각의 로봇 동작과 명령 단위에 연결한 GUI 실습입니다.

공식 설명과 설치된 그래프 생성 소스를 대조했습니다. 이번 개정에서는 로봇 GUI 동작을 실행하지 않았으며 `tutorial.json`의 상태는 `not_run`입니다. 실제 자산 로딩과 관절 반응은 위 순서대로 확인해야 합니다.
