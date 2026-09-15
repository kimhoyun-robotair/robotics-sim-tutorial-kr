# 172. 사진으로 재구성한 공간에서 로봇이 주행하려면?

## 이번에 배우는 것

**NuRec 장면에서 Carter를 주행시키고, 눈에 보이는 바닥과 로봇을 지지하는 충돌면의 차이를 확인합니다.**

사진으로 재구성한 방은 실제 공간처럼 보일 수 있습니다. 하지만 렌더링 표현에 바닥이 있다고 해서 물리 엔진이 그곳을 접촉면으로 사용하는 것은 아닙니다. 이번에는 준비된 NuRec 데이터셋을 열고 로봇의 실제 위치를 기록하면서 시각 장면과 물리 장면을 함께 살펴봅니다.

| 구성 | 역할 |
|---|---|
| 외부 NuRec 데이터셋 | Gaussian 기반으로 재구성한 실제 공간을 제공합니다. |
| `scenarios.json` | 네 장면의 파일 경로·시작점·목표 이동 값을 지정합니다. |
| Carter navigation USD | 로봇과 주행 OmniGraph를 제공합니다. |
| `run.py` | 선택 장면을 열고 실제 chassis 위치를 기록합니다. |
| `trajectory.json` | 앱 업데이트 번호, 타임라인 초, 세계 위치를 저장합니다. |

이 실습은 이미 재구성된 공간을 사용합니다. 사진으로부터 모델을 학습하거나 새로운 경로 계획 알고리즘을 만드는 과정은 포함하지 않습니다.

## 1. cafe 장면에서 주행 기록 만들기

Isaac Sim 5.1과 지원 RTX GPU·드라이버, NuRec neural volume renderer가 필요합니다. [PhysicalAI-Robotics-NuRec 데이터셋](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-NuRec)을 별도로 준비하세요. 루트 USD만 복사하지 말고 참조하는 volume과 텍스처의 폴더 구조를 유지합니다. 또한 5.1 자산 루트의 `Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd`와 참조 로봇 자산에도 접근할 수 있어야 합니다.

아래는 저장소 루트에서 실행하는 명령입니다. `/data/PhysicalAI-Robotics-NuRec`은 준비한 데이터셋의 실제 경로로 바꾸세요.

```bash
python3 src/172_digital_twin_nurec_navigation/run.py \
  --dataset /data/PhysicalAI-Robotics-NuRec --scenario cafe --check
```

이 검사는 `nova_carter-cafe/stage.usdz`의 존재를 확인합니다. 내부 참조, 신경 렌더링과 주행은 검사하지 않습니다. 화면을 보며 500회 앱 업데이트를 실행하려면 다음 명령을 사용하세요.

```bash
~/isaacsim/python.sh src/172_digital_twin_nurec_navigation/run.py \
  --dataset /data/PhysicalAI-Robotics-NuRec --scenario cafe --steps 500 \
  --output src/172_digital_twin_nurec_navigation/output/cafe
```

새 출력 경로를 사용하세요. `--steps`를 빼면 창을 직접 닫을 때까지 주행과 관찰을 계속합니다. `--headless`를 추가하면 창 없이 실행하며, 단계 수를 생략한 headless 실행은 500회입니다. **500회는 물리 시간 500초나 목표 도달 조건을 의미하지 않습니다.**

### 코드에서 볼 부분

장면을 연 뒤 실행기는 PhysicsScene의 update type을 `Synchronous`로 맞추고 `/World/NovaCarterNav`에 로봇을 추가합니다. 주행 그래프가 읽는 대상은 그 아래 `targetXform`, 위치를 관찰하는 대상은 `chassis_link`입니다.

```python
position = UsdGeom.Xformable(chassis).ComputeLocalToWorldTransform(0).ExtractTranslation()
records.append({"step": step, "timeline_seconds": timeline.get_current_time(),
                "chassis_world_position": list(position)})
```

이 기록은 목표 설정값을 복사하지 않고 **장면에서 실제 chassis의 세계 변환을 읽습니다.** 샘플은 10 업데이트마다 저장하며 제한 실행에서는 마지막 업데이트도 저장합니다. `step`은 0부터 시작하므로 500회가 끝난 마지막 번호는 499입니다.

### 실행 결과 확인하기

GUI에서 neural volume 배경과 Carter가 함께 보이는지 먼저 확인하세요. 로봇만 보이면 장면 재구성 표현의 로딩이 완료되었다고 판단할 수 없습니다.

종료 후 `output/cafe/trajectory.json`을 엽니다.

| 키 | 의미 | 비교 방법 |
|---|---|---|
| `step` | 0부터 시작하는 앱 업데이트 번호 | 기록 간격을 확인합니다. |
| `timeline_seconds` | 관찰 시점의 시뮬레이션 시간 | 실제로 시간이 진행했는지 봅니다. |
| `chassis_world_position` | chassis의 세계 좌표 `[x,y,z]` | 이동 방향과 높이 변화를 봅니다. |

장면의 거리 단위도 확인한 뒤 위치를 해석하세요. 좌표가 움직여도 목표에 도달했다고 자동 판정하지 않습니다. 화면의 장애물, 목표의 세계 위치, 궤적을 함께 확인해야 합니다. 창을 닫아 조기 종료한 기록은 요청한 500회를 모두 수행한 기록과 구분합니다.

