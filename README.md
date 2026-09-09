# Isaac Lab 한국어 튜토리얼

**Ubuntu 24.04 LTS에서 Isaac Lab을 처음 실행하는 단계부터, 로봇 학습 실험을 설계하고 정책을 비교하는 단계까지 따라가는 36단계 실습이다.** 코드와 설명은 **Isaac Lab `v3.0.0-beta2.patch1` / Isaac Sim 6.0.1 / Python 3.12**에 맞춘다.

| 항목 | 기준 |
| --- | --- |
| 작성·확인일 | 2026-09-09 |
| 운영체제 | Ubuntu 24.04 LTS, x86_64 PC |
| Isaac Lab | `v3.0.0-beta2.patch1`, 커밋 `ffff603eafc6b74264a5261cc0183d6a65390d78` |
| Isaac Sim | 6.0.1, pip 배포 버전 `6.0.1.0` |
| Python / PyTorch | Python 3.12 / PyTorch 2.10.0, x86_64 CUDA 12.8 wheel |
| 기본 실습 구성 | PhysX 물리 + Isaac RTX 카메라 렌더러 + Kit GUI |
| ROS | 필수 아님. 연동을 확장할 때는 ROS 2 Jazzy를 사용한다. |
| 브랜치 | `IsaacLab` |

## 최신 버전을 정한 기준

2026-09-09에 NVIDIA 공식 저장소의 공개 릴리스 목록과 태그를 확인했다. 가장 최근에 공개된 릴리스는 2026-07-02의 **3.0 Beta 2 Patch 1**이다. 이 패치는 Isaac Sim 6.0.1 지원을 추가한다. GitHub의 `prerelease` 메타데이터는 `false`이지만, 이름과 릴리스 설명은 **베타**로 명시하므로 정식 3.0으로 표현하지 않는다. 2.x의 최신 정식 태그는 `v2.3.2`이며, 이 튜토리얼은 사용자가 요청한 최신 공개 버전에 맞춰 3.0 베타를 사용한다.

