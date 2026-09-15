# 178. 물체의 6D 자세를 학습하기 위한 합성 데이터

권장 학습 순서 **178** · 사용 중단 문서와 레거시 참고 · 출처 ID `t050`

공식 **Pose Estimation Synthetic Data Generation**의 native 워크플로다. 이 수업은 공식적으로 **DEPRECATED**이며 Isaac Sim **5.1.0**을 기준으로 한다. 이 패키지의 YAML은 실제 공식 생성기에 전달된다. 생성기와 `flying_distractors` 모듈은 실행할 때 설치본에서 **새 output/native 폴더로 복사**하므로 설치 원본을 수정하지 않는다. 다른 튜토리얼의 코드를 가져올 필요가 없다.

## 목표와 준비

cracker box와 power drill 주변에 날아다니는 방해 물체를 배치하고, **MESH 4장 + DOME 4장**을 생성한다. 6D pose는 위치 3개와 회전 3자유도를 뜻한다. 사진만으로 얻기 어려운 정확한 물체 자세를 시뮬레이터 장면에서 추출한다.

Linux, RTX GPU, Isaac Sim 5.1 전체 설치와 네이티브 PyTorch/YAML 환경이 필요하다. Isaac Sim assets root에서 `/Isaac/Props/YCB/Axis_Aligned/`, `/NVIDIA/Assets/Skies/`를 읽을 수 있어야 한다. CenterPose는 `config/centerpose_config.yaml`의 mug asset 경로도 필요하다. 원격 assets root 또는 설치된 동일 버전 로컬 asset pack을 설정한다. USD 물체, HDR 배경은 패키지에 포함하지 않는다.

```bash
cd src/178_replicator_replicator_pose_estimation
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
python3 run.py --writer dope --num-mesh 4 --num-dome 4 --headless --output output/dope
python3 run.py --writer centerpose --num-mesh 4 --num-dome 4 --headless --output output/centerpose
python3 run.py --writer ycbvideo --num-mesh 4 --num-dome 0 --headless --output output/ycb
```

`--headless`를 빼고 `--steps`도 생략하면 생성 중 UI를 볼 수 있고, 생성과 저장을 마친 뒤에도 직접 닫을 때까지 창이 유지된다. `--steps 120`은 저장 후 GUI 업데이트 120회 뒤 종료한다(`--steps`에는 양의 정수를 지정). `--num-mesh`와 `--num-dome`이 생성량을 결정하며 창을 유지하는 동안 추가 이미지는 생성하지 않는다. `--headless`는 기존처럼 지정한 데이터만 생성하고 종료한다. `--output`은 존재하지 않는 경로여야 한다. 저장된 PNG/JSON/MAT와 debug 영상도 함께 확인한다. 실행 기록 `command.json`과 사용된 설정 `native/config/`도 결과와 함께 남는다.

## 단계별 실습

1. `config/dope_config.yaml`의 `OBJECTS_TO_GENERATE`를 확인한다. `part_name`은 asset 파일명, `prim_type`은 USD 파일 안의 실제 prim 이름이다. 두 값이 같은지 추측하지 말고 asset을 GUI에서 열어 Stage 트리로 확인한다.
2. `WIDTH=HEIGHT=512`, `F_X=F_Y=768`, `MIN_DISTANCE=0.4`, `MAX_DISTANCE=1.4`를 확인한다. intrinsic 값과 카메라에 대한 물체 거리로 시야 안에 놓일 영역이 결정된다.
3. 첫 DOPE 명령을 실행한다. `output/dope/data/`의 RGB와 JSON을 찾아 `objects[].class`, `location`, `quaternion_xyzw`, `projected_cuboid`를 조사한다. `projected_cuboid`는 8개 꼭짓점과 중심점이 화면 어디에 찍혔는지 알려 준다. writer의 debug 그림과 겹쳐 비교한다.
4. MESH 전반부는 물체·도형과 sphere light 중심, DOME 후반부는 HDR dome 배경 중심이다. 배경과 방해 물체 가시성이 바뀌는지 확인한다. 카메라 밖 물체·가림 상태에 따라 writer가 저장을 건너뛸 수 있으므로 요청 프레임 수와 저장 레코드 수를 구분한다.
5. CenterPose를 실행하면 여러 mug가 같은 범주의 예시가 된다. DOPE의 특정 물체별 모델과 범주별 모델의 입력 차이를 확인한다. YCBVideo는 해당 writer의 좌표·파일 규약(MAT 포함)을 사용하므로 DOPE JSON 판독기를 그대로 쓰지 않는다.
6. 생성 중 사용된 `output/dope/native/pose_generation.py`에서 `_setup_collision_box`, `_setup_distractors`, `_setup_train_objects`, `__next__`를 차례로 읽는다. 아래 해설이 각 함수의 역할이다.

