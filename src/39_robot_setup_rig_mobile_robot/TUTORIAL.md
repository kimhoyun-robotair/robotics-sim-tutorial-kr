# 39. 지게차의 7자유도를 직접 rigging하기

권장 학습 순서 **39** · 로봇 자산 가져오기와 제작 · 출처 ID `t123`

공식 Rig a Mobile Robot의 **GUI native** 실습이다. `run.py`는 Isaac Sim 5.1 asset `/Isaac/Samples/Rigging/Forklift/forklift_b_unrigged_cm.usd`를 새 로컬 편집 layer로 연다. 원본은 **cm 단위**이며 m 단위 숫자를 그대로 입력하면 안 된다. 완성 비교 asset은 같은 폴더의 `forklift_b_rigged_cm.usd`다.

## 이 실습의 의도

외형만 있는 지게차를 8개 강체와 7개 가동 joint로 나누고, 수동 roller·구동 뒷바퀴·조향·lift가 맡는 운동을 직접 설계한다. cm 단위 asset을 그대로 사용하여 geometry 크기, 직선 이동 범위, 중력을 같은 단위로 맞추는 것도 핵심이다. `run.py`는 unrigged 원본을 로컬 layer로 열고 초기 목록만 저장하므로, rigging과 주행·lift 조작은 아래 GUI 단계에서 수행한다.

## 실행 후 확인할 것

- **단위와 링크:** 초기 `initial_inventory.json`의 `meters_per_unit=0.01`을 확인한다. 제작 후 body·lift·back_wheel·back_wheel_swivel·roller 네 개가 각각 강체로 묶이고, 자식 collider에 강체가 중복 적용되지 않았는지 Stage에서 본다.
- **7개 관절 구성:** `inspect_result.py`를 Script Editor에서 실행해 movable joint가 7개인지 확인한다. 출력된 body0/body1·axis·limit·drive를 `joint_spec.json`과 직접 대조한다. 도구는 관절 수를 자동 검사하지만 연결·설정값 전체가 spec과 같은지 자동 판정하지는 않는다.
- **roller와 구동의 차이:** 네 roller joint에는 drive가 없고, `rear_drive`는 X축 속도 목표 -200 deg/s를 가진다. 완성 후 Play에서 뒷바퀴 구동으로 차체가 움직이고 앞 roller는 접촉에 따라 수동으로 구르는지 본다. 모든 바퀴에 같은 목표를 넣는 구성이 아니다.
- **lift·조향 반응:** lift 목표를 -15→50 cm로 바꾸면 Z축을 따라 올라가고, `rear_steer` 목표만 0→20 deg로 바꾸면 뒷바퀴 방향과 주행 경로가 달라지는지 확인한다. joint 범위 -15..200 cm와 -60..60 deg는 서로 다른 단위다.
- **접촉과 완료 판정:** collider 표시에서 fork의 빈 공간이 막히지 않고 바퀴의 윤곽이 매끈하게 맞는지 본다. 관절 수 검사 통과와 별도로 Play 직후 링크 분리·급격한 튀기·바퀴 떨림 없이 주행과 lift가 가능한지 관찰하고 결과를 저장한다.

## 실행과 준비

Isaac Sim **5.1.0**, RTX GPU, GUI, 위 forklift asset을 읽을 수 있는 assets root가 필요하다. 다른 로컬 패키지는 필요 없다. 기본 구성: 강체는 같이 움직이는 부품 묶음, collider는 접촉 표면, joint는 두 강체의 허용 운동, articulation은 이 joint들을 물리 solver의 트리로 묶는 정보다.

