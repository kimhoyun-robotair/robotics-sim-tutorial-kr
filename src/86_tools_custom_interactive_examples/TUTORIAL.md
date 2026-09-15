# 86. Custom Interactive Examples

권장 학습 순서 **86** · OmniGraph와 확장 개발 · 출처 ID `t163`

Examples Browser에 **Korean Examples > Korean Falling Cube** 항목을 등록하는 독립 확장이다. 공식 `user_examples` 폴더를 수정하는 대신 이 폴더의 extension으로 같은 BaseSample 구조를 사용한다.

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

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/custom_interactive_examples.html).
