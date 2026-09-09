# 디지털 트윈, Cortex와 창고 응용 실습

디지털 트윈 실습에서는 환경의 모양뿐 아니라 로봇, 센서, 작업 순서와 운영 데이터를 함께 다룬다. 이 장에서는 창고 장면의 구조를 정리하고, NVIDIA가 제공하는 Cortex 예제로 상황에 따라 행동을 바꾸는 방법을 확인한다.

## 1. 환경과 로봇을 나누어 관리하기

같은 창고에서 로봇 모델이나 작업만 바꾸려면 환경 전체를 복사하기보다 참조와 레이어를 나누는 편이 관리하기 쉽다.

| 권장 Prim 경로 | 담을 내용 | 첫 확인 항목 |
| --- | --- | --- |
| `/World/Environment` | 바닥, 벽, 선반, 조명 | 실제 치수, 충돌 형상, 조명 |
| `/World/Infrastructure` | 컨베이어, 충전소, 문 | 이동 방향과 속도 단위 |
| `/World/Robots` | 이동로봇과 로봇팔 | Articulation Root, 관절, 초기 자세 |
| `/World/Sensors` | 고정 카메라와 감지기 | 시야, 좌표계, timestamp |
| `/World/Looks` | 공통 재질 | 텍스처 경로와 렌더 결과 |

이 이름은 과정에서 사용하는 설계 예이다. NVIDIA asset을 가져왔다는 이유만으로 내부 Prim을 일괄 변경하지 않는다. 센서·컨트롤러·그래프가 참조하는 경로까지 함께 바뀔 수 있다.

먼저 작은 환경에서 다음 순서로 구성한다.

1. 바닥 하나와 선반 하나를 배치하고 미터 단위가 맞는지 확인한다.
2. 바닥과 선반에 정적 충돌 형상을 설정한다. 정적 선반을 불필요하게 강체로 만들지 않는다.
3. 작은 큐브를 떨어뜨려 바닥과 선반을 통과하지 않는지 확인한다.
4. 조명을 추가하고 카메라 한 대에서 실제 RGB와 깊이를 확인한다.
5. 검증한 로봇 한 대를 추가하고 정지 상태를 먼저 확인한다.
6. 이동 명령, 작업 로직, 추가 센서 순서로 확장한다.

창고를 크게 만든 다음 로봇이 무너지는 원인을 찾기보다 위 순서로 기능을 추가할 때마다 결과를 남긴다. [Digital Twin](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/index.html)

## 2. Warehouse Creator와 컨베이어 도구 사용하기

Warehouse Creator는 창고 배치를 만드는 도구이다. Conveyor Belt Utility는 컨베이어 표면의 이동을 설정하는 도구이다. 생성 도구를 사용해도 충돌 형상, 물체의 초기 위치와 마찰을 확인해야 한다. [Warehouse Creator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_omni_warehouse_creator.html), [Conveyor Belt Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/ext_isaacsim_asset_gen_conveyor.html)

컨베이어는 먼저 작은 상자 하나로 시험한다. 상자 중심 높이를 벨트 표면 높이 + 상자 높이의 절반 + 작은 여유로 지정한다. 초기부터 상자를 벨트 안에 묻어 두지 않는다. 벨트 방향을 바꾼 뒤에는 물체가 실제로 어느 축으로 움직이는지 확인한다.

```python
belt_surface_z = 0.75
box_height = 0.20
clearance = 0.01
spawn_z = belt_surface_z + box_height / 2 + clearance
print("box center z:", spawn_z)  # 0.86 m
```

벨트 속도가 0.2 m/s일 때 물체가 반드시 1초 후 정확히 0.2 m 이동하는 것은 아니다. 접촉 상태와 마찰에 따라 미끄러질 수 있다. 먼저 이동 방향, 벨트 밖 이탈, 관통이 없는지 확인하고 정착 후 이동 속도를 측정한다.

## 3. Cortex가 맡는 일

Cortex는 센서나 로봇 모델 자체가 아니라 **로봇의 행동을 구성하는 프레임워크**이다. 관측한 상태를 정리하는 monitor, 다음 행동을 고르는 decider, 행동을 실행하는 상태/명령 계층을 연결한다.

