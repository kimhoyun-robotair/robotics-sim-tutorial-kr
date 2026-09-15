# 60. t142 · Surface Gripper의 접촉·흡착·해제

권장 학습 순서 **60** · 로봇 제어와 동작 계획 · 출처 ID `t142`

이 패키지는 Isaac Sim **5.1.0**의 Surface Gripper schema와 설치된 gantry stage를 사용한다. 흡착은 진공 유체 해석이 아니라 접촉점에서 부모/물체를 연결하는 **D6 joint constraint**다. `run.py`는 실제 gripper prim을 만들고 attachment joint를 연결한 뒤 close→lift→open 상태와 잡힌 물체 경로를 기록한다.

## 준비와 실행

Isaac Sim 5.1의 `isaacsim.robot.surface_gripper` extension, RTX GPU와 드라이버가 필요하다. 이 실습의 stage는 설치 폴더 `exts/isaacsim.robot.surface_gripper/data/SurfaceGripper_gantry.usda`에 들어 있다. 다른 로컬 패키지나 저장소의 asset 폴더를 사용하지 않는다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/60_motion_robot_surface_gripper
"$ISAAC_SIM/python.sh" run.py
"$ISAAC_SIM/python.sh" run.py --headless --steps 420 --output output/headless.csv
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 물리를 계속 갱신한다. 자동 close→lift→open 동작은 한 번 수행하며 이후 장면을 계속 관찰할 수 있다. 양수 `--steps N`은 N스텝 뒤 종료하고, GUI의 `--steps 0`은 무제한이다. `--headless`에서 생략하면 기존 420스텝으로 종료하며, headless의 0과 음수는 거부한다. CSV는 창을 닫거나 제한에 도달할 때 파일 기록을 마친다.

1. gantry가 `x=0, y=0, z=0.140` joint target으로 큐브에 접근한다. 이 값은 **gantry joint의 이동량**이며 월드 z 좌표가 아니다.
2. 120 step에서 +0.5 action으로 닫는다. `output/gripper.csv`의 상태가 Closing→Closed로 바뀌며 잡힌 물체 경로가 생기는지 본다. 원본 시험 장면은 `/World/Boxes/Cube_28`을 대상으로 한다.
3. 240 step에서 z joint target을 0.05로 줄여 든다. 과도한 힘이면 constraint가 끊어질 수 있으므로 단계마다 상태를 확인한다.
4. 360 step에서 -0.5로 열어 물체를 놓는다. Open 상태와 빈 물체 목록이 해제의 증거다. 400스텝 이상 실행했는데 물체가 한 번도 실제 붙지 않으면 실패를 반환한다. 그 전에 창을 닫거나 작은 `--steps`로 종료한 경우는 전체 과정의 검증이 아니다. 마지막 해제 상태는 CSV에서도 확인한다.
5. 변수 하나 실험: `--grip-distance 0.005 --output output/short.csv`만 바꾸어 접근 거리와 Closing/Closed의 관계를 확인한다.

## GUI에서 직접 구성하기

1. Window > Extensions에서 `isaacsim.robot.surface_gripper` 활성화를 확인한다. **Window(s) > Examples > Robotics Examples > Manipulation > Surface Gripper > Load**로 native 예제를 연다.
2. gantry joint target을 편집하여 큐브 위에 내린다. 예제의 **Open/Close** 버튼을 누르고, 상승할 때 물체가 함께 움직이는지 본다. gamepad가 있다면 아래 face button도 동일한 동작을 한다.
3. 새 gripper prim은 **Create > Robots > Surface Gripper**에서 만든다. Stage에서 선택해 **Attachment Points**에 D6 joint 경로를 넣는다. 모든 joint의 Body 0은 같은 rigid body여야 하고 enabled=true, Exclude from Articulation=true여야 한다. Body 1은 gripper가 잡을 대상에 따라 런타임에 관리한다.
4. joint를 선택하고 **Properties > + Add > Edit API Schema > AttachmentPointAPI**를 적용한다. `Forward Axis` 기본은 X다. `ClearanceOffset`은 ray 시작점을 부모 collider 밖으로 이동시켜 자기 몸체를 잡지 않게 한다. 방향/offset을 부모 표면과 대조한다.
5. Action Graph에서 **Surface Gripper** node를 추가하고 target을 만든 surface gripper prim으로 설정한다. physics 재생 중 open/close 입력을 연결하고 API 방식과 같은 상태 변화가 생기는지 확인한다.

## 속성과 API 설명

`robot_schema.CreateSurfaceGripper(stage, path)`는 gripper USD prim을 작성한다. USD relationship인 `ATTACHMENT_POINTS`는 다른 prim인 D6 joint들을 가리킨다. mesh를 넣는 목록이 아니다. joint의 선형/각도 자유도·drive stiffness/damping은 D6 속성에서 설정한다. direct break force/torque 대신 Surface Gripper의 limit 속성을 사용한다.

| 속성 | 의미 |
|---|---|
| Max Grip Distance | attachment point가 접촉으로 받아들이는 거리(m) |
| Retry Interval | 닫기 시도를 지속할 시간(s) |
| Shear Force Limit | 축에 수직인 전단 방향의 제한 |
| Coaxial Force Limit | 축 방향 제한 |
| Status, Gripped Objects | 읽기 전용 상태 및 실제 잡힌 rigid body |

`GripperView(paths=...)`는 schema prim에 대한 5.1 API다. 이 실습은 view batch API에 길이 1인 배열을 전달한다. `apply_gripper_action([0.5])`는 닫기, `[-0.5]`는 열기이며 -0.3~0.3은 무시된다. `get_surface_gripper_status()`와 `get_gripped_objects()`는 현재 물리 상태를 읽는다. 원문의 단일 interface 방식도 가능하다: `acquire_surface_gripper_interface()` → `close_gripper(path)`/`open_gripper(path)`/`get_gripper_status(path)`.

## 문제 해결과 확인 범위

항상 Closing이면 거리·Forward Axis·ClearanceOffset·collider를 확인한다. 물체를 잡았다가 놓치면 limit, 질량, 가속도를 확인한다. attachment가 보이지 않으면 D6 타입, 같은 Body 0, 활성화 여부를 확인한다. UI 메뉴가 없으면 extension을 켠다. 소스/CLI 검사는 수행했으며 실제 흡착·물리 실행은 아직 미검증이다.

## 출처

[Isaac Sim 5.1 Surface Gripper](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html), [attachment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html#attachment-joints), [코드 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html#creating-a-surface-gripper-fully-on-code). 단계별 joint target은 설치된 5.1 `tests/test_surface_gripper.py`의 native gantry 시나리오와 대조했다.
