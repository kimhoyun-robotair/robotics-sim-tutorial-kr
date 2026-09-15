# 136. 카메라 프레임과 물리 시간은 어떻게 연결될까요?

## 이번에 배우는 것

**여러 카메라의 데이터와 물리·타임라인 기록을 비교하며, 필요한 순간에만 센서 데이터를 얻습니다.**

앱을 한 번 갱신했다고 모든 센서가 사진을 한 장씩 저장하는 것은 아닙니다. 물리 계산은 더 자주 진행할 수 있고, 물체가 정착한 뒤에만 촬영할 수도 있습니다. 이번 예제는 이 연결을 일곱 모드에서 살펴봅니다.

| 모드 | 촬영 또는 관찰 기준 |
|---|---|
| `multi-camera` | 같은 상태를 카메라 세 대로 촬영합니다. |
| `settled` | 물체의 속도와 높이가 정착 조건을 만족해야 촬영합니다. |
| `custom-event` | 지정한 물체의 회전 이벤트를 보낸 뒤 촬영합니다. |
| `motion-blur` | 움직임의 짧은 시간 구간을 렌더합니다. |
| `events` | 타임라인·물리·렌더·앱 이벤트의 횟수와 시간을 기록합니다. |
| `custom-fps` | 물리 단계 몇 번마다 센서를 읽을지 정합니다. |
| `cosmos` | CosmosWriter의 데이터 출력과 클래스 색 매핑을 확인합니다. |

각 모드는 새 장면을 만듭니다. 기본 도형을 사용하므로 외부 창고나 로봇 자산을 미리 준비할 필요는 없습니다.

## 1. 세 카메라의 결과를 구분해서 읽기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example multi-camera --headless --frames 3 --output /tmp/tutorial136-multi
```

새 출력 경로를 사용합니다. 세 번 촬영한 뒤 종료하며, GUI에서 `--headless`와 `--steps`를 생략하면 저장 후 창이 남습니다. `--steps`를 명시하면 작업 후 GUI 대기 없이 종료합니다. 이 값은 `settled`의 대기 한도와 `events`의 관찰 횟수로 쓰이며, 다른 모드의 사진 장수를 정하지 않습니다.

### 코드에서 볼 부분

```python
products = [rep.create.render_product(camera, (320 + 80 * index, 240),
            name=f'camera_{index}') for index, camera in enumerate(cameras)]
```

카메라별 너비가 320, 400, 480이고 높이는 모두 240입니다. 각 render product에 별도의 RGB annotator를 붙여 직접 읽는 경로와, `CameraWriter.write(data)`가 전달받아 저장하는 경로를 함께 사용합니다. Writer 콜백은 사용자 반복문이 아니라 Replicator가 호출합니다.

### 실행 결과 확인하기

| 파일 | 무엇을 비교하나요? |
|---|---|
| `0000_camera_0.png` 등 | 직접 읽은 세 카메라 RGB입니다. 같은 프레임 번호끼리 비교합니다. |
| `custom_writer/` | Writer가 받은 RGB를 저장한 결과입니다. |
| `writer_payloads.json` | Writer 입력의 `key`와 배열 `shape`로 카메라를 구분합니다. |
| `measurements.json` | `camera_shapes`와 타임라인 시간을 기록합니다. |
| `scene.usda` | 마지막 장면과 그래프 구성입니다. |

배열 shape는 `[높이, 너비, 채널]`입니다. 두 번째 카메라는 `[240, 400, ...]`인지 보세요. 한 Cube의 색은 프레임마다 무작위화되지만 같은 프레임의 세 카메라는 그 상태를 서로 다른 시점에서 봅니다.

## 2. 시간과 물리 상태를 촬영 조건으로 만들기

먼저 일정한 센서 간격을 확인합니다.

```bash
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example custom-fps --headless --stage-fps 60 --sensor-fps 10 --frames 6 --output /tmp/tutorial136-fps10
```

### 코드에서 볼 부분

```python
stride = args.stage_fps // args.sensor_fps
for step in range(1, args.frames * stride + 1):
    world.step(render=False)
    if step % stride == 0:
        capture(step // stride - 1, physics_time_s=world.current_time,
                requested_sensor_fps=args.sensor_fps)
