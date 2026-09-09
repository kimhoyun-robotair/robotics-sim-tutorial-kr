# 19. URDF를 가져오기 전에 질량과 관성부터 확인하다

## 목표와 준비

로봇의 겉모양과 물리 모델이 별개라는 점을 이해하고, 제공한 단일 관절 URDF를 USD로 변환한다. 18단계까지의 물리 장면 실습을 마친 상태에서 진행한다. 이번 단계는 변환 결과를 **Stop 상태에서** 살펴보는 실습이다. 바닥 고정과 제어는 20~22단계에서 이어서 구성한다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$TUTORIAL_ROOT"
ls assets/one_joint_arm.urdf
mkdir -p artifacts/urdf-gui
```

`link`는 함께 움직이는 몸체, `joint`는 몸체 사이의 움직임을 제한하는 연결이다. `visual`은 화면에 보이는 모양이고 `collision`은 접촉을 계산하는 모양이다. `inertial`은 질량과 무게중심, 회전하기 어려운 정도를 나타내는 관성을 담는다. 화면에 정상적으로 보이는 로봇도 이 세 부분이 서로 어긋나면 Play 직후 튀거나 쓰러질 수 있다.

## 1. 먼저 파일 속 길이와 질량을 읽다

제공 파일의 받침대는 한 변이 0.3 m인 상자이고 질량은 4 kg이다. 링크 원점은 바닥에 두고 상자 중심과 무게중심은 모두 높이 0.15 m에 둔다.

```xml
<link name="base_link">
  <inertial>
    <origin xyz="0 0 0.15" rpy="0 0 0"/>
    <mass value="4"/>
    <inertia ixx="0.06" ixy="0" ixz="0"
             iyy="0.06" iyz="0" izz="0.06"/>
  </inertial>
  <visual>
    <origin xyz="0 0 0.15"/>
    <geometry><box size="0.3 0.3 0.3"/></geometry>
  </visual>
  <collision>
    <origin xyz="0 0 0.15"/>
    <geometry><box size="0.3 0.3 0.3"/></geometry>
  </collision>
</link>
```

관성의 단위는 kg·m²이다. 균일한 직육면체의 중심 관성은 다음 식으로 계산한다. 길이만 m에서 mm로 바꾸면 물리량이 크게 달라지므로 숫자를 그대로 옮기지 않는다.

```python
# 일반 Python에서 실행 가능한 계산 예제이다.
mass = 4.0
x, y, z = 0.3, 0.3, 0.3
ixx = mass * (y*y + z*z) / 12
ixy = 0.0  # 상자의 주축과 inertial 좌표축을 맞춘 경우이다.
print(ixx, ixy)  # 0.06, 0.0
```

질량이 양수인지만 확인해서는 부족하다. 관성 행렬은 대칭이고 양의 정부호여야 하며, 주관성 모멘트는 삼각 부등식을 만족해야 한다. 다음 코드는 제공 파일의 모든 링크를 검사한다.

```bash
python3 - <<'PY'
import xml.etree.ElementTree as ET
import numpy as np
root = ET.parse('assets/one_joint_arm.urdf').getroot()
for link in root.findall('link'):
    inertial = link.find('inertial')
    mass = float(inertial.find('mass').get('value'))
    a = inertial.find('inertia').attrib
    v = {key: float(value) for key, value in a.items()}
    matrix = np.array([[v['ixx'],v['ixy'],v['ixz']],
                       [v['ixy'],v['iyy'],v['iyz']],
                       [v['ixz'],v['iyz'],v['izz']]])
    moments = np.linalg.eigvalsh(matrix)
    assert mass > 0 and np.all(moments > 0)
    assert moments[-1] <= moments[0] + moments[1] + 1e-8
    print(link.get('name'), mass, moments)
