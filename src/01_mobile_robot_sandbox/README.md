# 01 — Standalone Mobile Robot Sandbox

## Goal / Execution Context

**Isaac Sim 5.1.0 · Standalone Python.** Python 프로세스가 `SimulationApp`을 시작하고, `World.reset()` 후 바퀴 명령과 physics step을 직접 실행합니다. 예외가 나도 공통 종료 처리를 거쳐 Kit를 닫습니다.

```text
run.py → SimulationApp → World/Scene → Jetbot
                               ↑         ↓
                         wheel command ← pose.csv
```

### Sources

- NVIDIA Isaac Sim 5.1 — [SimulationApp](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)
- NVIDIA Isaac Sim 5.1 — [Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)

## Dependencies / How to Run

저장소 루트에서 실행하세요. Isaac Sim 설치 이외에 pip 패키지를 추가로 설치할 필요는 없습니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/run.py --pattern straight --steps 300
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/run.py --pattern turn --steps 120
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/run.py --headless --pattern square --steps 2880
```

기본 사각형은 전진 10초 + 회전 2초를 네 번 반복하는 **open-loop** 실험입니다. 한 변은 1m, 명령 속도는 0.1m/s입니다. 실제 이동 거리는 접촉·마찰·모델의 치수와 timestep의 영향을 받으므로 정확한 사각형 복귀를 보장하지 않습니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)
- NVIDIA 공식 v5.1.0 소스 — [Jetbot standalone example](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/standalone_examples/api/isaacsim.robot.wheeled_robots.examples/jetbot_differential_move.py)

## 코드 읽기 / USD Assets / Physics

1. [motion.py](motion.py): 시간에 따라 `(v, yaw_rate)`를 선택합니다.
2. [run.py](run.py): `World` 생성 → ground → 로봇 reference → reset → 명령 → step → pose 순서로 읽습니다.
3. [import_urdf.py](import_urdf.py): URDF의 joint drive를 velocity 제어에 맞게 설정합니다.

| 항목 | 이 예제의 설정 |
|---|---|
| Robot model / USD reference | `/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd` |
| Prim hierarchy | `/World/Robot`, `/World/Robot/chassis`, 두 wheel joint |
| Physics / render dt | 기본 1/60초, `--dt`로 변경 |
| Stage units | 1m |
| Controller | `DifferentialController`, wheel radius 0.03m, wheel base 0.1125m |
| Joint 명령 | `left_wheel_joint`, `right_wheel_joint`, rad/s |
| Mass / inertia / collider / drive | NVIDIA USD asset의 설정 사용 |
| Pose quaternion | `[w, x, y, z]` |

Stage는 현재 scene이고, `/World/Robot` Prim은 외부 robot USD를 reference합니다. Python의 `robot` 객체와 USD의 Prim, PhysX의 articulation handle은 같은 개념이 아닙니다. `reset()` 전후에 어떤 데이터가 준비되는지 확인하세요.

### Sources

- NVIDIA Isaac Sim 5.1 — [Wheeled Robots API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.robot.wheeled_robots/docs/index.html)
- NVIDIA Isaac Sim 5.1 — [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)

## URDF → USD 실습

교육용 [learning_bot.urdf](assets/learning_bot.urdf)는 mesh 다운로드 없이 box·cylinder·sphere로 로봇을 정의합니다. 생성된 USD는 configuration layer를 포함하므로 **출력 폴더 전체**를 보관하세요.

```bash
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/import_urdf.py --headless --output outputs/my_urdf
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/run.py \
  --headless --robot-usd "$PWD/outputs/my_urdf/robot.usd" --pattern straight --steps 300
```

이 importer는 포함된 두 wheel joint 이름을 검사합니다. 임의의 URDF를 범용으로 제어하는 importer는 아닙니다. 다른 모델은 joint 이름·축·wheel radius/base를 먼저 확인하고 `run.py`의 CLI 값을 맞추세요. USD angular drive의 각도 단위와 Core controller의 radian 단위를 혼동하지 마세요.

### Sources

- NVIDIA 공식 v5.1.0 소스 — [URDF import example](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py)
- NVIDIA Isaac Sim 5.1 — [URDF Importer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)

## 결과 / Known Limitations / 실험

`pose.csv`에는 step·실험 경과시간·pose·명령이, `summary.json`에는 실제 시작·종료 위치와 변위가 기록됩니다. 초기 60 step은 접촉이 안정화되는 구간이며 CSV의 실험 시간에서는 제외합니다.

이 머신의 headless 검증에서는 Jetbot 180 step 직진 후 0.337m 이동했고, URDF 변환 및 생성한 asset의 바퀴 구동도 실행했습니다. URDF 모델은 학습용 치수·관성·skid caster를 사용하므로 Jetbot과 같은 command에 같은 변위를 내지 않습니다.

- `--dt 0.008333333333`와 기존 dt에서 **같은 simulation duration**으로 비교해보세요.
- `--wheel-radius`를 바꾸고 명령 속도와 pose의 차이를 설명해보세요.
- 사각형 끝점 오차를 줄이려면 시간 대신 pose를 읽어 다음 구간으로 넘어가는 controller를 작성해보세요.
- URDF의 mass·inertia·joint axis·drive damping 중 한 항목만 바꾸고 결과를 기록하세요.

학습 노트: **예상한 결과 / 실제 결과 / 확인한 Prim·API / 다음 실험** 네 항목으로 정리해보세요.
