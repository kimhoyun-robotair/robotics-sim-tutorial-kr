# 36. 세 도형으로 로봇의 몸체와 바퀴 구성하기

권장 학습 순서 **36** · 로봇 자산 가져오기와 제작 · 출처 ID `t120`

공식 Assemble a Simple Robot의 **기하·물리·재질 편집** 수업이다. 이 패키지는 body cube와 cylinder 바퀴 두 개, 바닥, 빛, 마찰 재질을 직접 생성한다. 외부 asset과 다른 로컬 수업은 필요 없다. 아직 joint가 없으므로 Play를 누르면 세 강체는 따로 떨어진다. 이것이 이번 단계의 올바른 관찰이다.


## 이 실습의 의도

몸체와 바퀴의 외형을 배치하고 각각에 강체·충돌·마찰을 부여하는 로봇 제작의 첫 단계를 익힌다. 파란 cube 몸체와 어두운 cylinder 바퀴 둘은 모양상 한 로봇처럼 보이지만, 아직 joint가 없어 독립된 세 강체다. 실행기는 이 출발 장면을 작성하고 창을 유지하며, 사용자가 Play하여 부품별 낙하와 접촉을 확인한 뒤 외관 재질을 직접 편집한다.

## 실행 후 확인할 것

- **세 강체의 위치:** Stage에서 `/World/body/body`, `/World/wheel_left/wheel_left`, `/World/wheel_right/wheel_right`를 찾는다. Rigid Body와 Collider는 이 geometry prim에 적용되어 있고, 부모 Xform은 배치용 변환을 가진다.
- **의도된 분리 낙하:** Play하면 몸체와 두 바퀴가 각각 떨어져 바닥과 접촉해야 한다. 바퀴가 몸체에서 분리되어 움직이는 것은 joint를 아직 만들지 않은 이 단계의 정상 결과이며, 함께 주행하는 로봇은 이번 출력의 성공 기준이 아니다.
- **초기 구조 기록:** 기본 `initial_inventory.json`의 `rigid_bodies`는 위 세 prim, `joints`와 `articulation_roots`는 빈 목록이어야 한다. GUI에서 나중에 수정한 내용은 초기 목록에 자동 반영되지 않는다.
- **바퀴의 접촉 재질:** `/World/Looks/WheelPhysics`에서 static friction `0.8`, dynamic friction `0.6`, restitution `0`을 보고, 두 cylinder의 physics material binding이 이 재질을 가리키는지 확인한다. 값만 만든 것과 실제 바퀴에 연결한 것은 구분한다.
- **외관과 물리 비교:** 기본 색은 `displayColor`이며 OmniPBR 실습은 직접 수행한다. 복사한 stage에서 한 부품의 Collider만 제거하면 그 부품은 중력으로 떨어져도 바닥을 통과할 수 있다. 색 변경과 접촉 변경이 서로 독립적이라는 점을 확인한다.

## 실행 환경과 파일

Isaac Sim **5.1.0**, 지원되는 RTX GPU와 GUI가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 설치 디렉터리다. Python CLI 도움말은 일반 Python에서도 열린다. 이 패키지는 자체 코드/설정을 가지며 다른 로컬 튜토리얼을 import하지 않는다.

