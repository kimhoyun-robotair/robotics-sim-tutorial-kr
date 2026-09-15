# 74. 센서가 읽는 비가시 재질

권장 학습 순서 **74** · 센서와 측정 데이터 · 출처 ID `t148`

RGB 색은 같은 세 상자에 서로 다른 비가시 재질을 적용하고 USD 속성과 material ID debug view를 비교합니다. 5.1의 USD 속성 기반 경로를 직접 구현했습니다.

## 이 실습의 의도

같은 RGB 색의 세 상자에 다른 비가시 재질을 바인딩하여, 화면에서 비슷하게 보이는 물체도 센서용 재질 설정은 다를 수 있음을 익힌다. 기본 실행은 aluminum+paint, steel+clearcoat, concrete+paint 조합과 공통 `emissive` 속성을 작성하고 JSON과 USD로 저장한다. 이 장면에는 Lidar/Radar를 만들지 않으며, 재질 적용의 시각적 확인은 사용자가 GUI의 Non-Visual Material ID debug view를 선택해야 한다.

## 실행 후 확인할 것

- **같은 외형과 위치**: GUI에서 `/World/Box0`~`Box2`가 같은 RGB 재질 색으로 보이는지 확인한다. 상자는 `VisualCuboid`이므로 z=1 m에 그대로 있는 것이 정상이며, 낙하나 물리 접촉을 관찰하는 장면이 아니다.
- **조합별 바인딩**: Stage에서 각 상자가 `/World/Looks/Material0`~`Material2`에 각각 연결되었는지 확인한다. `material_attributes.json`의 세 행에서 base/coating 조합과 공통 `behavior=emissive`가 코드의 설정과 맞아야 한다.
- **실제 USD 속성**: JSON의 `authored_attributes`와 `materials.usda`에 `omni:simready:nonvisual:base`, `:coating`, `:attributes`가 작성되었는지 확인한다. base/coating 이름이 JSON의 설명 필드에만 적혀 있는 것으로 재질 적용을 판정하지 않는다.
- **수동 debug view 확인**: **RTX - Real-Time > Debug View > Non-Visual Material ID**로 바꾸어 세 조합이 구분되는지 본다. 색은 material ID 표시이며 RGB 색, 물체 ID, Lidar 반사 강도의 수치가 아니다. headless 파일 생성만으로 이 GUI 확인이 끝난 것은 아니다.
- **저장과 측정의 범위**: 기본 240스텝 후 저장되는 것은 재질 설정과 장면이며, 센서 반환 파일은 없다. GUI에서 coating을 바꿔 비교한 결과를 보존하려면 별도로 저장해야 하며 기존 JSON/USD는 자동 갱신되지 않는다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/74_sensors_sensors_rtx_materials
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 렌더링이 계속됩니다. 처음 240스텝 뒤 작성된 재질 속성과 장면을 한 번 저장하며, 이후 관찰 중에는 파일을 추가하거나 바꾸지 않습니다. 이 실행은 센서를 생성하거나 측정값을 수집하지 않습니다. `--steps N`에 양수를 주면 N스텝 뒤 파일을 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. `--headless`와 `--steps` 없이 실행해 Stage에서 `/World/Looks/Material0`, `Material1`, `Material2`를 찾습니다. RGB 색이 같아도 aluminum+paint, steel+clearcoat, concrete+paint 조합이 다릅니다.
2. viewport의 **RTX - Real-Time > Debug View > Non-Visual Material ID**를 선택합니다. 다른 재질 조합이 서로 다른 ID 색으로 나타나는지 봅니다. ID 색은 RGB 재질 색이나 반사 강도 값이 아닙니다.
3. `material_attributes.json`과 `materials.usda`를 열어 authoring된 센서 재질 속성을 확인합니다. `apply_nonvisual_material`은 Material prim에 적용하고 `apply_visual_material`로 상자에 바인딩합니다.
4. Material prim 우클릭 **Add > Attribute**로 사용자 속성 입력 창을 확인합니다. API가 만든 속성 이름·타입과 일치시켜야 렌더러가 읽습니다. 이름만 비슷한 임의 속성을 만들지 마세요.
5. 코드에서 두 번째 재질의 coating만 `clearcoat`에서 `paint`로 바꿔 새 폴더에 실행하고 debug ID를 비교합니다. RGB 색과 geometry는 유지합니다.

## API와 USD 개념

USD material binding은 geometry가 어떤 Material prim을 사용할지 연결합니다. 가시 재질은 화면 색·조명 반응을, 비가시 재질은 센서 파장대의 반응을 지정합니다. `apply_nonvisual_material(prim, base, coating, attribute)`가 유효 이름을 검사하고 USD 속성을 작성하며 renderer가 조합으로 material ID를 계산합니다. 물체 ID, semantic class ID, material ID는 서로 다릅니다.

이 예제의 USD 속성 검사와 debug view는 재질 적용을 확인합니다. Lidar 강도나 Radar 반사율을 수치로 측정했다고 주장하지 않습니다. 그 측정에는 센서와 annotator를 붙여 실제 반환값을 수집해야 합니다.

## 확장 실습·성공 기준·문제 해결

5.1에서 CSV 시각 재질 이름 매핑은 deprecated입니다. 기존 프로젝트를 읽을 때 `kit/rendering-data/runtime/RtxSensorMaterialMap.csv`, `/rtx/materialDb/rtSensorNameToIdMap`, `/rtx/materialDb/rtSensorMaterialLogs`를 볼 수 있습니다. 기존 CSV의 키는 `/Looks/` 뒤 첫 재질 이름 토큰을 소문자로 쓴 값이며 시작 시 읽힙니다. 설치 파일을 변경하는 실습은 이 패키지에서 하지 않습니다. 새 USD에는 위 API 속성을 쓰세요.

ID 색이 같다면 실제 재질이 해당 mesh에 바인딩됐는지, 이름 조합이 유효한지 확인합니다. 서로 다른 RGB 재질도 같은 비가시 조합이면 동일 ID일 수 있습니다. 본 실습은 RTX GPU와 UI로 debug view를 관찰해야 완료됩니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — RTX Sensor Non-Visual Materials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_rtx_materials.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

Python 문법·도움말과 파일 구성을 검사했으며, RTX 영상/점군과 PhysX 런타임·GUI 상호작용은 작성 작업에서 실행하지 않았습니다. 실제 성공 여부는 위 단계의 **측정 파일과 화면 결과**로 확인합니다. `tutorial.json`의 verification은 그 이유로 `not_run`입니다.
