# 162. 위치는 따로 바꾸고 모양은 함께 공유하기

## 이번에 배우는 것

**동일한 큐브를 여러 링크에서 참조하고, 링크의 위치는 독립적으로 바꾸면서 내부 geometry는 하나의 prototype으로 공유합니다.**

로봇이 여러 대 있어도 같은 부품의 메시를 매번 별도로 정의할 필요는 없습니다. 다만 각 로봇의 링크는 서로 다른 위치로 움직여야 합니다. 이번에는 “개별 위치”와 “공유 모양”을 USD 계층의 다른 위치에 놓는 이유를 작은 장면으로 확인합니다.

| 항목 | 이번 예제의 역할 |
|---|---|
| `meshes.usda` | 한 변 0.5 m인 큐브 원본 정의 |
| `instances.usda` | 원본을 참조하는 네 링크의 배치 |
| `Link` | 각각 따로 바꿀 수 있는 위치 |
| `Geometry` | reference와 instanceable을 가진 공유 루트 |
| `instances.json` | 실제 instance·prototype·proxy 상태 기록 |

여기서 prototype은 여러 instance가 공유하는 USD 내부 정의이고, instance proxy는 그 공유된 자식을 각 instance 경로로 바라보는 방식입니다.

## 1. 네 개의 공유 큐브 만들기

Isaac Sim 5.1과 지원 GPU·드라이버가 필요합니다. 외부 로봇 자산은 사용하지 않습니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/162_motion_instanceable_assets/run.py --count 4 --steps 120
```

120번의 **앱 업데이트** 후 종료합니다. 이 예제에는 물리 장면과 `world.step()`이 없으므로 120번을 물리 시간으로 환산하지 않습니다. `--steps`를 빼면 창을 닫을 때까지 유지하고, `--headless`를 추가하면 창 없이 실행합니다. Headless에서 단계 수를 생략하면 600번 업데이트합니다.

실행마다 이 폴더의 새 `output/run_*`에 결과를 저장합니다. `--output /절대경로/새폴더`로 지정할 수도 있지만 기존 경로는 거부합니다.

### 코드에서 볼 부분

먼저 원본 파일에 `/Geometry/Cube`를 만들고, 각 링크에서 다음 두 호출을 수행합니다.

```python
geometry.GetReferences().AddReference('./meshes.usda', '/Geometry')
geometry.SetInstanceable(not args.no_instancing)
```

`AddReference()`의 첫 인수는 USD **파일 경로**, 둘째는 그 파일 안의 **Prim 경로**입니다. 상대 파일 참조이므로 `meshes.usda`와 `instances.usda`를 함께 옮겨야 합니다. `SetInstanceable(True)`는 같은 구성을 가진 참조가 공통 prototype을 사용할 수 있게 합니다.

```text
/World/Robot_0/Link              ← 개별 translate
                 /Geometry     ← reference + instanceable
                          /Cube ← 공유된 자식
