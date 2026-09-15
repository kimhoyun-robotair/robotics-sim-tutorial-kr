# 62. 카메라 영상·렌즈·투영 좌표

권장 학습 순서 **62** · 센서와 측정 데이터 · 출처 ID `t145`

고정된 세 물체를 640×480 카메라로 촬영하고 RGB, motion vector, 월드 점의 영상 좌표를 저장합니다. 원문의 외부 환경을 로컬 도형으로 바꾸고 측정 스냅샷을 저장한 뒤 GUI에서 계속 관찰할 수 있게 했습니다. 렌즈 왜곡은 5.1의 네이티브 OpenCV schema를 사용합니다.

## 이 실습의 의도

고정된 세 상자를 위에서 촬영하여 USD 카메라 설정이 실제 이미지와 픽셀 좌표로 이어지는 과정을 익힌다. 물체와 카메라를 정지시켜 렌즈 왜곡에 따른 영상 변화와 움직임에 따른 motion vector를 구별할 수 있게 했다. 기본 `--lens none`은 왜곡 계수 0인 OpenCV pinhole 설정이며, 렌더링 후 이미지 한 장과 이상적 투영 좌표를 저장한다.

## 실행 후 확인할 것

- **카메라 영상**: `rgba.png`와 `camera.npz`의 `rgba`를 열어 `/World/Box0`~`Box2`와 바닥이 보이는지 확인한다. 기본 해상도의 배열 형태는 `[480, 640, 4]`이며, 검은 화면이나 빈 배열을 정상 촬영으로 보지 않는다.
- **월드 점과 픽셀의 대응**: 기본 렌즈에서 `measurements.json`의 `projected_points`는 각 상자 윗면 중심 `[-1,0,0.9]`, `[0,0,0.9]`, `[1,0,0.9]` m의 `(u,v)`다. 이미지 배열은 `[v,u]`로 찾아 상자 영역과 대조하고, 카메라 방향 때문에 월드 x의 변화가 이미지 세로 방향으로 나타나는 것을 확인한다.
- **정지 장면의 센서값**: `motion_vectors`가 거의 0인 것은 이 장면의 의도에 맞는다. 카메라는 30 Hz, 물리·렌더 step은 60 Hz이므로 매 step이 독립적인 새 카메라 샘플이라고 가정하지 않는다.
- **렌즈 비교의 경계**: `--lens pinhole`과 `--lens fisheye`로 만든 이미지의 주변부 형태를 비교한다. 왜곡 pinhole의 저장 좌표는 여전히 이상적 투영이고 fisheye의 `projected_points`는 빈 배열이므로, 두 경우를 기본 렌즈의 픽셀 대응 실패로 판정하지 않는다.
- **저장 시점**: 기본 실행은 240스텝 후 마지막 RGBA·motion vector를 한 번 저장한다. 이후 GUI가 계속 갱신되어도 저장 파일은 영상 스트림이나 모든 프레임의 기록으로 늘어나지 않는다.

## 이 패키지만으로 준비하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Isaac Sim 설치의 `python.sh`가 필요합니다. GUI 관찰 단계는 화면과 RTX 렌더링이 가능한 환경에서 수행합니다. 로컬 기본 장면은 코드로 만들며 다른 `src` 패키지, 공통 모듈, 저장소의 asset/에 의존하지 않습니다. 원문의 별도 에셋·설치 예제를 사용하는 추가 단계는 아래에 구체적으로 구분했습니다.

```bash
export ISAAC_SIM_PATH=/path/to/isaacsim
cd src/62_sensors_sensors_camera
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/run-01
```

출력 폴더는 **존재하지 않는 새 경로**를 지정합니다. 이미 있으면 오류로 멈추어 이전 결과를 보호합니다. `--output`을 생략하면 이 패키지의 `output/날짜_시간/`에 저장합니다.

`--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 렌더링·카메라 갱신이 계속됩니다. 처음 240스텝을 마친 시점의 이미지·motion vector와 투영 좌표를 한 번 저장하며, 이후 관찰 중에는 파일을 추가하거나 바꾸지 않습니다. `--steps N`에 양수를 주면 N스텝 뒤 스냅샷을 저장하고 종료합니다. `--headless`만 사용하면 기존과 같이 240스텝 후 종료합니다. `--interactive`는 기존 명령 호환용이며 이제 필요하지 않습니다. 명시한 `--steps`의 종료 조건을 해제하지 않고, `--headless`와 함께 사용할 수 없습니다.

run.py는 standalone 실행용이므로 Script Editor에 전체를 붙이지 않습니다. 처음 240스텝을 마치기 전에 창을 닫으면 결과 파일은 완성되지 않을 수 있습니다.

창 없이 유한 실행으로 결과만 만들 때는 별도의 새 출력 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240 --output output/batch-01
```

## 실습 순서와 관찰

