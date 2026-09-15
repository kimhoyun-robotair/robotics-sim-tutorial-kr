# 19. Rubik 큐브에 물리 성질을 단계별로 붙이기

권장 학습 순서 **19** · 물리 기초와 Core API 확장 · 출처 ID `t104`

공식 원문: **Adding Props** · Isaac Sim **5.1.0** · 인덱스 **t104**

## 만들 결과와 실행 방식

공식 Rubik 에셋에 강체, mesh 충돌체 또는 숨겨진 sphere 충돌체, 질량, 마찰과 반발 재질을 붙입니다. visual/rigid/mesh/sphere의 네 가지 모드를 실제 낙하 결과로 비교합니다.

이 패키지는 `Adding Props` 원문의 핵심 학습 흐름을 **standalone Python**으로 구현한 한국어 실습입니다. 공식 Core 원문의 확장(BaseSample) 워크플로는 Isaac Sim GUI가 앱 수명과 이벤트 루프를 관리합니다. 여기서는 `SimulationApp`을 직접 시작하고 `World.reset()` → 반복 `World.step()` → `app.close()` 순서를 한 폴더에서 읽을 수 있게 구성했습니다. GUI 단계가 주제인 부분은 아래 절차에 함께 적었습니다. 다른 로컬 패키지나 공통 모듈을 먼저 공부할 필요가 없습니다.

## 준비

- Isaac Sim 5.1.0이 설치되고 NVIDIA GPU/드라이버가 정상 동작해야 합니다. `--headless`는 창만 숨기며 Isaac Sim 런타임 요구사항을 없애지 않습니다.
- Isaac Sim 5.1 에셋 `/Isaac/Props/Rubiks_Cube/rubiks_cube.usd`가 필요합니다. 별도 설치한 5.1 에셋 팩은 `--asset /절대경로/Isaac/Props/Rubiks_Cube/rubiks_cube.usd`로 지정합니다. 모형을 일반 큐브로 대체하지 않으며 Rubik의 참조 mesh가 없으면 오류로 중단합니다.
- 이 폴더의 파일을 통째로 복사해도 실행할 수 있습니다. 아래는 이 폴더 안에서 실행하는 명령입니다. `ISAAC_SIM_ROOT`에는 실제 5.1 설치 경로를 지정합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --physics visual --slope 0
"$ISAAC_SIM_ROOT/python.sh" run.py --physics rigid --slope 0
"$ISAAC_SIM_ROOT/python.sh" run.py --physics mesh --slope 0
"$ISAAC_SIM_ROOT/python.sh" run.py --physics sphere --slope 10 --restitution 0.8
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지됩니다. 양수 `--steps N`을 지정하면 최대 N단계 실행 후 종료합니다. `--headless`에서 생략하면 기존 기본값 360단계를 사용합니다. 기본 360단계의 위치 샘플을 저장한 뒤에도 물리 시뮬레이션을 계속합니다. 저장된 결과는 최초 관찰 구간의 기록입니다. 실행 중 GUI의 Stop/Play로 초기화를 시도하는 대신 프로그램을 다시 실행하세요. 기본 출력은 이 폴더의 `output/<고유번호>/`이며 `--output`으로 지정한 경로가 이미 있으면 덮어쓰지 않고 오류를 냅니다.

## 파일 안내

- `run.py`
- `tutorial.json`: 공식 출처, 실행 형태, 산출물과 검증 상태입니다.

## 차례대로 실습하기

