# 133. Recorder는 언제부터 데이터를 저장할까요?

## 이번에 배우는 것

**움직이는 카메라 장면을 준비한 뒤, Recorder의 설정과 기록 시작을 나누어 이해합니다.**

132번에서는 Python이 직접 촬영을 요청했습니다. 이번에는 Synthetic Data Recorder가 카메라·해상도·저장할 항목을 받아 기록을 진행합니다. 장면이 열렸다는 것과 이미지가 저장되기 시작했다는 것은 다른 상태입니다.

| 방식 또는 파일 | 역할 |
|---|---|
| GUI `run.py` | 장면과 설정 JSON을 준비하고 사용자의 Start를 기다립니다. |
| `--headless` | 같은 확장의 `SyntheticRecorder`로 유한한 자동 기록을 수행합니다. |
| `custom_writer.py` | RGB와 표면 법선을 저장하는 `BeginnerNormalWriter`를 등록합니다. |
| `randomize_camera.py` | Script Editor에서 실행해 무작위 시점의 카메라를 추가합니다. |
| `visualization_params.json` | 검출 결과를 이미지 위에 표시할 때 쓰는 설정 예시입니다. |

장면에는 고정된 `/World/Carton`과 이동하는 `/World/AnimatedCamera`가 있습니다. 상자 대신 카메라가 움직이므로 시간 진행이 사진의 시점에 어떻게 반영되는지 살펴볼 수 있습니다.

## 1. GUI에서 장면을 준비하고 기록하기

Isaac Sim 5.1 전체 설치, RTX GPU, 데스크톱 화면이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/133_replicator_replicator_recorder/run.py --frames 10 --output /tmp/tutorial133-gui
```

`--output`은 아직 없는 폴더로 지정합니다. 터미널에 `Load Writer > Config:`와 설정 파일 경로가 표시되면 다음 순서로 진행하세요.

1. **Tools > Replicator > Synthetic Data Recorder**를 엽니다.
2. **Writer > Config**에서 `/tmp/tutorial133-gui/recorder_config.json`을 불러옵니다.
3. render product의 카메라가 `/World/AnimatedCamera`, 해상도가 512×512인지 확인합니다.
4. BasicWriter에서 RGB·Semantic Segmentation·Bounding Box 2D Tight를 확인합니다.
5. Control의 프레임 수 10과 **Control Timeline**을 확인하고 Start합니다.

GUI는 창을 닫을 때까지 남습니다. `--steps N`을 지정하면 준비 후 앱을 최대 N번 갱신하고 닫으므로 버튼 실습에는 생략하세요. PNG가 없는데 `recorder_stage.usda`와 `recorder_config.json`만 있다면, 아직 기록을 시작하지 않았을 수 있습니다.

### 코드에서 볼 부분

카메라는 기본 방향인 local -Z를 바라보고 높이 7 m에서 움직입니다.

```python
stage.SetTimeCodesPerSecond(60)
translation.Set((-1, 0, 7), 0)
translation.Set((1, 0, 7), 120)
```

`0`, `120`은 초가 아닌 **USD time code**입니다. 이 장면에서는 초당 60 time code이므로 전체 이동은 2초 구간에 작성되어 있습니다. 10장만 촬영해 카메라의 전체 이동이 끝나지 않아도 정상입니다. Control Timeline은 Recorder가 이 시간 진행을 제어할지를 정합니다.

### 실행 결과 확인하기

설정의 `out_working_dir`는 `/tmp/tutorial133-gui`, `out_dir`는 `recording`입니다. 그 아래 Recorder가 만든 기록 경로에서 RGB와 정답을 확인하세요.

- RGB에서 상자가 보이고 프레임이 진행하면서 시점이 달라지는지 봅니다.
- 의미 라벨에 `carton`이 있고 tight box가 보이는 상자와 맞는지 확인합니다.
- `recorder_stage.usda`는 장면, `recorder_config.json`은 기록 설정입니다. JSON만 불러오면 장면까지 복원되지는 않습니다.

Pause와 Resume도 확인하려면 GUI에서 프레임 수를 충분히 늘리고 **새 출력 경로**를 선택하세요. Start → Pause → Resume → Stop을 눌러 진행 상태를 비교합니다. 비동기 저장 큐에 있던 파일은 Pause 직후에도 마무리될 수 있으므로 버튼 상태와 프레임 진행을 함께 보세요.

## 2. 자동 기록과 사용자 Writer 비교하기

자동 실행은 같은 확장을 사용하지만 버튼을 대신 눌러야 하는 대기가 없습니다.

```bash
~/isaacsim/python.sh src/133_replicator_replicator_recorder/run.py --headless --frames 10 --output /tmp/tutorial133-auto
```

`SyntheticRecorder.start_stop_async()`를 예약하고 바깥 반복문에서 `app.update()`를 호출해 작업을 진행합니다. 완료 또는 기본 10000번 앱 갱신 한도까지 기다립니다. Headless의 `--steps`는 **기록을 기다리는 한도**이고 `--frames`는 저장할 프레임 수입니다.

### 코드에서 볼 부분

GUI 실행 때 이미 등록한 `BeginnerNormalWriter`는 RGB와 normals annotator를 선택합니다. 법선은 표면이 어느 방향을 향하는지 나타내는 벡터입니다.

```python
color = np.clip((values[..., :3] + 1) * 127.5, 0, 255).astype(np.uint8)
self.backend.write_image(f"{key}/{self.frame:06d}.png", color)
```

법선 성분의 -1~1 범위를 이미지의 0~255로 옮깁니다. 그래서 법선 이미지의 빨강·초록·파랑은 재질 색이나 물체까지의 거리가 아니라 **표면 방향을 보기 위한 표시**입니다.

Recorder의 사용자 Writer 설정에서 `BeginnerNormalWriter`를 선택하고 **Parameters Path**에 이 폴더의 `custom_writer_params.json` 절대경로를 넣으세요. 이 파일은 `rgb=true`, `normals=true`를 전달합니다. 출력 경로는 새로 지정합니다. 결과는 `rgb.../000000.png`, `normals.../000000.png`처럼 annotator별 폴더에 저장됩니다. 기본 headless 명령은 BasicWriter를 사용하므로 이 사용자 Writer를 자동 선택하지 않습니다.

검출 상자를 이미지 위에서 확인하려면 Script Editor에서 `from isaacsim.replicator.writers import DataVisualizationWriter`를 실행한 뒤 사용자 Writer로 `DataVisualizationWriter`를 선택하고 같은 입력 칸에 `visualization_params.json`을 지정합니다. 파일은 tight box를 RGB 위에 초록색으로, loose box를 normals 위에 빨간색으로 표시하고, 3D box를 RGB 위에 투영하도록 요청합니다. 이는 원래 검출 배열을 대신하는 학습 정답이 아니라 경계가 물체와 맞는지 살펴보는 시각화입니다.

카메라 무작위화는 별도 실습입니다. 장면을 연 상태에서 **Window > Script Editor**에 `randomize_camera.py`를 붙여 넣어 실행하세요. 출력된 Camera prim 경로를 Recorder의 새 render product에 연결합니다. 스크립트가 카메라를 추가해도 기존 AnimatedCamera 연결이 저절로 바뀌지는 않습니다.

### 공식 창고 장면으로 옮겨 보기

로컬 상자의 기록을 확인했다면 공식 예제의 여러 카메라와 라벨이 있는 창고에서도 같은 절차를 적용할 수 있습니다. 5.1 자산 라이브러리가 필요합니다.

1. 기록을 Stop한 뒤 Content Browser에서 **Isaac Sim > Samples > Replicator > Stage > full_warehouse_worker_and_anim_cameras.usd**를 엽니다.
2. Stage에서 실제 Camera prim을 선택하고 Recorder의 **Add New Render Product**로 연결합니다. 이전 장면의 `/World/AnimatedCamera` 항목은 삭제합니다.
3. BasicWriter의 RGB·분할을 선택하고, 새 출력 경로·유한한 프레임 수·Control Timeline을 설정한 뒤 Start합니다.
4. 움직이는 카메라와 고정 카메라의 결과를 프레임 번호별로 비교합니다. 창고의 기존 의미 라벨도 함께 읽어 보세요.

`randomize_camera.py`까지 적용한다면 `look_at="/World/Carton"`을 새 장면의 실제 표적 경로로 바꾸고 위치 범위도 창고 안의 표적 주변으로 정해야 합니다. 로컬 상자에 맞춘 좌표를 그대로 쓰면 표적 밖을 촬영할 수 있습니다. 자산 경로와 GUI 연결 방식은 [공식 Recorder의 Getting Started](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#getting-started)에서 확인할 수 있습니다.

## 3. 준비·시간 진행·파일 저장의 관계 정리

```text
USD 장면 준비 + Recorder JSON 준비
    → Recorder에 설정 로드
    → Start
    → 타임라인 진행과 카메라 렌더
    → 선택한 annotator를 Writer가 저장