```bash
cd src/36_robot_setup_intro_assemble_robot
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

기본 실행은 창을 계속 열어 두므로 아래 GUI 실습을 수행하고 **Ctrl+S**로 로컬 root layer를 저장한 뒤 창을 닫는다. `output/first/stage.usda`와 `initial_inventory.json`이 생긴다. 기존 output은 덮어쓰지 않으므로 다음 실행은 `output/second`처럼 새 경로를 쓴다. 저장한 실습을 다시 열려면 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다. 재개 시에도 새 로컬 layer가 이전 결과를 참조한다.

GPU/UI 자동 점검을 위한 한정 실행은 `--headless --steps 120 --output output/check`다. 이는 장면 로드 확인만 하며 GUI 작업이나 로봇 동작의 성공을 증명하지 않는다. 패키지 작성 과정에서는 문법·CLI를 확인했으며 GPU와 실제 GUI 조작은 미검증이다.


## 단계별 실습

1. `/World/body`는 translate=(0,0,1)인 Xform이고 자식 `body`는 size=1, scale=(1,2,0.5)인 cube다. GUI로 만들 때 **Create → Xform**, **Create → Shape → Cube**를 사용한다. parent transform과 geometry scale은 서로 다른 계층의 값이다.
2. `/World/wheel_left`는 translate=(1.5,0,1), Rotate XYZ=(90,0,0)이다. 자식 cylinder의 radius=0.5, height=1이다. 이 Xform을 Duplicate하고 x=-1.5로 옮겨 `wheel_right`로 이름을 바꾼다. 코드는 원본 GUI 수업의 도형 배치를 명시적으로 재현한다.
3. cube와 두 cylinder의 Property에서 **Rigid Body**와 **Collider** section을 찾는다. 직접 만드는 경우 세 geometry를 선택하고 **+ Add → Physics → Rigid Body with Colliders Preset**을 적용한다. Xform과 자식 geometry 양쪽에 rigid body를 중복 적용하지 않는다.
4. Play 후 세 물체가 따로 바닥에 닿는지 확인하고 Stop. 하나를 선택해 Collider API를 제거하는 실험은 복사한 stage에서 한다. rigid body만 있으면 떨어지지만 다른 물체를 통과할 수 있다. collider만 있으면 정적인 장애물이다.
5. viewport eye → **Show By Type → Physics → Colliders → All**로 충돌 윤곽을 본다. visual mesh와 collider가 같은 개념은 아니다. dynamic mesh에는 convex hull/decomposition 등 지원되는 근사 형식을 사용한다. static triangle mesh와 dynamic convex 충돌을 혼동하지 않는다.
6. `/World/Looks/WheelPhysics`의 static friction=0.8, dynamic friction=0.6, restitution=0을 확인한다. 직접 만드는 메뉴는 **Create → Physics → Physics Material → Rigid Body Material**이다. cylinder의 **Materials on Selected Model**에서 **physics** 목적의 material이 이 재질인지 확인한다.
7. 외관 재질은 별도다. **Create → Materials → OmniPBR** 두 개를 만들고 이름을 body_color, wheel_color로 정한다. cube와 바퀴에 각각 visual material을 연결하고 **Material and Shader/Albedo**와 roughness를 바꾼다. 기본 fixture의 `displayColor`는 간단한 표시 색이며 OmniPBR 편집 실습을 대신하지 않는다.
8. Ctrl+S로 저장하고 `initial_inventory.json`의 rigid body 3개, joint 0개와 실제 Stage를 비교한다. source의 비교 asset은 `/Isaac/Samples/Rigging/MockRobot/mock_robot_no_joints.usd`다.

## 코드·개념·실험

`UsdGeom.Cube/Cylinder.Define`이 geometry prim을 만들고 `AddTranslateOp`, `AddRotateXYZOp`, `AddScaleOp`가 각 좌표계 변환을 작성한다. `UsdPhysics.RigidBodyAPI`는 운동, `CollisionAPI`는 접촉을 활성화한다. `UsdPhysics.MaterialAPI`는 마찰/반발계수이며 `UsdShade.MaterialBindingAPI.Bind(..., materialPurpose="physics")`로 외관 재질과 구분해 연결한다.

한 변수 실험: WheelPhysics의 restitution만 0→0.7로 바꾸고 바퀴를 같은 높이에서 떨어뜨린다. 튕김의 변화가 있는지 실제 재생으로 확인한다. 물체가 옮겨지는 순간 위치가 틀어지면 reparent의 부모 변환 상속/월드 변환 유지 설정을 확인한다. 바퀴가 몸체와 같이 움직이지 않는 것은 이 단계에서는 joint가 없기 때문이다.

## 출처

- [Isaac Sim 5.1 Tutorial 2: Assemble a Simple Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_assemble_robot.html)
- 로컬 설명/코드는 해당 버전의 실제 GUI 작업을 재구성한 실습이며 NVIDIA 문서 전문을 복제하지 않는다.
