# 42. 같은 로봇을 USD·URDF·Lula 설정으로 표현하기

## 이번에 배우는 것

**UR10e의 관절 이름과 초기 자세, 충돌 구를 내보내고 서로 다른 파일이 같은 로봇을 설명하는지 확인합니다.**

USD에서 잘 움직이는 로봇을 운동 계획기에 바로 넘길 수 있는 것은 아닙니다. 계획기는 링크와 관절의 구조, 움직일 관절 집합, 충돌을 판단할 형상을 별도 설정으로 읽습니다. 이번에는 그 정보를 직접 작성하고 이름과 값이 연결되는지 검사합니다.

| 결과물 | 담는 내용 | 이번 확인 방법 |
|---|---|---|
| `lula_ready.usda` | 편집 가능한 로봇 장면 | instance 해제와 실제 관절 목록 |
| `ur_gripper.urdf` | 링크·관절 구조와 mesh 경로 | XML의 이름과 참조 파일 |
| `ur10e.yaml` | Lula의 cspace·default_q·충돌 구 | URDF와 교차 검사 |
| `ur10e.xrdf` | cuMotion용 로봇 설정 | GUI export와 파일 확인 |

**cspace**는 계획기가 움직일 관절 좌표 집합입니다. 이번에는 팔의 여섯 관절만 넣고, 별도로 제어할 그리퍼 관절은 고정된 값으로 다룹니다.

## 1. 로봇을 편집할 수 있는 상태로 준비하기

Isaac Sim 5.1.0, 지원 GPU와 공식 구성 완료 에셋 접근이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/42_robot_setup_generate_robot_config/run.py \
  --output src/42_robot_setup_generate_robot_config/output/prepared
```

기본 입력은 `/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd`입니다. 자신의 구성 파일은 `--asset`으로 지정할 수 있습니다.

실행기는 `lula_ready.usda`와 `preparation_report.json`을 만든 뒤 창을 유지합니다. **URDF·YAML·XRDF는 아직 생성하지 않습니다.** 아래 GUI 단계에서 직접 내보냅니다. `--steps`는 앱 갱신 한도이며 자동 Play가 아닙니다. Headless에서 생략하면 `--frames`의 기본값인 1200회가 적용됩니다.

### 코드에서 볼 부분

공유된 인스턴스 내부는 개별 편집이 제한되므로 실행기는 다음 작업을 반복합니다.

```python
instances = [prim for prim in Usd.PrimRange(root) if prim.IsInstance()]
for prim in instances:
    changed.append(str(prim.GetPath()))
    prim.SetInstanceable(False)
```

한 겹을 해제한 뒤 더 안쪽의 인스턴스가 보일 수 있어, 남은 인스턴스가 없을 때까지 다시 조사합니다. 이것은 mesh를 새 모양으로 만드는 작업이 아니라 각 링크의 형상을 편집 도구에서 다룰 수 있게 하는 준비입니다.

### 실행 결과 확인하기

보고서의 `uninstanced_prims`는 실제로 해제한 경로이고 `joints`는 장면에서 읽은 관절입니다. `active_arm_joints`는 코드에 적힌 **권장 여섯 이름**입니다. 그 필드가 있다고 Lula에서 Active 설정까지 끝난 것은 아닙니다.

이후 GUI 편집을 보존하려면 **File > Open으로 출력된 `lula_ready.usda`를 다시 여세요.** 실행기는 메모리상의 장면을 Export했으므로, 출력 파일을 명시적으로 작업 대상으로 삼는 것이 저장 위치를 확인하기 쉽습니다.

## 2. 관절 집합과 충돌 구를 내보내기

### 설정에서 볼 부분: URDF와 cspace

1. **Window > Extensions**에서 **Isaac Sim USD to URDF Exporter**를 켭니다. 검색되지 않으면 `@feature` 필터를 제거합니다.
2. 저장소의 `src/42_robot_setup_generate_robot_config/output/exports` 폴더를 만들고 **File > URDF Exporter**를 엽니다. 공식 튜토리얼의 **Export URDF**는 이 내보내기 도구를 가리킵니다. 파일을 이 폴더의 `ur_gripper.urdf`로 정하고 **Root Prim Path=/ur**, mesh 출력은 같은 폴더 아래 `meshes`로 지정한 뒤 내보냅니다.
3. **Isaac Sim Lula** 확장을 켜고 **Play**합니다.
4. **Tools > Robotics > Lula Robot Description Editor**에서 `ur` articulation을 선택합니다.
5. 아래 여섯 joint를 **Active Joint**, 그리퍼 finger/knuckle 관절을 **Fixed Joint**로 둡니다.

```text
shoulder_pan_joint, shoulder_lift_joint, elbow_joint,
wrist_1_joint, wrist_2_joint, wrist_3_joint
```

YAML에서 `cspace`와 `default_q`는 같은 순서로 대응합니다. 예를 들어 `cspace[0]`이 shoulder_pan_joint라면 `default_q[0]`은 그 관절의 시작 각도이며 단위는 rad입니다. 길이가 같더라도 순서가 다르면 다른 자세를 뜻하므로 이름과 값을 함께 확인하세요. `cspace_to_urdf_rules`의 고정 그리퍼 값도 USD에서 출발할 자세와 맞춰야 합니다.

### 설정에서 볼 부분: 충돌 구

Lula가 사용할 충돌 형상은 여러 구로 근사합니다. 긴 링크를 구 하나로 덮으면 불필요하게 넓어질 수 있으므로 여러 구를 배치합니다.

1. Select Link에서 `upper_arm_link`를 선택합니다.
2. Link Sphere Editor의 **Generate Spheres > Select Mesh**에서 `/collisions/upperarm/mesh`에 해당하는 mesh를 선택합니다.
3. **Radius Offset=0.03**, **Number of Spheres=8**로 preview를 만듭니다.
4. 빨간 구들이 링크를 덮는지 보고 **Generate Spheres**로 확정합니다. 확정된 cyan 구를 필요에 따라 조정합니다.
5. 나머지 팔과 그리퍼 링크에도 구를 배치합니다. 자동 생성이 어려운 mesh는 수동으로 구를 추가하고 사이를 채웁니다.

이 구는 PhysX Collider와 별개입니다. 너무 작은 구는 계획 단계에서 충돌을 놓칠 수 있고, 너무 큰 구는 실제로 통과할 공간까지 막을 수 있습니다. 따라서 파일 형식 검사와 별도로 **화면에서 형상을 덮는 정도**를 확인해야 합니다.

설정과 구 배치를 마친 뒤 **Play와 Editor를 유지한 상태에서** Export To File을 사용합니다. **Export to Lula Robot Description File**로 앞서 만든 exports 폴더의 `ur10e.yaml`, **Export to cuMotion XRDF**로 같은 폴더의 `ur10e.xrdf`를 각각 저장하세요. 편집 중 Stop하거나 도구를 닫으면 임시 작업을 잃을 수 있으므로 파일을 확인한 뒤 종료합니다.

### 실행 결과 확인하기

세 파일과 mesh 폴더가 존재하는지 확인한 후 저장소 루트에서 검사기를 실행하세요. 이 도구는 시뮬레이터를 시작하지 않으며 XML과 YAML을 읽습니다.

```bash
~/isaacsim/python.sh src/42_robot_setup_generate_robot_config/validate_exports.py \
  src/42_robot_setup_generate_robot_config/output/exports/ur_gripper.urdf \
  src/42_robot_setup_generate_robot_config/output/exports/ur10e.yaml
