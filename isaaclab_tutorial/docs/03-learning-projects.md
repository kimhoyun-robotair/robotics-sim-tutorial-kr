# 23–36단계: 로봇 학습과 재현 가능한 프로젝트

이 장은 1–22단계에서 장면, 로봇, 센서가 정상 동작하는 것을 확인한 뒤 진행한다.
실습 기준은 **Ubuntu 24.04 LTS / Isaac Lab v3.0.0-beta2.patch1 / Isaac Sim 6.0.1 / PhysX**이다.
GUI를 볼 때 `--viz kit`를 붙인다. 학습 명령에서 이 옵션을 생략하면 화면 없이 계산한다.
`--headless`가 들어 있는 2.x 예제를 그대로 섞지 않는다.

각 명령은 Isaac Lab 가상환경을 활성화한 터미널에서 실행한다.
두 저장소의 역할도 구분한다. `IsaacLab`에는 NVIDIA 원본이, 이 저장소에는 설명과 별도 실습 코드가 있다.

```bash
export ISAACLAB_ROOT="$HOME/IsaacLab"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
cd "$ISAACLAB_ROOT"
```

아래 반복 횟수는 실습 시작값이다. 해당 횟수에 도달했다는 사실만으로 학습 성공을 판정하지 않는다.
이 문서의 실행 예제는 고정한 태그의 명령행 파서와 환경 설정을 대조한 것이다.
작성 환경에서 RTX GPU로 학습·렌더링을 실행한 결과를 제시하는 문서는 아니다.
실제 성공 여부는 각 단계의 완료 조건과 36단계 기록으로 확인한다.

<a id="step-23"></a>

## 23. 관측·행동·보상·종료로 학습 문제 정의하기

**목표:** 로봇이 움직이는 장면을 학습 가능한 문제로 바꾸는 방법을 이해한다.

정책은 현재 관측을 받아 행동을 출력하는 함수다.
강화학습은 그 함수를 바꾸어 여러 번의 행동 끝에 얻는 보상을 높이는 과정이다.
로봇의 형상과 물리 설정만 준비해서는 정책이 무엇을 배워야 하는지 정해지지 않는다.

Cartpole은 레일 위 카트를 좌우로 움직여 막대의 균형을 유지하는 문제다.
이 단순한 문제에도 다음 구성요소가 모두 필요하다.

| 요소 | Cartpole에서의 의미 | 실수하기 쉬운 부분 |
|---|---|---|
| 상태 | 시뮬레이터가 알고 있는 위치·속도 등 | 정책이 상태 전체를 받는다고 가정하기 |
| 관측 | 기본 관절 위치에 대한 차이, 관절 속도 차이 | 관측 순서나 단위를 바꾸고 이전 정책 쓰기 |
| 행동 | 카트의 슬라이더 관절에 가할 힘 | 정규화된 행동을 곧바로 뉴턴으로 읽기 |
| 보상 | 생존, 막대 자세, 속도 등으로 계산한 점수 | 화면이 좋아 보인다는 이유만으로 보상 설계 확정하기 |
| 종료 | 카트가 레일 범위를 벗어나는 실패 | 실패와 시간 제한을 같은 의미로 취급하기 |
| 초기화 | 새 에피소드의 위치·속도 샘플링 | 관절 위치만 바꾸고 속도·버퍼를 남기기 |

공식 Manager 기반 Cartpole의 행동은 다음 설정을 사용한다.
`a=0.2`이면 힘 목표가 `20 N`인 셈이다. 실제 물리 결과에는 자산의 제한도 관여한다.

```python
from isaaclab.envs.mdp import JointEffortActionCfg

cart_action = JointEffortActionCfg(
    asset_name="robot",
    joint_names=["slider_to_cart"],
    scale=100.0,
)
```

공식 관측은 두 관절의 상대 위치와 상대 속도를 이어 붙인다.
관절 순서를 기억에 의존해 하드코딩하지 말고, 실제 자산의 이름과 관측 설정을 함께 확인한다.

```python
# 환경이 생성된 뒤 콘솔이나 디버거에서 확인하는 코드다.
print(env.unwrapped.scene["robot"].joint_names)
print(env.unwrapped.observation_manager.active_terms)
print(env.unwrapped.action_manager.action.shape)
```

기본 설정은 물리 시간 간격 `1/120초`, 행동 간격은 물리 두 스텝마다 한 번이다.
따라서 정책은 시뮬레이션 시간 기준 약 `60 Hz`로 새 행동을 낸다.
에피소드 제한은 `5초`이므로 최대 약 `300`번의 행동을 수행한다.

```python
physics_dt = 1.0 / 120.0
decimation = 2
control_dt = physics_dt * decimation
print(control_dt, 1.0 / control_dt)  # 약 0.0167초, 60 Hz
```

공식 Manager Cartpole은 카트 위치 `±3 m` 범위 이탈을 실패로 처리한다.
막대가 특정 각도 이상 기울면 곧바로 종료한다는 조건은 이 설정에 없다.
시간 제한까지 살아남았더라도 막대를 제대로 세웠는지는 별도 각도 지표로 확인해야 한다.
또한 RewardManager는 각 보상 항의 가중치에 제어 시간 간격을 곱한다.
한 스텝의 생존 보상이 항상 `1`이라고 가정하고 다른 라이브러리의 결과와 비교하지 않는다.

**완료 조건:** 행동의 단위, 정책 주기, 실패 종료와 시간 제한의 차이를 말로 설명한다.

공식 근거: [Cartpole 환경 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/cartpole/cartpole_env_cfg.py), [RewardManager](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/managers/reward_manager.py).

<a id="step-24"></a>

## 24. Manager 기반과 Direct 환경 비교하기

**목표:** 코드의 책임을 보고 환경 구현 방식을 선택한다.

Manager 기반 환경은 관측, 행동, 보상, 종료, 초기화를 각각의 설정과 함수로 나눈다.
Direct 환경은 환경 클래스가 해당 계산을 직접 구현한다.
두 방식 모두 강화학습 환경이며, GUI 유무와는 별개의 구분이다.

| 기준 | Manager 기반 | Direct |
|---|---|---|
| 보상 수정 | 보상 함수와 `RewardTermCfg` 추가 | `_get_rewards()` 구현 수정 |
| 관측 수정 | 관측 그룹에 항 추가 | `_get_observations()` 수정 |
| 종료 수정 | 종료 항 추가 | `_get_dones()` 수정 |
| 초기화 수정 | reset 이벤트 설정 | `_reset_idx()` 구현 수정 |
| 장점 | 항별 설명·재사용·실험 비교가 쉽다 | 계산 흐름을 한 클래스에서 세밀하게 다룬다 |
| 이 장에서 사용 | 기본 학습과 보상 비교 | 공식 코드 구조 비교 |

