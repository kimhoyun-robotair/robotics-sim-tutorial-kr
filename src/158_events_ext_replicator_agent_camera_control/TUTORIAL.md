# 158. 카메라를 어디에 놓고 누구를 바라보게 할까요?

## 이번에 배우는 것

**배우를 바라보는 카메라의 배치 범위를 설정하고, 설정값·실제 월드 좌표·촬영 영상을 비교합니다.**

사람이 장면에 있어도 카메라가 천장이나 빈 통로를 보면 유용한 영상이 나오지 않습니다. 이번에는 사람을 기준으로 카메라 위치와 시선을 정합니다. 카메라의 위치를 바꾸는 설정과 렌즈 값을 바꾸는 설정도 구별합니다.

| 파일 | 하는 일 | 확인할 결과 |
|---|---|---|
| `prepare.py`, `lesson.json` | 사람 두 명·카메라 한 대의 IRA 설정 생성 | `config.yaml` |
| `camera_settings.json` | 배치 높이·거리·시선·렌즈 범위 지정 | 적용할 입력값 |
| `apply_camera_settings.py` | 열린 앱에 카메라 설정 적용 | 적용된 설정값 출력 |
| `inspect_cameras.py` | Setup 후 실제 카메라 조사 | 월드 위치, focalLength, 시선 방향 |

설정 적용 함수는 카메라를 직접 만들지 않습니다. **설정을 적용한 뒤 Setup해야** 새 배치에 반영됩니다.

## 1. 카메라 설정을 적용하고 장면 만들기

Isaac Sim 5.1, RTX GPU, 5.1 창고·사람 자산이 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
python3 src/158_events_ext_replicator_agent_camera_control/prepare.py --output src/158_events_ext_replicator_agent_camera_control/output/camera_01 --frames 90
~/isaacsim/isaac-sim.sh
```

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화하고 필요한 재시작을 마칩니다.
2. **Tools > Action and Event Data Generation > Actor SDG**에서 생성한 `output/camera_01/config.yaml`을 불러옵니다.
3. Scene의 창고에 NavMesh가 없으면 창고를 열어 **Create > Navigation > NavMesh Include Volume**으로 바닥을 덮고 **Window > Navigation > NavMesh**에서 Bake합니다. 새 USD로 저장하고 **Scene > Asset Path**를 그 복사본으로 지정합니다.
4. **Set Up Simulation을 누르기 전에** Script Editor를 열고 아래 두 줄을 실행합니다. 두 경로는 현재 저장소의 실제 절대 경로로 바꾸세요.

```python
exec(open('/절대경로/저장소/src/158_events_ext_replicator_agent_camera_control/apply_camera_settings.py').read())
apply_camera_settings('/절대경로/저장소/src/158_events_ext_replicator_agent_camera_control/camera_settings.json')
```

5. **Set Up Simulation**을 누르고 사람·카메라 로딩을 기다립니다. Character 명령의 이름을 실제 actor 이름과 맞추고 **Save Commands**합니다.
6. 카메라 뷰에서 사람이 보이는지 확인한 뒤 설정을 저장하고 **Start Data Generation**을 실행합니다. 90프레임 생성 후 GUI는 남습니다.

### 설정에서 볼 부분

`camera_settings.json`에는 다음 범위가 들어 있습니다.

| 설정 | 기본값 | 의미 |
|---|---|---|
| `aim_camera_to_character` | `true` | 사람을 기준으로 배치합니다. |
| `character_focus_height` | `0.7` | 사람 발 위치보다 0.7 m 높은 지점을 봅니다. |
| `min/max_camera_height` | `2.0 / 3.0` | 카메라 높이 범위(m)입니다. |
| `min/max_camera_distance` | `6.5 / 14.0` | 사람 기준 배치 거리 범위(m)입니다. |
| `min/max_camera_look_down_angle` | `0.0 / 60.0` | 내려다보는 각도 범위(도)입니다. |
| `min/max_camera_focallength` | `13.0 / 23.0` | 렌즈의 focalLength 속성 범위입니다. |

거리와 focalLength는 다른 값입니다. 13~23을 배우까지의 거리(m)로 읽지 마세요. 렌즈 속성은 USD 카메라 단위 규칙을 따릅니다.

## 2. 설정값이 실제 카메라에 반영됐는지 확인하기

### 코드에서 볼 부분

적용 함수는 먼저 범위의 모순을 검사한 뒤 설정을 씁니다.

```python
prefix = "/persistent/exts/isaacsim.replicator.agent/"
settings = carb.settings.get_settings()
settings.set(prefix + name, value)
```

최소값이 최대값보다 크면 거부합니다. 카메라 최소 높이는 초점 높이보다 높아야 하고, 최대 높이는 최대 거리보다 작아야 합니다. 이 검사는 숫자의 관계를 확인할 뿐 창고 안에 유효한 공간이 있는지까지 판정하지는 않습니다.

Setup 후 **Window > Script Editor**에서 `inspect_cameras.py` 전체를 실행하세요. 핵심은 다음 부분입니다.

```python
transform = cache.GetLocalToWorldTransform(prim)
transform.ExtractTranslation()
transform.TransformDir((0, 0, -1))
```

`GetLocalToWorldTransform()`은 카메라의 부모 Xform까지 합친 변환을 구합니다. 카메라 자신의 Translate만 보면 부모의 이동·회전을 놓칠 수 있습니다. USD 카메라가 보는 로컬 방향은 -Z이므로 `(0, 0, -1)`을 월드 방향으로 바꿔 출력합니다.

### 실행 결과 확인하기

출력에서 `/World/Cameras/` 아래 카메라마다 세 값을 확인합니다.

- `world position`: 유효한 배우 지향 배치가 이루어졌다면 Z가 설정한 2~3 m 범위인지 봅니다.
- `focalLength`: 렌즈 무작위화가 켜져 있을 때 13~23 범위인지 봅니다.
- `view direction`: 시선 벡터입니다. 이 값만 보고 배우가 보인다고 판정하지 말고 실제 카메라 뷰도 확인하세요.

검사 스크립트는 카메라와 배우 사이의 거리나 시선 일치를 자동 판정하지 않습니다. `output/camera_01/capture`의 RGB와 카메라 파라미터까지 대조해야 촬영 조건을 확인할 수 있습니다.

유효한 배우 지향 위치를 찾지 못하면 원점을 향하는 기본 배치가 사용될 수 있습니다. NavMesh 자체가 없으면 카메라 배치 단계가 실패할 수도 있으므로 먼저 Bake 여부를 확인하세요. 이런 결과를 정상적인 배우 지향 무작위 표본으로 세지 마세요.

`aim_camera_to_character`와 `randomize_camera_info`도 별개입니다. 전자는 배우 중심 배치를, 후자는 렌즈 정보 무작위화를 제어합니다. 미리 배치한 카메라를 사용하려면 Setup한 장면에서 카메라를 원하는 위치로 옮겨 새 USD로 저장합니다. 새 출력 설정의 `scene.asset_path`에 그 USD를 지정하고 `sensor.camera_num`을 제거한 뒤 다음처럼 실제 카메라 경로를 넣으세요.

```json
{"camera_list": ["/World/Cameras/Camera"]}
```

이 객체는 `sensor` 항목의 내용이며 경로는 Stage의 실제 이름으로 바꿉니다. 새 설정을 불러와 Setup한 뒤 inspector와 RGB를 비교하세요. `camera_num`과 `camera_list`를 동시에 두지 않습니다.

## 3. 입력 범위와 실제 관찰값 정리

```text
JSON의 배치 범위
    → 앱의 persistent 설정
    → Setup에서 유효한 위치 선택
    → USD 카메라의 월드 위치·시선
    → RGB와 카메라 파라미터
