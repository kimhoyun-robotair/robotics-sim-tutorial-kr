# 80. OmniGraph로 Jetbot의 바퀴를 움직이기

## 이번에 배우는 것

**전진·회전 명령을 바퀴 속도로 바꾸는 그래프를 직접 연결하고, 자동 생성한 WASD 그래프에서도 같은 흐름을 찾아봅니다.**

“초당 0.1 m로 전진하세요”라는 명령은 바퀴 관절이 바로 사용하는 값이 아닙니다. 바퀴 크기를 고려해 좌우 각속도로 바꾼 뒤 각 관절에 전달해야 합니다. OmniGraph는 이 계산과 실행을 노드와 선으로 표현합니다.

| 그래프 요소 | 역할 | 이 실습에서 확인할 값 |
|---|---|---|
| On Playback Tick | 재생 중 실행 신호 제공 | 두 controller의 `execIn` |
| Differential Controller | 몸체 속도를 좌우 바퀴 속도로 변환 | 반지름 0.03 m, 좌우 바퀴 간격 0.1125 m |
| Constant Token + Make Array | 바퀴 이름을 순서대로 전달 | 왼쪽, 오른쪽 관절 |
| Articulation Controller | 계산 결과를 로봇 관절에 적용 | `/World/jetbot` |

이 폴더에는 자동 실행 코드나 Jetbot USD가 없습니다. GUI에서 공식 자산을 불러오고 그래프를 만드는 실습입니다.

## 1. Jetbot과 수동 그래프 준비하기

Isaac Sim 5.1.0 GUI와 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음으로 시작하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 새 장면을 열고 **Create > Physics > Ground Plane**을 추가합니다.
2. Content Browser의 `Isaac Sim/Robots/NVIDIA/Jetbot/jetbot.usd`를 장면으로 드래그합니다. 공식 NVIDIA 자산 경로에 접근할 수 있어야 합니다.
3. 로봇 prim 경로를 `/World/jetbot`, 위치를 `(0, 0, 0.1)` m로 맞춥니다.
4. **Play**로 바닥에 착지하는지 확인한 뒤 **Stop**합니다. Stage에서 `left_wheel_joint`, `right_wheel_joint`를 찾습니다.
5. **Window > Graph Editors > Action Graph > New Action Graph**로 빈 그래프를 만듭니다.

### 설정에서 볼 부분

**Articulation Controller**, **Differential Controller**, **On Playback Tick**, **Constant Token** 두 개, **Make Array**를 추가합니다. 각 노드 선택 후 Property에서 설정하세요.

| 노드 | 입력 | 값 |
|---|---|---|
| Articulation Controller | `robotPath` | `/World/jetbot` |
| Differential Controller | `wheelRadius` / `wheelDistance` | `0.03` / `0.1125` m |
| Differential Controller | `maxAngularSpeed` | `0.2` rad/s |
| Constant Token 두 개 | 값 | `left_wheel_joint`, `right_wheel_joint` |
| Make Array | `arraySize` / 타입 | `2` / `token[]` |

Articulation Controller에 `usePath`가 보이면 경로 사용으로 설정합니다. 또는 `targetPrim`에 로봇을 직접 지정할 수 있습니다. Articulation은 관절로 연결된 강체 묶음이며, controller가 적용할 로봇을 이 입력으로 정합니다.

Make Array에서 `+`로 두 번째 입력을 추가한 뒤 다음과 같이 연결하세요.

```text
왼쪽 Constant Token → Make Array.input0
오른쪽 Constant Token → Make Array.input1
Make Array.array → Articulation Controller.jointNames

On Playback Tick.tick → Differential Controller.execIn
On Playback Tick.tick → Articulation Controller.execIn
Differential Controller.velocityCommand → Articulation Controller.velocityCommand
```

실행 신호와 숫자·이름 데이터는 역할이 다릅니다. Tick 선은 노드를 실행하게 하고, 다른 선은 계산할 값이나 적용 대상을 전달합니다. **5.1의 Differential Controller에는 `execOut`이 없으므로 tick을 두 controller에 각각 연결합니다.**

### 실행 결과 확인하기

Play한 뒤 Differential Controller의 Desired Linear Velocity를 `0.1`, Desired Angular Velocity를 `0`으로 설정합니다. 두 바퀴가 같은 방향으로 돌고 몸체가 직진하는지 보세요.

이어 선속도를 `0`, 각속도를 `0.2`로 바꿉니다. 좌우 바퀴 명령이 반대 부호가 되고 로봇이 제자리에서 회전하는지 확인한 뒤 두 입력을 0으로 돌립니다. 그래프가 화면에 존재한다는 것보다 **계산 출력과 실제 로봇 반응이 이어지는지**가 확인 대상입니다.

Stop한 뒤 **File > Save As**로 이 튜토리얼 폴더에 `manual_graph.usda`를 저장하세요. 4절의 반지름 실험에서 이 수동 그래프를 다시 사용합니다.

## 2. 같은 제어를 WASD 그래프로 만들기