등록된 환경은 서로 다른 이름을 가진다.
둘을 같은 모델 이름으로 취급하거나 체크포인트를 서로 바꿔 끼우지 않는다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 1 --viz kit physics=physx
```

GUI를 닫은 뒤 Direct 버전을 실행한다.

```bash
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Cartpole-Direct-v0 --num_envs 1 --viz kit physics=physx
```

`zero_agent`의 영 행동은 이 Cartpole에서는 카트 힘이 0이라는 뜻이다.
모든 로봇 환경에서 영 행동이 모터 비활성화를 뜻하지는 않는다.
관절 위치 제어에서는 영 행동이 기본 자세를 유지하는 목표로 바뀔 수 있다.

공식 Direct 코드는 다음 역할을 가진 메서드들로 읽는다.
아래는 구현을 복사한 코드가 아니라 파일을 탐색할 때의 읽기 순서다.

```text
_pre_physics_step(actions) : 새 정책 행동을 저장·전처리한다.
_apply_action()            : 매 물리 스텝에 힘이나 목표를 전달한다.
_get_observations()        : 다음 정책 입력을 계산한다.
_get_rewards()             : 환경별 보상을 계산한다.
_get_dones()               : 실패와 시간 제한을 각각 계산한다.
_reset_idx(env_ids)        : 끝난 환경만 초기화한다.
```

환경 하나가 끝났다고 모든 병렬 환경을 초기화하면 학습 데이터가 왜곡된다.
관측 배열 첫 번째 차원의 길이가 병렬 환경 수라는 점을 기억한다.

**완료 조건:** 관측 하나를 추가할 위치와 종료 조건 하나를 추가할 위치를 두 방식에서 찾는다.

공식 근거: [Manager Cartpole 등록](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/cartpole/__init__.py), [Direct Cartpole 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/direct/cartpole/cartpole_env.py).

<a id="step-25"></a>

## 25. 무작위 정책으로 학습 전 기준 확인하기

**목표:** 학습이 잘못된 것과 환경 자체가 잘못된 것을 구분한다.

먼저 학습하지 않은 무작위 행동을 넣어 본다.
카트가 좌우로 이동하고, 막대가 흔들리며, 카트가 범위를 벗어나면 해당 환경이 초기화되는 것이 자연스럽다.
무작위 정책이 막대를 넘어뜨리는 현상 자체는 잘못된 로봇 모델의 증거가 아니다.
반면 자산 생성 직후 관절이 분리되거나 전체 상태가 NaN이 되는 현상은 진행을 멈추고 확인해야 한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/environments/random_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 4 --viz kit physics=physx
```

카메라를 움직여 각각의 환경이 분리되어 있는지 확인한다.
네 개를 같은 원점에 겹쳐 생성한 장면과 네 환경을 병렬로 실행하는 장면은 다르다.
`ENV_REGEX_NS`와 `env_spacing`을 임의로 지우지 않는다.
공식 무작위 에이전트는 `[-1, 1]` 범위에서 행동을 샘플링한다.

```python
# 공식 random_agent.py에서 사용하는 행동 샘플링 방식이다.
actions = 2 * torch.rand(
    env.action_space.shape, device=env.unwrapped.device
) - 1
```

직접 루프를 작성할 때는 Gymnasium 환경의 반환값이 다섯 개임을 구분한다.
아래 코드의 `env`는 RSL-RL wrapper로 감싸기 전 환경이다.

```python
obs, info = env.reset()
with torch.inference_mode():
    obs, reward, terminated, truncated, info = env.step(actions)
    assert torch.isfinite(reward).all(), "보상에 NaN 또는 Inf가 있다."
    assert torch.isfinite(obs["policy"]).all(), "관측에 NaN 또는 Inf가 있다."
    done = terminated | truncated
```

한 프레임에 대한 assertion만으로 안정성을 보장할 수는 없다.
초기 생성, 수백 스텝 진행, 여러 차례 reset을 모두 관찰해야 한다.
`random_agent.py`는 창을 닫을 때까지 동작하므로 확인이 끝나면 Kit 창을 닫는다.
이 스크립트에는 GUI를 기본으로 여는 설정도 있으므로 학습 명령의 기본값과 혼동하지 않는다.

다음 내용을 실습 노트에 남긴다.

```text
환경 이름: Isaac-Cartpole-v0
병렬 환경 수: 4
물리 백엔드: physx
확인 항목: 생성 / 관절 연결 / 카트 이동 / reset / 유한한 관측·보상
관찰 결과: 실제로 확인한 결과만 기입
```

**완료 조건:** 학습을 시작하기 전에 환경 생성과 reset을 포함한 동작을 확인한다.

공식 근거: [무작위 에이전트](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/environments/random_agent.py), [RSL-RL 환경 wrapper](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py).

<a id="step-26"></a>

## 26. 프로젝트 5 — Cartpole을 PPO로 학습하기

**만들 결과:** 스스로 막대를 세우는 정책과 학습 설정·체크포인트다.

PPO는 현재 정책으로 모은 경험을 이용하되 한 번에 정책을 지나치게 바꾸지 않도록 조절하는 알고리즘이다.
Isaac Lab이 장면과 환경을 담당하고, 여기서는 RSL-RL이 PPO 학습을 담당한다.
먼저 필요한 라이브러리를 설치했는지 확인한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p -c 'import importlib.metadata as m; print(m.version("rsl-rl-lib"))'
./isaaclab.sh train --rl_library rsl_rl --help
```

이 태그의 RSL-RL 학습 스크립트는 `5.0.1` 이상을 요구한다.
설치 장에서 선택 설치를 진행하지 않았다면 `./isaaclab.sh -i 'rl[rsl-rl]'`로 설치한다.
다른 환경의 torch를 덮어 설치하는 방식으로 해결하지 않는다.

처음에는 적은 환경으로 실행 경로를 확인한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 64 \
  --seed 42 --max_iterations 5 --run_name smoke_s42 \
  --experiment_name tutorial_cartpole_smoke --viz kit physics=physx
```

다섯 iteration은 설치와 실행을 확인하는 용도다.
정책이 균형을 잘 잡지 못하더라도 그 사실만으로 학습 코드가 잘못되었다고 판단하지 않는다.
짧은 실행이 완료되면 다음 학습을 진행한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 512 \
  --seed 42 --max_iterations 150 --run_name baseline_s42 \
  --experiment_name tutorial_cartpole_first physics=physx
