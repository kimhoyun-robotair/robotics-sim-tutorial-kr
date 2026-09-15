# 15. 설정값은 어디에 쓰고 언제 읽을까요?

## 이번에 배우는 것

**하나의 Carb 설정을 네 위치에서 바꾸며, 실행 중의 값과 다음 실행의 기본값을 구분합니다.**

Carb 설정은 Isaac Sim 앱과 확장이 사용하는 설정 저장소입니다. 이번에는 `/exts/kr.settings.demo/data/foo`라는 Boolean 값 하나를 읽는 작은 확장을 사용합니다. `False`와 `True`를 출력할 뿐 장면을 만들지는 않으므로, 변화는 뷰포트가 아닌 터미널의 로그에서 확인합니다.

| 값을 쓰는 위치 | 적용하는 때 | 앱을 다시 켰을 때 |
|---|---|---|
| Script Editor의 `settings.set()` | 현재 앱 실행 중 | 이번 메모리 변경은 남지 않음 |
| 명령행 `--/exts/.../foo=true` | 앱을 시작할 때 | 같은 인자를 다시 줘야 함 |
| 확장의 `extension.toml` | 확장을 불러올 때의 기본값 | 파일에 쓴 값이 남음 |
| 사용자 앱의 `.kit` | 해당 앱 구성을 불러올 때 | 같은 앱 구성에서 다시 사용함 |

이번 확장은 **켜질 때 한 번** 설정을 읽습니다. 따라서 설정 저장소의 값이 바뀌었다는 것과, 확장이 그 값을 다시 읽었다는 것은 별도로 확인해야 합니다.

## 1. 먼저 확장의 기본값 읽기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 있는 환경에서 실행합니다. 아래는 저장소 루트 기준 Linux 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/15_tools_carb_settings/exts" \
  --enable kr.settings.demo
```

`--ext-folder`는 확장들이 들어 있는 부모 `exts` 폴더를 가리킵니다. `$PWD`를 사용하므로 이 명령은 저장소 루트에서 실행해야 합니다. 앱은 창을 닫을 때까지 유지됩니다.

### 설정에서 볼 부분

`exts/kr.settings.demo/config/extension.toml`의 기본 설정입니다.

```toml
[settings]
exts."kr.settings.demo".data.foo = false
```

TOML에서 따옴표로 묶은 `kr.settings.demo`는 확장 이름 하나입니다. 이 표기는 Python에서 사용하는 `/exts/kr.settings.demo/data/foo` 경로와 같은 설정을 가리킵니다.

확장의 `kr_settings_demo/__init__.py`에서는 다음과 같이 읽습니다.

```python
def on_startup(self, ext_id):
    self.value = carb.settings.get_settings().get("/exts/kr.settings.demo/data/foo")
    print("kr.settings.demo startup foo =", self.value)
```

`on_startup()`은 확장이 활성화될 때 호출됩니다. `self.value`에는 그 시점의 값이 들어갑니다. 이후 설정이 바뀌어도 이 변수에 저절로 다시 대입되지는 않습니다.

### 실행 결과 확인하기

원본 TOML을 유지하고 별도의 설정 인자를 주지 않았다면 터미널에서 다음 출력을 찾습니다.

```text
kr.settings.demo startup foo = False
```

큐브나 로봇이 새로 나타나지 않는 것이 정상입니다. 이번 비교의 기준은 확장이 실제로 읽어서 출력한 `False`입니다.

## 2. 실행 중 변경과 파일에 남는 변경 비교하기

### 코드에서 볼 부분

열린 앱에서 **Window > Script Editor**를 열고 이 폴더의 `change_setting.py` 전체를 실행하세요. 핵심 흐름은 다음과 같습니다.

```python
settings.set("/exts/kr.settings.demo/data/foo", True)
manager.set_extension_enabled_immediate("kr.settings.demo", False)
manager.set_extension_enabled_immediate("kr.settings.demo", True)
```

첫 줄은 현재 설정을 바꿉니다. 뒤의 두 줄은 확장을 껐다 켜서 `on_startup()`이 새 값을 읽게 합니다. 앱 전체를 재시작하는 동작과는 다릅니다.

### 실행 결과 확인하기

출력에서 다음 순서를 찾아보세요.

```text
kr.settings.demo shutdown
kr.settings.demo startup foo = True
live setting True
```

`startup`은 확장이 다시 읽은 값이고, `live setting`은 스크립트 끝에서 설정 저장소를 직접 읽은 값입니다. 둘 다 `True`인지 확인한 다음 앱을 완전히 종료합니다. 원본 TOML 상태로 1절 명령을 다시 실행하면 `False`로 돌아오는지 보세요.

### 명령행에서 시작값 지정하기

앱을 종료하고 다음 명령으로 실행합니다.

```bash
~/isaacsim/isaac-sim.sh \
  --ext-folder "$PWD/src/15_tools_carb_settings/exts" \
  --enable kr.settings.demo \
  --/exts/kr.settings.demo/data/foo=true