```

| 자동 검사 | 직접 확인할 내용 |
|---|---|
| cspace joint가 URDF에 존재하는지 | 그 순서와 각도의 의미가 맞는지 |
| cspace와 default_q 길이가 같은지 | 실제 USD의 출발 자세와 일치하는지 |
| sphere link가 URDF에 존재하는지 | 구가 해당 링크의 형상을 덮는지 |
| 반지름이 양수, 중심이 3성분인지 | 구의 크기·위치가 적절한지 |
| 충돌 구가 하나 이상인지 | 필요한 모든 링크를 포함했는지 |

성공하면 `urdf_links`, `active_joints`, `collision_spheres`가 출력됩니다. **XRDF 내용과 mesh 경로는 이 검사기의 입력 대상이 아닙니다.** URDF에서 실제 mesh 참조를 열어 보고, XRDF도 별도 파일로 확인하세요.

## 3. 같은 이름이 파일을 연결하는 방식 정리

```text
USD의 joint/link
    → URDF의 joint/link 이름
    → YAML cspace와 collision_spheres의 이름
    → 계획기가 제어하고 검사할 대상
```

계획기의 로봇 표현은 물리 articulation 전체와 같을 필요가 없습니다. 팔 여섯 관절을 움직이되 그리퍼는 고정 형상으로 취급할 수 있습니다. 다만 그 선택이 실제 제어 방식과 일치해야 합니다. 이름 하나가 달라져도 계획기가 다른 링크를 참조하거나 초기화에 실패할 수 있습니다.

## 4. 간단한 확인 실험

같은 `upper_arm_link`와 mesh, Radius Offset을 유지하고 **Number of Spheres만 8에서 4로** 줄여 preview를 비교하세요. 기존 확정 구를 남긴 채 새 구를 중복 추가하지 않도록 preview 단계에서 먼저 관찰합니다.

구 사이의 빈틈과 링크 바깥으로 벗어나는 정도를 비교해 보세요. 적은 수가 언제나 나쁜 것은 아니지만 개수만으로 형상 충실도를 판단할 수는 없습니다. 선택한 근사를 확정했다면 새 파일로 export하고 검사 결과의 구 개수도 함께 기록하세요.

## 실행할 때 막히면

- **출력에 YAML이나 URDF가 없습니다**: `run.py`는 USD 준비만 합니다. Exporter와 Lula Editor에서 직접 저장하세요.
- **Lula에서 로봇을 선택할 수 없습니다**: Play 상태, 확장 활성화, 로봇 articulation과 인스턴스 해제를 확인하세요.
- **`Active joints absent from URDF`가 나옵니다**: YAML과 실제 URDF의 이름을 대조하세요. 내보내기 과정에서 `/`가 `_`로 바뀌는 경우도 조사합니다.
- **구 생성이 실패하거나 엉뚱한 형상을 덮습니다**: 선택한 링크와 mesh를 확인하고, 자동 생성에 적합하지 않은 열린 mesh는 수동 구를 사용하세요.
- **검사 통과 후 mesh가 보이지 않습니다**: 검사기는 mesh 파일을 열지 않습니다. URDF와 내보낸 mesh 폴더를 함께 보존하고 경로를 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 8: Generate Robot Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html)에 대응합니다. 로컬 준비기와 검사기를 원문의 GUI export 과정에 연결했습니다.

`tutorial.json`은 `not_run`입니다. 실제 GUI export, 충돌 구의 덮임, XRDF 소비 도구와 운동 실행은 미검증입니다. 이름·길이·기본 구 형상 검사는 이들 동작 검증과 구분합니다.
