# 01–10단계: Isaac Lab의 역할부터 첫 장면까지

이 장은 Ubuntu 24.04 LTS가 설치된 x86_64 워크스테이션에서 시작한다. 이전 Isaac Sim 사용 경험이나 ROS 설치를 전제로 하지 않는다. 설치를 끝낸 뒤에는 GUI에서 물체를 선택하고, 장면의 구조를 읽고, 같은 장면을 Python으로 다시 만들 수 있어야 한다.

기준일은 **2026-09-09**이며, 기준 버전은 **Isaac Lab `v3.0.0-beta2.patch1` / Isaac Sim `6.0.1` / Python `3.12`**이다. Isaac Lab의 최신 공개 릴리스에 해당하지만 **3.0 베타 계열**이라는 상태도 함께 기억한다. 이 문서의 명령은 태그에 고정한 공식 문서와 소스를 기준으로 작성했다. GPU에서 실제 실행했음을 뜻하지는 않으며, 각 단계의 통과 기준을 사용자 장비에서 확인해야 한다. [공식 릴리스](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1)

<a id="step-01"></a>

## 01단계. Isaac Lab, Isaac Sim, GR00T, Omniverse의 역할을 구분하다

로봇 학습 실습에는 서로 다른 일이 섞여 있다. 로봇의 모양을 불러오는 일, 중력과 충돌을 계산하는 일, 카메라 영상을 만드는 일, 로봇이 성공했는지 판단하는 일, 성공 확률이 높아지도록 정책을 학습하는 일이다. NVIDIA의 여러 제품 이름은 이러한 역할이 나뉘어 있기 때문에 생긴다.

| 이름 | 주된 역할 | 실습에서 다루는 대상 |
|---|---|---|
| OpenUSD | 계층, 형상, 재질, 변환, 참조 등을 표현하는 장면 기술 체계 | `/World/Robot` 같은 prim 경로와 USD 자산 |
| Omniverse | OpenUSD 기반 응용 프로그램과 시뮬레이션을 만드는 라이브러리·기술 | Kit 응용 프로그램, 확장 기능, 렌더링 등 기반 구성 요소 |
| Isaac Sim | 로봇과 환경을 구성하고 물리·센서를 실행하는 시뮬레이션 응용 프로그램 | 장면, 로봇, 카메라, 충돌, ROS 2 연결 |
| Isaac Lab | 반복 가능한 로봇 학습 환경과 학습 작업 흐름을 구성하는 프레임워크 | 관측, 행동, 보상, 종료 조건, 환경 복제, 학습·평가 |
| Isaac GR00T | 여러 로봇에 적용할 수 있는 로봇 기초 모델과 관련 학습·추론 도구 | 영상·언어·로봇 상태를 입력받아 행동을 생성하는 모델 |