PY
```

## 2. GUI로 가져오다

1. Isaac Sim에서 File → New를 선택하고 Play 버튼이 꺼져 있는지 확인한다.
2. File → Import를 누르고 `assets/one_joint_arm.urdf`를 선택한다.
3. USD Output을 `artifacts/urdf-gui`의 절대 경로로 지정한다. 파일 선택 창에 `$TUTORIAL_ROOT` 문자열을 그대로 넣지 않고 실제 경로를 입력한다.
4. URDF에 collision이 있으므로 **Collision From Visuals를 끈다.** 이 실습에서는 복잡한 메쉬를 쪼개는 작업이 필요하지 않다.
5. Import를 실행하고 Output Log에서 실패한 변환이나 누락된 파일이 없는지 확인한다.
6. 변환한 로봇의 최상위 USD를 열고 Stage에서 `base_link`, `arm_link`, `shoulder`를 찾는다. 선택 후 F를 눌러 화면 가운데로 이동한다.
7. Property에서 링크에 Rigid Body가 있고, collision에 Collider가 있으며, 관절의 연결 대상이 두 링크를 가리키는지 살펴본다. 출력 폴더 안에는 물리·시각 자료를 나눈 보조 USD도 생길 수 있으므로 파일 하나만 따로 옮기지 않는다.

6.0.1의 Importer는 입력과 출력 경로를 `URDFImporterConfig`에 담는 Python API를 제공한다. 예전 자료의 `URDFParseAndImportFile` 호출을 새 실습의 출발점으로 사용하지 않는다.

## 3. 동일한 변환을 Python으로 구성하다

아래는 Isaac Sim의 Window → Script Editor에서 실행하는 예제이다. 경로 두 곳을 실제 절대 경로로 바꾼다.

```python
from isaacsim.asset.importer.urdf import URDFImporter, URDFImporterConfig

config = URDFImporterConfig(
    urdf_path="/home/YOUR_NAME/robotics-sim-tutorial-kr/assets/one_joint_arm.urdf",
    usd_path="/home/YOUR_NAME/robotics-sim-tutorial-kr/artifacts/urdf-python",
    collision_from_visuals=False,
    merge_mesh=False,
    allow_self_collision=False,
)
output_path = URDFImporter(config).import_urdf()
print("변환 결과:", output_path)
```

완결 실행 파일은 [03_robot_stability.py](../../examples/03_robot_stability.py)이다. 이 파일은 변환 뒤에 바닥 고정, 구동기 설정, 수치 검사까지 수행하므로 22단계에서 실행한다.

## 기대 결과와 문제 진단

주황색 막대 하나가 회색 받침대 위에 놓인 형태로 보인다. 회전축은 Z축이며 팔은 수평으로 회전한다. 이 단계에서 아직 바닥 고정을 하지 않았으므로 GUI에서 즉시 Play하여 제어 성능을 판정하지 않는다.

| 증상 | 확인할 내용 |
| --- | --- |
| 300 m 크기로 보이다 | URDF 길이가 m인지, Stage의 metersPerUnit이 1인지 확인한다. |
| 모양이 있지만 충돌하지 않다 | visual과 collision을 각각 펼쳐 Collider 적용 여부를 확인한다. |
| Import 창을 찾지 못하다 | Window → Extensions에서 `isaacsim.asset.importer.urdf`와 해당 UI 확장을 확인한다. |
| 회전축 주변에서 두 물체가 겹치다 | joint origin과 collision origin을 따로 확인한다. |

## 확인 과제

팔의 질량을 1 kg에서 2 kg으로 바꾸려면 관성도 어떻게 바꾸어야 하는지 계산한다. 실제 기준 파일은 유지하고 사본에서 실험한다. 팔의 길이만 두 배로 바꾸는 경우에는 모든 관성을 단순히 두 배로 만들면 안 되는 이유도 설명한다.

## 공식 참고 자료

- [6.0.1 URDF Importer: GUI와 출력 구조](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [6.0.1 URDF Importer Python API](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/extensions/isaacsim.asset.importer.urdf/docs/index.html)
- [6.0.1 로봇 설정 문제 해결](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/robot_setup/troubleshooting.html)

[다음: Articulation과 Drive](20-articulation-drives.md)
