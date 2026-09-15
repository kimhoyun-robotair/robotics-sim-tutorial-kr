# 59. RMPflow Tuning Guide: 항목별로 켜서 원인 찾기

권장 학습 순서 **59** · 로봇 제어와 동작 계획 · 출처 ID `t180`

원문이 제안하는 단계별 RMP 활성화 순서를 실제 설정 파일과 Franka 움직임으로 비교합니다. 각 실행에서 변경된 YAML과 측정 오차를 저장하여 어떤 항목을 바꿨는지 재현할 수 있습니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

Isaac Sim 5.1 Assets의 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`가 필요합니다. `get_assets_root_path()`가 반환하는 asset 서버 또는 로컬 asset 팩에서 읽습니다. 첫 로딩에는 네트워크가 필요할 수 있습니다. 이 로봇 USD와 해당 재질/mesh 참조를 함께 사용할 수 있어야 합니다.

터미널에서 이 패키지 폴더(`59_motion_rmpflow_tuning`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --phase baseline
"$ISAAC_SIM_ROOT/python.sh" run.py --phase cspace
"$ISAAC_SIM_ROOT/python.sh" run.py --phase target
"$ISAAC_SIM_ROOT/python.sh" run.py --phase collision
"$ISAAC_SIM_ROOT/python.sh" run.py --phase directional
"$ISAAC_SIM_ROOT/python.sh" run.py --phase orientation
"$ISAAC_SIM_ROOT/python.sh" run.py --phase limits
"$ISAAC_SIM_ROOT/python.sh" run.py --phase damping
```

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 물리·제어 루프가 계속 실행됩니다. `--steps 600`처럼 양수를 지정하면 그 물리 스텝 수까지 실행하고 종료합니다. GUI의 `--steps 0`도 무제한이며, `--headless`에서 생략하면 기존 기본값인 600스텝을 실행합니다. headless의 0과 음수는 허용하지 않습니다. 창을 닫거나 지정한 스텝에 도달하면 실행 결과가 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 준비할 관찰표

각 output의 `rmpflow.yaml`과 `tuning_trace.json`을 함께 보관합니다. phase, 마지막 위치 오차, 접근 경로, 장애물 근처 지연, 급격한 관절 속도 변화를 기록합니다. 로봇의 drive gains와 physics dt는 고정한 채 하나씩 비교합니다. 이 예제는 파라미터 탐색 실험이며 모든 단계에서 충돌 회피가 활성화되어 있는 것은 아닙니다.

## 단계별 실습

1. baseline으로 설치된 Franka의 정상 설정을 관찰합니다. 새 로봇도 우선 형태와 크기가 비슷한 Franka/UR10 설정에서 출발하는 것이 원문의 첫 권장 절차입니다. 로봇 크기가 크게 다르면 길이 단위 파라미터를 재검토하고 joint 수가 달라지면 c-space 관련 threshold도 살펴봅니다.
2. cspace는 다른 RMP의 metric/inertia를 끈 뒤 cspace_target_rmp를 복구합니다. robot description의 default configuration을 향하는 기본 자세 편향을 봅니다. target으로 가지 않는 것이 이 단계의 예상 결과입니다. metric_scalar는 전역 상대 크기의 기준이며 원문은 1~100 정도의 작은 값을 예로 듭니다.
3. target은 위치 attractor를 켭니다. `min_metric_alpha=0`, `metric_alpha_length_scale=100000`, `proximity_metric_boost_scalar=1`로 방향별 차이/boost를 줄여 단순한 동작부터 관찰합니다. 위치 RMP의 max_metric_scalar가 cspace 쪽보다 커야 말단 목표가 우선됩니다.
4. 같은 target phase에서 `--target-gain 20`, `--target-gain 40`을 따로 실행합니다. accel_p_gain 한 값만 바꿔 수렴 속도/오차를 비교합니다. accel_d_gain과 accel_norm_eps는 이어서 한 번에 하나씩 output YAML을 참고하며 조정할 수 있습니다. metric을 무조건 키워 오차를 줄이려 하지 말고 오차 개선이 포화되는 범위를 찾습니다.
5. collision은 obstacle 회피 항목을 켭니다. target과 collision의 상대 metric을 비교합니다. 장애물 옆에서 끌리는 듯 느려지면 두 반응의 경쟁을 관찰합니다.
6. directional은 target의 방향 의존 metric과 boost를 원래 값으로 복구합니다. 멀리 있을 때/목표 근처의 움직임을 비교합니다. 원문은 min_metric_alpha를 0보다 크게, length scale을 점차 줄여가며 조정하도록 설명합니다.
7. orientation은 axis_target_rmp를 켜고 quaternion `[0,0,1,0]` 방향을 함께 추종합니다. 위치 목표 근처에서 orientation 우선도가 커지는지 관찰합니다.
8. limits는 joint limit와 velocity cap 항목을 복구합니다. 관절 한계에서 밀어내는 반응을 살펴봅니다. damping은 전역 damping과 cspace inertia를 복구하여 급격한 움직임을 줄이는 방향으로 비교합니다.

## API와 문서 표기 차이

이 프로그램은 원본 YAML을 읽어 복사본에서 `rmp_params` 값을 수정한 뒤 해당 경로를 `RmpFlow`에 전달합니다. 설치 파일을 직접 수정하지 않습니다. `ArticulationMotionPolicy`가 관절 action을 만들고 actual joint state 기반 FK로 위치 오차를 기록합니다. collision sphere 시각화도 켭니다.

원문 tuning guide의 `c-space_target_rmp` 표기는 실제 YAML에서 `cspace_target_rmp`입니다. 원문의 `proximity_metric_boost_length_scalar`는 5.1 설치 설정의 유효 키가 아니며 boost 비율은 `proximity_metric_boost_scalar`입니다. 마지막 단계의 inertia는 실제 설정에 존재하는 `cspace_target_rmp/inertia`와 `damping_rmp/inertia`를 사용합니다. 문서 표기를 그대로 새 YAML 키로 만들어 효과가 있다고 가정하지 않습니다.

metric은 목표들 사이의 상대 가중/방향 구조를 정하고 gain은 각각의 반응 크기와 감쇠를 정합니다. drive stiffness/damping은 다시 별개의 물리 제어 계층입니다. RMP 파라미터만으로 USD 로봇의 부정확한 관절 gains나 잘못된 collision sphere를 해결할 수 없습니다.

## 관찰 기준과 한 변수 실험

각 실행에 실제 사용한 YAML이 남고, phase에 따라 활성 metric이 달라지며 trace가 기록되어야 합니다. `--target-gain`만 바꿔 비교하는 것이 가장 작은 후속 실험입니다. phase 순서 자체는 여러 RMP를 단계적으로 복구하는 원문 절차를 따르므로 모든 phase가 baseline보다 좋다고 주장하지 않습니다.

## 문제 해결

초기 phase에서 장애물과 접촉하거나 target을 무시하는 것은 꺼진 항목을 확인할 단서입니다. 발산하면 baseline으로 돌아가 gain, dt, base 좌표, sphere 모델을 확인합니다. 같은 target에서 drive 추종이 나쁘면 먼저 실제 로봇과 정책 시각화의 차이를 관찰합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — RMPflow Tuning Guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/concepts/rmpflow_tuning_guide.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 실행 길이 선택과 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.
