# 164. 속도 명령을 받은 Spot과 H1의 움직임 읽기

## 이번에 배우는 것

**설치된 보행 정책에 전진·회전·정지 명령을 보내고, 목표 속도와 실제 몸통 위치를 나란히 기록합니다.**

정책은 로봇 상태와 원하는 속도를 받아 관절 목표를 계산하는 학습된 함수입니다. 속도 명령을 줬다고 로봇이 즉시 그 속도로 움직이는 것은 아닙니다. 관절 제어와 지면 접촉을 거친 실제 결과를 확인해야 합니다. 이번에는 정해진 6초 명령 순서를 사용해 입력과 이동을 비교합니다.

| 항목 | Spot | H1 |
|---|---|---|
| 선택 옵션 | `--robot spot` | `--robot h1` |
| 물리 간격 | 0.002초, 500 Hz | 0.005초, 200 Hz |
| 한 명령 주기 | 6초 | 6초 |
| 한 주기 관찰 단계 수 | 3000회 | 1200회 |
| 사용 클래스 | `SpotFlatTerrainPolicy` | `H1FlatTerrainPolicy` |

이 코드는 새 정책을 학습하지 않습니다. 실제 로봇 USD와 학습된 정책 자산을 불러와 추론합니다.

## 1. Spot의 6초 명령 순서 실행하기

Isaac Sim 5.1, RTX GPU, 5.1 로봇·정책 자산 접근이 필요합니다. 설치된 확장 이름은 `isaacsim.robot.policy.examples`입니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/164_motion_robot_policy_example/run.py --robot spot --steps 3000 --output src/164_motion_robot_policy_example/output/spot_01.csv
```

3000번의 물리 진행 후 종료합니다. GUI에서도 물리는 `world.step(render=False)`로 한 단계씩 진행하고, 약 0.02초 간격의 별도 `world.render()`는 물리 진행을 잠시 끈 상태에서 화면만 갱신합니다. 따라서 이 실행기의 3000스텝은 Spot의 6초 물리 구간과 대응합니다. `--steps`를 빼면 창을 닫을 때까지 같은 명령 순서를 반복합니다. `--headless`를 추가하면 창 없이 실행합니다. Headless의 생략 기본값은 2000스텝이므로 Spot에서는 4초만 진행되어 정지 구간을 관찰하기 부족합니다.

CSV는 실행 중 작성하며 기존 파일은 덮어쓰지 않습니다. 재실행할 때는 새 `--output` 파일을 지정하세요.

### 코드에서 볼 부분

```python
phase = int(step * dt / 2) % 3
command[:] = [(0.4, 0, 0), (0.3, 0, 0.4), (0, 0, 0)][phase]
world.step(render=False)
```

`step * dt`로 계산한 시뮬레이션 시간마다 명령을 고릅니다. 세 값은 몸체 좌표계의 전진 속도, 측면 속도, 회전 속도입니다.

| 구간 | 명령 `(vx, vy, yaw)` | 관찰할 변화 |
|---|---|---|
| 0~2초 | `(0.4, 0, 0)` | 몸체 전방 이동 |
| 2~4초 | `(0.3, 0, 0.4)` | 전진하면서 방향 전환 |
| 4~6초 | `(0, 0, 0)` | 이동 감소·정지 자세 |

선속도는 m/s, 회전 속도는 rad/s입니다. 몸체가 회전한 뒤 전진하면 월드 +X만 따라가지 않을 수 있습니다. 명령의 기준 좌표계와 기록 위치의 기준 좌표계가 다르기 때문입니다.

### 실행 결과 확인하기

CSV는 약 0.1초 간격으로 로봇마다 한 행을 씁니다.

| 열 | 의미 |
|---|---|
| `time_s` | 반복문 인덱스에서 계산한 명령 시각 |
| `robot` | 로봇 번호 |
| `vx_command`, `vy_command`, `yaw_command` | 정책에 전달한 목표 속도 |
| `x`, `y`, `z` | 물리 진행 후 읽은 월드 위치(m) |

`time_s`는 물리 진행 전 `step * dt`이고 위치는 해당 단계 후 읽습니다. 매우 짧은 구간을 분석할 때는 이 한 단계 차이도 고려하세요. 일반적인 이동 비교에서는 연속 행의 위치 변화와 명령 구간을 함께 봅니다.

몸통의 Z와 화면도 확인하세요. 넘어져 미끄러지는 로봇도 X가 변할 수 있으므로 이동 거리만으로 정상 보행을 판단하지 않습니다. 정지 명령 뒤에도 관성이나 자세 보정 때문에 즉시 완전히 정지하지 않을 수 있습니다.

## 2. H1과 여러 로봇의 정책 상태 비교하기

H1의 한 주기도 실행해 보세요.

```bash
~/isaacsim/python.sh src/164_motion_robot_policy_example/run.py --robot h1 --steps 1200 --output src/164_motion_robot_policy_example/output/h1_01.csv
```

### 코드에서 볼 부분

첫 물리 콜백에서는 초기화만 수행하고 다음 콜백부터 정책을 진행합니다.

```python
if not initialized:
    for robot in robots:
        robot.initialize()
    initialized = True
else:
    for robot in robots:
        robot.forward(step_size, command)