| 계층 | 예 |
| --- | --- |
| 상태 갱신 | 상자가 도착했는지, 집기가 성공했는지 확인 |
| 행동 선택 | 대기, 집기, 뒤집기, 쌓기 중 선택 |
| 동작 수행 | 목표 자세 전송, 그리퍼 조작, 완료 조건 검사 |
| 물리 실행 | 관절 구동과 접촉 계산 |

`DfNetwork`는 전체 행동 구조를 담고, `DfDecider.decide()`는 자식 행동을 선택한다. `enter()`와 `exit()`는 같은 행동을 계속 실행할 때 매번 호출되는 함수가 아니라 해당 행동으로 들어가거나 나갈 때 호출된다. [Decider Networks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_2_decider_networks.html)

## 4. 설치본의 공식 예제를 실행하기

다음은 Isaac Sim 5.1.0 Workstation 설치본에 포함된 예제 경로이다. 먼저 파일이 있는지 확인한다.

```bash
export CORTEX_EXAMPLES="$ISAACSIM_PATH/standalone_examples/api/isaacsim.cortex.framework"
rg --files "$CORTEX_EXAMPLES" -g '*main.py'
```

폴더가 없다면 다른 버전의 파일을 임의로 섞지 말고 설치 방식과 5.1.0 예제 포함 여부를 확인한다. 정상적으로 파일이 있으면 다음을 실행한다.

```bash
cd "$CORTEX_EXAMPLES"
"$ISAACSIM_PATH/python.sh" follow_example_main.py
```

1. 앱과 로봇 asset이 모두 로딩될 때까지 기다린다.
2. Play를 누른다. 이 예제는 앱이 열렸다는 이유만으로 자동 재생되지 않는다.
3. 로봇 말단 근처의 구를 선택한다.
4. Move 도구로 구를 조금 이동한다. 로봇팔이 목표를 따라가는지 확인한다.
5. 처음에는 도달 가능한 근처 목표만 사용한다. 바닥이나 로봇 몸체 안으로 목표를 넣지 않는다.
6. Stop 후 앱을 닫고 다음 예제로 진행한다.

목표가 움직이는 것과 로봇이 목표에 도달하는 것은 다르다. 실제 말단 위치와 목표 위치의 차이를 확인해야 한다.

```python
import numpy as np

actual_position = np.array([0.40, 0.10, 0.50])
target_position = np.array([0.405, 0.10, 0.50])
error_m = float(np.linalg.norm(target_position - actual_position))
print("error_m:", error_m)
print("reached:", error_m < 0.01)
```

위 코드는 오차 계산만 확인하는 독립 예제이다. 로봇 제어 코드에서는 실제 API로 읽은 말단 위치와 목표 위치를 넣는다. 화면에서 비슷해 보인다는 이유로 성공 판정을 하지 않는다.

## 5. 고정 절차와 반응형 행동 비교하기

다음 두 실행을 하나씩 비교한다.

```bash
"$ISAACSIM_PATH/python.sh" franka_examples_main.py --behavior=peck_state_machine
```

```bash
"$ISAACSIM_PATH/python.sh" franka_examples_main.py --behavior=peck_decider_network
```

두 예제 모두 Play 후 로봇이 물체를 피해 목표로 움직인다. 공식 실습은 이동 중인 목표 근처로 블록을 옮겼을 때 고정된 절차가 목표를 고집하는 경우와, decider가 다른 행동을 선택하는 경우를 비교한다. 처음에는 정상 경로를 관찰하고, 이후 블록 이동으로 상태 변화에 대한 반응을 확인한다. [Peck Games](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_3_example_peck_games.html)

자신의 프로젝트에서는 어떤 조건이 다른 조건보다 우선인지 먼저 독립 함수로 정리할 수 있다.

