# 센서·물리 검증과 문제 해결

이 문서는 화면에 장면이 보이는지, 센서 배열이 실제로 유효한지, 로봇 상태가 물리적으로 안정적인지를 나누어 확인하는 방법을 설명한다. 화면 한 장만 보고 세 항목을 모두 통과했다고 판단하지 않는다. 기준 버전은 Isaac Lab `v3.0.0-beta2.patch1`이며, 아래 실습은 PhysX와 Isaac RTX 렌더러를 사용한다.

## 1. 검증 결과를 읽는 기준

| 확인 항목 | 이 튜토리얼을 작성한 환경에서 확인 가능한 범위 | GPU PC에서 추가로 확인할 내용 |
|---|---|---|
| 파이썬 구문 | `py_compile`로 확인한다 | 실제 환경에서 import와 실행이 되는지 확인한다 |
| 버전별 API | 고정한 공식 태그의 함수·설정 정의와 대조한다 | 설치한 패키지가 같은 태그인지 확인한다 |
| RGB/depth 판정 함수 | NumPy 기반 CPU 테스트로 검은 영상, 잘못된 depth 등 실패 사례를 확인한다 | 실제 렌더러 출력으로 검사한다 |
| 로봇의 자세·접촉 | 예제의 초기 높이, 충돌, 관절 목표와 상태 검사 코드를 검토한다 | PhysX에서 충분히 진행하고 상태 로그와 GUI를 함께 확인한다 |
| RTX 영상·학습 | 작성 환경에 NVIDIA GPU/Isaac Sim 실행 환경이 없어 실행하지 못했다 | 지원 GPU에서 아래 검사와 학습을 실행하고 결과를 보관한다 |

CPU 테스트 통과는 RTX 영상이나 로봇 안정성 검증을 대신하지 못한다. 이 튜토리얼은 실제 GPU 실행을 완료했다고 주장하지 않는다. 드라이버·GPU·자산 상태까지 포함한 무결함을 문서나 정적 검사만으로 보장할 수 없으므로, 아래 절차로 실패를 확인하고 원인을 좁힌다.

## 2. 카메라 최소 장면부터 검증한다

로봇·환경 USD·대규모 복제를 동시에 넣으면 영상이 검게 나왔을 때 원인을 찾기 어렵다. 먼저 바닥, 빨간 상자, 초록 상자, 파란 상자, 조명, 카메라 한 대로 구성한 [p04_camera_check.py](../examples/p04_camera_check.py)를 실행한다. 장면의 물체는 모두 고정된 기본 도형이다. 로봇 자산을 다운로드하지 않으며, 자유 강체가 없어서 이 단계의 영상 검사에 낙하나 관절 제어가 영향을 주지 않는다.

새 터미널에서 설치 때 사용한 Isaac Lab 환경을 활성화한 뒤 경로를 설정한다. 다음 예시는 Isaac Lab을 `$HOME/IsaacLab`에 설치했다고 가정한다.

```bash
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
cd "$HOME/IsaacLab"

./isaaclab.sh -p \
  "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p04_camera_check.py" \
  --device cuda:0 --enable_cameras --viz kit \
  --steps 120 \
  --output-dir "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/p04_camera"
```

`--viz kit`은 Kit 창을 연다. 카메라 센서 출력을 켜는 옵션은 별도로 `--enable_cameras`이다. 창 없이 검사하려면 위 명령의 `--viz kit`을 `--viz none`으로 바꾼다. 이 예제는 뷰어를 설정하지 않았으므로 `--viz`를 생략하면 창 없이 실행한다. 다른 스크립트에서는 `SimulationCfg.visualizer_cfgs`도 확인하며, GUI 실습에서는 옵션을 명시한다. 물리 장치만 `cpu`로 바꾸어도 RTX 카메라에 필요한 GPU가 사라지는 것은 아니다.

기본 120단계 중 처음 30단계는 렌더러 준비 시간으로 사용한다. 나머지 90개 프레임을 검사하고 자동으로 종료한다. `--warmup`으로 준비 단계를 늘릴 수 있지만 최소 30이며, `--steps`는 준비 단계를 포함한 전체 단계 수이다. 창을 일찍 닫으면 미완료로 실패한다.

완료 후 다음 파일을 확인한다.

