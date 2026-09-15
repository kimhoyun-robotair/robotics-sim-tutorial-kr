# 53. t135 · Lula Robot Description과 XRDF를 직접 작성하기

권장 학습 순서 **53** · 로봇 제어와 동작 계획 · 출처 ID `t135`

Isaac Sim **5.1.0**의 native **Lula Robot Description Editor**로 Franka의 제어 관절과 충돌 구를 정하고 Lula YAML 및 cuMotion XRDF를 내보낸다. 이 패키지의 `run.py`는 편집할 non-instanceable 로봇 reference를 준비한다. 파일 작성·구 편집은 공식 UI에서 사용자가 수행한다. 내보낸 파일이 없는 상태에서 모션 계획 완료로 표시하지 않는다.

## 준비와 시작

Isaac Sim 5.1, RTX GPU/드라이버와 5.1 자산 팩이 필요하다. 사용하는 로봇은 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`다. extension 이름은 `isaacsim.robot_setup.xrdf_editor`다. 기존 다른 패키지나 root asset을 참조하지 않는다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/53_motion_manipulators_robot_description_editor
mkdir -p output
"$ISAAC_SIM/python.sh" run.py
# 자동 구동 환경에서 창 초기화만 제한적으로 실행할 때
"$ISAAC_SIM/python.sh" run.py --headless --steps 120
```

`--steps`를 생략하면 창을 닫을 때까지 계속 실행한다. 양수 `--steps N`을 지정하면 앱 업데이트 N회 뒤 종료하며, GUI의 `--steps 0`도 무제한이다. headless에서는 양수 `--steps`를 지정해야 한다. 예전 `--frames`는 headless에서 `--steps`를 생략한 경우에만 제한값으로 사용하고 GUI 종료에는 관여하지 않는다. 음수와 headless의 0은 거부한다. headless 120회 업데이트는 **편집 실습을 수행하지 않는다**. 원본 USD를 직접 여는 대신 `/World/Franka`에 reference한다. instanceable 링크는 편집이 가능하도록 이 stage의 override로 해제한다.

## 이 파일이 필요한 이유

URDF는 링크·관절 연결과 형상을 설명하지만, planner가 어떤 관절을 제어할지 또는 충돌 회피에 어떤 근사 형상을 쓸지는 별도 계약이다. **c-space**는 선택한 관절 위치를 좌표로 하는 공간이다. Franka의 팔 7축을 Active로 지정하고 gripper는 Fixed로 가정하면 planner는 손가락 개폐를 직접 제어하지 않는다.

Lula `robot_description.yaml`은 active joint 이름·기본 자세·fixed joint 가정·링크별 collision sphere를 제공한다. IK/trajectory처럼 외부 장애물을 다루지 않는 알고리즘에는 sphere가 필수가 아니다. RMPflow에 sphere를 생략하면 외부 장애물 회피를 기대할 수 없다. 여기서 **Fixed**는 USD의 joint 타입을 바꾸는 것이 아니라 planner의 가정이다.

## 단계별 작성

