# 173. 충돌 검사·역기구학·궤적 계획은 무엇이 다른가요?

## 이번에 배우는 것

**cuRobo의 다섯 예제를 선택해 실행하고, 각 계산이 로봇 동작의 어떤 질문에 답하는지 비교합니다.**

목표에 손이 닿는 관절 자세를 찾는 역기구학(IK)과, 현재 자세에서 그곳까지 안전하게 움직이는 경로를 찾는 일은 다릅니다. 이번에는 동일한 시뮬레이터에서 충돌 검사, 역기구학, 궤적 계획과 반복 제어를 구분해 봅니다.

| `--example` | 계산하는 내용 | 기본 로봇 설정 |
|---|---|---|
| `collision` | 로봇·장애물 사이 충돌 거리 | 해당 예제의 기본 설정 |
| `ik` | 목표 자세를 만족하는 관절 상태 | `franka.yml` |
| `motion` | 시작에서 목표까지의 관절 궤적 | `franka.yml` |
| `mpc` | 반복적으로 후보 움직임을 평가하는 제어 | `franka.yml` |
| `multi-arm` | 양팔 목표를 위한 움직임 | `dual_ur10e.yml` |

로컬 `launch.py`는 설치된 cuRobo 예제를 선택하는 실행기입니다. planner 자체와 CUDA 코드는 별도의 cuRobo checkout에서 가져옵니다.

## 1. 먼저 Franka MotionGen 예제 실행하기

