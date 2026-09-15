# 36. 도형에 물리 속성을 붙이면 무엇이 달라질까요?

## 이번에 배우는 것

**몸체와 바퀴를 만들고, 모양·운동·접촉·재질이 각각 어디에 설정되는지 비교합니다.**

화면에서 바퀴가 몸체 옆에 있다고 해서 두 부품이 연결된 것은 아닙니다. 이번 장면은 큐브 하나와 원기둥 두 개를 로봇처럼 배치하지만, 각 부품은 독립적으로 떨어집니다. 이 모습을 통해 로봇 제작에서 외형을 만드는 일과 물리적 연결을 만드는 일을 구분합니다.

| 장면의 요소 | 실제 위치 또는 설정 | 맡은 역할 |
|---|---|---|
| 몸체 외형 | `/World/body/body`의 Cube | 길이 1 × 2 × 0.5 m의 상자 |
| 바퀴 외형 | `/World/wheel_left/wheel_left`, `/World/wheel_right/wheel_right` | 반지름 0.5 m, 높이 1 m인 원기둥 |
| Rigid Body | 위 세 geometry prim | 중력과 힘에 따라 움직이는 강체 |
| Collider | 위 세 geometry prim | 다른 물체와 접촉하는 표면 |
| WheelPhysics | `/World/Looks/WheelPhysics` | 바퀴 접촉의 마찰과 반발 |

USD에서 **prim**은 Stage 트리에 보이는 장면 요소입니다. 부모 Xform에는 부품의 배치를, 자식 geometry에는 실제 도형과 물리 속성을 둡니다.

## 1. 세 부품이 있는 장면 열기

Isaac Sim 5.1.0과 지원되는 RTX GPU, GUI 환경에서 진행합니다. 외부 로봇 에셋은 필요하지 않습니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/36_robot_setup_intro_assemble_robot/run.py \
  --output src/36_robot_setup_intro_assemble_robot/output/first
