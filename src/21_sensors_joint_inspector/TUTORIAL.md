# 21. 한 관절 팔의 회전축과 제한각 확인하기

## 이번에 배우는 것

**월드에 고정된 한 관절 팔을 만들고, Physics Inspector에서 연결 위치·회전축·관절 한계를 확인합니다.**

팔이 엉뚱한 점을 중심으로 돌거나 원하는 각도까지 움직이지 않을 때는 제어 명령보다 관절 설정부터 살펴볼 필요가 있습니다. 이번에는 외부 로봇 에셋 없이 Base와 Link 두 강체만 만들어 관절 구조를 읽습니다.

| 구성 | 역할 | 초기 설정 |
|---|---|---|
| `/World/Arm/Base` | 움직이지 않을 기준 몸체 | 중심 높이 2 m |
| `/World/Arm/FixedRoot` | 월드와 Base를 고정 | ArticulationRootAPI도 적용 |
| `/World/Arm/Link` | 회전할 긴 막대 | 길이 1.5 m, 질량 1 kg |
| `/World/Arm/Joint` | Base와 Link 연결 | Y축 회전, -80°~80° |

**Articulation**은 관절로 연결된 강체들을 로봇 구조로 다루는 방식입니다. 각 몸체의 강체 설정과 연결 구조의 루트 설정은 서로 역할이 다릅니다.