1. 기본 명령을 실행하고 출력 `rgba.png`를 엽니다. 세 상자와 바닥을 확인합니다. `camera.npz`에는 RGBA 배열, 투영한 점, motion vector가 있습니다. 정지 장면의 motion vector가 거의 0인 것은 정상입니다.
2. `--headless`와 `--steps` 없이 실행해 뷰포트 카메라 메뉴 **Cameras > Camera**로 전환합니다. Stage에서 `/World/Camera`를 선택해 focalLength와 aperture를 봅니다. **Create > Camera**로 별도 카메라를 만들면 prim만 생성되며 영상 배열을 얻으려면 render product가 필요합니다.
3. **Tools > Sensors > Camera Inspector**를 열고 **Refresh** 후 `/World/Camera`를 선택합니다. Camera State의 위치·orientation을 복사하고 **Create Viewport**로 두 영상을 나란히 봅니다. 해상도 비율은 aperture 비율과 일치시켜 square pixel을 유지합니다.
4. `--lens pinhole --output output/pinhole`과 `--lens fisheye --output output/fisheye`로 각각 실행합니다. 같은 도형의 가장자리 휨과 주변부 시야를 비교합니다. 렌즈 변경만으로 카메라 위치는 바뀌지 않습니다.
5. 기본 `--lens none`도 명시적인 OpenCV pinhole schema에 0 왜곡 계수를 설정하여 640×480, fx=fy=320, cx=320, cy=240을 렌더러에 지정합니다. 출력 좌표는 동일한 K와 `get_view_matrix_ros()`로 계산한 이상적인 pinhole 투영입니다. Fisheye 모드에서는 이 좌표를 생략합니다. 왜곡을 켠 pinhole 영상에는 별도의 distortion mapping이 필요하므로 이상적 좌표와 그대로 일치한다고 해석하면 안 됩니다.

## API와 USD 개념

`SimulationApp`은 Kit를 먼저 시작하고, `World`는 물리/렌더 step을 관리합니다. `Camera.initialize()`가 render product와 기본 RGB annotator를 준비합니다. `get_rgba()`는 그 렌더 결과입니다. Camera prim은 USD 장면의 렌즈·자세 정의이고 render product는 실제 이미지 생성 요청입니다.

이 예제는 m 단위입니다. `Camera.set_focal_length(.018)`은 18 mm, `set_horizontal_aperture(.036)`은 36 mm를 의미합니다. Raw USD 카메라 속성에는 1/10 stage unit 관례가 있으므로 wrapper와 raw 숫자를 그대로 섞지 마세요. quaternion 순서는 `(w,x,y,z)`입니다. Camera wrapper의 world 축 관례와 USD Camera의 -Z 시선 축은 내부에서 변환됩니다. 5.1의 `get_image_coords_from_world_points()`/`get_intrinsics_matrix()`는 렌즈 모델 이름에 소문자 pinhole이 있는지를 검사하여 OpenCV 모델 이름에서도 제한이 생깁니다. 이 패키지는 알려진 K와 공개 view matrix로 직접 투영하여 그 제한을 피합니다. 실제 렌더에도 같은 K를 명시합니다.

내부 보정 K의 fx,fy,cx,cy는 픽셀, 외부 보정은 센서/월드 좌표 변환입니다. 다른 도구의 변환행렬은 축 방향·world-to-camera인지 camera-to-world인지 확인한 뒤 변환해야 합니다. rig Xform 밑에 카메라들을 자식으로 두면 공통 변환을 상속합니다.

## 확장 실습·성공 기준·문제 해결

렌즈 모드 하나만 바꾸어 세 이미지의 가장자리 형태를 비교합니다. 검은 영상이면 `--steps 480`으로 워밍업을 늘리고 빛과 카메라 시선을 확인합니다. `--headless`에서는 viewport가 없으므로 저장된 PNG를 봅니다.

원문의 센서 rig 예제인 RealSense D455는 NVIDIA 에셋 `/Isaac/Sensors/Intel/RealSense/rsd455.usd`를 Content Browser에서 열어 RSD455 아래 left/right/color/IMU 및 `Camera_Pseudo_Depth`를 확인합니다. 이 pseudo depth는 펌웨어 stereo 알고리즘을 재현한 결과가 아닙니다. 좌우 카메라의 상대 transform을 바꾸며 baseline 의미를 관찰하세요.

5.1 추가 pre-ISP 실습은 새 출력 폴더로 다음 원래 설치 예제를 실행합니다. HDR→color correction→CFA→companding 단계별 출력과 최종 ISP 이미지를 비교하고 CFA 데이터가 RGB 이미지와 다른 배열임을 확인하세요. 이것은 설치된 NVIDIA 예제 실행입니다.

```bash
"$ISAAC_SIM_PATH/python.sh" "$ISAAC_SIM_PATH/standalone_examples/api/isaacsim.sensors.camera/camera_pre_isp_pipeline.py" --draw-output --output-dir output/pre-isp-01
```

이전 fisheyePolynomial 근사나 폐기된 RTX Camera Projection 속성 대신 이 패키지의 `set_opencv_*_properties`를 사용합니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 — Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- 구현 API는 설치된 5.1 `exts/`와 해당 `standalone_examples/` 원본을 함께 확인했습니다. 원문과 다른 작은 장면·GUI 관찰 루프·측정 스냅샷 저장은 이 패키지에서 추가했습니다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
