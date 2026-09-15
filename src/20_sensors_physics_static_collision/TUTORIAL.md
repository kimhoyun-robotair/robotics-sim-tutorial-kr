# 20. 보이는 물체만 골라 충돌체 붙이기

## 이번에 배우는 것

**Physics API Editor로 하위 물체에 충돌 속성을 적용하고, 선택 범위와 가시성 필터의 차이를 확인합니다.**

창고의 벽이나 바닥처럼 움직이지 않는 환경에도 로봇과 부딪힐 충돌체가 필요합니다. 많은 물체를 편집할 때는 하나씩 선택하는 대신 부모 아래를 한꺼번에 처리할 수 있습니다. 이때 숨겨 놓은 물체까지 적용할지는 별도 조건입니다.

이번 장면은 비교가 쉬운 상자 두 개만 사용합니다.

| Prim | 화면 표시 | 초기 CollisionAPI |
|---|---|---|
| `/World/StaticSet` | 두 상자를 묶는 부모 Xform | 없음 |
| `/World/StaticSet/Box0` | 보임 | 없음 |
| `/World/StaticSet/Box1` | 숨김 | 없음 |

`Box1`도 Stage 안에 존재합니다. **안 보이는 것과 장면에 없는 것은 다르다**는 점을 충돌 API의 적용 결과로 확인합니다.

## 1. 먼저 편집할 장면 열기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 다음 명령을 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/python.sh src/20_sensors_physics_static_collision/run.py
```

이 스크립트는 장면을 초기화한 뒤 타임라인을 **Stop**하고 창을 유지합니다. 상자가 떨어지기를 기다릴 필요는 없습니다. 이번 실행의 목적은 GUI로 편집할 초기 장면을 준비하는 것입니다.

출력은 이 폴더의 `output/날짜_시간/static_scene.usda`입니다. `--output`을 지정한다면 새 폴더를 사용하세요. `--steps N`을 추가하면 앱 업데이트 N회 후 종료하므로 수동 편집할 때는 생략합니다. Headless에서는 단계 수 생략 시 240회 업데이트 후 종료하지만, GUI 편집은 수행할 수 없습니다.

### 코드에서 볼 부분

두 상자는 `VisualCuboid`로 만들고 두 번째만 숨깁니다.

```python
cube = VisualCuboid(
    f'/World/StaticSet/Box{i}',
    name=f'box{i}',
    position=np.array([i*2, 0., 1.]),
    size=1,
)
if i == 1:
    UsdGeom.Imageable(cube.prim).MakeInvisible()
```

두 상자의 중심은 각각 `(0, 0, 1)`, `(2, 0, 1)` m이고 한 변은 1 m입니다. `VisualCuboid`는 여기서 충돌·강체 운동을 추가하지 않습니다. `MakeInvisible()`도 충돌 설정을 바꾸는 호출이 아니라 렌더링에서 숨기는 호출입니다.

장면 준비 뒤의 반복문은 `world.step()` 대신 `app.update()`를 사용합니다. 타임라인은 정지한 채 메뉴·화면·편집 도구가 응답하도록 앱을 갱신합니다.

### 실행 결과 확인하기

Stage에서 `/World/StaticSet`을 펼쳐 Box0과 Box1이 모두 있는지 확인하세요. 화면에는 Box0만 보여야 합니다. 각 Prim의 Property에서 아직 CollisionAPI가 없는지도 살펴봅니다.

두 상자는 공중에 있지만 강체 운동을 켜지 않았으므로 떨어지지 않습니다. 움직임 대신 **API가 어디에 붙는지**를 확인하는 실습입니다.

## 2. Physics API Editor로 보이는 자식에 적용하기

1. **Window > Extensions**에서 `isaacsim.util.physics`를 활성화하고 **Tools > Physics > Physics API Editor**를 엽니다.
2. Stage에서 부모 `/World/StaticSet`만 선택합니다.
3. **Apply to children**과 **Visible only**를 켭니다.
4. Collision Type을 **Convex Hull**로 두고 **Apply Static**을 누릅니다.
5. 도구의 처리가 끝날 때까지 기다린 뒤 Box0과 Box1을 각각 선택해 Property의 Collision 관련 속성을 확인합니다. API 적용은 앱 업데이트에 걸쳐 비동기로 진행됩니다.

### 설정에서 볼 부분

| 설정 | 이번 선택에서의 역할 |
|---|---|
| Apply to children | 부모 아래 Box0·Box1까지 탐색 |
| Visible only | 탐색한 대상 중 숨긴 Box1 제외 |
| Collision Type | 메시의 충돌 형상을 만들 때 사용할 근사 방식 |
| Apply Static | 선택 범위의 정적 충돌 속성 적용 |

부모 Xform은 큐브 형상 자체가 아닙니다. 자식 적용을 끄고 부모만 처리하면 실제 Box에 충돌체가 붙지 않을 수 있습니다. 가시성은 이렇게 찾아낸 대상에 추가로 적용하는 조건입니다.

현재 상자는 단순 Cube 형상이므로 복잡한 메시 근사 간 차이를 관찰하기 위한 장면은 아닙니다. 여기서는 Collision Type보다 **어떤 Prim이 적용 대상이 되는지**에 집중합니다.

### 실행 결과 확인하기

Box0에는 CollisionAPI가 생기고, 숨긴 Box1에는 아직 없어야 합니다. 상자가 움직이지 않는 것은 정상입니다. Static 적용은 강체를 만들어 중력 낙하를 켜는 동작이 아닙니다.

적용 후 뷰포트의 눈 아이콘에서 **Show By Type > Physics Mesh > All**을 켜 충돌 형상을 확인합니다. 설치 UI에서 Colliders로 표시된다면 그 항목을 사용하세요. 대상을 탐색하며 API를 붙이거나 제거하는 동안에는 시각화를 끄고, 작업 후 다시 켜는 순서가 좋습니다.

결과를 보존하려면 **File > Save As**로 새 USD를 저장합니다. 코드가 만든 `static_scene.usda`는 GUI 편집 전 파일이므로 자동으로 바뀌지 않습니다.

## 3. 선택 범위와 필터 정리

```text
선택한 /World/StaticSet
    → 자식 탐색 켜짐 → Box0, Box1
    → 보이는 대상만 → Box0
    → Apply Static  → Box0에 CollisionAPI
