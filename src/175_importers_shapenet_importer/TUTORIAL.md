# 175. OBJ의 꼭짓점과 면을 USD 장면으로 가져오기

## 이번에 배우는 것

**작은 사각뿔 OBJ를 USD로 변환하고, 원본 형상과 장면에 들어온 mesh를 비교합니다.**

ShapeNet 전용 importer를 찾기 전에 파일 자체가 어떤 형식을 사용하는지 살펴봅니다. Isaac Sim 5.1의 공식 안내는 사용 중단된 `omni.isaac.shapenet` 대신 일반 OBJ import 경로를 사용하도록 설명합니다. 이번에는 외부 데이터셋 없이 형상을 직접 확인할 수 있는 `sample.obj`로 같은 변환 흐름을 익힙니다.

| 파일 또는 장면 경로 | 의미 |
|---|---|
| `sample.obj` | 직접 작성한 꼭짓점 5개·면 5개의 사각뿔입니다. ShapeNet 데이터가 아닙니다. |
| `run.py` | asset converter의 완료를 기다리고 변환된 mesh를 불러옵니다. |
| `converted.usd` | 변환기가 작성한 재사용 가능한 USD 자산입니다. |
| `/World/Imported` | 현재 장면에서 변환 자산을 reference로 연결한 위치입니다. |

이번에는 시각 형상을 가져옵니다. rigid body나 collider를 추가하지 않으므로 피라미드를 떨어뜨리는 물리 실습은 아닙니다.

## 1. 먼저 기본 OBJ 변환하기

Isaac Sim 5.1, RTX GPU와 드라이버, 번들 `omni.kit.asset_converter`가 필요합니다. 기본 입력에는 별도 ShapeNet 계정이나 온라인 데이터 다운로드가 필요하지 않습니다.

저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/175_importers_shapenet_importer/run.py \
  --output src/175_importers_shapenet_importer/output/first
```

출력 폴더는 새 경로여야 합니다. 변환이 끝나면 창이 남습니다. Stage의 `/World/Imported`를 선택하고 **F**로 선택한 물체를 화면 중심에 맞춰 보세요.

자동 종료가 필요하면 `--steps 120`을 추가합니다. 이 수는 변환 완료 후 화면을 업데이트하는 횟수입니다. 창 없이 확인하려면 다음처럼 실행할 수 있습니다.

```bash
~/isaacsim/python.sh src/175_importers_shapenet_importer/run.py \
  --headless --steps 5 \
  --output src/175_importers_shapenet_importer/output/headless_first
```

headless에서 `--steps`를 생략하면 기존 호환 옵션 `--frames`의 값, 기본 120회를 사용합니다. `--frames`가 OBJ의 변환 개수나 물리 프레임을 정하는 것은 아닙니다. 변환은 한 번 수행합니다.

### 코드에서 볼 부분

실제 변환 요청은 다음 부분입니다.

```python
context = omni.kit.asset_converter.AssetConverterContext()
task = omni.kit.asset_converter.get_instance().create_converter_task(
    str(args.obj.resolve()), str(converted), None, context,
)
future = asyncio.ensure_future(task.wait_until_finished())
```

`context`는 변환 설정, `task`는 비동기 변환 작업입니다. 작업을 만들자마자 결과 파일을 읽으면 아직 변환 중일 수 있습니다. 그래서 `app.update()`로 앱 처리를 진행하며 `future.done()`이 될 때까지 기다립니다. `future.result()`가 false이면 변환기 오류를 보고합니다.

이후 아래 코드로 새 장면에 자산을 연결합니다.

```python
add_reference_to_stage(str(converted), '/World/Imported')
```

파일 경로는 저장된 자산의 위치이고 `/World/Imported`는 장면 안의 위치입니다. Reference를 쓰면 변환된 자산을 다른 장면에서도 다시 사용할 수 있습니다.

### 실행 결과 확인하기

`output/first/converted.usd`와 콘솔의 `Converted mesh prims:` 목록을 확인하세요. 실행기는 변환 완료뿐 아니라 현재 Stage에서 실제 `UsdGeom.Mesh`가 있는지도 검사합니다.

GUI에서는 사각형 밑면과 삼각형 옆면 네 개가 이루는 사각뿔을 확인합니다. 파일 크기가 특정 값이어야 하는 것은 아닙니다. exporter의 설정이나 표현 방식에 따라 같은 형상도 다른 파일 크기를 가질 수 있습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 2026-09-14의 headless `--frames 5` 조건에서 종료와 변환 파일 존재를 확인한 기록입니다. 기록된 1436바이트는 그 실행의 관측값이며 모든 변환 결과의 기대 크기가 아닙니다.

## 2. 원본의 좌표와 변환된 형상 연결하기

### 코드에서 볼 부분

`sample.obj`의 꼭짓점 정의는 다음과 같습니다.

```text
v -0.1 -0.1 0
v 0.1 -0.1 0
v 0.1 0.1 0
v -0.1 0.1 0
v 0 0 0.2
```

`v`는 꼭짓점 좌표입니다. 처음 네 점은 z=0인 밑면이고, 마지막 점은 가운데 위쪽의 꼭대기입니다. 좌표상 밑면 폭과 높이는 각각 0.2입니다. OBJ 자체가 m나 cm 단위를 강제하지는 않으므로 실제 치수는 변환된 USD의 단위와 적용된 scale을 함께 확인해야 합니다.

면은 꼭짓점 번호를 연결해 정의합니다.

```text
f 1 4 3 2
f 1 2 5
```

OBJ의 번호는 1부터 시작합니다. 첫 줄은 네 꼭짓점의 밑면, 다음 줄은 두 밑면 점과 꼭대기를 이은 옆면입니다. 변환기는 이 연결 구조를 USD mesh로 옮기며 내부적으로 면 표현을 바꿀 수 있습니다. 결과 mesh의 면 개수만 원본과 같아야 한다고 요구하기보다 실제 형상도 비교하세요.

자신이 확보한 OBJ로 확장하려면 다음처럼 입력을 바꿉니다.

```bash
~/isaacsim/python.sh src/175_importers_shapenet_importer/run.py \
  --obj /data/model/model_normalized.obj \
  --output src/175_importers_shapenet_importer/output/custom
