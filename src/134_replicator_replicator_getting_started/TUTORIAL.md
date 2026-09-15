# 134. 네 가지 시작 예제로 데이터 캡처 흐름 익히기

권장 학습 순서 **134** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t037`

공식 Getting Started Scripts의 네 시나리오를 `--example`으로 선택합니다. 각 실행은 자기 장면, 라벨, 카메라와 writer를 새로 만듭니다. 앞 예제의 상태나 다른 패키지를 먼저 실행할 필요가 없습니다. 결과는 모두 실제 annotator/writer가 반환한 데이터입니다.

## 이 실습의 의도

동일한 라벨 있는 Cube를 사용해 정지 캡처, 여러 카메라, 속성 무작위화, 물리 이벤트 캡처의 실행 시점을 비교하는 실습입니다. 기본 `basic`은 물체를 움직이지 않고 네 번 촬영하므로 이미지 배치가 그대로인 것이 정상입니다. `events`에서만 강체와 중력을 추가하며 바닥은 만들지 않아, 낙하 높이 변화로 촬영을 시작하고 같은 상태의 보이는/숨긴 이미지 쌍을 만듭니다. GUI는 캡처 완료 후 장면을 유지하지만 파일을 계속 추가하지 않습니다.

## 실행 후 확인할 것

- **basic:** 출력 폴더의 RGB, semantic segmentation, tight box에서 `/World/Cube`의 `carton` 정답을 확인합니다. `observations.json`의 position은 기본 네 프레임 모두 `[0,0,0]`이며 고정 배치 반복 촬영이 의도입니다.
- **multi:** front RGB는 512×512, side는 320×240인지 확인하고 `rgb_shapes`의 높이·너비 순서가 각각 `[512,512,...]`, `[240,320,...]`인지 봅니다. `camera_metadata_*.json`에는 각 render product의 camera_params와 3D box가 들어 있어야 하며 `pose/`는 `--pose-writer`를 지정했을 때 확인합니다.
- **randomize:** `observations.json`에서 x/y는 [-1,1] 범위로 바뀌고 z는 0을 유지하는지 봅니다. 조명 custom event는 0부터 센 짝수 프레임에만 전송되므로 물체 위치와 조명 변화가 서로 다른 주기를 가집니다. seed가 같아도 렌더 픽셀의 완전한 동일함을 성공 기준으로 두지 않습니다.
- **events:** `observations.json`의 height가 이전 이벤트보다 0.4 m 이상 낮아지고 `pair`가 두 연속 캡처 번호를 가리키는지 확인합니다. 각 쌍은 보이는 Cube와 숨긴 Cube를 같은 물리 상태에서 촬영하므로 숨긴 프레임의 carton 정답이 빠지는 것은 정상입니다.
- **종료와 개수:** events의 `--frames`는 최대 이벤트 수이고 이벤트 하나에 두 캡처가 생깁니다. z<0 또는 `--steps` 상한 때문에 요청 수보다 일찍 끝날 수 있으므로 실제 개수는 `observations.json`과 `Capture steps:`로 확인합니다. 이벤트가 하나도 없으면 코드는 오류로 종료합니다.
- **기존 검증의 범위:** [RUNTIME_CHECK.md](RUNTIME_CHECK.md)의 기록은 `basic --headless --frames 2`에서 RGB 두 장과 비어 있지 않은 정답을 확인한 사례입니다. multi/randomize/events 및 GUI는 해당 모드의 위 결과를 별도로 확인해야 합니다.

## GUI 실행과 종료

GUI 실행에서 `--steps`를 생략하면 정해진 캡처와 파일 저장을 끝낸 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 추가 이미지를 무한히 생성하지 않습니다. `--steps`는 events 모드의 물리 update 상한이며 생략 시 캡처에는 기존 300회를 사용합니다. 양수 `--steps N`을 명시하면 해당 설정으로 작업을 마치고 GUI 대기 없이 종료합니다. `--headless`는 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0 전체 설치, NVIDIA RTX GPU/드라이버와 저장 공간이 필요합니다. 기본 예제는 USD 기본 도형만 사용해 원격 자산을 요구하지 않습니다. Isaac Sim에서 제공하는 NumPy를 사용하고 별도로 pip install하지 않습니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/134_replicator_replicator_getting_started
"$ISAAC_SIM_PATH/python.sh" run.py --example basic --headless
"$ISAAC_SIM_PATH/python.sh" run.py --example multi --headless
"$ISAAC_SIM_PATH/python.sh" run.py --example randomize --headless
"$ISAAC_SIM_PATH/python.sh" run.py --example events --headless
# multi 예제에 공식 PoseWriter 출력도 추가
"$ISAAC_SIM_PATH/python.sh" run.py --example multi --pose-writer --output output/multi_pose
```

같은 출력 폴더는 덮어쓰지 않습니다. `output/basic`, `output/multi`, `output/randomize`, `output/events`가 각각 생깁니다. `--frames`는 기본/다중/무작위 모드의 캡처 횟수입니다. events에서는 최대 이벤트 수이고 한 이벤트에 두 장을 기록합니다. 물체가 바닥 높이 아래로 떨어지면 더 일찍 끝나므로 실제 이벤트 개수는 `observations.json`으로 확인합니다.

## 1. BasicWriter