```

VRAM이 부족하면 `512 → 256 → 128` 순서로 환경 수를 줄인다.
한 번에 카메라 해상도, 환경 수, 알고리즘까지 바꾸면 무엇이 해결되었는지 알기 어렵다.
환경 수를 변경하면 같은 iteration 수에서 수집하는 데이터 양도 달라진다.

공식 Cartpole PPO는 환경당 `16`스텝씩 경험을 모은다.
따라서 `512`개 환경으로 한 iteration을 수행하면 약 `8192`개의 transition을 모은다.

```python
num_envs = 512
num_steps_per_env = 16
iterations = 150
print(num_envs * num_steps_per_env * iterations)  # 1,228,800
```

정책과 가치 함수는 각각 `[32, 32]` 크기의 은닉층을 사용한다.
학습 결과는 실행 위치 기준 `logs/rsl_rl/<experiment_name>/<시각>_<run_name>/`에 기록된다.
여기에는 `model_*.pt`와 `params/env.yaml`, `params/agent.yaml`이 포함된다.

```bash
find logs/rsl_rl/tutorial_cartpole_first -type f \
  \( -name 'model_*.pt' -o -name 'env.yaml' -o -name 'agent.yaml' \)
```

**완료 조건:** 모델 파일만 보관하지 말고 대응하는 환경·에이전트 설정과 seed를 함께 보관한다.

공식 근거: [통합 학습 진입점](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/train.py), [RSL-RL 학습 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/train_rsl_rl.py), [Cartpole PPO 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/classic/cartpole/agents/rsl_rl_ppo_cfg.py).

<a id="step-27"></a>

## 27. 체크포인트를 불러오고 동영상으로 확인하기

**목표:** 어느 학습 결과를 재생했는지 명확하게 남긴다.

콘솔에 출력된 실제 경로를 확인한 뒤 `CHECKPOINT`에 넣는다.
아래 경로의 시각과 모델 번호는 자신의 파일로 바꾸어야 한다.
가장 최근 파일을 무조건 자동 선택하면 다른 실험의 결과를 보는 실수를 하기 쉽다.

```bash
export CHECKPOINT="$ISAACLAB_ROOT/logs/rsl_rl/tutorial_cartpole_first/실제_실행_폴더/model_실제번호.pt"
test -f "$CHECKPOINT"
```

`test`가 실패했다면 실행하지 말고 위 단계의 `find` 결과에서 경로를 다시 확인한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh play --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 4 \
  --checkpoint "$CHECKPOINT" --seed 1000 \
  --viz kit --real-time physics=physx
```

정책은 추론만 수행한다. `play`는 학습을 이어가는 명령이 아니다.
재생 스크립트는 체크포인트 폴더의 `exported/`에 JIT와 ONNX 정책도 내보낸다.
이는 정책 추론용 파일이지 로봇의 관측 순서·제어 주기·단위를 자동으로 맞춰 주는 배포 패키지가 아니다.

영상도 같은 체크포인트로 만든다.

```bash
./isaaclab.sh play --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 1 \
  --checkpoint "$CHECKPOINT" --seed 1000 \
  --video --video_length 300 --viz kit physics=physx
```

공식 재생 코드는 `--video`가 있으면 카메라 활성화 설정을 켠다.
300은 초가 아니라 환경 스텝 수이며, 이 Cartpole 설정에서는 약 5초에 해당한다.
영상은 체크포인트가 있는 실행 폴더 아래 `videos/play/`에 저장된다.
첫 영상은 GUI와 함께 생성해 창과 영상이 일치하는지 확인한다.

검은 영상이 만들어지면 다음 순서로 원인을 좁힌다.

1. 같은 명령에서 창에 장면이 정상적으로 보이는지 확인한다.
2. 환경 수를 1로 유지하고 카메라가 로봇을 향하는지 확인한다.
3. 환경의 DomeLight와 자산 다운로드 오류를 확인한다.
4. 첫 프레임뿐 아니라 영상 중간 프레임까지 살핀다.
5. 센서 배열과 렌더러의 유효성 검사를 통과한 뒤 화면 없는 촬영을 시도한다.

학습 재개에는 `--resume`과 학습 실행 폴더·파일 이름을 사용한다.
이 명령의 체크포인트 인자는 학습 폴더 안에서 찾을 이름/패턴이며, 위 `play`의 절대 경로 사용과 구분한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 512 --seed 42 \
  --experiment_name tutorial_cartpole_first --resume \
  --load_run '실제_실행_폴더' --checkpoint 'model_실제번호.pt' \
  --max_iterations 50 --run_name resumed_s42 physics=physx
```

재개 전에는 actor 구조와 관측 차원이 원래 학습과 같은지 확인한다.
보상 변경의 비교 실험에는 재개보다 동일한 시작 조건의 새 학습을 사용한다.

**완료 조건:** 모델 경로, 영상, 실행 설정이 하나의 실험을 가리킨다.

공식 근거: [RSL-RL 재생 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/play_rsl_rl.py), [학습·재생 인자](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/cli_args.py).

<a id="step-28"></a>

## 28. 프로젝트 6 — Franka 목표 자세 도달하기

**만들 결과:** Franka 말단이 주어진 목표 위치와 자세에 접근하는 정책이다.

이 프로젝트는 물체를 잡는 과제가 아니다.
말단 목표에 도달하는 문제부터 다뤄야 자세 제어, 목표 관측, 보상 의미를 이해하기 쉽다.
공식 `Isaac-Reach-Franka-v0`는 관절 위치 행동을 사용한다.
목표 자세의 위치 범위는 로봇을 기준으로 x `0.35–0.65 m`, y `-0.2–0.2 m`, z `0.15–0.5 m`다.
목표는 약 4초마다 바뀌고 에피소드 제한은 12초다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Reach-Franka-v0 --num_envs 1 --viz kit physics=physx
```

바닥이 원점 아래에 있는 것은 공식 장면이 테이블과 고정 베이스 로봇을 포함하기 때문이다.
테이블이 낯선 높이에 보인다고 로봇 베이스의 z값만 바꾸지 않는다.
장면·충돌·로봇 고정 설정을 함께 봐야 한다.

핵심 행동 설정은 다음과 같다.

```python
from isaaclab.envs.mdp import JointPositionActionCfg

arm_action = JointPositionActionCfg(
    asset_name="robot",
    joint_names=["panda_joint.*"],
    scale=0.5,
    use_default_offset=True,
)
```

이는 행동 1을 무조건 관절 각도 1 rad로 보내는 설정이 아니다.
기본 자세에 행동값의 0.5배를 더한 관절 위치 목표로 변환한다.
말단은 `panda_hand`이고 손가락을 여닫는 행동은 이 기본 Reach 과제의 학습 목표가 아니다.

장면을 확인한 뒤 짧게 학습 경로를 점검하고 본 학습을 수행한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Reach-Franka-v0 --num_envs 32 \
  --max_iterations 5 --seed 42 --run_name reach_smoke \
  --experiment_name tutorial_franka_smoke --viz kit physics=physx
