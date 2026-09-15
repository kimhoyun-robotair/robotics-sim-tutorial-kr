# 21. Physics Inspector로 관절 편집

권장 학습 순서 **21** · 물리 기초와 Core API 확장 · 출처 ID `t160`

외부 로봇 없이 한 관절 팔을 만들어 정지 상태의 Physics Inspector로 축·한계·관절 동작을 검사합니다. GUI 도구가 주제이며 run.py는 조작 가능한 articulation을 실제 생성합니다.

## 이 실습의 의도

월드에 고정된 Base와 Y축으로 회전하는 Link 하나를 직접 만들어 Physics Inspector에서 관절 연결·회전축·제한각을 편집하는 법을 익힙니다. 단순한 한 관절 구조는 로봇 에셋의 복잡한 계층 없이 잘못된 축이나 limit를 눈으로 구분하기 위한 구성입니다. 기본 스크립트는 팔을 초기화하고 Stop한 상태로 두므로, 처음에 팔이 가만히 있는 것이 정상이며 Inspector 조작은 사용자가 수행합니다.

## 실행 후 확인할 것

- Stage의 `/World/Arm/FixedRoot`가 월드와 Base를 묶고 ArticulationRootAPI를 가지며, `/World/Arm/Joint`의 body0/body1이 Base와 Link를 가리키는지 확인합니다. `arm.usda`에도 이 초기 연결이 저장되어야 합니다.
- Physics Inspector에서 `/World/Arm`을 선택하면 조절할 회전 관절 하나가 나타나는지 봅니다. 위치를 조금 바꿨을 때 Base는 고정되고 Link가 Base 중심의 관절 위치를 기준으로 Y축 회전하는지 관찰합니다.
- 초기 lower/upper limit가 -80°/80°인지 확인하고, 해당 값만 -30°/30°로 줄였을 때 허용 범위도 줄어드는지 비교합니다. 화면의 움직임과 속성 값이 대응해야 관절 편집을 확인한 것입니다.
- 일반 Play 동작을 볼 때는 Inspector를 닫고 실행합니다. 이 관절에는 목표 0°의 angular drive가 있으므로 중력과 drive가 만드는 자세를 보되, Inspector의 부분 초기화 상태를 일반 시뮬레이션 결과로 해석하지 않습니다.
- 변경한 limit를 보존하려면 **File > Save As**로 저장하고 새 파일에서 다시 확인합니다. 기본 `arm.usda` 생성이나 headless 종료만으로 Inspector의 관절 조작이 검증되지는 않습니다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/21_sensors_joint_inspector
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다. GUI 실행에서 `--steps`를 생략하면 사용자가 창을 닫을 때까지 창을 유지합니다. 장면을 만든 뒤 타임라인은 정지하고, 화면과 도구를 위한 `app.update()`만 반복합니다. `--steps N`을 지정하면 이 앱 업데이트를 최대 N번 수행한 뒤 종료하며 N은 양수여야 합니다. `--headless`는 창 없이 실행하고, `--steps` 생략 시 240번 업데이트 후 종료합니다. 이전 명령과 호환되는 `--interactive`는 더 이상 필요하지 않으며 명시한 `--steps`의 종료 조건을 바꾸지 않습니다. `--headless`와 `--interactive`는 함께 쓰지 않습니다. run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다.

## 실습 순서와 관찰

1. 위 GUI 명령처럼 `--steps` 없이 실행합니다. 스크립트는 팔을 생성·초기화한 뒤 **Stop**하고 창을 유지합니다. 출력 `arm.usda`를 나중에 File > Open으로 열어도 됩니다.
2. **Tools > Physics Toolbar**로 authoring toolbar를 켭니다. **Tools > Physics > Physics Inspector**를 엽니다.
3. Stage에서 `/World/Arm`을 선택합니다. Joint의 Y축과 한계 -80°~80°, base 고정 상태를 확인합니다. Inspector의 관절 위치 조절을 소량 움직여 팔이 기대한 축으로 도는지 봅니다.
4. `/World/Arm/Joint`의 lower/upper limit를 -30°/30°로 바꾸고 조절 가능한 범위가 좁아졌는지 비교합니다. limit 값만 변경합니다.
5. 일반 물리 시뮬레이션을 할 때는 **Physics Inspector 창을 닫고** Play합니다. Inspector가 열려 있는 부분 초기화 상태를 일반 simulation 오류로 해석하지 마세요.
6. 변경 결과는 **File > Save As**로 새 파일에 저장합니다. 기본 출력 arm.usda는 원래 생성 직후 값이므로 이후 GUI 편집은 자동 저장되지 않습니다.

## API와 USD 개념

Inspector는 관절 authoring을 돕기 위해 PhysX를 부분 초기화하는 도구입니다. 일반 World Play 루프와 같은 실행 상태라고 가정하면 안 됩니다. Isaac Sim의 메뉴 위치는 연결된 일반 Omniverse 문서와 다를 수 있어 이 패키지는 5.1의 **Tools > Physics > Physics Inspector** 경로를 사용합니다.

이 팔의 root fixed joint는 월드와 Base를 묶고 RevoluteJoint는 Base와 Link를 연결합니다. joint local frame은 두 body 기준 좌표이며 원점이 맞아야 합니다. USD limit는 degree입니다. Root articulation schema와 rigid body schema는 서로 다른 역할입니다.

## 확장 실습·성공 기준·문제 해결

팔이 목록에 없으면 `/World/Arm` 아래 FixedRoot에 ArticulationRootAPI가 있는지, Joint body 관계가 유효한지 확인합니다. 일반 Play가 이상하면 먼저 Inspector 창을 완전히 닫습니다. 본 튜토리얼은 joint authoring 검사이며 센서 데이터를 실제 수집했다고 주장하지 않습니다. 성공 기준은 Inspector에서 한 관절과 제한 범위를 관찰하고 창을 닫은 후 정상 시뮬레이션을 확인하는 것입니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·프레임 수 옵션·출력 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