| 파일 | 내용 | 확인 방법 |
|---|---|---|
| `rgb.png` | 마지막 프레임의 RGB 영상 | 가운데 빨간 상자, 좌우의 다른 색 상자, 바닥이 보이는지 연다 |
| `rgb.npy` | 원본 RGB 배열 | 크기, 자료형, 픽셀 값을 확인한다 |
| `depth.npy` | `distance_to_image_plane` 배열, 미터 단위 | 유한한 양수 영역과 중앙 표적의 거리를 확인한다 |
| `camera_report.json` | 단계 수, 실패 프레임, 최종 통계, 판정 기준 | `status`, `checked_frames`, `failed_frames`를 확인한다 |

```bash
python -m json.tool \
  "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/p04_camera/camera_report.json"
```

정상 완료의 조건은 프로세스 종료 코드 `0`, `status: "PASS"`, `checked_frames: 90`, `failed_frames: []`이다. 여기서 90은 기본 명령의 `120 - 30`으로 계산한 예상 개수이며, 실측 결과를 제시한 값이 아니다. 검사 실패 시 종료 코드는 0이 아니며, 가능한 경우 마지막 영상과 보고서를 남긴다. 시뮬레이터나 카메라 초기화 자체가 실패한 경우에는 프레임 보고서를 만들기 전일 수 있으므로 터미널 오류부터 확인한다.

## 3. 어떤 센서 설정이 왜 필요한가

핵심 코드는 다음과 같다. 완전한 실행 코드는 예제 파일에 있다.

```python
from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.renderers import IsaacRtxRendererCfg
import isaaclab.sim as sim_utils
from isaaclab.sensors import Camera, CameraCfg

sim_cfg = sim_utils.SimulationCfg(
    dt=1.0 / 60.0,
    render_interval=1,
    device="cuda:0",
    physics=PhysxCfg(),
)
camera_cfg = CameraCfg(
    prim_path="/World/Camera",
    width=320,
    height=240,
    update_period=0.0,
    data_types=["rgb", "distance_to_image_plane"],
    renderer_cfg=IsaacRtxRendererCfg(depth_clipping_behavior="none"),
    spawn=sim_utils.PinholeCameraCfg(
        focal_length=24.0,
        horizontal_aperture=20.955,
        clipping_range=(0.1, 20.0),
    ),
)
```

`dt`는 물리 시간 간격이고, `render_interval=1`은 매 물리 단계의 렌더링을 요청한다. `update_period=0.0`은 센서 갱신 시 별도의 긴 샘플링 간격을 두지 않는 설정이다. 예제에서는 `sim.step()` 다음에 `camera.update(dt, force_recompute=True)`를 호출해서 준비 단계에도 실제 센서 갱신을 요청한다. 해상도는 먼저 320×240으로 두고, 한 대에서 통과한 뒤 늘린다.

`distance_to_image_plane`은 카메라 광학 축 방향의 깊이이다. 카메라 원점에서 물체까지의 유클리드 거리인 `distance_to_camera`와 영상 가장자리에서 값이 다를 수 있다. 두 배열을 같은 거리라고 보고 비교하면 잘못된 검사 결과가 나온다. `depth_clipping_behavior="none"`에서는 먼 배경에 `+inf`가 나올 수 있다. 이를 모두 실패로 처리하거나 `0`으로 바꾸어 평균에 넣지 않는다. 유한하고 양수인 영역만 거리 통계에 사용한다.

3.x의 센서 출력은 `ProxyArray`이다. `.torch`로 Torch 뷰를 얻은 뒤 첫 카메라를 선택한다.

```python
output = camera.data.output
rgb = output["rgb"].torch[0].detach().cpu().numpy().copy()
depth = output["distance_to_image_plane"].torch[0].detach().cpu().numpy().copy()
```

첫 차원은 카메라 수이다. RGB는 `(N, H, W, 3)`, depth는 `(N, H, W, 1)` 형태로 다룬다. `.torch`는 원본과 메모리를 공유하는 뷰이므로, 다음 프레임과 비교할 표본은 `.copy()` 또는 Torch의 `.clone()`으로 보관한다. 원본 뷰만 변수에 저장하면 다음 갱신이 이전 프레임까지 바꿀 수 있다. 2.x 예제의 배열 처리 코드를 그대로 가져오지 않는다.

