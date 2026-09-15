# 11. 로봇 USD를 참조할 때 환경까지 따라오지 않게 만들기

## 이번에 배우는 것

**로봇을 대표하는 defaultPrim을 정하고, 같은 USD를 두 번 배치하면서 한쪽만 수정하는 방법을 배웁니다.**

로봇 자산을 다른 장면으로 가져올 때 원본의 조명과 물리 환경까지 따라오면 관리하기 어렵습니다. 이번에는 큐브 몸체와 원통 바퀴 두 개로 작은 시각적 모형을 만들고, 재사용할 로봇 루트와 환경 루트를 나눕니다.

| 파일 | 담는 내용 | 확인할 차이 |
|---|---|---|
| `robot.usda` | 로봇 모형과 별도 환경 루트입니다. | defaultPrim은 `/mock_robot`입니다. |
| `assembly.usda` | 원본 로봇을 두 곳에 참조합니다. | RobotB 몸체에만 파란색을 덮어씁니다. |
| `flattened.usda` | 참조를 합성한 결과를 내보냅니다. | 두 로봇의 Prim 구조가 유지됩니다. |
| `composition.json` | 각 Stage의 Prim 목록입니다. | 가져온 범위와 평탄화 결과를 비교합니다. |

**defaultPrim은 USD 파일에서 대표로 사용할 루트 Prim입니다.** 참조 대상의 세부 Prim 경로를 생략하면 이 루트가 선택됩니다. 이 모형에는 관절·강체·주행 제어를 추가하지 않습니다.

## 1. 로봇 자산과 두 배치 만들기

Isaac Sim 5.1과 지원 GPU·드라이버를 준비하세요. 기본 도형만 사용하므로 외부 로봇·텍스처가 필요하지 않습니다. 저장소 루트에서 실행합니다.

```bash
~/isaacsim/python.sh src/11_python_usd_intro_to_usd/run.py --steps 120
```

설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 파일을 만든 뒤 앱을 120번 업데이트하고 종료합니다. 이 횟수는 물리 단계가 아니라 화면을 유지하는 앱 업데이트 수입니다. `--steps`를 생략하면 GUI를 계속 열어 두며, Headless 실행은 `--headless`를 추가합니다. Headless에서 생략한 횟수는 120입니다.

### 코드에서 볼 부분

원본은 다음 계층으로 구성합니다.

```text
robot.usda
├─ /mock_robot                 ← defaultPrim
│  ├─ body                     ← Cube
│  ├─ wheel_left               ← Cylinder
│  └─ wheel_right              ← Cylinder
└─ /World
   ├─ PhysicsScene
   └─ Light
```

몸체는 한 변 0.6 m, 중심 Z=0.4 m입니다. 두 바퀴는 반지름 0.2 m, 높이 0.1 m이고 원통 축은 Y입니다. 중심은 Y=±0.4 m, Z=0.2 m로 놓아 몸체 양옆에 배치합니다.

```python
asset.SetDefaultPrim(robot.GetPrim())
asset.GetRootLayer().Save()
```

`robot`은 `/mock_robot`을 가리킵니다. 이 줄은 환경을 삭제하는 것이 아니라, 다른 장면에서 기본적으로 참조할 루트를 지정합니다. 따라서 `robot.usda` 자체를 열면 `/World`도 보입니다.

조립 장면에서는 같은 파일을 두 경로에 참조합니다.

```python
for name, x in (("RobotA", -1.0), ("RobotB", 1.0)):
    prim = UsdGeom.Xform.Define(assembly, "/World/" + name)
    prim.GetPrim().GetReferences().AddReference("robot.usda")
    prim.AddTranslateOp().Set(Gf.Vec3d(x, 0, 0))
```

참조에 `/mock_robot` 경로를 직접 쓰지 않았습니다. 원본의 defaultPrim이 선택되므로 그 하위 몸체·바퀴만 각 배치 아래 합성됩니다. 조립 장면의 조명과 PhysicsScene은 `/World` 아래에 한 번 따로 만듭니다.

