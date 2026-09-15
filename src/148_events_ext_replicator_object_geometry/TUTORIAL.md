# 148. 도형의 모양과 물리 역할을 따로 정하기

## 이번에 배우는 것

**정적 충돌체와 동적 강체를 비교하고, 기본 도형·USD 메시·변형 병이 각각 어떻게 만들어지는지 살펴봅니다.**

화면에 큐브가 있다는 사실만으로 그 큐브가 떨어지거나 다른 물체를 받치지는 않습니다. `subtype`은 모양을 고르고 `physics`는 물리 계산에 참여하는 방식을 고릅니다. 이번에는 두 설정을 분리해 읽는 연습을 합니다.

| 설정 파일 | 주요 대상 | 관찰할 변화 |
|---|---|---|
| `scene.yaml` | 빨간 구, 정적 녹색 큐브, 떨어지는 파란 큐브 | 낙하와 정적 받침의 차이 |
| `mesh.yaml` | `models/box.usda`의 메시 | USD 참조와 축별 배율 |
| `bottle.yaml` | 확장에 포함된 병 모델 | effector 값에 따른 형상 변경 |

모든 위치는 **cm**, 위쪽은 **Y축**입니다. 기본 큐브 한 변이 100 cm라는 기준을 기억하면 중심 높이와 받침 높이를 계산할 수 있습니다.

## 1. 고정된 받침과 떨어지는 물체 비교하기

Isaac Sim 5.1, `isaacsim.replicator.object` 확장과 RTX GPU 환경에서 실행하세요. 아래는 저장소 루트 기준입니다.

```bash
cd src/148_events_ext_replicator_object_geometry
~/isaacsim/python.sh run.py --launch --frames 3
```

콘솔에 나온 `configuration:` 경로를 **Tools > Action and Event Data Generation > Object SDG > Description File**에 넣습니다. **Initialize scene randomization**으로 처음 배치를 보고, **Simulate**로 물리를 진행한 뒤 결과를 저장하세요. 초기화는 stage를 바꾸므로 편집 중인 장면을 먼저 저장합니다.

`run.py`만 호출하면 `output/<UTC시간>-<고유값>/prepared.yaml` 준비에서 끝납니다. `--launch`가 실제 앱을 열며 GUI는 생성 후에도 남습니다. 창 없이 세 장을 생성하고 종료하려면 `--launch --headless --frames 3`을 사용하세요. 설치 위치가 다르면 Python 경로와 `--isaac-root /설치/경로`도 바꿉니다.

### 설정에서 볼 부분

```yaml
static_cube:
  type: geometry
  subtype: cube
  tracked: true
  color: [0.2, 0.7, 0.3]
  transform_operators:
  - translate: [100, 50, 0]
  - scale: [1, 1, 1]
  physics: collision
```

녹색 큐브는 한 변 100 cm, 중심 Y가 50 cm이므로 밑면은 바닥 Y=0, 윗면은 Y=100에 있습니다. `physics: collision`은 부딪힐 표면을 제공하지만 동적 강체를 만들지 않습니다. 중력을 켜도 받침 자체는 떨어지지 않습니다.

파란 `falling_cube`는 중심 `(100,210,0)`, 한 변 60 cm이며 `physics: rigidbody`입니다. 녹색 받침과 X·Z가 같으므로 아래로 내려오면서 받침 위에 닿습니다. 빨간 구 `subject`도 rigidbody이지만 X=-130 cm에 있어 바닥 쪽으로 떨어집니다.

전역 중력은 981 cm/s²이고 물리 시간은 1초입니다. **충돌체인지와 라벨 대상인지는 서로 독립적**입니다. `tracked: true`를 지정해도 물리가 생기지 않으며, `collision`이라고 자동으로 정답 대상이 되는 것도 아닙니다.

### 실행 결과 확인하기

초기화 때의 공중 배치와 `Simulate` 후 `images/`의 640×480 RGB를 비교하세요. 녹색 큐브 위치는 유지되고, 빨간 구와 파란 큐브는 내려오는 것이 관찰 기준입니다. 접촉이 일어났다고 완전히 정착했다고 단정하지 마세요.

`descriptions/`는 촬영 시점의 `global_transform`을 저장합니다. 행렬 마지막 행의 X·Y·Z를 보면 최종 중심 위치를 확인할 수 있습니다. 물리 이전의 `translate`·`scale` 연산은 `prepared.yaml`에서 확인하세요. IRO는 저장할 때 이를 최종 행렬로 합칩니다.

## 2. USD 메시와 변형 병 실행하기

앞의 실행을 종료하고 같은 폴더에서 메시 설정을 선택합니다.

```bash
~/isaacsim/python.sh run.py --config mesh.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

```yaml
subject:
  type: geometry
  subtype: mesh
  usd_path: '@PACKAGE@/models/box.usda'
  tracked: true
  transform_operators:
  - translate: [0, 50, 0]
  - scale: [1, 1.5, 0.7]
