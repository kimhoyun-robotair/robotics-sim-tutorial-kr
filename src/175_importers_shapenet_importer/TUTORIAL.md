# 175. t114 · 폐기된 ShapeNet 전용 importer 대신 OBJ 가져오기

권장 학습 순서 **175** · 사용 중단 문서와 레거시 참고 · 출처 ID `t114`

Isaac Sim **5.1.0**의 이 공식 페이지는 `omni.isaac.shapenet`이 deprecated이며 ShapeNet 모델을 일반 OBJ처럼 가져오라고 안내한다. 따라서 이 패키지는 현재 지원되는 OBJ→USD 변환 경로를 구현한다. 포함한 `sample.obj`는 직접 작성한 사각뿔(면 5개) 예제이며 **ShapeNet에서 내려받은 데이터가 아니다**.

## 이 실습의 의도

사용 중단된 ShapeNet 전용 importer에 의존하지 않고, 일반 OBJ의 꼭짓점·면을 USD mesh로 변환해 장면에서 재사용하는 흐름을 익힌다. 작은 피라미드를 사용하는 이유는 dataset 접근 없이도 원본 형상과 변환 결과를 직접 비교할 수 있기 때문이다. 기본 실행은 `sample.obj` 변환과 `/World/Imported` 아래 reference 표시까지이며, 물리 속성이나 ShapeNet 데이터 다운로드를 추가하지 않는다.

## 실행 후 확인할 것

- **원본 형상:** `sample.obj`의 꼭짓점 5개와 면 5개가 사각형 밑면·삼각형 옆면 네 개를 이루는지 확인한다. 정점 좌표상 밑면 폭과 높이는 각각 0.2지만 실제 단위 적용은 변환된 USD에서 확인한다.
- **실제 변환물:** 종료 코드뿐 아니라 `output/converted.usd`와 콘솔의 `Converted mesh prims:` 목록을 확인한다. GUI의 `/World/Imported`를 선택하고 F로 맞춰 피라미드가 보이는지 본다.
- **형상 변화:** 꼭대기 z만 0.2에서 0.4로 바꿔 새 output에 변환했을 때 밑면 폭은 유지되고 높이가 커지는지 비교한다. 파일 크기가 특정 바이트 수와 같아야 하는 것은 아니다.
- **물리 범위:** 이 실행기는 timeline을 재생하거나 rigid body·collider를 붙이지 않으므로 피라미드가 떨어지지 않는 것이 정상이다. 화면 표시 성공과 동역학 모델 준비 완료를 구분한다.
- **기존 실행 근거:** `RUNTIME_CHECK.md`는 지정된 headless 조건의 종료와 변환 파일 존재를 확인한 기록이다. GUI 모양, 사용자 OBJ의 재질·텍스처, 다른 옵션은 해당 기록의 보장 범위에 포함되지 않는다.

## 준비와 실행

Isaac Sim 5.1과 RTX GPU/드라이버, 번들 `omni.kit.asset_converter`가 필요하다. 다른 로컬 패키지·온라인 dataset 계정은 기본 실습에 필요하지 않다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/175_importers_shapenet_importer
"$ISAAC_SIM/python.sh" run.py
# 정식으로 확보한 자신의 ShapeNet OBJ로 확장
"$ISAAC_SIM/python.sh" run.py --obj /absolute/model_normalized.obj --output output/shapenet
```

`output/converted.usd`에 실제 변환 결과를 저장하고 mesh prim 경로를 출력한다. 변환 완료를 기다려 실패 상태를 검사하며 기존 output은 덮어쓰지 않는다. 일반 Python의 `--help`는 simulator 없이 동작한다.

`--steps`를 생략하면 변환이 끝난 뒤에도 GUI를 사용자가 닫을 때까지 유지합니다. `--steps 240`은 변환 후 화면 업데이트 240회 뒤 종료합니다. `--headless`에서 생략하면 기존 `--frames` 값(기본 120회)을 사용합니다. `--frames`는 이전 명령과의 호환을 위한 headless 미리보기 횟수이며 GUI를 자동 종료시키지 않습니다. OBJ 변환은 한 번만 실행됩니다.

## 직접 확인하기

1. `sample.obj`를 열어 `v` 다섯 개가 꼭짓점, `f`가 면의 vertex index라는 것을 확인한다. OBJ index는 1부터 시작한다.
2. 실행한 stage에서 `/World/Imported`를 선택하고 `F`로 화면 중심에 맞춘다. 단순히 converter task가 생성되었다는 사실 대신 실제 mesh prim이 생겼는지 확인한다.
3. 원본 OBJ의 꼭대기 z만 0.2→0.4로 바꿔 다른 output에 변환한다. 폭을 유지한 채 높이만 바뀌는지 비교한다.
4. 자신의 ShapeNet OBJ를 넣을 때는 해당 모델의 MTL과 texture 상대 경로를 함께 유지한다. OBJ 자체는 m/cm 같은 단위 계약이 강제되지 않으므로 실제 치수를 측정해 scale을 정한다.
5. GUI에서는 **File > Import**에서 `.obj`를 선택해 같은 변환을 할 수 있다. USD로 저장한 뒤에는 reference로 재사용한다. ShapeNet 전용 메뉴를 찾을 필요가 없다.

## API와 표현 범위

`AssetConverterContext`는 변환 설정, `create_converter_task()`는 입력/출력 파일을 지정한 비동기 작업이다. `wait_until_finished()`의 실제 결과를 기다린 다음 USD를 stage에 reference한다. `UsdGeom.Mesh`는 vertex/face topology를 가진 prim이다. OBJ에는 articulated robot joint나 PhysX rigid body가 없으므로 **시각 mesh import가 자동 물리 모델 생성은 아니다**. rigid body/collider가 필요하면 가져온 USD에 별도로 작성한다.

자산이 흰색이면 MTL/texture 경로를 확인하고, 보이지 않으면 scale·위치와 frame selection을 확인한다. timeout은 `--timeout`을 늘려 파일 크기에 맞출 수 있다. dataset 접근권한/다운로드는 사용자가 준비해야 하며 이 패키지는 전용 downloader를 되살리지 않는다. 기존 headless 변환 실행의 파일 생성은 아래 `RUNTIME_CHECK.md`에 기록되어 있다. GUI 렌더 결과와 사용자 OBJ 변환은 별도 확인이 필요하다.

## 출처

[Isaac Sim 5.1 ShapeNet Importer deprecation 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/shapenet_importer.html). 실제 변환 API는 설치된 5.1 `omni.kit.asset_converter`의 `tests/test_asset_converter.py`에서 확인했다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
