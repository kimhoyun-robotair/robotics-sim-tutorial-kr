# 83. 로컬 확장을 찾아 켜고 버전 확인하기

## 이번에 배우는 것

**작은 UI 확장을 등록해 큐브 생성 버튼을 실행하고, 검색 경로·활성화·버전 변경이 각각 무엇을 바꾸는지 확인합니다.**

확장이 검색된다고 그 코드가 실행 중인 것은 아닙니다. 반대로 창이 열려 있어도 지금 선택된 것이 내가 수정한 폴더인지 확인해야 할 때가 있습니다. 이번에는 로컬 확장 하나로 발견부터 실제 버튼 동작까지 연결합니다.

| 구성 | 위치 또는 값 | 역할 |
|---|---|---|
| 확장 부모 폴더 | 이 폴더의 `exts` | Extension Search Paths에 등록할 위치 |
| 확장 ID | `kr.version.lesson` | 검색할 패키지 이름 |
| 메타데이터 | `config/extension.toml` | 버전 1.0.0, 의존성, 모듈 지정 |
| Python 코드 | `kr_version_lesson/__init__.py` | 창과 버튼 callback 구현 |
| 생성할 prim | `/World/ExtensionCube` | 버튼 실행 결과 |

Callback은 버튼을 눌렀을 때 호출하도록 연결한 함수입니다. 확장 목록의 표시뿐 아니라 그 함수가 현재 Stage에 실제 큐브를 만드는지 확인합니다.

## 1. 로컬 경로를 등록하고 버튼 실행하기

Isaac Sim 5.1.0 GUI와 지원 NVIDIA GPU 환경에서 실행합니다. 저장소 루트에서 다음 명령을 사용하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다.

```bash
~/isaacsim/isaac-sim.sh
```

1. **File > New**로 새 Stage를 엽니다.
2. **Window > Extensions**의 우측 메뉴에서 **Settings**를 엽니다.
3. **Extension Search Paths**의 `+`를 누르고 `src/83_tools_updating_extensions/exts`의 절대 경로를 추가합니다.
4. **Third Party**에서 `kr.version.lesson` 또는 `Korean Extension Starter`를 검색합니다.
5. 선택된 항목의 경로와 버전 `1.0.0`을 확인하고 Enabled를 켭니다.
6. 열린 **Korean Extension Starter** 창에서 **Create Cube**를 누릅니다.

검색 경로에는 `kr.version.lesson` 자체가 아니라 그 **부모인 `exts`**를 넣습니다. 이 폴더 안의 여러 확장을 함께 찾도록 하는 구조입니다. 같은 이름의 확장을 다른 위치에서도 등록했다면 실제 선택된 경로를 확인하세요.

### 실행 결과 확인하기

Stage에 `/World/ExtensionCube`가 생기고 Console에는 `created /World/ExtensionCube`가 나오는지 확인합니다. Property에서 크기 `0.3`, 위치 `(0, 0, 0.5)`를 확인하세요. m 단위 Stage에서는 한 변이 0.3 m인 큐브입니다.

같은 Stage에서 버튼을 다시 누르면 `ExtensionCube exists` 오류가 납니다. 기존 큐브를 덮어쓰지 않게 한 코드의 동작입니다. 반복하려면 결과를 저장한 뒤 새 Stage를 열어 실행하세요.

## 2. TOML과 Python이 연결되는 방식 읽기

### 설정에서 볼 부분

`exts/kr.version.lesson/config/extension.toml`의 핵심은 다음과 같습니다.

```toml
[package]
version = "1.0.0"
title = "Korean Extension Starter"

[dependencies]
"omni.kit.uiapp" = {}
"omni.usd" = {}

[[python.module]]
name = "kr_version_lesson"
```

`package`는 목록에 표시할 패키지 정보입니다. `dependencies`는 UI와 USD를 사용하기 위해 필요한 확장을 나타냅니다. `python.module`은 활성화 시 불러올 Python 모듈 이름이며, 폴더의 `kr_version_lesson`과 연결됩니다.

### 코드에서 볼 부분

Python의 `on_startup()`은 창을 만들고 버튼에 함수를 연결합니다.

```python
ui.Button("Create Cube", clicked_fn=self.create_cube)
```

여기서 `self.create_cube`는 지금 함수를 실행한 결과가 아니라, 나중에 클릭할 때 부를 함수 자체입니다. 버튼을 누르면 그 함수에서 현재 Stage를 가져와 다음을 실행합니다.

```python
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.3)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
```

크기와 이동값을 USD에 작성합니다. 강체나 충돌 schema를 적용하는 코드는 없으므로, Play해도 큐브가 공중에 머무는 것이 정상입니다. 큐브 생성은 시뮬레이션 재생을 기다리지 않고 버튼 클릭으로 이루어집니다.

