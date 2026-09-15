# 62. 카메라가 본 상자는 이미지의 어느 픽셀에 있나요?

## 이번에 배우는 것

**세 상자를 촬영한 이미지와 월드 좌표의 투영 결과를 비교하며, 카메라 자세·내부 보정·렌즈 왜곡의 역할을 구별합니다.**

이미지에서 물체를 찾으려면 장면 속 위치와 이미지 속 위치를 연결해야 합니다. 월드 좌표가 미터로 표현된다면 이미지 좌표는 픽셀로 표현됩니다. 이번에는 움직이지 않는 카메라와 상자를 사용해 이 연결을 차근차근 확인합니다.

| 구성 | 기본 설정 | 확인할 데이터 |
|---|---|---|
| 카메라 | 높이 5 m에서 아래를 바라봄 | `/World/Camera`의 자세 |
| 세 상자 | x가 -1, 0, 1 m, 윗면 높이 0.9 m | 상자 윗면 중심의 투영 좌표 |
| 영상 | 640×480, 30 Hz | `rgba.png`, `camera.npz` |
| 내부 보정 | fx=fy=320, cx=320, cy=240 픽셀 | `measurements.json`의 `intrinsic_matrix` |
| 기본 렌즈 | 왜곡 계수가 0인 OpenCV pinhole | 이미지와 이상적 투영의 대응 |

물리와 렌더링은 60 Hz로 진행하지만 카메라는 30 Hz로 설정합니다. 따라서 물리 한 단계마다 독립적인 새 이미지가 생긴다고 가정하지 않습니다.

## 1. 세 상자를 촬영하고 이미지 열기

Isaac Sim 5.1과 지원 NVIDIA GPU가 있는 환경에서, 저장소 루트 기준으로 실행하세요.

```bash
~/isaacsim/python.sh src/62_sensors_sensors_camera/run.py --steps 240 --output src/62_sensors_sensors_camera/output/base
```

240단계 후 마지막 카메라 프레임을 저장하고 앱이 종료됩니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 출력 폴더는 아직 없는 경로여야 합니다. `--output`을 생략하면 튜토리얼 폴더의 `output/날짜_시간/` 아래에 만듭니다.

GUI에서 카메라를 계속 관찰하려면 `--steps 240`을 빼세요. 처음 240단계 후 파일을 한 번 저장하고 창은 직접 닫을 때까지 유지합니다. 창 없이 촬영하려면 `--headless`를 추가합니다. Headless에서도 영상 렌더링은 수행합니다.

### 실행 결과 확인하기

먼저 `output/base/rgba.png`를 엽니다. 세 상자와 바닥이 보이는지 확인하세요. 같은 폴더의 다른 파일은 다음 정보를 담습니다.

| 결과 | 읽는 방법 |
|---|---|
| `camera.npz`의 `rgba` | `[높이, 너비, 채널]`, 기본 `[480,640,4]` 배열 |
| `projected_points` | 상자 윗면 중심 세 점의 `(u,v)` 픽셀 좌표 |
| `motion_vectors` | 마지막 프레임의 움직임 정보; 이 정지 장면에서는 큰 움직임을 기대하지 않음 |
| `measurements.json` | 렌즈 모드, 배열 크기, 투영 좌표, 내부 보정 행렬 |
| `scene.usda` | 촬영에 사용한 장면 설정 |

기본 렌즈의 투영 좌표는 대략 `(320,318)`, `(320,240)`, `(320,162)`입니다. 이미지 배열에서는 **`rgba[v, u]`** 순서로 픽셀을 찾습니다. 첫 좌표의 상자는 이미지 아래쪽, 마지막 좌표의 상자는 위쪽에 놓입니다. 월드의 x 방향이 이미지에서도 가로일 것이라고 생각하면 이 결과가 뒤바뀐 것처럼 보일 수 있습니다.

## 2. 카메라 설정에서 픽셀 좌표까지 따라가기

### 코드에서 볼 부분

```python
camera = Camera(
    '/World/Camera', position=np.array([0., 0., 5.]),
    orientation=euler_angles_to_quats(np.array([0.,90.,0.]), degrees=True),
    resolution=(640,480), frequency=30,
)
world.reset()
camera.initialize()
camera.add_motion_vectors_to_frame()
```

