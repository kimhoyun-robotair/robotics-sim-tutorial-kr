# 05 — Parallel Robot Policy Evaluation Lab

## Goal / Architecture / Execution Context

**Isaac Sim 5.1.0 · Standalone Python.** `GridCloner`로 Spot과 바닥을 여러 개 복제하고, NVIDIA가 배포한 학습된 `SpotFlatTerrainPolicy`를 각각 실행합니다. 각 환경의 마찰을 바꾸고 실제 이동·자세·속도를 평가합니다.

```text
Env_0 / Spot ─ policy ─ floor μ0 ─ result 0
Env_1 / Spot ─ policy ─ floor μ1 ─ result 1
...                  같은 World에서 stepping
```

정책 학습은 하지 않습니다. observation 구성·action scaling·joint 순서·decimation은 배포된 Spot wrapper가 담당합니다. 임의의 TorchScript checkpoint를 이 wrapper에 넣으면 호환된다고 가정하면 안 됩니다. Isaac Lab 연결은 정책과 함께 배포된 environment 설정을 이해하는 수준에서 시작합니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Reinforcement Learning Policies Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html)
- NVIDIA Isaac Sim 5.1 — [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)

## Dependencies / How to Run

Isaac Sim에 포함된 torch와 policy extension을 사용합니다. 별도 Isaac Lab checkout이나 policy training은 필요 없습니다. 첫 실행은 robot USD, policy `.pt`, environment `.yaml`에 접근할 수 있어야 합니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --headless --num-envs 4
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --num-envs 4 --render-every 10
```

## USD Assets / Robot Model / Physics Configuration / APIs Used

| 항목 | 설정 |
|---|---|
| Robot USD | `/Isaac/Robots/BostonDynamics/spot/spot.usd` |
| Policy / config | `/Isaac/Samples/Policies/Spot_Policies/spot_policy.pt`, `spot_env.yaml` |
| Scene | `/World/envs/env_i/Robot`, `/World/envs/env_i/Floor` |
| Cloning | `GridCloner`, 12m 간격, `copy_from_source=True` |
| Collision | `filter_collisions`로 환경 간 충돌 제외 |
| Floor | 10×10m, 정적 cuboid, 마찰 0.3–1.2를 seed로 sample |
| Physics dt | 1/500초, 공식 Spot standalone 예제와 동일 |
| Warm-up | 250 physics steps, command 0 |
| Evaluation | 기본 2500 steps, +X 0.3m/s command |
| Rendering | headless에서는 loop rendering 생략, GUI는 기본 10 step마다 |

복제 후 각 바닥에 독립적인 `PhysicsMaterial`을 bind합니다. robot 전체를 USD instance로 만들지 않습니다. 관절별 상태를 다르게 제어해야 하기 때문입니다. asset 자체의 mesh instancing은 유지합니다. 이 예제에서는 per-environment material 구성을 단순하게 유지하려고 `replicate_physics=False`를 사용합니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Getting Started with Cloner](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_cloner.html)
- NVIDIA Isaac Sim 5.1 — [Cloner API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.cloner/docs/index.html)
- NVIDIA Isaac Sim 5.1 — [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
- NVIDIA 공식 v5.1.0 소스 — [Spot standalone](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/standalone_examples/api/isaacsim.robot.policy.examples/spot_standalone.py)

## 결과 / 공부 순서

1. [evaluate.py](evaluate.py)의 source env → clone → material → policy initialize 순서로 읽습니다.
2. world 좌표에서 clone origin을 빼서 env-local 좌표를 기록하는 곳을 확인합니다.
3. [metrics.py](metrics.py)에서 이동거리·기울기와 성공 판정을 읽습니다.

`trajectory.csv`는 env별 위치, 속도, 마찰, 자세, 낙상 여부를 기록합니다. `summary.json`의 `completed`는 평가 loop 완료이고, 각 `results[].success`는 **전체 step 실행 + 낙상 없음 + command 기준 기대 전진거리의 50% 이상 이동**입니다. 낙상 기준은 base 높이 0.25m 미만 또는 local Z축의 world Z 방향 성분이 0.5 미만인 상태입니다. 한 번의 낙상도 최종 판정에 남깁니다.

이 판정은 프로젝트에서 정한 교육용 기준입니다. `success: false`도 평가 결과입니다. command 속도와 실제 속도가 다르다고 결과를 성공으로 바꾸지 않습니다. 짧은 2초 테스트에서는 두 로봇 모두 넘어지지 않았지만 기대 속도 기준은 통과하지 못했습니다.

## Performance / Known Limitations / 실험

`timing_s`는 policy+control, physics+render, 상태 읽기+logging 구간의 wall time입니다. `env_steps_per_second`는 `환경 수 × 완료 step 수 / 평가 wall time`, real-time factor는 한 환경의 simulation duration / wall time입니다. 초기 asset 로딩·warm-up은 제외합니다. CPU/GPU 전체를 정밀 profiling한 결과가 아니므로 세 구간을 병목 후보로 해석하세요.

**적용한 최적화:** sensor가 없는 headless 평가에서 rendering을 생략하고, GUI에서도 rendering 빈도를 줄였습니다. 아래 비교는 다른 simulator·GPU 작업을 종료한 후 같은 seed/환경 수/steps로 실행하세요.

```bash
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --num-envs 4 --render-every 1 --output outputs/policy_render1
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --num-envs 4 --render-every 10 --output outputs/policy_render10
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --num-envs 4 --headless --output outputs/policy_headless
```

물리는 복제 환경을 한 World에서 처리하지만 Python의 policy 호출은 env별 순차 실행입니다. **GPU batched inference 구현은 아닙니다.** 큰 N에서는 이 부분과 중복 policy 로딩이 병목이 될 수 있습니다. 기본 지형은 평지이며 terrain randomization·별도 Isaac Lab 학습·새 checkpoint 연결은 확장 과제입니다. 바닥 이탈을 줄이기 위해 command distance가 4m를 넘는 설정은 거부합니다.

실험: N=1/4/16의 처리량 → rendering 빈도 → log 주기 → 마찰과 tracking error 관계 순서로 한 항목씩 비교하고, 다음에 최적화할 구간을 기록하세요.

### Sources

- NVIDIA Isaac Sim 5.1 — [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
- NVIDIA Isaac Sim 5.1 — [Deploying Policies in Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html)