Omniverse는 단일한 로봇이나 특정 학습 알고리즘을 가리키지 않는다. Isaac Sim은 이 기반 기술을 활용하는 로봇 시뮬레이션 응용 프로그램이다. Isaac Lab은 시뮬레이터를 여러 번 실행하는 데 필요한 환경 관리, 로봇 데이터 접근, 센서 구성, 학습 라이브러리 연결을 정리한다. [Omniverse 공식 소개](https://developer.nvidia.com/omniverse), [Isaac Lab 공식 소개](https://github.com/isaac-sim/IsaacLab/tree/v3.0.0-beta2.patch1)

예를 들어 상자를 집는 작업을 생각한다. Isaac Sim에서 로봇 팔, 상자, 탁자, 조명과 카메라를 배치한다. Isaac Lab에서는 집게 위치와 상자 위치를 관측으로 묶고, 관절 목표를 행동으로 정의하며, 상자가 충분히 올라오면 보상을 주는 환경을 만든다. PPO 같은 학습 알고리즘은 이 환경과 상호작용하며 정책의 가중치를 바꾼다. Isaac Lab만 설치했다고 로봇이 스스로 상자를 집는 정책까지 준비되는 것은 아니다.

GR00T 계열의 VLA, 즉 Vision-Language-Action 모델은 영상과 언어 지시 등을 받아 로봇 행동을 생성하는 모델이다. Isaac Lab의 환경에서 정책을 평가하거나 시연 데이터를 만들 수 있지만, GR00T의 모델 가중치·데이터 형식·행동 표현은 별도의 구성 요소이다. 특정 GR00T 모델의 행동을 아무 로봇의 관절 명령에 그대로 연결해서는 안 된다. 관절 순서, 제어 주기, 행동 단위, 로봇 형상에 맞는 연결이 필요하다. [NVIDIA GR00T 저장소](https://github.com/NVIDIA/Isaac-GR00T), [GR00T N1 논문](https://arxiv.org/abs/2503.14734)

### GUI, Extension, Python은 왜 나뉘는가

GUI는 사람이 장면을 보고 수정하는 인터페이스이다. Extension은 Kit에 기능을 추가하는 모듈이다. Python standalone은 프로그램이 앱의 시작·시뮬레이션 진행·종료를 소유하는 실행 방식이다. Extension도 Python으로 작성할 수 있고, GUI의 도구 자체가 Extension인 경우도 있다. 따라서 셋은 완전히 배타적인 제품 분류가 아니다. [Isaac Sim 작업 방식](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/workflows.html)

| 하려는 일 | 처음 선택할 방식 | 이유 |
|---|---|---|
| 로봇의 관절이나 카메라 방향을 눈으로 확인하다 | GUI | 잘못 배치된 물체를 바로 찾을 수 있다 |
| 버튼·패널·반복되는 장면 편집 도구를 만들다 | Extension | 이미 실행 중인 앱에 기능을 붙인다 |
| 동일한 환경을 매번 만들고 학습하다 | Python standalone | 초기화 순서, 시간 간격, 반복 횟수를 코드로 관리한다 |

이 튜토리얼은 GUI에서 구조를 익힌 뒤 Python standalone으로 옮겨 간다. GUI에서 이동한 로봇 위치가 학습 스크립트에 자동으로 반영되는 것은 아니다. 반복 실행에 필요한 값은 USD 자산이나 Python 설정에 저장한다.

**통과 기준:** “시뮬레이터가 계산하는 것”과 “학습 환경이 정의하는 것”을 상자 집기 예시로 설명할 수 있다.

<a id="step-02"></a>

## 02단계. 최신 버전을 고정하고 3.0의 실행 구성을 이해하다

최신이라는 표현은 시간이 지나면 달라진다. 실습의 재현성을 위해 저장소의 움직이는 `main`이나 `develop` 대신 공개 태그를 사용한다. 이 문서에서 `latest` 링크는 버전 확인용으로도 사용하지 않으며, 실행 코드는 지정한 태그에 맞춘다.

| 항목 | 이 튜토리얼의 값 | 확인할 곳 |
|---|---|---|
| 운영체제 | Ubuntu 24.04 LTS, x86_64 | `cat /etc/os-release`, `uname -m` |
| Isaac Lab 소스 | `v3.0.0-beta2.patch1` | `git describe --tags --exact-match` |
| Isaac Sim 표시 버전 | `6.0.1` | 앱 버전 및 공식 릴리스 |
| Isaac Sim pip 배포 버전 | `6.0.1.0` | Python 패키지 메타데이터 |
| Python | `3.12.x` | `python --version` |
| PyTorch / torchvision | `2.10.0` / `0.25.0` | 태그의 pip 설치 문서 |
| CUDA wheel 계열 | `cu128` | PyTorch 설치 인덱스 |
| ROS로 확장할 때의 기준 | ROS 2 Jazzy | 32단계의 확장 안내 |

`6.0.1`과 `6.0.1.0`은 여기서 서로 다른 Isaac Sim 세대를 의미하지 않는다. 제품 문서와 Python 패키지의 버전 표기를 구분한 것이다. `nvidia-smi`에 표시되는 CUDA 버전은 드라이버가 지원하는 CUDA 수준이며, 현재 Python이 불러온 PyTorch wheel의 CUDA 버전은 `torch.version.cuda`로 확인한다.

설치 명령은 [고정 태그의 pip 설치 문서](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/pip_installation.rst)를 따른다. 이후 개발 문서에 다른 PyTorch 버전이 보이더라도 일부 줄만 섞어서 설치하지 않는다.

### 물리 엔진, 렌더러, 뷰어를 따로 생각하다

Isaac Lab 3.0은 물리 엔진에 종속되는 구현을 분리했다. 사용자가 `isaaclab.assets.Articulation`을 생성하면 활성 물리 백엔드에 맞는 실제 구현이 선택된다. PhysX, Newton, OvPhysX가 같은 기능을 전부 지원하는 것은 아니므로, 이름만 바꾸면 모든 센서와 로봇이 똑같이 실행된다고 가정하면 안 된다. [다중 백엔드 공식 설명](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/overview/core-concepts/multi_backend_architecture.rst)

| 구성 | 답하는 질문 | 이 장의 선택 |
|---|---|---|
| 물리 백엔드 | 접촉과 관절 운동을 누가 계산하는가? | PhysX |
| 렌더러 | 카메라나 장면 영상을 누가 계산하는가? | Isaac Sim의 RTX 경로 |
| Visualizer | 사람이 어느 창으로 장면을 보는가? | `--viz kit` |

Newton을 사용하는 Kit-less 구성에서는 Isaac Sim 없이도 지원되는 학습 작업을 실행할 수 있다. 이 장은 GUI와 RTX 센서를 단계적으로 다룰 예정이므로 Isaac Sim을 설치하고 PhysX 경로를 사용한다. Kit-less를 설치가 빠른 동등 대체 경로로 취급해서 같은 명령에 섞지 않는다. [Kit-less 설치 범위](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/kitless_installation.rst)

3.0에서 알아둘 실행 옵션은 다음과 같다.

```bash
# GUI로 장면을 볼 때 추가하다.
--viz kit

# 설정 파일에 뷰어가 있어도 모든 뷰어를 명시적으로 끄다.
--viz none

# 카메라 센서 실습에 필요한 렌더링 기능을 켜다.
--enable_cameras
```

위 블록은 옵션 설명이며, 세 줄을 단독 명령으로 실행하지 않는다. 완전한 실행 명령은 09단계부터 나온다. `--viz`를 생략하면 `SimulationCfg.visualizer_cfgs` 설정을 따른다. 설정된 뷰어가 없으면 창 없이 실행한다. 기존 `--headless`는 3.0에서 deprecated 상태이며, 이 튜토리얼은 `--viz none`을 사용한다. [3.0 이전 안내](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/migration/migrating_to_isaaclab_3-0.rst)

**통과 기준:** “창을 끄는 것”과 “카메라 센서 렌더링을 끄는 것”이 다른 설정임을 이해한다.

<a id="step-03"></a>

## 03단계. Ubuntu와 GPU의 실행 조건을 확인하다

아래 명령은 터미널에서 한 줄씩 실행한다. 오류가 발생하면 해당 명령의 출력부터 해결하고 다음 단계로 진행한다.

```bash
cat /etc/os-release
uname -m
ldd --version
free -h
df -h "$HOME"
nvidia-smi
```

확인할 값은 `Ubuntu 24.04`, `x86_64`, GLIBC 2.35 이상, 충분한 RAM·SSD 공간, 정상적으로 인식된 NVIDIA GPU이다. pip 방식의 GLIBC 조건은 [Isaac Lab 설치 문서](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/pip_installation.rst)에 명시되어 있다.

Isaac Sim 6.0.1의 공식 x86_64 요구 사양은 최소 RAM 32GB, SSD 50GB, RTX 4080급 GPU와 VRAM 16GB이다. 실제 학습에서는 환경 복제와 센서 때문에 RAM·VRAM이 더 필요하며, 자산 캐시와 체크포인트를 저장할 SSD 공간도 별도로 확보한다. RT 코어가 없는 A100·H100은 이 Isaac Sim GUI/RTX 실습 경로의 지원 GPU가 아니다. [Isaac Sim 6.0.1 요구 사양](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)

드라이버 숫자를 읽을 때는 문서의 목적도 확인한다. 고정된 Lab 태그의 문서에는 Linux `580.95.05` 이상 권장이 적혀 있고, 확인한 Isaac Sim 6.0.1 요구 사양 페이지는 Linux 테스트 드라이버로 `595.58.03`을 표시한다. 이미 정상인 드라이버를 단순히 숫자를 맞추기 위해 다운그레이드하지 않는다. 새 설치에서는 해당 GPU를 지원하는 NVIDIA Production Branch 드라이버와 Isaac Sim의 호환성 검사를 함께 확인한다. [태그의 드라이버 안내](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/index.rst)

GPU 이름과 메모리만 간단히 기록하려면 다음 명령을 사용한다.

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv
```

`nvidia-smi`부터 실패한다면 Python 패키지를 반복 설치해도 해결되지 않는다. 먼저 운영체제의 드라이버 설치·재부팅·GPU 인식 상태를 확인한다. 메모리가 부족하면 처음부터 수천 개 환경을 실행하지 않고, 이후 문서의 최소 환경 수부터 시작한다.

**통과 기준:** GPU를 인식하고, GUI/RTX 실행을 위한 공식 사양을 충족하며, 저장할 경로에 설치와 로그를 위한 공간이 있다.

<a id="step-04"></a>

## 04단계. 두 저장소와 Python 환경을 준비하다

이 튜토리얼은 공식 Isaac Lab 소스와 한국어 실습 저장소를 서로 다른 디렉터리에 둔다. 경로를 매번 추측하지 않도록 두 변수를 사용한다.

```bash
export ISAACLAB_ROOT="$HOME/IsaacLab"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
```

새 터미널을 열면 변수와 가상환경 활성화 상태가 사라질 수 있다. 이후 실습을 재개할 때는 이 두 줄과 환경 활성화 명령을 다시 실행한다.

필요한 기본 도구를 설치한다.

```bash
sudo apt update
sudo apt install -y git curl build-essential cmake python3.12 python3.12-venv
```

공식 저장소는 지정한 태그만 가져온다.

```bash
git clone --branch v3.0.0-beta2.patch1 --single-branch \
  https://github.com/isaac-sim/IsaacLab.git "$ISAACLAB_ROOT"

git -C "$ISAACLAB_ROOT" describe --tags --exact-match
git -C "$ISAACLAB_ROOT" rev-parse HEAD
```

첫 번째 확인 명령은 `v3.0.0-beta2.patch1`을 출력해야 한다. 태그를 clone했을 때의 detached HEAD 안내는 고정된 버전을 읽고 실행하기 위한 정상 상태이다. 공식 소스를 다른 브랜치로 바꿀 필요가 없다.

한국어 실습 파일은 `IsaacLab` 브랜치에서 가져온다. README의 시작 명령으로 이미 내려받았다면 아래 `git clone`은 생략하고 브랜치 확인 명령만 실행한다.

```bash
git clone --branch IsaacLab --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git "$TUTORIAL_ROOT"

git -C "$TUTORIAL_ROOT" branch --show-current
```

결과는 `IsaacLab`이어야 한다. 이미 같은 이름의 디렉터리가 있다면 `git clone`은 덮어쓰지 않고 중단한다. 이 경우 다른 작업이 들어 있는 디렉터리를 삭제하거나 강제로 reset하지 말고, 두 환경 변수를 사용하지 않는 새 디렉터리로 지정한 뒤 해당 clone 명령을 실행한다. 이 문서의 뒤쪽 명령은 지정한 변수 경로를 따른다.

uv는 Python 환경과 패키지를 관리하는 도구이다. [uv 공식 설치 방법](https://docs.astral.sh/uv/getting-started/installation/)에 따라 설치하고, 현재 터미널의 PATH를 반영한다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

Isaac Lab 디렉터리 안에 Python 3.12 전용 가상환경을 만든다.

```bash
cd "$ISAACLAB_ROOT"
uv venv --python 3.12 --seed env_isaaclab
source "$ISAACLAB_ROOT/env_isaaclab/bin/activate"
uv pip install --upgrade pip

python --version
python -c 'import sys; print(sys.executable)'
```

`--seed`는 가상환경에 pip도 포함한다. Isaac Lab 설치 도구가 사용하는 기능이므로 생략하지 않는다. Python 경로는 지정한 `IsaacLab/env_isaaclab/bin/python` 아래여야 한다. 시스템 Python에 `sudo pip install`을 실행하지 않는다. [고정 태그의 가상환경 준비](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/include/pip_python_virtual_env.rst)

**통과 기준:** 한국어 저장소의 현재 브랜치가 `IsaacLab`이고, 공식 저장소의 태그와 Python 3.12 가상환경이 확인된다.

<a id="step-05"></a>

## 05단계. Isaac Sim과 Isaac Lab을 설치하고 버전을 기록하다

04단계의 가상환경이 활성화된 터미널에서 진행한다. 패키지 다운로드 중 디스크가 꽉 차지 않는지 확인하며, 앞 명령이 성공한 뒤 다음 명령을 실행한다.

```bash
cd "$ISAACLAB_ROOT"
source "$ISAACLAB_ROOT/env_isaaclab/bin/activate"

uv pip install "isaacsim[all,extscache]==6.0.1.0" \
  --extra-index-url https://pypi.nvidia.com \
  --index-strategy unsafe-best-match \
  --prerelease=allow

uv pip install -U torch==2.10.0 torchvision==0.25.0 \
  --index-url https://download.pytorch.org/whl/cu128

./isaaclab.sh --install
```

첫 명령은 Isaac Sim과 확장 캐시를 설치한다. 두 번째 명령은 x86_64용 CUDA 12.8 계열 PyTorch wheel을 설치한다. 마지막 명령은 clone한 Isaac Lab 소스를 설치한다. `uv pip install isaaclab`만 실행하면 이 장에서 사용할 공식 `scripts/tutorials`와 학습 예제 소스까지 확보하는 흐름이 아니므로, 소스 clone과 설치를 모두 수행한다. [공식 pip 설치](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/pip_installation.rst)

3.0의 `--install` 기본값은 핵심 패키지, 선택 모듈 `mimic`·`teleop`, 자동 추가 기능 `newton`·`rl`·`visualizer`이다. 초보 과정에서 이후 장의 의존성이 빠지지 않도록 기본 설치를 사용한다. 개발자가 범위를 좁힐 때는 `./isaaclab.sh -i 'rl[rsl-rl],visualizer[kit]'`처럼 선택할 수 있지만, 이 선택 설치만으로 모방학습·원격조작의 모든 의존성이 설치되었다고 판단하면 안 된다. [3.0 설치 명령 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/cli/__init__.py)

설치된 배포 패키지와 현재 Python 경로를 확인한다. 이 블록은 터미널에 통째로 붙여 넣는다.

```bash
python - <<'PY'
import os
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

print("Python:", sys.version)
print("Executable:", sys.executable)
for package in ("isaacsim", "isaaclab", "torch", "torchvision"):
    print(package, version(package))
assert sys.version_info[:2] == (3, 12)
assert version("isaacsim") == "6.0.1.0"
extension_file = Path(os.environ["ISAACLAB_ROOT"]) / "source/isaaclab/config/extension.toml"
with extension_file.open("rb") as file:
    source_package_version = tomllib.load(file)["package"]["version"]
assert version("isaaclab") == source_package_version
assert version("torch").split("+")[0] == "2.10.0"
assert version("torchvision").split("+")[0] == "0.25.0"
PY
```

소스 설치의 Isaac Lab 패키지 버전은 릴리스 태그와 별도로 관리된다. 이 태그의 `setup.py`는 `extension.toml`의 내부 버전 `6.1.14`를 사용하므로, `version("isaaclab")`가 `3.0.0`으로 시작해야 한다는 검사를 넣지 않는다. 위 코드는 현재 checkout의 내부 패키지 버전과 비교하며, 릴리스 식별은 04단계의 Git 태그·커밋으로 수행한다. 값이 다르면 다른 Python 환경이나 다른 checkout을 설치했는지 점검한다. [패키지 설정](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/setup.py), [내부 버전](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/config/extension.toml)

다음은 CUDA 계산을 별도의 짧은 Python 프로세스에서 확인하는 명령이다.

```bash
python - <<'PY'
import torch

print("torch:", torch.__version__)
print("wheel CUDA:", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())
assert torch.cuda.is_available(), "가상환경에서 CUDA GPU를 사용할 수 없다."
print("GPU:", torch.cuda.get_device_name(0))
x = torch.tensor([1.0, 2.0, 3.0], device="cuda:0")
print("tensor check:", (x * x).sum().item())
PY
```

마지막 출력은 `14.0`이어야 한다. 이 검사는 PyTorch의 CUDA 사용만 확인한다. Kit GUI, RTX 렌더러, 로봇 물리 검사를 대신하지 않는다. 이후 스크립트 안에서는 AppLauncher보다 먼저 불필요하게 torch나 Omniverse 모듈을 import하지 않는다.

성공한 환경의 기록은 다음과 같이 남긴다.

```bash
mkdir -p "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/setup"
python -m pip freeze > "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/setup/packages.txt"
git -C "$ISAACLAB_ROOT" rev-parse HEAD > "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/setup/isaaclab-commit.txt"
nvidia-smi > "$TUTORIAL_ROOT/isaaclab_tutorial/outputs/setup/gpu.txt"
```

`pip freeze`에는 editable 설치의 로컬 경로도 들어갈 수 있다. 이 파일은 현재 환경을 설명하는 기록이며, 다른 컴퓨터에서 무조건 그대로 설치되는 독립적인 lockfile은 아니다.

**통과 기준:** 버전 확인의 assertion이 통과하고, CUDA tensor 계산이 `14.0`을 출력한다.

<a id="step-06"></a>

## 06단계. Isaac Sim GUI를 처음 실행하다

먼저 Isaac Lab 스크립트 없이 Isaac Sim 앱 자체를 실행한다. 설치와 GUI 문제를 구분하기 위해 필요한 단계이다.

```bash
source "$ISAACLAB_ROOT/env_isaaclab/bin/activate"
isaacsim
```

처음 실행하면 NVIDIA 이용 약관 확인과 확장 다운로드가 나타날 수 있다. 약관 내용을 확인한 뒤 동의 여부를 직접 선택한다. 최초 실행은 확장 준비와 셰이더 컴파일 때문에 오래 걸릴 수 있으므로, 터미널 로그와 네트워크·디스크 상태를 살펴본다. 창이 아직 준비되지 않았다고 동일한 앱을 여러 개 띄우면 메모리 부족을 악화시킬 수 있다. [공식 첫 실행 확인](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/include/pip_verify_isaacsim.rst)

기본 창이 열리면 `File > New`로 빈 장면을 만든다. 빈 장면에서는 반사할 물체와 조명이 없으므로 검은 화면만 보일 수 있다. 이후 단계에서 바닥과 조명을 추가하여 렌더링 자체의 문제와 빈 장면을 구분한다.

앱이 종료되거나 GPU 오류가 발생하면 터미널의 첫 관련 오류를 확인한다. 마지막의 종료 메시지만으로 원인을 판단하지 않는다. 최소한 다음 정보를 함께 기록한다.

```text
Ubuntu 버전:
GPU와 VRAM:
NVIDIA 드라이버:
Isaac Sim 배포 버전:
처음 발생한 Error 문장:
Error 바로 앞뒤의 로그:
```

**통과 기준:** GUI 창이 열리고, 메뉴와 패널을 클릭할 수 있으며, 종료 후 동일 명령으로 다시 실행할 수 있다.

<a id="step-07"></a>

## 07단계. Viewport, Stage, Property를 연결해서 읽다

다시 `isaacsim`을 실행하고 `File > New`로 시작한다. 창 배치는 저장된 레이아웃에 따라 달라질 수 있으므로 패널 이름을 기준으로 찾는다. [Isaac Sim GUI 안내](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_user_interface.html)

| 패널 | 보는 내용 | 가장 먼저 해 볼 일 |
|---|---|---|
| Viewport | 선택한 시점에서 렌더링한 장면 | 상자를 선택하고 시점을 움직인다 |
| Stage | 장면 prim의 계층과 경로 | `/World` 아래의 상자를 찾는다 |
| Property | 선택한 prim의 변환·재질·물리 속성 | 상자의 Translate 값을 숫자로 바꾼다 |
| Content Browser | 파일과 자산 | 저장한 USD 파일의 위치를 확인한다 |
| Console 또는 터미널 로그 | 경고·오류·Python 출력 | 물체가 안 보일 때 로딩 오류를 찾는다 |

`Create > Shape > Cube`를 선택한다. Stage에서 생성된 Cube를 선택하고 Property의 Transform 항목을 확인한다. Viewport에서 선택한 물체와 Stage에서 선택한 prim은 같은 장면 요소를 가리킨다. 부모 Xform을 선택했는지, 실제 형상 prim을 선택했는지에 따라 Property 항목이 달라질 수 있다.

단축키는 마우스가 Viewport에 있을 때 연습한다. Property의 숫자 입력 칸에 커서가 있다면 키가 글자로 입력될 수 있다.

| 조작 | 결과 |
|---|---|
| Stage에서 대상 선택 후 `F` | 선택한 물체를 중심으로 시점을 맞춘다 |
| `W` | 물체 이동 도구를 선택한다 |
| `E` | 물체 회전 도구를 선택한다 |
| `R` | 물체 크기 조절 도구를 선택한다 |
| `Esc` | 물체 선택을 해제한다 |
| 마우스 오른쪽 버튼을 누른 채 `W/A/S/D` | 시점을 전후좌우로 이동한다 |

같은 `W`라도 오른쪽 버튼을 누르고 있느냐에 따라 물체 이동 도구와 카메라 전진이라는 다른 동작을 한다. 카메라 이동은 물체의 Translate를 바꾸지 않는다. Viewport의 시점만 바꾼 뒤 Property 값이 그대로인지 확인한다. [공식 단축키](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/gui/reference_keyboard_shortcuts.html), [prim에 시점 맞추기](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/openusd_tuning_tutorials/tutorial_03_inspect_asset.html)

로봇을 처음 불러왔을 때도 같은 순서를 사용한다. 먼저 Stage에서 로봇 prim이 존재하는지 찾고, 그다음 `F`로 프레임을 맞추며, 마지막으로 Property에서 위치와 visibility를 확인한다. 화면이 비어 있다는 이유만으로 자산을 여러 번 추가하면 중복 로봇이 겹쳐 생길 수 있다.

**통과 기준:** 상자를 선택하고, 시점만 이동하는 조작과 상자 자체를 이동하는 조작을 구분할 수 있다.

<a id="step-08"></a>

## 08단계. 단위·USD·Play/Pause/Stop을 이해하다

Isaac Lab의 위치와 길이는 기본적으로 미터 단위로 다룬다. USD의 장면에는 단위와 위쪽 축에 대한 메타데이터가 있으며, 이 튜토리얼은 미터와 Z-up을 기준으로 한다. 외부 자산을 들여올 때는 크기가 100배나 1,000배 차이 나는지 먼저 확인한다.

USD는 단순한 메시 파일보다 많은 것을 담는다. prim의 계층, 로봇의 참조, 재질, 카메라, 조명, 물리 속성 등을 하나의 장면으로 구성할 수 있다. `/World/Robot`은 로컬 파일 경로가 아니라 USD Stage 안의 prim 경로이다. Xform은 자식 요소를 함께 이동시키는 데 쓰는 변환 노드이다.

GUI에서 현재 장면을 읽어 보려면 `Window > Script Editor`를 열고 아래 코드를 한 번 실행한다. 이 블록은 **이미 실행 중인 Isaac Sim의 Script Editor 전용**이다.

```python
import omni.usd
from pxr import UsdGeom

stage = omni.usd.get_context().get_stage()
print("metersPerUnit:", UsdGeom.GetStageMetersPerUnit(stage))
print("upAxis:", UsdGeom.GetStageUpAxis(stage))
for prim in stage.Traverse():
    print(str(prim.GetPath()), prim.GetTypeName())
```

예상되는 핵심 값은 `1.0`, `Z`이다. 물리 실습을 시작하기 전에 장면 단위가 맞는지 확인한다. 이미 완성된 외부 장면에서 숫자만 강제로 바꾸면 물체가 의도한 크기로 자동 보정되는 것은 아니므로, 단위가 다르면 새 미터 기준 장면에서 실습한다. [공식 GUI·Script Editor 기초](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/quickstart_isaacsim.html)

### GUI에서 시뮬레이션을 실행하다

빈 장면에서 바닥과 조명을 추가한다.

1. `Create > Physics > Ground Plane`을 선택한다.
2. `Create > Lights > Distant Light`를 선택한다.
3. 기존 Cube를 선택하고 Property의 Transform에서 Translate를 `(0, 0, 1)`, Rotate를 `(0, 0, 0)`, Scale을 `(0.2, 0.2, 0.2)`로 입력한다. 한 축만 바꾸지 않도록 세 칸을 모두 확인한다.
4. `Play`를 누르고 상자가 움직이는지 살펴본다.

시각 형상만 추가한 상자는 중력의 영향을 받지 않는다. 떨어지는 실습을 하려면 선택한 상자의 Property에서 `Add > Physics > Rigid Body with Colliders Preset`을 추가한다. GUI의 Stop 상태에서 초기 위치를 바닥 위로 정하고, 옆에서 보았을 때 상자 아래에 빈 공간이 있는지 확인한 뒤 Play로 낙하와 접촉을 관찰한다. Rigid Body는 동역학 계산에, Collider는 충돌 계산에 필요하다는 점을 구분한다. [공식 기본 사용 튜토리얼](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/introduction/quickstart_isaacsim.html)

| 조작 | 의미 | 이 장에서의 용도 |
|---|---|---|
| Play | 시간 진행을 시작하거나 재개하다 | 낙하와 접촉을 관찰하다 |
| Pause | 진행을 잠깐 멈추다 | 현재 자세를 살펴보다 |
| Stop | 시뮬레이션 실행을 끝내고 편집 상태로 돌아가다 | 초기 배치와 물리 구성을 수정하다 |

중력이 켜진 상자 중심을 바닥 안에 두면 시작 순간 겹침을 해소하는 큰 힘이 생길 수 있다. 로봇에서도 링크가 바닥이나 서로의 collider 안에서 시작하면 튀거나 무너질 수 있다. “처음 배치가 겹치지 않는가”를 이 단계부터 습관적으로 확인한다.

장면을 `File > Save As`로 `isaaclab_tutorial/outputs/gui_scene.usda`에 저장한다. Python 학습 루프와 정책 가중치는 이 USD 저장으로 함께 보존되지 않는다. GUI에서 배치한 자산과 학습 코드를 별도로 관리해야 하는 이유이다.

**중요:** 여기까지의 Play/Stop 실습은 `isaacsim`으로 직접 띄운 편집 앱에서 수행한다. 다음 단계의 Isaac Lab standalone 스크립트는 Python이 실행 상태를 관리한다. AppLauncher는 실수로 물리 상태를 무효화하지 않도록 Stop 버튼을 숨긴다. Lab 실습에서 초기화가 필요하면 문서의 reset 코드나 프로그램 재실행을 사용한다. [AppLauncher 구현](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/source/isaaclab/isaaclab/app/app_launcher.py)

**통과 기준:** 시각 형상, 강체, 충돌체의 차이를 설명하고, 바닥 위에서 시작한 상자가 낙하 후 바닥에 놓이는 것을 확인한다.

<a id="step-09"></a>

## 09단계. 공식 첫 예제로 AppLauncher의 실행 순서를 배우다

GUI 실습 앱을 종료한 뒤 아래 명령을 실행한다. 터미널 두 개에서 Isaac Sim을 동시에 띄우지 않으면 GPU 메모리 사용량을 비교하기 쉽다.

```bash
source "$ISAACLAB_ROOT/env_isaaclab/bin/activate"
cd "$ISAACLAB_ROOT"

./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py \
  --device cuda:0 --viz kit
```

이 예제는 이름 그대로 빈 Stage를 만든다. `[INFO]: Setup complete...`가 나오고 GUI가 반응하지만 Viewport가 검게 보이는 것이 공식 예제의 예상 결과이다. 조명도 물체도 없는 예제를 카메라 블랙아웃 오류로 분류하지 않는다. [공식 실행 확인](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/docs/source/setup/installation/include/src_verify_isaaclab.rst)

명령의 각 부분은 다음과 같다.

| 부분 | 의미 |
|---|---|
| `./isaaclab.sh` | 현재 Isaac Lab 설치의 실행 래퍼 |
| `-p` | 이어지는 Python 파일을 실행하다 |
| `scripts/tutorials/00_sim/create_empty.py` | 공식 첫 번째 장면 예제 |
| `--device cuda:0` | 첫 번째 CUDA GPU를 사용하다 |
| `--viz kit` | Kit GUI 뷰어를 열다 |

실제 파일을 열어 다음 구조를 찾는다.

```bash
sed -n '1,180p' "$ISAACLAB_ROOT/scripts/tutorials/00_sim/create_empty.py"
```

핵심 순서는 아래와 같다. 이 코드는 구조 설명용이며, 실행은 위의 공식 파일을 사용한다.

```python
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# 시뮬레이터와 관련된 import는 앱 시작 뒤에 수행하다.
from isaaclab.sim import SimulationCfg, SimulationContext

sim = SimulationContext(SimulationCfg(dt=0.01))
sim.set_camera_view([2.5, 2.5, 2.5], [0.0, 0.0, 0.0])
sim.reset()
while simulation_app.is_running():
    sim.step()
simulation_app.close()
```

`AppLauncher`는 옵션을 읽고 필요한 앱과 확장을 준비한다. `SimulationContext`는 시간 간격과 물리 실행을 관리한다. `sim.reset()`은 만들어 둔 장면을 실행 가능한 상태로 초기화하고, `sim.step()`은 정해진 시간 간격으로 시뮬레이션을 한 단계 진행한다. 시간 간격 `dt=0.01`은 물리 시뮬레이션 시간 기준 0.01초이며, 컴퓨터의 벽시계로 정확히 0.01초가 걸린다는 의미는 아니다. [공식 create_empty.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/00_sim/create_empty.py)

아직 실행 중인 GUI의 Script Editor에 위 standalone 코드를 다시 붙여 넣지 않는다. 이미 앱이 있는데 새 AppLauncher를 만드는 흐름은 이 예제의 사용 방식이 아니다. 종료는 창을 닫거나 해당 터미널에서 `Ctrl+C`를 사용한다.

**통과 기준:** GUI가 반응하고 Setup 메시지가 나오며, 빈 Viewport가 이 예제의 의도임을 설명할 수 있다.

<a id="step-10"></a>

## 10단계. 중간 프로젝트 1 — 조명이 있는 첫 장면을 만들다

**목표:** 회색 바닥 위에 파란 상자, 빨간 구, 초록 원뿔을 만들고, 같은 위치·색·시점으로 재실행한다. 이 프로젝트는 외부 로봇 USD나 HDR 이미지가 필요하지 않다. 설치된 앱만으로 생성하는 도형을 사용하므로 자산 다운로드 문제를 장면 렌더링 문제와 분리해서 확인할 수 있다.

실행 파일은 [p01_lit_scene.py](../examples/p01_lit_scene.py)이다. 먼저 수정 없이 실행한다.

```bash
cd "$ISAACLAB_ROOT"
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p01_lit_scene.py" \
  --device cuda:0 --viz kit --rendering_mode balanced
```

화면에는 바닥과 세 가지 색의 도형이 보여야 한다. Stage에는 `/World/Floor`, `/World/Light`, `/World/Cube`, `/World/Sphere`, `/World/Cone`이 있어야 한다. 화면에서 하나가 가려지면 Stage에서 해당 prim을 선택하고 `F`로 시점을 맞춘다.

### 설정 객체와 생성 호출을 구분하다

파일의 바닥 생성 코드를 살펴본다.

```python
floor_cfg = sim_utils.CuboidCfg(
    size=(4.0, 4.0, 0.1),
    collision_props=CollisionBaseCfg(collision_enabled=True),
    visual_material=sim_utils.PreviewSurfaceCfg(
        diffuse_color=(0.35, 0.35, 0.35),
        roughness=0.8,
        metallic=0.0,
    ),
)
floor_cfg.func("/World/Floor", floor_cfg, translation=(0.0, 0.0, -0.05))
```

`CuboidCfg`는 만들 물체의 크기·재질·충돌 속성을 보관하는 설정이다. 마지막의 `func(...)`를 호출할 때 실제 prim을 생성한다. 바닥 두께는 0.1m, 중심 높이는 -0.05m이므로 바닥 윗면은 정확히 z=0이다. 이 계산을 하지 않고 바닥 중심을 z=0에 두면 윗면이 z=0.05가 되어 이후 물체의 배치 기준이 달라진다.

바닥에는 collider만 있고 rigid body가 없다. 움직이는 동적 물체가 아니라 고정된 충돌체로 만든 것이다. 현재의 상자·구·원뿔은 시각 도형이므로 중력으로 움직이지 않는다. 로봇 물리 검증은 다음 장에서 수행한다.

### 조명과 재질을 직접 지정하다

```python
light_cfg = sim_utils.DomeLightCfg(
    intensity=1500.0,
    color=(1.0, 1.0, 1.0),
)
light_cfg.func("/World/Light", light_cfg)

cube_cfg = sim_utils.CuboidCfg(
    size=(0.4, 0.4, 0.4),
    visual_material=sim_utils.PreviewSurfaceCfg(
        diffuse_color=(0.15, 0.35, 0.8),
        roughness=0.8,
        metallic=0.0,
    ),
)
cube_cfg.func("/World/Cube", cube_cfg, translation=(0.0, 0.0, 0.2))
```

상자 높이는 0.4m이고 중심 높이는 0.2m이므로 바닥에 놓인다. 양의 조명 강도, 불투명한 재질, 지나치게 반짝이지 않는 표면을 먼저 사용한다. 화려한 유리나 반사 재질을 시작 장면에 넣으면 조명·노출·반사 노이즈 중 무엇을 보고 있는지 구분하기 어려워진다.

`DomeLightCfg`에는 외부 HDR 텍스처 경로를 지정하지 않는다. 검게 보일 때 “다운로드한 환경맵이 안 열렸는가”라는 추가 원인을 줄인다. 완전히 같은 RGB 픽셀을 모든 GPU에서 보장하는 설정은 아니며, 렌더링 품질은 실제 장비에서 확인한다. 공식 도형·조명 API의 사용 흐름은 [spawn_prims.py](https://github.com/isaac-sim/IsaacLab/blob/v3.0.0-beta2.patch1/scripts/tutorials/00_sim/spawn_prims.py)를 참고했다.

### 시점과 시뮬레이션 초기화를 지정하다

```python
sim = sim_utils.SimulationContext(
    sim_utils.SimulationCfg(
        dt=1.0 / 120.0,
        device=args_cli.device,
        physics=PhysxCfg(),
    )
)
sim.set_camera_view([2.8, 2.8, 2.2], [0.0, 0.0, 0.25])
design_scene()
sim.reset()
```

첫 번째 좌표는 뷰어 카메라 위치이고, 두 번째 좌표는 바라볼 목표이다. 카메라가 바닥 아래나 상자 내부에서 시작하지 않도록 눈에 보이는 장면 바깥에서 바라보게 한다. `design_scene()`을 `sim.reset()`보다 먼저 호출하여 필요한 prim을 만든 다음 물리를 초기화한다.

### 작게 바꾸고 다시 확인하다

프로그램을 종료한 뒤 파일의 값 하나만 바꾸고 재실행한다. 먼저 상자의 파란색을 `(0.8, 0.6, 0.1)`로 바꿔 노란색이 되는지 본다. 다음에는 원뿔의 x 위치를 `0.7`에서 `1.0`으로 바꿔 옆으로 이동하는지 확인한다. 한 번에 조명·크기·시점을 전부 바꾸면 원인을 추적하기 어렵다.

정해진 횟수로 짧게 실행하려면 다음 명령을 사용한다.

```bash
./isaaclab.sh -p "$TUTORIAL_ROOT/isaaclab_tutorial/examples/p01_lit_scene.py" \
  --device cuda:0 --viz kit --steps 600 --rendering_mode balanced
```

`--steps 600`은 600회 step 호출 뒤 종료한다. 기본 `--steps 0`은 창을 닫을 때까지 실행한다. 이 스크립트가 출력하는 “장면 생성 완료”는 필수 prim이 만들어졌다는 의미이며, 영상의 밝기·노이즈 검사를 자동 통과했다는 뜻은 아니다.

| 항목 | 직접 확인할 기준 | 실패하면 먼저 볼 곳 |
|---|---|---|
| 구성 | 바닥·조명·도형 3개가 Stage에 존재하다 | prim 생성 오류와 중복 경로 |
| 시점 | 세 도형이 바닥 위에 보이다 | 카메라 위치, 선택 대상, `F` |
| 밝기 | 세 도형의 색과 경계가 구분되다 | `/World/Light`, 조명 강도, 렌더링 모드 |
| 형상 | 물체가 찢어지거나 비정상적으로 늘어나지 않다 | 도형 크기와 부모 transform |
| 재실행 | 종료 후 다시 실행했을 때 같은 배치이다 | 코드에 반영하지 않은 GUI 편집 |

프로젝트 기록에는 사용한 GPU와 드라이버, 실행 명령, 화면 캡처, 수정한 값, 통과하지 못한 항목을 남긴다. 창 없이 실행한 로그만으로 “렌더링 검증 완료”라고 적지 않는다.

**프로젝트 1 완료 기준:** 기본 실행에서 조명과 세 도형을 확인하고, 색 한 곳과 위치 한 곳을 수정한 뒤 같은 결과를 재현한다. 다음 장에서는 이 정적인 장면에 실제 강체와 관절 로봇을 추가한다.
