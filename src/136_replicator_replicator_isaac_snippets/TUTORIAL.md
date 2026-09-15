# 136. 카메라 데이터, 캡처 시점, 이벤트, 모션 블러 실습 모음

권장 학습 순서 **136** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t048`

Isaac Sim 5.1.0 공식 **Useful Snippets**의 일곱 절을 독립적으로 실행합니다. 데이터가 **어느 카메라에서, 어느 시뮬레이션 시점에, 어떤 트리거로** 생성되었는지 확인하는 것이 목표입니다. 하나의 CLI에서 예제를 선택하지만 각 실행은 새 장면으로 시작하며 이전 실습 결과를 요구하지 않습니다.

## 이 실습의 의도

카메라 선택, 물리 상태, 이벤트, 시간 간격이 데이터 수집을 어떻게 결정하는지 비교하는 실습입니다. 기본 `multi-camera`는 같은 두 Cube를 서로 다른 위치와 해상도의 카메라 3대로 3회 촬영하고, annotator 직접 읽기와 사용자 Writer 저장을 함께 수행합니다. 정착·모션 블러·이벤트 빈도·CosmosWriter는 각각 별도 실행 모드이므로 아래에서 선택한 모드에 해당하는 결과를 확인합니다.

## 실행 후 확인할 것

- **기본 다중 카메라:** `0000_camera_0.png`부터 세 시점의 이미지 크기가 각각 320×240, 400×240, 480×240인지 확인합니다. `writer_payloads.json`의 `key`와 `shape`, `custom_writer/`의 파일을 함께 보아 카메라별 결과가 구분되는지 확인합니다. NumPy `shape`는 높이·너비·채널 순서입니다.
- **정착 모드:** `settled`의 `measurements.json`에서 `physics_steps`, `speed_m_s`, `height_m`를 확인합니다. 코드는 30스텝을 지난 뒤 선속도 <0.05 m/s·각속도 <0.1 rad/s·높이 <1 m가 10스텝 연속 유지될 때만 캡처하며, `--steps` 내 미충족은 timeout입니다.
- **사용자 이벤트:** `custom-event`에서 `requested_event`가 `lesson.left`, `lesson.right`로 교대하는지 보고 해당 RGB에서 요청한 Cube의 회전을 비교합니다. 기록에는 회전각 수치가 없으므로 이벤트 이름만으로 실제 회전 변경을 확인했다고 판단하지 않습니다.
- **센서 간격과 이벤트:** 기본 주파수의 `custom-fps`에서는 `physics_time_s`의 연속 차이가 약 0.1초인지 확인합니다. `events`에서는 `timeline_times`와 `physics_dt`가 비어 있지 않은지가 핵심이며, 네 이벤트의 횟수가 같거나 PNG가 저장될 필요는 없습니다.
- **모션 블러:** `motion-blur`의 `writer/` RGB에서 `/World/Animation_0`부터 세 객체와 `/World/Physics_0`부터 세 객체의 0·2·4 m/s 쌍을 비교합니다. 0속도 쌍은 기준이며, 이동 쌍의 번짐은 RT/PT 설정과 시간 샘플 수에 따라 달라집니다.
- **Cosmos 모드:** `cosmos/`의 실제 결과와 클래스 매핑을 확인합니다. floor=파랑·cube=빨강·sphere=초록은 의미 클래스 색이며 시각 재질 색과 다릅니다. 이 모드는 데이터 Writer를 실행하며 Cosmos 모델 추론이나 학습은 수행하지 않습니다.

## GUI 실행과 종료

GUI 실행에서 `--steps`를 생략하면 정해진 캡처와 파일 저장을 끝낸 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 추가 이미지를 무한히 생성하지 않습니다. `--steps`는 settled 모드의 캡처별 정착 대기 상한 또는 events 모드의 관측 update 수이며 생략 시 기존 600회를 사용합니다. 양수 `--steps N`을 명시하면 해당 설정으로 작업을 마치고 GUI 대기 없이 종료합니다. `--headless`는 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0, 지원 NVIDIA RTX GPU/드라이버가 필요합니다. Replicator, Isaac Core API, NumPy, Pillow는 설치에 포함된 것을 사용합니다. 자체 도형으로 장면을 만들므로 외부 로봇/환경 USD와 다른 튜토리얼 패키지는 필요 없습니다. `cosmos` 모드는 5.1 설치에 포함된 `CosmosWriter`를 사용하며 Cosmos 모델 추론이나 학습을 실행하지 않습니다.

이 패키지 폴더에서:

```bash
ISAACSIM="$HOME/isaacsim"
python3 run.py --help
"$ISAACSIM/python.sh" run.py --example multi-camera --headless --output output/multi
"$ISAACSIM/python.sh" run.py --example settled --headless --frames 2 --steps 600 --output output/settled
"$ISAACSIM/python.sh" run.py --example custom-event --headless --frames 4 --output output/events_capture
"$ISAACSIM/python.sh" run.py --example motion-blur --headless --renderer rt --output output/blur_rt
"$ISAACSIM/python.sh" run.py --example motion-blur --headless --renderer pt --subsamples 8 --output output/blur_pt
"$ISAACSIM/python.sh" run.py --example events --headless --steps 120 --output output/event_rates
"$ISAACSIM/python.sh" run.py --example custom-fps --headless --stage-fps 60 --sensor-fps 10 --frames 6 --output output/sensor10
"$ISAACSIM/python.sh" run.py --example cosmos --headless --frames 12 --output output/cosmos
```

설치 경로에 맞게 `ISAACSIM`을 바꾸고 Windows에서는 `python.bat`를 사용합니다. 출력 경로가 이미 있으면 중단합니다. 기본 출력은 패키지 내부 `output/`입니다. `--headless`와 `--steps`를 생략하면 작업과 저장이 끝난 뒤에도 UI를 직접 닫을 때까지 유지합니다. 저장한 `scene.usda`를 **File > Open**으로 다시 열면 장면 구성을 볼 수 있습니다.

## 1. 여러 카메라와 사용자 Writer

1. `multi-camera`를 실행합니다. 세 카메라는 서로 다른 위치에서 같은 두 Cube를 봅니다. 해상도는 320×240, 400×240, 480×240입니다.
2. 최상위 `0000_camera_0.png` 등은 annotator의 `get_data()`로 읽은 값입니다. `custom_writer/`의 이미지는 로컬 `CameraWriter.write(data)`가 받은 값입니다.
3. `writer_payloads.json`을 열어 key에 포함된 render product 식별자와 shape를 비교합니다. **카메라마다 별도 annotator를 attach**했으므로 다른 카메라의 데이터가 덮여 섞이지 않아야 합니다.
4. 코드에서 `WriterRegistry.register(CameraWriter)`와 `writer.attach(products)`를 찾습니다. `write()`는 Replicator가 호출하는 콜백이므로 사용자가 직접 프레임마다 호출하지 않습니다.

## 2. 특정 물리 상태에서 데이터 읽기

1. `settled`는 Cube를 공중에서 놓은 뒤 선속도, 각속도, 높이로 정착 여부를 판단합니다.
2. 최소 30 physics step이 지난 후, 선속도 <0.05 m/s, 각속도 <0.1 rad/s, 높이 <1 m 조건이 **10 step 연속** 만족될 때만 캡처합니다.
3. `measurements.json`의 `physics_steps`, `height_m`, `speed_m_s`를 봅니다. 처음 생성한 물체의 속도가 0이라고 즉시 정착으로 판정하면 안 되므로 시간/높이/연속 조건을 추가했습니다.
4. `--steps`는 최대 대기 예산입니다. 한도를 넘으면 timeout으로 실패하며 가짜 정착 이미지를 만들지 않습니다. `writer/`의 semantic segmentation 데이터에는 Cube의 `class=cube` 라벨도 포함됩니다.

## 3. 사용자 이벤트로 선택적 무작위화

1. `custom-event`는 두 Cube에 `lesson.left`, `lesson.right` 이벤트를 각각 연결합니다.
2. 캡처마다 이벤트를 교대로 보내고 변경된 장면의 RGB를 저장합니다. `requested_event`로 어느 Cube를 바꾸려 했는지 확인합니다. `measurements.json`은 요청 이름과 카메라 배열 크기를 기록하며 회전각 자체는 기록하지 않습니다.
3. `rep.utils.send_og_event()`는 그래프에 요청을 전달하고 `rep.orchestrator.step()`은 렌더/캡처를 진행합니다. 요청과 파일 쓰기를 같은 동작으로 생각하지 마십시오.
4. 저장한 stage에서 Replicator 그래프의 두 event trigger를 살펴봅니다. `on_frame`에 연결한 randomizer는 매 캡처마다 동작하므로 특정 객체만 변경하려는 경우 사용자 이벤트가 유용합니다.

## 4. 애니메이션과 물리 모션 블러

1. `motion-blur` 장면에는 속도 0, 2, 4 m/s에 해당하는 쌍이 있습니다. 한쪽은 USD time sample로 이동하고 다른 쪽은 gravity를 끈 rigid body velocity로 이동합니다.
2. `rt`와 `pt` 폴더의 `writer/` RGB를 비교합니다. 같은 이동 속도여도 렌더 방식과 시간 샘플링에 따라 경계 번짐이 다릅니다.
3. PT에서는 `--subsamples`로 한 노출 구간의 시간 표본을 설정하고 physics FPS를 `stage_fps × subsamples`로 맞춥니다. 렌더 SPP(여기서는 32)는 광선 샘플 수이며 시간 subsample과 구분합니다.
4. `--stage-fps 30`과 60을 새 경로에 실행하면 캡처 간격은 각각 1/30 s, 1/60 s입니다. 시간 간격이 바뀌면 같은 속도에서도 한 노출 동안의 이동량이 달라집니다.
5. 원문 cracker-box 자산 쌍을 자체 Cube 쌍으로 바꾸었습니다. RT/PT 설정, time-sampled animation과 physics velocity 비교는 실제 렌더 경로를 사용합니다. 긴 프레임 수에서는 물체가 카메라 시야 아래로 나갈 수 있습니다.

## 5. timeline / physics / render / app 이벤트

1. `events`는 네 종류의 실제 이벤트를 구독한 뒤 `--steps`만큼 app update를 수행합니다.
2. `measurements.json`의 `timeline_times`, `physics_dt`, `render_events`, `app_events`, `wall_seconds`를 읽습니다. 물리 step 횟수, 앱 update 횟수, 새 render frame 횟수가 반드시 같지는 않습니다.
3. `sum(physics_dt)`는 수집한 물리 시간입니다. 이를 `wall_seconds`로 나눈 값은 이 구간의 물리 시간 대비 벽시계 진행 비율입니다. 샘플 데이터에서 출력된 값으로 계산해야 합니다.
4. `timeline_times`가 없거나 physics step이 하나도 없으면 코드가 실패합니다. 콜백 객체를 변수에 보관해야 구독이 유지되며 작업이 끝난 후 해제합니다.
5. 원문의 추가 설정인 `timeline.set_ticks_per_frame()`, `/app/runLoops/main/rateLimitFrequency`, `/persistent/simulation/minFrameRate`는 각각 timeline substep, 앱 실행 제한, 물리 catch-up 제한입니다. 이번 CLI는 먼저 stage FPS와 실제 이벤트 차이를 관찰하도록 설정 수를 줄였습니다.

## 6. 특정 센서 FPS로 Writer와 annotator 사용

1. `custom-fps`는 physics를 60 Hz로 진행하고 6 step마다 캡처해 10 Hz 데이터를 만듭니다. sensor FPS는 stage FPS의 정수 약수여야 합니다.
2. `measurements.json`의 `physics_time_s` 차이를 확인합니다. 10 Hz이면 연속 캡처 간격은 약 0.1초여야 합니다. 이 값은 측정된 `World.current_time`입니다.
3. RGB는 Writer로, depth는 annotator의 `.npy`로 저장됩니다. 깊이 배열은 미터 거리값을 유지하며 배경에 무한값이 있을 수 있습니다.
4. 캡처가 없는 구간은 `hydra_texture.set_updates_enabled(False)`로 render product 업데이트를 끕니다. 캡처할 때만 다시 켜고 `step(delta_time=0)`을 호출하여 물리 시간을 의도치 않게 더하지 않습니다.
5. 원문은 timeline delta를 누적하여 capture 시점을 정합니다. 이 패키지는 **고정 physics step의 정수 비율**로 같은 목적을 구현해 입문자가 누적 오차 없이 간격을 확인할 수 있도록 했습니다.

## 7. Cosmos Writer

1. `cosmos`를 실행하면 라벨이 있는 floor, cube, sphere 장면을 생성합니다. Cube와 Sphere는 실제 collider/rigid-body 설정을 가집니다.
2. 출력 `cosmos/`에는 설치본 CosmosWriter가 구성하는 RGB 및 기하/세그멘테이션 관련 결과가 저장됩니다. 파일 목록과 이미지가 생성되는지 확인합니다.
3. `segmentation_mapping`은 클래스에 고정 색을 지정합니다. 이 예제에서는 floor=파랑, cube=빨강, sphere=초록입니다. 도형의 시각 재질 색과 의미 클래스 색은 별개입니다.
4. 클래스 이름을 바꾸면 생성 때의 semantic label과 writer mapping을 함께 맞춰야 합니다. 이 코드는 Cosmos 모델, 모델 가중치, 클라우드 추론을 호출하지 않습니다.

## API와 USD 기초

| 요소 | 의미 |
|---|---|
| `SimulationApp` | 확장과 렌더러 초기화입니다. 그 뒤에 `omni`, `pxr`를 import합니다. |
| USD Stage / Prim | 장면 문서와 그 안의 경로가 있는 객체입니다. 길이는 미터, 위쪽 축은 Z로 설정합니다. |
| Render product | 카메라와 해상도를 묶은 실제 렌더 출력입니다. 카메라 prim과 픽셀 배열 사이에 필요한 연결입니다. |
| Annotator | RGB, depth, semantic segmentation 등의 데이터 계산기입니다. `attach()`로 입력 출력을 연결합니다. |
| Writer | 여러 annotator 결과를 한 payload로 받아 파일/저장 매체에 기록합니다. |
| `TimeCode` | USD 속성에 시간별 값을 기록하는 키입니다. time code 값은 초가 아니라 stage FPS와 함께 해석합니다. |
| `delta_time` / `rt_subframes` | 전자는 물리/애니메이션 시간 진행, 후자는 같은 시점의 렌더 안정화 반복입니다. |
| `wait_until_complete()` | 비동기 파일 쓰기 큐가 끝날 때까지 기다립니다. 종료 직전에 필요합니다. |

`distance_to_camera`는 카메라에서 표면까지의 거리이고, optical axis 방향의 깊이인 `distance_to_image_plane`과 다릅니다. 물리 속도는 m/s, 각속도는 rad/s이며 `rotateXYZ`에 저장하는 회전각은 degrees입니다.

## 한 변수만 바꾸는 실험

`custom-fps`에서 stage FPS는 60으로 유지하고 sensor FPS만 10→20으로 바꿉니다. 동일한 물리 시간 동안 캡처 수가 두 배가 되는지 `physics_time_s`로 확인합니다. `events`의 wall time을 같은 값으로 고정된다고 가정하지 마십시오. 렌더링 부하는 실제 실행 속도에 영향을 줍니다.

## 문제 해결과 검증 범위

- `No module named omni/isaacsim`: 설치의 Python으로 실행합니다. 일반 Python에서는 `--help`만 지원합니다.
- settled timeout: `--steps`를 충분히 주고 위치/충돌/velocity를 확인합니다. timeout을 성공으로 바꾸지 마십시오.
- 빈 이미지: 카메라 위치, render product 활성화, writer/annotator attach 순서를 확인합니다. 렌더 전에 `get_data()`를 호출하면 새 프레임이 없습니다.
- CosmosWriter 미등록: 5.1 배포본의 Replicator extension 버전을 확인합니다. 일반 Writer로 바꾸어 Cosmos 출력이 검증됐다고 판단하지 않습니다.
- 이 패키지의 정적 문법/도움말 확인은 GPU 결과 검증을 대신하지 않습니다. 실제 프레임, callback 기록, 물리 시간과 출력 파일을 확인해야 합니다.

## 출처

- [Isaac Sim 5.1.0: Useful Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html)
- [여러 카메라](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#annotator-and-custom-writer-data-from-multiple-cameras), [물리 상태에 따른 캡처](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#synthetic-data-access-at-specific-simulation-timepoints), [사용자 이벤트](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#custom-event-randomization-and-writing)
- [모션 블러](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#motion-blur), [이벤트 구독](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#subscribers-and-events-at-custom-fps), [센서 FPS](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#accessing-writer-and-annotator-data-at-custom-fps), [CosmosWriter](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_isaac_snippets.html#cosmos-writer-example)
- 공식 설치 비교 경로: `standalone_examples/api/isaacsim.replicator.examples/`의 `multi_camera.py`, `simulation_get_data.py`, `custom_event_and_write.py`, `motion_blur.py`, `subscribers_and_events.py`, `custom_fps_writer_annotator.py`, `cosmos_writer_simple.py`.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
