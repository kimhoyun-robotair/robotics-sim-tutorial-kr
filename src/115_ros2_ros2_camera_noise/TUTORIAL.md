# 115. 카메라 영상에 Gaussian 잡음을 넣어 ROS 2로 발행하기

권장 학습 순서 **115** · ROS 2 연결과 기본 통신 · 출처 ID `t012`

Isaac Sim 5.1 **Add Noise to Camera**의 핵심은 화면을 바꾸는 것이 아니라 **센서 출력 파이프라인의 RGB 배열을 가공**하는 것이다. 이 독립 패키지는 카메라가 회전하는 작은 큐브 장면을 만들고 `/rgb_clean`과 `/rgb_augmented`를 함께 발행한다. 원문의 창고 장면 대신 로컬에서 생성한 물체를 사용하며, CPU NumPy와 GPU Warp 구현을 모두 제공한다. 원문 예제에서 생략한 0–255 범위 처리를 추가했다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 시뮬레이션 스텝과 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 지정하면 해당 횟수 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1800회를 사용합니다. 이전 `--frames` 옵션은 `--steps` 없는 headless 실행의 횟수만 정하며, GUI 종료에는 영향을 주지 않습니다. `--steps`를 지정하면 `--frames`보다 우선하며 0과 음수는 허용하지 않습니다.

## 준비와 실행

Isaac Sim 5.1.0과 RTX GPU, ROS 2 Humble(Ubuntu 22.04) 또는 Jazzy(Ubuntu 24.04), RViz2가 필요하다. `numpy`, `warp`, Replicator는 Isaac Sim Python 환경의 것을 사용한다. 일반 시스템 Python으로 패키지를 추가 설치하지 않는다. `noise.py`, `noise_warp.py`는 이 폴더 내부 파일이며 다른 튜토리얼과 연결되지 않는다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ISAAC_SIM=/home/hoyunkim/isaacsim
"$ISAAC_SIM/python.sh" run.py --device cpu --sigma 0.1
```

Jazzy 설치자는 source 경로를 `/opt/ros/jazzy/setup.bash`로 바꾼다. 받는 터미널에도 같은 ROS 배포판과 ROS_DOMAIN_ID를 설정한다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
ros2 topic info /rgb_augmented
ros2 topic hz /rgb_augmented
rviz2
```

`--steps`를 생략하면 창을 닫을 때까지 관찰할 수 있다. `--headless`에서도 별도 Render Product를 만들므로 영상 발행을 시도할 수 있다. Isaac Sim이 종료되면 발행도 끝난다.

## 실습 순서

1. 실행한 장면에서 `/World/Camera`를 찾아 Viewport의 Camera 메뉴에서 선택한다. 바닥과 색 큐브가 보이고 카메라가 매 프레임 0.25°씩 회전한다.
2. RViz에서 **Add > Image**를 두 번 누른다. 첫 번째 Image Topic은 `/rgb_clean`, 두 번째는 `/rgb_augmented`로 설정한다. 필요하면 Image의 Reliability를 publisher에 맞춰 Best Effort로 설정한다.
3. 두 영상의 장면 위치는 같고 잡음의 유무만 달라야 한다. Viewport에는 깨끗한 장면이 남는다. augmentation은 센서 배열에 적용되므로 USD 재질이나 카메라 자체를 수정하지 않는다.
4. 프로그램 종료 후 `--sigma 0`으로 재실행한다. 두 영상이 시각적으로 같아지는지 확인한다. `sigma=0.1`은 8-bit 밝기 값 기준 표준편차 25.5이다.
5. CPU 실험이 끝나면 다음 GPU 실험을 실행한다. 같은 seed를 줘도 NumPy와 Warp는 서로 다른 난수 생성기를 쓰므로 픽셀까지 같은 결과를 기대하지 않는다.

```bash
"$ISAAC_SIM/python.sh" run.py --device cuda --sigma 0.1 --seed 1234
```

## 코드에서 데이터 흐름 따라가기

1. `UsdGeom.Camera.Define`은 `/World/Camera`라는 USD 카메라를 만든다. `XformCommonAPI`가 위치와 회전을 정하고, `rep.create.render_product(..., (640,480))`가 센서 출력 해상도를 정한다.
2. `rep.annotators.get('rgb', device=...)`가 렌더된 RGBA 데이터를 읽는다. **Annotator**는 렌더 결과에서 필요한 데이터를 추출하는 처리기다.
3. `Augmentation.from_function()`이 Python 함수 또는 Warp kernel을 파이프라인에 연결한다. `augment_compose`로 원본 annotator와 augmentation을 조합하고 `lesson_rgb_noise`라는 새 annotator를 등록한다.
4. `noise.py`는 알파 채널을 제거하고 RGB를 float로 변환한 뒤 정규분포 잡음을 더한다. `clip(0,255)` 후 uint8로 돌아온다. unsigned 정수에서 직접 더하면 밝은 값이 0 부근으로 되돌아가는 overflow가 발생할 수 있으므로 이 순서가 필요하다.
5. GPU 버전은 Warp의 각 thread가 한 픽셀을 처리한다. `row * width + col`로 픽셀 ID를 정한다. 직사각형 이미지에서도 각 픽셀에 올바른 ID가 생기도록 높이가 아니라 너비를 곱한다. RGB마다 다른 난수 state를 만든다.
6. `register_node_writer`는 `isaacsim.ros2.bridge.ROS2PublishImage`를 잡음 annotator와 연결한다. `NodeConnectionTemplate('IsaacReadSimulationTime', ...)`는 메시지 timestamp에 시뮬레이션 시간을 넣는다.
7. `writer.initialize(topicName=..., frameId='sim_camera')`로 ROS 메시지 이름을 정하고 `attach([product])`로 데이터 흐름을 활성화한다. `frameId`는 토픽 이름이 아니라 데이터의 좌표계 이름이다. 마지막에 `detach()`와 `app.close()`로 파이프라인과 앱을 종료한다.

