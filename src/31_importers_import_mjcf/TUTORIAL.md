# 31. MJCF의 중첩 body를 USD 관절로 가져오기

## 이번에 배우는 것

**작은 진자의 MJCF를 가져오고, 중첩된 body와 hinge가 어떤 USD 물리 구조로 변환되는지 확인합니다.**

MJCF는 MuJoCo에서 사용하는 로봇·장면 설명 형식입니다. 부모 body 안에 자식 body를 넣어 좌표 관계를 표현할 수 있습니다. 이번에는 XML 몇 줄로 된 진자를 사용해 부모 좌표, 관절축, 형상 끝점이 어떤 의미인지 읽어 봅니다.

| `pendulum.xml` 요소 | 이 실습의 의미 |
|---|---|
| `body mount` | 높이 1 m의 지지점 |
| 그 안의 `body pendulum` | 지지점 기준으로 배치한 진자 |
| `joint hinge` | Y축 회전, 범위 -1.5~1.5 rad |
| `geom rod` | 두 끝점을 잇는 capsule 형상의 막대 |

입력을 USD로 가져온 뒤 물리를 진행하지만, MuJoCo와 PhysX의 모든 actuator·solver 동작이 같다고 검증하는 실습은 아닙니다.

## 1. 로컬 진자 가져오기

Isaac Sim 5.1과 지원 RTX GPU가 필요합니다. `isaacsim.asset.importer.mjcf`는 실행기가 활성화합니다. 기본 모델은 외부 mesh나 MuJoCo 설치 없이 이 폴더의 `pendulum.xml`을 사용합니다.

저장소 루트에서 실행하세요. `~/isaacsim`은 자신의 설치 경로입니다.

```bash
~/isaacsim/python.sh src/31_importers_import_mjcf/run.py --model local --steps 300 --output src/31_importers_import_mjcf/output/pendulum_a
```

새 출력 폴더를 사용합니다. 0.01초 간격으로 물리 300단계, 즉 시뮬레이션 시간 약 3초를 진행한 뒤 보고서를 저장하고 종료합니다. 단계 수를 생략하면 GUI는 창을 닫을 때까지, headless는 300단계까지 실행합니다. GUI의 `--steps 0`도 무제한이며 headless에는 양수만 허용합니다.

### 코드에서 볼 부분

진자의 형상은 다음 설정으로 기울어진 막대를 만듭니다.

```xml
<body name="mount" pos="0 0 1">
  <geom name="mount_shape" type="sphere" size="0.06" mass="1"/>
  <body name="pendulum" pos="0 0 0">
    <joint name="hinge" type="hinge" axis="0 1 0" limited="true" range="-1.5 1.5" damping="0.1"/>
    <geom name="rod" type="capsule" fromto="0 0 0 0.3 0 -0.3" size="0.025" mass="0.3"/>
  </body>
</body>
```

`pendulum`의 `(0, 0, 0)`은 세계 원점이 아니라 부모 mount 기준입니다. `fromto`의 앞 세 숫자는 막대의 시작점, 뒤 세 숫자는 끝점입니다. 초기 자세에서 끝점은 지지점보다 x로 0.3 m, z로 -0.3 m 이동한 위치에 놓입니다.

파일의 `compiler angle="radian"`에 따라 `range`는 rad 단위입니다. `run.py`도 `World(stage_units_in_meters=1.0, physics_dt=0.01)`을 명시합니다. 단위와 시간 간격은 가져온 로봇을 해석하는 기준이므로 XML과 실행 환경을 함께 읽으세요.

### 실행 결과 확인하기

`output/pendulum_a/`에 생성한 두 파일을 확인합니다.

| 파일·필드 | 의미 |
|---|---|
| `imported.usda` | 물리 루프 전에 저장한 변환 Stage |
| `report.json`의 `source` | 실제 가져온 MJCF 경로 |
| `joints` | Stage에서 찾은 USD Physics Joint 경로 |
| `stage_meters_per_unit` | Stage의 길이 단위, 기본 1.0 |

기본 모델에서 hinge와 지지점을 고정하는 joint가 생성되는지 확인하세요. 보고서는 관절 **목록**을 기록하며 진자의 각도·속도 시계열은 저장하지 않습니다. 관절 목록이 있다는 사실과 진자의 운동이 예상과 일치한다는 사실은 구분합니다.

## 2. 가져오기 설정과 다른 모델 비교하기

`run.py`는 먼저 `MJCFCreateImportConfig`로 설정을 만든 뒤 다음 조건을 적용합니다.

```python
config.set_fix_base(args.model == 'local')
config.set_make_default_prim(False)
```

local 진자는 지지점을 고정하고, ant·humanoid는 base가 움직일 수 있게 가져옵니다. `MJCFCreateAsset`은 `/World/Imported` 아래에 모델을 생성합니다. 프로그램은 해당 Prim이 존재하는지와 USD Physics Joint가 최소 하나 있는지 확인한 뒤 진행합니다.

### 코드에서 볼 부분

다른 모델의 경로는 importer 확장 설치 위치에서 찾습니다.

```python
source = Path(get_extension_path_from_name('isaacsim.asset.importer.mjcf')) / 'data/mjcf' / f'nv_{args.model}.xml'
```

설치된 예제 파일이 있는 환경에서 다음 명령을 실행할 수 있습니다.

