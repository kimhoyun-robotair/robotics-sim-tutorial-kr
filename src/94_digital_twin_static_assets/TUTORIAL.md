# 94. 창고의 시각 자산에 상자별 물리 동작 추가하기

## 이번에 배우는 것

**참조로 가져온 상자 더미에 강체와 충돌을 추가하고, 수정한 USD를 저장해 다시 사용할 수 있는지 확인합니다.**

창고에 상자가 보인다고 물리 엔진이 그 상자를 움직이거나 접촉을 계산하는 것은 아닙니다. 시각용 메시와 물리용 설정은 서로 다른 역할을 합니다. 이번에는 더미 전체가 한 덩어리로 움직이지 않도록 **상자마다 강체를 만들고 그 안의 형상에 충돌을 붙입니다.**

| 구성 | 역할 | 확인할 위치 |
|---|---|---|
| USD reference | 외부 자산을 현재 장면에 합성 | Layer와 reference 경로 |
| pile의 직접 자식 | 독립적으로 움직일 상자 | `RigidBodyAPI` |
| 상자 아래 Mesh/Cube | 접촉을 계산할 형상 | `CollisionAPI` |
| Mesh의 convex hull | 충돌용 볼록 근사 | `MeshCollisionAPI` |
| `apply_box_physics.py` | 현재 선택한 더미에 물리 속성 작성 | Script Editor 출력 |

보조 스크립트는 **선택한 root의 직접 자식 하나가 상자 하나**라고 가정합니다. 자산 구조를 읽고 올바른 root를 선택하는 단계가 실습의 일부입니다.

## 1. 자산을 가져오고 크기와 계층 확인하기

Isaac Sim 5.1 GUI, 지원 NVIDIA RTX GPU·드라이버와 NVIDIA Assets에 접근할 환경이 필요합니다. 저장소 루트에서 앱을 실행하세요.

```bash
~/isaacsim/isaac-sim.sh
```

1. 새 Stage에서 **Window > Browsers > NVIDIA Assets**를 엽니다.
2. Industrial > Buildings > Warehouse에서 **Warehouse01**을 찾아 Stage에 배치합니다.
3. 선반이나 rack을 하나 추가하고 Property의 실제 크기를 확인합니다.
4. meter 장면에 centimeter 기준 자산이 크게 들어왔다면 import parent의 Scale을 `(0.01,0.01,0.01)`로 정합니다.
5. 상자 실험은 별도의 새 Stage에서 시작합니다. `/World/Import`라는 Xform을 만들고 **WarehousePile_A04**를 그 아래로 가져옵니다. 이 새 Stage에서도 크기를 확인하세요. 원문의 centimeter 기준 pile이면 Import에 `(0.01,0.01,0.01)` scale을 주며, 앞 장면의 scale이 자동으로 이어지지는 않습니다.

Viewport에 드래그하면 화면에서 놓은 위치에 배치되고 Stage의 parent로 드래그하면 해당 parent를 기준으로 들어옵니다. **모든 자산에 0.01을 적용하지 마세요.** 이미 meter 기준인 자산은 추가 축소가 필요하지 않습니다.

### 설정에서 볼 부분

Stage에서 pile을 펼쳐 보세요. 다음처럼 상자별 자식이 보이는 root를 선택해야 합니다. 이름은 실제 자산마다 다를 수 있습니다.

```text
선택할 Pile root
├─ Box_A       ← 강체 하나
│  └─ Mesh     ← 충돌 형상
├─ Box_B       ← 강체 하나
│  └─ Mesh
└─ Box_C
   └─ Mesh
```

`Import` 아래 자식 하나가 pile 전체라면 Import를 선택하지 않습니다. 그렇게 하면 더미 전체를 강체 하나로 처리할 수 있기 때문입니다. 자식 중에 조명·장식·하위 그룹이 섞여 있다면 이 스크립트의 구조 가정을 만족하지 않습니다. 올바른 상자 그룹을 찾거나 GUI에서 상자들에 개별 설정을 적용하세요.

### 실행 결과 확인하기

물리를 추가하기 전에 두 가지를 확인합니다.

