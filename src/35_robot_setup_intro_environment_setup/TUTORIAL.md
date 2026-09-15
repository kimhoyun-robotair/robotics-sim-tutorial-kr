# 35. Stage의 단위·중력·바닥·조명

권장 학습 순서 **35** · 로봇 자산 가져오기와 제작 · 출처 ID `t119`

공식 Stage Setup 수업의 GUI 절차를 **로컬 절차형 USD fixture**와 함께 학습한다. 이 수업에는 외부 모델이 필요 없다. `run.py`는 아래 설정을 실제 USD API로 작성하여, 초심자가 Property의 값과 결과를 바로 비교할 수 있게 한다. 직접 만드는 연습은 별도 **File → New** stage에서 같은 순서로 수행한다.


## 이 실습의 의도

로봇을 배치하기 전에 stage의 길이 단위·위쪽 축·중력·바닥 충돌·조명을 서로 구분해 설정하는 연습이다. 기본 장면은 m·Z-up 환경과 초록색 spot light를 만들어 Property 값과 화면의 관계를 바로 비교하도록 했다. 실행기가 낙하용 큐브나 자동 Play를 추가하지 않으므로, 중력·접촉 확인은 아래 절차에서 큐브에 강체와 collider를 직접 붙인 뒤 수행한다.

## 실행 후 확인할 것

- **장면 단위:** 기본 생성 장면의 `initial_inventory.json`에서 `meters_per_unit=1.0`, `up_axis="Z"`를 확인한다. 강체·joint·articulation 목록이 비어 있는 것은 낙하 물체나 로봇을 아직 만들지 않은 출발 상태다.
- **물리 설정:** `/World/PhysicsScene`의 gravity direction `(0,0,-1)`, magnitude `9.8`, GPU dynamics 꺼짐, broadphase `MBP`를 Property에서 확인한다. GPU 렌더링이 동작하는 것과 GPU 물리를 선택하는 것은 별개다.
- **빛의 영향:** `/World/SpotLight` visibility를 토글해 바닥의 초록빛이 바뀌는지 본다. `/World/DefaultLight`도 있으므로 spot light를 껐다고 화면 전체가 검게 될 필요는 없다. cone angle만 45→20으로 바꾸면 비추는 영역의 변화를 비교할 수 있다.
- **수동 낙하 실험:** Z=2에 큐브를 만들고 Rigid Body with Colliders를 적용한 뒤 Play한다. 큐브가 아래로 떨어져 `/World/Ground`에 멈춰야 중력과 접촉을 함께 확인한 것이다. 기본 장면만 열었을 때 아무것도 떨어지지 않는 것은 정상이다.
- **편집 저장:** 단위·빛·큐브를 수정한 결과는 로컬 `stage.usda`에 Ctrl+S로 저장한다. `initial_inventory.json`은 실행 초기 상태만 기록하므로 나중에 만든 큐브가 그 파일에 추가되지 않는 것은 정상이다.

## 실행 환경과 파일

Isaac Sim **5.1.0**, 지원되는 RTX GPU와 GUI가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 설치 디렉터리다. Python CLI 도움말은 일반 Python에서도 열린다. 이 패키지는 자체 코드/설정을 가지며 다른 로컬 튜토리얼을 import하지 않는다.

```bash
cd src/35_robot_setup_intro_environment_setup
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

기본 실행은 창을 계속 열어 두므로 아래 GUI 실습을 수행하고 **Ctrl+S**로 로컬 root layer를 저장한 뒤 창을 닫는다. `output/first/stage.usda`와 `initial_inventory.json`이 생긴다. 기존 output은 덮어쓰지 않으므로 다음 실행은 `output/second`처럼 새 경로를 쓴다. 저장한 실습을 다시 열려면 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다. 재개 시에도 새 로컬 layer가 이전 결과를 참조한다.

GPU/UI 자동 점검을 위한 한정 실행은 `--headless --steps 120 --output output/check`다. 이는 장면 로드 확인만 하며 GUI 작업이나 로봇 동작의 성공을 증명하지 않는다. 패키지 작성 과정에서는 문법·CLI를 확인했으며 GPU와 실제 GUI 조작은 미검증이다.


## 단계별 실습

1. **Edit → Preferences → Stage**에서 Up Axis **Z**, 단위 **meters**, 회전 순서를 확인한다. 이 fixture의 `initial_inventory.json`은 `meters_per_unit=1`, `up_axis=Z`여야 한다. 좌표축과 길이 단위는 모델을 넣기 전에 정한다. cm 모델을 m로 잘못 해석하면 100배 차이가 난다.
2. Stage에서 `/World/PhysicsScene` 선택. 직접 만들 때는 **Create → Physics → Physics Scene**. gravity direction=(0,0,-1), magnitude=9.8이다. 작은 실습은 **Enable GPU dynamics 해제**, **Broadphase=MBP**로 CPU 물리를 쓴다. 렌더링에 RTX GPU가 필요하다는 점과 물리 CPU/GPU 선택은 다른 설정이다.
3. `/World/Ground`를 선택한다. 직접 만들 때는 **Create → Physics → Ground Plane**. 눈에 보이는 바닥의 크기와 무한 평면 충돌 영역은 다르다. viewport eye 메뉴에서 Grid를 켜 위치를 확인한다.
4. `/World/SpotLight`의 translate=(0,0,7), orientation=(0,0,0), color=(0.5,1,0.5), intensity=1000000, radius=0.05를 확인한다. 직접 만들 때 **Create → Light → Sphere Light**. **Shaping → cone:angle=45**, **cone:softness=0.05**를 지정한다. `/World/DefaultLight`는 intensity=300으로 둔다.
5. 조명 visibility를 토글하며 바닥에 초록빛이 사라지고 생기는지 확인한다. 색은 빛의 색이며 바닥 material의 색을 바꾼 것이 아니다.
6. 중력을 관찰하려면 **Create → Shape → Cube**를 만들고 translate Z=2, scale=(0.2,0.2,0.2)로 둔다. **Property → + Add → Physics → Rigid Body with Colliders Preset**을 적용하고 Play. 바닥에서 멈추면 gravity와 collider를 함께 확인한 것이다. Stop하면 초기 위치로 돌아오는지 확인한다.

## API 해설

`UsdGeom.SetStageMetersPerUnit`과 `SetStageUpAxis`는 stage metadata를 작성한다. `UsdPhysics.Scene`이 중력을, `PhysxSceneAPI`가 PhysX backend 설정을 담당한다. `PhysicsSchemaTools.addGroundPlane`은 충돌 평면과 표시용 기하를 구성한다. `UsdLux.SphereLight`는 점 크기가 있는 광원, `ShapingAPI`는 광원을 원뿔 범위로 제한한다. USD 장면은 물체 기하가 있다는 이유만으로 시뮬레이션하지 않으므로 낙하에는 `RigidBodyAPI`와 `CollisionAPI`가 필요하다.

한 변수 실험: cone angle만 45→20으로 바꾸고 빛이 비치는 영역을 비교한다. 광원 intensity나 위치도 함께 바꾸면 원인을 구분하기 어렵다. 물체가 떨어지지 않으면 rigid body, 통과하면 collider, 화면이 검으면 조명 visibility와 camera 노출을 확인한다.

## 출처

- [Isaac Sim 5.1 Tutorial 1: Stage Setup](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_intro_environment_setup.html)
- 로컬 설명/코드는 해당 버전의 실제 GUI 작업을 재구성한 실습이며 NVIDIA 문서 전문을 복제하지 않는다.
