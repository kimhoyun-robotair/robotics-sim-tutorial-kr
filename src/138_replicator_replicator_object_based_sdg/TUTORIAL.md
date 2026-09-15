# 138. 물체 중심 SDG: 충돌 공간, 방해 물체, 모션 블러

권장 학습 순서 **138** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t039`

이 패키지는 공식 Object Based Synthetic Dataset Generation의 실제 5.1 코드와 helper를 포함합니다. YCB pudding box·mustard bottle, 물리 방해 물체, 보이지 않는 충돌 벽, 목표를 바라보는 여러 카메라, 색/조명/배경 이벤트, PathTracing motion blur가 모두 원래 파이프라인으로 실행됩니다. 입문 config는 방해 물체 수와 카메라 수를 낮췄으며 BasicWriter로 RGB·분할·상자·깊이부터 관찰합니다.

## 준비와 명령

Isaac Sim 5.1.0 전체 설치, 지원 RTX GPU/드라이버, 충분한 GPU 메모리와 디스크가 필요합니다. 5.1 asset root에 YCB와 창고 Props 및 배경 텍스처가 있어야 합니다. 처음 실행은 서버에서 자산을 읽으므로 네트워크/로컬 미러 상태를 확인합니다. 이 패키지는 로컬 helper를 포함해 다른 src 패키지를 요구하지 않습니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/138_replicator_replicator_object_based_sdg
python3 run.py --check-config
python3 run.py --headless --frames 6
# 뷰포트 관찰
python3 run.py --frames 6 --output output_gui
# 저장 후 GUI를 120회 갱신하고 자동 종료
python3 run.py --frames 6 --steps 120 --output output_limited
```

`--steps`를 생략하면 정해진 프레임을 캡처하고 저장을 마친 후에도 GUI가 유지됩니다. 사용자가 창을 직접 닫으면 종료합니다. 대기 중에는 새 데이터셋 프레임을 생성하지 않습니다. `--steps N`은 **저장 완료 후 GUI를 갱신하는 횟수**이며 양수만 받습니다. 캡처 수를 정하는 `--frames`와 물리 스텝 수는 별개입니다. `--headless`는 GUI 대기를 건너뛰고 기존의 유한한 캡처가 끝나면 종료합니다.

`--frames 6`은 시뮬레이션 6 update가 아니라 캡처 시점 6개입니다. 카메라는 2대이므로 RGB는 일반적으로 12개입니다. writer 종류와 skip 정책에 따라 annotation 파일 수는 다를 수 있습니다. 기존 output은 덮어쓰지 않으며 effective_config.json을 기록합니다. 매 5번째 프레임(0 포함)은 PathTracing motion blur여서 첫 프레임부터 렌더 비용이 큽니다.

## 구성을 읽고 실행하기

1. `config.json`의 `working_area_size=[4,4,3]`을 확인합니다. 보이지 않는 여섯 벽은 물체가 공간 밖으로 나가지 않게 하는 **CollisionAPI** 형상입니다. invisible이어도 physics collision은 남습니다.
2. `labeled_assets_and_properties`에는 `/Isaac/Props/YCB/Axis_Aligned/008_pudding_box.usd`와 `/Isaac/Props/YCB/Axis_Aligned_Physics/006_mustard_bottle.usd`가 각각 3개입니다. 두 경로의 Physics 포함 여부가 달라도 helper가 필요한 강체/충돌을 보강합니다. `floating=true`는 중력 사용 방식에 영향을 주며 물체가 고정되어 있다는 뜻은 아닙니다.
3. shape distractor=40, mesh distractor=12를 확인합니다. distractor는 그림을 복잡하게 만드는 방해 물체이며 목표 class의 정답을 무작정 붙이지 않습니다. 원문 기본값 350/75는 부하가 훨씬 크므로 첫 실행에서 바로 쓰지 않습니다.
4. 출력 RGB와 semantic label JSON을 대조합니다. target class가 비어 있다면 학습 정답으로 쓸 수 있는 캡처인지 먼저 판단합니다. 가까운 카메라는 작은 물체의 검출에 유리하지만 가림/잘림도 생깁니다.
5. 6프레임에서 camera randomization은 0,3번에, light는 0,5번에 발생합니다. 렌더 로그에서 사건 간격을 확인하고 motion blur 프레임과 일반 프레임의 차이를 관찰합니다.

## API와 처리 순서

USD prim의 xformOp는 위치·회전·배율을 저장합니다. `UsdPhysics.CollisionAPI`는 충돌 가능 표면, `RigidBodyAPI`는 움직이는 물체를 정의합니다. mesh collision approximation은 렌더 삼각형 그대로 충돌 계산하는 비용과 정확도 사이의 선택입니다. PhysX scene-query overlap은 영역과 겹치는 강체를 찾으며, 바닥 bounce 영역에서는 속도를 위로 바꾸어 물체를 다시 섞습니다.

