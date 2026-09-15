# 153. 매크로로 장면 값 사이의 관계 표현하기

## 이번에 배우는 것

**전역 값·개체 번호·다른 객체의 난수를 참조해 세 큐브와 두 조명의 값을 연결합니다.**

큐브 간격을 바꿀 때 세 좌표를 각각 고치는 대신 간격 하나를 참조하게 만들 수 있습니다. 다른 조명의 세기에 일정 범위를 더하는 관계도 표현할 수 있습니다. IRO의 **매크로**는 이렇게 설정 속 값을 찾아 계산에 사용하는 `$[...]` 문법입니다.

| 이 실습의 참조 | 의미 | 연결되는 결과 |
|---|---|---|
| `$[/spacing]` | 설정 루트의 간격 | 세 큐브의 X 위치 |
| `$[../own_height]` | 부모 mutable의 자체 높이 값 | 해당 큐브의 Y 위치 |
| `$[/palette~$[index]]` | 번호에 해당하는 팔레트 항목 | 큐브 색 전체 |
| `$[seed]` | 현재 프레임 seed | 큐브의 회전 순서 |
| `$[/key_light/intensity]` | 다른 조명의 해석된 세기 | dome 세기의 범위 |

## 1. 매크로가 있는 설정 실행하기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트부터 실행합니다.

```bash
cd src/153_events_ext_replicator_object_macro
~/isaacsim/python.sh run.py --frames 3
```

이번 호출은 `output/<UTC시간>-<고유값>/prepared.yaml`을 만들고 종료합니다. 파일을 열면 `$[...]` 식이 그대로 남아 있습니다. `run.py`는 `@OUTPUT@` 같은 경로 표식을 바꾸는 준비 도구이며, IRO 매크로 계산은 아직 수행하지 않았습니다.

실제 계산과 촬영은 다음 호출로 진행하세요.

```bash
~/isaacsim/python.sh run.py --launch --headless --frames 3
```

이번 호출은 새로운 출력 폴더를 사용합니다. 콘솔의 최신 `output:` 경로를 기록하고 생성이 끝날 때까지 기다리세요. 설치 경로가 다르면 Python 경로와 `--isaac-root /설치/경로`를 함께 바꿉니다. `--steps`는 앱 업데이트 제한이므로 이 실습에서는 생략합니다.

### 설정에서 볼 부분

`subject`에서 높이와 이동 관계를 찾아보세요.

```yaml
count: 3
own_height: 40 + $[index] * 20
transform_operators:
- translate:
  - ($[../index] - 1) * $[/spacing]
  - $[../own_height]
  - 0
- rotateY: ($[../index] + $[seed]) % $[../count] * 45
- scale: [0.6, 0.6, 0.6]
```

개체 번호 0·1·2를 식에 대입하면 `own_height`는 40·60·80입니다. 이것은 큐브의 세로 길이가 아니라 **중심의 Y 위치**입니다. IRO는 Y-up·cm 단위를 사용하며 모든 큐브의 한 변은 60 cm입니다.

`spacing: 130`일 때 중심은 `(-130,40,0)`, `(0,60,0)`, `(130,80,0)` cm입니다. `/`로 시작하는 참조는 루트에서 찾고, `../`는 현재 속성 문맥의 부모로 올라갑니다. 이동 목록 속 식이 mutable에 정의된 번호와 높이를 쓰는 이유입니다.

### 실행 결과 확인하기

`images/`의 세 큐브와 `descriptions/`의 `own_height`를 비교하세요. 최종 위치는 각 subject의 `global_transform` 마지막 행에서 확인합니다. 저장 description은 원래 `translate`·`rotateY`·`scale`을 하나의 최종 행렬로 정리하므로, 계산 전 식은 `prepared.yaml`에서 읽어야 합니다.

## 2. 리스트 참조와 다른 난수에 의존하는 값 읽기

### 설정에서 볼 부분

```yaml
color: $[/palette~$[index]]
```

안쪽 `$[index]`를 먼저 계산합니다. 예를 들어 번호 1이면 바깥 참조는 팔레트의 `~1` 항목을 선택합니다. 팔레트가 RGB 벡터 세 개의 리스트이므로 **숫자 하나가 아니라 색 벡터 전체**가 color로 전달됩니다. 마찬가지로 카메라의 `$[/camera_parameters]`는 사전 전체를 넘깁니다.

회전 식의 `%`는 나머지 연산입니다. 시작 seed가 11일 때 `(index+11)%3*45`는 다음과 같습니다.

| 개체 번호 | 첫 프레임 회전 | 중심 Y | 팔레트 색 |
|---|---:|---:|---|
| 0 | 90° | 40 cm | `[0.9,0.2,0.1]` |
| 1 | 0° | 60 cm | `[0.1,0.7,0.2]` |
| 2 | 45° | 80 cm | `[0.2,0.3,0.9]` |

이 설정은 중력과 물리 시간이 0이므로 회전 변화는 물리 운동이 아니라 프레임별 배치입니다. 다음 프레임은 seed가 12이므로 회전 순서가 바뀝니다. 다만 큐브는 Y축 90도 회전에 대해 대칭입니다. **0도와 90도가 영상에서 같은 모양으로 보일 수 있으므로 RGB만으로 식을 판정하지 마세요.** 초기화 Stage의 회전이나 최종 변환 행렬을 함께 봅니다.