### 실행 결과 확인하기

결과는 이 폴더의 `output/날짜-시간/`에 생깁니다. GUI에 열린 `assembly.usda`에서 다음 구조를 확인하세요.

```text
/World
├─ Light
├─ PhysicsScene
├─ RobotA                     ← X=-1 m
│  ├─ body
│  ├─ wheel_left
│  └─ wheel_right
└─ RobotB                     ← X=+1 m
   ├─ body
   ├─ wheel_left
   └─ wheel_right
```

각 로봇 아래에 원본의 `/World` 환경이 따라오지 않아야 합니다. `composition.json`의 `asset_default_prim`은 `/mock_robot`이고, `assembly_prims`에는 위의 11개 Prim이 있어야 합니다. 모형이 주행하지 않는 것도 예상된 동작입니다.

## 2. 한쪽 색만 바꾸고 저장 방식 비교하기

### 코드에서 볼 부분

```python
UsdGeom.Cube.Get(assembly, "/World/RobotB/body").CreateDisplayColorAttr(
    [Gf.Vec3f(0.2, 0.5, 1.0)]
)
assembly.GetRootLayer().Save()
assembly.Export(str(output / "flattened.usda"))
```

원본 자산이 아니라 `assembly` Stage의 RobotB 몸체에 색을 작성합니다. 이 변경은 조립 레이어의 **override**, 즉 참조한 값 위에 덮어쓰는 의견입니다. 같은 원본을 참조하는 RobotA의 색까지 바뀌지는 않습니다.