```

각 Link의 translate는 `(i × 0.8, 0, 0.25)`입니다. 따라서 네 큐브의 중심 X는 0, 0.8, 1.6, 2.4 m이고 Z는 0.25 m입니다. 물리를 추가하지 않았으므로 큐브가 떨어지거나 관절이 움직이는 예제는 아닙니다.

### 실행 결과 확인하기

루프가 끝나면 `instances.json`과 같은 내용의 콘솔 출력이 생성됩니다.

| 필드 | 기본 실행의 확인 기준 |
|---|---|
| `path` | `/World/Robot_i/Link/Geometry` 네 경로 |
| `is_instance` | 네 항목 모두 `true` |
| `prototype` | 네 항목이 같은 prototype을 가리킴 |
| `child_is_instance_proxy` | Cube 자식이므로 `true` |

prototype의 구체적인 경로 문자열은 실행마다 달라질 수 있습니다. 이름 자체보다 공유 관계를 확인하세요. JSON은 장면 생성 당시 수집한 상태이며, GUI에서 나중에 수정한 결과를 다시 측정하지는 않습니다.

## 2. 공유를 끈 결과와 편집 범위 비교하기

다음 실행은 같은 참조 구조에서 instanceable만 끕니다.

```bash
~/isaacsim/python.sh src/162_motion_instanceable_assets/run.py --count 4 --no-instancing --steps 120
```

### 코드에서 볼 부분

관찰 함수는 서로 다른 계층을 조사합니다.

```python
geometry.IsInstance()
geometry.GetPrototype()
stage.GetPrimAtPath(str(geometry.GetPath()) + '/Cube').IsInstanceProxy()
```

`IsInstance()`는 공유 루트인 Geometry를, `IsInstanceProxy()`는 공유 자식인 Cube를 확인합니다. `--no-instancing` 결과에서는 두 상태가 false이고 prototype이 null이어야 합니다. reference 자체는 여전히 남습니다. **참조와 instancing은 같은 말이 아닙니다.**

편집 차이는 `--steps` 없이 GUI를 열어 관찰할 수 있습니다.

1. 기본 실행에서 `/World/Robot_0/Link`의 Translate를 바꿔 보세요. 다른 Link 위치는 그대로입니다.
2. 그 아래 `Geometry/Cube`의 속성을 직접 바꾸려 해 보세요. 공유 자식의 개별 편집은 제한됩니다.
3. 공통 모양을 바꾸려면 원본 `meshes.usda`를 수정합니다. 특정 instance만 다르게 만들려면 해당 Geometry의 instanceable을 끈 뒤 별도 속성을 작성합니다.

파일이 USD reference로 연결되어 있으면 instancing을 끈 상태에서도 원본 수정이 전달될 수 있습니다. 공유 자식 편집 제한과 원본 참조의 변경 전파를 구별하세요.

### 실제 로봇 자산에 적용하기

URDF/MJCF를 가져올 때도 링크의 개별 변환과 공유 geometry 계층을 확인합니다. 사용할 URDF·MJCF와 그 파일이 참조하는 메시·재질을 함께 준비한 뒤 다음 순서로 진행하세요.

1. 새 Stage에서 **Window > Extensions**의 `isaacsim.asset.importer.urdf` 또는 `isaacsim.asset.importer.mjcf`를 확인하고 **File > Import**로 `.urdf` 또는 `.xml`을 선택합니다.
2. Model 영역에서 **Referenced Model**을 선택하고 **USD Output**에 새 출력 폴더를 지정해 Import합니다. **Create in Stage**는 현재 Stage에 직접 만드는 별도 선택입니다.
3. 가져온 로봇의 링크를 펼쳐 geometry 부모의 Instanceable과 자식의 instance proxy 상태를 확인합니다. 링크를 옮겼을 때 다른 로봇의 위치와 구별되는지도 살펴보세요.
4. 새 Stage에서 출력한 주 robot USD를 참조해 구조가 유지되는지 확인합니다. 하위 USD·메시·재질 파일도 함께 보존합니다.

공식 Instanceable Assets 본문의 과거 `Create Instanceable Asset` 옵션을 현재 화면에서 찾기보다, 생성된 geometry 부모와 자식의 instance 상태를 확인하세요. 설치본 URDF·MJCF는 instanceable 가져오기 변경이 반영되어 있습니다. 출력 하위 USD와 재질을 함께 보존해야 참조가 유지됩니다.

기존 자산을 변환할 때는 원본 복사본에서 메시 위에 Xform을 만들고, 메시가 가진 reference를 그 부모로 옮깁니다. 공통 geometry를 별도 USD로 만든 뒤 부모가 그 파일을 참조하도록 연결하고 instanceable을 켭니다. 계층을 옮겼다면 재질·충돌 관계가 여전히 유효한 Prim을 가리키는지도 확인해야 합니다. 참조된 공유 파일 밖으로 나간 관계는 새 부모 또는 공유 파일 안의 유효한 경로로 정리해야 합니다. 이 폴더는 사용자 자산 변환기가 아니라 올바른 최종 계층을 직접 만드는 예제입니다.

## 3. 무엇을 공유하고 무엇을 따로 두는지 정리

| 위치 | 독립적인 값 | 공유되는 값 |
|---|---|---|
| `Robot_i/Link` | 링크 위치 | 없음 |
| `Geometry` | 각 instance의 경로 | 동일한 참조 구성 |
| `Geometry/Cube` | 개별 proxy 편집은 제한 | 크기 등 원본 geometry 정의 |

링크의 움직임과 메시의 정의를 분리하면 같은 모양을 다른 위치에 놓을 수 있습니다. 이 결과는 USD의 공유 구조를 보여 줍니다. GPU 메모리 절감량이나 환경 복제 성능을 측정한 결과는 아닙니다.

## 4. 간단한 확인 실험

`--count`만 4에서 20으로 바꿔 실행해 보세요.

- JSON 항목은 20개로 늘어야 합니다.
- `is_instance`와 `child_is_instance_proxy`가 여전히 true인지 확인합니다.
- 서로 다른 prototype 경로의 개수는 같은 모양을 공유하는 경우 하나로 유지되는지 봅니다.

큐브 수와 공유 정의 수를 별도로 세는 것이 이 실험의 핵심입니다.

## 실행할 때 막히면

- **파일을 옮긴 뒤 큐브가 사라짐**: 두 USD의 상대 위치가 유지됐는지 확인하세요.
- **Cube 속성을 편집할 수 없음**: instance proxy인지 확인하세요. 공유 자식의 정상적인 제한일 수 있습니다.
- **JSON이 아직 없음**: JSON은 루프 종료 후 씁니다. 창을 닫거나 유한한 `--steps`로 실행하세요.
- **물체가 떨어지지 않음**: 이 코드는 USD 구조를 만들고 `app.update()`만 호출합니다. 물리 낙하는 포함하지 않습니다.
- **`No module named isaacsim`**: 시스템 Python 대신 설치본 `python.sh`를 사용하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Instanceable Assets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/isaac_lab_tutorials/tutorial_instanceable_assets.html)에 대응합니다. 외부 로봇 없이 두 USD 파일을 만들어 참조 계층과 instance 상태를 비교합니다. importer 설명은 설치본의 UI와 변경 기록도 대조했습니다.

`tutorial.json`은 `not_run`입니다. 공유 상태의 기대값은 실제 실행 시 확인할 기준이며, 물리 동작이나 메모리 성능 검증을 포함하지 않습니다.