## 1. 먼저 정지 상태의 팔 준비하기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 있는 환경에서 실행합니다. 다음은 저장소 루트 기준 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/21_sensors_joint_inspector/run.py
```

팔을 만들고 초기화한 뒤 타임라인을 **Stop**합니다. 코드가 `app.update()`로 창을 유지하므로 팔이 처음에 가만히 있는 것이 정상입니다. 이번에는 Inspector로 관절을 직접 조작합니다.

현재 코드에는 Link의 비균일 Scale과 관절 연결 위치가 맞지 않는 부분이 있습니다. 관절 축·limit를 읽는 실습은 진행할 수 있지만, 처음 작성한 막대 끝과 회전 중심이 정확히 일치하는 정상 조립 예제로 보지는 마세요. 2절에서 이 차이를 좌표로 확인합니다.

출력은 이 폴더의 `output/날짜_시간/arm.usda`입니다. `--output`으로 직접 지정한다면 새 폴더를 사용하세요. 수동 편집에서는 `--steps`를 생략합니다. `--steps N`은 물리 N단계가 아닌 앱 업데이트 N회 뒤 종료하는 옵션입니다. Headless 기본 240회 업데이트로 파일을 준비할 수는 있지만 Inspector 조작은 확인할 수 없습니다.

### 코드에서 볼 부분

월드에 Base를 붙이는 고정 관절은 다음 설정을 사용합니다.

```python
fixed.CreateBody1Rel().SetTargets(['/World/Arm/Base'])
fixed.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 2))
UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
```

이 관절의 body0은 지정하지 않아 월드가 기준이 됩니다. 월드 쪽 연결 위치는 `(0, 0, 2)`이고, Base의 중심도 같은 위치입니다. 따라서 팔이 무게 때문에 통째로 떨어지지 않도록 Base를 고정합니다.

### 실행 결과 확인하기

Stage에서 `/World/Arm`을 펼쳐 Base·Link·FixedRoot·Joint를 확인하세요. Link는 Base에서 +X 방향으로 뻗습니다. 카메라 밖에 있다면 `/World/Arm`을 선택하고 선택 항목 프레이밍으로 보이게 합니다.

`arm.usda`는 Inspector 편집 전의 관절 설정을 저장합니다. 이후 GUI에서 바꾼 값은 이 파일에 자동 반영되지 않습니다.

## 2. Inspector에서 연결 위치와 축 확인하기

1. **Tools > Physics Toolbar**를 켭니다.
2. **Tools > Physics > Physics Inspector**를 엽니다.
3. Stage에서 `/World/Arm`을 선택하고 조절할 회전 관절 하나가 나타나는지 확인합니다.
4. 관절 위치를 조금씩 바꾸며 Base는 고정되고 Link가 회전하는지 봅니다.

### 코드에서 볼 부분

Base와 Link를 연결하는 관절의 핵심 값입니다.

```python
joint.CreateBody0Rel().SetTargets(['/World/Arm/Base'])
joint.CreateBody1Rel().SetTargets(['/World/Arm/Link'])
joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0))
joint.CreateLocalPos1Attr(Gf.Vec3f(-.75, 0, 0))
joint.CreateAxisAttr('Y')
joint.CreateLowerLimitAttr(-80)
joint.CreateUpperLimitAttr(80)
```

LocalPos는 각 몸체의 좌표계에서 본 관절 위치입니다. 코드가 작성하는 Base 중심은 `(0, 0, 2)`, Link 중심은 `(0.75, 0, 2)`입니다. 여기서 Link의 Scale=`(1.5, 0.15, 0.15)`도 고려해야 합니다. 물리 장면으로 파싱할 때 이 스케일은 local position에 반영됩니다.

```text
Base 쪽 작성 연결점 X = 0
Link 쪽 작성 연결점 X = 0.75 + 1.5 × (-0.75) = -0.375 m
```

따라서 원본의 두 연결점은 작성 상태에서 0.375 m 어긋납니다. 초기화 뒤 PhysX가 정렬한 상태와 코드의 시작 좌표는 달라질 수 있습니다. 이 불일치가 실제로 어떤 움직임을 만드는지는 Inspector와 물리 실행으로 따로 확인해야 합니다.

원래 중심과 크기를 유지하면서 막대 끝을 Base에 붙이는 별도 GUI 수정본을 만들려면, Stop 상태에서 Link 중심 X=`0.75`, Scale X=`1.5`를 확인하고 Joint의 localPos1 X를 `-0.5`로 설정하세요. 그러면 `0.75 + 1.5 × (-0.5) = 0`입니다. Inspector를 닫고 다시 열어 연결점을 확인하고 새 파일로 저장합니다. 현재 `run.py`는 이 값을 자동으로 수정하지 않습니다. 4절 limit 비교에서는 원본을 다시 실행해 다른 조건을 섞지 않습니다.

### 설정에서 볼 부분

Joint에는 목표 0°의 angular drive도 있습니다. `stiffness=100`은 목표 자세로 되돌리는 성향, `damping=10`은 움직임을 감쇠하는 성향을 정합니다. 관절 limit는 움직일 수 있는 범위이고, drive target은 그 범위 안에서 향하려는 목표이므로 같은 값이 아닙니다.

### 실행 결과 확인하기

Inspector에서 값을 움직였을 때 Link가 Y축을 중심으로 회전하는지 확인하세요. XZ 평면에서 끝점의 높이가 바뀌는 모습을 볼 수 있습니다. 초기 lower/upper limit는 -80°와 80°입니다. 이 USD 각도 값은 degree입니다.

일반 물리 재생을 확인할 때는 **Inspector 창을 닫은 다음 Play**하세요. Inspector는 관절 편집을 위해 PhysX를 부분적으로 초기화합니다. 그 상태를 일반 시뮬레이션과 동일하게 다루면 예상과 다른 동작이 나올 수 있습니다.

일반 Play에서는 중력과 angular drive가 함께 작용합니다. 원본의 연결점 불일치가 초기 정렬에 미칠 영향도 구분하세요. 목표가 0°라고 모든 조건에서 실제 각도도 정확히 0°가 되는 것은 아닙니다.

## 3. 관절 설정과 관찰 결과 정리

```text
FixedRoot → Base가 월드에 고정됨
body0/body1 → 어느 두 몸체를 연결할지
localPos0/localPos1 → 두 몸체의 어느 지점을 붙일지
axis → 어느 축으로 회전할지
lower/upper limit → 어디까지 회전할지
drive → 어느 자세를 향해 움직일지
```

하나의 관절에도 역할이 다른 값들이 들어 있습니다. 회전 중심이 틀리면 frame을, 방향이 틀리면 axis를, 움직일 범위가 틀리면 limit를 먼저 확인하세요. 긴 로봇 구조에서도 같은 순서로 작은 관절 하나를 이해할 수 있습니다.

## 4. 간단한 확인 실험

프로그램을 종료하고 1절 명령으로 다시 시작해 초기 팔을 준비합니다. Inspector를 열고 `/World/Arm/Joint`의 Property에서 **upper limit만 80°에서 30°로** 바꿉니다. lower limit는 -80°, axis는 Y로 유지하세요.

Inspector에서 양의 방향 허용 범위가 30°까지로 줄고 음의 방향은 -80°까지 유지되는지 비교합니다. 양쪽 한계를 동시에 바꾸지 않으면 어느 속성이 어느 방향을 제한하는지 더 분명하게 볼 수 있습니다.

수정 결과는 **File > Save As**로 새 파일에 저장하고 Property에서 `-80`, `30`이 남았는지 다시 확인하세요. 처음 생성한 `arm.usda`와 수정본의 차이가 이번 실험 결과입니다.

## 실행할 때 막히면

- **Inspector에 팔이 안 나타남**: `/World/Arm`을 선택했는지, FixedRoot에 ArticulationRootAPI가 있는지, Joint의 두 body 경로가 유효한지 확인하세요.
- **팔 전체가 움직이는 것처럼 보임**: Base 고정 관절의 body1과 월드 연결 위치를 확인하세요. 회전 관절만으로 Base가 월드에 고정되지는 않습니다.
- **일반 Play에서 동작이 이상함**: Physics Inspector 창을 완전히 닫고 재생하세요. 편집용 부분 초기화 상태부터 해제합니다.
- **다시 열면 limit가 원래 값임**: 편집 전 `arm.usda`를 열었는지 확인하세요. GUI 수정본을 별도로 저장해야 합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)에 대응합니다. 공식 Isaac Sim 메뉴와 Inspector 사용 중의 부분 초기화 주의를 대조했습니다. 외부 로봇 대신 한 관절 팔을 코드로 준비한 것은 이 폴더의 구성입니다.

관절 local position의 스케일 처리는 설치된 USD의 물리 파서와 [OpenUSD의 joint parsing 구현](https://github.com/PixarAnimationStudios/OpenUSD/blob/v25.05/pxr/usd/usdPhysics/parseUtils.cpp)을 대조했습니다. 현재 `tutorial.json`은 `not_run`이며 Inspector 슬라이더·PhysX 초기 정렬·일반 Play 동작은 실행하지 않았습니다. 좌표 파싱 확인은 실제 관절 운동 검증과 다릅니다.
