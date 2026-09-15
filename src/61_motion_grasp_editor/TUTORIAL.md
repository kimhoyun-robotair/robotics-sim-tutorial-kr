# 61. t143 · Grasp Editor로 파지 데이터를 만들고 좌표 변환하기

권장 학습 순서 **61** · 로봇 제어와 동작 계획 · 출처 ID `t143`

이 패키지는 Isaac Sim **5.1.0**의 native Grasp Editor에서 Panda hand와 머그의 파지를 직접 작성하고, `compute_pose.py`에서 **실제로 export한** 파일을 공식 API로 읽어 world 목표 자세를 계산한다. grasp 목표 계산과 팔의 충돌 없는 경로 계획은 별개다. 이 실습은 motion planner를 실행하지 않는다.

## 이 실습의 의도

머그 기준의 손 자세와 손가락 관절값을 Grasp Editor에서 직접 작성하고, 그 상대 자세를 다른 물체 월드 자세에 재사용하는 방법을 익힌다. Panda hand와 mug의 기준 frame을 먼저 고정하는 이유는 파지 데이터를 저장한 뒤에도 같은 상대 관계로 복원하기 위해서다. `run.py`는 stage와 편집기를 열어 두는 launcher이며, 사용자의 Simulate·Export 조작 후 `compute_pose.py`를 별도로 실행해야 목표 자세 JSON이 생성된다.

## 실행 후 확인할 것

- **편집 대상과 기준**: Grasp Editor에서 실제 Panda hand articulation과 `/World/mug`를 선택하고, gripper frame이 `panda_hand`를 가리키는지 확인한다. 창만 열거나 headless 업데이트를 끝낸 상태에서는 파지가 작성되지 않는다.
- **물리 파지의 결과**: `Author a Grasp > Simulate` 후 손가락이 머그에 닿아 닫히고, 외력을 가하는 동안 머그가 유지되는지 본다. `Skip Sim`으로 저장한 자세와 사용자가 입력한 `Confidence`만으로 물리 파지 성공을 판정하지 않는다.
- **내보내기와 복원**: 직접 만든 `output/authored_grasps.yaml`에 파지 이름, 물체 기준 `position`/`orientation`, 열린/닫힌 관절값이 들어 있는지 확인한다. 같은 frame을 선택해 Import했을 때 작성한 손 자세가 복원되어야 한다.
- **좌표 변환**: 같은 `grasp_0`에 대해 object x를 0.5 m에서 0.6 m로만 바꾼 두 계산 결과를 비교한다. `target.json`과 `shifted.json`의 gripper `position[0]` 차이는 0.1 m이고, 물체 회전이 같으면 출력 `quaternion_wxyz`도 같아야 한다.
- **결과의 범위**: `compute_pose.py`의 `position`은 월드 위치, quaternion은 WXYZ 순서다. 이 출력은 그리퍼의 목표 자세이며, 로봇 팔이 그곳까지 충돌 없이 도달하거나 물체를 들어 올렸다는 실행 기록은 아니다.

## 준비: 독립적인 실습 stage

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.robot_setup.grasp_editor` extension이 필요하다. 공식 [Grasp_Editor_Tutorial_Stage.zip](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/4d1aeb9e29208ad4bf35f0a38d105e49/Grasp_Editor_Tutorial_Stage.zip)(약 3 MB)을 **이 패키지의 `input/`에** 내려받고 압축을 푼다. ZIP 안의 `Isaac/`와 `Library/` 상대 경로를 유지한다. 자산은 재배포하지 않으며 원본 공식 stage가 입력이다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/61_motion_grasp_editor
mkdir -p input output
# 다운로드한 ZIP을 input/에 둔 뒤
unzip -n input/Grasp_Editor_Tutorial_Stage.zip -d input
"$ISAAC_SIM/python.sh" run.py --stage input/Grasp_Editor_Tutorial_Stage/grasp_editor_tutorial.usd
```

`--steps`를 생략하면 launcher는 사용자가 닫을 때까지 GUI를 유지한다. 양수 `--steps N`은 앱 업데이트 N회 뒤 종료하며, GUI의 `--steps 0`도 무제한이다. headless에서는 양수 `--steps`를 지정해야 한다. 예전 `--frames`는 headless에서 `--steps`를 생략한 경우에만 제한값으로 사용하고 GUI 종료에는 관여하지 않는다. 음수와 headless의 0은 거부한다. 원본 stage를 저장하지 않으면 실험 중 추가한 physics 변경을 보존하지 않는다. 다른 로컬 튜토리얼은 필요 없다.

## 파지 작성 실습

