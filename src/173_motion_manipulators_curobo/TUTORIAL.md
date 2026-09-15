# 173. t141 · cuRobo와 cuMotion의 실행 경계 이해하기

권장 학습 순서 **173** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t141`

Isaac Sim **5.1.0** 공식 튜토리얼은 외부 cuRobo 설치 및 native 예제로 연결하는 통합 안내다. 이 패키지는 설치된 **실제 cuRobo checkout**의 충돌 검사·IK·motion generation·MPPI·multi-arm 예제를 선택 실행하고 각 관찰 과제를 제공한다. cuRobo를 임의의 Lula 코드로 바꾸지 않는다. `launch.py` 자체가 planner를 구현하거나 vendor하지는 않는다.

## 이 실습의 의도

동일한 시뮬레이터 안에서도 충돌 거리 검사, 역기구학(IK), 전체 궤적 계획, 반복 제어가 서로 다른 질문에 답한다는 점을 실제 cuRobo 예제로 비교한다. 목표 cube와 장애물을 직접 옮겨 장면 변화가 planner의 world 표현과 계산 결과에 반영되는지 살펴본다. 기본 `--example motion`은 외부 checkout의 Franka MotionGen 예제를 실행하며, 이 launcher가 cuMotion ROS 2나 depth/nvblox 통합을 함께 시작하지는 않는다.

## 실행 후 확인할 것

- **MotionGen:** 목표 cube를 이동한 뒤 멈추고, 궤적 생성과 Franka 말단의 실제 목표 추종을 확인한다. 장애물을 추가한 경우 world 갱신 로그까지 본 뒤 다시 계획시켜 새 장애물이 반영되는지 살펴본다.
- **충돌·IK 비교:** `collision`에서는 검사 sphere와 장애물 사이 거리 시각화가 이동에 반응하는지, `ik`에서는 목표 주변의 도달 가능/불가능 표본이 구분되는지 확인한다. IK의 순간 자세 배치는 모터가 그 궤적을 동적으로 추종했다는 증거가 아니다.
- **반복 제어·양팔:** `mpc`에서는 움직이는 목표에 대한 응답과 rollout을, `multi-arm`에서는 두 목표를 놓고 마지막 red cube를 멈춘 뒤 양팔의 반응을 관찰한다. 장애물 뒤 정체나 계획 실패도 기록할 결과이며 무조건 모든 목표에 도달해야 하는 실습은 아니다.
- **모델과 좌표:** 기본 Franka 또는 dual UR10e 설정과 화면의 로봇이 일치하는지 확인하고, 목표는 planner의 로봇 base 좌표와 USD world 좌표를 구분해 읽는다. USD에 물체가 보이는 것과 planner가 장애물로 읽은 것은 별도 확인 사항이다.
- **실행 범위:** 파일 경로 검사나 native 창 실행만으로 GPU 계획 호환성이 검증되지는 않는다. 이 launcher는 결과 JSON을 저장하지 않으므로 선택한 checkout·예제·목표·계획 결과를 직접 기록한다.

## 준비와 버전 경계

x86_64 Linux, Isaac Sim 5.1, RTX GPU/드라이버, Isaac Python과 호환되는 CUDA/PyTorch 및 별도의 cuRobo 설치가 필요하다. **5.1 원문은 이 튜토리얼을 aarch64에서 지원하지 않는다고 명시하며 NvBlox 예제의 알려진 문제를 명시한다.**

cuRobo [설치 안내](https://curobo.org/get_started/1_install_instructions.html#install-for-use-in-isaac-sim)는 4.0-era 예제를 포함하므로 거기에 적힌 CUDA/Python 버전을 5.1 설치에 무조건 덮어쓰지 않는다. 선택한 cuRobo revision의 요구사항과 5.1의 Python/CUDA를 대조하고 별도 환경에 설치한다. 이 저장소는 설치·대규모 다운로드·환경 변경을 자동 실행하지 않는다. 사용자 환경에서 검증한 checkout 절대 경로와 commit을 실험 기록에 남긴다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
export CUROBO_ROOT=/absolute/path/to/curobo
cd src/173_motion_manipulators_curobo
python3 launch.py --curobo-root "$CUROBO_ROOT" --isaac-python "$ISAAC_SIM/python.sh" --example motion
```

launcher는 example 경로와 실행 가능한 `python.sh`를 확인한 뒤 프로세스를 실제 native 예제로 교체한다. 창을 닫거나 Ctrl+C로 종료한다. 추가 옵션은 `--` 뒤에 전달한다. 사용 중인 checkout이 `franka.yml` 이름을 바꾸었다면 그 checkout의 `--help`/config를 먼저 확인한다. **Isaac Sim 5.1과 외부 cuRobo의 런타임 호환성은 아직 검증하지 않았다.**

## 다섯 가지 native 실습

각 명령은 위 명령의 `--example` 값만 바꾼다. 첫 실행은 kernel compilation 때문에 느릴 수 있다.

