# 98. 손끝 목표와 팔의 자세 선호를 따로 명령하기

## 이번에 배우는 것

**Franka의 손끝 목표는 유지하면서 팔 자세와 그리퍼를 바꾸고, Cortex가 목표를 실제 운동으로 연결하는 과정을 살펴봅니다.**

손끝을 한 점으로 옮기려면 관절 각도를 모두 직접 계산해야 할까요? 이번 코드는 손끝의 목표 위치와 선호하는 팔 자세를 전달합니다. 이후의 운동 생성은 arm commander가 맡습니다.

팔을 뻗은 채 팔꿈치 위치를 바꿀 수 있는 것처럼, 같은 손끝 목표에 접근하는 팔 자세는 여럿일 수 있습니다. 이 여유를 활용하는 설정이 `posture_config`입니다.

| 코드의 값 또는 객체 | 역할 | 관찰할 내용 |
|---|---|---|
| `target_p` | 손끝 목표 위치, m | `(0.7, 0, 0.5)`로 고정 |
| `posture_config` | 팔 관절 7개의 자세 선호 | 상태에 들어갈 때마다 다시 샘플링 |
| `robot.arm` | 손끝 명령 처리 | 목표에 접근하는 팔 운동 |
| `robot.gripper` | 손가락 명령 처리 | 열기와 닫기 반복 |
| `NullspaceShiftState` | 명령과 전환 조건 정의 | 실제 시간 약 2초 뒤 다시 진입 |

## 1. 같은 손끝 목표를 반복해서 명령하기

Isaac Sim 5.1, 지원 NVIDIA RTX GPU와 Franka 샘플 자산 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/98_digital_twin_cortex_1_overview/run.py
```

Franka와 지면이 생성되고 자동으로 재생합니다. 몇 차례 자세가 바뀌는 모습을 본 뒤 창을 닫으세요. 단계 수로 끝내려면 `--steps 1800`을 추가합니다. `--headless`는 창 없이 실행하며 단계 생략 시 1800단계로 종료합니다. `--interactive`는 창에서 Play를 누를 때까지 기다리는 옵션이며 `--headless`와 함께 쓸 수 없습니다.

### 코드에서 볼 부분

`enter()`는 상태에 들어올 때 한 번 실행됩니다.

```python
posture_config = self.config_mean + np.random.randn(7)
self.context.robot.arm.send_end_effector(
    target_position=self.target_p, posture_config=posture_config
)
```

`config_mean`은 팔 관절 7개의 기준 각도입니다. `np.random.randn(7)`을 더해 새로운 자세 선호를 만들지만, 손끝 목표 `self.target_p`는 바꾸지 않습니다.

**`posture_config`는 최종 관절각을 그대로 고정하는 명령이 아닙니다.** 같은 손끝 목표로 가는 운동에서 어떤 관절 자세를 선호할지 알려 주는 값입니다. 따라서 입력한 각도 배열과 실제 관절각이 정확히 일치해야 하는 것은 아닙니다.

그리퍼는 별도 명령을 받습니다.

```python
if gripper.get_width() > 0.05:
    gripper.close(speed=0.5)
else:
    gripper.open(speed=0.1)
```

현재 폭이 5 cm보다 넓으면 닫고, 그렇지 않으면 엽니다. 닫는 속도와 여는 속도도 따로 지정되어 있습니다. 팔의 목표를 바꾸는 명령 안에 손가락 동작이 자동으로 포함되는 것은 아닙니다.

### 실행 결과 확인하기

Stage의 `/World/franka`와 콘솔의 `<enter> sampling posture config`를 함께 봅니다.

- 새 로그가 나올 때 팔의 구부러진 모양이 바뀌는지 확인하세요.
- 손끝은 같은 `(0.7, 0, 0.5)` m 주변을 향하는지 봅니다.
- 손가락은 현재 폭에 따라 열기 또는 닫기 명령에 반응하는지 확인합니다.

난수 때문에 실행마다 팔 모양은 달라질 수 있습니다. 이 예제는 위치 오차를 CSV로 저장하지 않으므로, 로그만으로 정밀한 제어 오차가 검증되었다고 판단하지 않습니다.

## 2. 상태를 반복시키는 Cortex 흐름 읽기

`main()`에서는 한 상태를 반복하는 시퀀스를 네트워크에 넣습니다.

```python
DfStateMachineDecider(
    DfStateSequence([NullspaceShiftState()], loop=True)
)
```

`DfStateSequence`는 상태를 순서대로 수행합니다. 여기에는 상태가 하나뿐이지만 `loop=True`이므로 완료되면 다시 처음으로 돌아갑니다. `DfStateMachineDecider`는 이 상태 기계를 Cortex의 의사 결정 네트워크에 연결하는 역할입니다.

### 코드에서 볼 부분

상태의 전환 조건은 다음과 같습니다.

```python
def step(self):
    if time.time() - self.entry_time < 2.0:
        return self
    return None
