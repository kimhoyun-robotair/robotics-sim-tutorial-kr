# 44. 닫힌 고리가 있는 Robotiq gripper rigging

권장 학습 순서 **44** · 로봇 자산 가져오기와 제작 · 출처 ID `t128`

공식 Rig Closed-Loop Structures의 GUI native 실습이다. 시작 asset은 `/Isaac/Samples/Rigging/Gripper/Robotiq 2F-85/Robotiq_2F_85_edit.usd`이며 **폴더 이름의 공백**도 경로의 일부다. `run.py`가 이 asset 위에 로컬 layer를 만들고 `build_test_rig.py`가 실제 lift/reach 축과 잡기 시험용 cylinder를 추가한다.

## 준비와 실행

Isaac Sim **5.1.0**, RTX GPU, GUI, 위 공식 5.1 asset에 접근 가능한 assets root가 필요하다. CAD에서 다시 시작하려면 원문의 Onshape 문서를 가져와 Group Mates로 같은 강체에 속한 부품을 묶고 joint와 질량을 정의한다. 이 패키지는 이미 import된 공식 checkpoint에서 시작하므로 Onshape 계정 없이 진행할 수 있다.

```bash
cd src/44_robot_setup_rig_closed_loop_structures
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

GUI는 닫을 때까지 유지된다. `output/first/stage.usda`에 저장한다. Layers에서 로컬 root를 authoring layer로 선택한다. 원문 base/edit/config layer의 분리는 **원본 CAD 재수입과 실험용 물체를 분리해 관리**하는 방식이다. 이 실습에서도 물체 geometry 원본을 수정하지 않고 local override를 저장한다.

## joint 정렬·loop·접촉

1. Stage의 finger/knuckle joint와 body0/body1을 조사한다. Onshape import 후 joint 방향이 뒤집힌 네 joint는 **Local Rotation 0과 1의 X에 같은 180° offset**을 적용해 양쪽 frame을 함께 맞춘다. 한쪽만 돌리면 constraint가 초기 자세를 강제로 바꾼다.
2. `[left,right]_outer_finger_joint` limits=0..180°, `finger_joint`와 `right_outer_knuckle_joint`=0..75°로 둔다. 그 외 joint는 필요 없는 limit를 제거한다.
3. **Create → Physics → Physics Material → Rigid Body Material**, 이름 fingertip_material. static/dynamic friction=0.8, friction Combine Mode=Max. 좌우 inner finger의 실제 pad mesh에 연결한다. instance proxy라 편집할 수 없으면 해당 visual/collider reference의 Instanceable을 먼저 해제한다.
4. articulation은 **트리**여야 한다. 그러나 기계적 loop 자체를 없앨 필요는 없다. `left_inner_knuckle_joint`, `right_inner_knuckle_joint`의 **Physics → Joint → Exclude From Articulation**을 체크한다. 두 joint는 여전히 물리 constraint로 존재하며 maximal-coordinate solver 쪽에서 처리된다. drive/limit/저항이 없는 연결을 loop 절단 위치로 선택한 이유다.
5. 비교 checkpoint는 `/Isaac/Samples/Rigging/Gripper/Robotiq 2F-85_complete/`이다. 경고가 없어졌다는 사실만 보지 말고 양쪽 링크가 닫힌 기구를 유지하는지도 확인한다.

## 실제 시험 장치와 drive

6. **Window → Script Editor**에서 이 패키지 `build_test_rig.py`를 열고 Run. base_link 강체 하나를 찾아 `/TestRig/anchor`, `/TestRig/slide`, world fixed joint, lift(Z)·reach(X) prismatic joint를 만든다. limits=0..1 m, stiffness=damping=10000, max joint velocity=5 m/s이다. fixture axis는 gripper base의 local 방향을 따르므로 원본 자세가 바뀌면 방향도 확인한다.
7. 0.2 kg cylinder를 x=0.12, ground z=-0.1에 만든다. cylinder radius=0.025 m, height=0.2 m로 명시한 실습 입력이다. 실제 fingertip 사이로 위치를 조정한다. Python script는 같은 `/TestRig`가 이미 있으면 재생성을 거절한다.
8. `finger_joint`, `right_outer_knuckle_joint`에 Angular Drive 추가: stiffness=0, damping=5000, maxForce=180, Maximum Joint Velocity=130 deg/s. position 제어를 끈 속도/힘 제한 방식으로 잡는다. `[left,right]_outer_finger_joint` stiffness=0.05로 평행 손가락을 유지하는 spring을 표현한다.
9. cylinder mass를 0.2→2.5 kg로 바꿔 실험한다. source는 heavy load에서 Physics Scene 80 steps/s 이상으로 개선된 사례를 보여 준다. fixture는 80 Hz로 준비하지만 모든 장면에서 성공을 보장하지 않는다. 접촉 안정성·하중·슬립을 실제로 관찰한다. 평행 그립에서 힘이 과하면 source의 비교값 maxForce=5도 시험할 수 있다.
10. 한 구동 입력으로 합치려면 `right_outer_knuckle_joint`의 기존 drive를 제거하거나 0으로 만들고 **+ Add → Physics → Mimic Joint**. reference=finger_joint, gearing=-1이다. reference drive와 mimic drive를 동시에 경쟁시키지 않는다. 이 1DOF joint에서 UI rotX 표시와 실제 revolute axis가 다를 수 있다.
11. eye → **Show By Type → Physics → Colliders → All**로 fingertip 근사를 본다. 필요한 곳은 Convex Decomposition으로 바꾸고, articulation의 **Self-Collision Enabled**를 켜 finger끼리 실제 접촉하는지 확인한다. 인접 joint로 연결된 body 간 collision filter도 고려한다.
12. **Window → Graph Editors → Action Graph**에서 완성 checkpoint의 `/World/Gripper_Controller`를 열어 boolean 입력이 joint target 속도 부호를 어떻게 바꾸는지 본다. 자기 stage에서 같은 속도/힘 제한 방식을 유지하려면 완성 graph를 복사해 root/body/joint 경로를 자신의 prim으로 연결하고, 최종적으로 쓰는 속도 target의 부호를 확인한다. **Tools → Robotics → OmniGraph Controllers → Open Loop Gripper**는 별도의 position 명령 기반 도구이므로 source의 stiffness=0인 force-driven graph와 같은 것으로 취급하지 않는다. 열기/닫기, lift/reach를 각각 시험한다.

## 저장·해설·실험

USD **layer**는 같은 prim에 대한 의견을 겹치는 방식이다. geometry, 물리 수정, 시험 장치는 별개 layer에 둘 수 있다. 여기서는 local root에만 수정하며 원본 edit layer로 drag하여 원격 asset을 변경하지 않는다. 필요하면 local 폴더에 별도 physics edit layer를 만든 뒤 원하는 prim opinion을 그쪽으로 이동한다.

`UsdPhysics.FixedJoint/PrismaticJoint`는 fixture의 연결을 실제 body relationship으로 만든다. `DriveAPI`는 목표 추종, `PhysxJointAPI`는 max velocity, `MassAPI`는 하중, `PhysxSceneAPI`는 step frequency를 설정한다. **Exclude From Articulation**은 joint 삭제가 아니므로 운동학 tree와 실제 폐쇄 기구를 함께 표현할 수 있다.

한 변수 비교는 80→120 Hz만 바꾸고 같은 질량·gain에서 slip을 관찰하는 것이다. 손가락이 튀면 loop, local frame, initial collider 겹침부터 확인한다. Physics Inspector를 이용한 경우 일반 Play 전에 도구를 닫는다. 검증 범위: 문법·CLI·asset URL 접근. 실제 grasp/loop 안정성과 graph 제어는 미검증이다.

## 출처

- [Isaac Sim 5.1 Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Breaking the loop](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html#breaking-the-articulation-loop), [Mimic joint](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html#adding-mimic-joint)
- [공식 수업의 Onshape 원본](https://cad.onshape.com/documents/02712153b53a69118b4e5c99/w/e4160a7cfa8bb14f2585a92f/e/6d63d85251b40eee71da6b56)
