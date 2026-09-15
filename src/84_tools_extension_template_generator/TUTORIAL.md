# 84. Extension Template Generator

권장 학습 순서 **84** · OmniGraph와 확장 개발 · 출처 ID `t164`

공식 생성기로 네 템플릿을 만드는 실습과 즉시 실행 가능한 작은 독립 UI extension을 함께 제공한다. 생성 결과의 README는 NVIDIA 생성기 산출물이며 이 저장소 README를 변경하는 절차가 아니다.

## 이 실습의 의도

공식 생성기가 만드는 네 템플릿을 각각 생성·활성화하고, 템플릿에 따라 장면과 제어를 누가 준비해야 하는지 확인한다. 함께 제공한 `kr.template.starter`는 startup→UI 버튼→USD prim 생성→shutdown의 최소 연결을 보여주며, 이를 켠다고 네 공식 템플릿이 생성되지는 않는다. 공식 생성 버튼은 파일을 만들고, 확장 검색 경로 등록·Enabled·각 템플릿의 Load/Run은 별도로 수행해야 한다.

## 실행 후 확인할 것

- Generate 후 `output/extensions` 아래 `kr.loaded`, `kr.scripted`, `kr.configuration`, `kr.components`의 파일과 생성 README가 각각 있는지 확인한다. 부모 search path를 등록한 뒤 각 이름이 Extensions에 검색되어 실제 메뉴/창을 여는지까지 본다.
- Loaded Scenario에서 **Load → Run → Stop → Reset**을 수행한다. 설치된 기본 템플릿의 `/ur10e` 관절이 순차적으로 움직이고 `/Scenario/cuboid`가 로봇 주위를 돌며, Stop 시 갱신이 멈추고 Reset 후 다시 시작할 상태로 돌아오는지 확인한다.
- Scripting에서는 Load/Run 후 로봇의 목표 이동과 gripper 개폐가 순서대로 진행되는 동안 UI가 응답하는지 본다. Configuration에서는 별도로 Franka를 추가하고 Play한 뒤 dropdown으로 선택해야 관절 UI와 실제 관절 이동을 확인할 수 있다.
- UI Component Library에서는 FloatField·체크박스·버튼의 callback에 전달되는 값과 타입을 생성 코드와 대조한다. 필드가 보이거나 바뀌었다는 것과 연결된 callback이 호출되는 것은 별도로 확인한다.
- 제공 starter의 **Create Cube**는 `/World/ExtensionCube`에 size=`0.3`, 높이 `0.5`의 도형을 만든다. 강체·충돌을 추가하지 않아 Cube가 떨어지지 않고, 확장을 꺼 창을 없애도 prim은 남는다. 이 결과로 공식 템플릿의 로봇 실행까지 완료했다고 판단하지 않는다.

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

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/extension_template_generator.html).
