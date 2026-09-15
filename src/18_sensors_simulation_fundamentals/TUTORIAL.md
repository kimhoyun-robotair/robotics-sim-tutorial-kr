# 18. 물리 스키마·충돌·시간 단계

권장 학습 순서 **18** · 물리 기초와 Core API 확장 · 출처 ID `t159`

같은 위치 높이에서 collider가 켜진 큐브와 꺼진 큐브를 떨어뜨려 화면 geometry와 물리 충돌의 차이를 기록합니다. 원문의 기초 물리 실습을 실행 가능한 시작점과 GUI 확장 실습으로 구성했습니다.

## 이 실습의 의도

동일한 크기·질량·시작 높이의 두 강체에서 충돌만 켜고 꺼, **중력으로 움직이는 설정과 바닥에 막히는 설정이 별개**임을 확인합니다. `/World/WithoutCollider`는 동역학을 유지한 채 collision만 비활성화했으므로 지면을 통과하도록 만든 비교 대상입니다. 기본 실행은 두 큐브의 높이를 240프레임 기록하며, 얇은 플랫폼·Torus·관절 실습은 아래에서 직접 구성하는 확장 단계입니다.

## 실행 후 확인할 것

- GUI에서 X=-1 m의 `/World/WithCollider`는 떨어진 뒤 바닥 위에 놓이고, X=+1 m의 `/World/WithoutCollider`는 바닥 아래로 계속 내려가는지 봅니다. 뒤쪽 결과는 의도된 낙하이며 충돌이 켜진 상자까지 지면을 통과하는 경우와 구별합니다.
- `fall.json`의 `time_s`, `with_collider_z`, `without_collider_z`를 같은 행끼리 비교합니다. 기본 높이 2 m에서 충분히 실행하면 한 변 0.5 m인 충돌 상자의 중심은 지면 위 약 0.25 m에 정착하고, 충돌이 꺼진 상자의 z는 0 아래로 내려가야 합니다. 매우 짧은 `--steps`에서는 아직 두 상자 모두 낙하 중일 수 있습니다.
- Stage에서 두 prim의 RigidBodyAPI와 CollisionAPI를 검사하고 `/World/WithoutCollider`의 collision enabled가 false인지 확인합니다. `scene.usda`와 높이 기록을 함께 보면 보이는 형상, 동역학, 충돌 여부를 구분할 수 있습니다.
- `--ccd`를 추가했다면 Physics Scene과 `/World/WithCollider` 양쪽의 CCD 설정을 확인합니다. 이 옵션은 충돌이 꺼진 상자를 멈추게 하지 않으며, 기본 바닥만 관찰한 결과로 얇은 플랫폼의 관통 방지 효과까지 확인했다고 판단하지 않습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/18_sensors_simulation_fundamentals
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/gui-01
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다. GUI 실행에서 `--steps`를 생략하면 처음 240프레임을 기록한 뒤에도 사용자가 창을 닫을 때까지 시뮬레이션을 계속합니다. 이후 프레임은 파일에 추가하지 않습니다. `--steps N`을 지정하면 최대 N프레임을 기록하고 종료하며 N은 양수여야 합니다. `--headless`는 창 없이 실행하고, `--steps` 생략 시 240프레임 후 종료합니다. 이전 명령과 호환되는 `--interactive`는 더 이상 필요하지 않으며 명시한 `--steps`의 종료 조건을 바꾸지 않습니다. `--headless`와 `--interactive`는 함께 쓰지 않습니다. run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다.

## 실습 순서와 관찰

