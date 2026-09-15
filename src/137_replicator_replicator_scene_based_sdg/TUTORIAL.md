# 137. 창고 장면 기반 합성 데이터셋

권장 학습 순서 **137** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t038`

이 패키지는 지게차·팔레트·상자·콘이 있는 **공식 scene-based SDG 전체 파이프라인**을 로컬로 포함합니다. 지게차 주변의 의미 있는 위치 관계, 물리 낙하, 세 카메라, 서로 다른 randomizer 주기, 여러 writer 설정을 유지합니다. `scene_based_sdg.py`와 `scene_based_sdg_utils.py`는 NVIDIA 5.1 설치 예제를 Apache-2.0 고지와 함께 포함했고 실행 제한·출력 보호·오류 시 앱 종료를 추가했습니다.

## 준비와 실행

Isaac Sim 5.1.0 전체 설치, 지원 RTX GPU/드라이버, 5.1 자산 서버 연결 또는 로컬 asset root가 필요합니다. 다른 튜토리얼의 공통 모듈은 필요하지 않습니다. 이 폴더 전체만 복사해도 로컬 helper와 config가 함께 갑니다. 런처는 일반 Python이고 자식 파이프라인을 설치본 `python.sh`로 실행합니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/137_replicator_replicator_scene_based_sdg
python3 run.py --check-config
python3 run.py --frames 6 --headless
# 화면을 보면서 실행
python3 run.py --frames 6 --output output_gui
# 저장 후 GUI를 120회 갱신하고 자동 종료
python3 run.py --frames 6 --steps 120 --output output_limited
```

`--steps`를 생략하면 정해진 프레임을 캡처하고 저장을 마친 후에도 GUI가 유지됩니다. 사용자가 창을 직접 닫으면 종료합니다. 대기 중에는 새 데이터셋 프레임을 생성하지 않습니다. `--steps N`은 **저장 완료 후 GUI를 갱신하는 횟수**이며 양수만 받습니다. 캡처 수를 정하는 `--frames`와 물리 스텝 수는 별개입니다. `--headless`는 GUI 대기를 건너뛰고 기존의 유한한 캡처가 끝나면 종료합니다.

기본 `output`이 있으면 새 `--output`을 지정합니다. 실제 적용한 설정은 `effective_config.json`에 보존됩니다. 외부 자산을 처음 여는 시간은 캡처 프레임 시간과 다를 수 있습니다. 데이터 캡처는 프레임 수만큼 끝나지만 원격 자산 다운로드가 오래 걸릴 수 있습니다.

필요한 자산은 5.1 root 아래 `/Isaac/Environments/Simple_Warehouse/full_warehouse.usd`, `/Isaac/Props/Forklift/forklift.usd`, `/Isaac/Environments/Simple_Warehouse/Props/SM_PaletteA_01.usd`, `S_TrafficCone.usd`, `SM_CardBoxD_04.usd`입니다. texture/mesh 참조도 해당 자산이 가리키는 위치에서 읽습니다. asset root는 `isaacsim.storage.native.get_assets_root_path()`로 결정됩니다.

## 실습 순서

1. `config.json`을 열어 resolution=512×512, num_frames=6, BasicWriter, class 이름 forklift/traffic_cone/pallet/cardbox를 확인합니다. CLI의 `--frames` 값이 JSON의 num_frames보다 우선합니다.
2. 실행 후 로그에서 창고 load, randomizer 등록, 상자 물리 낙하, 프레임 캡처가 순서대로 일어나는지 확인합니다. 배경이 없는 작은 임의 도형 예제가 아니라 지게차와 팔레트의 실제 참조 자산이 보여야 합니다.
3. 출력의 TopView/DriverView/PalletView 카메라별 RGB를 비교합니다. TopView는 높은 clipping 시작거리로 천장 너머의 작업 대상을 관찰하고, DriverView는 운전석 높이, PalletView는 팔레트를 향한 무작위 시점입니다.
4. 같은 프레임의 semantic label JSON과 bounding box 데이터에서 클래스 이름을 확인합니다. BasicWriter에 3D box, occlusion, distance_to_image_plane도 요청하므로 RGB 파일만 확인하고 완료로 판단하지 않습니다.
5. 두 번째 실행에서 `clear_previous_semantics`만 false로 바꾼 JSON 복사본을 사용합니다. 배경의 기존 의미 라벨까지 정답에 들어오는지 비교합니다. 별도 output을 사용합니다.

## 코드 읽는 순서와 API

Stage는 USD 장면 전체이고 `create_prim(usd_path=...)`는 외부 USD를 reference로 조합해 지게차/팔레트를 배치합니다. 파일 내용을 복사해서 정점으로 만드는 것이 아니라 원본 장면을 참조하므로 root와 그 아래 자산 URL이 모두 필요합니다. `Gf.Matrix4d`로 팔레트 오프셋을 지게차 좌표계에서 월드 좌표계로 변환합니다. 두 물체를 독립적으로 아무 곳에 놓는 randomization과 다릅니다.