```

이번에는 처음 `startup`부터 `True`를 기대합니다. Script Editor를 실행할 필요가 없습니다. 다음 실행에서 마지막 인자를 빼면 TOML 기본값을 다시 사용합니다.

### TOML과 KIT에 값 남기기

파일 설정을 비교하려면 앱을 종료하고 아래 순서로 진행하세요.

1. 이 실습의 `extension.toml`에서 `foo = false`만 `foo = true`로 바꿉니다.
2. 추가 설정 인자 없이 1절 명령을 실행합니다. 처음부터 `True`인지 확인합니다.
3. 다음 비교를 위해 TOML을 `false`로 되돌립니다.

여러 확장의 설정을 앱별로 묶고 싶다면 사용자 소유 `.kit`의 기존 `[settings]` 안에 다음 한 줄을 넣습니다.

```toml
exts."kr.settings.demo".data.foo = true
```

이 폴더의 `app_settings.toml`이 그 설정 조각입니다. **이 조각 자체는 실행 가능한 앱이 아닙니다.** 별도의 사용자 앱 구성이 있는 경우 그 `.kit`에 병합하고, 해당 앱의 실행 방법으로 시작하면서 위의 `--ext-folder`와 `--enable` 인자도 전달하세요. `[settings]` 표가 이미 있으면 중복 선언하지 않습니다.

### 사용자 KIT 앱을 직접 준비하기

사용자 앱이 아직 없다면 공식 [Isaac Sim App Template v5.1.0](https://github.com/isaac-sim/isaacsim-app-template/tree/v5.1.0)을 별도 폴더에 준비해 네 번째 방식도 비교할 수 있습니다. 이 단계는 Linux x86_64 기준이며 Git, 빌드 의존성 및 SDK 다운로드가 필요합니다. 저장소 루트에서 시작하세요.

```bash
export SETTINGS_LESSON_DIR="$PWD/src/15_tools_carb_settings"
mkdir -p "$SETTINGS_LESSON_DIR/output"
git clone --branch v5.1.0 --depth 1 https://github.com/isaac-sim/isaacsim-app-template.git "$SETTINGS_LESSON_DIR/output/app-template"
cd "$SETTINGS_LESSON_DIR/output/app-template"
```

새 폴더의 `source/apps/isaacsim.exp.full.kit`을 열고 기존 `[settings]` 바로 아래에 `exts."kr.settings.demo".data.foo = true` 한 줄을 넣습니다. 원래 Isaac Sim 설치의 `.kit`은 이 비교의 수정 대상이 아닙니다. 확장 `extension.toml`은 `false` 상태로 유지하고 다음을 같은 터미널에서 실행하세요.

```bash
./repo.sh build
./_build/linux-x86_64/release/isaacsim.exp.full.kit.sh --ext-folder "$SETTINGS_LESSON_DIR/exts" --enable kr.settings.demo
```

`startup foo = True`라면 이 앱의 KIT 설정이 확장의 기본값보다 우선한 것을 확인한 것입니다. 빌드 자체가 끝난 것과 이 실행 로그를 확인한 것은 구분하세요. 기존 설치로 실행한 1절의 `False`와 비교하고, 앱을 닫은 뒤 `cd "$SETTINGS_LESSON_DIR/../.."`로 저장소 루트에 복귀하세요. `app-template`이 이미 있으면 새 폴더 이름으로 복사본을 만들고 위 경로를 맞춥니다.

## 3. 값의 위치와 읽는 시점 정리

```text
TOML / KIT / 명령행 → 앱의 설정 저장소
                              ↓ on_startup에서 읽기
                         확장의 self.value

Script Editor의 set → 설정 저장소 변경
                      → 확장을 다시 켜기 → self.value도 새로 읽음
```

이 예제에서는 확장 재시작으로 새 값을 읽지만, 실행 중에 설정을 계속 읽도록 작성된 다른 기능은 곧바로 반응할 수도 있습니다. **설정 적용 시점은 그 값을 사용하는 코드가 결정합니다.**

Carb 설정은 USD Prim의 속성과도 다릅니다. **File > Save**로 장면을 저장해도 이번 `foo` 변경이 USD 장면에 들어가지는 않습니다.

## 4. 간단한 확인 실험

`extension.toml`의 기본값을 `false`로 유지하고 **명령행의 `foo` 인자 유무만** 바꿔 두 번 실행해 보세요.

- 인자 없이 시작: `startup foo = False`
- `--/exts/kr.settings.demo/data/foo=true`를 추가해 시작: `startup foo = True`

각 실행은 앱을 완전히 종료한 뒤 시작합니다. Script Editor 변경을 섞지 않으면, 파일 기본값과 이번 실행에서 지정한 값의 차이를 분명하게 볼 수 있습니다.

## 실행할 때 막히면

- **확장을 찾지 못함**: `--ext-folder`가 `kr.settings.demo` 자체가 아닌 그 부모 `exts`를 가리키는지 확인하세요.
- **`startup` 출력이 없음**: `--enable kr.settings.demo`를 전달했는지 확인하세요. 검색 경로 추가만으로 확장이 활성화되지는 않습니다.
- **설정은 True인데 저장한 변수는 False임**: 값을 읽은 시점이 다릅니다. 제공 `change_setting.py`처럼 확장을 껐다 켜서 다시 읽으세요.
- **재실행해도 예상한 기본값으로 돌아가지 않음**: CLI 인자, 수정한 `extension.toml`, 사용 중인 `.kit`을 확인하세요. 비교에 사용한 설정 위치를 하나씩 유지해야 합니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Modify Carb Settings](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/development_tools/carb_settings.html)에 대응합니다. 원문의 네 설정 위치를 출력 전용 로컬 확장으로 설명하며, 확장 시작 로그로 값을 비교하도록 구성했습니다.

현재 `tutorial.json`의 상태는 `not_run`입니다. 이번 개정에서는 Python과 TOML의 동일한 키, 확장 활성화 순서, 공식 설정 방식을 대조했습니다. GUI 재실행과 사용자 `.kit` 구성은 실제로 실행해 검증하지 않았습니다.