Camera prim은 렌즈와 자세를 정의합니다. `initialize()`는 그 카메라로 이미지를 만들 render product와 기본 영상 읽기를 준비합니다. `add_motion_vectors_to_frame()`은 추가 출력 종류를 요청합니다. 카메라를 장면에 배치하는 일과 그 영상을 데이터로 받는 일이 여기서 연결됩니다.

코드의 `set_focal_length(.018)`과 `set_horizontal_aperture(.036)`은 이 미터 단위 장면에서 각각 초점거리 18 mm와 센서 너비 36 mm를 설정합니다. `set_lens_aperture(0)`은 깊이에 따른 초점 흐림을 끄므로, 이 실험에서는 흐릿함보다 렌즈 왜곡과 픽셀 위치에 집중할 수 있습니다.

이 숫자는 Camera wrapper의 입력 단위입니다. Raw USD의 focalLength·aperture에는 1/10 stage unit 관례가 적용되므로 Property의 원시 숫자를 wrapper에 그대로 옮기지 마세요. 해상도 비율 640:480과 aperture 비율 36:27도 같아야 정사각형 픽셀의 비율이 유지됩니다.

기본 렌즈는 다음과 같이 명시합니다.

```python
camera.set_opencv_pinhole_properties(
    cx=320, cy=240, fx=320, fy=320, pinhole=[0.0]*12
)
```

`fx`, `fy`는 카메라 축에서 벗어난 점이 이미지에서 얼마나 멀어지는지를 정하는 픽셀 단위 초점 값입니다. `cx`, `cy`는 광학 중심이 놓이는 픽셀입니다. 왜곡 계수가 모두 0이므로 먼저 이상적인 pinhole 관계를 확인할 수 있습니다.

코드는 알려진 내부 보정 행렬 `K`와 `get_view_matrix_ros()`를 곱해 월드 점을 투영합니다. 의미를 풀면 다음과 같습니다.

```text
월드 점
    → view matrix로 카메라 기준 X, Y, Z 계산
    → u = fx × X/Z + cx
    → v = fy × Y/Z + cy
```

거리가 두 배인 물체는 같은 옆 방향 간격을 가져도 이미지에서는 중심에 더 가깝게 보입니다. 위 식의 `X/Z`, `Y/Z`가 그 원근 관계를 표현합니다. 이 파일은 Camera wrapper의 투영 편의 함수 대신 설정한 `K`와 공개 view matrix를 직접 사용합니다.

### 렌즈 모드에서 볼 부분

`--lens pinhole`은 왜곡 계수를 넣고, `--lens fisheye`는 fisheye 모델을 사용합니다. 두 모드에서도 카메라와 상자 위치는 유지됩니다. 다만 저장 좌표의 의미는 다음처럼 구분해야 합니다.

| 렌즈 모드 | 렌더링 | 저장된 `projected_points` |
|---|---|---|
| `none` | 왜곡 없는 pinhole | 실제 영상과 대조할 이상적 좌표 |
| `pinhole` | 왜곡 있는 pinhole | 왜곡을 적용하기 전의 이상적 좌표 |
| `fisheye` | fisheye | 계산을 생략한 빈 배열 |

왜곡 pinhole 이미지에서 이상적 좌표가 정확히 상자 중심을 가리키지 않는 것은 두 계산에 적용한 렌즈 모델이 다르기 때문입니다.

### Camera Inspector와 센서 rig 살펴보기

1. 1절을 새 출력 경로에서 `--steps` 없이 실행하고 **Tools > Sensors > Camera Inspector**를 여세요.
2. **Refresh** 후 `/World/Camera`를 선택하고 **Create Viewport**를 누릅니다. 센서 시점에서 본 상자 배치와 저장 PNG를 비교하세요.
3. **Camera State**에서 위치·회전을 확인합니다. 카메라 자세를 바꾸면 영상 속 위치도 바뀌지만 이미 저장한 PNG는 갱신되지 않습니다.
4. 센서 여러 개를 묶은 rig는 별도 새 stage에서 5.1 Assets의 `Isaac/Sensors/Intel/RealSense/rsd455.usd`를 reference해 살펴보세요. RSD455 아래의 left/right/color와 `Camera_Pseudo_Depth`를 비교하면 한 rig에도 서로 다른 카메라 기준점이 있다는 것을 볼 수 있습니다. 이 자산은 기본 상자 실습에 필요하지 않습니다.

