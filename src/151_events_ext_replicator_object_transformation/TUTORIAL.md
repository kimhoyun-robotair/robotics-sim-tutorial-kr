# 151. 회전 뒤의 이동은 왜 물체 주위를 돌게 만들까요?

## 이번에 배우는 것

**변환 순서로 카메라의 궤도와 큐브의 곡면 배치를 만들고, 이동과 회전의 순서를 바꿨을 때 결과를 예상합니다.**

카메라를 뒤로 물린 다음 회전시키는 구성은 관측 중심 주위의 여러 시점을 만들 수 있습니다. 반대로 같은 이동을 더 바깥쪽 변환으로 두면 위치는 고정되고 자세만 바뀔 수 있습니다. IRO의 `transform_operators`는 이런 관계를 순서 있는 목록으로 표현합니다.

| 설정 | 고정하는 것 | 무작위로 바꾸는 것 |
|---|---|---|
| `scene.yaml` | 직육면체, 관측 중심, 카메라 거리 700 cm | 카메라의 Y 회전 |
| `shell.yaml` | 큐브 중심 반지름 220 cm, 개체 크기 | 두 배치 각도와 각 큐브의 자세 |

두 설정 모두 중력과 물리 시간이 0입니다. 프레임마다 다른 배치를 만드는 실습이며 시간에 따라 연속으로 도는 애니메이션은 아닙니다.

## 1. 직육면체를 여러 시점에서 보기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트부터 실행하세요.

```bash
cd src/151_events_ext_replicator_object_transformation
~/isaacsim/python.sh run.py --launch --frames 3
```

**Tools > Action and Event Data Generation > Object SDG**에서 콘솔의 `configuration:` 경로를 **Description File**에 입력하고 초기화합니다. 작업 중인 stage는 먼저 저장하세요. **Randomize scene**으로 시점을 바꾸고 **Simulate**로 결과를 저장합니다.

`run.py`는 매 호출 새 `output/<UTC시간>-<고유값>/prepared.yaml`을 준비합니다. `--launch`가 없는 호출은 여기서 끝나며, 실제 데이터 생성은 IRO가 수행합니다. GUI는 생성 후에도 열려 있습니다. 자동 생성·종료는 `--launch --headless --frames 3`을 사용하세요. 설치 위치를 바꾸면 `--isaac-root`도 맞춥니다.

### 설정에서 볼 부분

```yaml
transform_operators:
- translate_global: [0, 50, 0]
- rotateY:
    distribution_type: range
    start: -60
    end: 60
- rotateX: -20
- translate_local: [0, 0, 700]
```

목록의 위쪽은 바깥 기준, 아래쪽은 그 안의 로컬 변환으로 읽으면 이해하기 쉽습니다. 관측 중심 `(0,50,0)`에 기준을 놓고, Y 회전과 X 기울기를 적용한 축을 따라 +Z로 700 cm 물러납니다. 카메라는 로컬 -Z를 보므로 이 배치는 다시 관측 중심 쪽을 향합니다.

`translate_global`과 `translate_local`의 접미사는 두 이동 연산에 서로 다른 이름을 붙입니다. **`global`이라는 글자 자체가 좌표계를 강제로 정하는 것은 아닙니다.** 설치 IRO는 이름의 `_`를 USD 연산 접미사 구분자 `:`로 바꾸며, 실제 합성 관계는 목록 순서로 정합니다.

### 실행 결과 확인하기

프레임마다 빨간 직육면체에서 보이는 옆면이 달라지는지 살펴보세요. 직육면체는 배율 `[1,1.7,0.5]`라 축별 길이가 다르므로 시점 차이를 알아보기 쉽습니다. 카메라 Y 회전 범위는 -60~60도이고 X 기울기는 -20도로 유지됩니다.

Stage에서 카메라의 `xformOpOrder`를 확인하면 두 이동과 두 회전의 합성 순서를 볼 수 있습니다. 설치 IRO가 기본 이동·회전·배율 연산도 추가하므로 목록의 모든 줄이 YAML과 일대일로 같지는 않습니다. 먼저 `translate:global`, `rotateY`, `rotateX`, `translate:local`에 대응하는 연산을 찾아보세요.

저장된 description에서는 원래 연산이 단일 최종 행렬로 바뀝니다. 따라서 순서는 **초기화한 Stage와 `prepared.yaml`**, 촬영 시 위치는 **description의 `global_transform`**에서 확인하세요.

## 2. 같은 원리로 큐브를 곡면에 배치하기

앞의 GUI를 닫은 뒤 비교 설정을 실행합니다.