```python
def choose_next_action(*, fault, timed_out, holding_box, box_ready):
    if fault:
        return "stop"
    if timed_out:
        return "recover"
    if holding_box:
        return "place"
    if box_ready:
        return "pick"
    return "wait"

cases = [
    dict(fault=False, timed_out=False, holding_box=False, box_ready=False),
    dict(fault=False, timed_out=False, holding_box=False, box_ready=True),
    dict(fault=False, timed_out=False, holding_box=True, box_ready=True),
    dict(fault=False, timed_out=True, holding_box=True, box_ready=True),
    dict(fault=True, timed_out=True, holding_box=True, box_ready=True),
]
for case in cases:
    print(case, "->", choose_next_action(**case))
```

예상 순서는 `wait`, `pick`, `place`, `recover`, `stop`이다. 이 함수는 로봇을 움직이지 않는다. 조건의 우선순위를 확인한 다음 공식 예제의 `DfDecision`과 자식 행동에 대응시킨다. timeout은 시뮬레이션 시간으로 계산하고, Stop/reset 뒤 이전 작업의 시작 시간이 남지 않도록 초기화한다.

## 6. UR10 컨베이어 작업으로 확장하기

```bash
cd "$CORTEX_EXAMPLES"
"$ISAACSIM_PATH/python.sh" demo_ur10_conveyor_main.py
```

로딩 후 Play를 누르면 컨베이어, UR10, 흡착 그리퍼, 팔레트가 있는 작업이 실행된다. 공식 예제는 상자의 방향에 따라 뒤집기 과정을 거쳐 팔레트에 쌓는다. 먼저 기본 장면의 동작을 확인한 뒤 컨베이어 속도나 물체 간격을 한 항목씩 바꾼다. [UR10 Bin Stacking](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking.html)

다음 항목을 작업마다 기록한다.

| 항목 | 의미 |
| --- | --- |
| 작업 ID | 어떤 상자와 시도인지 구분 |
| 시작/완료 시뮬레이션 시간 | Pause와 실제 실행 시간 구분 |
| 집기 성공 여부 | 그리퍼 명령 전송과 실제 부착을 구분 |
| 최종 위치 오차 | 팔레트의 목표 위치와 비교 |
| 실패 사유 | timeout, 물체 이탈, 부착 실패 등 |
| 환경/정책 버전 | 나중에 같은 조건으로 재현 |

작업이 멈췄을 때 로봇 관절의 수치가 정상인지, 목표가 도달 가능한지, 행동 선택 조건이 바뀌었는지 순서대로 확인한다. “무너졌다”는 시각적 표현만으로 제어기 오류와 충돌 형상 오류를 같은 원인으로 묶지 않는다.

## 7. 전용 앱으로 묶을 때

환경 USD, 필요한 Extension, 시작 설정이 정리되면 Application Template으로 전용 앱을 구성할 수 있다. 처음에는 [앞 장의 작은 Extension](02-extension-and-omnigraph.md)으로 UI와 수명 주기를 검증한다. 이후 앱의 experience 설정과 Extension 의존성, asset 경로를 함께 버전 관리한다. [Application Template](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/app_template/index.html)

여러 이동로봇의 경로 최적화는 cuOpt 같은 별도 도구와 연결할 수 있다. Isaac Sim이 센서와 로봇 실행을 담당한다고 실제 운영 시스템의 작업 배정과 경로 최적화까지 자동으로 완성되는 것은 아니다. 각 도구가 주고받을 좌표계, 작업 ID와 실패 응답을 정한다.

이 장의 완료 기준은 공식 예제 실행, 목표 추종 확인, 조건 변화에 따른 행동 전환 확인, 성공·실패 기록이다. 설치본의 asset 다운로드와 RTX/PhysX 런타임이 필요한 실습이며, 이 저장소의 문법 검사만으로 실제 동작을 검증했다고 간주하지 않는다.

## 출처

- [Digital Twin](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/index.html)
- [Cortex Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_1_overview.html)
- [Decider Networks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_2_decider_networks.html)
- [Peck Games](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_3_example_peck_games.html)
- [UR10 Bin Stacking](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking.html)
- [Building Cortex Based Extensions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_7_cortex_extension.html)
- [Application Template](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/app_template/index.html)
