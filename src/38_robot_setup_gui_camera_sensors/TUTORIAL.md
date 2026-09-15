# 38. 로봇에 붙인 카메라는 누구를 따라 움직일까요?

## 이번에 배우는 것

**움직이는 몸체 아래에 카메라를 장착하고, 외부 시점과 로봇에 고정된 시점을 나란히 비교합니다.**

로봇 근처에 카메라를 놓는 것과 로봇에 카메라를 붙이는 것은 다릅니다. 로봇이 움직여도 장착 위치를 유지하려면 카메라가 실제 움직이는 강체의 변환을 따라야 합니다. 이번에는 장착 자세를 저장할 Xform을 따로 두어, 카메라의 시야와 장착 위치도 구분합니다.

| 요소 | 파일 또는 Stage 위치 | 역할 |
|---|---|---|
| 출발 로봇 | `run.py`가 여는 `mock_robot_rigged.usd` | 몸체와 바퀴가 연결된 공식 에셋 |
| 장착 스크립트 | `attach_camera.py` | 실제 body 강체를 찾아 카메라 추가 |
| 장착 기준 | `body/camera_mount` | 몸체에 대한 위치와 회전 |
| 카메라 | `camera_mount/car_camera` | 초점거리·시야·클리핑 설정 |

이 실습의 출력은 **USD 카메라와 Viewport 영상**입니다. 이미지 파일 저장이나 ROS 토픽 발행은 포함하지 않습니다.

## 1. 로봇 장면을 열고 카메라 붙이기

Isaac Sim 5.1.0과 RTX GPU, GUI가 필요합니다. 공식 `/Isaac/Samples/Rigging/MockRobot/mock_robot_rigged.usd`에 접근할 수 있어야 합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/38_robot_setup_gui_camera_sensors/run.py \
  --output src/38_robot_setup_gui_camera_sensors/output/first
```

1. Stage에서 몸체와 바퀴 관절을 찾고 잠깐 Play하여 로봇의 운동을 확인한 뒤 Stop합니다.
2. **Window > Script Editor**를 엽니다.
3. 이 폴더의 **`attach_camera.py` 전체**를 붙여 넣고 실행합니다. 이미 열린 앱 안에 `run.py`를 붙여 넣지 마세요.
4. 출력 영역의 `Camera attached:` 경로를 Stage에서 찾습니다.

실행기만 열었을 때 새 `car_camera`가 없는 것은 정상입니다. 카메라를 추가하는 작업은 Script Editor 실행에서 이루어집니다. 창은 기본적으로 계속 열려 있으므로 아래 관찰까지 진행한 뒤 Ctrl+S로 저장하고 닫으세요.

### 코드에서 볼 부분

스크립트는 이름만으로 부모를 고르지 않습니다.

```python
bodies = [p for p in stage.Traverse()
          if p.GetName() == "body" and p.HasAPI(UsdPhysics.RigidBodyAPI)]
```

`body`라는 이름과 RigidBodyAPI를 **둘 다** 확인합니다. 부모 Xform이 배치용으로 존재하더라도 물리로 움직이는 자식 geometry는 별도 prim일 수 있기 때문입니다. 후보가 정확히 하나가 아니면 스크립트가 중단됩니다.

그 강체 아래에 다음 장착 자세를 작성합니다.

```python
mount.AddTranslateOp().Set(Gf.Vec3d(-6, 0, 2.2))
mount.AddRotateXYZOp().Set(Gf.Vec3f(0, -80, -90))
camera = UsdGeom.Camera.Define(stage, mount_path + "/car_camera")
```

Translate와 Rotate는 몸체 기준의 **local 값**입니다. 이 수치는 공식 mock robot의 크기와 좌표계에 맞춘 장착 예이며, 다른 로봇에 그대로 적용할 기본 위치는 아닙니다. 카메라 자체에는 추가 변환을 넣지 않아 local transform이 identity, 즉 추가 이동·회전이 없는 상태가 됩니다.

### 실행 결과 확인하기

Stage는 다음 구조가 되어야 합니다.

```text
실제 body 강체
└─ camera_mount       ← 장착 위치와 방향
   └─ car_camera      ← 카메라의 투영 속성
