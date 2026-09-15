# 68. 겹친 물체를 추적하는 Proximity Sensor

## 이번에 배우는 것

**두 상자가 겹쳤다가 분리되는 과정을 기록하고, overlap 목록·원점 거리·머문 시간이 각각 무엇을 뜻하는지 구별합니다.**

Proximity라는 이름만 보면 멀리 있는 물체까지의 거리를 계속 읽는 센서를 떠올릴 수 있습니다. 이 실습의 센서는 먼저 자신의 영역과 겹치는 물체를 찾고, 그 물체의 정보를 사전에 넣습니다. 따라서 거리 숫자보다 **어떤 물체 경로가 목록에 들어왔는지**부터 확인해야 합니다.

| 구성 | 기본 설정과 의미 |
|---|---|
| `/World/Cube1` | 센서가 붙은 한 변 1 m 상자 |
| `/World/Cube2` | 겹침을 관찰할 상대 상자 |
| 중심 간격 | `--separation 0.8`, 처음에는 x 방향으로 0.2 m 겹침 |
| 시작 높이 | 두 상자 모두 중심 z=3 m |
| `distance` | 두 prim 원점 사이의 거리(m) |
| `duration` | 해당 overlap을 기록한 뒤 지난 벽시계 시간(초) |

두 상자는 동적 강체입니다. 처음 겹쳐 둔 상태를 물리 엔진이 해소하고, 이후에는 중력으로 떨어집니다. 이 변화를 이용해 목록의 등장과 이탈을 살펴봅니다.

## 1. 겹친 상자를 실행하고 상대 경로 찾기

Isaac Sim 5.1과 지원 NVIDIA GPU 환경에서 저장소 루트 기준으로 실행하세요.

```bash
~/isaacsim/python.sh src/68_sensors_sensors_physics_proximity/run.py --steps 240 --output src/68_sensors_sensors_physics_proximity/output/base
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 240단계 후 `proximity.json`과 `scene.usda`를 저장하고 종료합니다. 출력 폴더는 새 경로여야 하며 생략하면 이 튜토리얼의 `output/날짜_시간/`을 사용합니다.

초기 겹침은 빠르게 해소될 수 있으므로 GUI의 마지막 모습만으로 판단하지 마세요. `--steps 240`을 빼면 첫 240단계 기록 후 창을 계속 열어 둘 수 있지만, 이후 목록은 파일에 추가하지 않습니다. `--headless`를 추가하면 창 없이 같은 기록을 만듭니다.

### 실행 결과 확인하기

`proximity.json`의 행에는 `simulation_time_s`와 `overlaps`가 있습니다. 목록이 비었는지만 세지 말고 다음 코드처럼 **상대 상자 경로**를 골라 읽어 보세요. 아래는 저장소 루트의 일반 Python에서 실행할 수 있는 파일 읽기입니다.

```python
import json
from pathlib import Path

rows = json.loads(Path(
    'src/68_sensors_sensors_physics_proximity/output/base/proximity.json'
).read_text())
for row in rows:
    other = row['overlaps'].get('/World/Cube2')
    if other is not None:
        print(row['simulation_time_s'], other['distance'], other['duration'])
```

기본 배치에서는 처음 몇 행에서 상대 상자 항목이 나타나는지, 분리 후 항목이 없어지는지 확인합니다. 센서는 자기 경로를 제외하도록 설정하지 않았으므로 `/World/Cube1`이 보일 수 있고, 낙하 뒤에는 바닥과 관련된 항목이 보일 수 있습니다.

콘솔의 `frames_with_overlap`은 **어떤 항목이든 있는 행 수**입니다. 이 숫자가 크다는 이유만으로 두 상자가 계속 겹쳤다고 판단할 수 없습니다.

## 2. 영역 등록과 반환 데이터 따라가기

### 코드에서 볼 부분

```python
sensor = ProximitySensor(cube1.prim)
register_sensor(sensor)
world.reset()
```

센서에 Cube1 prim을 넘긴 뒤 매번 갱신될 센서 목록에 등록합니다. 설치된 5.1 구현은 부모 prim의 위치·회전·scale을 이용한 상자 영역으로 PhysX overlap query를 수행합니다. 이 실습은 크기와 scale이 맞는 단위 큐브라서 그 영역과 큐브를 연결해 보기 쉽습니다.

물리 단계 뒤에는 현재 사전을 읽습니다.

```python
data = sensor.get_data()
```

사전의 키는 겹친 물체 경로이고 값에는 거리와 지속 시간이 들어 있습니다. 거리 계산은 두 prim의 월드 원점을 가져와 그 차이의 길이를 구합니다. 처음 중심 간격이 0.8 m이므로, 표면이 겹쳐 있어도 원점 거리는 양수입니다. **이 값은 표면 사이 빈틈이나 침투 깊이가 아닙니다.**

실행이 끝날 때 `finally`에서 `clear_sensors()`를 호출합니다. 센서 생성만큼 등록 해제도 필요한 이유는 앱의 갱신 목록에 이전 센서를 남기지 않기 위해서입니다.

### 두 시계에서 볼 부분

로컬 실행기는 `world.current_time`을 `simulation_time_s`로 저장합니다. 반면 설치 구현의 overlap 지속 시간은 다음 관계로 계산합니다.

```text
simulation_time_s: 진행한 물리 단계에 따른 시뮬레이션 시간
duration: 현재 time.time() - 해당 overlap의 시작 time.time()
```

`time.time()`은 실제 컴퓨터 시계입니다. 렌더링이 느려지거나 앱에 부하가 생기면 시뮬레이션 1초를 진행하는 데 실제로 더 오래 걸릴 수 있습니다. 두 필드가 모두 초 단위여도 같은 시계를 뜻하지 않으므로 서로 빼서 센서 지연으로 해석하지 마세요.

## 3. 겹침·거리·시간의 관계 정리

```text
부모 상자 영역으로 overlap query
    → 겹친 prim 경로를 목록에 기록
    → 각 경로의 원점 거리와 벽시계 지속 시간 갱신
    → 겹침에서 벗어난 경로는 목록에서 제거