조명의 참조는 다른 객체의 난수 결과를 사용합니다.

```yaml
dome_light:
  type: light
  subtype: dome
  intensity:
    distribution_type: range
    start: $[/key_light/intensity] + 50
    end: $[/key_light/intensity] + 100
```

`key_light.intensity`는 600~900에서 선택됩니다. 그 값이 720이라면 dome은 770~820 사이에서 선택합니다. dome을 설명한 YAML 줄이 먼저 나와도 key light 값을 먼저 알아야 합니다. **파일의 배치 순서보다 값의 의존 관계가 계산 순서를 정합니다.** 같은 프레임에서 참조한 key light 값은 다시 새로 뽑는 값이 아닙니다.

### 실행 결과 확인하기

같은 `frame_11_GLOBAL.yaml` 안에서 두 light의 세기를 찾아 차이를 계산하세요. `dome - key`가 50~100이면 관계를 만족합니다. 서로 다른 프레임의 값을 섞으면 이 검산이 의미 없어집니다.

카메라 파라미터가 문자열이 아닌 사전으로 풀렸는지, subject 색이 팔레트와 대응하는지도 확인합니다. GUI로 식을 살펴보려면 `--launch`로 실행하고 **Tools > Action and Event Data Generation > Object SDG**에 이번 `configuration:` 경로를 입력해 초기화하세요. **Simulate**가 저장하며, 준비와 미리보기는 별도입니다. 작업 중인 stage는 먼저 저장합니다.

## 3. 경로 치환·매크로·파일명 처리 정리

```text
run.py: @OUTPUT@ → 실제 출력 경로
IRO: $[/spacing], $[index], $[seed] → 장면 값과 계산 결과
writer: $(camera_name) → default_camera 또는 GLOBAL
```

겉모습이 비슷해도 처리 주체가 다릅니다. IRO 매크로에 셸 변수 문법을 섞지 마세요. 제공 파일의 `frame_$[seed]_$(camera_name)`은 seed를 먼저 계산하고 저장할 때 카메라 이름을 붙입니다.

공식 문서의 예약어를 다른 버전에 옮길 때도 구분이 필요합니다. 설치 IRO 0.4.13은 전역 매크로로 `seed`와 `num_frames`를 등록하지만, 공식 페이지에 등장하는 `$[frame]`·`$[camera]`는 예약 전역값으로 등록하지 않습니다. 이 파일명에서는 프레임을 구별할 때 `$[seed]`, 카메라를 구별할 때 writer의 `$(camera_name)`을 유지하세요. 특히 `$(camera_name)`을 `$[camera]`로 바꾸면 처리 주체까지 달라집니다.

또한 참조 관계에는 끝나는 지점이 있어야 합니다. `spacing`이 자기 자신을 참조하면 숫자를 결정할 수 없습니다. 이런 순환은 난수 범위가 좁거나 넓은 문제와 달리 해석 오류입니다.

## 4. 간단한 확인 실험

`scene.yaml`을 `wide_spacing.yaml`로 복사하고 **`spacing`만 130에서 180으로** 바꿉니다.

```bash
~/isaacsim/python.sh run.py --config wide_spacing.yaml --launch --headless --frames 3
```

중심 X는 -180·0·180 cm로 넓어지고 Y는 40·60·80 cm를 유지합니다. 같은 seed의 색과 회전 규칙도 같습니다. 가운데 큐브가 움직이지 않는 이유는 `(index-1)`이 0이기 때문입니다. 세 좌표를 따로 고치지 않고 관계 하나로 배치를 바꿨다는 점을 확인하세요.

## 실행할 때 막히면

- **`not found reference` 오류**: 루트 참조의 `/`, 부모 참조의 `../`, 리스트 인덱스의 `~` 위치를 확인하세요.
- **`cyclic reference` 오류**: 참조를 따라가다가 같은 속성으로 돌아오는지 살펴봅니다. 순환하는 참조를 독립 값이나 순환하지 않는 식으로 바꾸세요.
- **0도와 90도 큐브를 영상에서 구별하기 어려움**: 큐브의 대칭 때문일 수 있습니다. 최종 변환 행렬이나 초기화 Stage의 회전을 확인하세요.
- **dome과 key의 차이가 범위를 벗어남**: 같은 seed의 같은 description에서 두 값을 읽었는지 먼저 확인하세요.
- **준비 파일의 매크로가 안 풀림**: 준비 단계에서는 정상입니다. 실제 생성 후 `descriptions/`를 확인합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Macro](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/macro.html)에 대응합니다. 위치·색·회전·조명에 참조를 연결해 숫자·벡터·사전 전달과 계산 순서를 비교합니다. 파일명은 설치 IRO 0.4.13 writer가 지원하는 `$(camera_name)`을 사용합니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)에는 기본 설정 한 프레임의 이미지 1장·주석 4개 생성 기록이 있습니다. 설정 파일은 기록 당시와 같지만 현재 `run.py`는 그 뒤 변경되었습니다. 따라서 이 기록은 당시 조건에 한정되며 현재 실행 파일, 모든 식 변경과 GUI 조작까지 확인한 것은 아닙니다. 검증 범위는 `tutorial.json`을 함께 참고하세요.
