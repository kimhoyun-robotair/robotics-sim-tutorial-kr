# 64. 명령한 토크와 관절이 버티는 힘은 어떻게 다른가요?

## 이번에 배우는 것

**한 관절 팔에서 명령 effort, 측정 effort, 6성분 힘·토크를 함께 읽고 각 배열이 무엇을 나타내는지 구별합니다.**

수평으로 팔을 뻗으면 손에 아무것도 들지 않아도 어깨가 팔의 무게를 버팁니다. 이번에는 같은 상황을 길이 1.5 m의 링크 하나로 만듭니다. 관절의 위치 drive가 목표각 0°를 향해 움직이는 동안, 코드에서 명시적으로 준 effort와 물리 계산이 돌려주는 측정값을 비교합니다.

| 구성 | 이 장면의 설정 |
|---|---|
| `Base` | 높이 2 m에서 월드에 고정된 받침 |
| `Link` | 기본 질량 1 kg, 중심이 회전축에서 0.75 m 떨어진 링크 |
| `Joint` | Y축 회전, -80°~80° 제한, 목표각 0° |
| 위치 drive | stiffness 100, damping 10 |
| `joint_forces.json` | 명령 effort·측정 effort·6성분 반력의 시계열 |

Effort는 관절이 움직일 수 있는 방향에 작용하는 힘의 표현입니다. 회전 관절에서는 토크(N·m), 직선 관절에서는 힘(N)을 뜻합니다. 이 실습은 회전 관절이므로 effort의 단위는 N·m입니다.

## 1. 중력을 받는 한 관절 팔 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 있는 환경에서 저장소 루트 기준으로 실행하세요.

```bash
~/isaacsim/python.sh src/64_sensors_sensors_physics_articulation_force/run.py --steps 240 --output src/64_sensors_sensors_physics_articulation_force/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 60 Hz 물리 계산을 240단계 진행하고 결과를 저장한 뒤 종료합니다. 입력 로봇 자산은 따로 필요하지 않습니다. 코드는 받침·링크·관절을 직접 만듭니다.

출력 폴더는 새 경로여야 합니다. `--output`을 생략하면 이 폴더의 `output/날짜_시간/`에 저장합니다. 창 없이 실행하려면 `--headless`를 추가하세요. `--steps 240`을 빼면 첫 240단계의 기록을 저장한 뒤 GUI에서 물리를 계속 진행하지만 파일에는 추가하지 않습니다.

### 실행 결과 확인하기

`joint_forces.json`의 `samples`에서 초기 움직임과 뒤쪽의 비교적 안정된 구간을 나누어 보세요.

| 필드 | 의미 | 읽을 때 주의할 점 |
|---|---|---|
| `time_s` | 물리 경과 시간(초) | 앱 시작에 걸린 시간과 다름 |
| `applied_effort_Nm` | 사용자가 설정한 effort | 이 코드에는 `set_joint_efforts()` 호출이 없음 |
| `measured_effort_Nm` | 관절의 자유 축 방향으로 측정한 effort | 명령값과 항상 같지 않음 |
| `incoming_force_torque` | 링크에 들어오는 관절의 힘·토크 6성분 | 앞 3개는 N, 뒤 3개는 N·m |

**명령 effort가 0이어도 관절의 측정값은 0이 아닐 수 있습니다.** 위치 drive와 관절 제약이 중력 아래의 링크를 지지하기 때문입니다. 힘이 보인다는 사실만으로 사용자가 effort 명령을 보냈다고 역으로 판단하지 마세요.

## 2. 관절 구조와 배열 인덱스 따라가기

### 코드에서 볼 부분

팔의 연결은 다음과 같습니다.

```text
월드
    → FixedRoot로 Base 고정
    → Joint로 Base와 Link 연결
    → Y축 회전만 허용하고 drive로 목표각 유지
