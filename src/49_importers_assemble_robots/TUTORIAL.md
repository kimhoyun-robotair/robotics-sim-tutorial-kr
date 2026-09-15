# 49. t118 · Robot Assembler로 UR10e에 Allegro hand 붙이기

권장 학습 순서 **49** · 로봇 자산 가져오기와 제작 · 출처 ID `t118`

Isaac Sim **5.1.0**의 native `RobotAssembler`로 실제 두 로봇 reference를 fixed joint로 연결한다. 이 패키지는 단순 부모 Xform 재배치를 조립이라고 부르지 않는다. 조립된 물리 연결은 Play 중에만 작동하며 solver가 양쪽의 상대 pose를 유지한다.

## 이 실습의 의도

UR10e의 말단 frame과 Allegro hand의 mount frame을 정렬하고 native assembler가 만든 fixed joint로 물리적으로 연결한다. 기본 실행은 조립·물리 preview·mount 거리 측정·조립 마무리와 stage 저장까지 수행하며, `--prepare-only`는 같은 조립을 GUI에서 직접 할 출발 장면을 준비한다. 프레임을 연결한 결과와 취소한 session-layer 변경을 비교해 로봇 조립의 저장 범위를 이해한다.

## 실행 후 확인할 것

- 기본 실행의 Play preview에서 `/World/ur10e/ee_link`와 `/World/allegro_hand/allegro_mount`가 떨어지거나 hand가 튀지 않는지 본다. hand의 방향도 정렬 상태에 맞는지 확인한다.
- preview가 끝나면 터미널의 `Measured mounting-frame separation, meters:`를 확인한다. 작은 분리 거리는 연결 유지의 관찰 근거이며, 코드가 허용 오차를 정해 자동 합격시키거나 모든 자세의 안정성을 시험하지는 않는다.
- 종료 전 저장된 `assembled.usda`와 `report.json`의 `fixed_joint_paths`를 확인하고 새 조립 연결이 어느 경로에 생겼는지 살펴본다. 원본 로봇의 fixed joint도 목록에 포함되므로 목록이 비어 있지 않다는 사실만으로 조립을 판정하지 않는다.
- `--prepare-only`는 두 reference 준비 후 사용자가 Begin Assembly부터 수행해야 한다. `--cancel`에서는 `report.json`의 `cancelled=true`와 조립 변경이 되돌아간 stage를 확인하며, 완성 hand 연결을 기대하지 않는다.
- 저장 결과를 다시 열어 Play하고 mount 연결이 유지되는지 확인한다. 기본 GUI는 preview와 저장 뒤 정지한 장면을 계속 열어 두므로 그 시점의 정지를 물리 연결 실패로 해석하지 않는다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.robot_setup.assembler`, 5.1 자산 루트가 필요하다. 입력은 `/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd` 및 `/Isaac/Robots/WonikRobotics/AllegroHand/allegro_hand_instanceable.usd`다. 원래 로봇 asset을 수정하지 않고 새 stage에서 reference한다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/49_importers_assemble_robots
"$ISAAC_SIM/python.sh" run.py
"$ISAAC_SIM/python.sh" run.py --prepare-only --output output/gui
"$ISAAC_SIM/python.sh" run.py --cancel --output output/cancelled
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 240회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다. 기본 GUI는 240회 조립 검증 후 결과를 저장하고 창을 유지한다.

새 output 폴더에 stage와 fixed joint 경로 보고서가 저장된다. native assembly 임시 layer도 output 폴더 안에서 생성한다. 기본 실행은 mount 간 실제 거리(m)를 출력하고, GUI 준비는 사용자가 닫을 때까지 기다린다. articulation이 변한 뒤의 모든 자세 안정성을 인증하는 실험은 아니다.

## native GUI 조립 순서

1. `--prepare-only`로 stage를 열고 **Tools > Robotics > Asset Editors > Robot Assembler**를 연다.
2. **Base Robot**은 `/World/ur10e`, **Attach Robot**은 `/World/allegro_hand`다. Robot Schema가 있는 자산을 선택해야 한다.
3. base **Attach Point**는 `/World/ur10e/ee_link`, hand의 Attach Point는 `/World/allegro_hand/allegro_mount`다. attach point는 Robot Link 또는 Reference Point frame이다. namespace는 `Gripper`로 둔다.
4. **Begin Assembly**를 눌러 mount가 일치하도록 배치한다. X/Y/Z 90도 버튼 또는 gizmo로 방향을 조정한다. 본 API 예제는 설치된 test와 같이 Z -90도 후 Y -90도를 적용한다.
5. **Assemble and Simulate**로 fixed joint 연결을 시험한다. 링크가 폭발적으로 튀거나 mount가 크게 떨어지지 않는지 관찰한다. 잘못됐으면 **Cancel Assemble**로 session-layer 변경을 되돌린다.
6. 만족하면 **End Simulation and Finish**를 누르고 stage를 이 패키지 output 아래 새 파일로 저장한다. 다시 열어 Play하여 assembly가 editor 재실행 없이 유지되는지 확인한다.
7. 변수 하나 실험: hand의 orientation을 Y축 90도만 바꿔 재조립하고 mount 접촉과 collider 중첩을 비교한다. 떨어진 두 body를 Play 순간 강제로 연결하면 큰 보정 힘이 생길 수 있다.

## API, layer, variant

`begin_assembly(stage, base, base_mount, attachment, attachment_mount, namespace, variant)`는 임시 session sublayer를 만들어 수정 사항을 격리한다. `assemble()`이 fixed joint를 만들고 붙는 로봇의 기존 world root joint를 비활성화하며 articulation root를 정리한다. `cancel_assembly()`는 수정 layer를 제거하고 `finish_assemble()`은 완성 결과를 stage/asset 구성에 반영한다.

**Stage Editing**은 두 reference를 현재 stage에서 연결하므로 원본 자산을 바꾸지 않는다. **Direct Asset editing**은 base asset을 직접 열었을 때 `configuration/<robot>_<namespace>_<attachment>.usd`를 만들고 variant set으로 구성 선택을 제공한다. configuration 파일 외에 원본 stage도 저장해야 variant 변경이 남는다. 본 패키지는 Stage Editing으로 실행한다.

고정 테이블 위 움직이지 않는 로봇은 테이블과의 물리 fixed joint가 필요하지 않을 수 있다. assembler는 움직이는 base와 arm 또는 arm과 gripper처럼 simulation 중 상대 위치를 유지할 때 쓴다. 이 연결은 USD 계층만으로 생기는 정적인 parent transform과 다르다.

## 문제 해결과 확인 범위

목록에 로봇이 없으면 RobotAPI와 robotLinks/robotJoints 관계를 확인한다. mount 경로가 없으면 같은 5.1 자산을 썼는지 확인한다. 조립 후 폭주하면 frame 정렬, 중첩 collider, 중복 world 고정 joint, 질량/관성을 본다. `--cancel`은 완료 assembly를 만들지 않는 취소 실습이다. 코드/CLI를 확인했으며 실제 물리 안정성·GUI 저장/reload는 미검증이다.

## 출처

[Isaac Sim 5.1 Robot Assembler](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html), [UI](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html#using-the-robot-assembler-tool), [API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html#robot-assembler-api). mount 경로와 회전은 설치된 `isaacsim.robot_setup.assembler/tests/test_robot_assembler.py`의 UR10e/Allegro 조합을 확인했다.