- 실제 상자 크기가 장면 단위에 맞는지 확인합니다.
- 직접 자식 하나를 선택했을 때 의도한 상자 하나만 대응하는지 확인합니다.

원문처럼 pile을 Stage root로 옮겨 재사용 자산으로 정리할 수도 있습니다. 이때 parent에만 있던 0.01 scale이 사라지면 크기가 바뀝니다. **reparent 전후의 world 크기**를 비교하고 필요한 변환을 pile에 보존하세요. 이 작업은 물리 설정 전 끝내는 편이 관찰하기 쉽습니다.

## 2. 물리 속성을 작성하고 접촉 시험하기

1. 타임라인을 Stop합니다.
2. Stage에서 위 조건을 만족하는 pile root **하나만** 선택합니다.
3. 저장할 새 장면의 root layer를 현재 edit layer로 사용합니다.
4. **Window > Script Editor**에서 `src/94_digital_twin_static_assets/apply_box_physics.py` 전체를 실행합니다.
5. **Create > Physics > Ground Plane**을 추가합니다.
6. Play하고 상자들이 중력과 접촉에 따라 반응하는지 봅니다.

### GUI에서 같은 물리 설정 비교하기

원문의 GUI 방식은 상자별 자식들을 선택하고 Property의 **Add > Physics > Rigid Body with Colliders Preset**을 적용합니다. 코드는 pile root 하나를 선택하지만, 이 GUI 방식은 강체가 될 **각 상자 자식**을 선택한다는 차이가 있습니다. 코드와 GUI를 비교할 때는 새 자산 사본에서 한 방식씩 적용하고 상자 root의 Rigid Body와 하위 형상의 Collision을 확인하세요.

### 코드에서 볼 부분

선택 수와 자식 구조를 먼저 검사합니다.

```python
paths = context.get_selection().get_selected_prim_paths()
if len(paths) != 1:
    raise ValueError("Select the warehouse pile root prim, with one direct child per box")
boxes = [prim for prim in root.GetChildren() if prim.IsA(UsdGeom.Xformable)]
```

`GetChildren()`은 root 바로 아래만 읽습니다. 이후에는 각 상자 안의 자손을 순회해 Mesh 또는 Cube에 충돌을 붙입니다.

```python
UsdPhysics.RigidBodyAPI.Apply(box).CreateRigidBodyEnabledAttr(True)
for prim in Usd.PrimRange(box):
    if prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Cube):
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
```

강체를 상자 root에 붙이는 이유는 상자의 여러 메시가 한 물체로 함께 움직이게 하기 위해서입니다. 반대로 상자마다 다른 강체가 있어야 더미가 개별 물체로 무너질 수 있습니다.

Mesh에는 다음 근사를 추가합니다.

```python
UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("convexHull")
```

convex hull은 형상을 감싸는 볼록한 충돌 형태입니다. 직육면체 상자에는 단순한 접촉 모델이 되지만, 오목한 선반이나 구멍을 그대로 표현하지는 못합니다. 이 보조 코드를 임의의 창고 자산 전체에 적용하지 않는 이유입니다.

### 실행 결과 확인하기

Console에는 상자별로 다음 형태가 출력됩니다.

```text
Rigid box: <상자 경로>
```

이 출력은 강체 속성을 작성했다는 뜻입니다. 해당 자식 아래에 지원하는 Mesh/Cube가 없다면 collider는 생기지 않을 수 있습니다. **Property에서 상자 root의 Rigid Body와 하위 형상의 Collision을 모두 확인**하세요.

Play한 상태에서 아래쪽 상자를 **Shift를 누른 채 클릭·드래그**하여 다른 상자들이 개별적으로 떨어지고 부딪히는지 관찰합니다. 더미 전체가 같이 움직이면 root 선택과 강체 작성 위치를 확인하세요. 바닥을 통과하면 지면과 상자 collider를 살펴봅니다.

확인을 마치면 Stop하고 저장소 루트의 별도 터미널에서 출력 폴더를 만듭니다.