카메라 자세도 버전에 주의한다. Isaac Lab 3.x quaternion 순서는 `(x, y, z, w)`이며, 2.x의 `(w, x, y, z)`와 다르다. 또한 ROS 카메라 좌표계는 `+Z`가 전방이고 `-Y`가 위쪽이며, USD/OpenGL 카메라는 `-Z`가 전방이고 `+Y`가 위쪽이다. 이 예제는 직접 quaternion을 적는 대신 시선 목표를 지정한다.

```python
sim.reset()  # 센서를 초기화한 뒤 자세를 지정한다.
camera.set_world_poses_from_view(
    [[3.0, 0.0, 1.8]],       # 카메라 위치, m
    [[0.0, 0.0, 0.5]],       # 빨간 상자의 중심, m
)
```

이 코드에서 `ros` 좌표계라는 용어는 카메라 축 정의를 뜻한다. ROS 노드나 ROS 2 Bridge를 실행해야 한다는 뜻은 아니다.

## 4. 검은 영상과 무효 depth를 수치로 판정한다

[image_checks.py](../examples/image_checks.py)는 아래 조건을 확인한다. 이 값은 예제의 밝은 정적 장면을 위한 기준이며, 야간 장면·다른 거리·다른 재질의 일반적인 품질 기준은 아니다. 장면을 바꿨다면 근거에 맞게 기준도 바꾸어야 한다.

| 검사 | 통과 기준 | 잡아내려는 오류 |
|---|---|---|
| RGB 값 | uint8 또는 `[0,1]` 실수, NaN/무한대 없음 | 잘못된 배열 변환, 비정상 픽셀 |
| RGB 평균 | `[0,1]` 기준 0.02 이상 | 거의 검은 영상 |
| 신호가 있는 픽셀 | 최대 RGB 값이 `8/255`보다 큰 픽셀 10% 이상 | 대부분 검고 일부 픽셀만 밝은 영상 |
| 공간 변화 | 채널별 공간 표준편차의 평균 0.015 이상 | 한 색으로만 채워진 영상 |
| 완전한 흰색에 가까운 픽셀 | 모든 RGB 값이 `250/255` 이상인 픽셀 비율 99% 이하 | 거의 전체가 포화된 영상 |
| 유효 depth | 유한한 양수인 픽셀 30% 이상 | 전부 0 또는 전부 무한대인 depth |
| 잘못된 depth 값 | NaN·음수·음의 무한대 없음 | 변환·좌표계·센서 오류 |
| 중앙 표적 ROI | 중앙 가로 20%×세로 20% 중 유효 depth 90% 이상 | 물체를 보지 않는 카메라 |
| 중앙 depth 중앙값 | 2.2~3.7m | 미터/밀리미터 혼동, 잘못된 카메라 위치 |

RGBA의 alpha가 255여도 RGB가 모두 0이면 검은 영상이다. 따라서 통계에서는 alpha 채널을 제외한다. 또한 평평한 빨간 영상은 RGB 채널끼리는 값이 다르지만, 같은 채널 안에서 픽셀 위치에 따른 변화가 없다. 코드는 채널별 공간 표준편차를 계산해서 이런 영상도 실패로 처리한다.

정적 장면에서는 이전 영상과 다음 영상이 같아도 정상이다. 보고서에 `first_last_rgb_mae_255`를 남기지만, 시간이 지나면 반드시 영상이 변해야 한다는 조건은 두지 않는다. 이 숫자만으로 노이즈 여부를 판정할 수도 없다. 렌더링 노이즈·고스트·텍스처 깨짐은 PNG를 직접 확인하고, 이동하는 표적을 추가했다면 궤적과 프레임 시각을 함께 비교한다.

CPU에서 검사 함수 자체를 시험하는 명령은 다음과 같다. NumPy가 설치된 파이썬이면 Isaac Sim 없이 실행할 수 있다.

```bash
cd "$TUTORIAL_ROOT/isaaclab_tutorial"
python -m unittest discover -s tests -p 'test_image_checks.py' -v
```

테스트는 정상 영상, 무한대 배경, alpha만 밝은 검은 영상, 단색 영상, NaN RGB, 전체 무효 depth, 중앙 표적 누락, 잘못된 거리 단위 등을 넣는다. 이 테스트는 판정 함수가 실패를 놓치지 않는지 확인하며, 가짜 배열로 RTX 렌더링 성공을 증명하는 테스트가 아니다.