```

설정 출력은 “앱이 어떤 값을 받았는가”를 보여 주고, inspector는 “어떤 카메라가 만들어졌는가”를 보여 줍니다. RGB는 그 카메라가 실제로 본 결과입니다. 이 세 단계를 함께 읽어야 값은 적용됐지만 이전 카메라가 재사용된 경우도 구별할 수 있습니다.

## 4. 간단한 확인 실험

카메라 **높이 조건만** 고정해 보세요. `camera_settings.json`의 복사본에서 `min_camera_height`, `max_camera_height`를 모두 `2.5`로 바꾸고 다른 값은 유지합니다.

1. 복사본을 적용하고 **File > New**로 새 Stage를 만듭니다.
2. 새 출력 설정을 불러와 같은 Scene으로 다시 Setup합니다.
3. inspector의 실제 Z가 약 2.5 m로 고정되는지 비교하세요. 렌즈 값과 수평 배치는 여전히 달라질 수 있습니다.

기존 Stage에 카메라가 충분히 있으면 IRA가 이를 재사용할 수 있으므로 새 Stage가 필요합니다. 설정은 persistent 영역에 남으니 실험 후 원본 JSON을 다시 적용하세요.

## 실행할 때 막히면

- **`unknown settings` 오류**: IRA 확장을 먼저 활성화하세요. 함수는 존재하지 않는 설정 키에 조용히 값을 쓰지 않습니다.
- **높이 변경이 보이지 않음**: 기존 카메라를 조사한 것은 아닌지 확인하고 새 Stage에서 Setup하세요.
- **카메라가 원점만 봄**: NavMesh와 사람 배치를 확인한 뒤 거리·높이·각도 조건을 만족할 공간이 있는지 봅니다.
- **검사 출력이 비어 있음**: Setup 완료 여부와 실제 카메라 경로를 확인하세요. 검사 대상은 `/World/Cameras/` 아래의 Camera Prim입니다.
- **이미지에 사람이 없음**: viewport의 Perspective가 아니라 writer가 사용하는 카메라 뷰를 선택해 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Camera Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/camera_control.html)에 대응합니다. 로컬 도구는 설정값 적용과 USD 카메라 관찰을 연결합니다. 실제 카메라 생성과 촬영은 IRA 확장이 수행합니다.

`tutorial.json`은 `not_run`입니다. 범위 검사나 설정값 출력이 실제 카메라 배치·렌더링 검증을 대신하지 않습니다.