```bash
mkdir -p src/94_digital_twin_static_assets/output
realpath src/94_digital_twin_static_assets/output
```

**File > Save As**에서 위 폴더의 `pile_physics.usd`로 저장하세요. 재사용할 대표 pile을 Default Prim으로 정할 수 있습니다. 시험용 지면을 최종 자산에도 포함할지는 저장 전에 결정합니다. 파일을 다시 열어 reference와 물리 속성이 유지되는지 확인하세요. Layer 탭에서 root layer를 우클릭하여 **Edit**하면 외부 reference와 그 위에 작성된 physics 속성을 텍스트로 대조할 수 있습니다.

## 3. 원본 자산과 수정 내용의 관계 정리

```text
외부 시각 자산 ─reference→ 현재 Stage
                              +
현재 edit layer의 상자별 강체·충돌 속성
                              ↓
                    합성된 물리 장면
                              ↓
                   새 USD 저장과 재사용
```

**reference는 원본 내용을 가져오고, 현재 layer는 그 위에 수정값을 작성합니다.** 저장된 파일을 다른 곳에서 열 때에도 참조 자산 경로에 접근할 수 있어야 합니다.

이 실습에서 말하는 물리 버전은 별도로 저장한 수정본입니다. 스크립트가 USD의 `VariantSet`을 만들거나 원본 자산에 선택 메뉴를 추가하지는 않습니다. 또한 Save As는 참조 텍스처와 자산을 모두 한 파일에 포장하는 작업이 아닙니다.

## 4. 간단한 확인 실험

Stop한 상태에서 **맨 위 상자 하나의 Translate Z만 바꾸어 world 기준으로 0.5 m 높여** 보세요. 이 실습처럼 Stage가 미터이고 조상 prim에 회전이 없다면, 조상들의 Z scale을 곱한 값이 1일 때 로컬 Z를 0.5, 0.01일 때는 50 늘립니다. 작은 로컬 이동이 parent의 scale 때문에 눈에 거의 보이지 않는 일을 피하려는 계산입니다.

상자 크기, 질량, 마찰과 다른 상자 위치는 유지합니다. 다시 Play하면 높인 상자가 내려와 아래 상자와 접촉합니다. 관찰할 것은 그 상자만 독립적으로 움직이는지, 아래 상자들이 접촉에 반응하는지입니다. pile 전체가 함께 높아졌다면 상자 root 대신 pile parent를 수정한 것입니다. 실험을 마치면 Stop하고 Z를 원래 값으로 돌려 저장용 상태를 정리합니다.

## 실행할 때 막히면

- **root 하나를 선택하라는 오류:** 여러 상자 대신 상자들을 담은 pile root 하나를 선택하세요.
- **직접 자식이 없다는 오류:** 선택한 prim 아래 구조를 펼쳐 올바른 그룹을 찾으세요.
- **`Rigid box`는 나오지만 상자가 지면을 통과함:** 하위 Mesh/Cube에 Collision이 작성되었는지와 Ground Plane을 확인하세요.
- **속성 작성이 막히거나 instance proxy 오류:** 인스턴스 내부는 직접 편집할 수 없는 경우가 있습니다. 실제 편집 가능한 상자 구조인지 확인하고 자산 복사본 또는 GUI의 instance 설정을 준비하세요.
- **저장한 자산 크기가 달라짐:** import parent의 scale이 reparent 과정에서 사라졌는지 확인하세요.
- **다시 열면 메시가 없음:** Save As 결과의 외부 reference 경로가 여전히 접근 가능한지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Static Warehouse Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/warehouse_logistics/tutorial_static_assets.html)에 대응합니다. 자산 배치와 단위 확인을 거쳐 상자에 물리를 추가하는 흐름을 다룹니다.

`apply_box_physics.py`는 선택 구조에 맞춰 속성을 작성하는 로컬 보조 구현입니다. 이번 개정에서는 선택·순회·물리 API와 저장 범위를 검토했습니다. NVIDIA 자산 로딩, 실제 접촉 시험과 USD 재열기는 실행하지 않았으며 `tutorial.json`의 상태는 `not_run`입니다.
