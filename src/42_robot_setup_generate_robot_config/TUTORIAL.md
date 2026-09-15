# 42. UR10e URDF·Lula YAML·XRDF를 생성하고 맞춰 보기

권장 학습 순서 **42** · 로봇 자산 가져오기와 제작 · 출처 ID `t126`

공식 인덱스 **t126** · Isaac Sim **5.1.0**

## 결과와 준비

공식 USD to URDF Exporter와 Lula Robot Description Editor로 URDF, joint cspace, collision spheres, Lula YAML, cuMotion XRDF를 생성하는 GUI 실습입니다. 이 폴더의 `run.py`는 실제 준비 에셋의 인스턴스를 해제하고 관절 목록을 저장하며, `validate_exports.py`는 사용자가 내보낸 URDF/YAML의 이름과 형상을 교차 검사합니다. Exporter/Lula 편집 자체를 자동 구현했다고 주장하지 않습니다.

Isaac Sim 5.1.0과 GPU, 다음 공식 구성된 에셋이 필요합니다. 이전 로컬 패키지를 실행하지 않아도 됩니다.
`/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd`
공식 Lula 준비 완료 파일은 같은 폴더의 `ur_gripper_lula.usd`입니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 1200회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

`output/<고유번호>/lula_ready.usda`와 `preparation_report.json`이 생깁니다. 파일은 원본 reference 위의 local override이며 원본 에셋 접근은 계속 필요합니다. `--output`은 새 폴더만 허용합니다. 프로그램은 timeline을 자동 Play하지 않습니다. 창에서 편집을 마친 뒤 로컬 layer를 저장하고 직접 닫습니다. `--steps`를 지정한 한정 실행에서는 해당 GUI 갱신 횟수 후 종료합니다.

## 1. URDF 내보내기

1. Window > Extensions에서 **Isaac Sim USD to URDF Exporter**를 검색해 Enable합니다. 안 보이면 검색의 `@feature` 필터를 제거합니다.
2. `lula_ready.usda` 또는 공식 구성 에셋을 엽니다. File > Export URDF를 선택합니다.
3. 이 폴더의 새 출력 디렉터리에 파일 이름 **ur_gripper.urdf**를 지정하고 Mesh Directory Path도 같은 작업의 새 `meshes/` 폴더로 지정합니다. Export를 누릅니다.
4. URDF를 텍스트 편집기로 열어 link/joint 이름과 mesh 상대 경로를 확인합니다. mesh를 사용하려면 내보낸 URDF와 해당 mesh 폴더를 함께 보존합니다.

USD는 scene 합성/시각/물리를 담는 형식이고 URDF는 로봇 link/joint tree를 담는 형식입니다. USD의 모든 그래픽/시뮬레이션 기능이 URDF에 동일하게 표현되지는 않습니다.

## 2. Lula에서 편집할 준비

1. Window > Extensions에서 **Isaac Sim Lula**를 Enable합니다.
2. 직접 준비한다면 Stage에서 모든 visuals와 collisions Prim을 검색해 Property의 **Instantiable**을 해제합니다. `run.py` 출력은 이 과정을 현재 local layer에 적용한 상태입니다.
3. **Play를 누릅니다.** Tools > Robotics > Lula Robot Description Editor를 엽니다. Selection Panel에서 `ur` articulation을 선택합니다.
4. Set Joint Properties에서 팔의 `shoulder_pan_joint`, `shoulder_lift_joint`, `elbow_joint`, `wrist_1_joint`, `wrist_2_joint`, `wrist_3_joint`를 **Active Joint**로 지정합니다.
5. Robotiq의 finger/knuckle joint는 **Fixed Joint**로 둡니다. 그리퍼는 별도 제어되므로 팔 위치 최적화 cspace에 넣지 않습니다.
6. `default_q`와 `cspace_to_urdf_rules`의 고정 joint 값이 USD 초기 pose와 맞는지 확인합니다. 다르면 controller 초기화 때 같은 pose로 맞춰야 합니다.