```

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Reach-Franka-v0 --num_envs 256 \
  --max_iterations 500 --seed 42 --run_name reach_s42 \
  --experiment_name tutorial_franka_reach physics=physx
```

재생할 때 실제 Franka 체크포인트 경로를 지정한다.

```bash
export FRANKA_CHECKPOINT="실제_Franka_체크포인트_절대경로.pt"
./isaaclab.sh play --rl_library rsl_rl \
  --task Isaac-Reach-Franka-Play-v0 --num_envs 4 \
  --checkpoint "$FRANKA_CHECKPOINT" --viz kit physics=physx
```

`-Play` 설정은 관측 노이즈를 끈다.
잘 보이는 데모와 학습 분포에서의 정량 평가가 같은 조건이라고 생각하지 않는다.
이 환경은 기본 학습에서 관절 위치·속도에 작은 관측 노이즈를 넣으므로 숫자의 작은 변동은 의도된 설정일 수 있다.
영상에 깨진 픽셀이 생기거나 관절 상태가 비정상적으로 튀는 현상과 구분한다.

비슷한 이름의 `Isaac-Reach-Franka-IK-Abs-v0`와 `-IK-Rel-v0`는 이 태그에서 RSL-RL 설정이 등록되지 않았다.
이름만 교체해 위 PPO 명령을 실행하면 필요한 agent 설정을 찾지 못한다.
IK와 PPO의 차이는 제어 방식과 학습 설정을 함께 살펴야 이해할 수 있다.

**완료 조건:** 여러 목표가 바뀌는 동안 말단 위치·자세 오차와 과도한 관절 진동을 함께 관찰한다.

공식 근거: [Franka Reach 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/config/franka/joint_pos_env_cfg.py), [Reach 공통 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/reach_env_cfg.py), [Franka 환경 등록](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/config/franka/__init__.py).

<a id="step-29"></a>

## 29. 프로젝트 7 — ANYmal C 평지 보행 학습하기

**만들 결과:** 전진·횡이동·회전 속도 명령을 추종하는 사족보행 정책이다.

바닥 접촉과 중력 방향을 잘못 설정한 로봇으로 보행 학습을 시작하면 보상 함수만 바꾸어서는 해결되지 않는다.
앞 장의 물리 검증을 통과한 공식 ANYmal C 자산과 평지 환경을 그대로 사용한다.

먼저 영 행동에서 초기 자세와 접촉을 살펴본다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Velocity-Flat-Anymal-C-v0 \
  --num_envs 1 --viz kit physics=physx
```

처음 학습하는 정책과 무작위 정책이 넘어지는 것은 예상할 수 있다.
그러나 발이 바닥을 계속 관통하거나 관절 연결이 끊어지는 현상은 학습 과정의 시행착오로 처리하지 않는다.
이 환경은 몸통의 비정상 접촉을 종료 조건으로 사용한다.
물리 시간 간격은 `0.005초`, decimation은 `4`이므로 정책 주기는 `50 Hz`다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Velocity-Flat-Anymal-C-v0 \
  --num_envs 32 --max_iterations 5 --seed 42 \
  --experiment_name tutorial_anymal_smoke --run_name flat_smoke \
  --viz kit physics=physx
```

실행 경로가 확인되면 화면 없이 학습한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Velocity-Flat-Anymal-C-v0 \
  --num_envs 256 --max_iterations 1500 --seed 42 \
  --experiment_name tutorial_anymal_flat --run_name flat_s42 physics=physx
```

작은 병렬 환경 수는 메모리 부담을 줄이지만 같은 iteration에서 경험 수가 줄어든다.
1500 iteration으로 충분한지는 실제 속도 추종 오차와 넘어짐을 보고 결정한다.
학습 시간을 예측할 때는 GPU 이름, 병렬 환경 수, FPS를 함께 기록한다.

```bash
export ANYMAL_CHECKPOINT="실제_ANYmal_평지_체크포인트_절대경로.pt"
./isaaclab.sh play --rl_library rsl_rl \
  --task Isaac-Velocity-Flat-Anymal-C-Play-v0 \
  --num_envs 4 --checkpoint "$ANYMAL_CHECKPOINT" --viz kit physics=physx
```

평지 버전은 높이 스캔 관측과 지형 난이도 커리큘럼을 제거한다.
불규칙 지형 버전은 지형과 관측 구성이 달라지므로 평지 체크포인트를 그대로 재생하는 과제로 시작하지 않는다.
불규칙 지형은 별도 학습으로 확장한다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Velocity-Rough-Anymal-C-v0 \
  --num_envs 128 --max_iterations 1500 --seed 42 \
  --experiment_name tutorial_anymal_rough --run_name rough_s42 physics=physx
```

`-Play` 버전은 관측 노이즈와 밀기 이벤트 등을 비활성화한다.
학습 환경과 평가 환경의 차이를 보고서에 적는다.
속도를 잘 추종해도 과도한 토크나 미끄러짐이 있다면 좋은 제어 정책이라고 단정하지 않는다.

**완료 조건:** 평지에서 속도 추종, 넘어짐, 발 접촉, 관절 진동을 확인하고 영상 한 개를 남긴다.

공식 근거: [ANYmal C 평지 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/anymal_c/flat_env_cfg.py), [보행 환경 공통 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/velocity_env_cfg.py).

<a id="step-30"></a>

## 30. 보상 항 하나를 추가한 사용자 환경 만들기

**목표:** NVIDIA 원본을 수정하지 않고 비교 가능한 두 학습 문제를 등록한다.

보상 함수는 정책이 어떤 행동을 선호할지 정하는 장치다.
하지만 여러 항을 동시에 바꾸면 무엇이 결과를 바꾸었는지 알기 어렵다.
이 저장소의 [train_cartpole_variant.py](../examples/train_cartpole_variant.py)는 공식 Manager Cartpole을 그대로 사용하는 baseline과 행동 변화 비용 하나를 추가한 smooth를 등록한다.

| 변형 | Gym 환경 이름 | 공식 설정과의 차이 |
|---|---|---|
| baseline | `Isaac-Tutorial-Cartpole-Baseline-v0` | 없음 |
| smooth | `Isaac-Tutorial-Cartpole-Smooth-v0` | 행동 변화 제곱합에 음의 가중치 추가 |

핵심 보상 함수는 다음과 같다.

```python
def action_change_cost(env):
    delta = env.action_manager.action - env.action_manager.prev_action
    return delta.square().sum(dim=-1)
```

반환값은 `[num_envs]` 형태다.
`sum()`만 호출하면 모든 환경을 합친 스칼라가 되므로 마지막 차원만 합친다.
이 함수는 정규화된 정책 행동 변화량을 계산하며, 기계적인 jerk나 에너지 소비량을 직접 측정하지 않는다.