- [선택한 공식 릴리스](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1)
- [공식 릴리스 목록](https://github.com/isaac-sim/IsaacLab/releases)
- [버전을 고정한 설치 문서](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/pip_installation.rst)
- [기계가 읽을 수 있는 버전 기록](isaaclab_tutorial/version-lock.json)

`main`이나 `develop`의 최신 문서에는 이 태그와 다른 API가 들어갈 수 있다. 본문은 태그가 고정된 공식 소스를 우선한다. 예전 2.x 예제의 `--headless`, `wxyz`, 이전 상태 쓰기 함수를 그대로 붙여 넣지 않는다.

## 먼저 알아둘 검증 범위

**이 저장소를 작성한 환경에는 NVIDIA GPU와 Isaac Sim 런타임이 없어 실제 렌더링·로봇 동역학·학습 수렴을 실행 검증하지 못했다.** 실행 파일의 문법, 공식 태그의 API와 인자, 문서 경로를 확인하고, 영상 이상 판정과 평가 결과 집계에 대한 CPU 테스트를 수행했다. 자세한 결과는 [검증 기록](isaaclab_tutorial/reports/VALIDATION.md)에 남긴다.

실제 GPU PC에서는 강체 높이·속도, Franka 관절 오차와 root 이동, RGB 블랙아웃·포화, 깊이 유효값을 자동 검사한다. 자동 검사와 함께 Kit 화면을 확인해야 렌더링 이상이나 충돌 형상 오류를 판단할 수 있다. 학습되지 않은 사족보행 정책이 넘어지는 현상과, 잘못된 자산·물리 설정 때문에 로봇이 무너지는 현상은 원인을 나누어 확인한다.

## 시작하기

새 PC에서는 아래 순서로 진행한다. 기존 폴더가 있다면 이름이 겹치지 않는 새 폴더를 사용한다.

```bash
cd "$HOME"
git clone --single-branch --branch IsaacLab \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
export ISAACLAB_ROOT="$HOME/IsaacLab"
```

이 명령은 튜토리얼을 받는다. NVIDIA Isaac Lab과 Isaac Sim 설치는 [01–10단계](isaaclab_tutorial/docs/01-foundations-install-gui.md)에서 진행한다. 처음이라면 설치 명령부터 건너뛰지 말고, GPU·Python·가상환경의 역할을 읽은 뒤 진행한다. 터미널을 새로 열면 두 경로 변수와 Python 가상환경을 다시 설정한다.

## 36단계 학습 순서

각 단계는 목적, 실행 위치, 코드 또는 명령, 결과 확인, 다음 단계로 넘어갈 조건을 설명한다. 독립 스크립트는 [examples](isaaclab_tutorial/examples)에 모았다. 본문의 짧은 코드 조각은 설정을 설명하기 위한 발췌인지, 파일 전체인지 함께 확인한다.

| 단계 | 실습 내용 |
| --- | --- |
| [01](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-01) | Isaac Lab·Isaac Sim·GR00T·Omniverse의 역할 |
| [02](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-02) | 버전과 물리·렌더러·GUI 구성 이해 |
| [03](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-03) | Ubuntu와 GPU 사양 확인 |
| [04](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-04) | 작업 폴더와 Python 3.12 가상환경 |
| [05](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-05) | 고정 버전의 Isaac Sim과 Isaac Lab 설치 |
| [06](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-06) | Isaac Sim 첫 실행과 로그 확인 |
| [07](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-07) | Viewport·Stage·Property 탐색 |
| [08](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-08) | USD 저장과 Play·Pause·Stop |
| [09](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-09) | AppLauncher와 첫 Python 시뮬레이션 |
| [10](isaaclab_tutorial/docs/01-foundations-install-gui.md#step-10) | 프로젝트 1 — 조명이 있는 첫 장면 |
| [11](isaaclab_tutorial/docs/02-assets-sensors.md#step-11) | USD와 Prim으로 자산 구조 읽기 |
| [12](isaaclab_tutorial/docs/02-assets-sensors.md#step-12) | 좌표계·단위·XYZW quaternion |
| [13](isaaclab_tutorial/docs/02-assets-sensors.md#step-13) | 프로젝트 2 — 상자 낙하와 정착 |
| [14](isaaclab_tutorial/docs/02-assets-sensors.md#step-14) | 물리 스텝·reset·버퍼 갱신 |
| [15](isaaclab_tutorial/docs/02-assets-sensors.md#step-15) | articulation과 actuator |
| [16](isaaclab_tutorial/docs/02-assets-sensors.md#step-16) | 프로젝트 3 — Franka 초기 자세 유지 |
| [17](isaaclab_tutorial/docs/02-assets-sensors.md#step-17) | 환경 복제와 env_origins |
| [18](isaaclab_tutorial/docs/02-assets-sensors.md#step-18) | 프로젝트 4 준비 — 센서와 렌더러 |
| [19](isaaclab_tutorial/docs/02-assets-sensors.md#step-19) | RGB·깊이 카메라 수집 |
| [20](isaaclab_tutorial/docs/02-assets-sensors.md#step-20) | 접촉 센서의 힘 읽기 |
| [21](isaaclab_tutorial/docs/02-assets-sensors.md#step-21) | RayCaster로 바닥 높이 측정 |
| [22](isaaclab_tutorial/docs/02-assets-sensors.md#step-22) | 센서 통합 검사와 이상 화면 진단 |
| [23](isaaclab_tutorial/docs/03-learning-projects.md#step-23) | 관측·행동·보상·종료로 학습 문제 정의 |
| [24](isaaclab_tutorial/docs/03-learning-projects.md#step-24) | Manager 기반과 Direct 환경 비교 |
| [25](isaaclab_tutorial/docs/03-learning-projects.md#step-25) | 무작위 정책으로 학습 전 기준 확인 |
| [26](isaaclab_tutorial/docs/03-learning-projects.md#step-26) | 프로젝트 5 — Cartpole PPO 학습 |
| [27](isaaclab_tutorial/docs/03-learning-projects.md#step-27) | 체크포인트와 동영상 |
| [28](isaaclab_tutorial/docs/03-learning-projects.md#step-28) | 프로젝트 6 — Franka 목표 자세 도달 |
| [29](isaaclab_tutorial/docs/03-learning-projects.md#step-29) | 프로젝트 7 — ANYmal C 평지 보행 |
| [30](isaaclab_tutorial/docs/03-learning-projects.md#step-30) | 보상 항을 추가한 사용자 환경 |
| [31](isaaclab_tutorial/docs/03-learning-projects.md#step-31) | 환경 무작위화와 커리큘럼 |
| [32](isaaclab_tutorial/docs/03-learning-projects.md#step-32) | 모방학습·Mimic·GR00T |
| [33](isaaclab_tutorial/docs/03-learning-projects.md#step-33) | 같은 초기조건에서 정책 평가 |
| [34](isaaclab_tutorial/docs/03-learning-projects.md#step-34) | 최종 프로젝트 8 — 여러 시드로 보상 설계 비교 |
| [35](isaaclab_tutorial/docs/03-learning-projects.md#step-35) | CSV·JSON 해석과 실패 분석 |
| [36](isaaclab_tutorial/docs/03-learning-projects.md#step-36) | 최종 검증 보고서와 다음 실험 |

## 프로젝트별 결과물

| 프로젝트 | 직접 만드는 결과물 | 통과 조건 |
| --- | --- | --- |
| 1 | 외부 USD 없이 조명·바닥·도형이 있는 장면 | GUI에서 도형과 조명이 보이고 정해진 스텝 후 정상 종료 |
| 2 | 바닥에 떨어져 정착하는 상자 | root 상태 유한값, 바닥 관통·잔류 진동 검사 통과 |
| 3 | 공식 Franka 설정을 이용한 자세 유지 | 고정 root·관절 오차·속도 검사 통과 |
| 4 | RGB PNG·깊이 NPY·카메라 진단 JSON, 접촉·raycast 관측 | 블랙아웃·포화·잘못된 깊이 검출, 좌표·센서 대상 확인 |
| 5 | Cartpole PPO 체크포인트 | 재생 가능, 무작위 정책과 행동 차이를 확인 |
| 6 | Franka 도달 정책 | 목표와 end-effector를 함께 확인하고 학습 곡선 점검 |
| 7 | ANYmal C 보행 정책 | 목표 속도 추종·낙상 원인을 분리하여 관찰 |
| 8 | 보상 두 종류 × 학습 시드 3개, 공통 평가의 JSON·CSV | 동일 평가 seed·물리 조건으로 비교하고 실패를 포함해 보고 |

프로젝트 1–7이 중간 프로젝트이고, 프로젝트 8이 앞에서 배운 설정·학습·검증을 합친 심화 프로젝트이다. GPU 종류에 따라 환경 수와 학습 시간은 달라진다. 예시 iteration 수는 시작 설정이며, 수렴이나 성공률을 보장하는 수치가 아니다.

## 실행 검사

설치 후 같은 가상환경에서 실행한다. 아래 검사는 현재 PC에서 실제로 실행한 결과를 새로 만든다.

```bash
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
export ISAACLAB_ROOT="$HOME/IsaacLab"
# 04–05단계에서 만든 가상환경을 먼저 활성화한다.
python "$TUTORIAL_ROOT/isaaclab_tutorial/tools/preflight.py" \
  --isaaclab-root "$ISAACLAB_ROOT" \
  --output "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/preflight.json"

bash "$TUTORIAL_ROOT/isaaclab_tutorial/tools/run_gpu_checks.sh"
```

사전 점검이 실패하면 GPU 검사를 시작하지 않는다. 검사 로그를 읽고 원인을 해결한 뒤 다시 실행한다. 그래픽·센서 문제를 자세히 좁히는 방법은 [검증과 문제 해결](isaaclab_tutorial/docs/04-validation.md)을 참고한다.

GPU가 없어도 문서와 순수 계산 검사는 실행할 수 있다.

```bash
python "$TUTORIAL_ROOT/isaaclab_tutorial/tools/check_tutorial.py" \
  --upstream "$ISAACLAB_ROOT"
python -m unittest discover -s "$TUTORIAL_ROOT/isaaclab_tutorial/tests" -v
```

카메라 계산 테스트에는 NumPy가 필요하다. 이는 Isaac Lab 설치 환경에 포함된다. 이 검사만 통과한 상태를 시뮬레이션 실행 성공으로 해석하지 않는다.

## 공식 자료와 파일 안내

- [공식 튜토리얼 대응표](isaaclab_tutorial/docs/05-official-reference-map.md): 어떤 공식 문서와 소스를 읽었는지 확인한다.
- [예제 실행 파일](isaaclab_tutorial/examples): 본문에 나오는 독립 실행 예제와 최종 평가 도구이다.
- [검증 기록](isaaclab_tutorial/reports/VALIDATION.md): 수행한 검사와 미실행 항목을 구분한다.
- [NVIDIA 코드 저작권 고지](isaaclab_tutorial/THIRD_PARTY_NOTICES.md): 참고·응용한 BSD-3-Clause 코드의 출처이다.

학습 범위는 GUI·자산·센서·병렬 환경·강화학습·모방학습 입문과 재현 가능한 정책 비교이다. 모든 로봇과 선택적 물리 backend, 실제 로봇 배포까지 검증했다는 뜻은 아니다. Newton·OVPhysX·OVRTX나 실제 로봇으로 확장할 때는 해당 backend와 하드웨어의 공식 지원 범위를 별도로 확인한다.
