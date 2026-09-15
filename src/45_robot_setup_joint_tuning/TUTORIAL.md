# 45. Joint drive gain을 응답 곡선으로 조정하기

권장 학습 순서 **45** · 로봇 자산 가져오기와 제작 · 출처 ID `t129`

공식 Tuning Joint Drive Gains 수업의 원리를 **자체 1 kg prismatic 시험 장치**에 적용한다. 외부 로봇 asset 없이 실제 PhysX 관절을 시뮬레이션하고 위치·속도 CSV를 기록한다. 동시에 Robot Schema를 붙여 GUI Gain Tuner에서도 같은 joint를 찾을 수 있게 한다. 질량-스프링 계산을 시뮬레이터 대신 출력하는 모형이 아니다.

## 준비와 실행

Isaac Sim **5.1.0**, 지원 GPU, `usd.schema.isaac`와 Gain Tuner 확장이 필요하다. GUI는 240 Hz 물리 실습을 창을 닫을 때까지 계속한다. `--headless` 기본 실행은 720 step(시뮬레이션 시간 3초) 뒤 종료한다. 다른 패키지/공통 코드가 필요 없다.

```bash
cd src/45_robot_setup_joint_tuning
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --headless --output output/baseline
"$ISAAC_SIM_PATH/python.sh" run.py --headless --damping 5 --output output/low_damping
# GUI는 gain 조절을 마친 뒤 직접 닫는다.
"$ISAAC_SIM_PATH/python.sh" run.py --output output/gui
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 720회 한도를 사용한다. 실행 중에도 물리·제어가 계속 진행되며, 결과 요약은 실행을 마칠 때 기록한다.

결과는 각 output의 `gain_rig.usda`, `response.csv`, `metrics.json`이다. 기존 output은 덮어쓰지 않는다. CSV의 position/velocity는 **실제 articulation에서 읽은 값**이다. GUI에서 사용자가 gain/target을 바꾸면 CSV의 target 열은 최초 CLI 입력을 유지하므로 자동 응답 비교는 유한 실행끼리 수행한다.

## 단계별 실습

1. baseline의 fixture를 확인한다. `/GainRig/base`는 world fixed joint에 연결되고 slider는 X축 prismatic, 범위 0..1 m, 질량 1 kg, max force 200 N이다. target position=0.5 m, stiffness=100 N/m, damping=20 N·s/m다. visual cube는 편집용 표시이고 이 실험은 환경 접촉 없이 joint 자체의 응답을 분리한다.
2. baseline과 low_damping CSV를 spreadsheet에서 time_s를 X축, position_m를 Y축으로 그린다. 목표 0.5 m선과 비교한다. `metrics.json`의 overshoot_m 및 최종 오차를 본다. 결과를 실행하기 전에 어느 쪽이 더 빠르거나 안정적인지 미리 성공값으로 쓰지 않는다.
3. position drive 조정은 damping=0에서 stiffness를 올려 목표 근처로 오는 범위를 찾는 것으로 시작한다. source의 heuristic은 그 stiffness를 한 자릿수 낮추고 damping을 추가한 뒤 실제 응답으로 미세 조정하는 것이다. 본 fixture의 숫자는 설명용 시작점이며 모든 로봇의 최적 gain이 아니다.
4. GUI에서는 **Tools → Robotics → Asset Editors → Gain Tuner**를 열고 robot=`GainRig`, joint=`slider_joint`를 선택한다. 목록이 비면 Window → Extensions에서 `isaacsim.robot_setup.gain_tuner`를 검색하고, root의 Robot Schema 및 link/joint relationships를 확인한다.
5. **Tune Gains**에서 한 관절의 stiffness/damping을 바꾸고 **Test Gains Settings**에서 제한된 범위의 시험을 실행한다. 완료 후 graph에서 command와 measured의 색/옅기 차이를 읽는다. 측정 graph는 테스트가 끝난 뒤 나타난다.
6. 속도 제어는 `--stiffness 0 --damping 20 --target 0 --velocity 0.2 --steps 480 --output output/velocity`로 실행한다. 2초 동안 위치가 joint limit 1 m에 닿지 않는지 확인하고 velocity가 0.2 m/s로 접근하는지 본다. 추가 하중을 고려해 damping을 조금 늘리는 실험은 `--mass`를 바꾼 뒤 별도로 수행한다.
7. 산업용 robot에서는 Maximum Joint Velocity를 함께 정하고 실제 속도 제한 준수 여부를 본다. stiffness를 무한히 키우는 대신 제한 근처에서도 overshoot가 작도록 조정한다. gravity compensation을 이미 사용하는 로봇을 흉내 낼 경우에만 rigid body Disable Gravity 설정을 검토한다.
8. Gain Tuner **Save Gains to Physics Layer**는 joint가 정의된 원본 layer를 찾을 수 있다. 이 fixture의 실험에서는 자신의 local stage를 Save As하여 결과를 보존한다. 여러 관절 로봇은 팔·다리 등 작은 그룹부터 맞춘 후 함께 시험한다.

## API와 물리 해설

`UsdPhysics.DriveAPI`의 선형 힘은 위치 오차에 비례하는 stiffness와 속도 오차에 비례하는 damping의 조합이며 maxForce로 제한된다. `SingleArticulation.get_joint_positions/get_joint_velocities`는 시뮬레이션 결과를 읽는다. `World.step`은 실제 physics dt=1/240 s를 진행한다. `RobotAPI/LinkAPI/JointAPI`와 robot relationship은 Gain Tuner가 어떤 prim을 로봇 관절로 취급할지 알려 준다.

순수 1자유도 선형 모델에서 임계 감쇠의 기준은 `c=2√(km)`다. k=100, m=1이면 c=20이다. 이것은 비교할 이론적 기준이며 실제 drive 제한·solver·시간 간격 때문에 측정값이 그대로 일치한다고 가정하지 않는다. 원문이 제시한 작은 overshoot 목표(예: 1%)도 실제 데이터로 평가한다.

한 변수 실험은 위 damping 20→5 비교다. 최종 오차만 작고 중간 overshoot가 큰 경우를 놓치지 않는다. zero-gain에서 움직이지 않는 것은 예상 결과다. NaN·발산이 나타나면 힘 제한·time step·gain을 확인한다. 문법·CLI를 확인했으며 실제 PhysX CSV/GUI Gain Tuner 실행은 미검증이다.

## 출처

- [Isaac Sim 5.1 Tuning Joint Drive Gains](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)
- [Position drive](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html#position-drive), [Velocity drive](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html#velocity-drive)
- [Robot Schema API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html)
