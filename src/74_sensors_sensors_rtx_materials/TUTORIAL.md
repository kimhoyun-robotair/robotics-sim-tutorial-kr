# 74. 같은 색의 물체도 센서 재질은 다를 수 있습니다

## 이번에 배우는 것

**같은 RGB 색을 가진 세 상자에 서로 다른 비가시 재질을 연결하고, 화면의 색과 센서용 재질 속성을 나누어 확인합니다.**

사람이 보는 색만으로 Lidar나 Radar에 대한 물체의 반응을 모두 설명할 수는 없습니다. Isaac Sim의 비가시 재질은 센서가 다루는 파장 영역의 재질 정보를 USD에 적는 방법입니다. 이번에는 센서 측정 전에 필요한 **재질 작성과 바인딩**을 연습합니다.

| 상자와 재질 | 기본 재료 `base` | 코팅 `coating` | 공통 추가 속성 |
|---|---|---|---|
| `Box0` → `Material0` | `aluminum` | `paint` | `emissive` |
| `Box1` → `Material1` | `steel` | `clearcoat` | `emissive` |
| `Box2` → `Material2` | `concrete` | `paint` | `emissive` |

세 상자의 RGB 색은 모두 `(0.3, 0.6, 0.8)`입니다. 위치는 Y 방향으로 2 m씩 떨어져 있어 서로 비교하기 쉽습니다. `emissive`는 여기서 센서용 속성 이름이며 RGB 화면에서 세 상자가 밝게 빛나게 하는 지시로 읽지 않습니다.

## 1. 재질을 작성한 장면 열기

Isaac Sim 5.1.0과 RTX를 지원하는 NVIDIA GPU 환경에서 실행하세요. 다음 명령은 저장소 루트 기준입니다.

```bash
~/isaacsim/python.sh src/74_sensors_sensors_rtx_materials/run.py
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 처음 240단계 뒤 재질 파일을 저장하고 GUI는 계속 열어 둡니다. 터미널의 `Output:` 경로가 나타나면 저장이 끝난 것입니다. 관찰을 마친 뒤 창을 닫으세요.

파일 생성만 유한하게 실행하려면 `--headless --steps 240`을 추가합니다. 출력은 이 폴더의 `output/날짜_시간/`에 생깁니다. 직접 `--output`을 지정할 때는 존재하지 않는 새 폴더를 사용합니다.

### 실행 결과 확인하기

Stage에서 `/World/Box0`부터 `Box2`까지 선택해 보세요. 세 상자는 `VisualCuboid`로 만들었으므로 높이 1 m에 그대로 남습니다. 이 장면은 떨어지는 강체나 센서 점군을 만들지 않습니다.

저장 파일은 다음 두 개입니다.

- `materials.usda`: 상자, 가시 재질, 비가시 속성과 바인딩을 담은 장면
- `material_attributes.json`: 재료 조합과 실제 작성된 속성을 읽어 기록한 보고서

JSON의 `base`와 `coating`만 보지 말고 `authored_attributes`도 확인하세요. 앞의 두 값은 코드가 의도한 조합이고, 뒤의 값은 Material prim에서 실제로 읽은 속성입니다.

## 2. 재질 속성과 연결을 따라가기

### 코드에서 볼 부분

`run.py`의 반복문은 상자마다 별도의 `OmniPBR` 재질을 만든 뒤 두 번의 적용을 수행합니다.

```python
apply_nonvisual_material(mat.prim, base, coating, behavior)
cube.apply_visual_material(mat)
```

첫 줄은 **Material prim에 센서용 속성을 작성**합니다. 두 번째 줄은 **상자가 그 재질을 사용하도록 연결**합니다. 재질 파일에 값이 있어도 geometry가 그 재질에 연결되지 않았다면, 의도한 상자에 적용된 것을 확인한 셈이 아닙니다. 이 연결을 material binding이라고 부릅니다.

Stage에서 `/World/Looks/Material0`을 선택해 다음 속성을 찾아보세요.

| USD 속성 | 첫 번째 재질의 값 | 역할 |
|---|---|---|
| `omni:simready:nonvisual:base` | `aluminum` | 기본 재료 |
| `omni:simready:nonvisual:coating` | `paint` | 표면 코팅 |
| `omni:simready:nonvisual:attributes` | `emissive` | 센서용 추가 특성 |

이 API는 세 속성을 USD의 `String` 타입으로 작성합니다. JSON에도 속성값이 문자열로 변환되어 저장되지만, JSON만으로 USD 속성 타입까지 확인할 수는 없습니다. 타입과 실제 바인딩은 `materials.usda` 또는 Property에서 함께 살펴보세요.

### 실행 결과 확인하기

뷰포트의 **RTX - Real-Time > Debug View > Non-Visual Material ID**를 선택합니다. RGB 화면에서 비슷했던 세 상자가 센서 재질 ID 표시에서도 어떻게 나타나는지 비교하세요.

이 화면의 색은 재질 조합을 구분하기 위한 **ID 표시색**입니다. 빨간색이 파란색보다 강한 반사를 뜻하는 식으로 읽지 않습니다. 또한 물체마다 부여하는 object ID나 의미 분류용 class ID와도 다른 값입니다. 화면이 예상과 다르면 먼저 각 상자의 재질 연결과 세 비가시 속성이 맞는지 확인하세요.

## 3. 외형·재질·측정의 관계 정리

```text
상자 geometry ── material binding ── Material prim
                                     ├─ OmniPBR 색 → RGB 화면
                                     └─ 비가시 속성 조합 → 센서 재질 ID