`register_scatter_boxes`는 팔레트의 bounding box를 기준으로 scatter plane을 만들고 `scatter_2d(..., check_for_collisions=True)`로 상자끼리 겹치지 않게 배치합니다. AABB는 월드 축에 평행한 상자이고 OBB는 물체 방향을 고려한 상자입니다. 콘 randomizer는 지게차 OBB의 아래 모서리 중에서 위치를 고릅니다.

`simulate_falling_objects`는 World와 강체·충돌을 이용해 별도의 상자를 팔레트로 떨어뜨린 뒤 정착시킵니다. 이후 캡처 루프의 `delta_time=0.0`은 그 물리 상태를 고정합니다. `rep.trigger.on_frame`의 상자·조명·카메라 변화는 캡처마다, top camera는 4프레임마다, `randomize_cones` custom event는 코드에서 2프레임마다 발생합니다. Trigger는 OmniGraph에 기록된 실행 조건이며 일반 Python for문과 같은 시점에 항상 실행되는 것은 아닙니다.

Render product는 세 카메라의 렌더 요청입니다. 준비 중에는 `hydra_texture.set_updates_enabled(False)`로 불필요한 센서 렌더를 끄고 SDG 직전에 다시 켭니다. `BasicWriter.initialize(**writer_config)`가 어떤 정답을 저장할지 결정하고 모든 render product에 attach합니다. 종료 전 출력 큐를 기다린 뒤 detach/destroy합니다.

## writer 설정 확장

공식 `config_basic_writer.yaml`, `config_default_writer.json`, `config_kitti_writer.yaml`, `config_coco_writer.yaml`도 이 폴더에 포함합니다. 입문 런처는 JSON만 받습니다. YAML을 직접 사용하려면 설치 Python으로 `scene_based_sdg.py --config <절대 YAML 경로>`를 실행할 수 있지만, 먼저 YAML의 output_dir를 **새 절대경로**로 바꾸고 num_frames를 유한한 값으로 설정합니다. 이 직접 경로는 런처의 출력 충돌 검사를 거치지 않습니다. 직접 실행도 `--steps` 생략 시 GUI를 유지하며 `--steps N`으로 저장 후 GUI 갱신 횟수를 제한합니다. 기존 config의 `close_app_after_run` 값은 실행 시 `headless`와 명시적인 `--steps` 여부에 맞춰 결정됩니다.

CocoWriter는 `coco_categories`의 ID와 class 라벨 대응을, KittiWriter는 해당 데이터 형식의 라벨/색상 옵션을 요구합니다. 기본 writer_config와 다른 writer의 인자를 무작정 섞으면 초기화가 실패합니다. 이 로컬 구현도 외부 writer_config가 주어지면 기본 writer 인자를 비웁니다.

원문의 다음 단계인 TAO DetectNet V2 학습은 별도 TAO 환경·모델·학습 사양 파일이 필요한 후속 과정입니다. 여기서 생성한 데이터만으로 모델 학습이 자동 실행되지는 않습니다. Kitti 출력 검토 → TAO dataset-convert용 export spec 작성 → train용 spec과 모델 준비의 순서로 진행합니다. 링크의 오래된 모델/도구 버전과 Isaac Sim 버전을 혼동하지 않습니다.

## 관찰, 실험, 오류

성공 기준은 세 카메라에 지게차/팔레트가 보이고 class 매핑과 깊이/검출 정답이 실제 파일로 생기는 것입니다. **rt_subframes만 16→32**로 바꾸고 재배치된 상자/재질의 잔상과 캡처 시간을 비교합니다. 위치 random seed를 이 예제에서 고정하지 않으므로 두 실행의 픽셀 차이를 subframe 효과만으로 단정하면 안 됩니다.

자산을 열지 못하면 asset root와 5.1 경로를 확인합니다. dataset이 비었으면 writer 등록 이름, class 라벨, 카메라 시야를 확인합니다. `--check-config`는 JSON 구성을 확인할 뿐 GPU·원격 자산 실행 검증이 아닙니다. 복사한 NVIDIA 파일의 저작권/변경 사항은 `NOTICE.txt`와 `LICENSE-APACHE-2.0.txt`를 확인합니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
- [config scenarios](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html#config-scenarios)
- [domain randomization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html#domain-randomization)
- [running the script](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html#running-the-script)
- [next steps](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html#next-steps)
- [TAO 5.2 DetectNet V2 후속 학습 안내](https://docs.nvidia.com/tao/tao-toolkit-archive/5.2.0/text/object_detection/detectnet_v2.html)
