# 86. Custom Interactive Examples

권장 학습 순서 **86** · OmniGraph와 확장 개발 · 출처 ID `t163`

Examples Browser에 **Korean Examples > Korean Falling Cube** 항목을 등록하는 독립 확장이다. 공식 `user_examples` 폴더를 수정하는 대신 이 폴더의 extension으로 같은 BaseSample 구조를 사용한다.

## 이 실습의 의도

하나의 낙하 장면을 Examples Browser 항목으로 등록하고 BaseSample의 Load·Play·Reset과 확장 종료가 각각 맡는 역할을 확인한다. 초록 Cube는 `DynamicCuboid`로 생성해 강체와 충돌을 포함하므로 중력 낙하 후 바닥에 멈추는 동작이 목표다. 확장을 켜는 단계에서는 Browser 항목만 등록되며, 사용자가 **Korean Falling Cube → Load → Play**를 수행해야 장면 생성과 물리 실행으로 이어진다.

## 실행 후 확인할 것

- 확장 활성화 후 Robotics Examples에 **Korean Examples > Korean Falling Cube**가 한 항목으로 나타나는지 확인한다. 이때 장면에 Cube가 아직 없는 것은 Load를 누르기 전의 정상 상태다.
- **Load** 후 바닥과 `/World/LearningCube`가 생기고, Console의 `loaded pose:`와 Property에서 시작 위치 `(0, 0, 1.5)` m를 확인한다. Cube는 한 변 `0.25` m, 초록색 `(0.2, 0.7, 0.3)`이다.
- **Play**하면 Cube 높이가 줄고 바닥 위에 머무는지 관찰한다. 단순 표시용 도형과 달리 강체·충돌이 있는 Cube이므로 바닥을 계속 통과하는 결과는 이 실습의 기대 동작이 아니다. 접촉 후 중심 높이는 반변 길이인 약 0.125 m 부근이며 정확한 접촉값은 물리 설정에 따라 달라질 수 있다.
- **Reset** 후 `reset pose:`와 화면에서 Cube가 시작 높이 1.5 m로 복원되는지 확인한다. 낙하가 끝났다는 것과 reset callback이 정상 작동한다는 것은 각각 확인해야 한다.
- 확장을 끄면 Browser 항목이 제거되고 다시 켜면 하나만 등록되는지 본다. `on_shutdown`은 항목 등록을 해제하므로 기존 Stage의 Cube가 자동 삭제되는 것을 종료 성공 조건으로 삼지 않는다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 실행

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.browser.example
```

1. `Window > Examples > Robotics Examples`를 연다. **Korean Examples > Korean Falling Cube**를 선택한다.
2. **Load**를 눌러 바닥과 초록색 Cube를 만든다. Stage에서 `/World/LearningCube`를 선택하고 `F`를 누른다.
3. **Play**를 눌러 Cube가 떨어져 바닥에 멈추는지 확인한다. **Reset**으로 시작 높이 1.5 m로 돌아오는지 본다.
4. `Window > Extensions`에서 `kr.browser.example`을 비활성화하면 Browser 항목이 제거되는지 확인한다. 다시 켜면 중복 없이 한 항목만 등록되어야 한다.

## BaseSample과 UI lifecycle

`BaseSample.setup_scene()`은 World의 scene에 물체를 넣는 곳이다. `setup_post_load()`에서 물리 handle 초기화가 끝난 Cube를 조회하고, `setup_post_reset()`은 reset 후 위치를 확인한다. `BaseSampleUITemplate`는 Load/Reset의 비동기 작업과 기본 UI를 제공한다. `register_example`의 execute_entrypoint와 ui_hook는 창/패널 구성을 Browser에 연결한다. `on_shutdown`에서 `deregister_example`을 호출하여 뜬금없는 메뉴 중복을 막는다.

USD prim 생성과 rigid body runtime 초기화는 별개이므로 load 전에 관절/물리 handle을 조회하지 않는다. 예제는 외부 USD 자산을 요구하지 않고 DynamicCuboid와 ground plane을 직접 만든다.

한 변수 실험: Cube 시작 높이만 1.5→2.5로 바꿔 저장하고 확장을 reload한다. Load/Reset 후 실제 높이가 바뀌는지 확인한다. 항목이 안 보이면 `--ext-folder` 부모 경로, extension 활성 오류, Examples Browser 의존성을 확인한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html).
