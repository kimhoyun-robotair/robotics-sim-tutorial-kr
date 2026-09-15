# 162. USD Instanceable Asset의 공유 구조

권장 학습 순서 **162** · 병렬 환경과 학습 정책 활용 · 출처 ID `t006`

geometry 정의 파일과 이를 참조하는 Stage를 직접 만들고, 네 개의 로봇 링크가 동일 USD prototype을 공유하는지 출력합니다. 공식 문서의 계층 제약과 importer 설정을 설명하고 재현 가능한 작은 USD 실습을 제공합니다.

## 준비와 실행

이 폴더 하나를 다른 위치에 복사해도 실행할 수 있습니다. 다른 로컬 튜토리얼이나 공용 모듈을 먼저 읽을 필요가 없습니다. Isaac Sim **5.1.0** 설치, 지원 NVIDIA GPU/드라이버가 필요합니다. 일반 Python은 `--help` 확인에만 사용하고 시뮬레이션은 설치에 포함된 `python.sh`로 실행합니다. GUI 실행은 화면 세션이 필요하며 창 없이 실행하려면 `--headless`를 붙입니다.

외부 로봇 자산은 필요 없습니다.

터미널에서 이 패키지 폴더(`162_motion_instanceable_assets`)로 이동한 뒤 아래를 실행합니다. 설치 위치가 다르면 첫 줄만 바꿉니다. Windows에서는 설치 폴더의 `python.bat`에 동일한 인수를 전달합니다.

```bash
ISAAC_SIM_ROOT=/home/hoyunkim/isaacsim
python3 run.py --help
"$ISAAC_SIM_ROOT/python.sh" run.py --count 4
"$ISAAC_SIM_ROOT/python.sh" run.py --headless --count 4 --no-instancing
```

