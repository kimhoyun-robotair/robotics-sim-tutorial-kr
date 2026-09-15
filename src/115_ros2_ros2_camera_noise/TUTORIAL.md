# 115. 원본 영상과 잡음을 더한 센서 영상 비교하기

## 이번에 배우는 것

**같은 카메라의 RGB를 두 갈래로 발행하고, 한쪽 배열에만 Gaussian 잡음을 넣어 처리 위치와 잡음 크기를 확인합니다.**

실제 카메라는 같은 표면을 보아도 픽셀값이 조금씩 흔들립니다. 이 실습에서는 렌더링한 RGB 배열에 평균 0의 정규분포 잡음을 더합니다. 물체의 재질을 바꾸는 대신 **센서가 내보낼 데이터를 가공하는 과정**입니다.

| 파일·출력 | 역할 |
|---|---|
| `run.py` | 회전 카메라, 원본·가공 영상 파이프라인 구성 |
| `noise.py` | NumPy로 CPU에서 잡음 처리 |
| `noise_warp.py` | Warp kernel로 GPU에서 잡음 처리 |
| `/rgb_clean` | 원본 RGB |
| `/rgb_augmented` | 잡음이 적용된 RGB |

두 출력은 같은 640×480 Render Product를 사용하며 frame 이름은 `sim_camera`입니다. 카메라는 스텝마다 0.25°씩 회전합니다.

## 1. 두 영상을 나란히 받기

Isaac Sim 5.1, RTX GPU, Ubuntu 24.04의 ROS 2 Jazzy와 RViz2를 준비합니다. 저장소 루트의 Bash에서 실행하세요. Ubuntu 22.04/Humble에서는 아래 `jazzy` 값과 경로를 모두 `humble`로 바꿉니다.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 내부 브리지를 사용합니다. NumPy·Warp·Replicator도 Isaac Sim Python 환경의 것을 사용합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/115_ros2_ros2_camera_noise/run.py --device cpu --sigma 0.1 --seed 1234
```

설치 위치가 다르면 `ISAAC_SIM`을 바꾸세요. 기본 GUI는 창을 닫을 때까지 실행합니다. `--steps 1800`은 유한 실행이며, `--headless`만 지정해도 기본 1800스텝을 사용합니다. `--frames`는 headless 기본 한도에만 쓰입니다.

터미널 B에서 시스템 ROS를 준비합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic info /rgb_augmented
rviz2
```

RViz에 **Image**를 두 개 추가하고 `/rgb_clean`, `/rgb_augmented`를 각각 지정합니다. Isaac Sim Viewport도 `/World/Camera`로 바꿔 같은 카메라가 보는 장면을 관찰하세요.

### 실행 결과 확인하기

가공 영상의 균일한 바닥이나 큐브 면에서 픽셀 밝기가 흔들리는지 확인합니다. 원본과 물체 배치는 같아야 합니다. 카메라가 회전하므로 가능하면 같은 timestamp의 영상을 비교하세요. 시점 차이로 물체가 이동한 것을 잡음 효과로 오해하지 않습니다.

**Viewport는 깨끗한 장면을 유지합니다.** 잡음은 RGB 배열에서 더하므로 USD 물체·재질과 일반 Viewport의 렌더 결과를 수정하지 않기 때문입니다. `--device cpu`도 잡음 계산만 CPU에서 수행하며 장면 렌더링에는 RTX GPU가 필요합니다.

## 2. RGB 배열에 잡음이 들어가는 위치 읽기

### 코드에서 볼 부분

```text
카메라 → Render Product
             ├─ RGB writer ─────────────────→ /rgb_clean
             └─ RGB annotator → augmentation → /rgb_augmented
```

Annotator는 렌더 결과에서 RGB 같은 필요한 데이터를 읽는 처리기입니다. `Augmentation.from_function()`으로 가공 함수를 등록하고 `augment_compose()`로 원본 annotator 뒤에 연결합니다. 마지막 writer가 결과를 ROS Image로 보냅니다.

CPU 함수의 핵심은 세 줄입니다.

```python
rgb = data_in[..., :3].astype(np.float32)
rng = np.random.default_rng(seed)
return np.clip(rgb + rng.normal(0.0, sigma, rgb.shape), 0, 255).astype(np.uint8)
```

- `[..., :3]`은 알파 채널을 제외한 RGB 세 채널을 고릅니다.
- 먼저 float로 바꾸면 잡음을 더하는 중간값이 8-bit 정수 범위에 갇히지 않습니다.
- `clip(0,255)`는 범위 밖의 값을 양 끝으로 제한합니다. 그 뒤 `uint8`로 돌아옵니다.

정수 배열에 바로 더하면 255를 넘은 밝은 값이 작은 값으로 돌아가는 overflow 문제가 생길 수 있습니다. **실수 계산 → 범위 제한 → 정수 변환** 순서는 이 문제를 피하기 위한 것입니다.

CLI의 sigma는 255에 대한 비율입니다. `--sigma 0.1`이면 CPU 함수에는 `0.1×255=25.5`가 전달됩니다. 원본 픽셀이 128이라면 범위 제한 전 잡음 결과의 중심은 128, 표준편차는 25.5입니다. 0이나 255에 가까운 픽셀은 clipping 때문에 이론 분포와 다르게 보일 수 있습니다.