1. **Tools > Robotics > Grasp Editor**를 연다. **Selection Frame**에서 Panda hand articulation과 `/World/mug` object를 선택한다. prim 경로가 다르면 Stage 우클릭 **Copy Prim Path**로 실제 경로를 복사한다. export는 `output/authored_grasps.yaml`의 절대 경로로 지정한다. **존재하는 파일을 지정하면 편집기가 새 파일로 덮어쓰므로 새 파일명을 사용한다.**
2. **Ready**를 누른다. mug에 USD RigidBodyAPI/CollisionAPI가 붙어 힘에 반응할 수 있게 된다. 이것은 모델 데이터 변경이다. Play 상태에서 물체가 사라진 것처럼 보이면 원문에 알려진 시각 문제이므로 Stop→Play를 시도한다.
3. **Select Frames of Reference**에서 mug는 `/World/mug`, gripper는 `panda_hand`의 기준 prim을 선택한다. **Finalize** 후에는 파일 전체에서 이 기준이 고정된다. 전체 Franka를 사용할 때도 gripper frame은 팔 base가 아니라 `panda_hand`다.
4. **Joint Settings**에서 `panda_finger_joint1`을 **Part of Gripper**로 체크한다. mimic으로 움직이는 반대 손가락을 별도 독립 DOF로 중복 제어하지 않는다. `Position When Open=0.04 m`, `Position When Closed=0.0 m`로 시작하고 `Grasp Speed=0.02 m/s`, `Max Effort Magnitude=10 N`으로 시험한다. 이 마지막 두 값은 비교 실험을 위한 시작값이며 성공을 보장하는 공식 상수가 아니다.
5. **Utils > Mask Collision**으로 배치 중 충돌을 잠시 가리고 mug 테두리/손잡이를 손가락 사이로 이동한다. **Show Physics Colliders**로 보이는 mesh와 collider가 일치하는지 확인한다.
6. **Author a Grasp > Simulate**를 눌러 손가락이 실제 접촉까지 닫히게 한다. 파지 시에는 mask가 해제된다. 접촉면/손가락 변형/머그 이탈 여부를 확인한다. 복잡한 coupling이나 부정확한 collider 때문에 시뮬레이션이 부적합하면 외부 제어로 자세를 맞추고 **Skip Sim**으로 export할 수 있으나, 이를 물리적으로 검증한 파지라고 기록하지 않는다.
7. **Add External Rigid Body Forces**에서 force 0.5 N, torque 0으로 시험한다. 각 축 ±방향의 힘이 가해져도 잡힘이 유지되는지 본다. force만 3 N으로 올려 동일 파지를 비교한다. 원문 영상의 0.5/3 N 결과가 모든 geometry/gain에 동일하게 적용되지는 않는다.
8. Export panel에서 Confidence를 자신의 평가값으로 입력하고 **Export**한다. 다른 접근 방향으로 두 번째 파지를 만들어 같은 파일에 순서대로 추가한다. Confidence는 UI에서 지정하는 평가값이며 자동 성공 확률 측정치가 아니다.
9. **Import** panel에서 export 파일을 읽고 `grasp_0`, `grasp_1`을 차례로 선택해 다시 시각화/시뮬레이션한다. import 시 collisions는 mask되며 frame 선택은 다시 정확히 해야 한다.

## 실제 export를 코드에서 사용하기

```bash
"$ISAAC_SIM/python.sh" compute_pose.py --grasp-file output/authored_grasps.yaml --name grasp_0 --object-position 0.5 0 0.2
"$ISAAC_SIM/python.sh" compute_pose.py --grasp-file output/authored_grasps.yaml --name grasp_0 --object-position 0.6 0 0.2 --output output/shifted.json
```

첫 결과 대비 object x만 0.1 m 증가했으므로 목표 gripper x도 0.1 m 증가해야 한다. 물체 quaternion은 WXYZ 순서의 단위 quaternion이며 기본값은 회전 없음이다. `--object-quaternion 0.70710678 0 0 0.70710678`로 물체를 90도 회전하면 grasp의 상대 offset도 회전한다. 결과 파일은 기존 파일을 덮어쓰지 않는다.

`import_grasps_from_file()`는 `GraspSpec`을 만들고 `get_grasp_names()`는 유효한 파지 이름을 반환한다. `compute_gripper_pose_from_rigid_body_pose()`는 object world pose와 파일의 상대 pose를 합성한다. 올바른 식은 `p_world_gripper = R_world_object @ p_object_gripper + p_world_object`다. 원문의 수식 괄호가 모호하므로 여기서는 설치된 API의 실제 연산을 따른다. 회전도 같은 순서로 합성한다.

## 파일 구조와 USD 개념

`format: isaac_grasp`, `format_version: 1.0` 아래 `grasps`가 이름별 데이터를 갖는다. `position`/`orientation`은 **물체 기준** gripper pose, `cspace_position`은 닫힌 접촉 관절값, `pregrasp_cspace_position`은 열린 값이다. `object_frame_link`/`gripper_frame_link`의 USD 경로는 의미를 설명하지만 import 시 자동 frame 선택에 사용되지 않는다. 비-USD planner는 이 경로를 이해하지 못한다.

USD의 Xform frame은 위치·회전을 가진 기준 좌표다. mesh 중심과 URDF end-effector frame은 서로 다를 수 있다. camera가 알려주는 물체 pose의 기준과 grasp 작성 frame이 다르면 그 차이만큼 목표도 틀어진다. 필요한 기준이 없으면 object 아래 Xform을 만들어 그 frame으로 정한다.

## 문제 해결과 확인 범위

Ready 실패는 articulation 선택·object prim·export 경로를 확인한다. 손가락은 움직이는데 물체가 안 잡히면 collider와 최대 힘을 본다. import 후 엉뚱한 곳에 나타나면 world/object frame과 WXYZ 순서를 확인한다. 문법/CLI와 API 소스를 확인했지만 실제 파지 접촉·export/import GUI·GPU 실행은 미검증이다.

## 출처

[Isaac Sim 5.1 Grasp Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html), [기준 frame 선택](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html#select-frames-of-reference), [작성한 파지 사용](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html#using-authored-grasps-in-isaac-sim). API 연산은 5.1 `exts/isaacsim.robot_setup.grasp_editor/isaacsim/robot_setup/grasp_editor/grasp_importer.py`로 확인했다.
