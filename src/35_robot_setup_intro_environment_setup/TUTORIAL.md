# 35. 로봇을 놓기 전에 단위·중력·바닥·조명 준비하기

## 이번에 배우는 것

**같은 Stage에서 길이 단위, 중력, 바닥 충돌과 조명을 확인하고, 각 설정이 화면과 물리에 어떻게 영향을 주는지 구분합니다.**

로봇을 가져오기 전에 장면의 기준부터 정해야 합니다. 길이 숫자 1이 1 m인지 1 cm인지에 따라 모델 크기의 해석이 달라지고, 위쪽 축이 다르면 모델 방향도 달라집니다. 한편 조명을 추가했다고 중력이 생기는 것은 아니며, 바닥이 보인다고 모든 물체가 자동으로 충돌하는 것도 아닙니다.

| 준비할 것 | 이 실습의 Prim 또는 속성 | 기본 설정 |
|---|---|---|
| 길이·방향 기준 | Stage metadata | 1단위=1 m, Z-up |
| 물리 환경 | `/World/PhysicsScene` | 아래쪽 중력 9.8 m/s², CPU 물리 |
| 접촉 바닥 | `/World/Ground` | 지면 충돌과 표시용 바닥 |
| 기본 조명 | `/World/DefaultLight` | intensity 300 |
| 추가 조명 | `/World/SpotLight` | 높이 7 m의 초록색 원뿔 조명 |

기본 장면에는 떨어뜨릴 큐브나 로봇이 없습니다. 먼저 환경을 읽고, 2절에서 큐브를 추가해 중력과 접촉을 직접 확인합니다.

## 1. 준비된 Stage 열기

Isaac Sim 5.1과 지원 RTX GPU, GUI 화면이 필요합니다. 외부 에셋 없이 코드에서 환경을 만듭니다. 저장소 루트에서 실행하세요. `~/isaacsim`은 실제 설치 경로로 바꾸세요.

```bash
~/isaacsim/python.sh src/35_robot_setup_intro_environment_setup/run.py --output src/35_robot_setup_intro_environment_setup/output/first
```

`first`가 이미 있으면 새 폴더 이름을 사용하세요. 앱은 창을 닫을 때까지 열려 있습니다. 편집을 마치면 로컬 `stage.usda`에 저장하고 종료합니다. 양수 `--steps`는 장면 준비 후 앱 업데이트 횟수 제한이며 물리 실행 횟수가 아닙니다. Headless에는 양수 `--steps`가 필요하지만 아래 GUI 조작은 할 수 없습니다.

### 코드에서 볼 부분

`build_fixture()`는 장면의 기준과 중력을 명시적으로 작성합니다.

```python
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
scene.CreateGravityMagnitudeAttr(9.8)
```

Z-up에서 `(0, 0, -1)`은 아래 방향이고, magnitude 9.8은 그 방향의 중력 가속도입니다. 길이 단위를 먼저 확인해야 이 숫자를 m/s²로 해석할 수 있습니다. 이미 있는 모델의 크기를 맞추려면 모델의 transform과 자산 단위도 조사해야 하며, metadata만 바꾼다고 모델을 자동으로 원하는 크기로 재작성하는 것은 아닙니다.

`PhysxSceneAPI`는 GPU dynamics를 끄고 broadphase를 `MBP`로 설정합니다. 이 장면의 물리 계산을 CPU로 설정하는 항목입니다. 화면을 그리는 RTX GPU의 필요 여부와는 별도입니다.

### 실행 결과 확인하기

`output/first/initial_inventory.json`에서 다음을 확인하세요.

- `meters_per_unit`은 `1.0`, `up_axis`는 `"Z"`입니다.
- `rigid_bodies`, `joints`, `articulation_roots`는 기본 장면에서 비어 있습니다.
- `source`는 코드로 만든 로컬 환경임을 나타냅니다.

강체 목록이 비어 있는 것은 바닥이 없다는 뜻이 아닙니다. 움직이는 강체를 아직 만들지 않은 상태입니다. Stage에서 `/World/Ground`와 PhysicsScene을 직접 찾으세요. 초기 보고서는 이후 GUI 편집으로 만든 큐브를 자동으로 추가하지 않습니다.

## 2. Property 값과 실제 화면 연결하기

Stage에서 `/World/PhysicsScene`을 선택해 중력과 CPU 물리 설정을 확인하세요. 원문처럼 빈 Stage부터 만들고 싶다면 별도 새 장면에서 **Create > Physics > Physics Scene**, **Create > Physics > Ground Plane**으로 같은 구성 요소를 추가할 수 있습니다. 현재 준비된 장면에는 이미 있으므로 중복 생성할 필요가 없습니다.

직접 환경을 만드는 경우에는 **Edit > Preferences > Stage**에서 새 장면의 Up Axis를 Z, 단위를 meters로 정한 뒤 **File > New**로 시작하세요. Physics Scene과 Ground Plane을 만들고 위 중력값을 입력합니다. `/World` 아래에 **Create > Lights > Distant Light**와 **Sphere Light**를 추가하고 이름을 각각 `DefaultLight`, `SpotLight`로 정합니다. Distant Light의 intensity는 300으로, Sphere Light는 아래 표의 값으로 조절하세요. Shaping에서 cone angle과 softness를 정하면 준비기의 원뿔 조명과 같은 설정을 비교할 수 있습니다. Preferences의 새 장면 기본값을 바꾸는 것과 이미 불러온 자산의 크기를 변환하는 것은 구분하세요.

### 설정에서 볼 부분

조명은 `/World/SpotLight`를 선택해 다음 값과 화면을 연결합니다.