## 2. 다른 장면과 보이지 않는 충돌면 비교하기

`scenarios.json`의 네 항목은 다음과 같습니다.

| 장면 | 데이터셋 내 루트 파일 | 시작 위치 | `relative_target` | 평면 추가 |
|---|---|---|---|---|
| cafe | `nova_carter-cafe/stage.usdz` | `(0,0,0)` | `(-3,-1.5,0)` | 없음 |
| galileo | `nova_carter-galileo/stage.usdz` | `(-2.5,2.5,0)` | `(4,0,0)` | 없음 |
| wormhole | `nova_carter-wormhole/stage.usdz` | `(0,0,0)` | `(5,0,0)` | 없음 |
| lounge | `zh_lounge/usd/zh_lounge.usda` | `(-1.5,-3,-1.6)` | `(-0.5,5,-1.6)` | 있음 |

`--scenario lounge`로 바꾸고 새 출력 경로에 실행해 보세요. GUI의 Stage에서 `/World/CollisionPlane`을 선택합니다.

### 코드에서 볼 부분

lounge에서 추가하는 평면은 다음 속성을 사용합니다.

```python
plane.GetAttribute("xformOp:scale").Set((10, 10, 1))
plane.GetAttribute("xformOp:translate").Set(tuple(config["start"]))
plane.GetAttribute("visibility").Set("invisible")
UsdPhysics.CollisionAPI.Apply(plane).CreateCollisionEnabledAttr(True)
```

평면은 시작점 높이에 놓이며, 화면에서는 숨겨도 collision은 켜집니다. `scale=(10,10,1)`은 생성한 기본 평면의 배율이지 그 자체로 면적이나 가로 길이를 뜻하는 값은 아닙니다. 실제 크기는 원래 mesh와 함께 확인합니다.

이 평면이 있어 로봇은 렌더링된 바닥과 별개로 물리 접촉면을 사용할 수 있습니다. 반대로 neural volume이 잘 보이는데 로봇이 떨어진다면 렌더러보다 충돌 설정부터 확인해야 합니다.

목표 좌표도 같은 구분이 필요합니다. `relative_target`은 `targetXform`의 **부모 기준 이동 값**입니다. `trajectory.json`은 세계 좌표입니다. 두 배열을 그대로 빼서 도달 오차를 계산하지 말고 Stage 계층의 변환을 적용한 목표 세계 위치와 비교하세요.

## 3. 보이는 공간과 계산하는 공간 정리

```text
NuRec volume → 카메라에 보이는 재구성 공간
충돌 형상   → 로봇이 접촉하는 물리 공간
navigation graph + 목표 변환 → 로봇 주행
실제 chassis 세계 변환      → trajectory.json
```

주행이 멈추었을 때는 먼저 어느 연결이 끊겼는지 살펴봅니다. 배경이 없으면 데이터와 렌더링, 로봇이 떨어지면 충돌면, 지면에 서 있지만 이동하지 않으면 목표·주행 그래프·물리 진행을 확인할 수 있습니다.

## 4. 간단한 확인 실험

`scenarios.json`의 cafe `relative_target`에서 x만 **-3 → -2**로 바꾸고 같은 500회 조건으로 재실행하세요. 원래 값을 기록하고 새 출력 경로를 사용합니다.

출발점과 장면이 같으므로 목표 변경에 따른 초기 진행 방향과 궤적을 비교할 수 있습니다. 목표가 가까워졌더라도 동일 업데이트 수 안의 도달을 보장하지는 않습니다. 최종 위치뿐 아니라 중간 위치와 타임라인 초를 함께 비교하세요.

## 실행할 때 막히면

- **root scene이 없다는 오류**: 데이터셋 루트와 장면별 상대 경로를 대조하세요. `--dataset`에는 개별 USD가 아닌 데이터셋 폴더를 지정합니다.
- **Carter만 보이고 배경은 비어 있음**: NuRec renderer와 volume 참조를 확인하세요. 일반 mesh 렌더링 성공만으로 neural rendering을 확인할 수 없습니다.
- **로봇이 아래로 떨어짐**: 충돌 형상과 시작 z를 확인하세요. 특히 lounge의 추가 평면을 점검합니다.
- **로봇이 지면에서 멈춤**: 공식 navigation asset, Script Node 실행, 목표 변환, synchronous 물리 설정을 확인하세요.
- **궤적 파일이 짧음**: 창을 일찍 닫았는지와 요청한 update 상한을 확인하세요. 프로그램 종료 자체는 목표 도달 판정이 아닙니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Neural Volume Rendering](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/assets/usd_assets_nurec.html)에 대응합니다. 원문의 네 장면을 하나씩 선택하도록 구성하고 위치 기록을 추가했습니다. 직접 재구성할 때 필요한 학습 환경은 이 실습과 별도입니다.

문서에서는 실행기와 네 장면 설정을 대조했습니다. 외부 데이터셋 로딩, GPU neural rendering과 목표 도달은 이번 개정에서 실행하지 않았으며 `tutorial.json`의 상태는 `not_run`입니다.
