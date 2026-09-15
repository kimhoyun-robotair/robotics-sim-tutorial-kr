# 84. Extension Template Generator

권장 학습 순서 **84** · OmniGraph와 확장 개발 · 출처 ID `t164`

공식 생성기로 네 템플릿을 만드는 실습과 즉시 실행 가능한 작은 독립 UI extension을 함께 제공한다. 생성 결과의 README는 NVIDIA 생성기 산출물이며 이 저장소 README를 변경하는 절차가 아니다.

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

## 제공된 최소 확장 먼저 실행하기

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.template.starter
```

Korean Extension Starter 창의 **Create Cube**를 누르면 `/World/ExtensionCube`가 생긴다. 이 최소 예제는 extension.toml의 package/dependencies/python.module, `omni.ext.IExt` startup/shutdown, `omni.ui.Button` callback의 관계를 보여준다. official generator 산출물의 대체 구현이라고 주장하지 않는다.

생성된 확장의 `scripts/global_variables.py`는 이름/설명, `scripts/extension.py`는 메뉴/lifecycle, `scripts/ui_builder.py`는 사용자 UI/동작을 담당한다. 일반 수정 지점은 ui_builder다. ui.Button은 사용자가 클릭할 때 callback을 호출하고 Cube API는 USD에 prim을 만든다. UI창 종료와 Stage의 Cube 삭제는 서로 별개다.

한 변수 실험: 제공 starter의 Cube size만 0.3→0.6으로 수정하고 확장을 껐다 켠 뒤 새 Stage에서 Create Cube를 누른다. 성공은 UI 재로드와 실제 크기 변화다. 확장 검색 실패는 search path에 확장 자체가 아닌 부모가 들어갔는지 확인한다. 생성 템플릿에서 Load가 장면을 바꾸므로 보관할 Stage는 먼저 저장한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html).