```

60 Hz 물리를 6단계 진행할 때마다 센서를 읽으므로 간격은 `6 × 1/60 = 0.1초`입니다. 센서 주파수는 물리 주파수의 정수 약수여야 합니다. 촬영하지 않는 구간에는 render product 업데이트를 끄고 물리만 진행합니다.

`measurements.json`의 **`physics_time_s` 차이**를 확인하세요. 이 모드에서 센서 간격을 판단할 값은 측정한 `World.current_time`입니다. 최상위 `0000_depth.npy`는 `distance_to_camera`이며 카메라에서 표면까지의 거리를 미터 단위로 담습니다. 배경의 무한값은 통계에서 분리하세요.

정착 이후 촬영은 다른 조건을 사용합니다.

```bash
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example settled --headless --frames 2 --steps 600 --output /tmp/tutorial136-settled
```

매번 Cube를 공중으로 옮기고 속도를 0으로 초기화합니다. 30단계를 지난 뒤 선속도 <0.05 m/s, 각속도 <0.1 rad/s, 중심 높이 <1 m가 **10단계 연속** 만족될 때 촬영합니다. 처음 공중에 놓았을 때도 속도는 0이므로 속도 한 번만 읽어 정착이라고 판단하면 안 됩니다. 기록의 `physics_steps`, `speed_m_s`, `height_m`를 함께 읽으세요. `--steps` 안에 만족하지 못하면 timeout입니다.

### 나머지 모드에서 확인할 부분

다음 명령은 각각 새 출력 폴더를 사용합니다.

```bash
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example custom-event --headless --frames 4 --output /tmp/tutorial136-custom
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example events --headless --steps 120 --output /tmp/tutorial136-events
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example motion-blur --headless --renderer pt --subsamples 8 --output /tmp/tutorial136-blur
~/isaacsim/python.sh src/136_replicator_replicator_isaac_snippets/run.py --example cosmos --headless --frames 3 --output /tmp/tutorial136-cosmos
```

- **custom-event**: `lesson.left`, `lesson.right`를 교대로 보내 두 Cube 중 하나의 회전을 변경합니다. `requested_event`는 요청 이름이며 회전각 측정값은 아닙니다. 실제 변화는 해당 RGB와 함께 확인합니다.
- **events**: `timeline_times`, `physics_dt`, `render_events`, `app_events`, `wall_seconds`를 기록합니다. 이 모드는 촬영 루프를 부르지 않으므로 PNG가 없어도 됩니다. 물리 시간의 합과 실제 시계 시간을 비교할 수 있지만 네 이벤트 횟수가 같을 필요는 없습니다.
- **motion-blur**: 속도 0·2·4 m/s의 Cube 쌍을 만듭니다. 한쪽은 USD 시간별 위치, 다른 쪽은 중력을 끈 강체 속도로 움직입니다. `writer/` RGB에서 0속도 쌍을 기준으로 번짐을 비교하세요. `--renderer rt`는 다른 렌더 경로입니다. PT의 `subsamples`는 시간 표본이고 SPP=32는 광선 샘플 수입니다.
- **cosmos**: `cosmos/`에 실제 CosmosWriter 출력을 저장합니다. 클래스 색은 floor=파랑, cube=빨강, sphere=초록입니다. 모델 추론이나 학습을 수행하는 옵션은 아닙니다.

## 3. 세 종류의 횟수 정리

```text
물리 단계: 장면 속 위치·속도를 진행
앱 갱신: 타임라인, 렌더, 비동기 작업 등을 처리
캡처: 정한 시점의 annotator와 writer 출력을 얻음
```

`custom-fps`는 물리 단계 수로 촬영 간격을 만들고, `settled`는 관찰한 상태로 촬영 여부를 정합니다. `motion-blur`는 `delta_time=1/stage_fps`로 시간 구간을 진행하며, 다른 일반 캡처는 `delta_time=0.0`으로 준비된 상태를 읽습니다. 세 종류의 횟수를 하나의 “프레임”으로 섞으면 센서 주기와 결과 장수를 잘못 계산하게 됩니다.

## 4. 간단한 확인 실험

앞의 `custom-fps` 명령에서 **`--sensor-fps`만 10에서 20으로 바꾸어** 새 폴더에 실행하세요. `--stage-fps 60`, `--frames 6`은 유지합니다.

캡처 시점은 두 실행 모두 여섯 번입니다. 최상위의 `0000_camera_0.png`부터 여섯 RGB와 `measurements.json`의 여섯 기록을 비교하세요. `writer/`에도 같은 시점의 RGB 저장본이 생기므로 폴더 전체의 PNG 개수를 여섯 장으로 기대하면 안 됩니다. 달라지는 것은 물리 단계 간격이 6에서 3으로, 측정한 캡처 시간 차이가 약 0.1초에서 0.05초로 줄어든다는 점입니다. 고정된 캡처 수에서는 전체 관찰 물리 시간도 짧아집니다.

## 실행할 때 막히면

- **주파수 인수 오류**: `stage-fps`가 `sensor-fps`의 정수 배수여야 합니다. 이 검사는 모든 모드에 적용됩니다.
- **정착 timeout**: 캡처별 물리 대기 한도와 충돌·속도 상태를 확인하세요. timeout은 정착을 관찰하지 못했다는 뜻입니다.
- **events에서 사진이 없음**: 그 모드는 이벤트 계측용입니다. JSON의 물리·타임라인 목록이 비어 있지 않은지 확인하세요.
- **CosmosWriter를 찾지 못함**: Isaac Sim 5.1 배포본의 해당 Writer와 확장 상태를 확인하세요.
- **긴 motion-blur 실행에서 물체가 사라짐**: 물체가 아래로 계속 움직여 시야를 벗어났는지 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Useful Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html)에 대응합니다. 공식 일곱 주제를 자체 도형으로 구성했고, 센서 주기는 고정 물리 단계의 정수 비율로 구현했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 기존 실행은 기본 다중 카메라 한 프레임의 세 이미지 크기를 확인한 범위입니다. 다른 모드의 시간 계측·모션 블러·Cosmos 결과와 GUI는 별도 확인이 필요합니다. 이번 개정에서는 실제 GPU 실행을 추가하지 않았습니다.