## 핵심 API와 좌표계

`World.get_physics_context().set_gravity(0)`는 방해 물체를 띄운다. 보이지 않는 **collision box**가 물체를 가두며 `apply_force_to_prims`가 힘을 가해 계속 움직인다. 물리적 충돌은 메시가 서로 관통하는 가짜 배경을 줄인다. 관심 물체는 충돌 때문에 화면 밖으로 나가지 않도록 운동을 별도로 제어한다.

USD `Xform`은 위치·회전·스케일을 가진 노드다. `ComputeLocalToWorldTransform`으로 카메라 rig 좌표와 world 좌표를 연결하고, `get_world_pose_from_relative`와 `get_random_world_pose_in_view`로 시야 안의 자세를 만든다. `set_world_pose`는 이 결과를 물체에 적용한다. 일반 USD 카메라는 앞이 **-Z**, 위가 **+Y**지만 이 설정의 `CAMERA_ROTATION: [180,0,0]`은 rig에 대해 카메라를 뒤집어 **+Z 전방, +Y 아래**의 영상 규약과 연결한다. quaternion 저장 순서는 JSON 필드 이름 `xyzw`를 기준으로 해석한다.

Replicator는 `rep.randomizer.register`, `rep.trigger.on_frame`으로 색·재질·조명 그래프를 만들고 `orchestrator.step`으로 실행한다. `rep.create.render_product`는 카메라 영상의 출력 대상을 만들며 `WriterRegistry.get("PoseWriter")`와 `attach`가 해당 영상과 ground truth를 파일 형식에 연결한다. local YAML은 초보자의 첫 실행 부담을 낮추려고 원본 MESH 400/150개를 12/8개, DOME 30/20개를 6/4개로 줄였다. 알고리즘·모델을 대체하지 않는다.

## 한 변수 실험, S3, 문제 해결

`dope_config.yaml`의 `NUM_MESH_SHAPES`만 12에서 24로 바꾸고 `--output output/dope_more_shapes`로 실행한다. 물체 가림 비율과 저장 레코드 수를 비교한다. 다른 YAML이나 광원 수는 함께 바꾸지 않는다.

S3 사용 시 DOPE writer만 지원한다. 본인 계정의 boto3 자격증명 체인을 환경 또는 마운트된 `~/.aws/credentials`로 준비한 뒤 `--use-s3 --endpoint https://YOUR_ENDPOINT --bucket YOUR_BUCKET`을 추가한다. 실행기는 실제 S3 쓰기를 수행하므로 먼저 로컬 결과의 클래스·좌표를 검증한다. 자격증명은 이 패키지나 command.json에 넣지 않는다.

asset 로딩 오류면 YAML의 경로와 assets root를 검사한다. 이름 오류면 `part_name/prim_type`을 확인한다. 메모리 부족이면 방해 물체 수와 프레임 수를 줄인다. 대규모 `num_mesh/num_dome > 1000`에서 성능이 저하될 수 있다는 공식 예제의 제한을 고려한다. 생성된 dataset이 있다는 사실만으로 pose 모델을 학습한 것은 아니다.

검증 범위: 문법·CLI 확인. RTX, asset 해석, writer별 결과와 S3 실행은 미검증이다.

`native_runner.py`는 출력 폴더의 원본 예제를 실행하고 정상 완료를 확인한 뒤 writer 저장을 기다리고 연결을 해제한다. 그 다음 GUI만 유지하며, 자산 초기화 실패나 실행 오류에서는 기다리지 않고 앱을 정리한다. 이 어댑터는 패키지 내부에 있고 Isaac Sim 설치본을 수정하지 않는다.

## 출처

- [Isaac Sim 5.1 Pose Estimation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_pose_estimation.html)
- [Collision box](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_pose_estimation.html#creating-a-collision-box), [Switching writers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_pose_estimation.html#switching-writers)
- YAML은 5.1 배포본 `standalone_examples/replicator/pose_generation/config/`에서 가져와 위 수량을 변경했다. NVIDIA copyright 헤더와 Apache-2.0 라이선스를 `LICENSE-NVIDIA-EXAMPLES.txt`에 보존했다.