1. visual 모드로 실행합니다. 보이는 mesh만 있으면 중력이 적용되지 않아 공중에 떠 있습니다. rigid 모드는 강체만 추가하므로 바닥을 통과합니다. 두 결과의 `samples` z를 비교합니다.
2. mesh 모드는 실제 Rubik mesh에 `CollisionAPI`와 convexHull 근사를 추가합니다. 지면 위에 멈추는지 봅니다.
3. sphere 모드는 Rubik 아래에 반지름 0.07 m의 `/World/Rubik/PhysicsSphere`를 추가하고 보이지만 않게 만듭니다. mesh collider는 제거되어 있으므로 sphere가 물리 접촉 모양을 결정합니다.
4. slope 10°와 restitution 0.8인 실행에서 기울어진 바닥 위 구르기와 반발을 봅니다. 질량은 0.1 kg, static/dynamic friction은 0.5/0.4입니다.
5. 각 실행의 `configured_scene.usda`를 Isaac Sim의 File > Open으로 열어 실제 속성을 검사할 수 있습니다. 이 파일은 물리 진행 전 구성 상태를 저장하며 외부 Rubik reference가 포함되므로 원본 에셋 접근은 계속 필요합니다.
6. 원문 GUI 실습도 이 폴더의 안내만으로 할 수 있습니다. File > New Stage → Content Browser의 Isaac Sim > Props > Rubiks_Cube > rubiks_cube.usd를 끌어놓기 → 위치 (0,0,0.1) → Create > Isaac > Environment > Flat Grid를 추가합니다. 각 단계에서 PLAY/STOP하며 비교합니다.
7. GUI에서 Rubik을 우클릭해 Add > Physics > Rigid Body, Add > Physics > Collider Presets, Add > Physics > Mass 순서로 추가하고 Mass=0.1을 설정합니다. Viewport Eye > Show By Type > Physics > Colliders > All로 충돌 외곽을 확인합니다.
8. `/World/rubiks_cube/RubikCube`의 기존 Collider를 제거하고 자식 Sphere를 생성해 Radius=0.07, Collider Presets를 적용하고 눈 아이콘으로 숨깁니다. FlatGrid의 Transform Offset Mode를 켜고 Rotation=(10,0,0)을 지정합니다.
9. Create > Physics > Physics Material을 만들어 restitution=1을 설정하고 sphere의 Physics Material에 바인딩합니다. Rubik 위치 z=1에서 낙하해 봅니다. 원문의 GUI 마지막 단계에 해당하며 코드의 --restitution 1로도 비교할 수 있습니다.

## API와 Omniverse/USD 개념

| USD 물리 개념 | 역할 |
|---|---|
| RigidBodyAPI | 질량 중심의 운동을 시뮬레이션합니다. 충돌체를 자동으로 뜻하지 않습니다. |
| CollisionAPI | 접촉할 모양을 물리 엔진에 등록합니다. |
| MeshCollisionAPI / convexHull | 시각 mesh를 동적 강체가 사용할 볼록 근사로 바꿉니다. |
| MassAPI | kg 단위의 질량 등 관성 관련 속성을 정의합니다. |
| MaterialAPI | 마찰과 반발을 정의합니다. 시각 색/텍스처 재질과 다릅니다. |
| MaterialBindingAPI, purpose=physics | 생성한 물리 재질을 실제 충돌 shape에 연결합니다. |

USD의 visibility=invisible은 렌더링을 숨깁니다. 충돌을 끄는 설정이 아닙니다. 보이는 Rubik과 접촉용 sphere가 달라도 되므로 단순한 충돌체로 복잡한 모형을 근사할 수 있습니다. 이 코드는 비교 시작점을 일정하게 만들려고 참조 에셋의 물리 스키마를 제거하고 지정한 모드만 로컬 layer에 다시 저술합니다. 원본 USD 파일은 수정하지 않습니다.

## 관찰과 성공 판정

visual은 높이 유지, rigid는 지면 관통, mesh는 지면 접촉, sphere는 구르기/반발의 차이가 나타나야 합니다. `result.json`의 collider 경로와 실제 위치 샘플을 확인합니다. 반발계수 1이어도 마찰·충돌 수치해석 때문에 영구 운동을 보장하지 않습니다.

## 한 변수만 바꾸는 실험

sphere 모드의 slope/질량을 그대로 두고 `--restitution`만 0과 1로 비교합니다. 접촉 후 높이 변화를 samples에서 읽습니다.

## 문제 해결

No Rubik meshes 오류는 에셋 경로 또는 참조 리소스 접근 문제입니다. 장면의 PhysicsSphere는 의도적으로 보이지 않습니다. GUI에서는 collision visualization을 켜서 확인합니다. `--physics rigid`에서 지면 관통은 강체와 충돌체 차이를 보여주는 의도된 실험입니다.

`SimulationApp`보다 먼저 `omni`, `pxr`, Core 확장을 import하면 모듈 초기화에 실패할 수 있습니다. 일반 Python의 `--help`가 실행되는 것은 CLI 문법 검사일 뿐 물리 실행 성공은 아닙니다. 이 패키지의 검증 상태는 `tutorial.json`에 별도로 기록합니다.

## 버전 고정 출처와 원문 대응

- [NVIDIA Isaac Sim 5.1.0 — Adding Props](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html)
- [공식 5.1: configure-physics-properties](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html#configure-physics-properties)
- [공식 5.1: customize-collider](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html#customize-collider)
- [공식 5.1: add-physics-materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_props.html#add-physics-materials)

설명은 한국어로 새로 작성했으며 API 흐름과 실습 수치는 해당 5.1 공식 튜토리얼을 기준으로 합니다. 로컬 코드의 선택적 실행 길이 제한, 결과 파일, 인자, 별도 성공 측정은 초심자가 단독으로 실행하고 비교하도록 추가한 구성입니다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
