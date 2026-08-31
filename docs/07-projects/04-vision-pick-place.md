# 프로젝트 4: 시각 기반 pick-and-place cell

## 목표

커스텀 manipulator와 gripper를 구성하고 RGB-D camera로 대상 물체를 관측하다. Lula/RMPflow 또는 MoveIt 2로 충돌을 피하며 pick-and-place를 실행하고, Replicator로 perception dataset을 생성하다.

## 요구사항

- manipulator articulation, gripper, 작업대, bin 두 개, 물체 세 class를 포함하다.
- camera intrinsic/extrinsic과 optical frame을 기록하다.
- robot description/XRDF의 active joint, c-space, collision sphere를 검증하다.
- 접근, grasp, lift, transfer, place, retreat, recovery state를 분리하다.

## 1단계: robot을 구성하다

URDF 또는 USD asset을 가져온 뒤 joint limit·drive·gain을 검증하다. end-effector frame과 gripper open/close convention을 하나의 config로 관리하다. Lula Robot Description/XRDF Editor에서 collision sphere가 link를 충분히 덮되 지나치게 부풀지 않게 하다.

```yaml
robot:
  prim_path: /World/Cell/Robot
  end_effector_frame: tool0
  active_joints: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]
  gripper:
    open: [0.04, 0.04]
    closed: [0.0, 0.0]
```

## 2단계: motion generation을 검증하다

목표 pose를 바로 물체 grasp pose로 보내지 않고 pre-grasp와 retreat waypoint를 두다. RMPflow의 internal robot state와 USD articulation state가 어긋나지 않도록 reset 뒤 동기화하다.

```python
# API 이름은 선택한 5.1 motion generation example을 기준으로 구성하다.
articulation_controller.apply_action(action)
world.step(render=True)
```

각 state에는 timeout과 실패 transition을 두다.

```text
DETECT → PREGRASP → GRASP → LIFT → TRANSFER → PLACE → RETREAT
   └────────────── RECOVER ← collision/timeout/lost-object ─────┘
```

## 3단계: camera와 dataset을 만들다

camera calibration target으로 intrinsic/extrinsic을 검증한 뒤 randomization을 추가하다. light intensity·color temperature, object pose, distractor, material을 분포로 바꾸고 RGB, depth, instance segmentation, 2D bounding box를 저장하다.

```python
import omni.replicator.core as rep

output_dir = "/tmp/project-4-pick-place-sdg"
camera = rep.create.camera(position=(1.5, 1.5, 1.2), look_at=(0.0, 0.0, 0.4))
render_product = rep.create.render_product(camera, (640, 480))
writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(
    output_dir=output_dir,
    rgb=True,
    distance_to_image_plane=True,
    instance_segmentation=True,
    bounding_box_2d_tight=True,
)
writer.attach([render_product])
rep.orchestrator.run()
rep.orchestrator.wait_until_complete()
```

5.1 writer option 이름을 API에서 재확인하다. 100 frame pilot dataset으로 label 누락, depth unit, occlusion, 빈 frame을 검사한 뒤 규모를 늘리다.

## 4단계: ROS 2 또는 내부 perception을 연결하다

ROS 2를 선택하면 image, camera_info, depth, TF의 timestamp와 QoS를 맞추다. MoveIt 2를 선택하면 robot description과 planning group, controller joint order가 USD와 일치하는지 확인하다. 내부 Python perception을 선택하면 render product readback이 simulation step을 암묵적으로 지연시키는지 측정하다.

## 평가

물체 class별 30회 이상 시행하고 다음을 기록하다.

- detection 성공률
- grasp 성공률
- 전체 pick-place 성공률
- planning time과 execution time
- collision/contact peak
- 실패 state별 count

random seed와 초기 pose를 저장해 failure를 재실행하다. 물체가 gripper에 붙었다는 이유만으로 success로 보지 말고 지정 bin 내부에서 정지했는지 확인하다.

## 완료 조건

- 한 명령으로 scene load부터 10회 평가까지 실행되다.
- camera calibration과 TF가 수치로 검증되다.
- motion planner의 obstacle model과 visible obstacle이 일치하다.
- dataset manifest와 100-frame 품질 보고서를 제출하다.

## 출처

- [Tutorial 8: Generate Robot Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html)
- [Configuring RMPflow for a New Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)
- [Pick and Place Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html)
- [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