Stop한 뒤 앞의 수동 그래프를 삭제합니다. 같은 바퀴에 두 그래프가 동시에 명령하지 않도록 한 가지 입력 경로만 남깁니다.

1. **Tools > Robotics > Omnigraph Controllers > Differential Controller**를 엽니다.
2. Robot Prim=`/World/jetbot`, Graph Path=`/Graph/differential_controller`로 지정합니다.
3. Wheel Radius=`0.03`, Distance between wheels=`0.1125`를 넣습니다.
4. Left Joint Name=`left_wheel_joint`, Right Joint Name=`right_wheel_joint`, Use Keyboard Control (WASD)=On으로 생성합니다.

### 설정에서 볼 부분

자동 생성한 그래프도 열어 확인하세요. 바퀴 이름을 담는 `ArrayNames`의 **input0은 왼쪽, input1은 오른쪽**이 되도록 맞춥니다. 설치된 5.1 생성 코드에서는 입력한 좌·우 이름이 반대 순서로 배열에 들어갈 수 있으므로, 팝업 입력만 보고 순서가 맞다고 가정하지 않습니다.

`ScaleLinear`는 `0.1`, `ScaleAngular`는 `0.2`로 설정합니다. 키 상태는 눌림/해제 값이므로 이 배율이 실제 선속도와 각속도로 바꾸어 줍니다. 처음 실행할 때 도구가 생성한 기본 배율을 그대로 두지 말고 이 작은 로봇에 사용할 값을 확인하세요.

### 실행 결과 확인하기

Play하고 뷰포트를 클릭해 키보드 입력 초점을 줍니다. W/S로 전후 이동, A/D로 반대 방향 회전이 나타나는지 확인합니다. 키를 뗐을 때 입력이 돌아오는지도 봅니다. 마친 뒤 Stop하고 필요하면 **File > Save As**로 장면과 그래프를 저장하세요. 이 실습은 CSV를 자동 생성하지 않습니다.

## 3. 몸체 속도에서 바퀴 속도까지 정리

바퀴 반지름을 r, 바퀴 사이 거리를 L, 선속도를 v, 회전 속도를 ω라고 하면 계산은 다음과 같습니다.

```text
왼쪽 바퀴 각속도 = (v - ωL/2) / r
오른쪽 바퀴 각속도 = (v + ωL/2) / r
```

직진 `v=0.1`, `ω=0`에서는 두 값이 모두 약 `3.33 rad/s`입니다. 제자리 회전 `v=0`, `ω=0.2`에서는 약 `-0.375`, `+0.375 rad/s`입니다. 바퀴 이름 순서가 반대면 회전 명령의 해석도 반대가 될 수 있습니다.

Differential Controller는 이 수치를 계산하고, Articulation Controller는 같은 순서의 관절에 전달합니다. 실제 주행은 바닥 접촉과 물리 상태에도 영향을 받으므로 계산값과 화면을 함께 봅니다.

## 4. 간단한 확인 실험

**File > Open**으로 1절에서 저장한 `manual_graph.usda`를 엽니다. 수동 그래프의 직진 조건에서 **wheelRadius만 0.03에서 0.06으로** 바꿔 보세요.

먼저 Stop하고 반지름을 바꾼 뒤 다시 Play합니다. 선속도 `0.1`, 각속도 `0`을 다시 입력하세요. 이 노드는 반지름을 초기화할 때 읽으므로 재생 중 값만 바꾸어 비교하면 적용 시점을 놓칠 수 있습니다.

계산된 각속도는 약 `3.33 → 1.67 rad/s`로 절반이 예상됩니다. 실제 USD 바퀴 크기는 그대로이므로 로봇도 원래 목표보다 느리게 움직일 수 있습니다. 이 실험은 **제어기에 입력한 치수와 실제 로봇 치수가 일치해야 하는 이유**를 보여줍니다.

## 실행할 때 막히면

- **노드가 있지만 움직이지 않음**: Play, 두 execIn 연결, robotPath와 바퀴 이름을 차례로 확인하세요.
- **회전 방향이 예상과 반대임**: `jointNames` 배열이 계산 출력의 왼쪽·오른쪽 순서와 맞는지 보세요. 자동 생성 그래프도 검사 대상입니다.
- **WASD가 반응하지 않음**: 뷰포트를 클릭하고 입력하세요. 문자열 입력란에 초점이 있으면 키가 로봇으로 전달되지 않을 수 있습니다.
- **반지름 수정이 반영되지 않음**: Stop→수정→Play 후 속도 명령을 다시 입력하세요. Stop하면 속도 입력도 초기화됩니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Isaac Sim Omnigraph Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_tutorial.html)에 대응합니다. 수동 연결과 shortcut 생성에 계산 예와 실제 출력 순서 검사를 더했습니다.

공식 절차와 설치된 controller·그래프 생성 소스를 대조했습니다. 이번 개정에서는 Jetbot GUI 주행을 실행하지 않았고 `tutorial.json`은 `not_run`입니다. 위 각속도는 제어식의 기대값이며 실제 로봇 측정값이 아닙니다.
