# 04 — Robot Synthetic Data Factory

## Goal / Architecture / Execution Context

**Isaac Sim 5.1.0.** Jetbot의 바퀴를 구동하며 부착된 camera에서 RGB·depth·segmentation·bounding box를 저장합니다. Standalone은 batch 실행을 소유하고, Extension은 이미 실행 중인 Kit 안에서 GUI와 async 작업을 제공합니다.

```text
standalone/generate.py ─┐
                       ├─ core/robot_sdg/{robot,randomization,dataset}.py
extension/             ┘
  robot_learning.sdg/config/extension.toml
  robot_learning.sdg/robot_sdg_ui/extension.py
```

Extension 코드는 외부 편집기에서 수정하는 파일입니다. Script Editor에 큰 프로그램을 붙여넣는 방식이 아닙니다. 두 실행 경로가 동일한 scene 구성과 randomization·writer 설정을 공유합니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)
- NVIDIA Omniverse Kit — [Extensions in-depth](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/extensions_advanced.html)

## Dependencies / How to Run

Isaac Sim 설치, Jetbot asset 접근, rendering 가능한 NVIDIA GPU가 필요합니다. `core`를 별도로 pip 설치할 필요는 없습니다.

Standalone, 저장소 루트:

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/python.sh" src/04_robot_synthetic_data/standalone/generate.py \
  --headless --episodes 2 --frames 10 --seed 7 --output outputs/sdg_seed7
```

Extension은 **Kit GUI 프로세스**로 실행합니다:

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" \
  --ext-folder "$PWD/src/04_robot_synthetic_data/extension" \
  --enable robot_learning.sdg
```

빈 Stage에서 `Robot Learning SDG` 창의 **Load / Preview → Generate** 순서로 사용하세요. Seed, episode 수, episode당 frame 수, output 상위 폴더를 바꿀 수 있습니다. Cancel은 진행 중인 job을 취소하고 완료된 파일을 보존합니다. 생성 결과는 output 아래의 새 timestamp 폴더에 저장됩니다. 기본 GUI output은 `~/isaac_learning_outputs`입니다.

기존 scene을 지우지 않도록 World나 `/World`의 내용이 이미 있으면 로딩을 거부합니다. 새 실험은 File → New로 빈 Stage를 만든 뒤 Extension을 껐다 켜서 시작하세요. Standalone 안에서 Extension UI를 재현하려고 하지 말고 위 Kit 실행 명령을 사용하세요.

### Sources

- NVIDIA Isaac Sim 5.1 — [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- NVIDIA Omniverse Kit — [Extension lifecycle and Python modules](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/extensions_advanced.html)

## USD Assets / Robot Model / Physics / APIs Used

`/World/LearningSDG` 아래에 Jetbot reference, 6개 box, DomeLight를 배치합니다. camera는 robot chassis의 자식입니다. Box는 `FixedCuboid`로 위치가 물리 반응 때문에 변하지 않으며, robot은 매 physics step에 wheel velocity command를 받아 움직입니다. episode 시작의 robot pose randomization만 teleport입니다. 물리 dt는 1/60초, 기본 4 step마다 한 frame을 capture합니다.

| 개념 | 이 예제에서의 역할 |
|---|---|
| Sensor / render product | `Camera`, 기본 320×240, clipping 0.01–20m |
| Semantic label | `add_labels(..., instance_name="class")`, `box`, `mobile_robot` |
| Annotator | RGB, distance-to-image-plane, semantic segmentation, tight 2D boxes |
| Writer | `BasicWriter`가 위 annotator의 결과를 파일로 기록 |
| Randomization | episode 시작에 Python RNG로 parameter를 sample하고 USD/API로 적용 |
| Capture trigger | `rep.orchestrator.step` / `step_async`, `delta_time=0`, `rt_subframes=4` |

randomization 대상은 robot XY/yaw, box 위치와 diffuse color, light intensity/color, camera 높이/pitch/focal length입니다. `seed + episode`로 Python RNG를 생성하고 Replicator seed도 고정합니다. 이는 parameter 재현성을 제공하며 GPU 이미지의 bitwise 동일성까지 보장하지 않습니다. 모든 parameter는 metadata에 저장됩니다.

### Sources

- NVIDIA Isaac Sim 5.1 — [Getting Started Scripts: capture, writer, randomization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- NVIDIA Isaac Sim 5.1 — [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- NVIDIA 공식 v5.1.0 소스 — [BasicWriter standalone example](https://github.com/isaac-sim/IsaacSim/blob/v5.1.0/source/standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_01.py)

## 출력 읽기 / 공부 순서

Standalone의 `outputs/.../dataset/`, Extension의 선택한 timestamp 폴더:

```text
rgb_0000.png
distance_to_image_plane_0000.npy
semantic_segmentation_0000.png
semantic_segmentation_labels_0000.json
bounding_box_2d_tight_0000.npy
bounding_box_2d_tight_labels_0000.json
metadata.jsonl
```

`metadata.jsonl`의 `capture_index`가 파일 번호와 대응합니다. 각 행에 episode/frame 번호, simulation time, 실제 robot/camera pose, camera intrinsics, randomization parameter가 있습니다. pose quaternion은 wxyz입니다. depth의 무효 값은 따로 확인하고, segmentation의 정수 ID는 같은 frame의 label JSON과 함께 해석하세요.

1. [randomization.py](core/robot_sdg/randomization.py)부터 읽고 어떤 변수를 언제 뽑는지 확인합니다.
2. [robot.py](core/robot_sdg/robot.py)에서 chassis Prim과 articulation wrapper를 구분합니다.
3. [dataset.py](core/robot_sdg/dataset.py)에서 label → render product → writer 연결을 읽습니다.
4. [generate.py](standalone/generate.py)의 physics step과 capture step을 구분합니다.
5. [extension.py](extension/robot_learning.sdg/robot_sdg_ui/extension.py)의 startup, async job, cancel, shutdown을 읽습니다.

## Known Limitations / 실험

Headless에서도 camera rendering을 끄면 데이터가 생성되지 않습니다. 첫 asset 접근과 shader 준비가 느릴 수 있습니다. writer drain 후 detach하는 순서를 지켜 마지막 파일을 잃지 않도록 했습니다. Extension은 Kit의 update 주기를 사용하므로 Standalone과 같은 seed라도 frame의 물리 시점이 정확히 같지는 않습니다. 자동 batch 재현 실험에는 Standalone을 추천합니다.

- seed만 바꿔 metadata 차이를 비교하세요.
- camera 높이·focal length만 바꾸고 bounding box pixel 크기와 depth를 비교하세요.
- 먼저 `--episodes 1 --frames 3`으로 modality별 파일 개수와 label을 검사하세요.
- `--steps-per-frame`을 늘리고 시간 간격과 robot 이동 거리가 함께 늘어나는지 관측하세요.

### Sources

- NVIDIA Isaac Sim 5.1 — [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- NVIDIA Isaac Sim 5.1 — [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html)
