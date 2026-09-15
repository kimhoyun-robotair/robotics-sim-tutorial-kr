# 168. Antipodal grasp 후보를 만들고 실제 물리로 평가하기

권장 학습 순서 **168** · 고급 데이터 생성과 외부 시스템 통합 · 출처 ID `t075`

## 기대 결과와 준비

xArm gripper가 soup can 주위의 다섯 grasp 후보에서 손가락을 닫고, 각 후보의 실제 gripper 상태를 `capture_*.yaml`에 남깁니다. 5.1의 저장 결과는 gripper 상태 기록입니다. 파일이 생겼다는 이유만으로 안정적인 집기 성공/실패 label을 자동 판정하지 않습니다.

Isaac Sim 5.1, RTX GPU와 드라이버, `isaacsim.replicator.grasping` 및 GUI를 쓸 경우 `isaacsim.replicator.grasping.ui`가 필요합니다. sampler는 `libspatialindex`를 사용합니다. Ubuntu에 라이브러리가 없다면 시스템 관리 방식에 맞게 `libspatialindex-dev`를 설치합니다. 이 패키지는 라이브러리 설치를 실행하지 않습니다. gripper/물체/rigid body가 들어 있는 외부 5.1 Assets 장면은 다음 파일입니다.

`https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Stage/sdg_grasping_xarm.usd`

오프라인 5.1 자산팩이 있다면 `--scene /절대경로/sdg_grasping_xarm.usd`로 바꿉니다. cloud 모델, ROS, 다른 로컬 튜토리얼 패키지는 필요하지 않습니다. 아래 명령은 이 패키지 디렉터리에서 실행합니다.

```bash
python3 run.py --help
/home/hoyunkim/isaacsim/python.sh run.py --headless --samples 5 --steps 10000 --output output/grasps_01
```

설치 경로를 자신의 환경에 맞춥니다. GUI 관찰은 `--headless --steps 10000`을 모두 빼면 됩니다. 이 standalone은 공식 standalone 예제와 동일한 GraspingManager API 흐름을 사용하되 설정을 패키지 안에 두고, 선택적으로 실행 횟수를 제한하며, 출력 덮어쓰기를 거부합니다. GUI는 기본적으로 평가가 끝난 뒤에도 사용자가 창을 닫을 때까지 유지됩니다. 아래 native UI 실습으로도 직접 조작할 수 있습니다.

## API 흐름과 설정 해설

1. `SimulationApp`을 먼저 시작한 다음 extension을 켜고 stage를 엽니다. Kit가 초기화되기 전에 `omni`를 import하면 실패할 수 있으므로 순서가 중요합니다.
2. `GraspingManager.load_config()`로 `grasp_config.yaml`을 읽습니다. `gripper_path`는 `/World/Grippers/xarm_gripper`, `object_path`는 `/World/Objects/_05_tomato_soup_can`입니다. USD prim 주소와 USD 파일 주소는 다릅니다. joint 경로는 같은 gripper 계층의 실제 joint를 가리켜야 합니다.
3. `joint_pregrasp_states`의 0은 손가락을 연 초기 상태입니다. Close phase는 구동 joint 목표 48도, 시간 간격 1/60초, 32 step으로 약 0.533초 동안 닫습니다. 다른 mimic joint는 기계적 연결에 의해 따라갑니다. 주어진 값은 이 xArm 장면의 joint 정의를 전제로 하며 임의 gripper에 그대로 적용하지 않습니다.
4. `sampler_type=antipodal`은 물체 양쪽의 대응 접촉점을 찾습니다. aperture=0.08 m는 최대 입 벌림, standoff=0.17 m는 접근 위치의 여유 거리, grasp_align_axis와 approach_direction은 gripper 로컬 축입니다. world 위치와 섞으면 후보가 옆으로 돌아갑니다. `random_seed=12`는 표본을 재현하기 위한 seed입니다.
5. `generate_grasp_poses()` 후 `get_grasp_poses(in_world_frame=True)`로 물리 실행에 필요한 세계 좌표 자세를 받습니다. `store_initial_gripper_pose()`는 종료 후 복귀용입니다. `evaluate_grasp_poses()`는 coroutine이므로 Kit update를 진행하면서 기다리고 `task.result()`로 내부 예외를 다시 받습니다.
6. 결과 YAML 수가 실제 평가 후보 수와 같아야 합니다. `summary.json`에 sampled/evaluated 수와 실제 파일 이름을 기록합니다. `--steps`는 물리 timestep 수가 아니라 평가 대기와 완료 후 GUI 관찰을 합한 Kit update 최대 횟수입니다. 생략한 GUI는 창을 직접 닫을 때까지 유지하며, headless에서 생략하면 평가 대기를 10000회로 제한합니다. 후보 수와 저장 파일 수는 `--samples`로 결정되고, 관찰하는 동안 추가 평가·저장을 반복하지 않습니다. 물리 길이는 phase의 dt/steps가 결정합니다.