```bash
~/isaacsim/python.sh src/31_importers_import_mjcf/run.py --model ant --steps 300 --output src/31_importers_import_mjcf/output/ant_a
~/isaacsim/python.sh src/31_importers_import_mjcf/run.py --model humanoid --steps 300 --output src/31_importers_import_mjcf/output/humanoid_a
```

이 모드들도 importer를 통해 실제 모델을 가져오지만 보행 제어기는 추가하지 않습니다. 로봇이 쓰러지거나 주저앉더라도 학습된 보행 정책이 실패했다고 해석할 수 없습니다. 이번 코드에는 그런 정책 실행이 없습니다.

### 실행 결과 확인하기

각 `report.json`의 source와 joint 경로를 비교하세요. GUI에서는 Stage에서 `/World/Imported`를 펼치고 body 관계와 collider를 살펴봅니다. 진자의 운동이 예상보다 작거나 고정된 듯 보인다면 importer가 만든 drive stiffness·damping도 확인하세요. XML의 hinge damping 하나만으로 변환 후 모든 제어 설정을 알 수는 없습니다.

### 같은 모델을 GUI로 가져오기

1. 앞 실행을 종료하고 새 Isaac Sim 창에서 **Window > Extensions**의 `isaacsim.asset.importer.mjcf`를 켭니다. AUTOLOAD 옆 폴더 아이콘에서 설치 경로를 열면 `data/mjcf/nv_humanoid.xml`, `nv_ant.xml`을 찾을 수 있습니다.
2. **File > Import**로 원하는 XML을 선택하고, USD 출력은 설치 폴더가 아닌 자신의 새 작업 폴더로 지정합니다.
3. 로컬 진자는 **Static Base**, Ant·Humanoid는 **Moveable Base**로 설정합니다. 입력 모델과 base 고정 여부를 앞의 코드 실행과 같게 맞춰보세요.
4. 가져온 Stage에서 로봇의 Articulation Root와 joint의 Body0/Body1을 확인합니다. Physics Scene이 있는지 조사하고, 없을 때만 **Create > Physics > Physics Scene**으로 추가합니다.
5. **Create > Physics > Ground Plane**으로 지면을 준비하고 Play합니다. Collider 표시를 켜 화면의 mesh와 접촉 형상을 비교하세요.

GUI importer의 다른 기본값은 Python 설정과 다를 수 있습니다. 관성 가져오기, 단위, 자체 충돌까지 같은 조건인지 확인한 뒤 운동을 비교하세요. 모델과 설정을 동시에 바꾸면 결과 차이의 원인을 나누기 어렵습니다.

## 3. 좌표와 변환 결과 정리

```text
MJCF body 중첩 → 부모 기준 위치
MJCF hinge     → 두 body 사이의 허용 회전
MJCF geom      → 보이는 형상과 가져온 물리 형상
                         ↓
USD Prim·Physics Joint 검사 → PhysX에서 물리 진행
```

`/World/Imported`가 생겼는지 확인하는 것은 첫 단계입니다. 이후 joint의 연결 대상, 축, 범위, collider, Stage 단위를 차례대로 확인해야 변환 결과를 이해할 수 있습니다. 물리 엔진 사이의 결과 비교에는 추가적인 상태 기록과 동일한 제어 조건이 필요합니다.

## 4. 간단한 확인 실험

`pendulum.xml`의 hinge `damping`만 0.1에서 0.5로 바꾸고 새 출력 경로로 실행해 보세요. 원래 값을 메모해 두고 비교 후 복구하세요.

```bash
~/isaacsim/python.sh src/31_importers_import_mjcf/run.py --model local --steps 300 --output src/31_importers_import_mjcf/output/damping_05
```

변환된 joint 속성에 변경값이 어떻게 반영되었는지 먼저 확인합니다. 다른 drive 조건이 같다면 더 큰 감쇠는 운동을 더 빠르게 줄이는 방향으로 작용할 것으로 예상할 수 있습니다. 실제 진동은 GUI에서 관찰하고, `report.json`만으로 진동 감소를 판정하지 마세요. 이 보고서에는 각도·속도 데이터가 없습니다.

## 실행할 때 막히면

- **File > Import에서 MJCF를 선택할 수 없음**: `isaacsim.asset.importer.mjcf`가 켜져 있는지 Extensions에서 확인하세요.
- **Ant·Humanoid 입력 파일 오류**: importer 설치 폴더의 `data/mjcf/nv_ant.xml`, `nv_humanoid.xml`을 확인하세요. 기본 local 모드부터 구분해 실행하세요.
- **모델 크기나 중력이 이상함**: Stage의 `metersPerUnit`과 입력 단위를 확인하세요. cm 장면의 중력 숫자를 m 장면에 그대로 사용하지 않습니다.
- **`report.json`이 아직 없음**: 물리 루프가 끝난 뒤 저장됩니다. 무제한 GUI 실행 중이라면 창을 종료하거나 양수 `--steps`로 다시 실행하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial: Import MJCF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_mjcf.html)에 대응합니다. 로컬 진자를 추가해 중첩 body·단위·joint 생성을 읽기 쉽게 구성했고, 설치된 Ant·Humanoid도 선택할 수 있습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 2026-09-14의 local headless 60단계에서 hinge 생성과 `metersPerUnit=1.0`을 확인한 기록입니다. 진자 궤적의 정확성, Ant·Humanoid와 GUI import는 그 기록의 검증 범위 밖입니다. 이 기록은 당시 변환 결과의 근거이며 현재 실행기의 재검증 결과는 아닙니다.