```bash
~/isaacsim/python.sh run.py --config shell.yaml --launch --headless --frames 3
```

### 설정에서 볼 부분

`subject`의 첫 세 연산입니다.

```yaml
- rotateY:
    distribution_type: range
    start: -70
    end: 70
- rotateX:
    distribution_type: range
    start: -30
    end: 30
- translate: [0, 0, 220]
```

두 회전이 정한 방향으로 220 cm 이동하므로 중심은 직육면체 공간 전체가 아니라 **반지름 220 cm인 구면 일부**에 놓입니다. `count: 60`으로 이 배치를 60개 만듭니다.

뒤에는 개체별 `rotateXYZ`와 `scale: [0.15,0.15,0.15]`가 있습니다. 이 회전은 각 큐브의 자세를 바꾸고 배율은 한 변을 15 cm로 만듭니다. 두 연산이 이동보다 안쪽에 있으므로 이미 정한 큐브 중심 반지름을 바꾸지 않습니다.

### 실행 결과 확인하기

`images/`에서는 작은 큐브 무리가 곡면을 따라 놓이는지 확인합니다. IRO는 Y-up·cm 단위입니다. `shell.yaml`에는 바닥이 없지만 일부 큐브가 다른 큐브에 가려질 수 있습니다. 시야 안에서 보이는 개수와 생성된 개수 60을 같다고 요구하지 마세요.

저장 description에서 임의의 subject의 `global_transform` 마지막 행을 읽어 중심 `(x,y,z)`를 얻습니다. 다음 값이 약 220인지 계산해 보세요.

```text
원점에서 중심까지 거리 = sqrt(x² + y² + z²)
```

이 거리는 큐브 표면까지의 거리가 아닙니다. 개별 큐브의 자세가 달라도 중심 반지름이 유지되는지 보는 검사입니다.

## 3. 변환 순서의 효과 정리

```text
회전 → 이동 → 개체 회전 → 배율
방향 선택 → 그 방향으로 중심 배치 → 중심에서 자세 변경 → 크기 변경

이동 → 회전 → 개체 회전 → 배율
중심 위치 고정 → 그 자리에서 방향 변경 → 자세 변경 → 크기 변경
```

이 목록은 Python 코드처럼 물체를 한 번씩 움직이는 명령 이력이 아니라 합성할 좌표 변환의 순서입니다. 위쪽 변환이 아래쪽 변환의 기준을 정하기 때문에 두 연산을 교환하면 월드 위치가 달라집니다.

## 4. 간단한 확인 실험

`shell.yaml`을 `one_center.yaml`로 복사하고 **`translate: [0,0,220]` 항목을 `rotateY`보다 앞쪽으로** 옮기세요. 수치와 개수는 그대로 둡니다.

```bash
~/isaacsim/python.sh run.py --config one_center.yaml --launch --headless --frames 3
```

모든 큐브 중심이 `(0,0,220)`에 모이고 자세만 달라져 겹친 모습이 예상됩니다. RGB만으로는 큐브 수를 셀 수 없으므로 description의 개체별 중심을 확인하세요. 회전이 없어져서 모인 것이 아니라 이동에 적용되던 회전 관계가 달라진 것입니다.

## 실행할 때 막히면

- **카메라가 물체를 바라보지 않음**: 두 이동과 회전의 순서를 확인하세요. 카메라 전방은 -Z이고 마지막 이동은 로컬 +Z 방향입니다.
- **`duplicate op` 오류**: 같은 이름의 이동 두 개를 쓰지 않았는지 확인하세요. 제공 파일처럼 서로 다른 접미사를 사용합니다.
- **description에 `rotateY`가 없음**: 저장 과정에서 최종 행렬로 합쳐집니다. 원래 순서는 준비 YAML 또는 초기화 Stage에서 확인하세요.
- **직육면체가 바닥과 겹침**: 높이 170 cm인 물체의 중심이 50 cm입니다. 물리로 배치를 정리하지 않는 설정의 결과입니다.
- **카메라가 계속 도는 애니메이션이 안 나옴**: 각 프레임에 무작위 시점을 선택합니다. 연속 회전 동작은 이 설정에 없습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Transformation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/transformation.html)에 대응합니다. 카메라 궤도와 큐브 구면 배치를 통해 순서의 의미를 비교합니다. 모든 회전 표현과 행렬 입력을 나열하기보다 실제 사용하는 연산에 집중합니다.

접미사와 연산 순서는 설치 IRO 0.4.13의 `mutable.py`·`utility/xform.py`를 대조했습니다. 실제 장면 검증 상태는 `tutorial.json`의 `not_run`을 참고하세요.
