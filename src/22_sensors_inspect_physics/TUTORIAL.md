# 22. Simulation Data Visualizer로 실제 상태 읽기

권장 학습 순서 **22** · 물리 기초와 Core API 확장 · 출처 ID `t162`

한 관절 팔의 Python 측정 기록과 GUI 상태 그래프를 함께 관찰합니다. 외부 Cortex Franka 대신 로컬 articulation을 사용하고 physics residual reporting을 켭니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/22_sensors_inspect_physics
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다. GUI 실행에서 `--steps`를 생략하면 처음 240프레임을 기록한 뒤에도 사용자가 창을 닫을 때까지 시뮬레이션을 계속합니다. 이후 프레임은 파일에 추가하지 않습니다. `--steps N`을 지정하면 최대 N프레임을 기록하고 종료하며 N은 양수여야 합니다. `--headless`는 창 없이 실행하고, `--steps` 생략 시 240프레임 후 종료합니다. 이전 명령과 호환되는 `--interactive`는 더 이상 필요하지 않으며 명시한 `--steps`의 종료 조건을 바꾸지 않습니다. `--headless`와 `--interactive`는 함께 쓰지 않습니다. run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다.

## 실습 순서와 관찰

1. 위 GUI 명령으로 실행하고 viewport 눈 아이콘 **Show By Type > Physics > Simulation Data Visualizer**를 켭니다.
2. Stage에서 `/World/Arm/Link`를 선택합니다. 위치, 회전, 선속도, 각속도, 질량·관성을 봅니다. 비물리 Xform `/World/Arm`을 선택했을 때 표시 항목이 달라지는지 비교합니다.
3. Stop 후 Play를 다시 눌러 초기 변화 구간을 관찰합니다. `joint_motion.json`은 첫 자동 240 frame의 joint 위치/속도 기록이며 이후 GUI 조작은 자동 추가 저장되지 않습니다.
4. Physics Scene을 선택하고 **Add > Physics > Residual Reporting**, Advanced의 **Enable Residual Reporting**을 확인합니다. Reset/Start 후 RMS와 Max residual을 관찰합니다. 코드는 같은 API를 이미 적용했습니다.
5. `--mass 2 --output output/mass2`로 링크 질량만 바꿔 초기 진동·수렴 변화를 비교합니다.
6. UI 원본 예제도 보려면 **Window > Examples > Robotics Examples > Cortex > Franka Cortex Examples > Load Robot**, `/World/Franka/panda_hand` 선택, **START** 순서로 실행합니다. 이 선택 경로에는 NVIDIA Franka 에셋이 필요하지만 로컬 기본 실습에는 필요 없습니다.

## API와 USD 개념

Visualizer의 Position은 stage unit, Rotation은 degree, Linear Velocity는 stage unit/s, Angular Velocity는 degree/s입니다. API의 `get_joint_positions`와 `get_joint_velocities`는 rad와 rad/s이므로 JSON과 화면을 비교할 때 180/π를 곱합니다. 속도 그래프의 M은 벡터 크기입니다.

Mass는 stage mass unit, inertia는 질량×길이²입니다. 선택 prim이 물리 body인지에 따라 표시 가능한 상태가 다릅니다. residual은 physics scene·articulation root·joint의 제약 수렴 지표이며 위치/속도 RMS와 Max로 관찰합니다. residual이 작다고 센서 보정이나 현실 모델이 정확하다고 해석하지 않습니다.

## 확장 실습·성공 기준·문제 해결

그래프가 비면 rigid body Link가 선택됐는지, timeline이 Play인지 확인합니다. Inspector를 동시에 열었다면 닫고 일반 시뮬레이션을 재시작하세요. residual은 reporting API와 enable 옵션이 모두 필요하고 Reset 후 활성화될 수 있습니다. 숫자의 단위와 선택 prim 경로를 실험 기록에 함께 남기는 것이 성공 기준입니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Simulation Data Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/ext_isaacsim_inspect_physics.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·프레임 수 옵션·출력 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
