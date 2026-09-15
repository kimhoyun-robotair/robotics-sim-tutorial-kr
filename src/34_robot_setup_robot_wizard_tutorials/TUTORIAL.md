# 34. Robot Wizard로 3링크 로봇 만들기

권장 학습 순서 **34** · 로봇 자산 가져오기와 제작 · 출처 ID `t115`

공식 Robot Wizard Tutorial의 **GUI native** 실습이다. 실행기는 공식 `/Isaac/Samples/Rigging/RobotWizard/raw_blocks.usd`를 새 로컬 편집 layer로 열고, Wizard에서 실제 로봇 계층·joint·drive를 작성한다. Isaac Sim 5.1 assets root에서 이 파일을 읽을 수 있어야 한다. 원격 asset pack을 쓰거나 동일 버전 로컬 pack을 설정한다.


## 이 실습의 의도

Robot Wizard가 원시 도형을 링크·충돌 형상·관절·drive·articulation으로 조직하는 과정을 직접 익힌다. world에 고정된 link1, 직선 이동하는 link2, 회전하는 link3를 만들어 서로 다른 joint와 drive의 역할을 한 장면에서 비교한다. `run.py`는 `raw_blocks.usd`와 로컬 편집 layer를 열어 초기 구조만 기록하며, Wizard 조립·저장·Play는 아래 GUI 절차에서 사용자가 수행한다.

## 실행 후 확인할 것

- **시작과 완료 구분:** 실행 직후의 도형은 아직 Wizard에서 완성한 로봇이 아니다. `initial_inventory.json`은 GUI 편집 전의 강체·joint·root 목록이므로, 편집 후 결과가 자동 반영되는 최종 성적표로 읽지 않는다.
- **링크 구조:** Wizard 작업 후 `wizard_robot` 아래에 `link1`, `link2`, `link3`가 있고 지정한 도형이 각 링크로 묶였는지 Stage에서 확인한다. 자료용 `meshes`·`visuals`·`colliders` Scope의 원본이 겹쳐 보이면 visibility를 조정하고 실제 링크 위치는 유지한다.
- **연결과 목표:** Property에서 `fixed_joint`는 world→link1, `slider_joint`는 link1→link2의 X축, `rotate_joint`는 link2→link3의 Z축인지 확인한다. slider의 범위는 0..3, 위치 목표는 1이며 rotate는 속도 목표 100 deg/s와 양의 damping이 필요하다.
- **Play 후 운동:** link1이 고정된 채 link2가 slider 목표로 이동하고 link3가 계속 회전하는지 본다. link3가 멈추지 않는 것은 속도 목표를 유지하는 의도된 결과다. slider 목표만 2로 바꿨을 때 정착 위치가 달라지는지도 비교한다.
- **저장 결과:** Save Robot 결과의 root와 base/physics 구성 파일을 열어 세 joint의 body 관계와 drive가 저장되었는지 확인한다. `--headless --steps ...`로 원본이 열린 것만 확인한 실행은 이 GUI 제작·운동 확인을 대신하지 않는다.

## 실행 환경과 파일

Isaac Sim **5.1.0**, 지원되는 RTX GPU와 GUI가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 설치 디렉터리다. Python CLI 도움말은 일반 Python에서도 열린다. 이 패키지는 자체 코드/설정을 가지며 다른 로컬 튜토리얼을 import하지 않는다.