1. 창에서 **Tools > Robotics > Lula Robot Description Editor**를 연다. timeline이 멈춰 있으면 **Play**를 누른다. **Selection Panel > Select Articulation**에서 `/World/Franka`에 해당하는 articulation을 선택한다.
2. **Set Joint Properties**에서 `panda_joint1`~`panda_joint7`은 **Active**, 손가락 관절은 **Fixed**로 둔다. 최소 1개 Active가 필요하다. 원문 Set Joint Properties의 일부 문장은 Fixed/Active가 뒤바뀐 오기가 있으므로 문서 앞쪽의 정의와 실제 제어 의미를 따른다.
3. 팔의 default joint position을 `[0, -0.7854, 0, -2.3562, 0, 1.5708, 0.7854]` rad로, 존재하는 손가락 joint는 열린 값 `0.04` m로 설정한다. 관절 limit 안인지 UI에서 확인한다. gripper가 열린 최외곽을 충돌 구로 덮으면 닫힐 때도 그 범위 안에 있게 된다. acceleration/jerk limit는 로봇 사양에 맞게 입력한다. 이 패키지는 확인되지 않은 실제 로봇 limit를 만들어 제공하지 않는다.
4. **Select Link**에서 `panda_link4`를 선택하고 **Link Sphere Editor > Add Sphere**로 구를 하나 추가한다. 반지름 0.05 m에서 시작해 해당 링크의 보이는 mesh 범위에 맞춘다. Stage의 구 prim을 이동하면 **링크 원점 기준** 상대 위치가 바뀐다.
5. 같은 링크에 두 번째 구를 만들고 **Connect Spheres**에서 두 구 사이에 3개를 보간한다. 단순 원통 링크를 적은 구로 덮는 방법이다. robot visibility를 꺼 구 배치를 확인하고 Undo/Redo를 한 번씩 해 본다.
6. 다른 링크에서 mesh를 선택하고 **Generate Spheres** 수를 8로 설정해 preview를 확인한 뒤 생성한다. 여러 mesh가 있으면 각각 확인한다. 자동 생성은 watertight triangle mesh가 전제이므로 실패하면 Add/Connect 방식으로 채운다. 모든 링크와 gripper의 주요 외곽을 같은 방식으로 덮는다.
7. **Export To File > Export to Lula Robot Description File**에 이 패키지의 `output/franka_description.yaml` 절대 경로를 입력하고 **Save**한다. 실제 파일에서 cspace가 팔 7축인지, fixed finger 값, 링크별 sphere 좌표/반지름이 기록됐는지 확인한다.
8. **Export to File > Export to cuMotion XRDF**에 `output/franka.xrdf`를 지정한다. `.yaml`도 가능하다. YAML과 XRDF를 별개 파일로 보관한다.
9. 구 하나의 radius만 10% 키우고 새 이름으로 export한다. 이전 파일과 비교하여 어느 링크의 sphere 값만 달라졌는지 확인한다. 기존 파일을 덮어쓰려면 먼저 자신의 실험 결과를 보관한다.

## XRDF import/merge 실습

XRDF는 Lula description보다 많은 데이터를 담는다. editor가 새로 생성하는 파일은 collision/self_collision에 같은 sphere 그룹을 쓰고, self-collision에서 부모 및 같은 부모의 링크를 제외한다. **Tool Frames와 Modifiers는 새로 작성하지 않는다.**

1. **Import From File > Import Lula Robot Description File**로 자신이 만든 YAML을 불러와 active joint와 sphere가 복원되는지 확인한다. import는 편집기 상태를 교체한다.
2. **Import XRDF File**로 XRDF를 읽는다. 형식 1.0을 가정하며 collision group의 sphere를 가져온다. tool frames, modifiers, self_collision 설정을 UI에서 모두 편집할 수 있다고 가정하지 않는다.
3. 기존 XRDF 경로로 export할 때 나타나는 **Merge With Existing XRDF**를 사용하면 기존 tool frames/modifiers를 보존한다. self_collision geometry가 collision geometry와 같을 때 ignore 설정을 보존하며, 이번 editor에 없는 frame의 sphere도 유지한다. 결과 파일을 텍스트로 비교하여 보존 여부를 확인한다.

## USD/API와 막힐 때

USD **reference**는 원본 자산을 합성해 가져오는 기능이고 **prim**은 `/World/Franka/panda_link4` 같은 객체다. 구의 상대 좌표를 링크 아래에 저장해야 관절이 움직일 때 구도 같은 링크를 따라간다. scene의 Physics collider와 Lula collision sphere는 다른 표현이며 하나를 만들었다고 다른 하나가 대체되지 않는다.

`add_reference_to_stage()`가 로봇을 장면에 추가하고 `SetInstanceable(False)`는 편집 불가능한 공유 인스턴스를 해제한다. `World.reset()` 이후 articulation을 선택할 수 있다. 로봇이 목록에 없으면 Play, ArticulationRootAPI, instanceable 여부를 확인한다. Save 비활성화는 경로·확장자·Active joint 개수를 확인한다. 자동 구 생성 오류는 mesh 폐곡면 여부를 확인하고 수동으로 배치한다. 본 변경에서는 UI 편집/exports의 실제 GPU 실행은 미검증이다.

## 출처

[Isaac Sim 5.1 Lula Robot Description and XRDF Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html), [collision sphere](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html#adding-collision-spheres), [export/import](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_robot_description_editor.html#exporting-configuration-files). 실제 extension 이름은 5.1 `exts/isaacsim.robot_setup.xrdf_editor/config/extension.toml`로 확인했다.
