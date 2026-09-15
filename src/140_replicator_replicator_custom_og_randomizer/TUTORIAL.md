# 140. 직접 만든 구 영역 샘플러를 OmniGraph와 Replicator에 연결하기

권장 학습 순서 **140** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t045`

이 실습의 목표는 **같은 무작위 배치 계산을 어디에서 실행하는지** 이해하는 것입니다. 작은 Cube는 반지름 0.7 m 구 내부, Sphere는 반지름 1.4 m 구 표면, Cylinder는 2.1–2.6 m 구 껍질에 배치합니다. 직접 USD 값을 쓰는 경로, 수동 OmniGraph, ReplicatorWrapper가 만드는 그래프 경로를 모두 실행할 수 있습니다.

공식 튜토리얼은 `.ogn` 정의와 생성된 Database를 가진 세 개의 등록 노드를 만듭니다. 이 패키지는 **동일한 입력 검증·구 체적 샘플링·USD 변경 코드를 로컬 `sphere_node.py`와 ScriptNode에 구현**합니다. 이렇게 하면 별도 확장 빌드나 생성 파일 없이 패키지를 복사해 사용할 수 있습니다. 세 영역은 `inner`, `outer` 두 입력으로 통합합니다. 공식 등록 노드 자체의 재빌드를 했다고 주장하지 않습니다.

## 이 실습의 의도

구 내부·표면·껍질이라는 서로 다른 공간 제약을 직접 구현하고, 그 계산을 USD 직접 쓰기·수동 OmniGraph·Replicator 트리거에 연결하는 실습입니다. Cube·Sphere·Cylinder를 각 영역에 대응시켜 같은 화면에서도 표본의 소속을 구분할 수 있습니다. 기본 `replicator` 실행은 영역당 30개씩 90개 도형을 3회 재배치하고 RGB·좌표 기록·그래프가 포함된 USD를 저장합니다.

## 실행 후 확인할 것

- **공간 제약:** `samples.json`에서 각 프레임의 `inside`, `surface`, `shell` 기록을 확인합니다. 원점부터 **prim 중심까지의 거리**는 각각 0–0.7 m, 1.4 m, 2.1–2.6 m여야 합니다. 도형 표면 일부가 경계 밖으로 보이는 것은 중심 좌표 검사의 실패가 아닙니다.
- **표본 개수와 난수:** 기본값이면 기록은 3프레임 × 3영역의 9개이고 각각 `positions` 30개를 갖습니다. 내부·껍질의 `min_radius`와 `max_radius`가 구간 양 끝에 정확히 도달할 필요는 없습니다. 반지름 1.4의 표면은 부동소수점 오차 범위에서 확인합니다.
- **시각적 대응:** `rgb/`와 `sampling.usda`의 `/World/inside`, `/World/surface`, `/World/shell`을 비교해 Cube·Sphere·Cylinder가 세 영역을 이루는지 봅니다. 화면에 잘 안 보이는 표본도 좌표 기록으로 확인할 수 있습니다.
- **실행 경로:** `manual`은 `/World/SamplingGraph`의 세 ScriptNode와 `inputs:inner`, `outer`, `seed`, `prims`를 확인합니다. `replicator`는 `/Replicator` 아래 그래프를, `direct`는 그래프 없이 변경된 좌표를 확인합니다. 방법마다 난수 상태가 달라 좌표의 일대일 일치는 요구하지 않습니다.
- **실패 구분:** 원점에만 모인 표면·껍질 표본은 정상 결과가 아니며 런처의 반지름 검사도 실패해야 합니다. 저장한 ScriptNode는 이 실습의 구현으로, 공식 `.ogn` 등록 노드를 빌드한 결과와 구분합니다.

## GUI 실행과 종료

GUI에서 `--steps`를 생략하면 정해진 데이터 생성과 저장을 마친 뒤 사용자가 창을 닫을 때까지 장면을 유지합니다. 양수 `--steps N`은 **생성 완료 후 GUI를 관찰하는 app update 횟수**입니다. 생성 작업 자체나 데이터 프레임 수를 제한하는 값은 아니며, `--frames` 등으로 요청한 데이터가 무한히 늘어나지 않습니다. `--headless`는 관찰 대기 없이 기존 유한 작업을 마치면 종료합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 실행

Isaac Sim 5.1.0과 지원 NVIDIA RTX GPU/드라이버가 필요합니다. 모든 도형과 조명은 코드에서 만들며 외부 자산이나 형제 패키지가 필요하지 않습니다. `omni.graph.scriptnode`는 실행 중 활성화됩니다.

이 패키지 폴더의 터미널에서:

```bash
ISAACSIM="$HOME/isaacsim"
python3 run.py --help
"$ISAACSIM/python.sh" run.py --method direct --headless --output output/direct
"$ISAACSIM/python.sh" run.py --method manual --headless --output output/manual
"$ISAACSIM/python.sh" run.py --method replicator --headless --output output/replicator
```

설치 경로가 다르면 `ISAACSIM`을 변경합니다. Windows에서는 `python.bat`를 사용합니다. 각 경로는 **새 폴더**여야 합니다. 기본값은 이 패키지의 `output/`입니다. `--frames 3 --count 30`은 영역당 30개, 캡처 3회를 의미합니다. GUI를 보려면 `--headless`를 뺍니다. 관찰을 계속하려면 실행이 끝난 후 `output/.../sampling.usda`를 Isaac Sim의 **File > Open**으로 엽니다.

## 순서대로 해보기

1. `direct` 결과의 `rgb/` 이미지와 `samples.json`을 확인합니다. 각 표본은 로컬 좌표이며 부모가 단위 변환이어서 이 장면에서는 월드 좌표와 같습니다.
2. `sphere_node.py`의 `compute(db)`를 읽습니다. 먼저 반지름과 대상 prim 유효성을 검사하고, 실패하면 `execOut`을 비활성화하고 오류를 기록합니다.
3. `manual`을 실행합니다. `run.py`는 `/World/SamplingGraph`에 노드 세 개를 직접 만들고 동적 입력을 추가한 후 `Controller.evaluate_sync()`로 평가합니다. 저장된 USD를 열고 **Window > Visual Scripting > Action Graph**의 그래프 선택기에서 `SamplingGraph`를 확인합니다. 설치 UI에서 해당 편집기가 안 보이면 **Window > Extensions**에서 `omni.graph.window.generic`을 활성화합니다.
4. `replicator`를 실행합니다. `@ReplicatorWrapper` 안에서 만든 노드는 `rep.trigger.on_frame()`에 연결됩니다. 이때 `rep.orchestrator.step()`이 실행을 구동합니다. 저장된 stage에서 `Replicator`의 SDG 그래프와 ScriptNode의 입력을 비교합니다.
5. 그래프 노드를 선택하고 Property에서 `inputs:inner`, `inputs:outer`, `inputs:seed`, `inputs:prims`를 찾습니다. `prims`는 대상 USD prim을 가리키는 관계형 입력입니다. 스크립트 문자열은 저장된 USD에 포함되므로 저장한 그래프도 원래 Python 경로에 의존하지 않습니다.
6. `samples.json`의 `min_radius`, `max_radius`를 확인합니다. 코드도 위치 벡터의 길이를 계산해 영역 밖 표본이 나오면 예외를 냅니다. **위치가 모두 0인 채로 그래프 실행에 실패하는 경우**도 표면/껍질 검사가 탐지합니다.

## 샘플링을 이해하기

구 표면에서 위도 각도를 균등하게 뽑으면 극점 주변이 조밀해집니다. 여기서는 방향의 z 성분을 `[-1, 1]`에서 균등하게 뽑고 방위각을 `[0, 2π]`에서 뽑습니다. 구 내부의 부피는 반지름의 세제곱에 비례하므로 반지름은 `uniform(inner³, outer³) ** (1/3)`로 구합니다.

- 내부: `inner=0`, `outer=0.7`.
- 표면: `inner=outer=1.4`여서 모든 점의 거리도 1.4입니다.
- 껍질: `inner=2.1`, `outer=2.6`여서 빈 내부가 보입니다.

`seed`는 노드 인스턴스마다 별도 난수 생성기를 초기화합니다. 같은 프레임을 반복해서 계산해도 상태가 진행하므로 새 배치가 나옵니다. `direct` 경로는 단일 난수 생성기를 사용하므로 그래프 경로와 좌표를 한 점씩 동일하게 맞추려는 비교는 하지 않습니다.

## API와 장면 개념

| 요소 | 의미 |
|---|---|
| USD Stage / Prim / Xformable | 장면 문서 / 경로가 있는 요소 / 위치·회전·크기를 가질 수 있는 요소입니다. |
| `xformOp:translate` | prim의 이동 연산입니다. 속성을 만드는 것과 값을 쓰는 것은 구분됩니다. |
| `Sdf.ChangeBlock` | 여러 USD 값 변경을 한 묶음으로 알려 불필요한 변경 통지를 줄입니다. |
| `ScriptNode` | `setup`, `compute`, 선택적 `cleanup` 콜백을 실행하는 실제 OmniGraph 노드입니다. |
| `db.inputs`, `db.outputs` | 그래프 포트의 값입니다. `db.per_instance_state`에는 노드별 난수 상태를 보관합니다. |
| `set_target_prims()` | USD prim 목록을 그래프 target 포트에 연결합니다. |
| `ReplicatorWrapper` / `create_node()` | 사용자가 작성한 함수를 Replicator의 그래프 구성 문맥에 참여시킵니다. |
| `ExecutionAttributeState` | 다음 실행 노드로 흐름을 보낼지 명시합니다. 입력 검증 실패가 숨겨지지 않게 합니다. |

공식 `.ogn` 버전에서 입력 스키마는 `target prims`, `execution execIn`, `float radius` 또는 `radius1/radius2`, 출력은 `execution execOut`입니다. 노드 구현의 `compute(db)`는 여기에 대응합니다. `.ogn`을 직접 수정하는 확장 개발을 하려면 공식 5.1 설치의 `exts/isaacsim.replicator.examples/.../ogn/`에 있는 생성 Database와 `nodes/` 구현을 구분해서 읽으십시오. 이 실습에서는 동적 포트 생성 코드가 그 스키마 역할을 합니다.

## 한 변수만 바꾸는 실험

`run.py`의 `regions`에서 shell의 `outer`만 `2.6`에서 `3.2`로 바꾼 후 새 경로에 실행합니다. `samples.json`의 표면 영역은 계속 1.4에 있고 shell의 최대 거리만 증가해야 합니다. 다음으로 `--count 300`을 사용하면 분포를 더 쉽게 관찰할 수 있습니다.

## 문제 해결과 확인 범위

- ScriptNode 실행 오류가 보이면 `sphere_node.py`의 예외와 반지름 값을 먼저 확인합니다. `run.py`는 해당 프로세스에서 ScriptNode 실행 설정을 활성화합니다.
- `No module named omni`: Isaac Sim의 Python으로 실행해야 합니다. 일반 Python은 `--help`만 지원합니다.
- 그래프가 안 보이는 경우 저장한 파일의 `/World/SamplingGraph` 또는 `/Replicator` 경로를 Stage 창에서 먼저 찾습니다. `direct` 모드에는 샘플링 그래프가 없습니다.
- 문법/CLI 검사는 GPU 렌더링 또는 노드 계산의 실행 증거가 아닙니다. 실제 생성된 이미지와 반지름 기록으로 확인하십시오.

## 출처

- [Isaac Sim 5.1.0: Custom Replicator Randomization Nodes — Implementation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_custom_og_randomizer.html#implementation)
- [Isaac Sim 5.1.0: Python Custom OmniGraph Nodes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omnigraph/omnigraph_custom_python_nodes.html)
- 5.1 설치 API 확인: `omni.graph.scriptnode`의 `OgnScriptNodeDatabase.py`, `omni.graph`의 `node_controller.py`, `omni.replicator.core/scripts/utils/utils.py`의 `create_node`와 `set_target_prims`.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