x86_64 Linux, Isaac Sim 5.1, NVIDIA GPU·드라이버와 호환되는 cuRobo 환경이 필요합니다. 이 저장소의 기본 운영체제는 Ubuntu 24.04이며, cuRobo가 사용하는 Python·PyTorch·CUDA 조합도 실제로 맞아야 합니다. [cuRobo 설치 안내](https://curobo.org/get_started/1_install_instructions.html#install-for-use-in-isaac-sim)의 예전 Isaac Sim 버전 명령을 5.1 환경에 그대로 적용하지 말고 사용할 revision의 요구사항을 확인하세요.

Isaac Sim 5.1 원문은 이 튜토리얼의 aarch64 미지원과 NvBlox 예제의 알려진 문제를 명시합니다. 기본 실습은 정적 장애물을 사용하는 직접 cuRobo 연동입니다. [5.1의 범위 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_curobo.html)를 함께 확인하세요.

준비한 checkout이 `/data/curobo`에 있다고 가정합니다. 저장소 루트에서 실행하세요.

```bash
python3 src/173_motion_manipulators_curobo/launch.py \
  --curobo-root /data/curobo --isaac-python "$HOME/isaacsim/python.sh" \
  --example motion
```

경로는 자신의 설치에 맞춰 바꿉니다. 창을 닫거나 Ctrl+C로 종료하세요. 이 launcher에는 자체 `--steps` 옵션이나 결과 파일 저장 기능이 없습니다. 외부 예제 옵션은 `--` 뒤에 전달할 수 있습니다.

```bash
python3 src/173_motion_manipulators_curobo/launch.py \
  --curobo-root /data/curobo --isaac-python "$HOME/isaacsim/python.sh" \
  --example motion -- --help
```

외부 예제의 도움말 처리 시점에 따라 런타임 초기화가 필요할 수 있습니다. 파일 경로 검사가 통과해도 CUDA 계획까지 성공한 것은 아닙니다.

### 코드에서 볼 부분

`launch.py`의 선택 표에서 `motion`은 다음 파일과 기본 인수로 연결됩니다.

```text
'motion': ('motion_gen_reacher.py', ['--robot', 'franka.yml'])
```

경로와 인터프리터를 확인한 뒤 아래 호출로 실제 프로세스를 실행합니다.

```python
os.chdir(root)
os.execv(str(interpreter), [str(interpreter), str(script), *defaults, *extra])
```

작업 폴더를 cuRobo checkout으로 옮기는 이유는 원본 예제가 자신의 로봇 설정과 자산을 찾도록 하기 위해서입니다. 실행 후에는 native 예제의 동작과 오류가 그대로 나타납니다. 사용한 checkout revision과 예제 이름을 기록해 두면 재현할 때 같은 구현을 찾을 수 있습니다.

### 실행 결과 확인하기

1. 기본 Franka와 목표 cube가 나타나는지 확인합니다.
2. 목표 cube를 이동한 뒤 멈추세요. 원본 예제의 목표 갱신 조건에 따라 새 궤적이 계획됩니다.
3. 계획 결과와 실제 말단의 이동을 비교합니다. 계획 실패 로그가 있다면 실패한 목표도 함께 기록하세요.
4. 장애물을 추가했다면 planner의 world 갱신 로그를 확인한 뒤 목표를 다시 갱신합니다. 화면에 mesh가 보인다는 이유만으로 planner가 이미 읽었다고 판단하지 않습니다.

처음 CUDA kernel을 준비하는 동안 시간이 걸릴 수 있습니다. 단순히 창이 열려 있는지만 보지 말고 계획 결과와 실제 말단 움직임까지 확인하세요.

## 2. 같은 목표를 다른 계산으로 바라보기

### 예제에서 볼 부분

앞 명령의 `--example` 값을 바꾸어 실행할 수 있습니다.

| 선택과 실제 파일 | 직접 확인할 동작 | 결과의 의미 |
|---|---|---|
| `collision_checker_example.py` | Play 후 검사 sphere를 장애물 가까이 이동 | 거리와 gradient 표시가 장애물 위치에 반응하는지 봅니다. |
| `ik_reachability.py` | 목표 주변의 도달 가능 표본 비교 | 한 순간에 가능한 관절 자세를 찾는 계산입니다. |
| `mpc_example.py` | 목표를 계속 움직이며 응답·rollout 관찰 | 매 제어 단계의 후보 평가가 동작으로 이어집니다. |
| `multi_arm_reacher.py` | 양팔 목표를 배치하고 마지막 red cube를 멈춤 | 해당 예제의 트리거에 따라 양팔 계획을 관찰합니다. |

IK에서 로봇 관절이 곧바로 새 위치에 놓이는 것은 가능한 자세를 보여 주는 방식입니다. 모터가 그 궤적을 물리적으로 추종했다는 검증과 구분하세요. MPC의 rollout은 현재 상태에서 후보 제어를 적용했을 때의 미래 움직임을 펼쳐 본 결과입니다. 장애물 뒤에 정체되거나 MotionGen이 목표를 찾지 못하는 경우도 기록할 결과입니다.

cuRobo가 장면을 읽는 흐름은 다음과 같습니다.

```text
USD의 장애물 mesh·변환 → UsdHelper → WorldConfig → 충돌 검사
로봇 관절 상태 → JointState ─┐
목표 자세      → Pose ──────┴→ IK / MotionGen / 반복 제어
```

로봇의 planner 설정에는 링크와 충돌 표현이 포함됩니다. 화면의 로봇 USD만 바꿔도 `franka.yml`이 자동으로 새 로봇 설정이 되지는 않습니다. 또한 목표를 planner에 전달할 때는 로봇 base 기준 좌표와 USD 세계 좌표를 구분해야 합니다.

### cuMotion과 깊이 카메라로 확장하려면

cuMotion은 ROS 2·MoveIt 2를 통해 계획을 요청하는 별도 통합입니다. `--example motion`은 직접 cuRobo 예제를 실행하며 ROS 2 노드나 MoveIt을 시작하지 않습니다. 저장소 기본 ROS 조합은 Ubuntu 24.04/Jazzy이지만 외부 cuMotion 배포의 지원 조합은 [공식 연동 절차](https://nvidia-isaac-ros.github.io/concepts/manipulation/cumotion_moveit/tutorial_isaac_sim.html)에서 확인하세요. 다른 배포판이 필요하면 그 외부 환경을 별도로 준비합니다.

연동할 때는 robot description, joint name, 시뮬레이션 clock과 TF를 맞춘 뒤 joint state 수신 → 계획 요청 → trajectory 실행을 각각 확인해야 합니다.

깊이 입력을 사용하는 nvblox 경로는 정적 mesh 대신 갱신되는 거리장을 사용하므로 map 생성, 센서 좌표 변환과 업데이트 지연도 필요합니다. 5.1 원문의 알려진 문제가 있는 범위이므로 기본 예제의 성공을 이 경로까지 확대하지 않습니다.

## 3. 계산 결과와 실제 움직임의 차이 정리

| 결과 | 알 수 있는 것 | 추가로 확인할 것 |
|---|---|---|
| 충돌 거리 | 현재 두 형상의 관계 | 로봇 전체 모델과 장애물 갱신 여부 |
| IK 성공 | 목표를 만족하는 관절 상태의 존재 | 그곳까지 이동할 궤적 |
| MotionGen 성공 | 계획된 궤적 | 실제 시뮬레이터 추종과 접촉 |
| 반복 제어의 응답 | 현재 조건에 대한 제어 반응 | 큰 장애물·급격한 목표 변화의 실패 양상 |

한 단계의 성공은 다음 단계의 검사를 대신하지 않습니다. 예제마다 무엇을 계산하고 화면에는 무엇을 적용하는지 구분하는 것이 이번 실습의 핵심입니다.

## 4. 간단한 확인 실험

MotionGen에서 같은 목표를 사용하는 두 실행을 비교하되 **장애물 하나의 유무만** 바꾸세요. 로봇 설정과 목표 pose는 기록해 동일하게 맞춥니다.

장애물을 넣은 실행에서는 world 갱신을 확인한 뒤 다시 계획시키세요. 계획 성공 여부, 말단의 실제 끝 위치, 돌아가는 경로의 변화를 기록합니다. 장애물과 목표를 동시에 바꾸면 어느 변화가 원인인지 구분하기 어렵습니다.

## 실행할 때 막히면

- **예제 파일을 찾지 못함**: checkout에 `examples/isaac_sim/`과 선택한 파일이 있는지 확인하세요. 외부 revision 차이일 수 있습니다.
- **`No module named curobo`**: `--isaac-python`이 지정한 환경에 설치되어 있는지 확인하세요. system Python의 설치 여부와 다릅니다.
- **CUDA·symbol 오류**: 선택한 PyTorch, CUDA extension과 Python ABI의 호환을 점검하세요.
- **장애물을 추가해도 경로가 같음**: 원본 예제의 world 갱신 시점과 장애물 지원 표현을 확인하세요. 단순히 보이는 것만으로 포함을 판단하지 않습니다.
- **목표를 옮겼는데 계획하지 않음**: 해당 checkout의 목표 정지·변화 트리거를 확인하고 외부 예제 로그를 읽으세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [cuRobo and cuMotion](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_curobo.html)과 [cuRobo의 Isaac Sim 예제](https://curobo.org/get_started/2b_isaacsim_examples.html)를 연결한 실습입니다. 외부 cuRobo 문서는 5.1에 고정된 구현이 아니므로 사용한 revision이 중요합니다.

로컬 launcher의 파일·인수 전달을 확인했습니다. 외부 의존성 설치, GPU 계획, cuMotion과 nvblox 실행은 이번 개정에서 수행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`이며 결과 JSON은 launcher가 자동 저장하지 않습니다.