`GetRootLayer().Save()`는 참조 구조와 조립 레이어의 변경을 저장합니다. `assembly.Export()`는 합성된 Stage를 평탄화해서 새 파일로 내보냅니다. **평탄화는 여러 도형을 하나의 메시로 합치는 작업이 아닙니다.** 몸체와 두 바퀴는 별도 Prim으로 남습니다. 이 동작은 [OpenUSD의 UsdStage Export·Flatten 설명](https://openusd.org/release/api/class_usd_stage.html)에서도 확인할 수 있습니다.

### 실행 결과 확인하기

1. `assembly.usda`에서 RobotB의 body만 파란색인지 확인합니다.
2. `robot.usda`를 따로 열어 원본 body에 같은 파란색 변경이 저장되지 않았는지 확인합니다.
3. `composition.json`의 `assembly_prims`와 `flattened_prims`를 비교합니다. 두 로봇과 각 하위 Prim이 유지되어야 합니다.
4. `assembly.usda`를 텍스트로 열면 `robot.usda` 참조와 RobotB의 색 의견을 확인할 수 있습니다.

실제 자산에는 외부 텍스처·MDL 의존성이 남을 수 있습니다. 평탄화했다고 그런 파일까지 모두 USD 안에 내장된다고 가정하지 마세요.

### GUI 설정에서 볼 부분

같은 자산 구조를 손으로 만들며 저장·참조 차이를 확인할 수도 있습니다.

1. 새 GUI의 **File > New**에서 **Create > Xform**으로 루트 `mock_robot`을 만듭니다.
2. Cube와 Cylinder 두 개를 그 아래 두고 `body`, `wheel_left`, `wheel_right`로 이름을 바꿉니다. 앞의 크기·위치를 Property에 맞추세요. Cube는 Size와 Scale, Cylinder는 반지름·높이·축을 함께 확인합니다.
3. 환경 조명과 PhysicsScene은 별도 `/World` 아래 둡니다. 로봇이 그 자식으로 들어갔다면 **Edit > Unparent**로 루트 수준으로 옮깁니다.
4. `mock_robot`을 우클릭해 **Set as a Default Prim**을 선택하고 **File > Save As**로 새 `.usda` 파일을 저장합니다.
5. 다시 **File > New**를 선택하고 **File > Add Reference** 또는 Content에서 파일을 Viewport로 드래그해 추가합니다. 로봇의 몸체·바퀴만 들어오는지 확인하세요.
6. 원본 장면을 별도 이름으로 복사해 그 복사본의 defaultPrim만 `/World`로 바꾼 뒤 새 장면에 참조해 보세요. 이번에는 몸체·바퀴 대신 환경의 Light와 PhysicsScene이 들어옵니다. 같은 파일의 데이터가 없어지는 것이 아니라 참조에서 선택하는 루트가 달라지는 것입니다. 로봇 재사용용 원본은 `/mock_robot`을 유지합니다.
7. 재사용 자산을 옮길 때는 Content에서 저장 USD를 우클릭해 **Collect Asset**을 사용할 수 있습니다. 수집한 위치에서 다시 열어 참조가 해결되는지 확인합니다.

이 절차의 메뉴와 자산 저장 개념은 [공식 Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html)를 참고하세요. GUI로 만든 파일은 `run.py`의 출력과 별도로 저장합니다.

## 3. Open·Reference·Flatten 차이 정리

| 선택 | 무엇을 다루는가 | 이번 파일에서 보이는 결과 |
|---|---|---|
| Open | 파일을 Stage로 엽니다. | `robot.usda`의 로봇과 환경 루트를 모두 봅니다. |
| Add Reference | 현재 장면에 자산의 선택 루트를 합성합니다. | defaultPrim인 로봇을 두 곳에 배치합니다. |
| Override | 현재 레이어에서 특정 속성을 덮어씁니다. | RobotB만 파란색이 됩니다. |
| Flatten/Stage Export | 합성 결과를 한 레이어로 내보냅니다. | 두 로봇의 Prim 계층은 유지됩니다. |

`assembly.usda`와 `robot.usda`는 상대 참조로 연결되므로 함께 보관해야 합니다. 원본을 변경하지 않고 배치마다 값을 다르게 만들 수 있는 이유는 조립 레이어의 의견이 각 참조 경로에 따로 작성되기 때문입니다.

## 4. 간단한 확인 실험

`run.py`의 배치 목록에서 **RobotB의 x 값만** 바꿉니다.

```python
for name, x in (("RobotA", -1.0), ("RobotB", 2.0)):
```

같은 명령으로 실행하면 RobotA는 X=−1 m, RobotB는 X=2 m에 배치됩니다. 두 로봇 중심 간 거리가 2 m에서 3 m로 바뀌고, RobotB의 파란색과 원본 모양은 유지되는지 확인하세요. `composition.json`은 Prim 이름을 기록하므로 위치 변화는 GUI Property나 `assembly.usda`의 Translate 값에서 확인해야 합니다.

## 실행할 때 막히면

- **참조했는데 로봇이 비어 있음**: `robot.usda` 경로와 `/mock_robot` defaultPrim이 존재하는지 확인하세요.
- **환경까지 로봇 아래로 따라옴**: 원본 defaultPrim의 하위에 환경을 넣었는지 확인합니다. 원본 파일을 여는 것과 참조로 추가하는 것도 구분하세요.
- **RobotA도 파란색이 됨**: 원본 body를 수정했는지 확인하세요. 이 실습의 색 의견은 `/World/RobotB/body`에 작성합니다.
- **평탄화했는데 몸체·바퀴가 따로 있음**: Prim 구조가 유지되는 예상 결과입니다. 메시 병합 작업과 다릅니다.
- **파일 이동 후 참조 오류**: `assembly.usda`와 `robot.usda`를 같은 폴더에 유지하고 실제 자산의 종속 파일도 확인합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html)에 대응합니다. 원문의 계층·defaultPrim·참조·저장 개념을 외부 자산이 없는 시각적 모형으로 구성했습니다. 로봇 articulation이나 주행 제어 실습은 포함하지 않습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 이전 코드에서 Headless 2회 앱 업데이트로 defaultPrim·두 참조·조립 Prim 11개를 확인한 기록입니다. 현재 파일의 결과는 위 계층과 대조해 다시 확인하세요. `tutorial.json`의 부분 실행 검증은 GUI 재구성과 위치 변경 실험까지 포함하지 않습니다.