```

`usd_path`는 기존 USD의 형상과 재질을 **참조**합니다. 파일을 Python 모듈처럼 import하는 명령은 아닙니다. `models/box.usda`의 점 좌표는 각 축 -50~50이므로 배율을 적용한 크기는 X 100, Y 150, Z 70 cm입니다.

중심 높이가 50인데 세로 길이는 150이므로 밑부분은 Y=-25까지 내려갑니다. 이 설정은 메시 물리를 지정하지 않았고 물리 시간도 0입니다. 따라서 바닥과 겹친 부분을 자동으로 밀어 올리지 않습니다. 형상과 배치를 직접 설정한 결과를 관찰하는 예입니다.

병은 별도 설정으로 실행하세요.

```bash
~/isaacsim/python.sh run.py --config bottle.yaml --launch --frames 3
```

새 `configuration:` 경로를 Object SDG에 넣고 초기화·무작위화를 반복합니다. `base_effector`는 0.2~0.7, `neck_effector`·`horizontal_effector`·`vertical_effector`는 0.2~0.8 범위를 사용합니다. 이 값들은 병 모델의 변형 제어값입니다. cm나 배율로 곧바로 읽지 말고, 목·몸통·바닥 형상이 어떻게 바뀌는지 연결해 보세요.

### 실행 결과 확인하기

메시는 RGB와 `models/box.usda` 안의 Mesh 점 좌표·Material 연결을 비교합니다. 병은 `descriptions/`에 남는 네 effector 값과 저장 RGB의 외곽을 비교하세요. 두 비교 설정에는 rigidbody가 없으므로 낙하를 확인 기준으로 삼지 않습니다. 병 표면의 체크무늬는 로컬 `checker.png`를 사용하지만 병 형상 자체는 IRO 확장의 자원입니다.

병에는 별도의 지원 제한도 있습니다. 공식 5.1 문서는 변형된 병 형상의 충돌 검사가 지원되지 않아 **병의 물리 시뮬레이션을 지원하지 않는다**고 명시합니다. 기본 도형에 적용한 `physics: rigidbody`를 병에 그대로 추가해 낙하 실험으로 확장하지 마세요. 이 변형은 네 제어값과 시각적 외곽의 관계를 배우는 데 사용합니다.

## 3. 형상과 물리 설정의 관계 정리

| 질문 | 확인할 설정 |
|---|---|
| 어떤 모양을 만들까요? | `subtype: sphere / cube / mesh / bottle` |
| 기존 모델을 어디서 가져올까요? | 메시의 `usd_path` |
| 움직임 없이 부딪힐 표면만 필요할까요? | `physics: collision` |
| 중력과 충돌에 따라 움직여야 할까요? | `physics: rigidbody` |
| 정답을 수집해야 할까요? | `tracked` |

메시를 크게 만드는 것, 병의 형상을 바꾸는 것, 물체가 물리로 이동하는 것은 서로 다른 변화입니다. 화면을 비교할 때 외곽 형태와 중심 위치를 따로 읽어 보세요.

## 4. 간단한 확인 실험

`scene.yaml`을 `fixed_sphere.yaml`로 복사하고 **빨간 구 `subject`의 `physics`만 `rigidbody`에서 `collision`으로** 바꿉니다.

```bash
~/isaacsim/python.sh run.py --config fixed_sphere.yaml --launch --headless --frames 3
```

중력과 물리 시간은 같아도 빨간 구는 초기 높이 180 cm에 남아야 합니다. 파란 큐브는 계속 떨어집니다. 두 물체의 최종 Y 위치를 비교하면 장면에 중력이 있다는 것과 개별 물체가 동적이라는 것이 별개임을 확인할 수 있습니다.

## 실행할 때 막히면

- **녹색 큐브가 떨어지지 않음**: 정적 `collision` 설정의 정상 동작입니다. 낙하 대상은 두 rigidbody입니다.
- **메시가 바닥에 묻힘**: 세로 배율 1.5와 중심 높이 50 cm를 계산해 보세요. 이 설정에는 겹침을 해소할 물리가 없습니다.
- **`box.usda`를 찾지 못함**: `models/`를 포함해 폴더 전체를 유지하고 `prepared.yaml`의 절대 `usd_path`를 확인하세요.
- **병 모델을 불러오지 못함**: `isaacsim.replicator.object` 확장과 포함 자원 로딩 오류를 확인하세요. 체크무늬 파일만으로 병 형상이 만들어지지는 않습니다.
- **세 프레임이 모두 정착 상태여야 하는지 궁금함**: 각 프레임은 1초 후 촬영합니다. 완전 정지 여부는 추가 관찰이 필요한 별도 조건입니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Geometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/geometry.html)에 대응합니다. 기본 도형 물리, 로컬 USD 참조, 병의 형상 제어를 독립 설정으로 나누었습니다. 병에는 물리를 부여하지 않습니다.

치수와 확인 기준은 로컬 YAML·USD 및 IRO 물리 설정 코드를 근거로 설명했습니다. 실제 접촉·병 렌더링 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
