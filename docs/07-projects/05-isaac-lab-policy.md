# 프로젝트 5: Isaac Lab에서 학습하고 정책을 평가한다

강화학습은 로봇이 움직이는 영상을 만드는 것으로 끝나지 않는다. 관측값, 행동, 보상, 종료 조건을 정의하고 학습하지 않은 조건에서도 결과를 확인해야 한다. 먼저 Cartpole로 학습과 평가의 전체 흐름을 익히고, 마지막에 로봇 작업과 Isaac Sim 배포로 확장한다.

## 준비할 것과 범위

[Isaac Lab 설치·구조](../06-developer/04-isaac-lab.md)를 먼저 읽고 **Isaac Lab v2.3.2와 Isaac Sim 5.1.0**을 사용한다. 이 프로젝트에서 다른 버전의 학습 스크립트나 설정을 섞지 않는다. v2.3.2 공식 Linux 요구사항에 적힌 Ubuntu 버전과 이 과정의 Ubuntu 24.04 호스트를 구분한다. 설치 장에 설명한 검증된 학습 환경 또는 공식 컨테이너를 먼저 구성한다.

다음 명령은 Isaac Lab 설치와 해당 학습 라이브러리 설치가 끝난 터미널에서 실행한다. ROS Jazzy 환경을 추가로 source할 필요는 없다.

```bash
cd "$ISAACLAB_PATH"
git describe --tags --exact-match
git rev-parse HEAD
./isaaclab.sh -p scripts/environments/list_envs.py
```