인스턴스는 공통 mesh 데이터를 공유하는 USD 방식입니다. Lula editor는 개별 mesh 편집/분석이 필요하므로 이 실습에서는 instanceable을 해제합니다. cspace는 motion solver가 실제로 움직일 일반화 좌표 집합이며 articulation의 모든 DOF와 항상 같지 않습니다.

## 3. Collision sphere 생성

**이제 YAML/XRDF 내보내기를 끝낼 때까지 Stop을 누르거나 Lula editor를 닫지 않습니다.** 편집 중 임시 상태를 잃으면 joint 설정/구 생성을 다시 해야 할 수 있습니다.

1. Selection Panel/Select link=`upper_arm_link`를 선택합니다.
2. Link Sphere Editor > Generate Spheres > Select Mesh에서 `/collisions/upperarm/mesh`를 선택합니다.
3. Radius Offset=**0.03**, Number of Spheres=**8**을 지정합니다. 빨간 preview sphere 여덟 개가 긴 링크를 덮는지 봅니다.
4. Generate Spheres를 눌러 cyan sphere로 확정합니다. 필요한 경우 위치를 드래그해 조정합니다.
5. 나머지 팔과 그리퍼 link에도 반복합니다. 긴 link는 양 끝을 잡고 Add Spheres로 사이를 채우거나 Scale Spheres in Link로 크기를 조정합니다.
6. 삼각형 mesh가 watertight하지 않아 자동 생성이 실패하면 수동 sphere를 추가하고 연결합니다. 모든 시각 mesh에서 자동 생성이 보장되지는 않습니다.

Sphere는 Lula의 충돌 근사이며 PhysX의 실제 contact collider와 다릅니다. 너무 작으면 장애물을 놓치고 너무 크면 가짜 충돌로 motion이 막힙니다. 많을수록 근사가 세밀하지만 계산량도 늘어납니다.

## 4. YAML과 XRDF 내보내기

1. Play를 유지한 채 Export To File > Export to Lula Robot Description File에서 이 폴더 출력 경로의 **ur10e.yaml**을 지정하고 Save합니다.
2. Export to cuMotion XRDF에서 **ur10e.xrdf**도 내보냅니다.
3. 두 파일을 확인한 뒤에만 Stop합니다. YAML의 cspace 6개와 collision_spheres를 직접 읽습니다.
4. 생성한 URDF와 YAML을 이 폴더의 도구로 검사합니다. 이 명령은 시뮬레이터를 시작하지 않습니다. Isaac Python에 포함된 PyYAML을 사용합니다.

```bash
"$ISAAC_SIM_ROOT/python.sh" validate_exports.py output/내_내보내기/ur_gripper.urdf output/내_내보내기/ur10e.yaml
```

검사는 실제 URDF에 없는 cspace joint, 존재하지 않는 sphere link, cspace/default_q 길이 불일치, 잘못된 sphere 반지름/중심, 빈 sphere 목록을 오류로 보고합니다. 형식 검사 통과가 collision coverage나 motion 성능을 검증하지는 않습니다.

성공은 유효한 세 파일을 생성하고 sphere가 링크를 덮는 것을 GUI에서 확인하는 것입니다. 한 변수 실험으로 upperarm의 sphere 수만 8→4로 바꿔 근사 빈틈을 비교합니다. 링크 이름이 `ee_link/...`와 `ee_link_...`처럼 export 과정에서 바뀌면 YAML과 URDF의 실제 이름을 일치시켜야 합니다. 이름 검사를 우회하지 않습니다.
## 버전 고정 출처

- [NVIDIA Isaac Sim 5.1.0 — Tutorial 8: Generate Robot Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html)

한국어 절차는 새로 작성했습니다. 원문 GUI 기능과 이 폴더의 준비/검사/실행 코드를 구별해 설명합니다. 실제 runtime 검증 범위는 tutorial.json의 verification 기록을 확인합니다.