## 5. 카메라 검사를 로봇 실습으로 확장한다

카메라 최소 장면이 통과하면 로봇을 한 대만 추가한다. 처음에는 로봇의 기본 자세를 유지하고, 다음 순서로 변화량을 늘린다.

1. 로봇 한 대와 바닥만 둔다. 관절 이름, 기본 관절 위치, 관절 제한을 출력한다.
2. 기본 관절 위치를 목표로 넣고 몇 초간 진행한다. 루트와 관절 상태가 유한한지, 바닥을 뚫거나 빠르게 발산하는지 확인한다.
3. 목표를 바꿀 관절을 하나만 선택해서 작은 범위로 움직인다. 구동 관절인지, 목표가 해당 관절의 제한 안에 있는지 확인한다.
4. 카메라를 고정된 월드 위치에 먼저 추가한다. 영상 검사 후 로봇 링크 아래로 옮긴다.
5. 마지막으로 환경 수와 센서 수를 늘린다. 복제된 환경의 원점과 카메라 경로, VRAM 사용량을 확인한다.

3.x 로봇 상태를 검사하는 핵심은 다음과 같다. 이 코드는 로봇을 초기화하고 `robot.update(dt)`를 호출한 루프 안에 넣는 조각이다.

```python
import torch

root_state = robot.data.root_state_w.torch
joint_pos = robot.data.joint_pos.torch
joint_vel = robot.data.joint_vel.torch
if not torch.isfinite(root_state).all():
    raise RuntimeError("루트 상태에 NaN/무한대가 있다.")
if not torch.isfinite(joint_pos).all() or not torch.isfinite(joint_vel).all():
    raise RuntimeError("관절 상태가 발산했다.")
```

유한한 값만으로 물리적 안정성을 판정할 수는 없다. 로봇별 정상 높이, 관절 제한, 허용 속도와 목표 추종 오차를 추가해야 한다. 부유 베이스 보행 로봇을 제어 없이 놓으면 넘어질 수 있으며, 이것은 곧바로 충돌 모델 오류라는 뜻이 아니다. 로봇 예제의 목적이 기본 자세 유지인지, 수동 낙하인지, 학습된 정책 재생인지 먼저 구분한다. 고정 베이스 로봇팔의 경우와 동일한 높이 기준을 사족 로봇에 적용하지 않는다.

특히 초기 자세는 바닥과 겹치지 않도록 설정한다. 원점 위치만 확인하지 말고 발끝·바퀴·collision mesh의 가장 낮은 부분을 확인한다. 과도한 PD 강성, 큰 시간 간격, 작은 관성, 잘못된 질량·길이 단위가 함께 있으면 목표가 작아도 떨림이나 발산이 생길 수 있다. 한 번에 여러 설정을 바꾸지 말고 원인이 된 항목을 확인한다.

## 6. 증상별 점검표

