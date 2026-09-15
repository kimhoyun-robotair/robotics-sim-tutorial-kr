# 65. 떨어지는 상자의 접촉 센서는 언제 힘을 읽나요?

## 이번에 배우는 것

**상자의 자유낙하·충돌·정지를 하나의 기록으로 읽으며, 접촉 여부와 접촉력의 의미를 구별합니다.**

상자에는 공중에서도 중력이 작용합니다. 하지만 바닥과 닿기 전에는 바닥이 상자를 미는 접촉력이 없습니다. 이번에는 상자 높이와 접촉 센서값을 함께 기록해 이 차이를 확인합니다.

| 구성 | 기본값 | 관찰 의미 |
|---|---|---|
| 상자 크기 | 한 변 0.5 m | 바닥에 놓였을 때 중심 높이는 약 0.25 m |
| 초기 중심 높이 | 2 m | 바닥까지 낙하할 공간 |
| 질량 | 1 kg | 정지 후 지지력의 기준은 약 9.81 N |
| `/World/Cube/Contact` | 상자의 자식 ContactSensor prim | 부모 상자의 접촉 읽기 |
| 기록 주기 | 물리 60 Hz, 최신 데이터 읽기 | 높이와 힘을 물리 단계별로 비교 |

충돌 순간의 힘은 낙하 속도를 줄이는 동적 하중까지 포함합니다. 그러므로 정지 후의 무게와 충돌 순간의 최대 힘을 같은 값으로 기대하면 안 됩니다.

## 1. 상자를 떨어뜨리고 접촉 기록 만들기

Isaac Sim 5.1과 지원 NVIDIA GPU 환경에서 저장소 루트 기준으로 실행하세요.

```bash
~/isaacsim/python.sh src/65_sensors_sensors_physics_contact/run.py --steps 240 --output src/65_sensors_sensors_physics_contact/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 코드는 바닥과 상자를 만든 뒤 물리 240단계, 약 4초를 진행합니다. 유효한 접촉이 관측되면 `contact.json`과 `scene.usda`를 쓰고 종료합니다.

출력 폴더는 새 경로를 사용하세요. `--output`을 생략하면 이 튜토리얼의 `output/날짜_시간/`에 저장합니다. 창 없이 실행할 때는 `--headless`를 추가합니다. `--steps 240`을 빼면 첫 240단계만 저장하고 창을 닫을 때까지 물리를 계속 관찰할 수 있습니다.

### 실행 결과 확인하기

`contact.json`의 앞·중간·뒤 행을 다음 세 구간으로 나누어 읽어 보세요.

| 구간 | `height_m` | `valid`, `contact`, `force_N`에서 볼 점 |
|---|---|---|
| 공중 | 2 m에서 감소 | 유효한 비접촉 샘플인지 먼저 확인 |
| 충돌 | 약 0.25 m에 접근 | 접촉 시작과 순간적인 큰 힘 |
| 정지 | 약 0.25 m 부근 유지 | 유효 접촉과 약 9.81 N의 지지력 |

`valid=false`는 힘이 0이라는 측정 결과와 다릅니다. 센서가 아직 쓸 수 있는 데이터를 내지 않았다는 뜻이므로 분석에서 먼저 제외하세요. `contact=true`는 접촉 여부, `force_N`은 그때의 힘 크기를 나타냅니다.

콘솔에는 `last_force_N`과 `weight_N`이 함께 출력됩니다. 첫 값은 마지막 센서 읽기이고 두 번째는 `mass × 9.81`로 계산한 비교 기준입니다. 두 값은 상자가 충분히 정지한 뒤에 비교하는 것이 좋습니다.

## 2. 부모 상자의 접촉을 센서값으로 읽기

### 코드에서 볼 부분

```python
sensor = ContactSensor(
    '/World/Cube/Contact', frequency=60,
    min_threshold=0, max_threshold=1e7, radius=-1,
)
```

센서를 `/World/Cube`의 자식으로 만드는 이유는 이 상자에서 발생한 접촉을 읽기 위해서입니다. 기본 `radius=-1`은 부모 collider 전체의 접촉을 사용합니다. 센서 원점이 상자 중심에 있어도 바닥과 맞닿은 상자 표면의 힘을 읽을 수 있습니다.

`min_threshold`는 접촉으로 받아들일 최소 힘이고 `max_threshold`는 출력 상한입니다. 이 실습에서는 0과 큰 상한을 사용해 문턱값 때문에 착지 과정이 가려지지 않도록 했습니다.

```python
reading = interface.get_sensor_reading(
    '/World/Cube/Contact', use_latest_data=True
)
```

이 호출은 최신 물리 단계의 센서 읽기를 가져옵니다. 이후 `reading.time`, `is_valid`, `in_contact`, `value`와 상자 중심 높이를 한 행에 저장합니다. 센서 주기보다 물리가 빠른 경우 `use_latest_data=True`는 최신 물리 정보를 선택하는 옵션입니다. 물리 자체보다 더 빠른 새 접촉 정보를 만드는 옵션은 아닙니다.

접촉 센서는 PhysX의 접촉 보고를 부모 물체와 관심영역 기준으로 읽습니다. 바닥과 상자에는 충돌 형상이 있어야 합니다. 화면에 보이는 mesh만 있고 collider가 없다면 접촉 자체가 생기지 않습니다.

### 저장 전 검사에서 볼 부분

```python
if not any(r['valid'] and r['contact'] for r in rows):
    raise RuntimeError('No valid contact observed; simulate long enough for the cube to land')