### 실행 결과 확인하기

Extensions에서 이 확장을 끄세요. `on_shutdown()`이 창을 파괴하므로 창은 사라집니다. 그러나 그 함수는 Stage의 Cube를 삭제하지 않습니다. **확장 UI의 수명과 장면 데이터의 수명은 다릅니다.** 생성 결과를 보존하려면 File > Save As로 USD를 저장해야 합니다.

다시 켜면 창이 새로 생깁니다. 이전 Cube가 있는 장면에서 버튼을 누르면 여전히 중복 오류가 나는지 확인하세요. 이것으로 비활성화가 장면을 초기화하는 동작이 아니라는 점을 알 수 있습니다.

## 3. 로컬 버전과 Registry 업데이트 정리

| 조작 | 바꾸는 대상 | 확인할 결과 |
|---|---|---|
| Search Path 추가 | 발견할 로컬 폴더 | 목록에 패키지 표시 |
| Enabled 켜기 | 실행 중인 모듈과 UI | 창과 버튼 callback |
| 로컬 `version` 편집 | 내가 가진 패키지의 메타데이터 | 선택된 버전 표시 |
| Registry의 INSTALL / UPDATE | 제공자가 배포한 패키지 | 설치 또는 갱신된 패키지와 코드 |

Registry는 배포된 확장을 찾고 내려받는 저장소입니다. Extensions의 Settings에서 로컬 경로는 **Extension Search Paths**, 제공자의 URL은 **Extension Registries**에 들어갑니다. 두 입력란을 서로 바꾸어 사용하지 않습니다.

공식 안내의 설치 예시는 `omni.kit.window.tests`, 업데이트 예시는 `isaacsim.asset.importer.mjcf`입니다. 현재 Registry에서 항목과 호환 버전이 제공되는지 먼저 확인하세요. INSTALL은 패키지를 설치하고, 설치된 항목에 새 버전이 있으면 UPDATE로 갱신합니다. 일부 변경은 앱 재시작이 필요합니다.

이 로컬 실습의 확인에는 원격 패키지 설치가 필요하지 않습니다. Registry 동작을 이어서 살펴볼 때는 현재 버전과 의존성을 기록하고 Isaac Sim 5.1과 호환되는 항목을 선택하세요. UPDATE 버튼이 없다는 것만으로 로컬 등록이 실패한 것은 아닙니다.

## 4. 간단한 확인 실험

확장을 끈 상태에서 `extension.toml`의 **version만 `1.0.0`에서 `1.0.1`로** 바꿔 보세요. title과 Python 코드는 유지합니다.

1. Extensions 목록을 다시 검색하거나 새로 고침합니다. 이전 정보가 남으면 앱을 재시작합니다.
2. 선택된 경로가 자신의 로컬 폴더이고 버전이 `1.0.1`인지 확인합니다.
3. 새 Stage에서 확장을 켜고 Create Cube를 다시 누릅니다.

예상하는 변화는 목록의 버전 표시입니다. 창 제목과 큐브 생성 동작은 코드를 바꾸지 않았으므로 같아야 합니다. 버전 번호를 높이는 것만으로 새 기능이 생기거나 원격 업데이트가 이루어지지 않는다는 점을 확인하세요.

## 실행할 때 막히면

- **확장이 검색되지 않음**: 등록한 경로가 `exts`의 절대 경로인지, Third Party 탭을 보고 있는지 확인하세요.
- **다른 버전이 켜짐**: 같은 ID의 다른 설치본이 있는지 실제 패키지 경로를 확인하고 목록을 갱신하세요.
- **목록에는 있지만 창이 없음**: Enabled 상태와 Console의 모듈 로딩 오류를 확인하세요. 검색과 활성화는 다른 단계입니다.
- **`ExtensionCube exists`**: 이미 같은 경로의 prim이 있습니다. 결과를 저장하고 새 Stage에서 버튼을 다시 누르세요.
- **확장을 껐는데 큐브가 남음**: 종료 함수는 UI만 정리합니다. Stage geometry가 남는 것이 이 코드의 동작입니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Adding and Updating Extensions Guide](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html)에 대응합니다. 공식 검색·활성화 절차에 로컬 UI 확장을 제공하여 실제 callback과 버전 표시까지 확인하도록 구성했습니다.

이번 개정에서는 TOML과 Python 구현을 대조했습니다. GUI 로딩·버튼 클릭·Registry 설치는 실행하지 않았고 `tutorial.json`은 `not_run`입니다. 원격 패키지 갱신을 완료한 예제로 해석하지 않습니다.