| 증상 | 먼저 확인할 증거 | 조치 |
|---|---|---|
| Kit 창이 열리지 않는다 | 실행 명령의 `--viz`, 터미널의 초기화 오류 | 3.x GUI는 `--viz kit`으로 요청한다. 디스플레이가 없는 서버는 `--viz none`으로 검사한다 |
| GUI는 보이는데 RGB가 검다 | `--enable_cameras`, 센서 `prim_path`, `camera_report.json` | 카메라를 켜고 최소 장면으로 재현한다. viewport와 센서 카메라가 같은 출력이라고 가정하지 않는다 |
| 첫 프레임만 검거나 비어 있다 | 준비 단계 수, 단계별 실패 목록 | 30단계 이상 준비 후 검사한다. 준비 시간을 늘려도 지속되면 조명·렌더러·GPU 오류를 확인한다 |
| 영상 전체가 같은 색이다 | `rgb_spatial_std`, 중앙 ROI depth | 카메라가 바닥이나 배경만 보고 있는지 확인하고 `set_world_poses_from_view`로 표적을 지정한다 |
| depth 전체가 0이다 | dtype, shape, 갱신 호출, clipping 설정 | `camera.update`와 `distance_to_image_plane` 키를 확인한다. 준비 전 버퍼를 결과로 저장하지 않는다 |
| 하늘 부분의 depth만 무한대이다 | 유효 depth 비율, 중앙 ROI | `depth_clipping_behavior="none"`의 정상 배경일 수 있다. `+inf`를 제외한 거리 통계를 사용한다 |
| 중앙 물체의 depth가 수천 단위이다 | 거리 단위, geometry scale | USD 장면과 센서 출력을 미터 기준으로 맞춘다. 무조건 1000으로 나누기 전에 단위 오류의 위치를 확인한다 |
| 카메라가 뒤집히거나 옆을 본다 | quaternion 순서, offset convention | 3.x는 xyzw이다. world/ROS/OpenGL 축을 구분하고 먼저 look-at 방식을 사용한다 |
| 로봇이 시작과 동시에 튀어 오른다 | 초기 접촉·침투, 질량·관성, 목표 위치 | 충돌 겹침을 없애고 유효한 기본 자세를 적용한다. 과도한 gain을 낮추기 전에 초기 자세부터 확인한다 |
| 로봇이 바닥을 뚫는다 | 바닥과 링크 collider, 시간 간격, 물체 속도 | 시각 mesh와 collision이 별개인지 확인한다. 최소 장면에서 collision 및 시간 간격을 점검한다 |
| 접촉 중 떨림이 커진다 | 관절 목표·제한, stiffness/damping, physics dt | 공식 로봇 설정에서 출발하고 한 항목씩 조정한다. solver 반복 수를 무조건 크게 올리는 것으로 해결했다고 판단하지 않는다 |
| 복제 환경의 로봇이 겹친다 | `env_origins`, reset 시 쓰는 루트 위치 | 환경별 원점을 한 번만 더한다. local/world 좌표를 혼합하지 않는다 |
| 센서를 늘린 뒤 blackout/종료가 생긴다 | `nvidia-smi`의 VRAM, renderer/PhysX 로그 | 환경 수·카메라 수·해상도를 줄여 재현한다. GPU 버퍼 부족이나 드라이버 오류를 무시하고 학습을 계속하지 않는다 |
| 정지 장면에서 얼룩·고스트가 보인다 | PNG와 연속 프레임, renderer 설정 | 먼저 랜덤화와 추가 노이즈를 끄고 준비 후 비교한다. 작은 센서 해상도에서 렌더러의 시간 필터 영향을 확인한다 |
| ROS 메시지는 오지만 RViz가 비어 있다 | Jazzy 환경, `/clock`, 토픽·frame_id·TF·QoS | 시뮬레이터 자체의 RGB/depth를 먼저 통과시킨 뒤 ROS 2 Jazzy 연결을 점검한다 |

## 7. 검증 기록을 남긴다

학습 결과를 비교하거나 질문할 때는 버전, GPU, 명령, 실패 시점이 필요하다. 비밀번호나 인증 토큰이 포함될 수 있는 전체 환경 변수 덤프는 필요하지 않다.

```bash
mkdir -p "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/system"
nvidia-smi > "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/system/nvidia-smi.txt"
git -C "$HOME/IsaacLab" describe --tags --always \
  > "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/system/isaaclab-version.txt"
```

GPU 실행 결과가 없다면 보고서에 `실행하지 않음: NVIDIA GPU/Isaac Sim 환경 없음`이라고 적는다. 이미지 검사는 통과했지만 로봇 정책을 재생하지 않았다면 두 결과를 따로 적는다. 실패 기준을 낮춰서 통과 표시만 만드는 대신, 장면을 고정하고 원인을 확인한 뒤 다시 실행한다.

## 공식 근거

- [고정 태그의 공식 USD 카메라 예제](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/04_sensors/run_usd_camera.py)
- [고정 태그 CameraData: ProxyArray와 출력 형태](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/camera_data.py)
- [고정 태그 Camera: 카메라 좌표계와 look-at](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/sensors/camera/camera.py)
- [고정 태그 IsaacRtxRendererCfg: depth clipping](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_physx/isaaclab_physx/renderers/isaac_rtx_renderer_cfg.py)
- [고정 태그 AppLauncher: 카메라와 visualizer 옵션](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/app/app_launcher.py)
- [고정 태그 PhysxCfg: 물리 설정과 GPU 버퍼](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab_physx/isaaclab_physx/physics/physx_manager_cfg.py)