1. basic을 실행하고 RGB PNG, semantic segmentation PNG/JSON, tight bounding box 파일을 찾습니다.
2. `class=carton`이 각 정답에서 어떻게 표현되는지 확인합니다. 화면의 색과 label ID는 별개입니다. bounding box 숫자는 픽셀 좌표이고 prim의 translate는 미터입니다.
3. `observations.json`의 position이 모든 프레임에서 같은지 확인합니다. 이 모드에는 물리 진행이나 randomizer가 없어 같은 상태를 반복 촬영합니다.

## 2. 여러 카메라와 사용자 writer

1. multi를 실행합니다. front는 512×512, side는 320×240입니다. `rgb_shapes`는 NumPy 배열의 **높이, 너비, 채널** 순서라 side는 `[240,320,...]`로 표시됩니다.
2. `camera_metadata_0000.json`을 엽니다. `CameraMetadataWriter`가 camera_params와 bounding_box_3d를 `renderProduct` 관점으로 묶습니다. 투영 행렬·카메라 transform과 3D box의 정답을 RGB와 같은 프레임으로 저장합니다.
3. `--pose-writer`로 다시 실행해 `pose` 아래 정답과 debug 이미지를 확인합니다. Writer마다 annotation 스키마가 다르므로 BasicWriter 파일을 임의로 PoseWriter 형식이라고 부르지 않습니다.

## 3. USD randomizer와 OmniGraph 이벤트

1. randomize를 실행해 `observations.json`의 물체 x/y가 매 프레임 달라지는지 확인합니다. 이는 Python `random.uniform`과 USD translate 속성으로 직접 작성한 변화입니다.
2. 코드에서 `frame % 2 == 0`일 때만 `send_og_event("change_light")`가 호출됨을 확인합니다. 이 이벤트가 Replicator 그래프의 dome light 색을 바꿉니다. `step()` 자체는 여기서 해당 custom event를 발생시키지 않습니다.
3. 같은 seed=42로 새 출력 폴더에 실행해 배치 위치를 비교합니다. seed는 randomizer 재현성을 돕지만 GPU 렌더 픽셀의 비트 단위 동일함을 보장하지 않습니다.

## 4. 낙하 높이에 따른 이벤트 캡처

1. events를 실행합니다. USD Physics Scene의 중력은 z=-9.81m/s²이며 상자는 z=2m에서 떨어집니다. World 바닥을 추가하지 않아 z<0일 때 중지합니다.
2. 이전 캡처 높이에서 0.4m 이상 내려갔을 때 timeline을 pause합니다. 같은 물리 상태에서 상자가 보이는 이미지와 숨긴 이미지를 연속 촬영한 후 다시 표시하고 play합니다.
3. `observations.json`의 height가 내려가는지, `pair`가 두 연속 캡처 번호를 가리키는지 확인합니다. hidden 프레임에서는 carton의 의미/검출 정답도 달라져야 합니다.

## API와 기본 개념

USD **Stage**는 전체 장면, **prim**은 Cube/Camera/Light 같은 항목, **schema**는 해당 항목의 속성 규약입니다. `CollisionAPI`는 충돌 형태, `RigidBodyAPI`는 물리 엔진이 움직일 강체임을 표시합니다. 단순 Cube prim만 만들면 중력으로 떨어지지 않습니다.

`SimulationApp`을 먼저 만든 뒤 `omni`·`pxr`를 import합니다. `rep.create.render_product`는 카메라와 해상도를 묶습니다. annotator의 `get_data()`는 GPU 렌더에서 만들어진 배열을 직접 반환하고 writer의 `write()`는 같은 데이터를 파일 단위로 조직합니다. `CameraMetadataWriter`의 JSON 변환은 NumPy 값을 보존하기 위한 직렬화이며 카메라 값을 합성하지 않습니다.

`set_capture_on_play(False)`는 타임라인 실행 때 원치 않는 기록을 막습니다. `step(delta_time=0.0)`은 캡처 중 물리를 진행시키지 않습니다. `pause_timeline` 기본값과 timeline.play 호출 위치를 함께 읽어야 합니다. `rt_subframes`는 렌더 안정화용 반복이고, DLSS 설정값 2는 Quality입니다. 마지막 `wait_until_complete()`는 비동기 출력이 완료되기 전 프로그램이 닫히지 않도록 합니다. writer/annotator detach 후 render product를 해제합니다.

공식 문서는 Script Editor의 `await step_async()`와 standalone의 `step()`을 모두 제공합니다. 여기서는 재실행 가능한 CLI를 위해 synchronous standalone으로 구현했습니다. Script Editor에 전체 `run.py`를 붙여넣어 두 번째 SimulationApp을 만들면 안 됩니다.

## 하나씩 바꿔보기와 문제 해결

randomize의 **빛 이벤트 간격만 2→3**으로 바꿉니다. 물체 위치 변화 간격은 유지하고 사진에서 조명 변화의 빈도를 비교합니다. 검은 영상은 카메라·조명·초기 렌더 로딩을 확인하고 `--rt-subframes 16`으로 다시 시도합니다. multi에서 bounding box가 비면 carton이 카메라 시야에 있는지 확인합니다. events가 한 장도 기록하지 않으면 실제 Physics Scene·RigidBody 적용과 USD transform 갱신을 확인합니다. 이 경우 코드는 성공을 출력하지 않고 오류로 종료합니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- [orchestrator step function](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#orchestrator-step-function)
- [custom writer and annotators with multiple cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#custom-writer-and-annotators-with-multiple-cameras)
- [custom randomizations replicator graph and usd api](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#custom-randomizations-replicator-graph-and-usd-api)
- [event triggered data capture timeline and simulation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html#event-triggered-data-capture-timeline-and-simulation)

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
