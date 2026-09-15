# 102. 흡착한 상자를 뒤집을지 바로 쌓을지 판단하기

## 이번에 배우는 것

**UR10이 공급된 상자를 흡착해 옮기는 과정을 관찰하고, 부착 여부와 방향 판단이 집기·뒤집기·적재로 연결되는 구조를 읽습니다.**

집을 물체가 항상 같은 방향으로 들어온다면 정해진 이동을 반복할 수 있습니다. 이번 상자(bin)는 위치와 방향이 달라집니다. 목표는 **상자의 열린 쪽이 아래를 향하도록 적재하는 것**입니다. 위로 열린 상태로 들어온 상자는 먼저 집어 flip station에서 뒤집은 뒤 팔레트의 다음 자리에 놓습니다.

| 구성 | 파일 또는 위치 | 역할 |
|---|---|---|
| 장면·공급 task | `run.py` | 작업대, UR10, 새 bin 생성 |
| 의사 결정 | `bin_stacking_behavior.py` | 집기·뒤집기·놓기 선택 |
| 로봇 | `/World/Ur10Table/ur10` | 팔과 suction gripper |
| 공급 물체 | `/World/Ur10Table/bins/bin_0`부터 | 작업 영역에 들어올 상자 |
| 적재 좌표 | 3 × 3 위치, 4층 | 총 36개 목표 자리 |

여기의 흡착 상태는 논리 판단과 실제 물리 운동을 함께 봐야 합니다. 콘솔에 `is_attached=True`가 나와도 상자가 손끝과 함께 올라오는지 확인하세요.

## 1. 상자 공급과 적재 장면 실행하기

Isaac Sim 5.1과 지원 NVIDIA RTX GPU가 필요합니다. 다음 5.1 자산에 접근할 수 있어야 합니다.

- `Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_short_suction.usd`
- `Isaac/Props/KLT_Bin/small_KLT.usd`
- `Isaac/Environments/Simple_Warehouse/warehouse.usd`

저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/102_digital_twin_cortex_5_ur10_bin_stacking/run.py --interactive
```

장면이 로드되면 Play를 누르고 첫 bin이 작업 영역으로 들어오는 것을 기다립니다. `--interactive`를 빼면 자동 Play합니다. 창을 닫으면 종료하고, `--steps 1800`을 추가하면 해당 물리 단계에서 끝납니다. `--headless`의 기본 한도도 1800단계이며 36개 적재 완료를 뜻하지 않습니다.

### 코드에서 볼 부분

새 bin은 다음 초기 위치와 속도를 받습니다.

```python
x = random.uniform(-0.15, 0.15)
y = 1.5
z = -0.15
```

```python
rigid_bin.set_linear_velocity(np.array([0, -0.30, 0]))
```

X는 좌우로 분산되고, Y가 줄어드는 방향으로 공급됩니다. 작업대 자산의 기준 위치에 맞춘 장면이므로 Z=-0.15라는 이유만으로 물체가 바닥을 뚫었다고 해석하지 마세요.

behavior가 활성 bin을 고르는 영역은 `-0.4 < x < 0.4`, `0 < y < 0.7`입니다. 출발 Y=1.5에서는 아직 그 영역 밖이므로 처음의 `<no active bin>`은 자연스러운 대기 상태입니다.

공급 task는 현재 bin이 공급 영역을 벗어나면 다음 bin을 만듭니다. “앞 상자가 팔레트에 완전히 안착했는지”를 검사하는 조건은 아닙니다. 공급과 적재 판단을 별도로 읽어야 합니다.

### 실행 결과 확인하기

콘솔의 다음 항목을 같은 이름의 bin과 대응시켜 보세요.

| 출력 | 의미 | 함께 볼 화면 |
|---|---|---|
| `bin_obj.name` | 현재 작업 대상 | 팔이 향하는 bin |
| `is_grasp_reached` | 손끝이 잡을 자세에 가까운지 | 흡착면과 손끝의 정렬 |
| `is_attached` | 가까운 자세와 gripper 닫힘을 조합한 판단 | bin이 함께 들리는지 |
| `needs_flip` | 현재 기준에서 뒤집기가 필요한지 | flip station을 거치는지 |

초기 방향은 무작위이므로 짧은 실행에 뒤집기와 직접 적재가 모두 나오지 않을 수 있습니다. 그리퍼를 연 뒤에는 bin이 목표 자리에 남아 지지되는지 관찰합니다.

## 2. 집기·뒤집기·놓기의 분기 읽기

`Dispatch.decide()`는 현재 상태를 다음 순서로 해석합니다.

```text
적재 완료 → home
활성 bin 없음 → home
활성 bin이 아직 부착되지 않음 → pick_bin
부착되었고 needs_flip → flip_bin
부착되었고 뒤집기 불필요 → place_bin
```

뒤집기 후에는 물체를 놓았다가 다시 집어야 하므로, flip이 끝났다고 바로 place로 고정 전환하지 않습니다. 모니터가 현재 부착과 방향 상태를 다시 읽습니다.

### 코드에서 볼 부분

`monitor_active_bin_grasp_reached()`의 부착 판단은 다음 두 조건을 묶습니다.

```python
self.active_bin.is_attached = (
    math_util.transforms_are_close(
        self.active_bin.grasp_T, fk_T, p_thresh=0.1, R_thresh=1.0
    )
    and self.robot.suction_gripper.is_closed()
)
```

`grasp_T`는 bin의 흡착면을 기준으로 만든 목표 자세이고 `fk_T`는 현재 손끝 자세입니다. 엄격한 잡기 도달 판정에는 더 작은 위치 임계값 0.01 m를 쓰고, 부착 추정에는 0.1 m를 사용합니다. 두 값이 다르므로 `is_grasp_reached`와 `is_attached`가 항상 같은 값일 필요는 없습니다.

적재 위치는 `stack_coordinates`에 층 → 행 → 열 순서로 담깁니다. 다음 위치의 인덱스는 완료 목록 길이입니다. `PlaceBin`은 놓기 접근, 대기, 잠금, 흡착 해제, lift, 완료 목록 기록, 잠금 해제 순으로 진행합니다. 목록이 36개가 되면 논리상 완료입니다. 이 목록만으로 각 층의 실제 지지 상태까지 검사하지는 않습니다.

위층에 놓을 때는 아래 bin과 XY 오차도 봅니다.

```python
if np.linalg.norm(xy_err) < 0.02:
    self.target_p[:2] += 0.1 * (bin_under_p[:2] - bin_grasped_p[:2])
