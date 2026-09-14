# Isaac Sim 5.1 로봇 미니 프로젝트

[학습 로드맵](isaac_sim_5_1_robot_learning_roadmap.md)의 5개 프로젝트를 실행하며 공부하는 저장소입니다. 각 폴더의 README에 **코드 읽는 순서 → 실행 → 관찰 → 바꿔볼 실험**을 정리했습니다.

| 순서 | 프로젝트 | 실행하며 확인할 것 |
|---|---|---|
| 01 | [Mobile Robot Sandbox](src/01_mobile_robot_sandbox/README.md) | Jetbot 주행, pose CSV, URDF → USD |
| 02 | [ROS 2 Sensor Navigation](src/02_ros2_sensor_navigation/README.md) | RGB/depth, RTX LiDAR, IMU, TF, SLAM, Nav2 goal |
| 03 | [Manipulator Pick & Place](src/03_manipulator_pick_place/README.md) | Franka, IK/RRT/RMPflow, 접촉·effort, grasp 판정 |
| 04 | [Robot Synthetic Data](src/04_robot_synthetic_data/README.md) | 주행 camera, randomization, dataset, Extension GUI |
| 05 | [Parallel Policy Evaluation](src/05_parallel_policy_evaluation/README.md) | Spot 복제, 학습된 policy 추론, 마찰별 평가·성능 |

## 시작하기

Isaac Sim **5.1.0** 설치와 호환 NVIDIA GPU가 필요합니다. 시뮬레이터 코드는 설치에 포함된 `python.sh`로 실행합니다. `SimulationApp`이 Kit를 시작한 다음 simulator API를 import합니다. ROS-side 코드는 별도 ROS 2 터미널에서 실행합니다.

```bash
cd /path/to/robotics-sim-tutorial-kr
export ISAAC_SIM_PATH="$HOME/isaacsim"  # 자신의 5.1 설치 위치
"$ISAAC_SIM_PATH/python.sh" src/01_mobile_robot_sandbox/run.py --pattern straight --steps 300
```

기본은 GUI, `--headless`를 붙이면 창 없이 실행합니다. 도움말은 일반 Python에서도 볼 수 있습니다.

```bash
python3 src/01_mobile_robot_sandbox/run.py --help
"$ISAAC_SIM_PATH/python.sh" src/03_manipulator_pick_place/run.py --headless
"$ISAAC_SIM_PATH/python.sh" src/04_robot_synthetic_data/standalone/generate.py --headless --episodes 1 --frames 5
"$ISAAC_SIM_PATH/python.sh" src/05_parallel_policy_evaluation/evaluate.py --headless --num-envs 4
```

### Sources

- NVIDIA Isaac Sim 5.1 — [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- NVIDIA Isaac Sim 5.1 — [SimulationApp API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.simulation_app/docs/index.html)

## 실행과 결과 읽기

결과는 저장소의 `outputs/<project>/<timestamp>/`에 저장됩니다. `--output /새/디렉터리`로 바꿀 수 있으며 기존 디렉터리는 덮어쓰지 않습니다. 데이터셋 파일은 4번 출력의 `dataset/` 아래에 있습니다. `src/tutorial_common/`은 CLI·출력·asset 조회·종료 처리만 공유하며, 각 예제의 `World`와 loop는 해당 프로젝트에서 직접 볼 수 있습니다.

1. 처음에는 짧게 실행하고 CSV/JSON과 scene의 움직임을 비교하세요.
2. README의 실험에서 한 변수만 바꾸고 다른 출력 폴더에 저장하세요.
3. simulation time과 wall time, command와 실제 측정값을 구분하세요.
4. GUI에서 Pause/Stop하면 해당 실험을 종료합니다. 새 실험은 재실행해서 로그를 분리합니다.

**API 선택:** 개념 학습을 위해 5.1의 `World`, `WheeledRobot`, `Franka` 등 기존 Core 계열을 사용합니다. Experimental Core로 일괄 변환하지 않았습니다. 일부 공식 5.1 문서의 오래된 `*View` 표기와 실제 클래스 이름이 다른 경우 설치된 5.1 API 및 공식 v5.1.0 소스와 대조했습니다. 버전이 다르면 launcher에서 중단합니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html)
- NVIDIA Isaac Sim 5.1 — [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)

## 검증과 한계

GPU 없이 검사할 수 있는 명령·seed·판정·CLI 경계는 다음과 같이 검증합니다. 이 검사는 물리 시뮬레이션이나 ROS 통신 검증을 대신하지 않습니다.

```bash
python3 -m unittest discover -s tests -v
```

각 프로젝트 README, [실제 실행 검증 기록](docs/validation/README.md), 실행 후 `summary.json`을 함께 보세요. NVIDIA 로봇 USD와 사전학습 policy는 재배포하지 않으며, 최초 실행 때 5.1 asset 서버에 접근할 수 있어야 합니다. 다른 머신의 asset root는 설치 설정을 따릅니다. ROS, 센서, GPU 성능은 머신과 설정에 따라 달라집니다.

추천 학습 범위는 실행 가능한 작은 scene입니다. 3번의 경로는 작은 정적 장애물 하나, 5번은 평지에서의 추론 평가이며 완전한 산업용 grasp planner나 RL 학습 파이프라인은 포함하지 않습니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Robot Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_robots.html)
- NVIDIA Isaac Sim 5.1 — [Reinforcement Learning Policies Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html)
