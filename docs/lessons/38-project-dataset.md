# 38단계 — 중간 프로젝트 8: 조건이 기록된 검사 부품 데이터셋

## 목표와 준비

37단계의 고정 장면을 확장해 부품 위치, 회전, 조명을 바꾸며 12장을 촬영한다. 각 이미지의 생성 조건도 저장하고 파일 손상·누락·검은 영상·비어 있는 라벨을 자동 검사한다. 완료 결과물은 단순한 이미지 폴더가 아니라 촬영 조건을 추적할 수 있는 데이터 묶음이다.

37단계가 정상 종료되어야 한다. Python 데이터 검사용 환경은 Isaac Sim 내장 환경과 별도로 만든다. 아래 명령은 저장소 루트에서 한 번 실행한다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

## 설계를 먼저 정하다

| 바꿀 값 | 범위 | 제한 이유 |
|---|---|---|
| 부품 x/y | −0.35~0.35 m | 카메라 시야와 검사대 안에 유지하다 |
| yaw | −45~45° | 회전에 따른 외형 차이를 만들다 |
| 조명 intensity | 700~1300 | 완전한 암전으로 데이터를 채우지 않다 |
| 부품 높이 | 중심 z=0.2 m 고정 | 0.4 m 물체가 바닥을 뚫지 않다 |

조명 intensity는 USD 조명 속성값이며 현실의 조도계가 읽는 lux라고 해석하지 않는다. 이 프로젝트는 실제 카메라의 노출·잡음 모델을 보정하는 실험이 아니다. 위치와 밝기 변화가 데이터에 반영되는지 확인하는 작은 실습이다.

## 제작과 검사

1. 다른 시뮬레이터를 종료하고 아래 명령을 실행한다. `--fixed`가 없으면 무작위 변화를 적용한다.

```bash
"$ISAAC_SIM_PATH/python.sh" examples/08_dataset.py \
  --headless --seed 601 --frames 12 --output-dir artifacts/dataset-seed601
.venv/bin/python scripts/inspect_dataset.py artifacts/dataset-seed601
```

2. `inspection.json`에서 `status`와 `problems`를 읽는다. 이미지·분할·라벨 파일이 각각 12개 있어야 하며 프레임 번호가 서로 일치해야 한다.
3. 파일 관리자에서 첫 번째, 중간, 마지막 RGB와 분할을 연다. 색칠된 영역이 실제 부품 외곽과 맞는지 눈으로 확인한다. 라벨 이름이 존재한다는 것만으로 픽셀별 정답이 맞다는 뜻은 아니다.
4. 같은 seed를 새 폴더에서 반복하고 `manifest.json`의 `frames` 값이 같은지 비교한다. 이때의 재현성 기준은 물체 배치·조명 설정이다.

```bash
"$ISAAC_SIM_PATH/python.sh" examples/08_dataset.py \
  --headless --seed 601 --frames 12 --output-dir artifacts/dataset-seed601-repeat
python3 - <<'PY'
import json
from pathlib import Path
a = json.loads(Path('artifacts/dataset-seed601/manifest.json').read_text())
b = json.loads(Path('artifacts/dataset-seed601-repeat/manifest.json').read_text())
assert a['frames'] == b['frames'], '같은 seed의 생성 조건이 다르다'
print('생성 조건 일치')
PY
```

## 검사 코드를 이해하다

RGBA의 네 번째 채널은 투명도이다. 검은 영상에서도 alpha가 255일 수 있으므로 채널 전체의 평균을 계산하면 암전을 놓칠 수 있다. 검사기는 RGB 세 채널만 읽는다.

```python
rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
dark_fraction = float((rgb.max(axis=2) <= 2).mean())
flat_image = float(rgb.std(axis=(0, 1)).max()) < 1.0
```

이 실습에서는 98% 이상이 거의 검거나 표준편차가 1 미만이면 실패로 처리한다. 이 수치는 붉은 부품과 회색 검사대 장면을 위한 진단 기준이다. 야간 장면이나 단색 보정판에 그대로 적용하면 오탐이 생기므로 장면이 바뀌면 기준도 새로 정한다.

전체 검사기는 [inspect_dataset.py](../../scripts/inspect_dataset.py)에 있다. 누락된 분할, 프레임 번호 불일치, 검은 RGB를 넣으면 실패하는지도 [단위 테스트](../../tests/test_dataset_inspection.py)로 확인한다. 정상 데이터만 넣는 검사는 고장 감지 능력을 보여주지 못한다.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## 완료 기준

- 12개의 RGB·분할·라벨이 모두 대응하고 `inspection.json`이 PASS이다.
- 두 번 실행한 manifest의 배치·회전·조명이 일치한다.
- 세 장 이상을 직접 열어 부품과 분할 경계가 대응함을 확인한다.
- 사용한 GPU, 드라이버, Isaac Sim `VERSION` 문자열과 시각 검사 결과를 실험 기록에 남긴다.

## 실패했을 때와 과제

이미지 수가 24개라면 이전 실행 폴더에 결과를 합쳤는지 확인한다. 예제는 이를 막기 위해 빈 폴더를 요구한다. 라벨 파일은 있지만 물체가 안 보이면 위치 범위와 카메라 방향을 확인한다. 분할 결과가 RGB와 한 프레임씩 어긋나 보이면 캡처 요청 시점, 렌더 완료 대기, 파일 번호를 차례로 확인한다.

과제는 seed만 602로 바꾸어 별도 검증용 데이터를 만들고, 601로 생성한 데이터와 섞지 않는 것이다. 프레임을 임의로 나누는 것과 생성 조건을 분리하는 것의 차이를 설명한다.

## 공식 참고

[Randomization Snippets](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/replicator_tutorials/tutorial_replicator_isaac_randomizers.html)에서 조명·재질·물체 배치를 바꾸는 API를 확인한다. [6.0.1 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)의 렌더링과 SDG 제한도 함께 읽는다.