```

`initial_inventory.json`은 카메라를 만들기 전에 저장한 강체·관절 목록입니다. 카메라 추가 여부는 Script Editor 출력과 Stage로 확인하세요. 저장 후 카메라가 남는지는 `output/first/stage.usda`를 다시 열어 확인할 수 있습니다.

## 2. 외부 화면과 카메라 화면 비교하기

1. **Window > Viewports > Viewport 2**로 두 번째 Viewport를 엽니다.
2. 한쪽은 Perspective로 유지하고, 다른 쪽의 카메라 메뉴에서 새 `car_camera`를 선택합니다.
3. **Tools > Robotics > Camera Inspector**를 열어 Refresh하고 같은 카메라를 선택합니다.
4. 필요하면 눈 모양 메뉴의 **Show By Type > Cameras**로 카메라 윤곽을 표시합니다.
5. Play하여 로봇이 움직일 때 두 화면을 함께 관찰합니다.

### 설정에서 볼 부분

카메라가 바라보는 방향은 USD 카메라의 local **-Z**, 위쪽은 **+Y**입니다. 로봇의 전방 축을 그대로 카메라 전방으로 생각하면 영상이 옆이나 뒤를 향할 수 있습니다. 이번 장착 회전은 이 축 차이까지 포함합니다.

스크립트가 설정하는 투영 값은 다음과 같습니다.

| Camera 속성 | 값 | 읽는 방법 |
|---|---:|---|
| Focal Length | 24 | 같은 aperture에서 커질수록 시야가 좁아짐 |
| Horizontal Aperture | 20.955 | 가로 투영 크기 |
| Vertical Aperture | 15.2908 | 세로 투영 크기 |
| Clipping Range | 0.01, 10000 | 가까운 쪽과 먼 쪽의 표시 경계 |

표의 Focal Length와 Aperture는 `UsdGeom.Camera`에 작성한 원시 속성값입니다. 이 속성의 길이 단위는 **Stage 길이 단위의 1/10**, Clipping Range는 **Stage 길이 단위**입니다. 예를 들어 `meters_per_unit=0.01`인 cm Stage에서 focalLength=24는 24 mm에 해당합니다. 다른 단위의 Stage에서도 무조건 24 mm라고 읽지 마세요. [OpenUSD 카메라 단위](https://openusd.org/release/api/class_usd_geom_camera.html)에서 정의를 확인할 수 있습니다.

초점거리와 aperture는 함께 시야각을 정합니다. 장착 위치를 옮기지 않아도 렌즈 설정만으로 화면에 담기는 범위가 달라집니다. Clipping Range 밖의 물체는 화면에서 잘릴 수 있으므로 영상이 비어 있을 때 장착 방향과 함께 조사하세요.

### 실행 결과 확인하기

Perspective에서는 로봇이 장면을 이동하고, 카메라 화면에서는 몸체와의 상대 장착 관계가 유지되어야 합니다. 로봇이 회전하면 카메라가 바라보는 세계의 방향도 같이 돌아갑니다.

카메라 Viewport를 마우스로 탐색하면 카메라 자체의 transform이 바뀔 수 있습니다. 장착 기준을 복구하려면 `camera_mount`를 유지하고 `car_camera`의 추가 이동·회전을 초기화하세요. 이것이 장착용 Xform을 분리한 이유입니다.

GUI에서 직접 만드는 경우에는 **Create > Camera** 또는 원하는 Perspective에서 **Camera > Create from View**를 사용합니다. 새 카메라를 실제 `body` 강체 아래로 옮긴 뒤 카메라 자체의 Translate=(-6, 0, 2.2), Rotate=(0, -80, -90), Scale=(1, 1, 1)을 입력하면 원문의 직접 장착 방식과 비교할 수 있습니다. 이 방식은 mount를 별도로 만들지 않으므로 코드 방식의 카메라와 구분해 이름을 정하고, 두 Viewport에서 한 결과씩 관찰하세요.

## 3. 몸체·장착부·카메라의 관계 정리

```text
몸체의 world 자세
    → 장착부의 body 기준 자세
    → 카메라의 추가 local 자세
    → 최종 카메라 위치와 방향
```

**부모 관계는 카메라가 무엇을 따라갈지 정하고, 렌즈 속성은 그 위치에서 얼마나 넓게 볼지 정합니다.** 로봇의 운동, 센서 장착 보정, 렌즈 조절을 각각 다른 위치에서 다루면 영상이 예상과 다를 때 원인을 찾기 쉽습니다.

## 4. 간단한 확인 실험

로봇을 Pause하여 같은 장면을 유지하고 `car_camera`의 **Focal Length만 24에서 48로** 바꿔보세요. Aperture와 `camera_mount`의 transform은 그대로 둡니다.

카메라 화면에 담기는 주변 범위가 좁아지고 중앙 물체가 더 크게 보이는지 확인하세요. Perspective에서 본 카메라 장착 위치는 바뀌지 않아야 합니다. 이 차이로 카메라를 가까이 옮기는 것과 렌즈를 바꾸는 것을 구분할 수 있습니다.

## 실행할 때 막히면

- **`camera_mount exists`가 나옵니다**: 이전 장착이 남아 있습니다. 기존 mount를 먼저 확인하고, 다시 만들 목적일 때만 해당 mount를 제거한 뒤 실행하세요.
- **body 후보가 0개 또는 여러 개입니다**: 다른 에셋을 열었거나 장면에 로봇이 여럿 있습니다. 기본 rigged mock robot 장면에서 실제 강체 경로를 확인하세요.
- **카메라가 로봇을 따라오지 않습니다**: 단순 배치용 부모가 아니라 RigidBodyAPI가 있는 body 아래에 장착되었는지 확인하세요.
- **화면이 검거나 방향이 이상합니다**: Viewport의 활성 카메라, mount 회전, 카메라 local transform, clipping 순서로 확인하세요.
- **출력 폴더 오류 또는 자동 종료가 생깁니다**: 새 `--output` 경로를 사용하세요. GUI 실습은 `--steps`를 생략합니다. Headless에는 양수 `--steps`가 필요하며 카메라 추가와 화면 관찰을 대신하지 않습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Tutorial 4: Add Camera and Sensors to a Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_camera_sensors.html)에 대응합니다. 원문의 카메라 장착을 로컬 `attach_camera.py`와 두 Viewport 비교로 익힙니다.

장착용 Xform과 중복 생성 검사는 로컬 실습에서 마련한 구성입니다. `tutorial.json`의 검증 상태는 `not_run`이며 카메라 영상 방향과 실제 추종은 GUI에서 확인할 항목입니다.
