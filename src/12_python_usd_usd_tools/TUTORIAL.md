# 12. USD 도구: 끊어진 자산 경로와 Variant

권장 학습 순서 **12** · Python 실행 환경과 USD 기초 · 출처 ID `t175`

## 이 실습의 의도

USD Paths와 Variant 도구가 다루는 데이터를 이해하도록 일부러 끊어진 참조를 만들고, 경로를 고친 파일에서 색 대안을 선택한다. 원본 `broken.usda`는 보존하고 `repaired.usda`에 경로 치환 결과를 저장해, 파일 경로 문제와 Prim 내부의 variant 선택을 분리해서 비교한다. 기본 실행은 로컬 API로 복구와 `finish=red` 선택까지 수행하고 보고서를 남기며, GUI의 USD Paths·Variant Presenter·Variant Editor 조작은 후속 수동 실습이다.

## 실행 후 확인할 것

- `tools_report.json`에서 `broken_has_body`는 `false`, `repaired_has_body`는 `true`인지 확인한다. `broken.usda`의 없는 `old_assets/body.usda` 참조 경고와 Body 누락은 의도된 출발 상태이며, 복구된 장면에서도 Body가 없으면 문제다.
- 보고서의 `path_changes`에 `old_assets/body.usda` → `moved_assets/body.usda` 치환이 있는지 확인한다. 실제 `moved_assets/body.usda` 파일도 존재해야 하며, 문자열만 바뀌고 참조가 해결되지 않은 결과는 성공으로 보지 않는다.
- `variants`에 `red`, `blue`가 있고 기본 `selection`은 `red`, `color`는 `[1, 0, 0]`인지 확인한다. `--variant blue` 실행은 `selection=blue`, `color=[0, 0, 1]`이어야 한다. 목록의 순서는 기준이 아니다.
- GUI에서 `repaired.usda`의 `/World/Robot/Body`를 선택해 한 변 0.5 m의 큐브가 보고서와 같은 색인지 본다. `finish`를 바꾸면 같은 위치·크기에서 색만 바뀌며, 물리 속성을 만들지 않아 낙하는 수행하지 않는다.
- 후속 GUI 실습으로 `green`을 추가했다면 그 variant 안에서만 초록색이 나타나는지 확인한다. 기본 스크립트는 `green`을 생성하지 않으며, 모든 선택에서 초록이면 variant 밖의 강한 색 override가 있는지 조사한다.

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py --variant red`를 실행한다. 새 output 폴더 안에 `moved_assets/body.usda`와 `broken.usda`, `repaired.usda`가 생성된다.
2. body 자산에는 `finish` variant set과 `red`, `blue` 두 variant가 있다. 각 variant의 edit context 안에서 Body의 displayColor를 작성한다.
3. broken stage는 의도적으로 `old_assets/body.usda`를 가리킨다. 이 파일은 존재하지 않으므로 USD 참조 경고가 나타나는 것이 실습의 일부다. 경고 횟수를 성공 기준으로 삼지 않는다.
4. 새 레이어에 broken 내용을 복사한 뒤 `UsdUtils.ModifyAssetPaths`로 `old_assets/` 접두사를 `moved_assets/`로 변경한다. 사용자 원본 파일을 수정하지 않고 새 repaired 파일을 만든다.
5. repaired stage를 실제 재개방해 `/World/Robot/Body`가 생겼는지 확인한다. `tools_report.json`의 broken/repaired 여부, 경로 치환 목록, 선택 가능한 variant와 실제 색을 확인한다.
6. `~/isaacsim/python.sh run.py --variant blue`로 새 결과를 만든다. 같은 자산 구조에서 선택 의견만 달라졌는지 비교한다.

## GUI 도구로 후속 실습

GUI의 **Window > Extensions**에서 `USD Paths`, `Variant Presenter`, `Variant Editor`를 각각 검색한다. 5.1 설치에 포함/활성화된 확장의 설명에 표시된 실행 메뉴를 사용한다. 이 세 도구의 메뉴는 설치된 Kit 확장 버전에 따라 달라질 수 있으므로 본문에서 임의 메뉴 경로를 가정하지 않는다. 도구가 없는 경우 자동 설치하지 않고 위 로컬 API 실습으로 같은 USD 동작을 확인할 수 있다.

1. `broken.usda`의 복사본을 **File > Open**으로 연다. USD Paths에서 `old_assets/`를 검색하고 `moved_assets/`로 치환한 뒤 새 이름으로 저장한다. 재개방했을 때 Body가 로드되는지 확인한다.
2. `repaired.usda`를 열고 Stage에서 `/World/Robot`을 선택한다. Property의 variant 선택에서 finish=red/blue를 바꿔 큐브의 색 변화를 본다.
3. Variant Presenter에서 finish 그룹과 두 선택지가 표시되는지 본다. 이 도구는 이미 존재하는 variant를 보여주고 선택하는 데 초점이 있다.
4. Variant Editor에서 `finish`에 새 `green` variant를 추가하고 그 variant 안에서 Body displayColor만 초록으로 바꾼다. 작업 레이어를 확인하고 새 파일로 저장한다.
5. red로 돌아왔을 때 초록 변경이 남지 않고, green을 선택하면 다시 나타나는지 확인한다. variant edit context 바깥의 강한 색 override가 있으면 모든 variant를 덮을 수 있다.

## USD 개념 해설

AssetPath는 외부 파일 경로이고 `/World/Robot/Body`는 Stage 내부 Prim 경로다. 문자열처럼 보여도 서로 다르다. 상대 자산 경로는 경로를 작성한 레이어 위치를 기준으로 해석된다. 현재 shell 디렉터리를 바꾸는 것만으로 잘못된 참조가 고쳐지지 않는다.

VariantSet은 여러 대안을 묶는 이름이고 VariantSelection은 사용할 대안을 지정하는 의견이다. geometry, 재질, 센서 장착 여부 등도 variant로 표현할 수 있다. `GetVariantEditContext` 안의 작성과 일반 레이어 작성이 같은 강도를 갖는다고 가정하지 않는다.

## 한 가지 변수 실험과 문제 해결

`--variant`만 변경해 위치·크기는 같고 색만 달라지는지 확인한다. repaired도 비어 있으면 `moved_assets` 폴더를 함께 복사했는지 확인한다. source doc의 외부 도구 링크는 최신 확장 설명으로 연결되므로 설치된 5.1 메뉴와 다를 수 있다. `broken.usda`의 참조 경고를 전체 패키지 실패와 혼동하지 않는다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [USD Tools](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/usd_tools.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