```

관절의 두 기준점을 만드는 부분을 보세요.

```python
joint.CreateBody0Rel().SetTargets(['/World/Arm/Base'])
joint.CreateBody1Rel().SetTargets(['/World/Arm/Link'])
joint.CreateLocalPos0Attr(Gf.Vec3f(0,0,0))
joint.CreateLocalPos1Attr(Gf.Vec3f(-.75,0,0))
joint.CreateAxisAttr('Y')
```

링크 중심은 처음 x=0.75 m에 있지만 회전축은 x=0 m에 있습니다. 그래서 링크 기준 관절 위치가 `(-0.75,0,0)`입니다. 두 body의 서로 다른 로컬 좌표가 같은 월드 회전축을 가리키도록 맞추는 것입니다. 이 연결이 잘못되면 링크가 엉뚱한 지점을 중심으로 움직이거나 큰 반력이 생깁니다.

측정 배열에는 두 종류의 인덱스를 사용합니다.

```python
world.reset()
dof = robot.get_dof_index('Joint')
link_index = robot._articulation_view.get_link_index('Link')
```

- `dof`: 회전 가능한 자유도의 번호입니다. 두 effort 배열에서 사용합니다.
- `link_index`: 연결된 강체의 번호입니다. `get_measured_joint_forces()`의 행을 고를 때 사용합니다.

힘 배열에는 base에 대응하는 행도 있지만 DOF 배열은 움직일 수 있는 자유도를 셉니다. **같은 이름의 관절을 살펴봐도 두 인덱스가 같다고 가정할 수 없습니다.** 코드가 JSON 맨 위에 두 번호를 함께 저장하는 이유입니다. `_articulation_view`는 내부 경로를 사용하므로 다른 Isaac Sim 버전으로 옮길 때는 다시 확인해야 합니다.

### 힘의 좌표계에서 볼 부분

`incoming_force_torque`는 `[Fx,Fy,Fz,Tx,Ty,Tz]` 순서입니다. 기준은 해당 링크로 들어오는 관절의 child frame입니다. 예를 들어 링크가 회전하면 이 좌표계도 바뀝니다. 그래서 로컬 `Fz`를 곧바로 월드 수직 힘이라고 부르면 안 됩니다.

Y축 회전의 스칼라 effort와 6성분 벡터를 비교할 때도 값의 부호만 맞추려 하지 마세요. 어떤 body에 작용하는 값인지, 어떤 축 방향으로 표시했는지부터 확인해야 합니다.

## 3. 중력 하중과 측정값의 관계 정리

링크가 정확히 수평이고 정지해 있다면 중력의 회전 효과 크기는 다음처럼 가늠할 수 있습니다.

```text
질량 × 중력 가속도 × 회전축에서 중심까지 거리
= 1 × 9.81 × 0.75
≈ 7.36 N·m
```

이 값은 장면 치수에서 계산한 **수평 정지 상태의 기준 규모**입니다. 시뮬레이션에서는 링크가 진동하거나 처지고, drive가 목표각을 회복하는 중일 수 있습니다. 따라서 매 행의 측정 토크를 7.36에 맞추는 대신, 초기 과도 구간과 자세가 안정된 구간을 구분해서 읽으세요.

세 API는 각각 “어떤 effort를 명령했는가”, “관절의 움직임 방향에 어떤 effort가 측정되는가”, “관절을 통해 어떤 힘과 토크가 전달되는가”를 보여 줍니다.

## 4. 간단한 확인 실험

링크 질량만 1 kg에서 2 kg으로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/64_sensors_sensors_physics_articulation_force/run.py --steps 240 --mass 2 --output src/64_sensors_sensors_physics_articulation_force/output/mass2
```

길이와 목표각, drive 설정은 그대로입니다. 두 JSON의 뒤쪽 구간에서 측정 토크의 크기와 변동을 비교하고 GUI에서 처짐이 달라지는지도 보세요. 수평 정지 상태라면 중력 토크 규모는 두 배지만 실제 자세가 달라질 수 있으므로, 각 행이 정확히 두 배라는 기준은 사용하지 않습니다.

## 실행할 때 막히면

- **물리 handle이 초기화되지 않았다는 오류**: 힘 읽기보다 `world.reset()`이 먼저 실행되어야 합니다. 코드를 일부만 실행했다면 전체 `run.py`로 다시 시작하세요.
- **힘 배열에서 다른 관절을 읽는 것 같음**: JSON의 `dof_index`와 `link_index`를 구분하세요. effort 배열의 인덱스를 힘 배열에 그대로 사용하지 않습니다.
- **링크가 예상과 다르게 움직임**: `Joint`의 Body0·Body1, 두 localPos, Y축 설정을 확인하세요. `arm.usda`에서 구조를 살펴볼 수 있습니다.
- **토크 부호가 예상과 반대임**: child joint frame과 관절 축을 확인하세요. 우선 크기와 시간에 따른 변화를 비교합니다.
- **저장한 `arm.usda`에서 초기 움직임을 못 봄**: 이 파일은 저장 시점의 장면입니다. 초기 수평 자세부터 보려면 `run.py`를 재실행하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Articulation Joint Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_articulation_force.html)에 대응합니다. 공식 예제의 여러 관절 로봇을 한 관절 구조로 바꾸어 인덱스와 물리량을 비교합니다.

이번 개정에서는 로컬 관절 구성과 설치된 `SingleArticulation`의 힘 좌표계 설명을 대조했습니다. 물리 실행과 질량 비교는 수행하지 않았으며 `tutorial.json`은 `not_run`입니다. 위 수치는 측정 결과가 아니라 해석을 위한 기준 계산입니다.
