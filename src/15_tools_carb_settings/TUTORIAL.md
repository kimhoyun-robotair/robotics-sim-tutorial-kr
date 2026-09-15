# 15. Modify Carb Settings

권장 학습 순서 **15** · Python 실행 환경과 USD 기초 · 출처 ID `t091`

이 패키지의 작은 확장은 startup 때 `foo` 값을 읽는다. Script Editor, 명령행, extension TOML, app KIT의 네 가지 설정 위치를 실제 값으로 비교한다.

## 이 실습의 의도

하나의 Carb 설정 `/exts/kr.settings.demo/data/foo`를 확장 시작 시 읽어, 실행 중 변경과 다음 앱 실행에도 남는 설정의 차이를 비교합니다. 작은 확장은 장면을 만들거나 로봇을 움직이지 않고 `on_startup()`에서 읽은 값을 출력합니다. 기본 TOML, Script Editor, 명령행 인자, 사용자 app 설정을 차례로 바꾸며 **어디에 값을 썼는지와 언제 읽었는지**를 연결하는 실습입니다.

## 실행 후 확인할 것

- 원본 `extension.toml`을 유지하고 별도 설정 인자 없이 확장을 켰다면 Console/터미널에 `kr.settings.demo startup foo = False`가 나와야 합니다. 이 값이 이후 비교의 기준입니다.
- Script Editor에서 `change_setting.py`를 실행하면 확장이 꺼졌다 켜지며 `shutdown` 다음의 startup 값과 `live setting`이 `True`인지 확인합니다. 현재 프로세스의 값을 바꾸고 다시 읽는 동작입니다.
- TOML을 수정하지 않은 상태에서 앱을 완전히 종료하고 인자 없이 다시 실행하면 기본값 `False`로 돌아오는지 봅니다. USD Stage 저장은 이 설정을 보존하지 않습니다.
- `--/exts/kr.settings.demo/data/foo=true`를 넣은 실행은 startup이 `True`인지 확인합니다. TOML을 false로 유지한 채 CLI 인자만 바꿔야 두 설정 위치의 차이를 판단할 수 있습니다.
- 설정을 저장하는 단계에서는 extension TOML 또는 사용자 app KIT를 수정한 뒤 재실행해 startup 값을 봅니다. `app_settings.toml` 자체는 붙여 넣을 설정 조각이므로 이 파일만 실행해서 앱이나 결과 창이 만들어지는 실습은 아닙니다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 1. 로컬 확장 기본값

터미널에서 기존 앱을 종료한 뒤 이 폴더의 절대 경로를 사용한다.

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.settings.demo
```

`config/extension.toml`의 `[settings]` 기본값은 false다. Console/터미널에서 `startup foo = False`를 확인한다. `omni.ext.IExt.on_startup`은 활성화 때 실행되므로 설정을 읽는 시점이 중요하다.

## 2. Script Editor 변경과 재시작

`Window > Script Editor`에서 `change_setting.py`를 열고 Run한다. 설정 경로 `/exts/kr.settings.demo/data/foo`는 TOML의 점 표기와 같은 키다. `settings.set`은 현재 프로세스의 값을 바꾸고 extension manager의 disable/enable은 startup을 다시 실행한다. 두 번째 startup 출력이 True인지 본다. 앱 재시작 시에는 TOML 기본값으로 돌아간다.

## 3. 명령행

```bash
"$ISAAC_SIM_PATH/isaac-sim.sh" --ext-folder /absolute/path/to/this-package/exts --enable kr.settings.demo --/exts/kr.settings.demo/data/foo=true
```

startup이 True다. 다음 실행에서 인자를 빼면 false로 돌아간다.

## 4. TOML과 KIT에 저장

1. 이 패키지의 `exts/kr.settings.demo/config/extension.toml`에서 `foo = false`를 `true`로 바꾸고 저장한다. 다시 앱을 시작하면 인자가 없어도 true다.
2. 여러 확장의 기본값을 묶는 app KIT도 TOML 문법이다. 사용 중인 **사용자 소유 app**의 `.kit`에서 `[settings]` 표 아래 `exts."kr.settings.demo".data.foo = true`를 넣으면 된다. 이미 `[settings]`가 있으면 표를 중복 선언하지 않는다.
3. 독립 app 구성까지 재현하려면 이 폴더 output 아래 공식 App Template v5.1.0을 받는다.

```bash
git clone --branch v5.1.0 https://github.com/isaac-sim/isaacsim-app-template.git /absolute/path/to/this-package/output/app-template
cd /absolute/path/to/this-package/output/app-template
```

4. 그 폴더의 `source/apps/isaacsim.exp.full.kit`에서 기존 `[settings]` 안에 제공 `app_settings.toml`의 `exts...foo = true` 한 줄을 추가한다. `[settings]` 표 자체를 중복 복사하지 않는다. 원래 설치의 apps 파일은 수정하지 않는다.

```bash
./repo.sh build
./_build/linux-x86_64/release/isaacsim.exp.full.kit.sh --ext-folder /absolute/path/to/this-package/exts --enable kr.settings.demo
```

5. startup foo=True를 확인한다. app template 빌드는 별도 SDK/dependency 다운로드가 필요하다. 제공 `app_settings.toml`은 설정 조각이며 독립 실행 app 파일이 아니다. 고정 template 커밋은 `6c344c155b823ce3f5797fd21bc24fb8d90f5e11`이다.

한 변수 실험: TOML false를 유지하고 CLI만 true로 바꿔 우선순위를 관찰한다. 설정은 USD prim attribute와 다르므로 Stage를 저장해도 Carb 설정은 USD에 들어가지 않는다. extension 검색 실패는 `--ext-folder`가 확장 자체가 아니라 그 부모 `exts`인지 확인한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 위의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/carb_settings.html).