```

오차가 2 cm 미만인 가까운 정렬 상태에서 그 오차의 10%를 목표에 반영합니다. 큰 오차를 한 번에 순간 이동으로 없애는 방식이 아니라 접근 목표를 조금씩 조정합니다.

### 실행 결과 확인하기

Stage의 `/World/Ur10Table/Obstacles`에는 숨겨진 구와 캡슐 네 개가 있습니다. 잠시 visibility를 켜면 이동 중 피하려는 영역을 볼 수 있습니다. 표시 여부와 동작 생성기의 장애물 활성 여부는 별개입니다.

flip station에 접근해야 하는 순간에는 해당 영역을 계속 피하면 작업을 수행할 수 없습니다. `FlipStationObstacleMonitor`와 `NavigationObstacleMonitor`가 손끝·목표 관계에 따라 필요한 회피 영역을 바꿉니다. 잠금 구간에서는 잡기와 놓기가 중간에 다른 행동으로 바뀌지 않도록 보호합니다.

## 3. 공급부터 적재까지 정리

```text
무작위 위치·방향으로 공급 → 작업 영역에서 활성 bin 선택
    → 흡착 자세 접근 → 부착 확인
    → 필요하면 flip station에서 해제하고 재집기
    → 다음 적재 좌표 접근 → 해제·상승 → 완료 목록 갱신
```

방향 분기와 부착 판단은 같은 것이 아닙니다. `needs_flip`이 맞아도 실제 흡착이 이루어지지 않으면 적재할 수 없습니다. 출력값은 로봇이 무엇을 믿고 판단하는지 알려 주고, 화면은 그 판단이 물리 결과와 맞는지 보여 줍니다.

## 4. 간단한 확인 실험

`run.py`의 `random_bin_spawn_transform()`에서 **X 범위만 `(-0.15, 0.15)`에서 `(-0.05, 0.05)`로** 좁혀 보세요.

초기 bin 위치의 좌우 분산이 줄어들어 첫 집기 위치가 더 가운데에 모여야 합니다. 공급 속도, 방향 난수, 뒤집기 조건은 그대로이므로 모든 bin이 같은 자세로 들어오지는 않습니다. 여러 공급을 비교한 뒤 원래 범위로 복구하세요.

## 실행할 때 막히면

- **UR10이나 작업대 일부가 없음**: 먼저 세 USD 자산 로딩을 확인하세요. 로봇 없는 장면에서 행동 로그만 관찰하면 원인을 구분하기 어렵습니다.
- **`<no active bin>`이 계속됨**: bin이 생성되었는지와 실제 XY가 활성 영역으로 들어오는지 확인하세요. 공급 task와 활성 선택 조건을 각각 봅니다.
- **닫힘 로그 후 bin이 들리지 않음**: 손끝의 흡착 위치·방향과 bin 충돌 형상을 확인하세요. 콘솔 부착 추정만으로 성공을 판단하지 않습니다.
- **36개 뒤에도 앱이 계속 실행됨**: behavior는 home을 선택하지만 공급 task와 앱 종료를 연결하지 않습니다. 관찰 후 창을 닫으세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Walkthrough: UR10 Bin Stacking](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking.html)에 대응합니다. NVIDIA 장면 실행 예제와 behavior를 로컬에서 연결하며, 출처와 라이선스는 `NOTICE.md`, `LICENSE-NVIDIA-EXAMPLES`에 있습니다.

부착 판단과 실제 흡착·적재를 함께 확인하세요. `tutorial.json`의 검증 상태는 `not_run`이며 36개 완료 목록이 실제 네 층의 지지를 자동 검사하지는 않습니다.