```

`self`는 현재 상태를 계속 수행한다는 뜻이고, `None`은 상태가 끝났다는 뜻입니다. 완료 후 다시 `enter()`에 들어가므로 자세를 새로 뽑고 그리퍼 폭을 다시 판단합니다.

여기의 `time.time()`은 **컴퓨터의 실제 시계**입니다. 물리 시간이 2초 진행되어야 전환한다는 의미가 아닙니다. 느린 렌더링이나 일시정지가 있으면 상태 사이에 진행한 물리 단계 수는 달라질 수 있습니다.

`CortexWorld`는 논리 상태 모니터, 행동 판단, 로봇 commander를 순서대로 처리하고 물리를 진행합니다. 이번 context는 별도 논리 관찰값이 필요 없는 `DfBasicContext`이며, 상태에서 로봇의 command API에 접근할 수 있도록 연결합니다.

## 3. 목표·판단·제어의 역할 정리

```text
상태 진입 → 손끝 목표와 자세 선호 전달
           → 그리퍼 폭을 보고 열기/닫기 전달
CortexWorld → commander가 명령 처리 → 물리 운동
실제 시간 약 2초 경과 → 상태 완료 → 새 자세로 다시 진입
```

공식 Cortex 개요는 관측, USD에 표현한 세계 상태, 논리 상태, 판단, 명령, 제어를 연결합니다. 이번 실습은 그중 **판단에서 command API로 목표를 전달하는 부분**을 작게 떼어 봅니다. 카메라 인식이나 실제 로봇 동기화는 구성하지 않습니다.

## 4. 간단한 확인 실험

`run.py`의 `self.target_p`에서 **Z만 `0.5`에서 `0.6`으로** 바꾸고 다시 실행해 보세요. 기준 자세와 난수 생성, 그리퍼 속도는 유지합니다.

손끝이 향하는 높이가 10 cm 높아지는지 보세요. 매번 다른 자세를 샘플링하므로 팔꿈치 모양 하나를 비교하기보다, 여러 상태에서 손끝이 향하는 공통 위치를 비교하는 편이 좋습니다. 실험을 마치면 Z를 0.5로 되돌립니다.

## 실행할 때 막히면

- **`No module named isaacsim`**: 일반 Python이 아니라 Isaac Sim의 `python.sh`로 실행하세요.
- **로봇은 보이는데 움직이지 않음**: `--interactive`로 시작했다면 Play를 누르세요. Franka 자산 로딩이 끝났는지도 확인합니다.
- **새 자세가 한 번만 보이고 종료됨**: 너무 작은 `--steps`를 지정했을 수 있습니다. 여러 실제 시간 전환을 관찰할 수 있도록 단계 제한을 빼세요.
- **목표를 크게 바꾼 뒤 도달하지 못함**: 작업 영역을 벗어난 목표일 수 있습니다. 원래 좌표로 돌아와 자세 선호와 위치 목표를 하나씩 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Isaac Cortex: Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_1_overview.html)에 대응합니다. `run.py`는 NVIDIA command API 예제에 실행 옵션과 종료 조건을 더한 코드이며, 출처와 라이선스는 `NOTICE.md`, `LICENSE-NVIDIA-EXAMPLES`에 있습니다.

손끝 목표 유지, 자세 변화, 그리퍼 반응은 실제 운동에서 확인할 기준입니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
