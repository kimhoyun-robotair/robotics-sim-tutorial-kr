# Isaac Lab과 로봇 학습

Isaac Lab은 Isaac Sim의 새 이름이 아니다. Isaac Sim이 physics·rendering·sensor·USD runtime을 제공한다면, Isaac Lab은 그 위에 vectorized environment, robot·sensor configuration, task, observation/action/reward, domain randomization, RL framework 연결을 제공하는 별도 오픈소스 framework이다.

## 언제 Isaac Lab을 사용하다

| 목표 | 선택 |
| --- | --- |
| 한 대 로봇의 sensor와 ROS 2 integration을 만들다. | Isaac Sim Core API/ROS 2 Bridge를 우선하다. |
| 수백~수천 환경에서 locomotion/manipulation policy를 학습하다. | Isaac Lab을 사용하다. |
| 학습된 policy를 photorealistic scene이나 ROS 2에서 시연하다. | Isaac Lab에서 학습하고 Isaac Sim에 배포하다. |
| USD asset을 rigging하고 joint gain을 맞추다. | 먼저 Isaac Sim Robot Setup 도구를 사용하다. |

## task 구성 mental model

```text
Scene config
  ├─ robot / object / terrain / sensor
  ├─ observation terms
  ├─ action terms
  ├─ reward terms
  ├─ termination terms
  ├─ event·randomization terms
  └─ curriculum terms
```

학습을 시작하기 전에 single environment에서 다음을 확인하다.

- joint 순서와 action scale이 실제 actuator 의미와 일치하다.
- observation 단위와 normalization이 명시되어 있다.
- reward 각 항의 평균·분산과 지배 항을 log로 볼 수 있다.
- reset 뒤 penetration이나 폭발적인 contact impulse가 없다.
- training simulation step과 policy decimation이 의도한 control rate를 만들다.

## 설치 경계를 지키다

Isaac Sim 5.1.0에는 **Isaac Lab v2.3.2**를 고정하다. 최신 Isaac Lab `main`은 Isaac Sim 6.0 계열을 대상으로 하므로 이 과정에 섞지 않다. 또한 v2.3.2의 General Requirements는 Linux 기준 Ubuntu 22.04 x86_64를 명시한다. 따라서 이 과정의 Ubuntu 24.04 호스트에서 Isaac Sim 본편은 공식 지원 범위이지만, Isaac Lab v2.3.2 네이티브 학습은 공식 검증 범위 밖이다. 재현성이 필요하면 Lab 학습만 v2.3.2 공식 Docker/Ubuntu 22.04 환경에서 실행하고 checkpoint를 5.1 배포 scene으로 가져오다.

```bash
git clone --branch v2.3.2 --depth 1 \
  https://github.com/isaac-sim/IsaacLab.git "$HOME/IsaacLab-v2.3.2"
export ISAACLAB_PATH="$HOME/IsaacLab-v2.3.2"
```

설치 후 제공되는 환경 목록·zero action·random action smoke test를 먼저 실행하고, 그 다음 학습 framework를 연결하다.

```bash
# 실제 경로와 launcher 이름은 선택한 Isaac Lab 릴리스 문서를 따르다.
cd "$ISAACLAB_PATH"
export TASK_ID="Isaac-Cartpole-v0"
./isaaclab.sh -p scripts/environments/list_envs.py
./isaaclab.sh -p scripts/environments/zero_agent.py --task "$TASK_ID" --num_envs 16
./isaaclab.sh -p scripts/environments/random_agent.py --task "$TASK_ID" --num_envs 16
```

이 명령은 workflow 예시이다. repository tag의 실제 script 경로를 확인한 뒤 사용하다.

## policy를 Isaac Sim에 배포하다

학습 checkpoint만 옮기면 충분하지 않다. 다음 contract를 함께 고정하다.

```yaml
policy_contract:
  checkpoint_sha256: "..."
  joint_order: [joint_1, joint_2]
  observation_order: [base_ang_vel, projected_gravity, joint_pos, joint_vel]
  action_scale: 0.5
  control_hz: 50
  normalization: "training_config.yaml"
  default_pose: [0.0, 0.0]
```

Isaac Sim의 `isaacsim.robot.policy.example`은 H1 humanoid와 Spot quadruped 등 Isaac Lab에서 학습한 policy 배포 예를 제공하다. 실제 커스텀 policy는 observation 계산, joint order, history, clip, decimation을 학습 환경과 동일하게 구현하다.

ROS 2로 policy를 실행할 때는 inference node가 simulation time을 사용하는지, sensor topic QoS와 latency가 학습 가정에 맞는지 확인하다. 시뮬레이션이 일시 정지한 동안 wall-clock timer만 진행하면 observation과 action이 어긋나다.

## 성능과 asset 최적화

병렬 환경은 reference/instanceable asset과 Cloner를 이용해 memory를 줄이다. 모든 prim을 instanceable로 만들 수 있는 것은 아니며, instance 내부를 environment별로 직접 수정해야 하는 randomization과 충돌할 수 있다. geometry·material처럼 공유 가능한 부분과 articulation state처럼 환경별인 부분을 분리하다.

## 출처

- [Isaac Lab](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/index.html)
- [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)
- [Running a Reinforcement Learning Policy through ROS 2 and Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rl_controller.html)
- [Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
- [Isaac Lab v2.3.2 문서](https://isaac-sim.github.io/IsaacLab/v2.3.2/)
- [Isaac Lab v2.3.2 설치와 요구사항](https://isaac-sim.github.io/IsaacLab/v2.3.2/source/setup/installation/index.html)
- [Isaac Lab v2.3.2 소스](https://github.com/isaac-sim/IsaacLab/tree/v2.3.2)