```

상대 경로가 없다는 것은 이 센서가 그 시점에 그 물체를 overlap 대상으로 반환하지 않았다는 뜻입니다. 먼 물체의 거리가 0이라는 뜻도, 모든 거리 측정이 실패했다는 뜻도 아닙니다. 이 센서는 **영역에 들어온 물체와 머문 시간을 추적하는 용도**로 읽어야 합니다.

설치된 5.1 wrapper에는 목록 처리의 제한이 있습니다. 이전 프레임과 overlap **개수가 바뀌었을 때** 이탈한 경로를 정리하므로, 한 물체가 나가며 다른 물체가 들어와 개수가 같으면 오래된 경로가 사전에 남을 수 있습니다. 기본 비교에서는 `/World/Cube2`의 초기 겹침과 분리를 먼저 보세요. 여러 대상이 교체되는 장면으로 확장할 때는 반환 사전만으로 정확한 이탈 시점을 확정하지 않습니다.

## 4. 간단한 확인 실험

초기 중심 간격만 0.8 m에서 1.5 m로 늘려 보세요.

```bash
~/isaacsim/python.sh src/68_sensors_sensors_physics_proximity/run.py --steps 240 --separation 1.5 --output src/68_sensors_sensors_physics_proximity/output/separated
```

두 상자 사이에는 시작부터 0.5 m의 표면 간격이 생깁니다. 기본 결과와 첫 행들을 비교해 `/World/Cube2` 항목이 사라지는지 확인하세요. 자기 자신이나 바닥 항목까지 모두 비어야 한다는 조건을 붙이지 않습니다. 바뀐 것은 상대 상자와의 초기 겹침입니다.

## 실행할 때 막히면

- **기본 실행에서 상대 상자가 안 보임**: JSON 앞부분부터 확인하세요. 마지막 행에는 초기 겹침이 이미 해소되었을 수 있습니다. 초기 위치·collider·센서 등록도 대조합니다.
- **분리했는데 overlap 행 수가 0이 아님**: `overlaps`의 실제 경로를 확인하세요. 자기 자신이나 바닥 항목일 수 있습니다.
- **duration이 실행마다 크게 다름**: 벽시계 값이므로 렌더링 속도와 컴퓨터 부하에 영향을 받습니다. 고정된 시뮬레이션 시간과 동일하게 기대하지 마세요.
- **겹쳐 있는데 distance가 양수임**: 원점 사이 거리이므로 정상적으로 가능한 결과입니다.
- **출력은 저장됐지만 비교가 애매함**: 코드에는 상대 상자 검출을 강제하는 성공 검사가 없습니다. `/World/Cube2`의 등장·이탈을 실제 데이터로 확인하세요.
- **떠난 물체의 경로가 계속 남음**: 같은 프레임에 다른 물체가 들어와 overlap 개수가 유지됐는지 확인하세요. 설치 wrapper의 개수 기반 이탈 처리 제한일 수 있습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Proximity Sensor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_physics_proximity.html)에 대응합니다. 공식 두 큐브 overlap 예제를 로컬 시계열 저장과 간격 비교로 구성했습니다.

거리·벽시계 duration·자기 경로 처리 설명은 설치된 `proximity_sensor.py`와 대조했습니다. 이번 개정에서는 실제 overlap을 실행하지 않았으며 `tutorial.json`은 `not_run`입니다. 기본 초기 겹침을 놓치지 않고 관측했는지는 위 데이터 확인으로 판단해야 합니다.
