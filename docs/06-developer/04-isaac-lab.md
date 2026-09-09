# Isaac Lab의 역할과 로봇 학습 입문

Isaac Lab은 Isaac Sim의 새 이름이 아니다. Isaac Sim은 물리·렌더링·센서와 USD 실행 환경을 제공한다. Isaac Lab은 그 위에서 여러 학습 환경을 함께 실행하고, 관측·행동·보상·초기화와 강화학습 라이브러리를 연결하는 프레임워크이다.

## 1. 언제 Isaac Lab이 필요한가

| 목표 | 시작할 도구 |
| --- | --- |
| 로봇 한 대에 센서를 붙이고 ROS 2와 연결 | Isaac Sim GUI/Core API/ROS 2 Bridge |
| 로봇 관절 축과 충돌 형상 수정 | Isaac Sim Robot Setup |
| 수백 개 환경에서 같은 정책 학습 | Isaac Lab |
| 학습한 정책으로 로봇을 제어하고 센서 확인 | Isaac Lab 학습 결과 + Isaac Sim 배포 코드 |

센서 토픽을 발행하거나 키보드로 로봇을 움직이는 데 강화학습이 반드시 필요한 것은 아니다. 먼저 Isaac Sim에서 로봇이 안정적으로 움직이는지 확인하고, 학습할 문제가 분명할 때 Lab을 연결한다. [Isaac Lab 소개](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/index.html)

## 2. 버전과 설치 환경부터 구분하기

이 과정에서는 **Isaac Lab v2.3.2**를 사용한다. 다른 릴리스의 `main`이나 최신 설치 명령을 섞지 않는다. Lab 문서의 해당 버전 요구사항은 Linux x64의 Ubuntu 22.04와 Isaac Sim 5.x의 Python 3.11을 명시한다. 따라서 이 튜토리얼의 Ubuntu 24.04에서 Isaac Sim 본편을 실행하는 것과, Lab v2.3.2 학습 환경의 공식 요구사항을 만족하는 것은 구분해야 한다. [v2.3.2 설치 요구사항](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/index.html)

Ubuntu 24.04 호스트를 유지하면서 요구사항을 맞추려면 Lab 학습은 별도의 Ubuntu 22.04 환경 또는 해당 버전의 공식 컨테이너 절차로 구성한다. 아래 명령은 **Lab 설치 환경 안에서** 실행하는 순서이다. 호스트의 ROS 2 Jazzy Python 패키지를 Lab의 Python 3.11 환경에 복사하지 않는다.

```bash
git clone --branch v2.3.2 --depth 1 \
  https://github.com/isaac-sim/IsaacLab.git "$HOME/IsaacLab-v2.3.2"
cd "$HOME/IsaacLab-v2.3.2"
git describe --tags --exact-match
```

출력은 `v2.3.2`여야 한다. 그 환경에 설치된 Isaac Sim 5.1.0의 경로를 지정하고 연결한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
ln -s "$ISAACSIM_PATH" _isaac_sim
```

`_isaac_sim`이 이미 있으면 먼저 `readlink -f _isaac_sim`으로 가리키는 위치를 확인한다. 다른 설치본을 가리킨다고 강제로 덮어쓰지 않는다. Conda가 설치된 별도 학습 환경에서는 다음 순서로 환경과 학습 라이브러리를 준비한다.

```bash
./isaaclab.sh -c isaaclab-232
conda activate isaaclab-232
source _isaac_sim/setup_conda_env.sh
./isaaclab.sh -i rsl_rl
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
```

`create_empty.py`는 비어 있는 장면을 실행한다. 볼 물체와 조명이 없는 검은 Viewport는 이 단계에서는 예상 결과이다. 앞 장의 조명과 큐브가 있는 카메라 실습에서 영상이 검게 나오는 현상과 구분한다. 설치 링크와 환경 설정의 의미는 [Pre-built Binaries 설치 절차](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/binaries_installation.html)를 따른다.

## 3. 학습 전에 환경 하나를 검사하기

```bash
./isaaclab.sh -p scripts/environments/list_envs.py
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 1
```

목록에서 `Isaac-Cartpole-v0`를 확인한 뒤 실행한다. Cartpole은 이동하는 카트 위의 막대를 세우는 문제이다. Zero agent는 행동값을 0으로 보내므로 막대가 넘어질 수 있다. 이것은 로봇 모델이 분해되는 오류와 다르다. 카트와 막대가 관절로 연결된 채 움직이고, 종료 조건에 도달하면 정상적으로 reset되는지 본다.

다음으로 무작위 행동을 실행한다.

```bash
./isaaclab.sh -p scripts/environments/random_agent.py \
  --task Isaac-Cartpole-v0 --num_envs 1