1. 실행 후 `fall.json`에서 두 높이를 비교합니다. collider가 있는 상자는 바닥에 놓이고 없는 상자는 바닥을 통과합니다. shape prim만으로 물리가 자동 설정되지 않는다는 점을 관찰합니다.
2. 위 GUI 명령으로 실행한 창에서 `/World/WithCollider`와 `/World/WithoutCollider`의 RigidBodyAPI·CollisionAPI를 봅니다. `GetCollisionEnabledAttr().Set(False)`는 동역학을 끄는 것과 다릅니다.
3. File > New에서 Ground Plane, Xform(Z=10), 자식 Cube(local Z=.5)를 만들고 Xform에 Rigid Body, Cube에 Collider를 추가하는 원문 계층 실습을 반복합니다. 부모가 움직여도 자식 local 위치는 유지됩니다.
4. 높이 Z=3에 scale=(2,2,.01)인 static collider 플랫폼을 만듭니다. 물체를 Z=80에서 떨어뜨려 tunneling을 관찰하고 Physics Scene과 rigid body **두 곳**에 CCD를 켭니다. 로컬 스크립트의 `--ccd`도 두 곳을 켜지만 기본 ground plane만으로 tunneling 개선을 증명하지 않습니다.
5. Torus를 Z=3, scale=(5,5,5)로 만들고 **Rigid Body With Colliders Preset**을 추가합니다. viewport 눈 아이콘 **Show By Type > Physics > Colliders > Selected**로 convex hull이 구멍을 막는지 봅니다. Collision approximation을 **Convex Decomposition**으로 바꾸고 구멍이 유지되는지 비교합니다.

## API와 USD 개념

USD Physics schema는 rigid body, collision, joint 등의 속성을 USD prim에 부여합니다. `Apply`는 API를 붙이고 `Create...Attr`는 값이 있는 속성을 만들며 `Get...Attr().Set`은 그 속성을 수정합니다. 속성 tooltip에서 `physics:velocity` 같은 이름을 확인할 수 있습니다.

physics_dt와 rendering_dt는 서로 다른 시간 간격입니다. 이 코드는 둘 다 1/60초지만 실제 실행 속도가 실시간이라는 뜻은 아닙니다. Root Layer의 Timecodes per second는 animation 시간 척도, Physics Scene의 Simulation Steps per Second는 물리 적분 빈도입니다. 100 Hz physics와 30 Hz rendering처럼 정수배가 아니면 화면 frame당 물리 step 수가 달라집니다.

convex hull은 오목한 구멍을 메우는 빠른 근사입니다. convex decomposition은 여러 convex로 나누므로 비용이 늘고, 동적 triangle mesh는 그대로 지원되지 않아 SDF Mesh 등을 고려합니다. 시각 geometry와 collider는 별도이므로 숨긴 mesh도 충돌할 수 있습니다.

## 확장 실습·성공 기준·문제 해결

이어서 원문 세부 실습을 진행하세요.

- Collider Advanced의 **Rest Offset**은 표면을 부풀리거나 줄이고 **Contact Offset**은 접촉 제약을 미리 생성할 거리를 정합니다. 작은 contact offset은 놓침·떨림, 큰 값은 계산량 증가를 유발할 수 있습니다.
- **Create > Physics > Physics Material**에서 Rigid Body Material을 만들고 collider의 Physics Materials에 할당합니다. restitution/friction만 하나씩 바꾸어 튀기·미끄러짐을 봅니다. combine mode 우선순위는 average<min<multiply<max입니다. Compliant contacts의 spring/damper는 rigid body 접촉을 부드럽게 근사합니다.
- 두 rigid body를 차례로 선택하고 **Create > Physics > Joints > Revolute Joint**를 만듭니다. body0/body1과 두 local joint frame, 축, lower/upper limit를 확인합니다. USD 각도는 degree이며 Python articulation 각도는 radian인 API가 많습니다. **Add > Physics > Angular Drive**로 목표각/속도를 지정합니다.
- Articulation root는 joint tree를 로봇용으로 처리합니다. On Physics Step을 사용하는 Action Graph는 Raw USD Properties의 pipeline stage를 **PipelineStageOnDemand**로 설정해 physics step과 대응시킵니다.
- Physics Scene/Articulation Root/Joint에 **Add > Physics > Residual Reporting**을 적용하고 Simulation Data Visualizer에서 residual을 봅니다. 낮은 residual은 제약 수렴 지표이고 현실과의 모델 오차가 아닙니다.

한 변수 실험은 `--height 4 --output output/height4`로 낙하 높이만 바꾸어 충돌 전 시간을 비교하는 것입니다. 바닥 통과가 둘 다 일어나면 collider·단위·step 크기를 확인합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·프레임 수 옵션·출력 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
