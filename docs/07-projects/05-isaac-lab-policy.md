# 프로젝트 5: Isaac Lab policy 학습과 Isaac Sim 배포

## 목표

커스텀 robot task를 Isaac Lab의 vectorized environment로 구성하고 policy를 학습하다. 평가에서 domain randomization 효과를 분석한 뒤 checkpoint를 Isaac Sim scene에 배포하고 선택적으로 ROS 2 command/telemetry를 연결하다.

## 범위 선택

다음 중 하나를 고르다.

- 4족 또는 humanoid의 속도 명령 추종
- 이동 robot의 local obstacle avoidance
- manipulator의 reach 또는 lift

처음에는 기존 5.1 호환 task를 복제해 observation 한 항과 reward 한 항만 바꾸다. 새 robot, 새 task, 새 RL algorithm을 한 번에 바꾸지 않다.

## 1단계: 호환성과 baseline을 고정하다

Isaac Sim 5.1.0에는 Isaac Lab v2.3.2를 고정하다. 최신 `main`은 Isaac Sim 6.0 계열이므로 사용하지 않다. v2.3.2의 공식 Linux 요구사항은 Ubuntu 22.04 x86_64를 명시하므로, 이 과정의 Ubuntu 24.04 호스트에서 Lab 네이티브 학습은 공식 검증 범위 밖이다. 재현 평가에서는 Lab v2.3.2 공식 Docker 또는 Ubuntu 22.04 학습 환경을 사용하고 checkpoint를 5.1 배포 scene으로 옮기다. commit SHA, Python environment, GPU, driver를 기록하다.

```bash
cd "$ISAACLAB_PATH"
git rev-parse HEAD
export TASK_ID="Isaac-Cartpole-v0"
./isaaclab.sh -p scripts/environments/list_envs.py
./isaaclab.sh -p scripts/environments/zero_agent.py \
  --task "$TASK_ID" --num_envs 16
./isaaclab.sh -p scripts/environments/random_agent.py \
  --task "$TASK_ID" --num_envs 16
```

script 경로는 선택한 Isaac Lab tag에서 확인하다. zero/random agent가 안정적으로 reset되지 않으면 학습을 시작하지 않다.

## 2단계: task contract를 작성하다

```yaml
task_contract:
  physics_dt: 0.005
  policy_dt: 0.02
  episode_seconds: 20
  observations:
    - base_angular_velocity
    - projected_gravity
    - command
    - joint_position_error
    - joint_velocity
    - previous_action
  actions:
    type: joint_position_offset
    scale: 0.5
  terminations:
    - timeout
    - illegal_contact
    - base_height
```

각 observation의 shape, 단위, frame, normalization을 표로 남기다. reward는 이름과 weight만 기록하지 말고 episode 동안 항별 mean을 log하다.

## 3단계: 작은 환경에서 debug하다

1. `num_envs=1`, rendering on으로 joint 방향과 contact를 보다.
2. deterministic command에서 reward sign과 termination을 unit test하다.
3. `num_envs=16` random agent로 NaN과 reset leak를 찾다.
4. 그 다음에만 수백~수천 environment로 확장하다.

## 4단계: 학습과 평가를 분리하다

```bash
TRAIN_SCRIPT="scripts/reinforcement_learning/rsl_rl/train.py"
test -f "$TRAIN_SCRIPT"
./isaaclab.sh -p "$TRAIN_SCRIPT" \
  --task "$TASK_ID" \
  --num_envs 1024 \
  --seed 1 \
  --headless
```

seed를 최소 세 개 사용하고 best training reward 하나만 보고하지 않다. held-out terrain/material/mass에서 deterministic evaluation을 실행하다. randomization on/off의 성능과 실패 유형을 비교하다.

## 5단계: Isaac Sim에 배포하다

checkpoint와 함께 다음 deployment contract를 export하다.

```json
{
  "joint_order": ["joint_a", "joint_b"],
  "observation_order": ["base_ang_vel", "gravity", "command", "q", "qd", "last_action"],
  "action_scale": 0.5,
  "control_hz": 50,
  "clip_observation": 100.0,
  "clip_action": 1.0,
  "checkpoint_sha256": "..."
}
```

Isaac Sim deployment scene에서 observation을 같은 frame·순서·단위로 계산하다. policy output을 joint name 기준으로 reorder하고, NaN·limit 초과·stale sensor가 발생하면 safe action으로 전환하다.

ROS 2를 연결하면 command input과 telemetry만 bridge하고 physics state 전체를 무분별하게 publish하지 않다. `/clock`과 inference timer가 simulation time을 따르는지 pause/resume test를 수행하다.

## 완료 조건

- training config와 evaluation config가 분리되다.
- seed별 metric과 confidence interval 또는 분포를 보고하다.
- unseen parameter 조합에서 baseline 대비 개선/악화를 분석하다.
- deployment scene에서 10분 이상 안정성 test를 통과하다.
- joint/observation order를 일부러 바꾼 negative test가 실패를 검출하다.

## 확장 과제

instanceable asset과 Cloner 적용 전후 memory와 step throughput을 비교하다. synthetic sensor noise와 실제 rosbag 통계의 차이를 이용해 randomization 범위를 다시 정하다.

## 출처

- [Isaac Lab](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/index.html)
- [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)
- [Running a Reinforcement Learning Policy through ROS 2 and Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html)
- [Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
- [Isaac Lab v2.3.2 요구사항과 설치](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/index.html)
