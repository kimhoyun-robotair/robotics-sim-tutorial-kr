# 165. H1 정책의 입력 69개와 출력 19개는 무엇일까요?

## 이번에 배우는 것

**H1 정책이 실제로 받은 첫 관측과 마지막 행동을 기록하고, 학습된 정책을 옮길 때 맞춰야 할 입출력 조건을 이해합니다.**

정책 파일을 불러오는 것만으로 배포가 끝나지는 않습니다. 같은 숫자 19개라도 관절 순서가 다르면 무릎을 움직일 값이 팔에 전달될 수 있습니다. 이번에는 평평한 바닥과 일정한 전진 명령을 사용해 장면 복잡도보다 관측 배열·관절 순서·제어 주기에 집중합니다.

| 파일 | 담는 내용 | 확인하는 질문 |
|---|---|---|
| `trace.csv` | 단계별 몸통 위치와 속도 명령 | 로봇이 실제로 어떻게 움직였나요? |
| `contract.json` | 관절 이름, 관측, 행동, 제어 주기 | 정책이 기대한 형식과 맞나요? |
| 외부 `policy.pt` | 선택한 TorchScript 정책 | 어떤 학습된 함수를 실행하나요? |
| 외부 `env.yaml` | 선택한 환경·제어 설정 | 어떤 기본 자세와 주기를 사용하나요? |

기본 실행은 설치된 H1 정책을 사용합니다. 새 정책을 훈련하거나 다른 로봇의 관측 형식을 자동 변환하지 않습니다.

## 1. 기본 H1 정책 실행하기

Isaac Sim 5.1, RTX GPU와 드라이버, 5.1 H1 USD·정책 자산 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/165_motion_policy_deployment/run.py --speed 0.5 --steps 1200 --output src/165_motion_policy_deployment/output/base_01
```

1200번 물리를 진행한 뒤 종료합니다. 기본 H1 물리 간격 0.005초에서 6초입니다. 이 실행기는 `world.step(render=False)`로 물리를 한 단계 진행하고 GUI에서는 8단계마다 `world.render()`를 별도로 호출합니다. 화면 갱신 동안 추가 물리를 진행하지 않으므로 GUI 렌더 간격과 정책 시간 간격을 혼동하지 마세요. 외부 환경 파일을 선택했다면 전체 물리 시간은 `1200 × contract.json의 physics_dt`로 계산합니다. `--steps`를 빼면 창을 닫을 때까지 진행하고, `--headless`에서는 생략 시 1200스텝으로 제한합니다.

`trace.csv`는 실행 중, `contract.json`은 루프가 끝난 뒤 씁니다. 기존 두 결과 파일 중 하나라도 있으면 새 `--output` 폴더를 선택해야 합니다. 첫 추론 전에 창을 닫으면 trace만 남을 수 있습니다.

### 코드에서 볼 부분

실습의 `InspectedH1`은 관측 계산을 새로 구현하지 않고 설치된 H1 클래스의 결과를 복사합니다.

```python
observation = super()._compute_observation(command)
if self.first_observation is None:
    self.first_observation = observation.copy()
