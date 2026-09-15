# 97. 3D 장애물을 지도와 블록 장면으로 바꾸기

## 이번에 배우는 것

**같은 장애물을 2D 점유 지도로 만들고 다시 블록 장면으로 가져오며, 이 과정에서 남는 정보와 사라지는 정보를 비교합니다.**

로봇이 사용할 지도에는 모든 표면의 색이나 곡면이 필요하지 않을 수 있습니다. 이번 실습에서는 일정 높이의 공간을 작은 격자로 나누어 장애물이 있는 칸을 표시합니다. 이를 **점유 지도(occupancy map)**라고 부릅니다.

지도 이미지에서 검은 칸을 다시 충돌 블록으로 만들 수 있지만, 원래의 3D 물체가 그대로 복원되지는 않습니다. 이 차이를 보기 위해 옆으로 누운 원뿔 하나를 사용합니다.

| 단계 | 입력 | 얻는 결과 |
|---|---|---|
| 장면 준비 | `mapping_lab.usda` | Collider가 있는 원뿔 |
| 지도 계산 | 높이, 계산 영역, Cell Size | occupied/free/unknown 격자 |
| 이미지 저장 | 색상과 이미지 회전 설정 | `output/occupancy.png` |
| 블록 재구성 | PNG와 같은 Cell Size | `output/block_world.usd`에 저장할 장면 |

## 1. 원뿔의 단면을 점유 지도로 만들기

Isaac Sim 5.1과 지원 NVIDIA RTX GPU, GUI 세션을 준비합니다. 저장소 루트에서 앱을 실행하세요.

```bash
mkdir -p src/97_digital_twin_asset_generator_occupancy_map/output
~/isaacsim/isaac-sim.sh
```

`output/`은 생성한 PNG와 재구성 장면을 저장할 폴더입니다.

1. **File > Open**에서 `src/97_digital_twin_asset_generator_occupancy_map/mapping_lab.usda`를 엽니다.
2. **Window > Extensions**에서 `isaacsim.asset.gen.omap`과 메뉴를 제공하는 `isaacsim.asset.gen.omap.ui`가 활성화되어 있는지 확인합니다.
3. **Tools > Robotics > Occupancy Map**을 열고 아래 표의 값을 입력합니다.
4. **Use PhysX Collision Geometry**를 켜고 **CALCULATE**, **VISUALIZE IMAGE**를 누릅니다.
5. Occupied는 검정, Freespace는 흰색, Unknown은 회색으로 정합니다. Block World와 방향을 비교할 이번 저장본은 **Rotate Image=180°**로 만듭니다.
6. **Save Image**로 이 폴더 아래 새 `output/occupancy.png`를 저장합니다. 표시된 origin, resolution, 회전값도 함께 메모하세요.

### 설정에서 볼 부분

| 설정 | 값 | 의미 |
|---|---|---|
| Origin | `(0, 0, 0.1)` | 지도 계산을 시작할 빈 위치 |
| Lower Bound | `(-1, -1, 0)` | Origin 기준 계산 영역의 하한 |
| Upper Bound | `(1, 1, 0)` | Origin 기준 계산 영역의 상한 |
| Cell Size | `0.05` | 한 픽셀이 나타내는 길이 0.05 m |

Bounds는 Origin에 대한 상대 범위입니다. **Origin의 Z=0.1, 두 Bound의 Z=0**으로 두면 높이 0.1 m의 단면을 계산합니다. 세 Z 값을 모두 0.1로 맞추면 같은 의미가 아닙니다. Origin은 이미지의 왼쪽 아래 픽셀을 임의로 고르는 값이 아니라 **장애물 밖의 시작 위치**입니다. 원뿔 중심을 시작점으로 사용하지 마세요.

원뿔의 로컬 설정은 다음과 같습니다.

```usda
double height = 0.4
double radius = 0.15
double3 xformOp:translate = (0.3, 0, 0.1)
float3 xformOp:rotateXYZ = (90, 0, 0)
```

원뿔의 중심을 옮기고 X축으로 90° 회전해 눕혔습니다. 지도는 이 물체를 위에서 사진처럼 찍는 것이 아니라 지정한 높이에서 충돌 형상을 조사합니다. Viewport의 눈 아이콘에서 **Show By Type > Physics Mesh > All**을 켜면 PhysX 계산에 쓰이는 형상을 볼 수 있습니다.

`Use PhysX Collision Geometry`를 끄는 선택지도 있지만, 이때는 원본 USD 메시를 사용하는 RTX 경로로 바뀝니다. 충돌 근사와 원본 메시가 다르면 지도 경계도 달라질 수 있습니다. 이번 첫 계산에서는 옵션을 켠 상태로 유지해 샘플 높이와 격자 간격의 영향을 먼저 구분하세요.

### 실행 결과 확인하기

검은 영역이 원뿔 주변에 나타나는지, 빈 시작점 주변에 자유 공간이 있는지 확인하세요. 회색 unknown은 아직 판별하지 못한 공간이므로 흰색 free와 같은 뜻으로 읽지 않습니다.