```

`initialize()`는 물리가 준비된 뒤 관절 제어를 초기화합니다. `forward()`는 물리 콜백마다 관절 목표를 적용하지만 신경망 추론은 정책의 `decimation` 간격에 수행하고 그 사이에는 이전 행동을 유지합니다. 설치된 Spot은 48개 관측에서 12개 행동을, H1은 69개 관측에서 19개 행동을 계산합니다. 두 클래스 모두 기준 관절 위치에 행동을 더한 위치 목표를 사용하며 행동 배율은 Spot 0.2, H1 0.5입니다. 로봇 종류만 바꾸는 것은 같은 신경망에 다른 모양을 씌우는 일이 아닙니다. `world.step()`이 이 콜백을 실행시키므로 콜백 등록만으로 로봇이 계속 움직이는 것은 아닙니다.

`--robots 3`을 주면 `/World/Robot_0`부터 세 로봇을 Y 방향 2 m 간격으로 만듭니다. 각 로봇에 별도의 정책 객체와 articulation이 생깁니다. 같은 속도 명령을 받지만 이전 행동 등 정책 내부 상태는 각 객체에 보관됩니다.

### GUI 예제로 넓혀 보기

새 Isaac Sim 창에서 **Window > Examples > Robotics Examples > POLICY**를 열면 관련 공식 예제도 비교할 수 있습니다.

- **Humanoid > LOAD**: H1의 위 화살표는 전진, 좌우 화살표는 회전입니다.
- **Quadruped > LOAD**: Spot의 좌우 화살표는 측면 이동이며 회전은 `N`, `M`입니다.
- **Franka > LOAD**: 손잡이 접근과 서랍 열기를 관찰하고 RESET 후 다시 확인합니다.

서로 다른 예제로 바꿀 때는 새 Stage를 사용하세요. 이 폴더의 CSV 실행기는 Spot/H1만 지원합니다. Franka의 팔 과제와 ANYmal의 지형 보행은 별도 설치본 예제입니다. ANYmal은 설치 디렉터리에서 다음과 같이 실행합니다.

```bash
cd ~/isaacsim
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/anymal_standalone.py
```

같은 설치 폴더에는 H1과 Spot 원본 standalone도 있습니다. 각각 종료한 뒤 다음 예제를 실행하세요.

```bash
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/h1_standalone.py --num-robots 5 --env-url /Isaac/Environments/Grid/default_environment.usd
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/spot_standalone.py
```

원본 H1의 `--num-robots`와 이 폴더 실행기의 `--robots`는 서로 다른 옵션입니다. 원본 예제는 키보드 조작을, 로컬 실행기는 6초 시간표와 CSV 기록을 비교하는 데 사용합니다. 원본 standalone은 창을 닫아 종료합니다. 이 거친 지형 예제를 정책 파일 표의 ANYmal flat 정책과 같은 실험으로 취급하지 않습니다.

## 3. 명령·정책·실제 상태 정리

```text
시간표의 속도 명령
    → 현재 로봇 상태와 함께 정책 입력
    → 관절 목표 계산·적용
    → 물리 계산과 지면 접촉
    → 실제 몸통 위치 기록
```

CSV의 명령은 입력이고 위치는 결과입니다. 예를 들어 전진 명령 0.4 m/s를 2초 주었더라도 위치 차이가 정확히 0.8 m여야 하는 것은 아닙니다. 시작 자세와 추종 오차를 포함한 실제 반응을 읽는 것이 목적입니다.

정책 자산은 5.1 Assets의 `/Isaac/Samples/Policies/Spot_Policies/`, `/Isaac/Samples/Policies/H1_Policies/`에 있습니다. 정책과 환경 YAML, 로봇의 관절 구성·제어 주기가 함께 맞아야 합니다.

## 4. 간단한 확인 실험

저장소 루트로 돌아와 H1 명령에서 `--robots 1`만 `--robots 3`으로 바꾸고 새 CSV에 기록해 보세요. 물리 단계 수와 로봇 종류는 유지합니다.

- 같은 `time_s`에 robot 0, 1, 2의 행이 있는지 확인합니다.
- 초기 Y가 약 2 m 간격인지 보고, 각 로봇의 위치 변화는 자기 초기 위치를 기준으로 비교합니다.
- 관절 상태가 독립인 세 로봇이 같은 입력에 어떻게 반응하는지 관찰합니다. 이 결과를 속도나 메모리 벤치마크로 해석하지 않습니다.

## 실행할 때 막히면

- **정책·로봇 로딩 실패**: 5.1 자산 루트와 위 정책 폴더에 접근할 수 있는지 확인하세요.
- **첫 화면에서 움직이지 않음**: 첫 콜백은 초기화입니다. 이후 물리 진행과 실제 CSV 행을 확인하세요.
- **Spot의 정지 구간이 없음**: 2000스텝은 4초입니다. `--steps 3000`으로 한 주기를 관찰하세요.
- **최종 pose 콘솔 출력이 없음**: GUI를 직접 닫으면 생략될 수 있습니다. 실행 중 기록한 CSV를 확인하세요.
- **넘어진 채 이동함**: 몸통 높이와 자세를 확인하고 로봇 종류에 맞는 물리 간격·관절 구성·정책 자산을 사용했는지 봅니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Reinforcement Learning Policies Examples in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html)에 대응합니다. 로컬 실행기는 설치본 Spot/H1 정책에 시간표를 전달하고 이동을 기록합니다. Franka와 ANYmal은 별도의 공식 실행 경로로 소개했습니다.

`tutorial.json`은 `not_run`입니다. 실제 보행, 서랍 열기, 지형 이동은 아직 이 패키지의 실행 검증으로 기록되지 않았습니다.
