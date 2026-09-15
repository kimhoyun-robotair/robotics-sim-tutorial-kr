# 85. Extension Template Generator Explained

권장 학습 순서 **85** · OmniGraph와 확장 개발 · 출처 ID `t165`

네 생성 템플릿의 callback과 timeline 상태를 분석한다. 독립 starter 확장으로 UI callback을 먼저 확인하고 공식 생성물의 Load/Reset/Run, generator, 동적 관절 UI를 실험한다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.
## 공식 생성기로 네 종류 생성

1. `Window > Extensions`에서 **isaacsim.examples.extension**을 켜고 `Utilities > Generate Extension Templates`를 연다.
2. 이 패키지 안에 새 `output/extensions/` 폴더를 만들고 **Loaded Scenario Template**을 펼친다. Extension Path=`/absolute/path/to/this-package/output/extensions/kr.loaded`, Name=`kr.loaded`, Description=`Load reset run lesson`을 입력해 Generate Extension을 누른다.
3. **Scripting Template**은 `kr.scripted`, **Configuration Tooling Template**은 `kr.configuration`, **UI Component Library**는 `kr.components`로 같은 부모 아래 각각 생성한다. 같은 폴더에 덮어쓰지 않는다.
4. `Window > Extensions`의 메뉴→Settings→Extension Search Paths에서 **부모 output/extensions 절대 경로**를 +로 추가한다. Third Party 탭에서 각 확장을 찾아 하나씩 Enabled를 켠다.
5. 메뉴바에 새 항목이 나타나는지 확인하고 해당 창을 연다. 공식 로봇을 쓰는 generated sample은 Isaac Sim 5.1 자산 서버/로컬 asset pack이 필요하다.

| 템플릿 | 수행할 동작 | 성공 기준 |
|---|---|---|
| Loaded Scenario | Load → Run → Stop → Reset | 로드 후 동작, reset 시 초기 상태 |
| Scripting | Load → Run | 순차 동작이 프레임마다 진행되고 UI가 응답 |
| Configuration | 새 Stage에 Franka 추가, Play, 로봇 dropdown 선택 | 관절 UI 생성 및 선택 관절 이동 |
| UI Component Library | FloatField/체크박스/button 값 변경 | callback이 전달받는 값/타입 확인 |

Franka는 Content `Isaac Sim > Robots > FrankaRobotics > FrankaPanda > franka.usd`를 새 Stage에 드래그한다. Configuration 템플릿은 Stage/타임라인을 소유하지 않으므로 사용자가 Play한 로봇을 선택해야 한다.

## 1. Callback이 보장하는 상태

생성된 `scripts/ui_builder.py`를 연다. 다음 함수에 `print("함수명")` 한 줄씩 넣어 각 버튼과 timeline event가 어느 함수를 호출하는지 Console에서 확인한다. 공식 설치 원본이 아닌 방금 만든 output 아래 파일을 편집한다.

| 함수 | 호출 시점/사용법 |
|---|---|
| `build_ui` | UI 구성, field/button callback 연결 |
| `on_menu_callback` | 도구 창 열기 |
| `on_timeline_event` | Play/Pause/Stop 반응 |
| `on_physics_step` | Play 중 물리 step마다 실행 |
| `on_stage_event` | Stage 열기/닫기 대응 |
| `cleanup` | subscription 등 자원 해제 |

Loaded Scenario의 Load는 World 생성→`setup_scene_fn`에서 `world.scene.add`→초기화→`setup_post_load_fn` 순서다. post-load에서는 timestep 0에 pause된 초기화 객체를 사용할 수 있다. Reset의 pre-reset은 상태를 가정하지 않고 post-reset은 기본 pose로 복원된 객체를 사용한다. `World`는 하나의 simulator lifecycle을 관리하는 singleton이므로 다른 예제 World와 동시에 섞지 않는다.

## 2. StateButton과 물리 callback

Loaded Scenario에서 Run을 누르면 A(Run)→B(Stop) 상태로 바뀐다. `on_a_click`, `on_b_click`과 B 상태에서만 활성인 `physics_callback_fn`을 찾아 출력으로 호출 순서를 확인한다. Stop은 해당 subscription을 해제한다. 타임라인의 외부 Stop을 눌러도 template이 UI 가정을 복구하는지 관찰한다.

## 3. Scripting의 yield / yield from

`scenario.py`의 `my_script()`는 `goto_position`, `open_gripper_franka`, `close_gripper_franka`를 `yield from`으로 순서대로 실행한다. 매 physics step의 `next(generator)`는 다음 yield까지 진행하고 제어권을 Kit에 반환한다. `while`로 도착을 기다리면서 yield를 빼면 UI/physics 모두 멈추므로 도착하지 못한다.

제공 `bounded_wait.py`의 `wait_for_target`은 같은 원리를 작은 함수로 구현하며 300 step 이후 도착하지 않으면 TimeoutError를 낸다. 생성한 scenario에 함수를 복사하고 `yield from wait_for_target(articulation, [7,8], [0.04,0.04])`처럼 **명령을 보낸 뒤** 호출한다. 이것은 실제 관절 위치를 읽으며 시간 경과만으로 성공을 꾸미지 않는다.

## 4. Configuration과 UI wrapper

Configuration 템플릿은 현재 Stage에서 articulation을 검색해 dropdown을 채우고 선택이 바뀔 때 Robot Control Frame을 다시 만든다. Play 전에는 물리 handle이 없어서 관절 조작을 막는다. UI Component Library는 FloatField, DropDown, StateButton 등 wrapper callback의 인수/반환 타입을 확인하는 참고 구현이다. UI 값 변경만으로 물리가 변하지 않으며 연결된 callback이 실제 action을 보내야 한다.

## 제공 starter와 확인

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.lifecycle.starter
```

Create Cube callback과 `on_shutdown`의 window.destroy를 보고 생성기 boilerplate와 비교한다. 한 변수 실험: Scripting의 관절 도착 tolerance만 0.001→0.01로 바꾸고 다음 동작 시작 시점을 비교한다. 성공은 Load/Reset 상태 보장, Run 동안 UI 응답, 실제 관절 도착 후 다음 동작, 확장 종료 후 callback 해제다. 오래 멈추면 목표 도달 가능성/관절 인덱스/yield를 점검한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_templates_tutorial.html).