```

ShapeNet 모델의 사용 조건에 맞게 입력을 확보하고 MTL·텍스처 상대 경로를 유지하세요. 기본 사각뿔에는 재질 파일이 없지만 사용자 OBJ는 외부 파일을 참조할 수 있습니다. GUI의 **File > Import**에서도 OBJ를 가져올 수 있으므로 같은 자산의 형상·scale을 비교해 볼 수 있습니다.

## 3. 변환·배치·물리 설정의 차이 정리

```text
OBJ 꼭짓점과 면 → converter → USD mesh 자산
                                  ↓
                         reference로 장면에 배치
                                  ↓
                    필요하다면 별도 collider·rigid body 작성
```

Mesh가 보이면 형상 import를 확인한 것입니다. 관절이나 구동기, 질량과 충돌 설정까지 준비된 것은 아닙니다. 이 실행기는 timeline을 재생하지 않으므로 물체가 떨어지지 않는 것이 정상입니다.

## 4. 간단한 확인 실험

`sample.obj`를 `/tmp/tutorial_pyramid_tall.obj` 같은 새 파일로 복사하고, 꼭대기 줄의 z만 **0.2 → 0.4**로 바꾸세요. `--obj`로 그 파일을 전달하고 출력 경로도 새로 지정합니다.

밑면 네 점은 유지했으므로 폭은 그대로이고 높이만 두 배가 되어야 합니다. GUI의 같은 시점이나 변환된 mesh의 bounds로 비교하세요. 원본 좌표 변화가 결과에 반영되는지를 확인하는 실험이며 파일 바이트 수를 두 배로 예상하는 실험이 아닙니다.

## 실행할 때 막히면

- **입력·출력 조건 오류**: OBJ가 존재하는지와 출력 폴더가 새 경로인지 확인하세요. 실패한 실행이 만든 폴더도 다음 실행에서는 기존 경로입니다.
- **변환 시간 초과**: 기본 `--timeout`은 120초입니다. 큰 파일의 로그를 확인한 뒤 필요하면 늘리세요.
- **mesh 목록은 있는데 화면에서 안 보임**: `/World/Imported` 선택 후 F를 누르고 scale·위치를 확인하세요.
- **사용자 모델이 흰색으로 보임**: MTL과 텍스처의 상대 경로를 확인하세요.
- **물체가 움직이지 않음**: 이 실행에는 물리 재생과 rigid body가 없습니다. import와 동역학 설정을 구분하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ShapeNet Importer 안내](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/shapenet_importer.html)는 전용 확장의 사용 중단과 일반 OBJ import를 설명합니다. 이 폴더는 그 대체 경로를 작은 원본 OBJ로 실습합니다.

이번 개정에서는 실행기·OBJ·기존 실행 기록을 대조했습니다. `tutorial.json`의 `partial_runtime_verified`는 [기록 당시의 headless 실행](RUNTIME_CHECK.md)을 나타냅니다. 이후 실행기가 변경되었으므로 현재 코드의 재실행 검증으로 확대하지 않습니다. GUI 형상·사용자 OBJ·다른 CLI 조건도 기존 확인 범위 밖이며 이번에 새 GPU 실행은 수행하지 않았습니다.
