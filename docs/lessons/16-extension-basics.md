# 16단계. Extension의 구조와 수명주기를 익히다

**목표:** Extension Manager가 어떤 파일을 읽고, 활성화·비활성화 때 어떤 함수가 호출되는지 이해한다. 다음 프로젝트에서 사용할 [tutorial.scene](../../extensions/tutorial.scene/config/extension.toml)을 직접 활성화한다.

## Extension은 폴더 하나에서 시작하기

| 파일 | 역할 |
|---|---|
| `extensions/tutorial.scene/config/extension.toml` | 이름·버전·의존성·Python 모듈을 선언 |
| `extensions/tutorial.scene/tutorial/scene/__init__.py` | 시작 클래스를 패키지에서 노출 |
| `extensions/tutorial.scene/tutorial/scene/extension.py` | UI와 장면 생성 함수, 시작·종료 처리를 구현 |

첫 번째 `tutorial.scene`은 Extension 폴더 이름이다. `tutorial/scene`은 Python 모듈 `tutorial.scene`이 위치하는 경로이다. 두 이름을 맞춰 두면 폴더를 보고 import 경로를 찾기 쉽다. `config/extension.toml`이 없으면 일반 Python 폴더를 복사해도 Kit가 Extension으로 발견하지 못한다.

```toml
[package]
version = "0.1.0"
title = "Tutorial Scene Builder"
description = "A small, repeatable scene authoring exercise for Isaac Sim 6.0.1"
category = "Tutorial"

[dependencies]
"omni.ui" = {}
"omni.usd" = {}
"omni.timeline" = {}

[[python.module]]
name = "tutorial.scene"
```

`dependencies`는 “이 기능을 먼저 사용할 수 있게 해 달라”는 선언이다. Python import를 작성했다고 해당 Extension의 모든 의존성이 자동으로 준비되는 것은 아니다. 이 도구에는 UI, 현재 Stage, Timeline만 필요하므로 ROS 2나 센서 Extension을 의존성에 넣지 않는다.

## 시작과 종료를 한 쌍으로 작성하기

다음 코드는 구조를 보여 주는 최소 예이다. 제공된 파일을 이 조각으로 덮어쓰지 말고 전체 구현과 비교한다.

```python
import omni.ext
import omni.ui as ui

class TutorialSceneExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._window = ui.Window("Tutorial Scene Builder", width=460, height=190)
        with self._window.frame:
            with ui.VStack():
                ui.Label("장면을 만들 준비가 되었다.")

    def on_shutdown(self):
        if self._window is not None:
            self._window.destroy()
            self._window = None
```

활성화하면 Kit가 `on_startup()`을 호출한다. 비활성화·재로딩 때는 `on_shutdown()`으로 UI와 콜백을 정리한다. 여기에서 `SimulationApp()`을 만들거나 `app.close()`를 호출하면 이미 열려 있는 앱의 수명주기와 충돌한다. Extension은 자신이 만든 기능의 시작·종료만 담당한다.

## 저장소의 Extension을 등록하기

1. Isaac Sim GUI에서 `Window > Extensions`를 연다.
2. 검색창 오른쪽 메뉴의 Settings에서 `Extension Search Paths` 항목을 찾는다.
3. 새 경로에 저장소의 `extensions` 폴더 절대 경로를 입력한다. 예: `/home/사용자명/robotics-sim-tutorial-kr/extensions`.
4. `.../extensions/tutorial.scene/config`를 등록하지 않는다. Extension 폴더들이 들어 있는 **상위 폴더**가 검색 경로이다.
5. 검색창에 `tutorial.scene` 또는 `Tutorial Scene Builder`를 입력한다. `@feature` 같은 필터가 있으면 지운다.
6. 외부 경로에서 추가한 Extension이므로 Third Party 항목도 확인한다.
7. 활성화 스위치를 켠다. `Tutorial Scene Builder` 창이 나타나는지 확인한다.

이 경로 등록 절차는 공식 Extension Template Generator의 안내를 따른다. [공식 6.0.1 Extension Template Generator](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/utilities/extension_template_generator.html)

터미널에서 새 앱을 시작할 때 검색 경로와 활성화를 함께 지정하는 방법도 있다.

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" \
  --ext-folder "$TUTORIAL_ROOT/extensions" \
  --enable tutorial.scene
```

## 재로딩을 확인하기

Extension을 끄면 창이 사라지고 다시 켜면 창 하나가 나타나야 한다. hot reload 설정에 따라 파일 저장 시 재로딩될 수도 있으므로, 처음에는 Manager에서 끄고 켜는 절차로 확인한다. 큰 물리 실험이 실행 중일 때 코드 변경과 재로딩을 동시에 진행하지 않는다.

물리 콜백이나 비동기 작업을 추가한 Extension이라면 종료 시 해당 콜백 ID를 해제하고 작업을 취소해야 한다. 다른 Extension의 콜백까지 삭제하는 `deregister_all_callbacks()`는 일반적인 정리 방법으로 사용하지 않는다. 이 예제는 버튼으로 동작하는 작은 도구여서 별도 반복 콜백이 없다.

**예상 결과:** 창에 Create / Reset Scene, Remove Scene 버튼과 상태 문구가 보인다. 버튼의 구체적인 동작은 다음 단계에서 검사한다.

**진단:** 검색되지 않으면 검색 경로와 manifest 이름을, 활성화 직후 꺼지면 Console의 import 오류와 `[[python.module]]` 값을 확인한다. 창의 X 버튼만 닫은 경우에는 Extension을 한 번 끄고 켜서 다시 연다.

**완료 기준:** manifest의 세 부분을 설명하고 활성화→비활성화→활성화 후 창이 하나만 존재함을 확인한다.

**과제:** 공식 `Utilities > Generate Extension Templates`에서 템플릿을 별도 폴더에 생성한다. 제공된 최소 도구와 비교해 UI 코드와 장면 로직이 어디서 연결되는지 찾아본다. [공식 템플릿 구조 설명](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/utilities/extension_templates_tutorial.html)

[이전](15-project-drop-test.md) · [다음: 중간 프로젝트 3](17-project-scene-extension.md) · [학습 목차](../../README.md)