`v2.3.2`가 맞는지 확인하고 목록에 `Isaac-Cartpole-v0`가 있는지 찾는다. 해당 태그의 [Cartpole 등록 소스](https://github.com/isaac-sim/IsaacLab/blob/v2.3.2/source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/cartpole/__init__.py)는 RSL-RL용 설정을 포함한다. 소스 경로를 확인하지 않고 다른 버전의 작업 이름을 추측하지 않는다.

## 1단계: 학습 없이 물리와 초기화를 확인한다

```bash
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 1
```

힘을 주지 않을 때 막대가 쓰러지고 에피소드가 다시 시작하는지 관찰한다. 이 상태에서 이미 NaN, 바닥 통과, 자산 로딩 오류가 있으면 학습 전에 해결한다. 종료 후 무작위 행동도 확인한다.

```bash
./isaaclab.sh -p scripts/environments/random_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 16
```

한 환경의 실패가 다른 환경의 상태를 끌고 가면 충돌 분리와 reset 설정을 확인한다. `num_envs`는 동시에 실행하는 환경 수이며, 16개의 독립된 시도를 한 번에 계산한다는 뜻이다.

## 2단계: 작업 정의를 읽는다

Cartpole의 설정은 다음 파일에서 시작한다.

```bash
sed -n '1,220p' \
  source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/cartpole/cartpole_env_cfg.py
```

처음에는 코드를 바꾸지 않고 아래 표를 채운다.

| 항목 | 코드에서 찾을 내용 |
|---|---|
| 관측 | 카트 위치·속도, 막대 각도·각속도가 어떤 순서로 들어가는가 |
| 행동 | 힘 또는 구동 입력 하나가 어느 관절에 적용되는가 |
| 보상 | 막대를 세워 두는 보상과 위치·속도 관련 항이 어떻게 합쳐지는가 |
| 종료 | 시간 초과와 카트 범위 이탈이 어떻게 구분되는가 |
| 초기화 | 카트와 막대의 초기값을 어떤 범위에서 뽑는가 |
| 시간 간격 | 물리 한 step과 정책 한 번의 행동 사이에 몇 step이 있는가 |

관측의 순서를 바꾸면 같은 숫자 배열이라도 정책이 다른 값으로 해석한다. 체크포인트와 함께 단위·좌표계·순서를 기록해야 하는 이유이다.

## 3단계: 짧게 학습해 실행 경로를 확인한다

먼저 환경 64개, 반복 100회로 작은 실행을 한다.

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 64 \
  --max_iterations 100 \
  --seed 1 \
  --run_name course_smoke \
  --headless
```

이 실행은 학습 경로와 체크포인트 저장을 확인하기 위한 것이다. 100회 반복만으로 좋은 정책이 만들어졌다고 판단하지 않는다. 콘솔에서 보상과 에피소드 길이가 유한한 값인지, 로그 디렉터리와 `model_*.pt`가 생기는지 확인한다.

```bash
find logs/rsl_rl -type f -name 'model_*.pt'
```

출력 중 이번 실행의 파일을 골라 아래 환경 변수에 **실제 절대 경로**를 넣는다. 예시 경로를 그대로 실행하지 않는다.

```bash
export POLICY_CHECKPOINT="/actual/path/to/this/run/model_99.pt"
test -f "$POLICY_CHECKPOINT"
sha256sum "$POLICY_CHECKPOINT"
```

실제 마지막 파일 이름은 저장 간격과 학습 반복 수에 따라 달라진다. 학습 CLI 인자는 [v2.3.2 학습 파일](https://github.com/isaac-sim/IsaacLab/blob/v2.3.2/scripts/reinforcement_learning/rsl_rl/train.py)을 기준으로 한다.

## 4단계: 저장한 정책을 다시 읽어 평가한다

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task Isaac-Cartpole-v0 \
  --num_envs 1 \
  --checkpoint "$POLICY_CHECKPOINT"
```

학습이 끝난 프로세스의 상태를 이어 쓰는 것이 아니라 저장 파일을 다시 읽어 실행한다. 막대가 일정 시간 균형을 유지하는지, 초기화 뒤에도 다시 균형을 잡는지 확인한다. [v2.3.2 평가 파일](https://github.com/isaac-sim/IsaacLab/blob/v2.3.2/scripts/reinforcement_learning/rsl_rl/play.py)과 [체크포인트 인자 정의](https://github.com/isaac-sim/IsaacLab/blob/v2.3.2/scripts/reinforcement_learning/rsl_rl/cli_args.py)에 나온 인자를 사용한다.

그다음 학습 반복 수와 환경 수를 늘리고 seed를 바꾸어 적어도 세 번 실행한다. GPU 메모리가 부족하면 먼저 `num_envs`를 줄인다. 환경 수를 크게 늘리는 것을 성능 향상 자체로 해석하지 않는다.

## 5단계: 조건을 하나 바꾸어 비교한다

다음 중 하나만 선택한다.

- 초기 막대 각도의 범위를 늘린다.
- 평가 때 카트 또는 막대 질량을 바꾼다.
- 관측에 작은 노이즈를 추가한다.

학습 설정과 평가 설정을 별도로 저장한다. 시험 조건마다 에피소드 수를 동일하게 두고 평균 보상뿐 아니라 종료 원인과 에피소드 길이도 기록한다.

```json
{
  "task": "Isaac-Cartpole-v0",
  "seed": 1,
  "checkpoint_sha256": "실제 해시",
  "episodes": 30,
  "mean_episode_seconds": null,
  "early_termination_count": null,
  "changed_parameter": "initial_pole_angle_range"
}
```

`null`은 아직 측정하지 않은 값이다. 실패한 실행도 결과에 포함한다. 보상 함수를 바꿨다면 새 보상 숫자만으로 기존 정책보다 좋아졌다고 비교하지 말고 같은 물리적 성공 조건으로 평가한다.

## 6단계: 로봇 작업으로 확장한다

Cartpole을 완료한 뒤 이동·보행·팔 제어 중 하나를 선택한다. 처음에는 v2.3.2에 포함된 작업을 복제하고 관측 또는 보상 한 항만 바꾼다. 새 로봇, 새 작업, 새 학습 알고리즘을 동시에 도입하지 않는다.

보행 로봇이라면 다음과 같은 기록이 추가로 필요하다. 이 예시는 **보행용 설명 형식**이며 Cartpole 설정에 그대로 붙여 넣는 YAML이 아니다.

```yaml
policy_interface:
  joint_order: [joint_1, joint_2]
  observation_units: [rad_per_second, unit_vector, meter_per_second]
  action_type: joint_position_offset
  action_scale: 0.5
  physics_dt: 0.005
  policy_dt: 0.02
  reset_previous_action: true
```

관절 이름과 순서는 실제 작업의 배열과 맞춰 바꾼다. 정책 주기가 0.02초이고 물리 주기가 0.005초이면 한 행동을 물리 4 step 동안 유지한다. 이 비율을 배포에서도 유지한다.

## 7단계: Isaac Sim 배포를 검증한다

정책을 Isaac Sim에 배포할 때는 학습 관측·정규화·행동 범위를 같은 방식으로 계산해야 한다. TorchScript나 ONNX 파일만 복사하는 것으로 끝나지 않는다. 배포 방법은 [공식 5.1.0 정책 배포 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)을 따른다.

1. 공식 배포 예제를 원본 정책으로 실행해 기준 동작을 확인한다.
2. 자신의 정책이 요구하는 관절 이름·순서, 관측 차원·순서, 정규화, 행동 범위와 주기를 기록한다.
3. 정책 출력이 NaN/Inf 또는 제한 범위를 벗어나면 해당 로봇에 맞는 정지·안전 자세로 전환한다. 모든 로봇에서 숫자 0이 안전 자세인 것은 아니다.
4. 초기화 시 이전 행동과 재귀 정책의 숨은 상태를 함께 초기화한다.
5. 관측 배열 하나를 의도적으로 잘못 넣는 검사를 통해 시작 전에 오류를 찾는지 확인한다.
6. 올바른 설정에서 실제 로봇 위치·속도·접촉을 기록하며 반복 평가한다.

Cartpole 정책을 다른 로봇에 바로 적용하지 않는다. ROS 2를 연결할 경우 명령과 필요한 상태만 외부 노드로 주고받고, Isaac Sim의 Python 3.11 환경에 시스템 Jazzy의 Python 3.12 패키지를 섞지 않는다.

## 완료 조건

- 학습 없이 물리·초기화 확인을 끝냈다.
- 저장한 체크포인트를 새 프로세스에서 읽어 평가했다.
- 세 seed의 결과와 변경한 평가 조건을 기록했다.
- 배포한 경우 학습과 배포의 관측·행동 정의를 수치로 비교했다.
- 학습 통과, 평가 통과, 배포 통과를 각각 기록했다. 실행하지 않은 단계는 미실행으로 남겼다.

## 출처

- [Isaac Lab](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/index.html)
- [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)
- [Running a Reinforcement Learning Policy through ROS 2 and Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html)
- [Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
- [Isaac Lab v2.3.2 요구사항과 설치](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/index.html)