```

창이 열리면 파란 몸체, 어두운 바퀴 두 개, 바닥이 보입니다. **Play를 직접 눌러** 세 물체가 각각 떨어지는지 확인하고 Stop하세요. 이 단계에는 관절이 없으므로 바퀴가 떨어져 나가는 모습이 예상한 결과입니다.

실습을 끝낼 때는 **Ctrl+S**로 저장한 뒤 창을 닫으세요. `--steps`를 생략하거나 0으로 지정하면 GUI를 계속 유지합니다. 자동 종료를 원하면 `--steps 120`을 추가할 수 있지만, 이 값은 화면과 앱의 갱신 횟수입니다. 실행기가 물리를 120단계 자동 재생하는 뜻은 아닙니다. `--headless`에는 양수 `--steps`가 필요합니다.

### 코드에서 볼 부분

몸체는 두 계층으로 만듭니다.

```python
body = UsdGeom.Xform.Define(stage, "/World/body")
body.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
cube = UsdGeom.Cube.Define(stage, "/World/body/body")
cube.CreateSizeAttr(1.0)
cube.AddScaleOp().Set(Gf.Vec3f(1, 2, 0.5))
```

부모의 Translate는 몸체 중심을 높이 1 m에 놓습니다. 자식의 Scale은 한 변 1 m인 큐브를 늘려 몸체 크기를 정합니다. 부모 위치와 자식 크기를 나누면, 모양을 바꾸더라도 부품을 배치한 기준점을 유지하기 쉽습니다.

같은 계층을 직접 만들어 보고 싶다면 별도 새 장면에서 **Create > Xform**으로 `body`를 만든 뒤 그 아래 **Create > Shape > Cube**를 추가하세요. Cube의 Size=1, Scale=(1, 2, 0.5), 부모 Translate=(0, 0, 1)을 위 코드와 맞춥니다. 바퀴도 Xform 아래 Cylinder를 만들고 Radius=0.5, Height=1로 정합니다. 부모를 `(1.5, 0, 1)`에 놓은 뒤 복제하여 다른 바퀴를 `(-1.5, 0, 1)`에 배치하면 코드의 세 부품과 비교할 수 있습니다.

바퀴의 부모 Xform은 X축으로 90° 회전합니다. 원기둥 자체의 축을 바퀴가 놓일 방향으로 돌리는 과정입니다. Stage에서 부모와 자식을 번갈아 선택해 회전과 도형 크기가 서로 다른 곳에 있는지 확인해 보세요.

### 실행 결과 확인하기

지정한 출력 폴더에 다음 파일이 생깁니다.

| 파일 | 확인할 내용 |
|---|---|
| `stage.usda` | 편집하고 저장할 로컬 USD 장면 |
| `initial_inventory.json` | 최초 장면의 단위, 강체, 관절, articulation 목록 |

기본 장면의 `meters_per_unit`은 `1.0`, `up_axis`는 `Z`, `rigid_bodies`는 세 geometry 경로입니다. `joints`와 `articulation_roots`는 빈 목록이어야 합니다. 이 JSON은 **GUI 편집 전의 기록**이며 이후 수정 사항을 자동으로 다시 조사하지 않습니다.

## 2. 움직임과 접촉, 색을 따로 살펴보기

먼저 `/World/body/body`를 선택하고 Property의 Rigid Body와 Collider를 찾으세요. 직접 새 도형을 만들 때는 **+ Add > Physics > Rigid Body with Colliders Preset**으로 둘을 함께 추가할 수 있습니다. 이미 강체인 부모 아래에 강체를 중복으로 추가하지 않도록 적용 위치를 확인하세요.

### 설정에서 볼 부분

코드는 각 도형에 두 속성을 적용합니다.

```python
UsdPhysics.RigidBodyAPI.Apply(prim)
UsdPhysics.CollisionAPI.Apply(prim)
```

Rigid Body는 물체의 운동을 계산하게 하고, Collider는 접촉을 계산하게 합니다. 따라서 강체만 남기면 중력으로 떨어져도 바닥을 통과할 수 있습니다. Viewport의 눈 모양 메뉴에서 **Show By Type > Physics > Colliders > All**을 켜 실제 접촉 윤곽을 확인하세요.

바퀴의 물리 재질은 다음 값으로 준비됩니다.

```python
physics_material.CreateStaticFrictionAttr(0.8)
physics_material.CreateDynamicFrictionAttr(0.6)
physics_material.CreateRestitutionAttr(0.0)
UsdShade.MaterialBindingAPI.Apply(prim).Bind(material, materialPurpose="physics")
```

정지 마찰과 운동 마찰은 접촉면이 미끄러지기 시작하거나 이미 미끄러질 때의 저항에 관여합니다. Restitution은 충돌 후 튕기는 성질입니다. 재질 prim을 만드는 것에 더해 **바퀴에 바인딩하는 마지막 줄**이 있어야 바퀴가 그 설정을 사용합니다.

색을 바꾸는 실습도 해보세요. **Create > Materials > OmniPBR**로 외관 재질을 만들고 몸체에 연결한 뒤 Albedo와 Roughness를 조절합니다. 기본 코드는 간단한 표시 색인 `displayColor`를 사용합니다. OmniPBR의 색이나 거칠기는 바퀴의 physics 재질과 다른 설정입니다.

### 실행 결과 확인하기

몸체의 색을 바꾸면 화면에서 즉시 차이를 볼 수 있습니다. 반면 WheelPhysics의 값은 접촉이 일어나야 운동에 영향을 줍니다. Property에서 바퀴의 **physics 목적 material binding**이 `/World/Looks/WheelPhysics`를 가리키는지 확인하고 Play하세요. 다른 부품과 연결되어 움직이는지는 아직 확인할 대상이 아닙니다.

## 3. 로봇 외형의 네 가지 역할 정리

```text
Xform과 geometry → 어디에 어떤 모양으로 보일지
Rigid Body       → 힘을 받으면 어떻게 움직일지
Collider         → 어디에서 다른 물체와 만날지
Physics Material → 접촉에서 얼마나 미끄러지거나 튕길지
```

**옆에 놓인 부품들을 하나의 기구로 묶으려면 관절이 추가로 필요합니다.** 이번에는 관절을 넣기 전 상태를 분명히 이해하는 것이 중요합니다. “세 부품이 모두 바닥에 닿는다”와 “세 부품이 연결되어 함께 움직인다”는 서로 다른 결과입니다.

## 4. 간단한 확인 실험

Stop 상태에서 `/World/Looks/WheelPhysics`의 **Restitution만 0에서 0.7로** 바꾸고 다시 Play하세요. 시작 높이와 마찰은 그대로 둡니다.

바퀴가 처음 바닥에 닿은 뒤 튀어 오르는 정도를 비교해 보세요. 몸체에는 이 물리 재질을 연결하지 않았으므로 바퀴와 같은 변화가 반드시 나타나지는 않습니다. 기대한 차이가 없다면 값 자체보다 바퀴의 재질 연결을 먼저 확인하세요.

## 실행할 때 막히면

- **바퀴가 몸체에서 분리됩니다**: 기본 장면에는 관절이 없습니다. `initial_inventory.json`의 빈 `joints`와 함께 이번 단계의 출발 상태인지 확인하세요.
- **색은 바뀌는데 마찰이 그대로입니다**: 외관 재질과 physics 재질을 구분하고 바퀴의 물리 재질 연결을 확인하세요.
- **출력 폴더가 이미 있다는 오류가 납니다**: `--output`은 기존 폴더를 덮어쓰지 않습니다. `output/second`처럼 새 경로로 실행하세요.
- **저장한 장면에서 이어가고 싶습니다**: 같은 실행 명령에 `--stage`로 저장한 `stage.usda`의 절대 경로를 지정하고 출력은 새 폴더로 바꾸세요. 이전 결과 위에 새 편집 layer가 만들어집니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Tutorial 2: Assemble a Simple Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_assemble_robot.html)에 대응합니다. 원문의 도형·물리·재질 편집을 직접 만든 출발 장면과 연결해 설명합니다.

장면 생성과 초기 목록 저장은 `run.py`가 수행하며, Play와 재질 편집은 독자가 GUI에서 진행합니다. `tutorial.json`의 검증 상태는 `not_run`입니다. 여기에 적은 낙하와 반발은 실습에서 확인할 관찰 기준이며 실제 GUI 검증 완료 기록은 아닙니다.