원문은 활성 Viewport의 `get_render_product_path()`를 얻고 `set_camera_prim_path()`로 카메라를 연결한다. 이 패키지는 별도 Render Product를 만들어 Viewport 조작에 센서가 영향을 받지 않도록 했다. 원문의 native 흐름도 확인하려면 Isaac Sim 설치 폴더에서 다음을 실행한다. 이 명령은 **설치된 NVIDIA 예제**를 실행하며 이 패키지의 코드를 실행하는 명령과 구별한다.

```bash
cd "$ISAAC_SIM"
./python.sh standalone_examples/api/isaacsim.ros2.bridge/camera_noise.py
```

이 native 예제는 `/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd` 자산에 접근할 수 있어야 한다. 원문과 같이 Viewport에 연결된 창고 카메라가 회전하고 `/rgb_augmented`를 발행한다.

## seed, sigma, 장치의 의미

| 설정 | 의미 |
|---|---|
| `--sigma 0.1` | 255의 10%를 표준편차로 사용한다. 평균은 0이다. |
| `--seed 1234` | 동일한 난수 초기 조건을 요청한다. 장치 간 동일 픽셀은 보장하지 않는다. |
| `--device cpu` | NumPy 함수가 CPU 메모리에 있는 배열을 처리한다. |
| `--device cuda` | Warp kernel이 GPU 배열을 처리하며 출력 shape `(-1,-1,3)`을 지정한다. |

Replicator는 seed를 생략하거나 음수로 지정하면 global seed와 노드 식별자로 seed를 정할 수 있다. Warp augmentation은 kernel 호출마다 새 seed를 얻을 수 있다. `--seed`는 통계적으로 재현 가능한 실험 조건을 위한 설정이지 연속 프레임의 잡음이 반드시 고정된다는 약속은 아니다. 0과 255에서 clipping되기 때문에 아주 큰 sigma에서는 출력 잡음 평균·분산이 이론 정규분포와 달라진다.

## 성공 기준과 추가 실험

실제 `/rgb_augmented` 메시지를 받아 잡음 영상이 보이고, sigma=0일 때 깨끗한 영상으로 돌아가면 augmentation 경로를 확인한 것이다. 토픽 이름이나 프로세스 실행만으로 이미지 검증을 대체하지 않는다.

변수 하나만 바꾸는 실험: seed와 장치를 고정하고 sigma만 `0`, `0.05`, `0.2`로 바꾼다. 물체 경계와 균일한 바닥에서 잡음이 얼마나 두드러지는지 기록한다. 출력이 밝기 범위 밖으로 돌아가는 색상 반전 없이 0–255 안에 남는지도 관찰한다.

## 문제 해결과 검증

- `No module named isaacsim`: `python3 run.py` 대신 Isaac Sim의 `python.sh`를 사용한다.
- 검은 영상: 처음 렌더 준비 프레임을 기다린다. `--steps` 없이 실행하면 창을 닫을 때까지 ROS 영상을 확인할 수 있다.
- ROS 토픽이 없음: Bridge 로드 로그, ROS_DOMAIN_ID, ROS 배포판 source를 확인한다.
- CUDA augmentation 오류: `--device cpu`로 영상 발행 경로를 먼저 확인한다. CPU로 바꿔도 Isaac Sim 렌더링 자체에는 RTX GPU가 필요하다.
- 잡음 영상의 shape/dtype 오류: 함수 출력이 `(height,width,3)`인 uint8인지 확인한다. RGBA 4채널 또는 float 배열을 그대로 반환하지 않는다.

일반 Python으로 `python3 run.py --help`와 구문 컴파일이 가능하다. 실제 RTX 렌더링, GPU kernel, ROS 영상 수신은 별도의 실행 환경 검증이 필요하며 현재 상태는 `tutorial.json`에 기록한다.

## 출처

[Isaac Sim 5.1 Add Noise to Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html), [Code Explained](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html#code-explained). API 연결 방식은 공식 5.1 예제와 설치된 `standalone_examples/api/isaacsim.ros2.bridge/camera_noise.py`를 대조했다. 장면·해설·범위 처리와 두 영상 비교 흐름은 새로 작성했다.