```

Recorder 설정은 무엇을 기록할지 정하고 Control은 언제 기록할지 정합니다. 키프레임 카메라는 타임라인 시간을 따라 움직이며, 무작위 카메라는 Replicator의 `on_frame` 트리거로 위치를 선택합니다. 같은 카메라 변화처럼 보여도 변화의 기준이 다릅니다.

## 4. 간단한 확인 실험

로컬 상자 장면에서 카메라 경로와 프레임 수를 유지하고 **해상도만 512×512에서 256×256으로 바꾸세요.** 새 폴더에 기록합니다.

저장한 RGB의 가로·세로 크기는 절반이 되고 전체 픽셀 수는 1/4이 됩니다. 같은 상자의 2D 검출 좌표도 새 이미지 크기를 기준으로 읽어야 합니다. 장면의 1 m 상자가 실제로 작아진 것은 아닙니다.

## 실행할 때 막히면

- **장면은 보이지만 PNG가 없음**: GUI는 준비만 수행합니다. 설정을 불러왔는지와 Start 상태를 확인하세요.
- **`Native recorder exceeded --steps`**: 요청 프레임을 기록하기 전에 앱 갱신 한도에 도달했습니다. 먼저 프레임 수와 초기 로딩 상태를 확인하세요.
- **사용자 Writer가 목록에 없음**: `run.py`가 실행한 창인지 확인하세요. 다른 창에서는 `custom_writer.py` 등록도 별도로 필요합니다.
- **랜덤 카메라가 추가되었는데 같은 시점만 기록됨**: render product가 아직 `/World/AnimatedCamera`를 가리키는지 확인하세요.
- **JSON을 불러왔는데 카메라 경로가 없음**: 장면 USD를 먼저 열어야 합니다. 설정 파일과 장면 파일은 서로 대체하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Synthetic Data Recorder](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html)에 대응합니다. 공식 Recorder의 설정·제어·사용자 Writer를 외부 창고 자산이 필요 없는 로컬 상자로 연습합니다.

[VERIFICATION.md](VERIFICATION.md)에 기록된 범위는 정적 검사이며 `tutorial.json`은 `not_run`입니다. Headless 코드의 PNG 존재 확인은 최소 검사일 뿐 프레임 수·라벨 내용·GUI 버튼 동작을 모두 검증하지 않습니다. 위 절차의 생성 결과는 실행 환경에서 직접 확인할 기준입니다.
