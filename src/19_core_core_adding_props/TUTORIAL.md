# 19. 보이는 Rubik 큐브와 부딪히는 모양 분리하기

## 이번에 배우는 것

**같은 Rubik 에셋에 물리 속성을 단계별로 붙이며, 낙하와 접촉을 결정하는 설정을 비교합니다.**

복잡한 소품을 장면에 가져오면 외형은 잘 보여도 원하는 방식으로 움직이지 않을 수 있습니다. 이 실습에서는 같은 에셋을 네 모드로 실행합니다. 시각 형상만 두는 상태부터 강체·메시 충돌체를 차례로 비교하고, 마지막에는 보이지 않는 구를 충돌체로 사용합니다.

| `--physics` | 운동 설정 | 접촉 형상 | 수평 바닥에서 볼 차이 |
|---|---|---|---|
| `visual` | 없음 | 없음 | 처음 위치에 남음 |
| `rigid` | 강체 | 없음 | 바닥을 통과해 낙하 |
| `mesh` | 강체 | Rubik 메시의 볼록 근사 | 메시 충돌체로 지지됨 |
| `sphere` | 강체 | 반지름 0.07 m의 숨긴 구 | 구의 외곽으로 접촉 |

기본값은 `sphere`, 바닥 경사 10°, 반발계수 0.8입니다. 네 물체를 동시에 만드는 코드가 아니라 **한 번 실행할 때 한 모드**를 선택합니다.

## 1. 먼저 기본 구 충돌체로 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU 외에 공식 Rubik 에셋이 필요합니다. 기본 경로는 Isaac 에셋 루트 아래 `/Isaac/Props/Rubiks_Cube/rubiks_cube.usd`입니다.