| 속성 | 값 | 의미 |
|---|---:|---|
| Translate | `(0, 0, 7)` | 바닥 위 광원 위치 |
| Color | `(0.5, 1, 0.5)` | 녹색 성분이 더 큰 빛 |
| Intensity | `1000000` | 광원 밝기 설정 |
| Radius | `0.05` | 구형 광원의 크기 |
| Shaping cone angle | `45`도 | 빛을 원뿔 형태로 제한하는 각도 |
| Shaping cone softness | `0.05` | 원뿔 경계의 부드러움 |

코드는 `SphereLight`에 `ShapingAPI`를 적용해 이 조명을 만듭니다. SpotLight라는 Prim 이름만으로 광원 종류가 결정되는 것은 아닙니다. 이름과 실제 USD 타입·속성을 함께 보세요.

SpotLight의 visibility를 껐다 켜며 바닥의 초록빛을 비교해 보세요. 바닥 재질 색을 바꾸지 않았어도 조명이 달라지면 표면 색이 달라 보입니다. DefaultLight가 남아 있으므로 SpotLight를 꺼도 장면 전체가 검게 될 필요는 없습니다.

### 실행 결과 확인하기

이번에는 중력과 접촉을 확인할 물체를 직접 추가합니다.

1. **Create > Shape > Cube**로 큐브를 만듭니다. 위치를 `(0, 0, 2)`로 옮기고 Scale을 `(0.2, 0.2, 0.2)`로 줄입니다. Scale은 배율이므로 실제 한 변 길이는 Cube의 Size 속성도 함께 확인하세요.
2. 큐브를 선택하고 **Property > + Add > Physics > Rigid Body with Colliders Preset**을 적용합니다.
3. **Play**를 누릅니다. 큐브가 아래로 떨어져 바닥에서 멈추는지 관찰하세요.
4. **Stop**으로 초기 편집 상태로 돌아온 뒤 **Ctrl+S**로 로컬 장면을 저장합니다.

Rigid Body는 큐브를 물리 운동 대상으로 만들고 Collider는 접촉 형상을 제공합니다. 둘을 함께 적용해야 떨어지면서 바닥과 부딪히는 동작을 확인할 수 있습니다. 바닥의 보이는 사각형과 충돌 평면의 범위도 구분하세요. 이 Ground Plane은 표시 영역 밖으로도 충돌 평면이 이어집니다.

저장한 장면은 다음처럼 새 편집 레이어로 다시 열 수 있습니다.

```bash
~/isaacsim/python.sh src/35_robot_setup_intro_environment_setup/run.py --stage src/35_robot_setup_intro_environment_setup/output/first/stage.usda --output src/35_robot_setup_intro_environment_setup/output/reopen
```

이번에는 처음부터 환경을 다시 만드는 대신 저장된 Stage를 참조합니다. 새 `initial_inventory.json`에 저장했던 큐브의 강체 경로가 나타나는지도 확인하세요.

## 3. 화면과 물리 설정의 관계 정리

```text
Stage 단위·축 → 좌표 숫자의 의미
Physics Scene → 중력과 물리 계산 설정
Rigid Body + Collider + Ground → 낙하와 접촉
Light + 표면 재질 → 화면에 보이는 밝기와 색
```

물체가 보이는지, 움직이는지, 바닥에서 멈추는지는 서로 다른 질문입니다. 이번에는 큐브의 낙하로 물리를 확인하고, 조명 visibility로 화면 변화를 확인했습니다. 원인을 나누어 관찰하면 이후 로봇이 이상하게 보이거나 움직일 때도 확인할 설정을 좁힐 수 있습니다.

## 4. 간단한 확인 실험

`/World/SpotLight`의 cone angle만 45도에서 20도로 줄여 보세요. 위치·색·intensity·softness는 그대로 둡니다.

바닥에 빛이 비치는 영역이 더 좁아지는지 관찰하세요. 큐브를 떨어뜨리는 운동이나 바닥 충돌은 이 조명 각도 변경으로 달라지지 않아야 합니다. 처음 값과 비교한 뒤 유지하고 싶은 상태를 저장하세요. 화면 밝기 변화만으로 물리 설정이 바뀌었다고 판단하지 않는 연습입니다.

## 실행할 때 막히면

- **실행했는데 아무것도 떨어지지 않음**: 기본 파일은 환경만 만듭니다. 큐브를 추가하고 강체·collider를 적용한 뒤 Play하세요.
- **큐브가 바닥을 통과함**: 큐브의 Collider와 Ground가 존재·활성 상태인지 확인하세요. 시각적인 바닥만으로 접촉이 생기지는 않습니다.
- **SpotLight를 껐는데도 밝음**: DefaultLight의 intensity 300이 남아 있습니다. 추가 조명 효과를 비교하는 정상 조건입니다.
- **장면이 100배 크거나 작아 보임**: Stage 단위와 입력 모델의 단위·scale을 확인하세요. 길이 metadata와 모델 치수를 구분합니다.
- **저장 후 초기 보고서에 큐브가 없음**: 보고서는 최초 로드 시점에 한 번 작성됩니다. 저장한 Stage를 새 output으로 다시 열어 조사하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 1: Stage Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_environment_setup.html)에 대응합니다. 원문의 Stage·물리·바닥·조명 구성을 코드로 준비하고, GUI에서 값과 결과를 비교하도록 구성했습니다. 큐브 낙하는 환경의 역할을 확인하기 위해 추가한 수동 실험입니다.

`tutorial.json`의 상태는 `not_run`입니다. 환경 값은 생성 코드와 공식 5.1 설정에 따른 확인 기준입니다. 장면 렌더링, 조명 비교, 큐브 낙하와 GUI 저장의 실제 실행은 아직 검증하지 않았습니다.