```

각 실행을 종료한 뒤 다음 명령을 실행한다. 처음부터 수천 개 환경을 만들면 로봇 하나의 축, 관절, 초기화 문제를 찾기 어렵다. 한 환경이 정상이면 16개로 늘리고, 환경끼리 겹치거나 충돌하지 않는지 확인한다.

## 4. 학습 과제의 구성 요소 이해하기

| 요소 | 질문 | Cartpole에서 생각할 예 |
| --- | --- | --- |
| Scene | 무엇을 시뮬레이션하는가 | 카트, 막대, 관절 |
| Observation | 정책은 무엇을 입력받는가 | 카트 위치/속도, 막대 각도/각속도 |
| Action | 정책 출력은 무엇을 뜻하는가 | 카트에 작용하는 힘 |
| Reward | 무엇을 잘했다고 평가하는가 | 막대를 세우고 위치를 유지 |
| Termination | 언제 실패 또는 종료인가 | 막대가 너무 기울거나 카트가 범위를 벗어남 |
| Reset | 다음 시도를 어떻게 시작하는가 | 작은 초기 상태 변화와 속도 초기화 |
| Decimation | 행동 한 번 동안 물리가 몇 step 진행되는가 | 물리 주기와 정책 주기의 비율 |

예를 들어 물리가 200 Hz이고 decimation이 4라면 정책은 50 Hz로 실행된다.

```python
physics_dt = 1.0 / 200.0
decimation = 4
policy_dt = physics_dt * decimation
print("policy_hz:", 1.0 / policy_dt)  # 50.0
```

관측 순서가 바뀌거나 각도를 degree로 바꾸면 숫자 배열 크기가 같아도 다른 입력이 된다. 보상값이 증가한다고 물리 모델이 올바른 것도 아니다. reset 직후의 관통, 과도한 접촉 힘, 잘못된 관절 방향을 먼저 확인한다.

## 5. 짧게 학습하고 결과 재생하기

다음 명령은 학습 파이프라인이 연결되는지 확인하는 짧은 실행이다. 정책의 최종 성능을 보장하는 학습 횟수가 아니다.

```bash
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task Isaac-Cartpole-v0 --num_envs 64 --max_iterations 50 --headless
```

완료 후 `logs/rsl_rl` 아래에서 checkpoint를 확인한다.

```bash
rg --files logs/rsl_rl -g '*.pt'
```

출력된 실제 checkpoint 경로를 지정해 한 환경에서 재생한다.

```bash
export POLICY_CHECKPOINT="logs/rsl_rl/실행폴더/model_49.pt"
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task Isaac-Cartpole-v0 --num_envs 1 --checkpoint "$POLICY_CHECKPOINT"
```

로그 폴더와 마지막 파일 번호는 실제 출력으로 확인한다. 예시 경로를 그대로 쓰지 않는다. 짧은 학습에서 막대가 잘 서지 않으면 보상 곡선, 종료 사유, 학습 횟수를 확인하며, 관절 연결 오류와 정책 성능 문제를 구분한다.

## 6. 학습 정책을 Isaac Sim으로 가져오기

checkpoint만 옮기면 충분하지 않다. 다음 정보가 학습 당시와 같아야 한다.

```yaml
policy_contract:
  isaac_sim: 5.1.0
  isaac_lab: v2.3.2
  checkpoint_sha256: "실제 파일의 SHA-256"
  observation_order: [cart_position, cart_velocity, pole_angle, pole_velocity]
  action_meaning: cart_force
  action_unit: newton
  observation_normalization: "학습 때 저장한 정규화 설정"
  physics_dt: "학습 설정에서 읽은 값"
  decimation: "학습 설정에서 읽은 값"
```

위 YAML은 확인할 항목의 예이며, Cartpole 환경의 실제 관측 순서와 정규화는 선택한 task 설정에서 읽어 기록한다. 이름만 보고 배열 순서를 추측하지 않는다. 다관절 로봇은 joint 이름, 순서, 기본 자세, action scale, 제한값까지 저장해야 한다.

NVIDIA의 [Policy Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)는 학습된 정책의 로봇 배포 예를 제공한다. ROS 2로 추론을 분리할 때는 simulation time, 센서 timestamp, QoS와 지연도 함께 맞춘다. Pause 중 wall-clock 타이머만 진행하면 오래된 관측에 행동을 계속 보낼 수 있다.

## 7. 환경 수를 늘리기 전 확인할 것

정책 입력에 NaN/Inf가 없고, 관절 순서가 맞으며, reset 뒤 물체가 겹치지 않는지 확인한다. 한 환경과 여러 환경에서 같은 설정의 동작이 일관적인지도 본다. 이후 Cloner와 instanceable asset으로 공유 가능한 형상·재질의 메모리 사용을 줄인다. 환경마다 바뀌는 관절 상태와 공유하는 형상을 구분해야 한다.

이 저장소의 정적 검사는 강화학습의 수렴이나 GPU 메모리 한계를 검증하지 않는다. Lab 학습은 별도 환경에서 수행하고 설치 버전, 로그, checkpoint와 재생 결과를 함께 기록한다.

## 출처

- [Isaac Lab v2.3.2 문서](https://isaac-sim.github.io/IsaacLab/v2.3.2/)
- [Isaac Lab v2.3.2 소스](https://github.com/isaac-sim/IsaacLab/tree/v2.3.2)
- [Policy Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)
- [ROS 2 RL Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html)
- [Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