```bash
cd src/34_robot_setup_robot_wizard_tutorials
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

기본 실행은 창을 계속 열어 두므로 아래 GUI 실습을 수행하고 **Ctrl+S**로 로컬 root layer를 저장한 뒤 창을 닫는다. `output/first/stage.usda`와 `initial_inventory.json`이 생긴다. 기존 output은 덮어쓰지 않으므로 다음 실행은 `output/second`처럼 새 경로를 쓴다. 저장한 실습을 다시 열려면 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다. 재개 시에도 새 로컬 layer가 이전 결과를 참조한다.

GPU/UI 자동 점검을 위한 한정 실행은 `--headless --steps 120 --output output/check`다. 이는 장면 로드 확인만 하며 GUI 작업이나 로봇 동작의 성공을 증명하지 않는다. 패키지 작성 과정에서는 문법·CLI를 확인했으며 GPU와 실제 GUI 조작은 미검증이다.


## 실습: 각 화면이 무엇을 만드는가

1. **Window → Extensions**에서 `isaacsim.robot_setup.wizard`를 켜고 **Window → Robot Wizard**를 연다. **Configure a Robot on Stage**, Robot Type **custom**, 이름 **wizard_robot**을 선택한다. **Select Robot Parent Xform**은 `/World`를 지정하고 **Prepare Files**로 진행한다.
2. Robot Root Folder는 이 패키지의 새 `output/wizard_robot`로 정한다. **Save a Copy in Robot Root Folder**를 체크하고 Next. 원격 원본이 아니라 자신의 output에 새 구성을 저장하는지 확인한다.
3. **Robot Hierarchy → New Links Structure**에 `wizard_robot/link3`를 추가한다. Cube/Cone은 link1, Cylinder는 link2, Cylinder_01/Cube_01은 link3로 옮긴다. **Add Colliders**를 클릭한다. Stage에서 robot 직계 자식으로 세 링크가 생겨야 한다.
4. Stage에 새로 생긴 `meshes`, `visuals`, `colliders` Scope를 조사한다. meshes는 원본 기하, visuals는 렌더링 reference, colliders는 충돌 reference다. 원점에 겹쳐 보이는 원본 자료는 이 세 scope를 Hide하여 숨긴다. 링크의 실제 위치를 0으로 바꾸는 것은 해결책이 아니다.
5. 이 기본 도형 예제에서는 기본 collider를 사용한다. **Add Joints & Drives**에서 아래 표의 joint 3개를 만든다. 첫 둘은 Create, 마지막은 Create & Close.

| 이름 | 종류/축 | parent → child | drive |
|---|---|---|---|
| fixed_joint | Fixed | world → link1 | 없음 |
| slider_joint | Prismatic / X | link1 → link2 | force |
| rotate_joint | Revolute / Z | link2 → link3 | force |

6. `slider_joint`의 범위는 0..3, target position=1, stiffness=100000, damping=20000. `rotate_joint`는 **Joint Range is Limited** 해제, target velocity=100, stiffness=0으로 설정한다. USD revolute drive의 각속도는 **degree/s**다. velocity drive에 damping이 0이면 토크가 없으므로 양의 damping 값을 확인한다.
7. **Save Robot**에서 articulation root를 `fixed_joint`로 지정하고 light와 physics scene을 포함시킨다. world에 고정된 로봇이므로 ground는 선택이다. 저장 후 Play: link2가 목표 위치로 이동하고 link3가 계속 회전하는지 관찰한다.
8. Layers에서 base와 physics 구성을 확인한다. 기하/링크 구조는 base, `RigidBodyAPI`, `CollisionAPI`, `Joint/DriveAPI`는 physics layer에 저장된다. root 설정만 보고 완료로 판단하지 말고 세 joint의 body0/body1 및 drive 값을 Property에서 다시 확인한다.

## 해설과 관찰 기준

**Prim**은 USD 장면의 노드, **Xform**은 변환을 가진 노드, **Scope**는 구조 정리용 노드다. 링크는 같이 움직이는 강체이고 joint가 링크 사이 허용 운동을 정한다. articulation은 강체와 joint를 효율적으로 함께 풀기 위한 물리 트리다. fixed joint를 root로 선택하면 world에 고정된 base가 명확해진다. Robot Schema의 Robot/Link/Joint API는 편집 도구가 로봇 의미를 찾는 정보이고 물리 API와 역할이 다르다.

확인할 파일은 최상위 robot USD와 `configurations` 안의 base/physics/robot 구성이다. 참조 경로가 자기 output을 가리키는지 확인한다. 비교 기준은 assets root `/Isaac/Samples/Rigging/RobotWizard/final/`이다. 원본 로봇 파일을 변경해 비교하지 않는다.

한 변수 실험은 slider target 1→2로 바꾸기다. 범위 0..3 안에서 정착점만 달라지는지 확인한다. 움직이지 않으면 Play, root 고정 joint, body target과 damping을 확인한다. shape가 중복되어 보이면 자료용 scope의 visibility부터 확인한다. Window 메뉴가 없으면 extension 필터의 `@feature`를 지우고 검색한다.

## 출처

- [Isaac Sim 5.1 Robot Wizard Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/robot_wizard_tutorials.html)
- 로컬 설명/코드는 해당 버전의 실제 GUI 작업을 재구성한 실습이며 NVIDIA 문서 전문을 복제하지 않는다.
