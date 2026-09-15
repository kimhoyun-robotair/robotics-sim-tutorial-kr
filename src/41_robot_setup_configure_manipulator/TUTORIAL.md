# 41. UR10e 관절과 Robotiq 접촉 성질 조정하기

권장 학습 순서 **41** · 로봇 자산 가져오기와 제작 · 출처 ID `t125`

공식 인덱스 **t125** · Isaac Sim **5.1.0**

## 결과와 준비

UR10e+Robotiq의 articulation solver 설정, finger 관절 최대 effort, fingertip 마찰을 설정한 로컬 USD를 만듭니다. 이후 Physics Inspector와 Gain Tuner에서 실제 목표 추종을 관찰합니다. `run.py`는 물리 속성 저술을 구현하며 Gain Tuner의 자동 실험을 대신 실행했다고 주장하지 않습니다.

Isaac Sim 5.1.0, 지원 NVIDIA GPU/드라이버와 다음 공식 에셋만 있으면 됩니다. 앞선 로컬 튜토리얼의 산출물은 필요 없습니다.

- 시작 에셋: `/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd`
- 완성 참고: `/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd`

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --frames 10 --friction 0.5
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 1200회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

현재 폴더 `output/<고유번호>/configured.usda`와 `configuration_report.json`이 생성됩니다. `--output`으로 기존 폴더를 지정하면 덮어쓰지 않습니다. 원본 USD reference 위의 **로컬 layer에만 override**를 쓰므로 설치 에셋은 수정하지 않습니다. 출력 파일은 원본 reference 접근이 계속 필요합니다. `--steps`는 Kit 갱신 횟수이며 자동 물리 실행은 아닙니다. 실습하려면 파일을 File > Open으로 다시 열어도 됩니다.

## 1. articulation 설정

1. GUI 수동 실습은 시작 에셋을 열어 새 로컬 사본을 만듭니다. 원문의 방식은 `configuration/*_physics.usd` layer를 직접 편집하는 것이며 이 패키지 코드는 같은 값을 로컬 상위 layer에서 override합니다.
2. `/ur/root_joint`를 선택합니다. Physics/Articulation의 Articulation Enabled를 켭니다.
3. Solver Position Iterations Count=**64**, Solver Velocity Iterations Count=**4**로 설정합니다.
4. Sleep Threshold=**0.00005**, Stabilization Threshold=**0.00001**로 설정합니다. 저장한 report의 position/velocity 값이 64/4인지 확인합니다.

반복 계산 횟수를 늘리면 mimic과 접촉 제약을 더 정밀하게 풀지만 계산 비용이 늘어납니다. sleep은 거의 움직이지 않는 물체의 계산을 줄이는 기준입니다. 이 값들이 모터 목표 위치를 대신하지 않습니다.

## 2. fingertip 재질과 effort

1. 원문에서 독립 gripper physics layer는 `import_manipulator/robotiq_2f_140/configuration/robotiq_2f_140_physics.usd`입니다. 직접 편집할 때는 그 layer의 로컬 사본을 사용합니다.
2. 그리퍼에 Create > Physics > Physics Material > Rigid Body Material을 생성합니다. Looks 아래에 두고 static friction=**1.0**, dynamic friction=**1.0**을 설정합니다.
3. `colliders/left_inner_finger/mesh_1/box`와 `colliders/right_inner_finger/mesh_1/box`의 Physics Material에 생성한 재질을 바인딩합니다. 전체 조립 에셋에서는 이 경로 앞에 `/ur/ee_link`가 붙을 수 있습니다.
4. `joints/finger_joint`의 Drive/Angular/Max Force=**200**을 설정합니다. 이 joint 하나가 구동하고 다른 finger/knuckle은 mimic으로 따라갑니다.
5. `configuration_report.json`에서 실제 바인딩한 collider 경로와 max_force=200을 확인합니다. 코드는 양쪽 inner finger의 CollisionAPI가 붙은 shape를 찾아 동일 재질을 바인딩합니다.

PhysxArticulationAPI는 NVIDIA PhysX의 solver 속성을 저술합니다. UsdPhysics.DriveAPI의 angular max force는 회전 관절의 effort 제한이며 API/물리 맥락에서는 토크입니다. 시각 재질은 색을, `MaterialBindingAPI(..., purpose="physics")`는 마찰/반발을 설정합니다. 마찰 1이 어떤 물체든 반드시 잡는다는 의미는 아닙니다.

## 3. Physics Inspector에서 추종 확인

1. `configured.usda` 또는 공식 완성 에셋을 엽니다. Tools > Physics > Physics Inspector를 선택합니다.
2. Stage에서 `/ur` articulation을 선택하고 원형 refresh 버튼을 누릅니다.
3. finger_joint의 blue target slider를 작은 값부터 움직입니다. 실제 DOF position이 목표에 도달하는지 확인합니다.
4. 일반 시뮬레이션 전에 Physics Inspector를 닫습니다. 도구가 작성한 시험 값을 저장할지 묻는다면 의도하지 않은 시험 값은 버립니다. Inspector는 PhysX를 부분 초기화하므로 열린 채 일반 시뮬레이션과 혼용하지 않습니다.

## 4. Gain Tuner 실험

1. Tools > Robotics > Asset Editors > Gain Tuner에서 Select Robot=`ur`를 선택합니다.
2. Tune Gains의 Nat. Freq.=**0.5**, Damping Ratio=**1.0**으로 시작합니다. 원문의 시작점이며 모든 로봇의 정답 gain은 아닙니다.
3. Test Gains Settings에서 손가락 또는 같이 움직일 작은 관절 묶음만 선택합니다. Sequence로 실행 순서를 정하고 테스트합니다.
4. 목표/실제 위치 plot을 비교합니다. 목표에 못 미치면 natural frequency를 조금 올려 보고, overshoot가 크면 frequency를 조금 낮추고 damping ratio를 올려 봅니다.
5. 필요하면 시험 중 중력을 꺼 gain 효과를 분리합니다. 실제 사용보다 지나치게 빠른 최대 속도 테스트는 줄입니다.

성공은 설정 파일 저장과 별도로 **측정 position이 목표를 추종하고 불필요한 진동이 줄어드는 것**입니다. 코드의 report는 USD 설정만 검증하며 Gain Tuner plot 검증은 사용자가 GUI에서 수행합니다. 한 변수 실험은 friction=1.0→0.5 또는 damping ratio만 변경하여 비교합니다.

No finger_joint/두 collider 오류는 다른 구성의 USD를 지정했거나 gripper variant=None일 때 확인합니다. 높은 effort에서 관통/진동이 생기면 물리 Time Steps per Second를 높이는 실험이 필요할 수 있습니다. maxForce를 올리는 것만으로 안정성이 개선되지는 않습니다.
## 버전 고정 출처

- [NVIDIA Isaac Sim 5.1.0 — Tutorial 7: Configure a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html)

한국어 절차는 새로 작성했습니다. 원문 GUI 기능과 이 폴더의 준비/검사/실행 코드를 구별해 설명합니다. 실제 runtime 검증 범위는 tutorial.json의 verification 기록을 확인합니다.
