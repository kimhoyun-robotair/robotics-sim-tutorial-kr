# 165. t003 · 학습된 H1 정책을 Isaac Sim으로 옮기기

권장 학습 순서 **165** · 병렬 환경과 학습 정책 활용 · 출처 ID `t003`

이 패키지는 Isaac Sim **5.1.0**에 설치된 `H1FlatTerrainPolicy`로 실제 추론을 실행하고, 입력 관측값·관절 순서·출력 행동·월드 위치를 기록한다. 정책 학습을 흉내 내지 않는다. 공식 문서의 배포 과정을 재현 가능한 단일 로봇 실험으로 구성했다. 다른 로컬 패키지의 코드나 설명을 먼저 읽을 필요가 없다.

## 이 실습의 의도

학습된 H1 보행 정책이 관측 배열을 받아 관절 목표 위치를 내보내는 과정을 단일 로봇에서 확인한다. 평평한 바닥과 일정한 전진 명령을 사용하는 이유는 장면 복잡도보다 관절 순서·관측 구성·제어 주기가 학습 당시 계약과 맞는지 살펴보기 위해서다. 기본 실행은 설치된 정책의 추론과 실제 위치 기록까지 수행하며, 새 정책을 학습하지 않는다.

## 실행 후 확인할 것

- **H1 자세와 이동:** GUI에서 `/World/H1`이 바닥에 지지된 채 기본 전진 명령 0.5 m/s에 반응하는지 본다. 종료 후 `trace.csv`의 `x_m`, `y_m`, `z_m`을 함께 읽는다. X 이동만 있어도 넘어져 미끄러진 결과일 수 있으므로 몸통 높이와 화면을 함께 판단한다.
- **입출력 계약:** `contract.json`의 `joint_names`와 `last_action`이 각각 19개, `first_observation`이 69개인지 확인한다. `first_observation[9:12]`는 기본 `[0.5, 0, 0]` 명령이며, 관절 이름은 개수뿐 아니라 순서까지 학습 설정과 대조한다.
- **정책 주기:** 같은 파일의 `physics_dt`, `decimation`, `policy_hz`가 `1 / (physics_dt × decimation)` 관계인지 확인한다. GUI 렌더 속도와 정책 추론 빈도는 별개다.
- **기록 완료 시점:** `trace.csv`는 실행 중 작성하고 `contract.json`은 시뮬레이션 루프가 끝난 뒤 작성한다. GUI를 닫거나 `--steps`만큼 실행한 후 최종 보고서를 확인하며, 첫 추론 전에 닫았다면 CSV만 남을 수 있다. 파일 생성이나 유한 횟수 종료 자체는 안정 보행의 판정이 아니다.

## 준비와 실행

