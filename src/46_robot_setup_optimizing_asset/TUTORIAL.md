# 46. 같은 Jetbot 외형을 더 적은 중복으로 표현하기

## 이번에 배우는 것

**한 링크 안의 mesh를 합치고 같은 바퀴 형상을 공유하면서, 외관과 물리 구조가 유지되는지 확인합니다.**

CAD에서 가져온 로봇은 작은 부품마다 mesh가 나뉘어 있을 수 있습니다. 하지만 같이 움직이는 한 링크의 외형을 언제나 많은 mesh로 나눌 필요는 없습니다. 또한 좌우 바퀴가 같은 모양이라면 원본 형상을 공유할 수 있습니다. 이번에는 이 두 작업을 나누어 적용합니다.

| 작업 | 바꾸는 것 | 보존할 것 |
|---|---|---|
| Mesh merge | 한 링크 안의 여러 시각 mesh를 통합 | 재질과 최종 외형 |
| Internal reference | 같은 Stage의 형상을 참조 | 각 링크의 배치 |
| Instanceable | 참조 구성을 공유하는 인스턴스 허용 | 동일하게 사용할 형상 |
| 구조 검사 | mesh·prototype·instance 목록 읽기 | 강체와 관절 연결 |

Mesh 수가 줄었다는 사실만으로 FPS가 개선되었다고 판정하지 않습니다. 이번에는 먼저 **무엇이 공유되었고 무엇이 그대로 남았는지** 확인합니다.

## 1. 원본 구조와 비교 기준 기록하기

Isaac Sim 5.1.0, RTX GPU, GUI와 Mesh Merge Tool이 필요합니다. 기본 입력은 `/Isaac/Samples/Rigging/Jetbot/Jetbot_Base/Jetbot_base.usd`입니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/46_robot_setup_optimizing_asset/run.py \
  --output src/46_robot_setup_optimizing_asset/output/first