```bash
cd src/39_robot_setup_rig_mobile_robot
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

창은 실습을 마칠 때까지 열린다. Ctrl+S는 `output/first/stage.usda`에 override를 저장한다. 원본 asset 경로를 authoring layer로 선택하지 않는다. `initial_inventory.json`의 단위가 0.01 m인지 확인한다. 다시 열 때는 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다.

## 링크와 collider 준비

1. 자유도를 먼저 종이에 적는다: 앞 roller wheel 4개는 무구동 회전, lift 1개는 구동 직선 이동, 뒤 wheel 회전 1개와 steering 회전 1개, 총 7개다.
2. Stage에 Xform `body`, `lift`, `back_wheel`, `back_wheel_swivel`, `roller_front_left`, `roller_front_right`, `roller_back_left`, `roller_back_right`를 만든다. source asset의 Looks 위쪽 geometry는 lift, Right Chain Wheel부터 Body Glass는 body에 속한다. 남은 wheel/swivel geometry를 각각 올바른 Xform 아래로 옮긴다. 지지대처럼 body와 함께 움직이는 고정 부품은 body에 포함한다.
3. 각 링크 Xform에 **+ Add → Physics → Rigid Body**를 적용한다. **강체 안에 또 다른 강체**를 만들지 않는다. wheel 중심에 Xform을 맞출 때 geometry의 Translate와 Translate:pivot을 합한 값을 parent 위치로 쓰고 geometry Translate는 pivot의 음수로 바꾼다. 옮기기 전후 world 위치가 유지되는지 확인한다.
4. body/lift의 기존 collider를 조사한다. eye → **Show By Type → Physics → Colliders → Selected**. fork의 빈 공간을 convex hull이 막으면 **Convex Decomposition**을 사용한다. swivel도 필요 시 decomposition으로 바꾼다.
5. wheel에는 매끈한 cylinder collider를 둔다. 앞 wheel용 cylinder scale=(0.16,0.16,0.08), Rotate Y=90; 뒤 wheel=(0.3,0.3,0.1), Rotate Y=90을 원본 수업 기준으로 사용한다. 해당 wheel Xform 아래에서 위치를 맞추고 **Collider**만 적용한다. 부모에 이미 rigid body가 있다. 시각용 cylinder는 숨기고 collider 표시로 둘레가 wheel과 맞는지 본다.

## joint와 drive 작성

6. body와 lift를 연결하는 **Create → Physics → Joints → Prismatic Joint**를 만들고 `lift_slide`로 이름을 정한다. axis=Z, limits=-15..200, **Linear Drive** target position=-15, stiffness=100000, damping=10000이다. 길이 값은 cm이다.
7. body와 각 roller를 **Revolute Joint**로 연결한다. axis=X, joint origin은 wheel 중심, angular drive는 추가하지 않는다. 네 joint를 roller_joints Scope에 모은다. body0/body1 관계를 매번 Property에서 확인한다.
8. back_wheel_swivel→back_wheel의 `rear_drive` revolute를 만들고 axis=X, Angular Drive stiffness=100, damping=10000으로 둔다. body→back_wheel_swivel의 `rear_steer`는 axis=Z, limits=-60..60 **deg**, stiffness=100000, damping=100이다.
9. 루트 `SMV_Forklift_B01_01`에 Articulation Root가 있는지 확인하고 Self Collision은 끈다. root가 이미 있으면 중복으로 추가하지 않는다. **Create → Physics → Physics Scene**, **Ground Plane**을 추가하고 stage 단위에 맞는 중력을 확인한다. cm stage에서 9.8 m/s²는 980 stage-unit/s²다.
10. `rear_drive` target velocity=-200 **deg/s**로 두고 Play. forklift가 전진하고 네 roller가 수동적으로 굴러가는지 본다. lift target을 -15→50으로 바꿔 위로 움직이는지 확인한다.
11. **Window → Script Editor**에서 `inspect_result.py`를 실행한다. revolute/prismatic joint가 7개인지 검사하고 body relationship, axis, limit, drive가 출력된다. 출력값을 `joint_spec.json`과 직접 대조한다. 도구는 실제 운동이나 모든 수치의 일치를 자동 검사하지 않으므로 접촉과 주행 안정성은 실제 화면에서 확인한다.

## 단위 변환과 마무리

`joint_spec.json`은 원본 cm stage의 값이다. 새 meter stage에 reference할 때 Metrics Assembler가 변환을 처리하는지 확인하고, 같은 폴더의 meter 완성 asset과 크기를 비교한다. **metersPerUnit만 바꾸는 것은 geometry와 drive/관성 값을 모두 올바르게 변환하는 작업이 아니다.** wheel radius, linear joint limit, 중력, mass/inertia가 일관되어야 한다.

한 변수 실험은 steering target만 0→20 deg로 바꿔 주행 방향을 관찰하는 것이다. collider가 초기에 겹치면 Play 직후 폭발적인 움직임이 날 수 있으므로 joint gain을 임의로 키우기 전에 충돌 윤곽을 확인한다. wheel이 떨리면 collision 근사의 매끈함과 axis 정렬을 본다.

검증 범위: Python 문법·CLI, 공식 asset URL 접근 확인. 실제 GUI rigging·주행은 미검증이다.

## 출처

- [Isaac Sim 5.1 Rig a Mobile Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html)
- [Joints and drives](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html#add-joints-and-drives), [Unit conversion](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_mobile_robot.html#converting-asset-to-a-different-unit)
