# 32. t112 · USD에서 URDF를 내보낼 때 사라지는 것 이해하기

권장 학습 순서 **32** · 로봇 자산 가져오기와 제작 · 출처 ID `t112`

이 패키지는 Isaac Sim **5.1.0** URDF exporter backend로 같은 로봇을 **visual-only / visual+collision / collision-only** 세 번 내보낸다. 코드에서 만드는 작은 2-link 로봇은 외부 mesh 없이 독립적이며 질량·관성을 명시한다. 공식 Franka GUI 실습은 아래에 별도로 재현한다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.asset.exporter.urdf`가 필요하다. backend `nvidia.srl.from_usd.to_urdf.UsdToUrdf`는 해당 extension에 번들되어 있다. 다른 패키지의 URDF를 필요로 하지 않는다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/32_importers_export_urdf
"$ISAAC_SIM/python.sh" run.py
# GUI 없이 변환 (새 출력 폴더)
"$ISAAC_SIM/python.sh" run.py --headless --output output/headless
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 120회 한도를 사용한다. 기존 `--frames`는 `--steps` 없는 headless 실행의 한도로만 쓰며 GUI를 닫지 않는다.

`output/{visual,both,collision}/`에 `source.usda`, `robot.urdf` 및 필요 mesh가 생성된다. `counts.json`은 XML에서 실제로 센 link/joint/visual/collision 개수다. 개수만으로 geometry가 보존되었다고 결론 내리지 말고 각 파일을 다시 열어 본다.

## 세 가지 export 비교

1. `source.usda`에서 `/Robot/link/experiment_sphere`를 찾는다. 반지름 0.03 m 구가 링크 옆에 붙는다. 이는 원문의 Franka 손 위 구 실험을 작은 로봇으로 축소한 것이다.
2. `visual` 출력은 구에 CollisionAPI가 없고 보인다. URDF에서 visual geometry에는 포함되고 collider에는 포함되지 않아야 한다.
3. `both` 출력은 보이는 구에 CollisionAPI를 추가한다. visual과 collision 양쪽에 포함되는지 확인한다.
4. `collision` 출력은 CollisionAPI를 유지하고 visibility를 invisible로 바꾼다. 구는 collision에만 있어야 한다. 각 링크의 여러 shape가 한 mesh로 합쳐질 수 있으므로 XML element 수가 항상 shape 수와 같지는 않다.
5. Isaac Sim **File > Import**로 `robot.urdf`를 다시 가져오고 viewport **Show by type > Physics > Colliders > All**을 켠다. 원래 stage와 관절 연결, 구의 위치, 보이는 형상/충돌 형상을 비교한다.

## 공식 Franka native GUI 실습

1. Window > Extensions에서 USD to URDF exporter를 켠다. 5.1 자산 루트의 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 연다.
2. **File > Export to URDF**에서 새 output 폴더와 `franka.urdf`를 지정한다. `franka.urdf`와 `meshes/`를 확인한다.
3. `panda_hand` 우클릭 **Create > Mesh > Sphere**를 추가하고 scale X/Y/Z 모두 0.3으로 둔다. 같은 비율의 scaling을 유지한다. stage 원본을 저장할 필요는 없다.
4. 구를 그대로 export, **Properties > + Add > Physics > Colliders Preset** 적용 후 export, eye 아이콘으로 구를 숨긴 뒤 export한다. 매번 서로 다른 출력 경로를 사용한다.
5. 재import하거나 원문이 연결한 URDF viewer로 링크·joint 및 **Show Collision** 결과를 확인한다. viewer를 쓸 경우 이전 데이터를 지우고 다시 로드한다.

## 경로 옵션과 변환 API

`Mesh Folder Name`은 기본 `meshes`다. **Mesh Path Prefix**는 `file://` 절대 경로, `package://` ROS package 경로, `./` 상대 경로 중 선택한다. package 경로는 **Package Name**을 지정해야 하며 비우면 URDF 파일명이 사용된다. 파일과 mesh 폴더를 함께 옮겨야 한다. `Root Prim Path`로 큰 장면에서 로봇만 선택하고 바닥/배경을 export하지 않게 한다. **Visualize Collisions**는 숨겨진 collider도 visual로 포함하게 한다.

코드의 `UsdToUrdf(stage, root='/Robot')`는 USD의 transform/joint graph를 URDF tree로 변환하며 `save_to_file()`이 XML과 mesh를 작성한다. USD의 rigid body mass/inertia와 joint Body0/Body1, local frame이 변환 근거다. primitive sphere는 별도 OBJ 없이 URDF primitive로 표현될 수도 있다.

## URDF의 표현 한계

kinematic tree 구조가 필요하며 loop를 그대로 보존할 수 없다. joint는 revolute/prismatic/fixed, link는 Xform이어야 한다. body0은 parent, body1은 child로 맞추고 양쪽 joint 기준점의 위치/방향을 일치시킨다. sphere는 등방 scale, cylinder는 반지름 두 축 scale이 같아야 한다. geometry는 Cube/Sphere/Cylinder/Mesh 및 tree leaf, sensor는 Camera/IsaacImuSensor가 대상이다. USD의 모든 기능을 1:1로 옮길 수 없으므로 변환 후 이름과 구조도 검토한다.

변수 하나 실험은 sphere visibility만 바꾸어 재export하는 것이다. exporter 오류가 나면 tree와 local joint frame부터 확인한다. mesh가 없으면 경로 prefix와 폴더 이동을 확인한다. 문법/CLI 및 설치 API는 확인했지만 exporter runtime과 재import 화면은 미검증이다.

## 출처

[Isaac Sim 5.1 Export URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/export_urdf.html), [collision 변환](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/export_urdf.html#collision-objects), [표현 제약](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/export_urdf.html#limitations). backend 호출은 설치된 5.1 `isaacsim.asset.exporter.urdf/exporter.py`와 대조했다.