```python
from isaaclab.managers import RewardTermCfg
from isaaclab.utils.configclass import configclass
from isaaclab_tasks.manager_based.classic.cartpole.cartpole_env_cfg import RewardsCfg

@configclass
class SmoothRewardsCfg(RewardsCfg):
    action_change = RewardTermCfg(func=action_change_cost, weight=-0.002)
```

음의 가중치이므로 빠르게 바뀌는 행동에 비용을 부과한다.
`-0.002`는 이 튜토리얼의 비교 시작값이며 공식 권장 최적값이 아니다.
과도하게 큰 비용은 필요한 균형 회복 행동까지 억제할 수 있다.

스크립트는 Gym registry를 등록한 **같은 Python 프로세스**에서 공식 학습 진입점을 실행한다.
다른 프로세스를 새로 시작하면 메모리에 등록한 사용자 환경이 사라지므로 이 구조가 필요하다.
자체 PPO 구현은 추가하지 않는다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/train_cartpole_variant.py" \
  --variant smooth --mode train --num_envs 64 --max_iterations 5 \
  --seed 42 --experiment_name tutorial_variant_smoke \
  --run_name smooth_smoke --viz kit physics=physx
```

콘솔의 reward 항 목록에 `action_change`가 나타나는지 확인한다.
학습 결과의 `params/env.yaml`에서도 가중치가 저장되었는지 확인한다.
보상 값이 음수라는 이유만으로 실패라고 판단하지 않는다.

GUI 재생에도 같은 등록 코드가 필요하다.

```bash
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/train_cartpole_variant.py" \
  --variant smooth --mode play --num_envs 1 \
  --checkpoint "실제_smooth_체크포인트_절대경로.pt" --viz kit physics=physx
```

**완료 조건:** smooth에만 보상 항 하나가 추가되며 관측, 행동, 물리 설정은 두 변형에서 같다.

공식 근거: [환경 설정 불러오기](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/utils/parse_cfg.py), [공식 학습 dispatcher](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/common.py).

<a id="step-31"></a>

## 31. 환경 무작위화와 커리큘럼 구분하기

**목표:** 관측의 작은 변동, 물리 조건 변화, 잘못된 센서 출력을 구분한다.

환경 무작위화는 초기 자세, 질량, 마찰, 관측 노이즈 등을 일정 범위 안에서 바꾸는 방법이다.
커리큘럼은 학습 단계나 성과에 따라 문제의 난이도·가중치를 바꾸는 방법이다.
둘은 동시에 사용할 수 있지만 원리와 점검 방식이 다르다.

| 설정 | 언제 바뀌는가 | 확인할 사항 |
|---|---|---|
| startup 이벤트 | 환경 초기 생성 | 물리 재질·질량이 유효 범위인가 |
| reset 이벤트 | 새 에피소드 | 서로 관통하지 않는 초기 자세인가 |
| interval 이벤트 | 일정 시간 간격 | 외란 크기와 주기가 의도와 같은가 |
| 관측 노이즈 | 관측 계산 | 단위·크기·평가 시 활성화 여부 |
| 커리큘럼 | 학습 진행·성공도 등 | 난이도 상승과 지표 저하의 관계 |

Franka Reach의 관측 노이즈는 공식 설정에서 위치·속도 항에 적용된다.
진단을 위해 관측 노이즈를 끈 실행은 다음과 같이 할 수 있다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Reach-Franka-v0 --num_envs 32 \
  --max_iterations 5 --seed 42 --viz kit physics=physx \
  env.observations.policy.enable_corruption=false
```

진단용 실행을 노이즈가 켜진 본 실험과 같은 이름으로 저장하지 않는다.
센서에 검은 프레임이나 NaN이 생기는 현상을 도메인 무작위화라고 해석해서는 안 된다.

Cartpole의 초기 막대 각도 범위를 줄여 더 쉬운 조건을 만드는 예시는 다음과 같다.

```bash
./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Cartpole-v0 --num_envs 128 --max_iterations 100 \
  --seed 42 --experiment_name tutorial_cartpole_easy physics=physx \
  'env.events.reset_pole_position.params.position_range=[-0.15,0.15]'
```

이는 고정된 쉬운 분포의 실험이며 자동 커리큘럼은 아니다.
마지막에 동일한 어려운 초기조건으로 평가해야 실제 개선인지 판단할 수 있다.

공식 ANYmal 기본 설정의 `add_base_mass`는 질량을 배율로 바꾼다.
현재 태그는 `operation="scale"`, `distribution="log_uniform"`을 사용하므로 옛 예제의 kg 단위 가산 값과 섞지 않는다.
마찰은 `physics_material` 이벤트, 밀기는 `push_robot` 이벤트를 확인한다.

Franka Reach에는 행동 변화·관절 속도 패널티 가중치를 일정 스텝 이후 바꾸는 커리큘럼이 있다.
그래서 시작 시 보상 가중치만 확인하고 전체 학습 동안 고정되어 있다고 가정하면 잘못 해석할 수 있다.

**완료 조건:** 비교 실험마다 활성화한 랜덤화와 커리큘럼을 표로 기록한다.

공식 근거: [보행 이벤트·커리큘럼](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/velocity_env_cfg.py), [Reach 커리큘럼](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/reach/reach_env_cfg.py).

<a id="step-32"></a>

## 32. 모방학습·Isaac Lab Mimic·GR00T 연결 이해하기

**목표:** PPO 외의 로봇 학습 흐름을 이해하고 키보드 시연 수집을 경험한다.

모방학습은 사람이 보여 준 관측·행동의 대응을 학습한다.
행동 복제의 단순한 예는 데이터 속 행동을 정책이 비슷하게 출력하도록 손실을 줄이는 것이다.
강화학습의 보상 설계와 다른 출발점이지만, 시연의 품질과 평가 조건을 정의해야 한다는 점은 같다.

```python
# 행동 복제의 개념 예제다. 완성된 학습 스크립트가 아니다.
predicted_action = policy(batch_observation)
loss = (predicted_action - demonstrated_action).square().mean()
```

Isaac Lab Mimic은 소수의 시연을 물체 기준의 하위 작업으로 나누고 새로운 배치에 맞게 변환하여 시연 데이터를 늘리는 도구다.
물체가 옮겨졌다고 손끝 궤적을 무조건 평행 이동하면 충돌과 도달 불가능한 목표가 생길 수 있다.
생성 후 성공 판정과 재생 검사가 필요한 이유다.
Mimic 자체가 PPO를 대신하는 범용 정책 모델인 것은 아니다.