Lower/Upper Bound는 최대 범위입니다. 영역 폭을 Cell Size로 나눈 값만으로 이미지 크기를 고정해 기대하지 마세요. 실제 생성된 이미지 크기와 표시된 좌표 정보를 함께 확인합니다. Coordinate Type을 ROS Occupancy Map Parameters File로 바꾸면 ROS용 정보를 읽을 수 있지만, 이 선택이 ROS 노드나 내비게이션을 실행하지는 않습니다.

## 2. 저장한 이미지로 Block World 만들기

1. 원본 장면을 남겨 둔 뒤 **File > New**로 새 장면을 만듭니다.
2. **Tools > Robotics > Block World Generator**를 엽니다.
3. **Load Image**로 방금 저장한 `occupancy.png`를 선택합니다.
4. **Cell Size=0.05 m**를 입력하고 **Generate Block World**를 누릅니다.
5. 검은 픽셀에 대응하는 블록과 충돌 형상이 생성되는지 확인하고, **File > Save As**로 `output/block_world.usd`에 저장합니다.

### 설정에서 볼 부분

지도 생성 때와 재구성 때의 Cell Size가 같아야 길이가 유지됩니다. 예를 들어 이미지에서 장애물이 6칸 너비라면, 0.05 m/칸으로 가져온 폭은 약 0.30 m입니다. 같은 이미지를 0.10 m/칸으로 가져오면 폭이 0.60 m로 커집니다.

이미지 회전은 방향 대응에 관여합니다. 크기는 맞는데 배치가 반대로 보이면 Cell Size를 바꾸지 말고, 저장할 때의 Rotate Image와 새 장면의 축을 비교하세요.

### 실행 결과 확인하기

원래 장면의 원뿔에는 기울어진 면과 높이 변화가 있습니다. 재구성 장면에서는 격자 경계에 맞춘 블록이 나타납니다. 흰 영역이 열려 있는지, 검은 영역의 외곽이 같은 크기와 방향을 갖는지 비교하세요. 회색 영역이 있다면 이를 자유 공간이라고 가정하지 말고 생성 결과를 따로 확인합니다.

## 3. 지도 변환에서 보존되는 정보 정리

```text
3D 충돌 형상
    → z=0.1 m에서 점유 여부 조사
    → 0.05 m 간격의 2D 격자
    → 이미지의 칸을 충돌 블록으로 변환
```

한 높이의 점유 여부로 바꾸는 순간 다른 높이의 모양은 빠집니다. 다시 3D 블록을 만들어도 그 정보가 되살아나지는 않습니다. 따라서 Block World는 지도 기반 주행 환경을 만드는 데 유용한 **격자 근사**로 이해하면 됩니다.

## 4. 간단한 확인 실험

원본 원뿔 장면에서 **Cell Size만 `0.05`에서 `0.025`로** 바꾸고 다시 계산하세요. 높이, bounds, 색상은 그대로 둡니다. 이전 PNG와 구분되는 이름으로 저장합니다.

- 한 칸의 길이가 절반이 되어 경계가 더 촘촘하게 표현되어야 합니다.
- 같은 물리 범위를 모두 표현한다면 가로·세로 칸 수는 각각 약 두 배, 전체 칸 수는 약 네 배가 됩니다.
- 실제 출력 크기와 계산 시간을 기록하세요. 최대 bounds와 실제 계산 범위가 같다는 가정은 하지 않습니다.

새 이미지를 Block World로 가져올 때도 `0.025`를 써야 합니다. 해상도를 높였다는 이유로 원래 장애물이 작아지는 것은 아닙니다.

## 실행할 때 막히면

- **보이는 원뿔이 지도에는 없음**: Collider 활성 여부와 Physics Mesh를 확인하세요. PhysX 모드는 표시용 외형만으로 장애물을 판별하지 않습니다.
- **지도가 비거나 계산이 이상함**: Origin이 빈 공간인지, Origin의 Z는 0.1이고 두 상대 Bound의 Z는 0인지 확인하세요.
- **수정 전 이미지가 계속 보임**: 형상·Cell Size 변경 후 CALCULATE를 다시 하고, 색·회전 변경 후 이미지 재생성 상태를 확인하세요.
- **Block World 크기가 다름**: PNG를 만들 때의 m/픽셀 값과 가져올 때의 Cell Size를 맞추세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Mapping](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/digital_twin/ext_isaacsim_asset_generator_occupancy_map.html)을 바탕으로 한 실습입니다. 로컬 USDA는 작은 충돌 장면을 제공하며 지도 계산, PNG 저장, 블록 생성은 GUI에서 수행합니다. 공식 문서의 RTX 원본 메시 경로는 PhysX 충돌 근사 경로와 다른 비교 대상입니다.

Origin과 상대 bounds를 구분해 지도 높이를 설정하세요. 실제 지도 생성·PNG 저장·Block World 재구성은 위 절차로 확인할 범위이며, `tutorial.json`의 검증 상태는 `not_run`입니다.