`object_based_sdg_utils.py`를 먼저 읽어 transform, collider/rigid body, working area, random pose, render update 함수를 확인합니다. `object_based_sdg.py`는 이를 사용해 자산을 생성한 다음 camera collider로 물체가 카메라와 겹친 상태를 잠깐 해소합니다. USD/PhysX 직접 조작과 Replicator의 이벤트 그래프가 함께 쓰이는 이유입니다.

카메라는 임의 위치에서 임의의 labeled asset을 바라봅니다. `camera_distance_to_target_min_max`는 시야 크기와 occlusion을 바꾸고 `camera_look_at_target_offset`은 표적 중심만 찍지 않도록 변화를 줍니다. 10프레임마다 물체를 중심 방향으로 당기는 속도, 15프레임마다 shape color, 17프레임마다 부유 distractor 속도, 25프레임마다 dome 배경을 바꾸는 공식 주기를 유지했습니다.

Motion blur는 멈춘 물체에 필터를 바르는 것이 아니라 짧은 노출 구간 동안 물리를 진행시키고 여러 PathTracing sub sample을 적분합니다. `capture_with_motion_blur_and_pathtracing`는 렌더 모드·physics step과 spp 설정을 조절하고 복구합니다. `rt_subframes`와 motion-blur sample 수는 서로 다른 값입니다. 일반 캡처의 delta_time=0과 blur 노출 중 시간 진행을 구분합니다.

`disable_render_products_between_captures=true`는 다음 캡처를 기다리는 동안 센서 렌더 비용을 줄입니다. 시뮬레이션은 계속 진행되며 capture 직전에 다시 켭니다. backend 쓰기는 비동기이므로 `wait_until_complete()` 후에만 종료합니다.

## 다른 writer와 실물 스캔 자산

공식 `object_based_sdg_config.yaml`, `object_based_sdg_dope_config.yaml`, `object_based_sdg_centerpose_config.yaml`을 포함합니다. 기본 전체 PoseWriter 설정은 원본 Python의 config에서도 읽을 수 있습니다. 설치 Python으로 `object_based_sdg.py --config <설정 경로>`를 직접 실행해도 `--steps` 생략 시 GUI를 유지하며, `--steps N`으로 저장 후 GUI 갱신 횟수를 제한할 수 있습니다. 직접 실행에서는 새 출력 경로를 설정 파일에 직접 지정해야 합니다. `writer_type`과 `writer_kwargs`는 함께 바꿔야 합니다. DOPE/CenterPose는 각 포즈 학습기의 클래스/키포인트·카메라 규약을 맞춰야 하며 BasicWriter JSON 이름만 변경한다고 호환되지 않습니다.

실물 스캔 USD를 사용하려면 AR Code 같은 도구에서 확보한 **본인 자산의 실제 USD 경로**를 config의 url로 바꾸고 label을 정합니다. 파일을 열어 metersPerUnit, upAxis, pivot, mesh 크기와 재질을 먼저 확인합니다. 변환 단위가 잘못되면 카메라 거리/충돌 공간에 비해 너무 크거나 작아집니다. 스캔 자체와 모델 학습은 이 패키지가 대신 생성하지 않습니다.

원문의 SyntheticaDETR는 이와 같은 합성 데이터로 훈련된 객체 검출 모델 사례입니다. NGC 모델 다운로드와 Isaac ROS RT-DETR 추론은 별도 환경입니다. 이 패키지 실행이 해당 모델 재학습이나 실세계 성능 재현을 의미하지 않습니다. 모델 페이지와 ROS 설명 링크는 출처에 제공합니다.

## 성공 기준과 한 가지 변경

RGB에서 YCB 물체가 두 카메라에 관찰되고 pudding_box/mustard_bottle label과 bbox/depth가 저장되어야 합니다. **shape_distractors_num만 40→80**으로 바꾼 config를 새 output으로 실행해 표적의 가림과 프레임 시간을 비교합니다. 메모리가 부족하면 해상도·카메라·방해 물체 수 중 하나만 줄여 원인을 분리합니다. 배경/재질이 검으면 asset root와 관련 texture 참조를 확인합니다. `--check-config`·compile 검사는 PhysX/렌더 성공 증거가 아닙니다. 원본 출처/라이선스는 NOTICE와 Apache-2.0 파일에 있습니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Object Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html)
- [util functions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#util-functions)
- [randomizers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#randomizers)
- [sdg loop](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#sdg-loop)
- [motion blur](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#motion-blur)
- [performance optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#performance-optimization)
- [syntheticadetr](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_object_based_sdg.html#syntheticadetr)
- [NGC SyntheticaDETR 모델](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/isaac/models/synthetica_detr)
- [Isaac ROS RT-DETR](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_object_detection/isaac_ros_rtdetr/index.html)
