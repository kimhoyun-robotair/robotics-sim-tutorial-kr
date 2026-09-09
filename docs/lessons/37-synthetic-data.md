# 37단계 — RGB와 정답 라벨을 함께 저장하다

## 목표와 준비

카메라 영상을 눈으로 확인하는 데서 한 걸음 더 나아가, 물체 종류를 나타내는 정답 라벨까지 저장한다. 이 단계는 24단계에서 RGB가 정상적으로 보이는 것을 확인한 뒤 진행한다. 결과는 물체 검출·분할 모델에 사용할 수 있는 작은 합성 데이터셋이다. 아직 학습된 모델의 정확도를 평가하는 단계는 아니다.

장면은 4 m 정사각형 검사대와 변 길이 0.4 m인 붉은 부품 하나로 구성한다. 지면 위에 놓인 정적 물체만 사용하므로 이 단계에서는 물체의 질량, 관절, 미끄러짐이 결과를 바꾸지 않는다. 초보자는 데이터 생성과 물리 시뮬레이션의 문제를 이렇게 나누어 확인하는 편이 이해하기 쉽다.

## 세 가지 객체를 구분하다

| 객체 | 역할 | 이 실습의 값 |
|---|---|---|
| USD Camera | 위치, 방향, 투영을 정의하다 | `(1.7, 1.7, 1.4)`에서 검사대를 바라보다 |
| Render Product | 특정 카메라를 특정 해상도로 렌더링하다 | 640×480 |
| Writer | RGB와 라벨을 파일로 기록하다 | `BasicWriter` + `DiskBackend` |

화면의 Viewport가 보인다고 Writer가 자동으로 기록되는 것은 아니다. Writer에 Render Product를 연결하고 캡처를 요청해야 파일이 생긴다. 하나의 카메라에 여러 Render Product를 붙이면 해상도가 다른 데이터를 만들 수 있지만 메모리 사용량도 증가한다. 처음에는 하나씩만 사용한다.

## 실행 절차

1. 이전 Isaac Sim 창을 닫는다. 새 터미널에서 저장소 루트로 이동한다.
2. 설치 경로를 지정한다. 저장소 경로는 실제 내려받은 위치로 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$HOME/robotics-sim-tutorial-kr"
export TUTORIAL_ROOT="$PWD"
"$ISAAC_SIM_PATH/python.sh" examples/08_dataset.py \
  --fixed --frames 3 --output-dir artifacts/dataset-fixed
```

3. 생성 창에서 붉은 부품과 회색 검사대가 보이는지 살펴본다. 스크립트가 캡처와 디스크 기록을 마치면 창을 닫는다.
4. `artifacts/dataset-fixed`에서 RGB PNG, 분할 PNG, 라벨 JSON, `scene.usda`, `manifest.json`을 확인한다. 출력 폴더에 파일이 이미 있으면 예제는 실행을 거부한다. 재실행할 때에는 `artifacts/dataset-fixed-02`처럼 새 폴더를 쓴다.

## 코드가 하는 일

전체 코드는 [08_dataset.py](../../examples/08_dataset.py)에 있다. 다음 코드는 장면의 물체에 사람이 정한 클래스 이름을 부여하는 부분이다. 라벨 이름은 Prim 이름과 별개이다. Prim 이름이 `/World/Part`여도 학습용 분류는 `inspection_part`라고 정할 수 있다.

```python
rep.functional.modify.semantics(
    target.GetPrim(), {"class": "inspection_part"}, mode="add"
)
```

다음은 이미 만들어진 `camera`에서 기록 경로를 구성하는 부분이다. `rep.create.render_product`의 해상도는 `(width, height)`이다. 24단계의 `CameraSensor`가 사용하는 `(height, width)`와 순서가 다르므로 함수별 문서를 확인한다.

```python
product = rep.create.render_product(camera, (640, 480))
backend = rep.backends.get("DiskBackend")
backend.initialize(output_dir=str(output))
writer = rep.writers.get("BasicWriter")
writer.initialize(
    backend=backend, rgb=True, semantic_segmentation=True,
    colorize_semantic_segmentation=True,
)
writer.attach(product)
```

캡처는 아래처럼 직접 요청한다. `delta_time=0.0`은 이 정적 실습에서 물리 시간을 진행하지 않겠다는 뜻이다. `rt_subframes`는 렌더링을 안정시키는 반복 횟수이며 저장 이미지 개수와 같지 않다. 종료 전에 Writer가 파일을 모두 쓰도록 기다린다.

```python
rep.orchestrator.step(rt_subframes=4, delta_time=0.0)
rep.orchestrator.wait_until_complete()
```

## 예상 결과와 확인

고정 모드에서는 동일한 배치로 3회 촬영한다. GPU와 드라이버가 달라지면 픽셀까지 완전히 같을 것이라고 가정하지 않는다. 이미지마다 붉은 부품이 화면 안에 있고, 분할 색상이 부품의 외곽을 따라가며, 라벨 JSON에 `inspection_part`가 있어야 한다.

Python으로 파일 수를 확인한다. 이 코드는 Isaac Sim 밖의 터미널에서 실행한다.

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('artifacts/dataset-fixed')
for pattern in ('rgb*.png', 'semantic_segmentation*.png', 'semantic_segmentation*.json'):
    print(pattern, len(list(p.rglob(pattern))))
PY
```

## 실패했을 때와 과제

RGB가 전부 검으면 카메라 자세와 조명부터 확인한다. RGB는 정상인데 분할이 단색이면 정답 라벨이 물체 Prim에 붙었는지 확인한다. 파일이 일부만 있으면 창을 너무 일찍 닫지 않았는지, `wait_until_complete()`까지 실행했는지 확인한다. 화면이 정상이어도 파일 검사는 생략하지 않는다.

과제는 부품의 클래스 이름을 `inspection_part_v2`로 바꾸어 RGB가 유지되면서 라벨 JSON만 의도대로 달라지는지 확인하는 것이다. 검사 스크립트가 기대하는 클래스 이름도 manifest와 함께 일치시킨다.

## 공식 참고

[6.0.1 Getting Started Scripts](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/replicator_tutorials/tutorial_replicator_getting_started.html)는 캡처와 Writer의 수명주기를 설명한다. [SDG Workflows](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/replicator_tutorials/tutorial_replicator_sdg_workflows.html)는 장면 설정, 데이터 기록, 물리 시뮬레이션을 함께 설계할 때 참고한다.