`Camera_Pseudo_Depth`는 깊이를 읽기 위한 편의 카메라입니다. 실제 RealSense 펌웨어가 좌우 영상으로 깊이를 계산하는 알고리즘을 재현한 결과와 구분하세요.

### RGB가 만들어지기 전의 데이터 비교하기

영상 처리 단계까지 보려면 설치된 별도 예제를 저장소 루트에서 실행합니다.

```bash
~/isaacsim/python.sh ~/isaacsim/standalone_examples/api/isaacsim.sensors.camera/camera_pre_isp_pipeline.py \
  --draw-output --output-dir src/62_sensors_sensors_camera/output/pre-isp
```

이 예제는 headless로 짧게 렌더링한 뒤 종료합니다. 새 출력 폴더에서 `hdr_input.png`, `raw_sensor_output.png`, `isp_output.png`를 비교하세요. HDR은 렌더링 입력, raw는 CFA 색 배열로 부호화한 센서 데이터, ISP 출력은 영상 처리 뒤 RGB입니다. raw의 밝기를 일반 RGB 픽셀과 바로 비교하면 안 되는 이유를 확인하는 단계입니다. 폴더에는 원시 `.bin`도 저장되며 로컬 `camera.npz`와는 별도 결과입니다. [공식 카메라 처리·Inspector 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html#exposing-the-pre-isp-camera-pipeline)을 참고하세요.

## 3. 자세·내부 보정·왜곡의 관계 정리

**카메라 자세는 어느 방향에서 보는지, 내부 보정은 그 방향을 몇 번째 픽셀로 옮기는지, 왜곡은 이상적인 픽셀 배치를 어떻게 변형하는지 정합니다.**

이 실습에서는 세 요소를 구분하기 위해 장면을 정지시켰습니다. 이미지와 점을 대조할 때는 먼저 기본 렌즈와 `(u,v)` 순서를 확인한 뒤 왜곡 모델을 살펴보세요. 조명과 렌더링 때문에 PNG 색은 소스의 색 배열과 정확히 같은 정수값이 아닐 수 있으므로 상자의 영역과 상대적인 색을 확인합니다.

## 4. 간단한 확인 실험

렌즈만 왜곡 pinhole로 바꿔 촬영하세요.

```bash
~/isaacsim/python.sh src/62_sensors_sensors_camera/run.py --steps 240 --lens pinhole --output src/62_sensors_sensors_camera/output/pinhole
```

기본 PNG와 같은 위치의 상자 가장자리, 중심에서 먼 부분의 형태를 비교해 보세요. `measurements.json`의 이상적 투영 좌표는 같아도 이미지는 달라질 수 있습니다. **같은 카메라 자세와 같은 K만으로 왜곡까지 설명할 수 있는지**가 이번 비교의 핵심입니다.

## 실행할 때 막히면

- **`Camera returned no image`**: 새 출력 경로에서 `--steps 480`으로 준비 시간을 늘리고 렌더러 로그를 확인하세요. 마지막까지 빈 배열이면 촬영 완료로 볼 수 없습니다.
- **뷰포트에는 상자가 있는데 PNG가 검음**: 뷰포트 시점과 센서 카메라는 다릅니다. GUI 카메라 메뉴에서 `/World/Camera` 시점으로 전환하고 조명·카메라 방향을 확인하세요.
- **투영 픽셀이 상자와 맞지 않음**: 우선 `--lens none`인지 확인하고 `(u,v)`를 배열의 `[v,u]`로 읽었는지 보세요.
- **fisheye의 투영 배열이 비어 있음**: 해당 모드에서 계산을 생략하는 코드의 동작입니다. PNG 촬영 여부는 별도로 확인합니다.
- **GUI를 움직여도 저장 PNG가 바뀌지 않음**: 파일은 한 번만 저장합니다. 새 장면의 측정값은 새 출력 폴더로 재실행하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)에 대응합니다. 공식 Camera와 OpenCV 렌즈 API를 세 상자 장면에 적용하고 PNG·배열·투영 좌표 저장을 추가했습니다.

기존 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 렌즈의 headless 60단계에서 영상 크기와 투영 픽셀의 상자 색을 확인한 과거 기록입니다. 현재 파일을 다시 실행한 결과는 아니며 왜곡 렌즈·Inspector·D455·pre-ISP 실습도 포함하지 않습니다. 실행 조건은 `tutorial.json`을 참고하고 각 모드의 출력으로 직접 확인하세요.