```

최소한 한 번은 실제 유효 접촉을 보아야 JSON을 저장합니다. 짧게 실행해 상자가 아직 공중에 있으면 이 검사가 실패할 수 있습니다. 반대로 이 검사를 통과했다고 정지 힘의 정확성까지 자동 확인한 것은 아닙니다. 마지막 구간의 높이와 힘을 직접 대조하세요.

### 같은 접촉을 OmniGraph에서 읽기

1절을 `--steps` 없이 새 출력 폴더로 실행해 센서가 있는 장면을 유지한 뒤 진행하세요. 그래프는 기존 센서를 읽으며 새 센서를 중복 생성하지 않습니다.

1. **Window > Graph Editors > Action Graph**에서 **New Action Graph**를 만들고 **On Playback Tick**, **Isaac Read Contact Sensor Node**, **To String**, **Print Text**를 추가하세요.
2. Tick → Read Contact Sensor → Print Text 순서로 실행 포트를 연결합니다. 센서의 **Force Value**를 To String에, 문자열 출력을 Print Text의 text에 연결하세요.
3. **Contact Sensor Prim**은 `/World/Cube/Contact`, **Use Latest Data**는 True로 설정합니다. Print Text의 Log Level을 Warning으로 두고 Play 상태에서 힘을 확인하세요.
4. **In Contact**와 **Sensor Time**도 선택해 살펴보세요. 힘 하나만 출력하는 것보다 접촉 여부와 측정 시점을 함께 읽으면 API의 `in_contact`, `time`, `value`가 그래프에서 어떻게 대응하는지 알 수 있습니다.

GUI로 센서를 처음 만들 때는 Rigid Body와 collider가 있는 부모를 선택한 뒤 **Create > Sensors > Contact Sensor**를 사용합니다. 이 장면에서는 이미 `/World/Cube/Contact`가 있으므로 새 센서 작성은 별도 stage에서 진행하세요. raw 접촉의 `impulse`를 읽는 경우 단위는 N·s이며 현재 표의 N 단위 힘과 직접 같다고 비교하지 않습니다. [공식 Contact Sensor 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)를 함께 볼 수 있습니다.

## 3. 접촉력과 무게의 관계 정리

상자가 정지해 있으면 중력은 아래로, 바닥의 지지력은 위로 작용해 균형을 이룹니다.

```text
공중: 중력으로 낙하, 바닥 접촉 없음
충돌: 바닥 접촉이 낙하 운동을 멈춤, 힘이 일시적으로 커짐
정지: 바닥이 무게를 지지, 접촉력 크기가 mg 부근
```

기본 질량 1 kg에서 `mg ≈ 9.81 N`입니다. 충돌 peak는 질량 외에도 속도, 물리 시간 간격, 접촉 계산 설정에 영향을 받습니다. **정지 구간은 무게를 확인하고, 충돌 구간은 시간에 따른 하중 변화를 확인하는 데 사용**하세요.

## 4. 간단한 확인 실험

상자의 질량만 2 kg으로 바꾸세요.

```bash
~/isaacsim/python.sh src/65_sensors_sensors_physics_contact/run.py --steps 240 --mass 2 --output src/65_sensors_sensors_physics_contact/output/mass2
```

바닥에 놓인 뒤 중심 높이는 여전히 약 0.25 m지만 지지력의 기준은 약 19.62 N으로 커집니다. 두 JSON의 마지막 여러 유효 접촉 행을 비교해 보세요. 한 번의 충돌 peak보다 **높이가 안정된 구간의 힘**이 질량 차이를 설명하기 쉽습니다.

## 실행할 때 막히면

- **`No valid contact observed`**: 착지 전에 끝났는지 확인하고 위의 240단계로 실행하세요. 계속 실패하면 상자와 바닥의 collider를 확인합니다.
- **상자가 바닥을 통과함**: mesh 표시와 충돌 설정은 별개입니다. `/World/Cube`의 RigidBody·Collision 설정과 ground plane을 확인하세요.
- **첫 행의 힘이 이상함**: `valid`를 먼저 읽고 초기 무효값을 제외하세요.
- **정지 힘이 무게보다 훨씬 큼**: 아직 충돌하거나 튀는 구간인지 `height_m`과 함께 보세요. 마지막 한 행 대신 안정된 여러 행을 확인합니다.
- **센서 위치나 부모를 바꾼 뒤 읽기가 안 됨**: Stop한 상태에서 편집하고 다시 Play해 물리 연결을 초기화하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Contact Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_contact.html)에 대응합니다. 공식 센서 생성·읽기 흐름을 낙하 상자에 적용해 높이와 힘을 함께 저장합니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 질량의 headless 180단계에서 180개 샘플과 약 9.81 N의 정지 힘을 확인한 과거 기록입니다. 현재 파일의 재실행이나 질량 변경·GUI 그래프까지 확인한 결과는 아닙니다. 조건은 `tutorial.json`에 있으며, 이번 문서 작업에서는 GPU 실행을 새로 수행하지 않았습니다.
