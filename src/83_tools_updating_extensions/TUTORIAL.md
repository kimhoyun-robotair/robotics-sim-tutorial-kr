# 83. Adding and Updating Extensions Guide

권장 학습 순서 **83** · OmniGraph와 확장 개발 · 출처 ID `t172`

로컬 extension 경로 추가, 활성화, 버전 변경 확인과 registry UPDATE 동작을 구분한다. 이 폴더의 실제 작은 UI 확장으로 검색/활성/재로드를 연습한다.

## 이 실습의 의도

로컬 확장을 검색할 수 있는 상태, 실제 Python 모듈이 활성화된 상태, 선택된 package 버전이 바뀐 상태를 각각 확인하는 실습이다. `kr.version.lesson`은 버튼 한 번으로 USD Cube를 만들어 경로 검색과 버전 표시를 실제 callback 실행까지 연결한다. 제공 확장에는 registry 다운로드나 UPDATE 자동화가 없으며, 로컬 metadata 변경과 원격 registry 업데이트는 아래에서 따로 수행한다.

## 실행 후 확인할 것

- Extension Search Paths에 `exts` 부모 경로를 추가한 뒤 Third Party에서 `kr.version.lesson`, version=`1.0.0`이 발견되는지 확인한다. 검색 결과의 실제 경로도 보아 같은 이름의 다른 설치본을 활성화하지 않았는지 확인한다.
- Enabled 후 **Korean Extension Starter** 창에서 **Create Cube**를 누르면 Stage의 `/World/ExtensionCube`와 Console의 `created /World/ExtensionCube`가 나타나야 한다. Cube의 size=`0.3`, translate=`(0, 0, 0.5)`를 Property에서 확인한다.
- Cube는 `UsdGeom.Cube`만 정의하므로 강체·충돌 동작이 없고 Play해도 떠 있는 것이 정상이다. 같은 Stage에서 버튼을 다시 누르면 `ExtensionCube exists` 오류를 내어 기존 prim을 덮어쓰지 않는다.
- 확장을 끄면 창이 없어지고 기존 Cube는 Stage에 남는지 확인한다. version을 `1.0.1`로 바꾼 후 목록에서 새 버전을 확인하고, 새 Stage에서 버튼까지 다시 실행해 실제 선택된 코드가 동작하는지 본다. 창 제목은 Python 문자열이므로 TOML title 변경과 자동으로 일치하지 않을 수 있다.
- registry 실습에서는 현재 제공되는 버전과 INSTALL/UPDATE 표시를 확인한다. UPDATE가 없는 상태도 가능한 결과이며, 로컬 version 숫자만 바꾼 것은 원격 패키지를 내려받아 갱신한 결과가 아니다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 로컬 경로 추가와 활성화

1. `Window > Extensions`를 열고 우측 메뉴→**Settings**로 들어간다.
2. **Extension Search Paths**의 +를 눌러 이 패키지의 `/absolute/path/to/this-package/exts`를 추가한다. `kr.version.lesson` 폴더 자체가 아닌 **부모** 경로다.
3. **Third Party** 탭에서 `kr.version.lesson` 또는 Korean Extension Starter를 검색한다. package version=`1.0.0`을 확인하고 Enabled를 켠다.
4. 창의 **Create Cube**를 눌러 `/World/ExtensionCube`가 생기는지 확인한다. 로컬 경로를 검색한 것과 실제 코드를 활성화한 것은 서로 다른 단계다.

## 로컬 버전 수정

1. 확장을 끈다. 이 패키지 `exts/kr.version.lesson/config/extension.toml`의 version을 `1.0.0 → 1.0.1`로 바꾼다. title도 구분 가능한 이름으로 변경한다.
2. Extensions 목록을 다시 검색/refresh하고 필요하면 Isaac Sim을 재시작한다. version 1.0.1이 선택되는지 확인한다.
3. 새 Stage에서 확장을 켜고 Create Cube를 다시 실행한다. 버전 metadata 변경만으로 잘못된 코드가 고쳐지는 것은 아니므로 실제 callback도 확인한다.

## Registry 설치/업데이트

1. 이미 등록된 registry의 확장은 Search로 찾는다. 공식 예시는 `omni.kit.window.tests`이며 없다면 다른 이름으로 추측하지 말고 현재 registry의 제공 여부를 확인한다.
2. 아직 설치되지 않은 항목은 **INSTALL**, 설치된 항목의 새 호환 버전이 있으면 **UPDATE**가 표시된다. UPDATE가 없다고 실패가 아니라 새 버전이 없거나 현재 app과 호환되지 않을 수 있다.
3. 원문은 `isaacsim.asset.importer.mjcf`를 업데이트 예시로 든다. 이 실습의 5.1 재현성을 유지하려면 먼저 현재 버전/dependency를 기록하고 **5.1 호환 버전**을 선택한다. 일부 확장은 재시작이 필요하다.
4. 새 registry를 추가할 때는 Settings의 **Extension Registries** +에 실제 제공자의 전체 URL을 넣는다. 로컬 search path와 registry URL은 서로 다른 입력란이다. 임의 URL을 예제로 실제 등록하지 않는다.

extension.toml의 package version은 코드 배포 버전, dependency는 필요한 확장이다. extension 활성 상태는 USD Stage에 저장되는 geometry와 별개다. 한 변수 실험은 로컬 version만 1.0.1로 바꾸어 표시와 선택 버전이 바뀌는지 확인한다. 성공은 경로 발견, 실제 UI callback, 버전 표시 일치다. 예제가 안 보이면 Third Party 탭과 부모 경로, 중복 이름의 다른 설치본을 점검한다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 앞의 확인 항목을 실제 실행 후 점검해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/updating_extensions.html).