```

원본 위에 로컬 `stage.usda`를 만들고 최초 물리 목록을 `initial_inventory.json`에 저장합니다. Layers에서 로컬 root를 편집 대상으로 선택하세요. **Edit > Preferences > Stage > Authoring > Inherit Parent Transform**을 켭니다.

**Window > Script Editor**에서 이 폴더의 `inspect_meshes.py` 전체를 실행하고 출력을 별도 메모에 보관하세요. 이 도구는 보고서 파일을 자동 저장하지 않습니다.

### 코드에서 볼 부분

검사기는 인스턴스 내부까지 순회합니다.

```python
for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
```

여기서 instance proxy는 공유된 인스턴스 내부를 각 배치 위치에서 볼 때의 prim입니다. 일반 순회에서는 그 내부가 드러나지 않을 수 있어 별도 순회 옵션을 사용합니다. mesh가 목록에서 사라졌다는 이유만으로 geometry가 삭제되었다고 오해하지 않도록 하기 위함입니다.

### 실행 결과 확인하기

| 출력 항목 | 의미 |
|---|---|
| `mesh_occurrences` | 순회에서 발견한 mesh 사용 위치 수 |
| `meshes[].faces` | 해당 mesh의 면 개수 |
| `meshes[].instance_proxy` | 인스턴스 내부에서 관찰한 mesh인지 |
| `instance_roots` | 실제 인스턴스 root 경로 |
| `prototypes` | USD가 구성한 공유 prototype 수 |

`mesh_occurrences`는 GPU 메모리 사용량이나 고유 mesh 데이터 개수와 같지 않습니다. 공유된 형상도 배치된 곳마다 관찰될 수 있습니다. 원본 형상을 보관할 `/Visuals` 아래 mesh 역시 순회에 포함될 수 있으므로 전체 숫자와 개별 경로를 함께 읽으세요.

## 2. mesh 통합과 형상 공유 적용하기

### 설정에서 볼 부분: 한 링크 안에서 합치기

1. Stage 메뉴에서 **Show Root**를 켜고 root 바로 아래 Xform `Jetbot_Sim`을 만듭니다. 우클릭 **Set as Default Prim**으로 지정합니다.
2. Root 아래에 형상 원본을 보관할 `Visuals` Scope도 만듭니다.
3. 기존 Jetbot의 물리 링크와 관절을 `Jetbot_Sim` 아래에 정리합니다. Reparent 전후 world 위치가 유지되고 joint Body0/Body1이 새 링크를 가리키는지 확인합니다.
4. 이동 때문에 원래 `/Jetbot` 아래 링크가 inactive로 남았다면 해당 원본 링크를 선택해 우클릭 **Activate**로 다시 보이게 합니다. 이 원본은 다음 병합의 입력입니다. 새 `/Jetbot_Sim` 링크에서는 대체할 **시각 geometry 자식만** 정리하고 Rigid Body, Collider, Joint는 보존하세요. 이 중간 상태에서 두 로봇을 함께 Play하지 말고 형상 정리를 먼저 마칩니다.
5. **Tools > Robotics > Asset Editors > Mesh Merge Tool**에서 원본 `Jetbot/left_wheel`을 선택합니다.
6. **Clear Parent Transform**은 끄고, **Combine Materials**와 **Deactivate source assets**를 켜고 material destination을 `/Jetbot_Sim/Looks`로 지정해 Merge합니다. 병합에 사용한 원본 링크를 다시 비활성화하여 시뮬레이션 대상과 겹치지 않게 합니다.
7. `/Merged/left_wheel`의 Property에서 transform을 초기화하여 Translate·Rotate=0, Scale=1로 만듭니다. `/Visuals/left_wheel` Xform을 원점에 만들고 그 아래로 결과 Mesh를 옮깁니다. 이곳에는 바퀴의 배치가 빠진 로컬 형상을 보관하고, 다음 단계의 실제 바퀴 링크가 위치와 방향을 제공합니다.

**서로 다른 강체의 geometry를 한 mesh로 합치지 마세요.** 두 바퀴가 각각 회전해야 하는데 mesh 하나로 묶으면 어느 링크를 따라 움직일지 표현하기 어려워집니다. 이 단계는 한 링크 내부의 시각 자료를 정리합니다.

### 설정에서 볼 부분: 같은 형상을 참조하기

`/Jetbot_Sim/left_wheel/Visuals` Xform을 만들고 **Add > Reference**를 추가합니다. Property의 References에서 **Asset Path는 비우고 Prim Path는 `/Visuals/left_wheel`**로 정합니다.

```text
/Visuals/left_wheel                 ← 공유할 형상 원본
/Jetbot_Sim/left_wheel/Visuals      ← 원본을 참조해 보여줄 위치
```

파일 경로를 비우면 같은 Stage의 prim을 가리키는 **internal reference**가 됩니다. 자기 자신을 reference 대상으로 삼으면 순환이므로 두 위치를 구분하세요. 원본 보관용 `/Visuals`는 숨기고 실제 바퀴 위치의 참조 geometry가 보이는지 확인합니다.

오른쪽 바퀴와 몸체도 같은 순서로 링크별 병합과 internal reference를 끝내세요. 오른쪽은 `/Visuals/right_wheel` 원본과 `/Jetbot_Sim/right_wheel/Visuals` 참조를 먼저 만듭니다. 원본 `/Jetbot` 쪽 물리 링크는 작업 후 모두 비활성화하고 새 `/Jetbot_Sim`만 물리 동작에 참여하는지 확인합니다.

좌우 바퀴 기하가 같다면 다음으로 공유 범위를 넓힙니다.

1. `/Visuals/left_wheel`을 `/Visuals/wheel`로 이름을 바꿉니다.
2. 좌우 바퀴의 `Visuals` reference Prim Path를 모두 `/Visuals/wheel`로 맞춥니다.
3. 더 이상 참조하지 않는 오른쪽 형상 원본만 정리합니다.
4. `/Jetbot_Sim` 아래 참조용 `Visuals` prim의 **Instanceable**을 켭니다.

Reference가 있다는 사실과 instance로 공유한다는 사실은 다릅니다. Instanceable을 통해 호환되는 구성을 공유하게 되면 개별 instance 내부 mesh의 속성을 따로 편집하는 데 제약이 생깁니다. 한쪽만 다른 geometry가 필요하다면 공유 경계를 다시 정해야 합니다.

### 실행 결과 확인하기

`inspect_meshes.py`를 다시 실행하여 바퀴의 instance root와 proxy, prototype을 확인하세요. Mesh merge 전후에는 해당 바퀴 경로의 mesh 개수와 face 수를 비교하고, instancing 전후에는 공유 구조를 비교합니다. 작업마다 같은 숫자가 줄어들어야 하는 것은 아닙니다.

그다음 외부 모습과 물리를 확인합니다.

- 바퀴 위치·방향과 재질이 원래와 같은지 봅니다.
- Collider와 joint Body0/Body1이 남아 있는지 확인합니다.
- 같은 재생 조건에서 바퀴가 제각각 회전하고 차체와 연결을 유지하는지 관찰합니다.
- Stop 후 Ctrl+S로 저장하고, 저장한 결과를 다시 열어 같은 구조가 남는지 확인합니다.

창은 기본적으로 닫을 때까지 유지됩니다. 양수 `--steps`는 앱 갱신 후 종료하는 옵션이며 mesh 편집이나 Play를 자동 수행하지 않습니다. Headless에는 양수 한도가 필요합니다.

## 3. 통합·참조·인스턴스의 차이 정리

```text
여러 mesh → merge → 한 링크의 시각 표현 정리
같은 형상 → reference → 여러 위치에서 원본 재사용
같은 참조 구성 → Instanceable → 공유 prototype 구성
```

Default Prim은 다른 파일이 이 자산을 참조할 때의 기본 진입점을 정합니다. 반면 reference의 Prim Path는 특정 형상을 명시적으로 선택합니다. 원본 자료와 로봇 배치를 분리하면 재사용 위치를 설명하기 쉬워집니다.

## 4. 간단한 확인 실험

Merge와 reference를 끝낸 같은 장면에서 **바퀴의 Instanceable만 켰다 꺼보세요.** 형상·재질·관절은 그대로 둡니다.

검사 출력의 `instance_roots`, `prototypes`, `instance_proxy`가 어떻게 변하는지 보고 외형은 유지되는지 확인합니다. 이 실험이 직접 보여주는 것은 공유 구조의 변화입니다. 성능을 평가하려면 같은 카메라·해상도·조명·로봇 수에서 별도로 시간을 측정해야 합니다.

## 실행할 때 막히면

- **바퀴 mesh가 사라집니다**: internal reference의 Prim Path, 원본의 active/visibility, 참조 prim의 visibility를 확인하세요.
- **바퀴 위치가 두 번 이동합니다**: merge에서 반영된 transform과 reparent 후 상속 변환이 중복되었는지 확인하세요.
- **물리 연결이 끊어집니다**: 시각 자식을 정리하면서 물리 API나 joint를 지웠는지, Body0/Body1이 옛 경로를 가리키는지 확인하세요.
- **인스턴스 내부 속성이 수정되지 않습니다**: proxy 자식은 개별 편집이 제한됩니다. 공통 원본을 편집하거나 해당 instance의 공유를 해제하세요.
- **재실행이 출력 폴더 오류로 멈춥니다**: 새 폴더를 지정하세요. 저장한 장면에서 이어가려면 `--stage`로 그 파일을 지정하고 출력은 다른 경로를 사용합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 12: Asset Optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html)에 대응합니다. 공식 비교 자료는 `/Isaac/Samples/Rigging/Jetbot/Jetbot_Optimized/`의 `Jetbot_optimized_post_merge.usd`와 `Jetbot_optimized_final.usd`입니다.

로컬 코드는 원본 준비와 구조 조사를 수행합니다. `tutorial.json`의 상태는 `not_run`이며 실제 mesh merge, 물리 보존, FPS·메모리 개선은 미검증입니다. 원문에 제시된 성능 수치를 이 로컬 실행의 결과로 사용하지 않습니다.