여기서 함수가 받는 `seed`와 CLI의 `--seed`도 구분해야 합니다. 설치된 5.1 Replicator의 증강 노드는 CLI seed로 내부 난수 생성기를 초기화하고, **실행할 때마다 다음 정수 seed를 CPU 함수 또는 CUDA 커널에 전달**합니다. 따라서 `np.random.default_rng(seed)`가 함수 안에 있어도 이 파이프라인에서 잡음이 매 프레임 같은 무늬로 고정되는 것은 아닙니다. CLI seed는 같은 실행 조건을 재현하기 위한 초기 조건으로 사용합니다.

### GPU 구현에서 볼 부분

CPU 실행을 종료하고 터미널 A에서 장치만 바꾸어 실행할 수 있습니다.

```bash
"$ISAAC_SIM/python.sh" src/115_ros2_ros2_camera_noise/run.py --device cuda --sigma 0.1 --seed 1234
```

Warp kernel은 한 thread가 한 픽셀을 담당합니다.

```python
row, col = wp.tid()
pixel = row * data_out.shape[1] + col
```

행 번호에 **영상 너비**를 곱해 픽셀의 고유 번호를 만듭니다. 채널마다 다른 난수 상태를 사용하고 출력 배열은 `(height,width,3)`의 `uint8`입니다. GPU 경로에서는 `sigma`를 함수 안에서 255배 합니다.

### 실행 결과 확인하기

CPU와 CUDA 모두 잡음 영상이 생성되는지, 출력 해상도와 RGB 형식이 유지되는지 확인합니다. 같은 seed라도 NumPy와 Warp의 난수 생성기가 다르므로 픽셀 단위로 완전히 같은 영상을 기대하지 마세요. 이 비교는 처리 장치가 바뀌어도 **같은 크기 척도의 잡음 처리**가 가능한지 보는 것입니다.

writer에는 `IsaacReadSimulationTime`을 연결해 메시지 시간을 넣습니다. 별도 발행 Gate는 없으며 실제 ROS 도착 빈도는 렌더 속도·잡음 계산·DDS 처리량에 영향을 받습니다.

### 공식 Viewport 방식과 비교하기

로컬 앱을 종료한 뒤 터미널 A에서 설치에 포함된 예제를 별도로 실행할 수 있습니다.

```bash
"$ISAAC_SIM/python.sh" "$ISAAC_SIM/standalone_examples/api/isaacsim.ros2.bridge/camera_noise.py"
```

이 경로는 `/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd`에 접근할 수 있어야 합니다. 공식 예제는 활성 Viewport의 Render Product에 잡음 writer를 연결하며, 이 폴더는 별도 Render Product와 원본 비교 토픽을 만듭니다. ROS에서는 `/rgb_augmented`를 확인하고 Viewport의 깨끗한 렌더와 비교하세요. 설치 예제에는 이 폴더의 `--device`, `--steps` 옵션을 그대로 전달하지 않습니다. 관찰을 마치면 창을 닫습니다.

## 3. sigma·seed·장치의 역할 정리

| 설정 | 바꾸면 달라지는 것 | 비교할 때 주의할 점 |
|---|---|---|
| sigma | 잡음의 크기 | 큰 값은 clipping 영향을 더 받음 |
| seed | 난수 초기 조건 | 장치가 다르면 같은 픽셀을 보장하지 않음 |
| device | 가공을 실행할 위치 | CPU를 골라도 GPU 렌더링은 필요 |

잡음을 크게 만드는 실험과 CPU/GPU 속도 비교는 다른 실험입니다. 먼저 한 장치에서 sigma의 의미를 확인하고, 장치 비교에서는 sigma·장면·해상도를 유지하는 편이 해석하기 쉽습니다.

## 4. 간단한 확인 실험

처음의 CPU 실행과 같은 조건에서 **`--sigma`만 0.1에서 0으로 바꿔 보세요.**

```bash
"$ISAAC_SIM/python.sh" src/115_ros2_ros2_camera_noise/run.py --device cpu --sigma 0 --seed 1234
```

평균 0, 표준편차 0인 잡음은 RGB 값을 바꾸지 않습니다. 같은 시각의 원본과 가공 영상에서 RGB 내용이 같아지는지 확인하세요. 화면을 눈으로 비교하는 것은 간단한 확인이며, 픽셀 일치를 주장하려면 timestamp가 같은 실제 메시지의 RGB 배열을 비교해야 합니다.

## 실행할 때 막히면

- **가공 영상만 shape/dtype 오류**: 함수 출력이 3채널 `uint8`인지 확인하세요. 원본 RGBA나 float 배열을 그대로 반환하지 않습니다.
- **CUDA 경로에서 오류**: `--device cpu`로 원본·가공 발행을 먼저 확인하면 Warp 처리와 ROS 연결 문제를 나누어 볼 수 있습니다.
- **sigma=0인데 두 화면에서 물체 위치가 다름**: 카메라가 회전하므로 메시지 timestamp를 비교하세요.
- **처음 몇 프레임이 검음**: 렌더 준비가 끝날 때까지 기다리세요. 관찰에는 단계 한도 없는 GUI 실행이 편리합니다.
- **토픽은 있지만 RViz Image가 비어 있음**: `ros2 topic info -v /rgb_augmented`로 QoS를 확인하고 수신 정책을 맞춥니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Add Noise to Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_noise.html)에 대응하며, 브리지 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

공식 예제의 창고·Viewport 대신 직접 생성한 장면과 별도 Render Product를 사용합니다. 원본 비교 토픽, CPU·GPU 함수와 밝기 범위 처리는 로컬 실습 구성입니다. `tutorial.json`은 `verification: not_run`이며 실제 RTX 영상·Warp kernel·DDS 수신은 이번 문서 개정에서 실행 검증하지 않았습니다.