GR00T는 NVIDIA의 로봇 기반 모델 계열이다.
Isaac Lab은 그런 정책을 학습·평가할 수 있는 시뮬레이션 환경과 데이터를 구성하는 역할을 한다.
Mimic으로 생성한 데이터가 곧바로 모든 GR00T 모델의 입력 형식에 맞는다고 가정하지 않는다.
로봇의 embodiment, 센서, 행동 표현, 시간 간격, 데이터 스키마를 맞춰야 한다.

이 단계의 선택 실습은 Linux에서 실행하는 Franka 큐브 쌓기 시연이다.
설치 장에서 최소 RL 구성만 설치했다면 Mimic과 teleop 의존성을 먼저 설치한다.
HDF5 파일 저장과 키보드 입력이 가능한 로컬 GUI 세션을 사용한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -i mimic,teleop
mkdir -p datasets/tutorial_stack
./isaaclab.sh -p scripts/environments/teleoperation/teleop_se3_agent.py \
  --task Isaac-Stack-Cube-Franka-IK-Rel-v0 \
  --num_envs 1 --teleop_device keyboard --sensitivity 1 --viz kit
```

처음에는 낮은 sensitivity에서 손끝 움직임과 축 방향을 확인한다.
키 입력이 적용되도록 시뮬레이터 창을 활성화한다.
키 바인딩은 실행 시 출력되는 도움말을 기준으로 확인한다.

| 조작 | 키 |
|---|---|
| x 이동 | W / S |
| y 이동 | A / D |
| z 이동 | Q / E |
| x축 회전 | Z / X |
| y축 회전 | T / G |
| z축 회전 | C / V |
| 그리퍼 전환 | K |
| 환경 초기화, 기록 중이면 현재 시연도 초기화 | R |

조작을 익혔다면 종료한 뒤 실제 시연을 기록한다.
`R`은 단순히 이동 명령을 0으로 만드는 키가 아니다. 현재 큐브 배치와 작업 진행 상태를 초기화하므로 누르기 전에 저장 상태를 확인한다.

```bash
./isaaclab.sh -p scripts/tools/record_demos.py \
  --task Isaac-Stack-Cube-Franka-IK-Rel-v0 \
  --teleop_device keyboard --viz kit \
  --dataset_file ./datasets/tutorial_stack/dataset.hdf5 --num_demos 10
```

단순히 10번 움직이는 것이 아니라 환경의 성공 조건을 만족하는 시연이 저장되는지 확인한다.
큐브는 아래에서 위로 파랑, 빨강, 초록 순서로 쌓는 공식 과제다.
수집 후 공식 문서의 replay, subtask annotation, 소량 생성, 대량 생성, 정책 학습 순서로 확장한다.
큰 데이터셋부터 생성하면 잘못된 성공 조건으로 불량 시연을 대량 저장할 수 있다.

본 튜토리얼의 필수 RL 프로젝트는 ROS를 사용하지 않는다.
실물 배포나 외부 제어기 연결로 확장하면서 ROS가 필요하면 **ROS 2 Jazzy**를 기준으로 별도 프로세스에서 통신 경로를 구성한다.
ROS 관절 이름·단위·시계와 Lab 정책의 관측/행동 규약을 명시적으로 대응시키기 전에는 정책 출력을 모터 명령으로 전달하지 않는다.

**완료 조건:** RL·행동 복제·Mimic·GR00T의 역할을 설명하고, 선택 실습에서는 성공 시연 파일을 확인한다.

공식 근거: [태그의 Mimic 공식 튜토리얼](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/overview/imitation-learning/teleop_imitation.rst), [GR00T 공식 저장소](https://github.com/NVIDIA/Isaac-GR00T).

<a id="step-33"></a>

## 33. 같은 초기조건에서 정책 평가하기

**목표:** 학습 곡선과 데모 영상만으로 결론 내리지 않는다.

정책의 학습 seed와 평가 seed는 역할이 다르다.
학습 seed는 신경망 초기화와 수집 경험 등에 영향을 준다.
평가 seed는 각 정책에 제공할 초기조건을 맞추는 데 사용한다.
같은 평가 seed를 사용하면 baseline과 smooth를 같은 문제에 놓고 비교할 수 있다.

[evaluate_cartpole.py](../examples/evaluate_cartpole.py)는 정책 두 개를 공통된 공식 Cartpole 환경에서 평가한다.
사용자 보상 항 때문에 총 보상 정의가 달라지는 문제를 피하기 위해 물리적인 상태·행동 지표를 비교한다.
관절 이름으로 인덱스를 찾고, 에피소드 종료 후 자동 초기화 전에 마지막 샘플을 기록한다.
끝난 상태 대신 다음 에피소드 초기 상태를 섞으면 넘어짐 직전 오차가 작아 보이는 오류가 생길 수 있다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/evaluate_cartpole.py" \
  --checkpoint "실제_baseline_체크포인트_절대경로.pt" \
  --label baseline --episodes 20 --seed_start 1000 \
  --output "$TUTORIAL_ROOT/isaaclab_tutorial/results/practice_baseline_s42.json"
```

```bash
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/evaluate_cartpole.py" \
  --checkpoint "실제_smooth_체크포인트_절대경로.pt" \
  --label smooth --episodes 20 --seed_start 1000 \
  --output "$TUTORIAL_ROOT/isaaclab_tutorial/results/practice_smooth_s42.json"
```

이 단계는 practice_ 파일명으로 평가를 연습한다. 34단계의 최종 실험 파일명과 구분하여, 기존 파일 때문에 배치 평가가 중단되지 않도록 한다.

이 평가기는 단일 환경에서 에피소드별 seed를 명시하여 비교한다.
학습은 다수 환경으로 빠르게 수행하고 평가에서는 비교 조건을 단순하게 만든다.
GPU 물리 연산과 드라이버 차이까지 비트 단위로 동일하다고 보장하는 것은 아니다.
평가기는 `rsl-rl-lib==5.0.1`을 요구한다. 다른 버전에서 평가하려면 먼저 정책 복원 API와 결과 형식을 다시 검토한다.
기존 출력 파일을 덮어쓰지 않으므로 재평가할 때는 새로운 파일 이름을 지정한다.

| 지표 | 의미 | 좋은 방향 |
|---|---|---|
| 막대 각도 RMS | 흔들림과 기울어짐의 크기 | 작을수록 유리 |
| 카트 누적 이동거리 | 불필요한 왕복 포함 이동량 | 균형 성능을 유지하면서 감소 |
| 명령 힘 RMS | 정책이 요청한 힘의 크기 | 다른 성능을 훼손하지 않으면서 감소 |
| 행동 변화 RMS | 연속 행동이 얼마나 급하게 변하는가 | 작을수록 부드러운 입력 |
| 실패/시간 제한 | 왜 에피소드가 끝났는가 | 실패 감소 |
| 에피소드 길이 | 얼마나 오래 유지했는가 | 단독 성공 지표로 사용하지 않음 |

