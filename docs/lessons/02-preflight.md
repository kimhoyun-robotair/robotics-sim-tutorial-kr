# 02. 설치 전에 컴퓨터와 저장 경로를 점검하다

## 목표와 준비

Ubuntu 24.04 LTS가 설치된 x86_64 데스크톱에서 GPU, 드라이버, 메모리, 디스크를 확인한다. 이 과정은 설치 오류를 미리 줄이는 단계이며, GPU 모델명만 보고 모든 센서 실습이 정상 동작한다고 판단하지 않는다. 이후 실습은 **Isaac Sim 6.0.1 + ROS 2 Jazzy + PhysX 기반의 작은 장면**에서 시작한다.

아직 저장소가 없다면 이 브랜치를 지정해 내려받는다. 이미 내려받았다면 해당 폴더에서 경로 설정만 실행한다.

```bash
git clone --branch IsaacSim6.0.1 --single-branch \
  https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr.git
cd robotics-sim-tutorial-kr
export TUTORIAL_ROOT="$PWD"
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
mkdir -p "$TUTORIAL_ROOT/artifacts/scenes" "$TUTORIAL_ROOT/artifacts/logs"
printf '실습 폴더: %s\n설치 폴더: %s\n' "$TUTORIAL_ROOT" "$ISAAC_SIM_PATH"
```

`TUTORIAL_ROOT`는 **이 저장소의 최상위 폴더**이고, `ISAAC_SIM_PATH`는 **Isaac Sim 실행 파일을 풀어 놓을 폴더**이다. 두 경로를 섞지 않는다. `export`는 현재 터미널과 그 터미널에서 시작한 앱에 값을 전달한다. 새 터미널을 열었다면 실제 경로에 맞게 다시 설정한다.

## 사양 표를 실제 출력과 비교하다

6.0.1 공식 요구사항의 x86_64 최소 항목은 RAM 32 GB, SSD 50 GB, RTX 4080, VRAM 16 GB이다. Linux 테스트 드라이버는 `595.58.03`으로 표시된다. 이는 “이 번호보다 높으면 무조건 정상”이라는 의미가 아니라 공식 테스트 조합이다. RT Core가 없는 A100/H100은 지원 GPU가 아니다. [공식 요구사항](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)

```bash
cat /etc/os-release
uname -m
free -h
df -h "$HOME" "$TUTORIAL_ROOT"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free \
  --format=csv
```

다음 항목을 읽는다.

| 명령 | 읽을 항목 | 확인 기준 |
| --- | --- | --- |
| `cat /etc/os-release` | `VERSION_ID` | `24.04`인지 확인하다 |
| `uname -m` | CPU 명령어 집합 | 이 과정에서는 `x86_64`를 사용하다 |
| `free -h` | `Mem`의 total, available | RAM 총량과 현재 여유량을 구분하다 |
| `df -h` | `Avail` | 다운로드·압축 해제·실습 결과를 둘 공간을 확보하다 |
| `nvidia-smi` | GPU, driver, total, free | NVIDIA GPU 인식 여부와 VRAM 여유를 확인하다 |

공식 설치 최소 용량과 학습 결과 저장 공간은 별개이다. 카메라 프레임이나 rosbag을 저장하기 시작하면 데이터가 빠르게 늘어나므로, 이 실습에서는 결과 폴더를 따로 둔다. 여러 카메라를 동시에 켜기 전에 하나씩 추가하며 메모리 사용량을 확인한다.

## 드라이버와 그래픽 세션을 확인하다

```bash
printf '세션: %s\nDISPLAY: %s\n' "${XDG_SESSION_TYPE:-unknown}" "${DISPLAY:-unset}"
nvidia-smi
```

첫 출력은 현재 로그인 세션의 종류를 확인하는 용도이다. SSH 터미널에서 `DISPLAY`가 비어 있을 수 있으며, 이 경우 로컬 데스크톱용 GUI 명령을 그대로 실행하면 창이 뜨지 않는다. 원격 학습은 공식 Livestream 경로를 별도로 구성한다. 이 단계에서는 실제 화면이 연결된 Ubuntu 데스크톱을 기준으로 진행한다.

`nvidia-smi`가 실패하면 Isaac Sim을 반복해서 재설치하지 않는다. 드라이버 로드, 재부팅 여부, Secure Boot의 모듈 서명 상태 등 운영체제 수준의 원인을 먼저 해결한다. 드라이버 설치 방식은 해당 장비의 관리 정책을 따른다. 이미 정상 동작하는 다른 개발 환경이 있는 장비에 임의의 드라이버 제거 명령을 실행하지 않는다.

## 점검 기록을 남기다

```bash
{
  date --iso-8601=seconds
  cat /etc/os-release
  uname -m
  free -h
  df -h "$TUTORIAL_ROOT"
  nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv
} > "$TUTORIAL_ROOT/artifacts/logs/machine-baseline.txt" 2>&1
```

나중에 검은 화면이나 실행 종료를 겪었을 때 이 파일과 현재 출력을 비교한다. 드라이버와 GPU 정보는 재현 조건의 일부이다. 파일에 “정상”이라고 수동으로 써 넣는 대신 명령 결과를 그대로 남긴다.

## 예상 결과와 실패 시 확인

운영체제, 아키텍처, NVIDIA GPU가 확인되고 설치 공간이 확보되어야 한다. 최소 사양을 충족해도 첫 실행의 셰이더 컴파일이나 온라인 자산 다운로드에는 시간이 걸릴 수 있다. 진행 중인 로그와 GPU 사용량을 보고 기다릴지 결정한다. GPU 메모리가 이미 대부분 사용 중이면 다른 그래픽 앱을 정리하고 작은 장면부터 다시 확인한다.

설치 후에는 6.0.1의 Compatibility Checker도 실행한다. 공식 문서는 standalone 설치에서 제공하는 Compatibility Checker 실행 방법을 안내한다. 실행 스크립트 이름은 설치 폴더에서 실제 존재 여부를 확인하고 [Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_workstation.html)의 해당 항목을 따른다. 체크 결과가 정상이어도 로봇 충돌·카메라 영상 검증을 대신하지는 못한다.

## 작은 과제

점검 파일에서 RAM 총량, VRAM 총량, 드라이버 버전 세 항목을 찾아 학습 기록에 적는다. “화면은 뜨지만 카메라 네 대를 켜면 종료된다”라는 상황에서 어떤 항목을 먼저 비교할지 설명한다.

## 공식 6.0.1 자료

- [Isaac Sim Requirements](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)
- [Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_workstation.html)
- [Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/manual_livestream_clients.html)

이전: [01. 플랫폼 개념](01-platforms.md) · 다음: [03. 설치와 첫 실행](03-installation.md)
