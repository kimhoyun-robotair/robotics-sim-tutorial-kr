# 140. 구 안에 고른 점을 OmniGraph로 옮기기

## 이번에 배우는 것

**구의 내부·표면·껍질에 물체 중심을 배치하고, 같은 계산을 직접 호출과 그래프 실행으로 연결합니다.**

무작위 위치를 고를 때 x·y·z를 각각 일정 범위에서 뽑으면 상자 모양의 공간을 채웁니다. 구 모양의 공간을 채우려면 방향과 반지름을 따로 고르는 편이 자연스럽습니다. 이번에는 이 계산을 만든 뒤 실제 OmniGraph ScriptNode에 넣습니다.

| 영역 | 물체 종류 | 중심에서 원점까지의 거리 |
|---|---|---|
| `inside` | Cube | 0~0.7 m |
| `surface` | Sphere | 1.4 m |
| `shell` | Cylinder | 2.1~2.6 m |

기본값은 영역마다 30개, 전체 90개입니다. 중심 좌표를 제한하는 실습이므로 도형의 표면 일부가 경계를 넘어 보이는 것과 중심 배치 오류는 구분해야 합니다.

## 1. Python에서 직접 위치를 써 보기

Isaac Sim 5.1과 RTX GPU 환경에서 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/140_replicator_replicator_custom_og_randomizer/run.py --method direct --headless --frames 3 --count 30 --output /tmp/tutorial140-direct
```

출력은 새 폴더로 지정합니다. 각 프레임에서 90개 중심을 다시 배치하고 480×360 RGB를 촬영합니다. 세 번 촬영한 뒤 종료합니다. GUI에서 `--headless`를 빼면 저장 후 창이 남고, `--steps N`을 추가하면 저장 후 앱을 N번 갱신하고 닫습니다. 사진 장수와는 별도의 관찰 한도입니다.

### 코드에서 볼 부분

```python
z, angle = rng.uniform(-1, 1), rng.uniform(0, 2 * math.pi)
radius = rng.uniform(inner ** 3, outer ** 3) ** (1 / 3)
xy = math.sqrt(1 - z * z)
```

여기서 `z`는 최종 높이가 아니라 **길이 1인 방향 벡터의 z 성분**입니다. 방향을 고른 뒤 반지름을 곱하여 위치를 만듭니다.

```text
x = radius × xy × cos(angle)
y = radius × xy × sin(angle)
z 위치 = radius × z 방향 성분
```

반지름을 그냥 균등하게 고르면 중심 근처에 표본이 몰립니다. 구의 부피가 반지름의 세제곱에 비례하므로 `inner³~outer³`에서 고른 값의 세제곱근을 사용합니다. 표면 영역은 inner=outer=1.4이므로 반지름이 고정됩니다.

### 실행 결과 확인하기

`rgb/`에서 세 종류의 도형을 구분하고 `samples.json`에서 실제 좌표를 읽으세요.

| JSON 항목 | 의미 |
|---|---|
| `frame`, `region` | 어느 촬영의 어느 영역인지 나타냅니다. |
| `positions` | 해당 영역의 중심 좌표 30개입니다. |
| `min_radius`, `max_radius` | 기록된 중심 거리의 최솟값과 최댓값입니다. |

기본 세 프레임이면 JSON 기록은 3×3=9개이고 각 기록에 좌표 30개가 있습니다. 표본이 구간 양 끝에 정확히 도달할 필요는 없습니다. `sampling.usda`에는 마지막 배치가 저장되며, 모든 프레임의 좌표는 JSON에 있습니다.

## 2. 같은 계산을 ScriptNode와 Replicator에 연결하기

```bash
~/isaacsim/python.sh src/140_replicator_replicator_custom_og_randomizer/run.py --method manual --headless --output /tmp/tutorial140-manual
~/isaacsim/python.sh src/140_replicator_replicator_custom_og_randomizer/run.py --method replicator --headless --output /tmp/tutorial140-replicator
```

`manual`은 `/World/SamplingGraph`에 세 ScriptNode를 만들고 직접 평가합니다. `replicator`는 같은 노드 구성을 `on_frame`에 연결합니다. `--method`를 생략하면 replicator 방식입니다.

### 코드에서 볼 부분

```python
@ReplicatorWrapper
def sample_region(paths, inner, outer, seed):
    return configure(create_node('omni.graph.scriptnode.ScriptNode'),
                     paths, inner, outer, seed)