명령 힘은 실제 접촉력이나 실제 소비 전력을 뜻하지 않는다.
시간 제한 도달률 또한 막대가 서 있었다는 성공률과 다르다.
공식 Manager Cartpole의 종료 조건을 기억하고 막대 각도 지표를 반드시 함께 본다.

**완료 조건:** 동일한 평가 seed 목록으로 얻은 두 JSON 파일과 지표의 단위를 확인한다.

공식 근거: [RSL-RL 재생에서 정책 복원](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/play_rsl_rl.py), [Manager 환경 스텝과 초기화](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/envs/manager_based_rl_env.py).

<a id="step-34"></a>

## 34. 프로젝트 8 — 여러 시드로 보상 설계 비교하기

**만들 결과:** baseline과 smooth를 같은 예산으로 학습하고, 동일한 초기조건으로 평가한 비교 보고서다.

질문을 먼저 적는다.
“행동 변화 비용을 추가하면 막대 균형 성능을 유지하면서 입력의 급격한 변화를 줄일 수 있는가?”
정책을 돌린 뒤 우연히 좋아 보이는 지표를 고르는 대신 무엇을 비교할지 미리 정한다.

실험은 다음 여섯 개 학습으로 구성한다.

| 조건 | 학습 seed | 환경 수 | iteration | 평가 seed |
|---|---|---:|---:|---|
| baseline | 42, 43, 44 | 512 | 150 | 1000–1019 |
| smooth | 42, 43, 44 | 512 | 150 | 1000–1019 |

GPU 메모리가 부족하면 여섯 실행의 환경 수를 모두 같은 값으로 줄인다.
비교 도중 한 조건만 더 오래 학습시키지 않는다.
여기서는 동시에 여섯 프로세스를 띄우지 않고 하나씩 순서대로 실행한다.

```bash
cd "$ISAACLAB_ROOT"
set -euo pipefail
for variant in baseline smooth; do
  for seed in 42 43 44; do
    ./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/train_cartpole_variant.py" \
      --variant "$variant" --mode train --num_envs 512 \
      --max_iterations 150 --seed "$seed" \
      --experiment_name tutorial_cartpole_compare \
      --run_name "${variant}_s${seed}" physics=physx
  done
done
```

각 실행이 정상 완료되면 마지막 체크포인트를 찾고 경로를 기록한다.
모델 번호는 문자열 정렬이 아니라 숫자 iteration으로 확인한다.
`model_99.pt`와 `model_149.pt` 중 전자를 더 최신으로 선택하지 않도록 주의한다.

```bash
find "$ISAACLAB_ROOT/logs/rsl_rl/tutorial_cartpole_compare" \
  -type f -name 'model_*.pt'
```

다음 표의 파일 경로를 실제 결과로 채운다.
이 매핑 자체가 실험 재현에 필요한 데이터다.

```csv
variant,train_seed,checkpoint
baseline,42,/실제/경로/baseline_s42/model_149.pt
baseline,43,/실제/경로/baseline_s43/model_149.pt
baseline,44,/실제/경로/baseline_s44/model_149.pt
smooth,42,/실제/경로/smooth_s42/model_149.pt
smooth,43,/실제/경로/smooth_s43/model_149.pt
smooth,44,/실제/경로/smooth_s44/model_149.pt
```

위 모델 번호도 예시다. 각 학습이 실제로 저장한 마지막 번호를 사용한다.
모든 실행을 완료했다면 33단계 평가를 여섯 체크포인트에 반복한다.
결과 파일은 `baseline_s42.json`부터 `smooth_s44.json`까지 생성한다.
각 명령의 `--episodes 20 --seed_start 1000`은 동일하게 유지한다.

경로 표를 `isaaclab_tutorial/results/checkpoints.csv`로 저장했다면 다음 코드로 여섯 평가를 순서대로 실행할 수 있다.
실제 체크포인트가 하나라도 없으면 해당 위치에서 중단한다.

```bash
cd "$TUTORIAL_ROOT"
python3 - <<'PY'
import csv
import os
from pathlib import Path
import subprocess

root = Path(os.environ["TUTORIAL_ROOT"])
lab = Path(os.environ["ISAACLAB_ROOT"])
result_dir = root / "isaaclab_tutorial/results"
with (result_dir / "checkpoints.csv").open(newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))
expected = {(variant, str(seed)) for variant in ("baseline", "smooth") for seed in (42, 43, 44)}
observed = {(row["variant"], row["train_seed"]) for row in rows}
assert len(rows) == 6 and observed == expected, "두 조건 × 세 학습 seed가 필요하다."
for row in rows:
    checkpoint = Path(row["checkpoint"]).expanduser().resolve()
    assert checkpoint.is_file(), checkpoint
    output = result_dir / f'{row["variant"]}_s{row["train_seed"]}.json'
    subprocess.run([
        str(lab / "isaaclab.sh"), "-p",
        str(root / "isaaclab_tutorial/examples/evaluate_cartpole.py"),
        "--checkpoint", str(checkpoint), "--label", row["variant"],
        "--episodes", "20", "--seed_start", "1000", "--output", str(output),
    ], cwd=lab, check=True)
PY
```

smooth 모델에서 입력 변화가 줄어도 막대 각도 오차나 실패가 크게 늘었다면 trade-off를 보고해야 한다.
한 seed만 좋아진 결과를 전체적인 개선으로 표현하지 않는다.
세 학습 seed도 작은 표본이므로 확정적인 일반화 주장보다 후속 검증의 출발점으로 삼는다.

**완료 조건:** 여섯 체크포인트, 대응 설정, 여섯 평가 파일이 연결되어 있다.

공식 근거: [RSL-RL seed·로그·설정 저장](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/train_rsl_rl.py), [환경 seed 유틸리티](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/utils/seed.py).

<a id="step-35"></a>

## 35. CSV·JSON 결과 해석과 실패 분석하기

**목표:** 실험 결과를 다른 사람이 검토할 수 있는 형태로 남긴다.

먼저 같은 학습 seed의 두 결과를 비교한다.

```bash
cd "$TUTORIAL_ROOT"
python3 isaaclab_tutorial/examples/summarize_evaluations.py \
  isaaclab_tutorial/results/baseline_s42.json \
  isaaclab_tutorial/results/smooth_s42.json \
  --output isaaclab_tutorial/results/comparison_s42.json \
  --csv-output isaaclab_tutorial/results/comparison_s42.csv
```