RTX GPU/드라이버, Isaac Sim 5.1 워크스테이션 설치, 5.1 Isaac 자산 접근이 필요하다. 이하 `ISAAC_SIM`은 자신의 설치 디렉터리다. 일반 Python은 `--help`만 실행할 수 있다. 자산 서버 대신 로컬 자산 팩을 사용하는 경우 Isaac Sim의 자산 루트를 먼저 설정한다. 런타임이 사용하는 자산은 `/Isaac/Robots/Unitree/H1/h1.usd`, `/Isaac/Samples/Policies/H1_Policies/h1_policy.pt`, 같은 디렉터리의 `h1_env.yaml`이다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/165_motion_policy_deployment
"$ISAAC_SIM/python.sh" run.py --speed 0.5
# 화면 없이 별도 결과에 기록
"$ISAAC_SIM/python.sh" run.py --headless --steps 1200 --output output/headless
```

`output/trace.csv`는 실제 월드 위치를 기록하고 `contract.json`은 첫 관측과 마지막 행동, 기본 관절 위치를 기록한다. 기존 결과 파일은 덮어쓰지 않는다. 1,200 physics step은 기본 설정에서 6초이며 렌더 프레임 수와 다르다.

`--steps`를 생략하면 GUI에서 사용자가 창을 닫을 때까지 시뮬레이션을 계속합니다. `--steps 1200`처럼 횟수를 지정하면 자동 종료합니다. `--headless` 실행에서 생략하면 1200회로 제한됩니다.


## 직접 해보기

1. 기본 명령을 실행한다. 바닥 위 H1이 +X 방향으로 움직이는지 관찰한다. 마지막 자세가 출력되어도 보행 성공이 자동 보장되지는 않는다. 넘어짐은 CSV의 몸통 `z_m`와 화면에서 함께 판단한다.
2. `contract.json`의 `joint_names`가 19개이고 `first_observation`이 69개인지 확인한다. 관절 이름의 **순서까지** 학습 시 순서와 같아야 한다.
3. 관측 배열을 `[0:3]` 몸체 좌표 선속도, `[3:6]` 각속도, `[6:9]` 몸체 좌표 중력 방향, `[9:12]` 명령, `[12:31]` 기본 자세 대비 관절 위치, `[31:50]` 관절 속도, `[50:69]` 이전 행동으로 나누어 읽는다. 중력 방향은 정규화된 벡터이며 `-9.81` 가속도 값 자체가 아니다.
4. `physics_dt`, `decimation`, `policy_hz`를 비교한다. 물리가 200 Hz이고 decimation이 4이면 추론은 50 Hz다. 정확한 값은 실제로 읽힌 환경 파일을 따른다.
5. `--speed 0.2 --output output/slow`만 바꿔 같은 step 수로 실행한다. 이동 거리를 비교한다. 다른 joint gain이나 물리 주기를 동시에 바꾸지 않는다.

## Isaac Lab 학습 결과를 사용하는 선택 실습

학습에는 별도 Isaac Lab 환경이 필요하다. 공식 5.1 문서가 제시한 **Isaac Lab 2.0 명령 예시**는 다음과 같다. 이를 현재 Isaac Lab 전체 버전의 공통 명령으로 간주하지 않는다. 훈련은 많은 GPU 시간을 사용하므로 여기서 자동 실행하지 않는다.

```bash
# Isaac Lab 작업 디렉터리에서
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task Isaac-Velocity-Flat-H1-v0 --headless
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py --task Isaac-Velocity-Flat-H1-v0 --num_envs 32
```

생성된 `logs/rsl_rl/<task>/<time>/params/env.yaml`과 내보낸 `exported/policy.pt`를 찾는다. `agent.yaml`은 네트워크 설정, `env.yaml`은 물리 주기·로봇 초기 자세·actuator gain/limit·관측 scale·행동 scale/offset·허용 명령 범위를 설명한다. 먼저 Lab의 `play.py`에서 정책이 정상인지 확인한 뒤 다음처럼 **H1의 동일한 69입력/19출력과 0.5 action scale 계약**을 가진 파일만 전달한다.

```bash
"$ISAAC_SIM/python.sh" run.py --policy /absolute/exported/policy.pt --environment /absolute/params/env.yaml --output output/custom
```

새 로봇이나 다른 관측 계약은 이 H1 어댑터로 자동 변환되지 않는다. 해당 로봇 클래스의 `_compute_observation()`과 `forward()`를 학습 계약에 맞게 구현해야 한다. `--environment`에서 dt는 읽지만 로봇 모델·관측 layout·행동 scale은 H1 구현을 유지한다.

## API와 USD를 이해하기

`SimulationApp`은 Kit 런타임을 열므로 `omni` 또는 로봇 API보다 먼저 만든다. USD의 **prim**은 `/World/H1` 같은 경로를 갖는 장면 객체다. USD reference는 로봇의 링크·관절·물리 속성을 장면에 합성한다. **articulation**은 이 관절들을 하나의 동역학 구조로 묶는다.

`initialize()`는 물리가 시작된 뒤 articulation handle, drive mode, gain, effort/velocity limit와 기본 자세를 설정한다. `load_policy()`는 TorchScript와 환경 설정을 읽는다. 본 실습의 하위 클래스는 최초 `_compute_observation()` 결과를 복사할 뿐 실제 계산은 설치된 H1 클래스를 호출한다. `_compute_action()`이 추론하고 `forward()`가 `default_pos + 0.5 * action`을 `ArticulationAction(joint_positions=...)`으로 보낸다. 이는 관절 모터의 **목표 위치**다. 매 step `set_joint_positions()`로 순간 이동시키면 정책이 학습한 물리 제어와 달라진다.

위치 정책을 torque 제어 로봇에 배포할 때는 별도 actuator 모델이 필요하다. 공식 ANYmal 경로는 `utils/actuator_network.py`의 `LstmSeaNetwork`, `/Isaac/Samples/Policies/Anymal_Policies/sea_net_jit2.pt`이다. `setup()`과 `reset()` 후 실제 관절 위치·속도·목표 offset을 `compute_torques()`에 전달하고 effort mode에서 torque를 적용한다. H1의 위치 명령을 그대로 torque 값으로 사용하면 안 된다. 이 패키지의 실행기는 H1 위치 제어이며 ANYmal actuator 네트워크 실행을 주장하지 않는다.

## 문제 해결과 확인 범위

- `No module named isaacsim`: 시스템 Python 대신 설치 폴더의 `python.sh`를 사용한다.
- 모델/정책 로딩 실패: 5.1 자산 루트와 위 세 파일의 접근성을 확인한다.
- 발끝 보행/몸통 붕괴: `joint_names` 순서, 기본 발목 위치, gain과 effort limit를 Lab의 env와 비교한다.
- 매우 느리거나 진동하는 보행: 200 Hz 물리와 decimation을 확인한다. 렌더링 FPS를 물리 주기로 착각하지 않는다.
- 입력 shape 오류: policy.pt와 env.yaml이 같은 훈련 run에서 나온 파일인지 확인한다.

소스 정적 검사와 CLI 도움말만 확인했으며 GPU 보행은 미실행 상태다. 실물 배포는 이 시뮬레이터 실습 범위 밖이다.

## 출처

- [Isaac Sim 5.1 정책 배포 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html), 특히 [관측/행동과 controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html#policy-controller-class), [debugging](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_policy_deployment.html#debugging-tips).
- 설치된 5.1 구현: `exts/isaacsim.robot.policy.examples/isaacsim/robot/policy/examples/robots/h1.py`, `controllers/policy_controller.py`, `utils/actuator_network.py`.
