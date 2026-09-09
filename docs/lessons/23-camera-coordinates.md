# 23. 카메라 좌표계와 조명을 먼저 맞추다

## 목표와 준비

카메라를 만들기 전에 어디에서 어느 방향을 보는지 정하고, 센서 영상과 Viewport 화면이 다를 수 있다는 점을 확인한다. 22단계 로봇과 분리한 작은 장면에서 시작한다. 움직이는 로봇과 센서를 동시에 추가하면 검은 화면의 원인이 카메라인지 로봇의 전도인지 구별하기 어렵다.

6.0.1에서 카메라의 새 Python API는 `isaacsim.sensors.experimental.rtx`에 있다. `RtxCamera`가 카메라 Prim을 구성하고 `CameraSensor`가 렌더링 결과를 읽는다. 이름이 비슷한 예전 `isaacsim.sensors.camera.Camera`와 인자 이름을 섞지 않는다.

## 1. 세 좌표계를 표로 정리하다

| 좌표계 | 앞 방향 | 위 방향 | 주로 사용하는 곳 |
| --- | --- | --- | --- |
| USD 카메라 | -Z | +Y | 카메라 Prim의 실제 방향 |
| ROS 카메라 optical frame | +Z | -Y | 이미지 투영과 CameraInfo |
| 일반 로봇 몸체 | +X | +Z | base_link와 이동 방향 |

카메라가 로봇 앞쪽에 달려 있어도 회전이 잘못되어 있으면 하늘이나 로봇 내부를 본다. 좌표계를 바꿀 때 위치 벡터만 옮겨서는 안 되고 회전도 적용해야 한다. Quaternion은 이 Python API에서 `[w, x, y, z]` 순서이다. ROS 메시지 필드는 `x, y, z, w` 순서라는 점을 구분한다.

이번 실습은 일부러 가장 단순한 배치를 사용한다. 카메라를 `(0, 0, 3)`에 놓고 회전을 identity로 두면 -Z 방향, 즉 바닥을 내려다본다.

```python
from isaacsim.sensors.experimental.rtx import RtxCamera

camera = RtxCamera(
    "/World/Camera",
    tick_rate=30.0,
    translations=[[0.0, 0.0, 3.0]],
    orientations=[[1.0, 0.0, 0.0, 0.0]],
)
```

카메라 Prim만 만들었다고 바로 NumPy 이미지가 생기지는 않는다. Render Product와 Annotator를 관리하는 `CameraSensor`를 다음 단계에서 연결한다.

## 2. 광학 설정과 실제 화면을 구분하다

Clipping Range는 보이는 거리의 앞·뒤 한계이다. 물체가 카메라에 너무 붙어 있거나 far clip 바깥에 있으면 화면에서 사라질 수 있다. 제공 예제는 0.05~20 m를 사용하고 물체를 약 2.4~3 m 앞에 둔다.

```python
from pxr import Gf, UsdGeom

usd_camera = UsdGeom.Camera(stage.GetPrimAtPath("/World/Camera"))
usd_camera.CreateClippingRangeAttr(Gf.Vec2f(0.05, 20.0))
usd_camera.CreateFocalLengthAttr(24.0)
usd_camera.CreateHorizontalApertureAttr(20.955)
usd_camera.CreateVerticalApertureAttr(15.71625)
```

이 값들은 새 예제의 USD 카메라 속성을 직접 설정한다. 숫자의 의미를 모른 채 실제 카메라의 초점거리와 센서 폭을 혼합하지 않는다. 실제 장치와 맞추는 작업에서는 광학 단위와 내부 파라미터까지 따로 검증해야 한다.

## 3. 조명이 있는 장면을 구성하다

센서 RGB는 실제 렌더링 결과이다. Viewport의 작업용 조명으로 물체가 보이더라도 센서 장면에 광원이 없으면 어두울 수 있다. 완결 예제는 씬에 DomeLight를 만든다.

```python
from pxr import UsdLux

light = UsdLux.DomeLight.Define(stage, "/World/Light")
light.CreateIntensityAttr(1000.0)
```

재질 문제를 줄이기 위해 외부 텍스처 대신 회색 바닥과 빨강·파랑 상자의 displayColor를 사용한다. 카메라 앞에 물체를 놓고도 회색 한 색만 보인다면 카메라 방향, 물체 위치, 조명 순서로 확인한다.

## 4. 저장된 카메라 장면을 GUI에서 확인하다

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/04_camera_check.py \
  --output-dir artifacts/camera-basics
```

1. 실행이 끝나면 GUI에서 `artifacts/camera-basics/camera_scene.usda`를 연다.
2. Stage의 `/World/Camera`를 선택하고 Property에서 높이와 clipping range를 확인한다.
3. Viewport의 카메라 선택 메뉴에서 `/World/Camera`를 선택한다. 기본 Perspective 카메라와 구분한다.
4. 바닥과 빨강·파랑 상자를 확인한다. 현재 Viewport 방향을 마우스로 바꾼다면 센서 카메라 자체를 이동시키는지 주의한다.
5. `rgb_preview.png`와 화면 구성을 비교한다. 렌더러의 후처리 때문에 화면과 저장 영상의 모든 픽셀이 같을 필요는 없다.

## 기대 결과와 진단

`rgb_preview.png`에는 두 색의 상자와 바닥이 보인다. 카메라는 정지해 있으므로 같은 장면에서 깊이가 크게 흔들리지 않아야 한다. 바닥만 보이면 센서가 정상이라는 결론을 내리기 전에 물체가 FOV 안에 있는지 확인한다.

| 증상 | 확인 순서 |
| --- | --- |
| 완전히 검은 영상 | 장면 광원 → camera Prim 경로 → clipping → Render Product |
| RGB는 보이지만 물체가 거꾸로 보이다 | USD 카메라 축과 ROS optical frame 회전을 확인하다 |
| 가로세로가 뒤바뀌다 | 6.0.1 `CameraSensor`의 `(height, width)` 순서를 확인하다 |
| GUI는 보이는데 headless 영상은 없다 | headless에서도 렌더링 갱신을 진행하는지 확인하다 |

## 확인 과제와 실행 파일

[04_camera_check.py](../../examples/04_camera_check.py)의 카메라 높이를 사본에서 3 m에서 4 m로 바꾸면 깊이 검사 기준도 수정해야 하는 이유를 설명한다. 24단계에서는 변경 전 기본 장면의 검사를 먼저 완료한다.

## 공식 참고 자료

- [6.0.1 Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/sensors/isaacsim_sensors_camera.html)
- [6.0.1 카메라 API 이전 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/migration_guides/isaac_sim_6_0/sensors_camera_to_experimental_rtx.html)
- [6.0.1 좌표계와 단위 규칙](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/reference_material/reference_conventions.html)

[이전](22-project-joint-rig.md) · [다음](24-rgbd-validation.md)