`--steps`는 물리 스텝 수(USD 전용 예제에서는 화면 업데이트 수)입니다. `--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 계속됩니다. `--steps 600`처럼 양수를 지정하면 해당 횟수 후 종료하며, `--headless`에서 생략하면 기존 기본값인 600회로 제한됩니다. 각 실행 결과는 이 폴더의 새 `output/run_*` 디렉터리에 저장됩니다. `--output /절대경로/새폴더`를 지정할 수도 있지만 기존 폴더를 덮어쓰지 않습니다. 코드는 `SimulationApp`을 만든 뒤 Isaac/Omni/USD 모듈을 가져오고 마지막에 `close()`로 종료합니다.

## 단계별 실습

1. 기본 실행의 `output/run_*/meshes.usda`와 `instances.usda`를 확인합니다. 전자는 `/Geometry/Cube`를 정의하고 후자는 여러 링크에서 `./meshes.usda`의 `/Geometry`를 참조합니다.
2. Stage에서 `/World/Robot_0/Link/Geometry`를 선택합니다. `Instanceable`이 켜져 있고 자식 Cube가 instance proxy임을 `instances.json`에서도 확인합니다.
3. `/World/Robot_0/Link`의 Translate를 변경합니다. 이 링크는 instance root 밖이므로 다른 Robot의 위치를 바꾸지 않고 이동할 수 있습니다.
4. `Geometry/Cube`의 크기를 그 복사본에서 직접 수정하려 해 봅니다. instance proxy 내부 편집은 제한됩니다. 공유 geometry 변경은 원본 `meshes.usda`에서 수행하거나 해당 instance root의 Instanceable을 끈 뒤 별도 의견으로 작성해야 합니다.
5. `--no-instancing` 실행의 `instances.json`과 비교합니다. reference는 유지되지만 `is_instance=false`, prototype은 null이어야 합니다. prototype 경로 문자열 자체는 세션마다 달라질 수 있습니다.

## 왜 Xform을 한 단계 넣는가

로봇 링크는 관절에 따라 각자 움직이지만 mesh는 동일합니다. `Link → Geometry(Xform, reference, instanceable) → Cube` 구조에서는 Link의 변환을 독립적으로 바꾸며 geometry 자식을 공유합니다. mesh 자체에만 flag를 켜는 것으로 모든 로봇 구조가 자동 공유되지는 않습니다. composition arc(reference 등)가 있는 부모와 공통 mesh 정의가 필요합니다.

`GetReferences().AddReference('./meshes.usda', '/Geometry')`는 파일/prim 참조를 추가하고, `SetInstanceable(True)`는 가능한 공통 prototype 생성을 요청합니다. `IsInstance()`와 `IsInstanceProxy()`는 각각 root와 공유된 자식 상태를 관찰합니다. 이것은 물리 환경 복제나 RL 정책이 아닙니다. 출력은 공유 여부이며 실제 GPU 메모리 절감량을 측정했다고 주장하지 않습니다.

## 5.1 URDF/MJCF importer에서 같은 구조 만들기

1. 새 Stage에서 `File > Import`로 URDF(`.urdf`) 또는 MJCF(`.xml`)를 선택합니다. 필요한 확장은 `Window > Extensions`에서 `isaacsim.asset.importer.urdf` 또는 `isaacsim.asset.importer.mjcf`로 찾습니다. 입력 robot description과 그 파일이 참조하는 mesh/texture를 함께 준비합니다.
2. 오른쪽 import 옵션의 Model 영역에서 **Referenced Model**을 선택하고 **USD Output**의 폴더 선택 버튼으로 이 패키지 아래 새 출력 위치를 정합니다. **Create in Stage**는 현재 Stage에 직접 생성하는 다른 방식입니다. 두 importer의 실제 5.1 File > Import 패널은 이 Model/출력 선택을 사용합니다.
3. Import를 실행한 뒤 생성된 robot의 링크를 펼칩니다. geometry 참조를 가진 부모 prim의 Instanceable 상태와 자식의 instance proxy 여부를 확인합니다. Script Editor에서 선택한 geometry 자식에 대해 `prim.IsInstanceProxy()`를 호출하면 공유 자식인지 확인할 수 있습니다. 링크 transform은 별도로 움직일 수 있습니다.
4. 새 Stage에는 출력한 주 robot USD를 참조합니다. importer가 만든 하위 USD·mesh·재질 파일도 함께 보존합니다. 출력 계층의 composition을 확인한 뒤 이동하며, 모든 버전이 `instanceable_meshes.usd`라는 단일 파일 이름을 만든다고 가정하지 않습니다.

공식 5.1 Instanceable Assets 본문에는 이전 **Create Instanceable Asset / Instanceable USD Path** 옵션 설명이 남아 있습니다. 실제 5.1 URDF importer는 해당 선택 옵션을 폐기하고 mesh를 instanceable로 가져옵니다. MJCF의 현재 File > Import 경로도 instanceable prim을 만들며 **Referenced Model / USD Output** 패널을 사용합니다. 설치 소스에 남아 있는 과거 UI 생성 함수의 checkbox 이름을 활성 화면에서 찾을 필요가 없습니다. 이 설명은 설치본 URDF CHANGELOG 1.15.0, `impl/ui/UrdfOptionWidget.py`, MJCF CHANGELOG 2.2.3, `impl/option_widget.py` 및 import delegate 연결을 대조한 것입니다.

## 기존 자산 변환 절차

원본을 복사한 작업 파일에서 mesh/primitive마다 부모 Xform을 추가하고, mesh가 가진 reference를 새 부모에 옮깁니다. 공통 geometry USD를 만든 뒤 그 부모가 외부 geometry prim을 참조하도록 작성하고 instanceable을 켭니다. 원문 `create_parent_xforms()`/`convert_asset_instanceable()`은 출발점이지만 임의 자산에 대한 안전한 일괄 변환기를 제공하는 것은 아닙니다. material binding, physics material, filtered collision 관계가 원래 Stage 밖 대상을 가리키면 참조 후 유효하지 않을 수 있습니다. 부모 Xform 또는 공유 파일 안의 유효 경로로 관계를 옮긴 뒤 검사해야 합니다. 이 패키지의 새 장면 생성 방식은 사용자 자산을 덮어쓰지 않고 그 최종 계층을 직접 보여 줍니다.

## 관찰 기준과 한 변수 실험

기본 4개 geometry의 prototype이 같아야 하며, Link 위치는 서로 달라야 합니다. `--count`만 4에서 20으로 바꾸고 여전히 공유되는지 확인합니다. 원본 Cube 크기를 바꾸면 모든 참조에서 변경이 보이는 것이 기대 결과입니다.

## 문제 해결

일부 geometry가 instance가 아니라면 instance root에 유효한 reference가 있는지 확인합니다. Cube 편집 실패는 instance proxy의 정상 제한일 수 있습니다. 파일을 옮긴 뒤 geometry가 사라지면 두 USD 파일의 상대 위치를 확인합니다.

## 검증 범위

이 패키지의 `tutorial.json`에 적힌 `verification`은 실제 시뮬레이터 실행 여부를 나타냅니다. Python 문법 검사와 `--help` 성공만으로 GPU 실행, 물리 동작, 충돌 회피 성능을 검증했다고 보지 않습니다. 실행 후 아래 관찰 기준으로 직접 결과를 확인합니다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 — Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)
- 원문의 학습 목적과 API를 유지하면서 한국어 설명, 명령행 옵션, 제한된 실행 루프와 실제 상태 기록을 추가한 독립 예제입니다. 원문 전체를 복제한 문서가 아닙니다.