요약기는 원본 에피소드 기록을 바탕으로 결과를 집계한다.
JSON은 원본 지표·설정·메타데이터를 보관하고 CSV는 표 계산 프로그램에서 비교할 때 사용한다.
값이 없는 측정 항목을 `0`으로 채우면 실제 측정값과 구분되지 않으므로 비어 있거나 미측정임을 나타내야 한다.
실제로 생성한 파일을 열어 지표 이름과 단위를 먼저 확인한다.

학습 seed 간 변동을 볼 때는 먼저 각 학습 결과의 평균을 계산한다.
그다음 세 학습 결과의 평균과 변동을 비교한다.
같은 정책에서 얻은 여러 에피소드를 서로 독립적인 학습 결과 20개처럼 세지 않는다.

먼저 세 학습 seed 모두에 대해 비교 파일을 만든다.

```bash
for seed in 42 43 44; do
  python3 isaaclab_tutorial/examples/summarize_evaluations.py \
    "isaaclab_tutorial/results/baseline_s${seed}.json" \
    "isaaclab_tutorial/results/smooth_s${seed}.json" \
    --output "isaaclab_tutorial/results/comparison_s${seed}.json" \
    --csv-output "isaaclab_tutorial/results/comparison_s${seed}.csv"
done
```

다음 명령은 실제 비교 파일에서 학습 seed별 평균을 읽어 다시 집계한다.
JSON과 CSV로 저장하므로 복사해서 수치를 옮길 필요가 없다.

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path
from statistics import mean, stdev

folder = Path("isaaclab_tutorial/results")
reports = [json.loads((folder / f"comparison_s{seed}.json").read_text()) for seed in (42, 43, 44)]
rows = []
for metric in reports[0]["metrics"]:
    for condition in ("reference", "candidate", "paired_delta"):
        values = [report["metrics"][metric][condition]["mean"] for report in reports]
        rows.append({
            "metric": metric, "condition": condition, "train_seeds": "42,43,44",
            "mean_of_seed_means": mean(values), "sample_std_across_train_seeds": stdev(values),
        })
(folder / "across_train_seeds.json").write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
with (folder / "across_train_seeds.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps(rows, indent=2))
PY
```

지표가 기대와 다를 때는 다음 순서로 확인한다.

| 관찰 | 먼저 확인할 항목 | 다음 실험 |
|---|---|---|
| 두 조건이 거의 같다 | smooth reward가 실제 cfg에 저장되었는가 | 가중치 하나만 조금 변경 |
| smooth가 거의 움직이지 않는다 | 행동 변화 비용이 지나치게 큰가 | 비용을 줄이고 동일 seed 재학습 |
| 학습 때 좋고 평가 때 나쁘다 | 관측·action scale·초기화 분포가 같은가 | 동일 cfg에서 정책 복원 검사 |
| 한 seed만 매우 좋다 | 학습 부족·초기화 민감도 | 학습 seed 추가 |
| 힘이 줄었는데 막대가 기울어 있다 | 목표 성능 희생 여부 | 각도 오차를 우선 제약으로 설정 |
| 영상만 검고 지표는 정상이다 | 렌더러·조명·카메라 경로 | 단일 환경 GUI 촬영 재검사 |
| 관절 상태가 NaN이다 | 물리 설정·reset·행동 범위 | 학습 중단 후 앞 장 물리 검증 |

보고서에는 좋아진 값뿐 아니라 나빠진 값과 미측정 항목도 남긴다.
학습이 실패한 실행을 말없이 지우고 성공한 시드만 모으면 재현 가능한 비교가 되지 않는다.

**완료 조건:** 표로 비교할 CSV와 원본을 추적할 JSON, 지표별 해석을 작성한다.

공식 근거: [공식 설정 저장·로그 구조](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/reinforcement_learning/rsl_rl/train_rsl_rl.py).

<a id="step-36"></a>

## 36. 최종 검증 보고서와 다음 실험 설계하기

**목표:** 무엇을 실제로 확인했는지 명확하게 말할 수 있는 상태로 프로젝트를 마친다.

아래 틀을 복사해 자신의 GPU에서 실행한 결과로 채운다.
체크하지 않은 항목에는 미실행이라고 적는다.
코드 문법 검사와 GPU 물리·렌더링 검사는 서로 다른 검증이다.

```text
실험 제목:
실행 날짜:
Ubuntu / 커널:
GPU / VRAM / 드라이버:
Isaac Lab 태그 / commit SHA:
Isaac Sim 버전:
RSL-RL / torch 버전:
물리 백엔드 / 렌더러 / visualizer:

[장면과 물리]
공식 자산 로딩:
관절 이름·개수 확인:
바닥 접촉과 초기 자세:
반복 reset 이후 상태:
관측·행동·보상의 NaN/Inf:

[렌더링과 센서]
GUI 화면:
센서 shape / dtype / 유효값:
단일 환경 영상:
반복 reset 이후 센서 갱신:

[학습과 평가]
학습 seed / 환경 수 / iteration:
체크포인트와 설정 파일:
평가 seed 목록 / 에피소드 수:
막대 각도·이동거리·명령 힘·행동 변화:
실패 종료·시간 제한:
학습 seed 간 변동:

[결론]
질문에 대한 답:
개선된 점:
나빠진 점:
미실행·미측정 항목:
다음 실험에서 바꿀 항목 하나:
```

설치와 버전을 기록하는 명령은 다음과 같다.

```bash
cd "$ISAACLAB_ROOT"
git describe --tags --always
git rev-parse HEAD
nvidia-smi
./isaaclab.sh -p -c 'import importlib.metadata as m; print({n:m.version(n) for n in ("isaacsim", "rsl-rl-lib", "torch")})'
```

비교가 끝나면 더 복잡한 로봇으로 확장할 수 있다.
Franka에서는 말단 오차와 관절 움직임의 부드러움을 함께 평가하고,
ANYmal에서는 속도 추종 오차·넘어짐·발 접촉·토크 요청을 함께 평가한다.
Cartpole의 좋은 가중치를 단위와 주기가 다른 로봇에 그대로 옮기지 않는다.
카메라 입력, 모방학습, Sim-to-Real도 관측·행동·시간 규약과 평가 절차를 유지한 상태에서 한 요소씩 추가한다.

이 단계까지 완료했다면 단순히 학습 명령을 실행한 것을 넘어,
환경의 물리와 센서를 확인하고 정책을 학습하며 보상 변경의 효과를 비교하는 기본 연구 흐름을 수행한 것이다.

**최종 완료 조건:** 실행한 결과만 담은 검증 보고서와 재현 가능한 학습·평가 파일 묶음을 남긴다.

공식 근거: [Isaac Lab 고정 태그](https://github.com/isaac-sim/IsaacLab/tree/v3.0.0-beta2.patch1), [해당 릴리스 공지](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1).