## 동일 동작을 native GUI로 익히기

1. `./isaac-sim.sh`를 실행하고 Content Browser에서 위 USD를 엽니다. `Tools > Replicator > Grasping`을 선택합니다. UI가 없으면 두 grasping 확장을 켭니다.
2. Config의 File Path에 이 패키지 `grasp_config.yaml` 절대 경로를 넣고 Load합니다. Gripper의 Path와 drive joint가 맞는지 확인합니다. Object Path에서 soup can을 선택합니다.
3. Grasp Pose Sampler에서 aperture 0.08, standoff 0.17, 후보 5, 방향 수 1을 확인하고 후보를 생성합니다. Grasp Poses에서 world/object-local 표시를 번갈아 보고 후보를 하나씩 넘깁니다. Trimesh 표시로 실제 sampler가 읽는 물체 표면을 확인합니다.
4. Grasp Phases에서 Close만 단독 실행해 joint가 닫히는지 확인합니다. 복잡한 작업은 Open/Close/Lift처럼 여러 phase를 순서대로 둘 수 있지만 올림은 gripper 구동/이동 정의까지 구성해야 합니다. 이름만 Lift로 바꾸면 자동으로 들어 올려지지 않습니다.
5. Workflow의 Number of Grasps Samples를 5 또는 -1(전체), Output Path를 새 `output/gui_01`로 설정하고 Overwrite Results를 끕니다. Render each simulation step을 켜고 Start Workflow합니다.
6. Simulation의 Simulate using timeline은 앱 timeline을 진행합니다. 직접 stepping은 해당 physics scene을 평가하는 데 사용합니다. Isolated physics scene은 별도 PhysicsScene Prim과 소유권 범위를 지정할 때 쓰며, standalone에서는 `--physics-scene /World/physicsScene`을 해당 Prim이 실제 존재할 때만 사용합니다. timeline 모드에서는 isolation 의미가 달라집니다.
7. Config Includes에서 Generated Grasp Poses를 포함해 새 YAML에 저장하면 같은 후보를 공유할 수 있습니다. overwrite를 끄고 원본을 보존합니다.

## 실험과 문제 해결

한 변수 실험은 `gripper_maximum_aperture`만 0.08→0.03 m로 줄여 새 output으로 실행하는 것입니다. 물체 폭이 aperture보다 크면 유효 후보가 줄거나 0이 될 수 있습니다. 이는 sampler 실패를 감추지 않고 보고해야 하는 결과입니다. 초기 장면 물체는 중력이 꺼져 있으므로 중력을 켠 다른 조건의 grasp 안정성을 이 결과에서 추론하지 않습니다.

libspatialindex 오류는 GPU 문제와 다릅니다. 자산 로딩 실패는 URL/로컬 자산팩을 확인합니다. 후보가 없으면 collider/mesh, 입 벌림, 접근 축과 standoff를 확인합니다. 관절이 움직이지 않으면 그 joint에 drive가 있는지와 phase에 포함했는지 확인합니다. `--steps` 초과는 부분 출력을 남기며 완료로 표시하지 않습니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [설정과 파이프라인](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html#overview)
- [GUI 단계](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html#ui-window-overview)
- [YAML 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html#configuration-file-example)
- [GraspingManager 코드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html#code-example)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