저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics sphere --steps 360
```

에셋을 로컬에 설치했다면 위 명령에 `--asset /절대경로/Isaac/Props/Rubiks_Cube/rubiks_cube.usd`를 추가합니다. 이후의 네 모드와 반발 비교 명령에도 같은 `--asset`을 사용하세요. USD가 참조하는 주변 파일도 접근 가능해야 합니다.

큐브는 중심 위치 `(0, 0, 1)` m에서 시작합니다. 360단계는 1/60초 간격으로 약 6초이며, 결과 저장 후 앱이 종료됩니다. `--steps 360`을 빼면 첫 360단계를 저장한 뒤에도 창을 닫을 때까지 물리가 계속됩니다. `--headless`는 창을 숨기며, 단계 수 생략 시 360단계 후 종료합니다.

출력은 이 폴더의 `output/고유번호/`에 저장됩니다. `--output`으로 지정한 폴더가 이미 있으면 덮어쓰지 않습니다.

### 코드에서 볼 부분

기본 모드의 접촉용 구는 다음과 같이 만듭니다.

```python
sphere = UsdGeom.Sphere.Define(world.stage, "/World/Rubik/PhysicsSphere")
sphere.CreateRadiusAttr(0.07)
sphere.MakeInvisible()
UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
```

`MakeInvisible()`은 렌더링에서 숨길 뿐 충돌을 끄지 않습니다. 화면에서는 Rubik이 보이고, 물리 계산에서는 자식 `PhysicsSphere`가 바닥에 닿습니다. 복잡한 외형을 단순한 충돌 모양으로 근사하는 방식입니다.

강체에는 기본 질량 0.1 kg을 설정하고, 충돌체에는 마찰·반발 재질을 바인딩합니다. 정지 마찰계수는 0.5, 동적 마찰계수는 0.4입니다. 물리 재질은 표면의 색이나 텍스처를 바꾸는 시각 재질과 구분합니다.

### 실행 결과 확인하기

`result.json`의 조건과 위치 샘플을 먼저 읽어보세요.

| 항목 | 기본 실행에서 확인할 내용 |
|---|---|
| `physics` | `sphere` |
| `colliders` | `/World/Rubik/PhysicsSphere` 하나 |
| `slope_deg` | 10 |
| `restitution` | 0.8 |
| `samples[].position_m` | 실제 Rubik 루트의 월드 위치, m |

물체가 떨어진 뒤 경사면을 따라 이동하는지 화면으로 관찰합니다. 보이는 Rubik의 모서리와 바닥이 정확히 맞지 않더라도 접촉용 구로 설명되는지 확인하세요.

위치는 15단계마다 기록합니다. `step`은 0부터 시작하는 반복문 인덱스이며, 코드가 `world.step()` 뒤에 읽으므로 **`step: 0`은 첫 물리 단계 이후**의 위치입니다. 기본 360단계에서는 인덱스 0, 15, …, 345의 24개 샘플이 생깁니다. 마지막 샘플이 마지막 물리 단계 자체는 아닙니다.

## 2. 같은 에셋의 물리 설정을 차례로 비교하기

비교가 쉬운 수평 바닥으로 고정하고 다음 모드를 각각 실행합니다.

```bash
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics visual --slope 0 --steps 120
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics rigid --slope 0 --steps 120
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics mesh --slope 0 --steps 120
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics sphere --slope 0 --steps 120
```

### 코드에서 볼 부분

코드는 참조한 Rubik의 기존 강체·충돌 스키마를 현재 장면에서 제거하고 선택 모드의 설정을 추가합니다. 원본 에셋 파일을 직접 고치지 않으면서 시작 조건을 맞추는 과정입니다. 참조에서 실제 Mesh를 찾지 못하면 일반 큐브로 대신 진행하지 않고 오류를 냅니다.

`mesh` 모드에서는 각 Rubik Mesh에 다음을 적용합니다.

```python
UsdPhysics.CollisionAPI.Apply(mesh)
UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr("convexHull")
```

메시의 시각 삼각형을 그대로 동적 충돌에 사용한다고 가정하지 않고, 볼록 근사를 지정합니다. `sphere` 모드와는 접촉 형상이 달라지므로 바닥에 놓이는 자세나 구르는 모습도 달라질 수 있습니다.

`visual`은 `SingleXFormPrim`으로 위치만 관리합니다. 나머지 모드는 Rubik 루트에 RigidBodyAPI와 MassAPI를 붙이고 `SingleRigidPrim`으로 운동 상태를 읽습니다.

### 실행 결과 확인하기

수평 바닥에서 네 결과의 Z 위치를 비교하세요.

- `visual`: 시작 높이 1 m를 유지하는지 봅니다.
- `rigid`: 충돌체가 없으므로 0 아래로 떨어지는지 봅니다.
- `mesh`: `colliders`에 메시 경로가 들어가고 바닥에서 지지되는지 확인합니다.
- `sphere`: 구 하나가 접촉체로 기록되는지 확인합니다. 반발이 남아 있다면 짧은 구간에서 완전히 정착하지 않을 수 있습니다.

`configured_scene.usda`는 초기화 후 물리 단계 반복문 **전**에 저장한 장면입니다. **File > Open**으로 열어 스키마를 비교하고, 뷰포트 눈 아이콘의 **Show By Type > Physics > Colliders > All**로 충돌 외곽을 확인해 보세요. 저장된 장면에도 Rubik의 외부 참조가 있으므로 에셋 접근은 계속 필요합니다.

### GUI에서 물리 속성 직접 붙이기

코드가 한 일을 직접 편집하려면 독립 실행을 종료하고 `~/isaacsim/isaac-sim.sh`로 새 GUI를 여세요. 2절에서 만든 **visual 모드**의 `configured_scene.usda`를 열면 기존 물리 속성을 제거한 동일 에셋에서 시작할 수 있습니다.

1. `/World/Rubik`에 **Add > Physics > Rigid Body**, **Add > Physics > Mass**를 추가하고 질량을 0.1 kg으로 설정합니다. Play하면 강체만 있는 모드처럼 바닥을 통과하는지 확인하고 Stop합니다.
2. Rubik의 실제 Mesh 자식들에 Collider Preset을 붙여 **Convex Hull**로 설정합니다. 충돌 시각화에서 적용한 메시를 확인하고 다시 Play해 바닥에서 지지되는지 봅니다.
3. Stop한 뒤 메시의 Collider를 제거하고 `/World/Rubik` 아래 **Sphere**를 만듭니다. local Translate=`(0,0,0)`, Radius=`0.07`로 두고 Collider를 추가합니다. 눈 아이콘으로 Sphere를 숨겨도 충돌 외곽은 남는지 확인하세요.
4. **Create > Physics > Physics Material**에서 만든 재질의 restitution을 1로 설정하고 Sphere의 Physics Material에 할당합니다. Rubik 루트의 높이를 1 m로 두고 낙하를 비교합니다.

처음부터 에셋을 넣는 원문 흐름도 사용할 수 있습니다. 새 Stage에서 Content Browser의 `Isaac Sim/Props/Rubiks_Cube/rubiks_cube.usd`를 추가하고 **Create > Isaac > Environment > Flat Grid**로 바닥을 만듭니다. 에셋에 이미 있는 강체·충돌 설정을 확인해 각 비교 단계가 중복 적용되지 않게 하세요. Flat Grid는 Transform Offset Mode에서 X 회전을 10°로 설정하면 경사 비교에 사용할 수 있습니다. 편집 결과는 원본 참조 파일에 덮어쓰지 않고 새 Stage로 저장합니다.

## 3. 시각 형상과 물리 형상의 관계 정리

```text
Rubik 메시 → 화면에 보이는 외형
Rubik 루트의 RigidBodyAPI·MassAPI → 전체 소품의 운동
자식 Mesh 또는 PhysicsSphere의 CollisionAPI → 접촉할 외곽
충돌체에 바인딩한 Physics Material → 마찰·반발
```

강체와 충돌체는 함께 쓰일 때가 많지만 각각의 역할이 있습니다. 강체만 있으면 떨어져도 바닥에 막히지 않고, 숨긴 충돌체는 보이지 않아도 접촉에 참여합니다. **운동이 이상할 때는 보이는 모형뿐 아니라 충돌 시각화도 확인**하세요.

## 4. 간단한 확인 실험

수평 바닥의 구 모드에서 **반발계수만** 바꿉니다.

```bash
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics sphere --slope 0 --restitution 0 --steps 360
~/isaacsim/python.sh src/19_core_core_adding_props/run.py --physics sphere --slope 0 --restitution 1 --steps 360
```

접촉 이후 다시 올라가는 높이와 반복 튀김을 비교하세요. Z 위치 샘플은 0.25초 간격이므로 짧은 순간의 최고점을 놓칠 수 있습니다. 화면과 샘플 추세를 함께 읽고, 계수 1을 영구적으로 같은 높이로 튀는 보장으로 해석하지 않습니다. 실제 접촉에는 바닥 재질과 수치 계산도 관여합니다.

## 실행할 때 막히면

- **`No Rubik meshes resolved`**: 지정한 에셋과 그 참조 리소스를 찾을 수 있는지 확인하세요. USD 파일 이름만 맞아도 내부 참조가 끊어지면 실행할 수 없습니다.
- **`PhysicsSphere`가 안 보임**: 코드가 의도적으로 숨긴 충돌체입니다. 일반 표시 대신 충돌 시각화를 켜보세요.
- **`rigid` 모드가 바닥을 통과함**: 충돌체 없이 운동만 켠 비교 조건입니다. `mesh`나 `sphere` 결과와 구분하세요.
- **GUI에서 다시 재생한 기록이 JSON에 없음**: 저장 구간 이후에는 샘플을 추가하지 않습니다. 같은 초기 조건으로 비교하려면 프로그램을 다시 실행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Adding Props](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html)에 대응합니다. 원문의 강체·충돌체·질량·물리 재질 추가 과정을 독립 Python의 네 모드로 구성했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 과거 코드의 기본 `sphere` 모드를 Headless 60단계로 실행한 참고 기록입니다. 현재 코드의 재실행, 네 모드 전체와 장시간 반발 비교는 확인하지 않았습니다. 본문의 운동과 샘플 값은 실행 후 대조할 기준입니다.