```

`configure()`는 `prims`, `inner`, `outer`, `seed` 입력을 만들고 `sphere_node.py` 내용을 노드의 script 입력에 넣습니다. `prims`는 위치를 쓸 USD 요소들의 경로입니다. 이 함수가 Replicator 문맥에 참여하도록 연결하는 부분이 `ReplicatorWrapper`입니다.

`sphere_node.py`의 `setup(db)`는 노드마다 난수 생성기를 한 번 만듭니다. `compute(db)`는 입력 반지름과 대상 prim을 검사한 뒤 좌표를 씁니다. 상태를 노드에 보관하므로 다음 호출에서는 난수 흐름이 이어집니다. `Sdf.ChangeBlock()`은 여러 USD 변경을 묶어서 알립니다.

실행을 진행하는 호출은 방식마다 다릅니다.

| 방식 | 위치 계산을 시작하는 부분 |
|---|---|
| direct | Python 반복문이 직접 좌표를 씁니다. |
| manual | `og.Controller.evaluate_sync(graph)`가 노드를 평가합니다. |
| replicator | `on_frame`에 연결된 노드가 `rep.orchestrator.step()`에서 실행됩니다. |

직접 방식은 하나의 난수 생성기, 그래프 방식은 영역별 seed를 사용하므로 세 결과의 좌표를 한 점씩 일치시키는 비교는 적절하지 않습니다. **각 방식이 같은 공간 제약을 만족하는지** 확인하세요.

### 실행 결과 확인하기

코드는 캡처 후 prim의 실제 translate를 다시 읽어 모든 반지름이 지정 범위 안인지 검사합니다. 노드 실행이 실패해 원점에 남았다면 surface와 shell 검사가 실패합니다. PNG가 생성되었다는 사실보다 이 좌표 확인이 실행 여부를 판단하는 데 더 직접적입니다.

`manual`의 `sampling.usda`를 열면 `/World/SamplingGraph`, replicator 결과에서는 `/Replicator` 아래 그래프를 살펴볼 수 있습니다. 노드 입력에서 반지름과 대상 경로를 확인하세요. `direct` 결과에는 샘플링 그래프가 없습니다.

## 3. 계산과 실행 연결의 역할 정리

```text
공간 규칙: 방향 + 부피에 맞는 반지름 → 좌표
실행 연결: Python / 수동 그래프 / Replicator 트리거
결과 확인: 실제 prim 좌표 → 거리 검사 → JSON·RGB 저장
```

ScriptNode는 실제 OmniGraph 노드지만 공식 예제의 `.ogn` 정의와 생성 Database를 빌드한 결과는 아닙니다. 이 폴더는 동적 입력과 Python 스크립트로 노드를 만들어 계산·입력·실행 조건의 관계를 익히도록 구성했습니다. 저장한 USD에는 스크립트 내용도 들어갑니다.

## 4. 간단한 확인 실험

기본 replicator 명령에서 **`--count`만 30에서 100으로 바꾸어** 새 출력 경로에 실행하세요.

영역은 여전히 세 개이고 각 중심의 허용 반지름도 같습니다. `samples.json`의 `positions`는 기록마다 100개, 전체 장면은 300개 도형이 됩니다. 표면이 더 조밀해져도 반지름이 1.4 m인지 확인하세요. 표본 수 증가와 공간 크기 증가를 구분하는 실험입니다.

## 실행할 때 막히면

- **표면·껍질이 원점에 모여 있거나 반지름 검사 실패**: ScriptNode 입력과 `sphere_node.py` 오류를 확인하세요. 렌더 문제만으로 판단하지 마세요.
- **그래프가 없음**: 선택한 `--method`를 확인하세요. direct는 그래프를 만들지 않습니다.
- **ScriptNode 실행 오류**: `omni.graph.scriptnode`가 활성화되는지 확인하세요. 코드는 이번 프로세스에서 script 실행 설정을 켭니다.
- **구 표면의 점이 안 보임**: 가림과 도형 크기 때문에 화면에서 구분하기 어려울 수 있습니다. 실제 중심 좌표를 먼저 확인하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Custom Replicator Randomization Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_custom_og_randomizer.html)에 대응합니다. 공식 구 영역 샘플링 개념을 실제 ScriptNode와 세 실행 경로로 재구성했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 replicator 한 프레임에서 내부 영역 표본 30개와 반지름 범위를 확인한 기존 기록입니다. 수동 그래프·직접 방식·모든 영역의 분포 균등성까지 검증한 기록은 아닙니다. 이번 개정에서는 새로운 GPU 실행 없이 코드와 문서의 대응을 확인했습니다.