```

이 흐름을 이해하면 “Apply를 눌렀는데 원하는 물체에 충돌이 없다”는 상황을 두 단계로 나눠 볼 수 있습니다. 먼저 선택·자식 탐색 범위를 확인하고, 다음으로 숨김 상태와 Visible only 조건을 확인합니다.

**Remove Collision API**는 충돌 관련 API를 지우는 작업이고, **Remove All Physics APIs**는 더 넓은 물리 설정을 제거합니다. 이번처럼 작은 연습 장면에서 결과를 비교하되, 기존 로봇 장면의 설정을 정리할 때 두 작업을 같은 것으로 취급하지 마세요.

## 4. 간단한 확인 실험

Stage에서 `/World/StaticSet`을 다시 선택하세요. Box1의 숨김 상태와 Apply to children을 유지하고 **Visible only만 Off**로 바꿔 다시 Apply Static을 누릅니다.

이번에는 Box1에도 CollisionAPI가 생기는지 확인하세요. Box1을 보이게 바꿀 필요 없이 Stage에서 선택해 속성을 읽을 수 있습니다. 이 관찰은 “숨긴 물체도 충돌할 수 있다”는 점을 확인합니다.

비교를 마친 뒤 `/World/StaticSet`을 다시 선택해 **Remove Collision API**를 실행합니다. 처리 완료 후 두 상자의 해당 API가 제거되는지 확인하세요. 삭제 결과를 남기려면 다시 새 이름으로 저장합니다.

## 실행할 때 막히면

- **Physics API Editor 메뉴가 없음**: **Window > Extensions**에서 `isaacsim.util.physics`를 켜고 Tools의 Physics 하위 메뉴를 확인하세요. 공식 페이지에는 확장 검색 이름이 `isaacsim.utils.physics`로 표기되어 있어 설치 목록의 실제 ID와 구분해야 합니다.
- **부모를 선택했는데 상자에 적용되지 않음**: Apply to children이 켜졌는지 확인하세요.
- **Box1만 적용되지 않음**: 숨김 상태와 Visible only를 확인하세요. On이면 의도적으로 제외합니다.
- **저장 파일에 편집 내용이 없음**: 기본 `static_scene.usda` 대신 GUI에서 Save As한 파일을 열었는지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Physics Static Collision Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/physics_static_collision.html)에 대응합니다. 선택·자식 탐색·가시성 조건을 상자 두 개로 비교합니다. 공식 도구는 정적 물체용이며 이 실습은 동적 물체의 접촉 반응을 측정하지 않습니다.

현재 `tutorial.json`은 `not_run`입니다. 이번 개정에서는 공식 메뉴와 설정 의미, 로컬 장면 준비 코드를 대조했습니다. 파일 생성과 GUI Apply·Remove 동작을 새로 실행해 검증하지 않았습니다.