```

이번 결과는 “재질이 작성되고 연결되었다”를 확인하는 자료입니다. `materials.usda`와 ID 화면만으로 Lidar 반사 강도나 Radar 반사율을 수치로 측정한 것은 아닙니다. 그런 비교에서는 동일한 센서와 입사 조건을 두고 실제 반환값을 수집해야 합니다.

이 구분을 익히면 색을 바꿨는데 센서 재질 ID가 같거나, 색이 같은데 센서 재질 ID가 다른 상황도 자연스럽게 이해할 수 있습니다.

## 4. 간단한 확인 실험

`run.py`의 `materials` 목록에서 **두 번째 조합의 코팅만** `clearcoat`에서 `paint`로 바꿔 실행해 보세요.

```python
('steel', 'paint', 'emissive')
```

상자 색, 위치와 다른 재료 조합은 유지합니다. 새 출력의 `Material1`에 해당하는 `authored_attributes`가 바뀌었는지 확인하고, GUI의 비가시 재질 ID를 비교하세요. 예상하는 직접적인 변화는 코팅 속성입니다. ID 표시의 변화 여부는 렌더러 결과로 관찰합니다.

GUI에서만 속성을 편집하면 최초에 저장한 JSON은 다시 기록되지 않습니다. 비교 결과를 파일로 남기려면 코드를 바꾸어 새로 실행하거나 수정한 Stage를 별도 이름으로 저장하세요.

## 실행할 때 막히면

- **상자가 떨어지지 않음**: `VisualCuboid`를 사용하는 이 실습의 정상 동작입니다. 물리 접촉 실험과 구분하세요.
- **재질 ID가 예상과 다름**: `Box1`이 실제로 `Material1`을 사용하는지 먼저 보고, 그 Material의 속성값을 확인하세요.
- **속성 이름을 직접 추가했는데 반영되지 않음**: 렌더러는 정해진 이름과 타입을 읽습니다. 임의로 비슷한 이름을 만들기보다 제공 API가 작성한 속성을 기준으로 비교하세요.
- **센서 출력 파일이 없음**: 이 코드는 센서와 annotator를 생성하지 않습니다. 확인할 파일은 `materials.usda`와 `material_attributes.json`입니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [RTX Sensor Non-Visual Materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html)에 대응합니다. 공식 USD 속성 작성 방식을 같은 색의 세 상자에 적용한 실습이며, 예전 CSV 이름 매핑이나 설치 내부 재질 데이터의 수정은 다루지 않습니다.

문서 개정에서는 코드와 5.1 재질 API를 대조했습니다. GPU 렌더링과 ID debug view는 이번에 실행하지 않았고, `tutorial.json`의 상태는 `not_run`입니다.
