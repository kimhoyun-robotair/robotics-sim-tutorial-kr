# Replicator와 합성 데이터 생성

합성 데이터 생성은 “이미지를 많이 저장하다”보다 넓다. scene 분포를 정의하고, randomization을 실행하며, sensor 결과를 annotator로 해석하고, writer가 dataset contract에 맞게 기록하며, 실제 데이터와의 차이를 평가하는 pipeline이다.

## 핵심 객체

| 객체 | 역할 |
| --- | --- |
| Camera/Render Product | 어떤 시점과 해상도를 렌더링할지 정하다. |
| Randomizer | pose, material, light, background, distractor 분포를 정의하다. |
| Trigger/Orchestrator | randomization과 capture 시점을 정하다. |
| Annotator | RGB, depth, normal, semantic/instance segmentation, bounding box 같은 ground truth를 산출하다. |
| Writer | 결과와 metadata를 파일 또는 사용자 backend에 기록하다. |

## 최소 offline capture

다음 예제는 실행 중인 Isaac Sim scope에서 사용하다. asset을 충분히 load한 뒤 frame을 캡처하고 output path를 별도 저장장치로 지정하다.

```python
import omni.replicator.core as rep

OUTPUT_DIR = "/tmp/isaacsim-course-sdg"

camera = rep.create.camera(position=(3.0, 3.0, 2.0), look_at=(0.0, 0.0, 0.5))
render_product = rep.create.render_product(camera, (640, 480))
targets = rep.get.prims(path_pattern="/World/Objects/.*")

with rep.trigger.on_frame(num_frames=100):
    with targets:
        rep.modify.pose(
            position=rep.distribution.uniform((-1.0, -1.0, 0.1), (1.0, 1.0, 1.5)),
            rotation=rep.distribution.uniform((0.0, 0.0, 0.0), (360.0, 360.0, 360.0)),
        )

writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(
    output_dir=OUTPUT_DIR,
    rgb=True,
    distance_to_camera=True,
    semantic_segmentation=True,
)
writer.attach([render_product])
rep.orchestrator.run()
rep.orchestrator.wait_until_complete()
```

`/World/Objects` 아래에 실제 대상 prim이 있어야 하다. semantic label을 부여하지 않으면 segmentation이 학습에 쓸 수 없는 값이 될 수 있다. API option은 writer 버전마다 달라지므로 5.1.0 `BasicWriter` schema를 확인하다.

## dataset contract를 먼저 만들다

```yaml
dataset:
  version: 1
  seed: 20260831
  frames: 10000
  resolution: [640, 480]
  modalities: [rgb, depth, semantic_segmentation]
  split: {train: 0.8, val: 0.1, test: 0.1}
  units: {length: meter, depth: meter}
  frame_convention: camera_optical
```

같은 seed가 모든 GPU와 renderer에서 bit-identical 결과를 보장한다고 가정하지 않다. 대신 config, asset hash, Isaac Sim version, driver, writer version, frame count를 manifest에 남기다.

## randomization 품질을 검증하다

1. 분포의 최소·최대뿐 아니라 histogram과 상관관계를 확인하다.
2. camera가 물체 안이나 벽 뒤에 생성되지 않도록 rejection 조건을 두다.
3. bounding box가 image 밖이거나 너무 작을 때 처리 규칙을 정하다.
4. class별 frame·instance 수와 occlusion 비율을 계산하다.
5. train/validation split에 같은 scene seed나 동일 asset instance가 누출되지 않게 하다.

GPU memory가 부족하면 resolution, 동시 render product, sensor 수를 먼저 줄이다. online generation은 학습 loop와 simulator failure를 함께 다뤄야 하므로 offline dataset을 먼저 검증한 뒤 적용하다.

## 확장 흐름

- Scene-based SDG는 YAML/JSON config, 환경 load, 물리 randomization, camera와 writer를 하나의 standalone pipeline으로 묶다.
- Object-based SDG는 mutable 속성과 distribution dependency로 asset 중심 variation을 만들다.
- Action/Event Data Generation은 actor, camera, writer control을 event와 결합하다.
- MobilityGen은 navigation trajectory와 mobile sensor data 생성을 다루다.
- pose estimation 과정은 synthetic pose dataset 생성 후 model training까지 연결하다.

## 출처

- [Perception Data Generation Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_overview.html)
- [Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_getting_started.html)
- [Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
- [Synthetic Data Recorder](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html)
- [Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/index.html)