return observation
```

따라서 기록된 첫 관측은 실제 추론에 전달한 값입니다. 이후에는 물리 콜백의 `controller.forward(dt, command)`가 관측·추론·관절 목표 적용을 진행합니다. 첫 콜백은 `initialize()`에 사용하므로 첫 물리 단계부터 이미 정책이 계산되었다고 가정하지 않습니다.

### 실행 결과 확인하기

`trace.csv`의 `x_m`, `y_m`, `z_m`을 함께 읽으세요. `command_vx_m_s`는 목표 전진 속도이고 나머지 세 값은 실제 월드 위치입니다. `physics_step`은 0부터 시작하는 반복문 인덱스이며 각 행의 위치는 그 물리 진행 후 읽습니다.

H1이 몸통을 지지한 채 이동하는지 화면과 Z를 함께 확인합니다. X가 변해도 넘어진 로봇의 미끄러짐일 수 있습니다. `contract.json`의 다음 항목도 확인하세요.

- `joint_names`: 19개 관절 이름과 순서
- `first_observation`: 69개 입력값
- `last_action`: 19개 정책 출력
- `default_joint_positions`: 행동을 더할 기준 자세
- `physics_dt`, `decimation`, `policy_hz`: 물리와 추론의 주기

## 2. 관측 배열과 관절 목표 해석하기

### 코드에서 볼 부분

설치된 H1의 관측 배열은 다음 순서입니다.

| 슬라이스 | 개수 | 의미 |
|---|---|---|
| `[0:3]` | 3 | 몸체 좌표계 선속도(m/s) |
| `[3:6]` | 3 | 몸체 좌표계 각속도(rad/s) |
| `[6:9]` | 3 | 몸체에서 본 중력 방향 |
| `[9:12]` | 3 | 전진·측면·회전 명령 |
| `[12:31]` | 19 | 기준 자세 대비 관절 위치(rad) |
| `[31:50]` | 19 | 관절 속도(rad/s) |
| `[50:69]` | 19 | 이전 정책 행동 |

합은 `3 + 3 + 3 + 3 + 19 + 19 + 19 = 69`입니다. 기본 명령은 `[0.5, 0, 0]`이므로 관측의 `[9:12]`에서 그대로 확인할 수 있습니다. 중력 입력은 방향 벡터이며 `-9.81`이라는 가속도 크기 자체가 아닙니다.

관절 위치는 절대 각도가 아니라 `현재 위치 - default_pos`입니다. 예를 들어 기준 무릎 각도가 0.79 rad이고 현재도 0.79 rad라면 해당 관측은 0에 가깝습니다. 기준 자세의 의미를 바꾸면 같은 실제 자세도 다른 입력이 됩니다.

설치된 H1은 정책 출력을 다음 위치 목표로 바꿉니다.

```python
ArticulationAction(joint_positions=self.default_pos + self.action * 0.5)
```

`action=0.2`라면 해당 관절의 기준 위치에 0.1 rad를 더한 목표입니다. 이는 관절을 그 위치로 즉시 옮기는 명령이 아니라 관절 drive가 추종할 목표입니다. 위치 목표를 torque 값으로 그대로 사용해서는 안 됩니다.

### 실행 결과 확인하기

추론 빈도는 다음 관계로 읽습니다.

```text
policy_hz = 1 / (physics_dt × decimation)
```

물리가 0.005초 간격이고 decimation이 4이면 네 물리 단계마다 추론하므로 50 Hz입니다. 그 사이에는 마지막 행동을 유지합니다. 정확한 값은 실행 결과에 기록된 환경 설정을 따르세요. GUI 렌더 빈도는 이 계산과 별개입니다.

### 학습한 정책을 연결하는 경우

사용자 정책에는 같은 학습 실행에서 나온 TorchScript와 환경 YAML이 필요합니다. Isaac Lab에서 먼저 정책을 재생해 확인한 뒤 **같은 H1의 69입력·19출력과 action scale 0.5 조건**인 경우 다음처럼 전달합니다.

```bash
~/isaacsim/python.sh src/165_motion_policy_deployment/run.py --policy /절대경로/exported/policy.pt --environment /절대경로/params/env.yaml --steps 1200 --output src/165_motion_policy_deployment/output/custom_01
```

두 인수는 함께 지정해야 합니다. 실행기는 환경 파일의 dt를 읽지만 로봇 USD와 관측 구성, H1의 행동 배율은 유지합니다. 다른 로봇·관절 수·정규화 규칙을 가진 정책은 파일 경로 교체만으로 호환되지 않습니다.

정책 파일을 아직 만들지 않았다면 별도 Isaac Lab 환경이 필요합니다. 공식 5.1 문서가 제시하는 **Isaac Lab 2.0 기준** 예시는 다음과 같습니다. 다른 Lab 버전에서는 해당 버전의 task·export 절차를 확인하세요.

```bash
# Isaac Lab 작업 디렉터리에서 실행합니다.
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task Isaac-Velocity-Flat-H1-v0 --headless
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py --task Isaac-Velocity-Flat-H1-v0 --num_envs 32
```

학습 결과의 `logs/rsl_rl/<작업>/<실행시각>/params/env.yaml`과 play/export에서 만든 `exported/policy.pt`를 찾습니다. 같은 실행의 파일을 짝지어 Lab 재생 결과부터 확인하세요. `agent.yaml`은 학습 알고리즘·네트워크 설정이고, 이 실행기의 `--environment`에는 로봇·물리·제어 설정을 담은 `env.yaml`을 전달합니다. 이 폴더 자체에는 학습 실행기를 포함하지 않습니다. 관절 이름 순서, 기본 자세, gain·limit, 관측·행동 배율을 학습 설정과 대조한 뒤 연결하세요.

## 3. 정책 배포의 연결 조건 정리

```text
실제 로봇 상태
    → 학습 때와 같은 좌표계·관절 순서의 69개 관측
    → 정책의 19개 행동
    → 기준 자세 + 행동 배율
    → 관절 위치 목표
    → 물리·접촉 → 다음 상태
```

파일 로딩 성공은 가운데 신경망을 읽었다는 뜻입니다. 그 앞의 관측과 뒤의 제어가 맞아야 로봇 행동으로 이어집니다. `contract.json`은 이 연결을 조사할 자료이고 `trace.csv`와 화면은 실제 반응을 보여 줍니다.

## 4. 간단한 확인 실험

`--speed 0.5`만 `--speed 0.2`로 바꾸고 새 출력에 같은 1200스텝을 기록하세요.

- 첫 관측의 `[9:12]`가 `[0.2, 0, 0]`으로 달라지는지 확인합니다.
- 몸통 높이를 유지한 구간에서 시작·끝 위치의 차이를 비교합니다.
- 이동 거리가 줄어드는지 관찰하되 정확히 0.4배를 요구하지 않습니다. 가속과 자세 제어의 과도 구간도 포함되어 있습니다.

## 실행할 때 막히면

- **모델 로딩 실패**: 5.1 Assets의 `/Isaac/Robots/Unitree/H1/h1.usd`와 `H1_Policies/h1_policy.pt`, `h1_env.yaml` 접근을 확인하세요.
- **입력 shape 오류**: policy와 env가 같은 학습 실행의 파일인지, 69/19 조건인지 확인하세요.
- **발끝 보행·넘어짐**: 관절 이름 순서, 발목 기준 자세, gain과 effort limit를 학습 설정과 대조하세요.
- **진동하거나 반응이 느림**: `physics_dt`와 `decimation`을 확인하세요. 렌더 FPS로 정책 빈도를 추측하지 않습니다.
- **contract가 없음**: 첫 추론까지 진행했는지와 루프가 정상 종료했는지 확인하세요. CSV 파일 존재만으로 추론을 증명할 수는 없습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)에 대응합니다. 설치본 `H1FlatTerrainPolicy`와 `PolicyController`를 사용해 관측·행동·주기를 기록합니다.

`tutorial.json`은 `not_run`입니다. 이 문서는 시뮬레이터 안의 H1 위치 제어를 다루며, 새 정책 학습·ANYmal actuator 네트워크·실물 로봇 배포의 실행 검증을 포함하지 않습니다.