| 선택 | 실제 checkout 파일 | 직접 할 일과 관찰 |
|---|---|---|
| `collision` | `examples/isaac_sim/collision_checker_example.py` | Play 후 검사 sphere를 장애물 근처/안으로 이동하고 거리 시각화 색과 gradient 방향을 비교한다. |
| `motion` | `examples/isaac_sim/motion_gen_reacher.py` | Franka 목표 cube를 옮긴 뒤 멈춰 trajectory 생성을 유도한다. 장애물을 추가한 후 world 갱신 메시지를 확인하고 다시 목표를 이동한다. |
| `ik` | `examples/isaac_sim/ik_reachability.py` | 목표 주변 표본 중 도달 가능한 영역과 불가능한 영역을 관찰한다. 장애물 하나만 추가하고 영역 변화를 비교한다. |
| `mpc` | `examples/isaac_sim/mpc_example.py` | 움직이는 목표를 따라가는 응답과 rollout 표시를 본다. 큰 장애물 뒤에서 정체되는 경우를 기록한다. |
| `multi-arm` | `examples/isaac_sim/multi_arm_reacher.py` | dual UR10e 두 목표를 설정한다. red cube를 마지막에 멈춰 양팔 계획을 유도한다. |

기본 Franka 로봇 구성은 cuRobo checkout의 `franka.yml`, dual-arm 구성은 `dual_ur10e.yml`에서 읽는다. USD 장면만 로드했다고 로봇의 planner 모델까지 자동 일치하는 것은 아니다. 첫 실습에서는 기본 로봇/config를 유지한다. GUI assets에서 **Props**의 단일 mesh 장애물을 넣고, world 갱신 로그가 나오기 전에 새 장애물을 planner가 인식했다고 판단하지 않는다.

## 데이터가 전달되는 과정

Isaac Sim의 USD stage는 prim의 mesh와 변환을 담는다. cuRobo의 `UsdHelper`가 장애물을 `WorldConfig`로 바꾸고, 충돌 검사기가 이를 사용한다. 로봇 관절은 `JointState`, 목표는 `Pose`로 전달된다. planner의 기준 좌표는 로봇 base이므로 world pose를 그대로 복사하면 안 된다. scene의 collider와 planner가 읽은 장애물 표현을 함께 확인한다.

IK는 목표를 만족하는 관절 위치를 찾는 기하 계산이다. native IK 예제의 관절 순간 이동은 구동기의 동적 추종 검증이 아니다. MotionGen은 관절 trajectory를 생성해 시간 간격별 action으로 적용하고, MPPI는 매 제어 단계에서 후보들을 평가한다. MPPI와 multi-arm은 공식 외부 문서에서 실험적인 기능으로 설명된다. 화면에서 한 번 움직였다는 사실만으로 모든 목표에 대해 collision-free라고 결론 내리지 않는다.

## cuMotion과 depth camera 확장

**cuRobo**는 직접 호출하는 Python/CUDA 라이브러리이고 **cuMotion**은 ROS 2/MoveIt 2와 연결되는 별도 배포 경로다. Isaac Sim의 ROS 2 bridge와 MoveIt robot description·joint name·clock·TF가 일치해야 한다. 이 패키지의 launcher에 `--example motion`을 주었다고 cuMotion ROS 2 통합을 실행한 것은 아니다. 별도 설치가 준비되면 [공식 cuMotion Isaac Sim 연동 절차](https://nvidia-isaac-ros.github.io/concepts/manipulation/cumotion_moveit/tutorial_isaac_sim.html)를 적용해 joint state 수신, 계획 요청, trajectory 실행을 각각 확인한다.

[Depth Camera 예제](https://curobo.org/get_started/2d_nvblox_demo.html)는 사전 생성 SDF 또는 RealSense 입력과 nvblox map을 사용한다. 정적 mesh world와 달리 map 생성·좌표 변환·갱신 지연·별도 CUDA extension이 필요하다. 5.1 문서가 알려진 문제를 명시하므로 여기에 동작하는 것처럼 대체 map을 넣지 않았다. 우선 위 정적 장애물 예제를 끝내고 실제 지원되는 cuRobo/nvblox 조합에서 원본 depth workflow를 수행한다.

## 기록과 문제 해결

같은 목표 pose에서 장애물 하나 유무만 바꾸고 계획 성공/실패, 실제 endpoint, 충돌 여부를 기록한다. 목표를 동시에 변경하면 장애물 효과를 분리하기 어렵다. `ModuleNotFoundError: curobo`는 launcher가 아니라 지정한 Isaac Python 환경의 설치 문제다. symbol/CUDA 오류는 PyTorch ABI와 CUDA 빌드 조합을 확인한다. example 파일이 없으면 선택 checkout의 버전 차이다. 경로 검사/CLI만 확인했으며 외부 dependency 설치와 GPU 계획 실행은 미검증이다.

## 출처

[Isaac Sim 5.1 cuRobo and cuMotion](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_curobo.html), [NVIDIA cuRobo 소스](https://github.com/NVlabs/curobo), [공식 Isaac Sim 예제 설명](https://curobo.org/get_started/2b_isaacsim_examples.html). 외부 문서는 5.1 버전 고정 페이지가 아니며 이 패키지는 2026-09-14에 해당 링크의 예제 경로를 확인했다.
