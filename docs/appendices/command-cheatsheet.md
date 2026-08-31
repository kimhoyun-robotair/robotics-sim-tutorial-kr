# Isaac Sim 5.1 · ROS 2 Jazzy 명령 치트시트

이 문서는 Ubuntu 24.04 LTS x86_64, Isaac Sim 5.1.0 독립형 패키지, ROS 2 Jazzy를 기준으로 자주 쓰는 명령과 GUI 조작을 한곳에 모은다. 먼저 [시스템 요구사항](../02-getting-started/01-system-requirements.md), [워크스테이션 설치](../02-getting-started/02-workstation-installation.md), [ROS 2 설정](../02-getting-started/03-ros2-jazzy-setup.md)을 끝낸 뒤 사용한다.

## 터미널 표기와 경로 가정

| 표기 | 의미 | 시작 상태 |
|---|---|---|
| `[HOST]` | Ubuntu 호스트 셸 | ROS를 source하지 않아도 되는 시스템·Docker 명령용이다. |
| `[SIM]` | Isaac Sim 전용 셸 | 원칙적으로 `/opt/ros/jazzy/setup.bash`를 source하지 않는다. |
| `[ROS]` | 시스템 ROS 2 Jazzy 셸 | `source /opt/ros/jazzy/setup.bash`를 실행한 상태이다. |
| `[CTR]` | 실행 중인 Isaac Sim 컨테이너 안의 셸 | 기본 작업 경로는 `/isaac-sim`이다. |
| `[USD]` | OpenUSD CLI가 `PATH`에 설치된 셸 | Isaac Sim ZIP이 모든 OpenUSD CLI를 `PATH`에 제공한다고 가정하지 않는다. |

워크스테이션 패키지는 `~/isaacsim`에 풀었다고 가정한다. 다른 위치에 설치했다면 모든 경로를 실제 위치로 바꾼다.

> **5.1 제약을 먼저 확인하다.** Isaac Sim 5.1 문서는 현재 지원 종료 상태의 고정 버전 문서이다. 5.1은 Omniverse Launcher 대신 독립형 ZIP과 `isaac-sim.selector.sh`를 사용한다. Ubuntu 24.04의 시스템 ROS 2 Jazzy는 Python 3.12이지만 Isaac Sim 내부 Jazzy 라이브러리는 번들 Python 3.11용이다. 두 Python 환경의 패키지를 섞지 않는다. 또한 RTX 코어가 없는 A100·H100은 Isaac Sim 렌더링용 GPU로 지원하지 않는다.

## 1. 설치와 하드웨어 확인

### 호스트 빠른 점검

| 터미널 | 목적 | 명령 | 통과 기준 |
|---|---|---|---|
| `[HOST]` | OS·아키텍처 | `cat /etc/os-release; uname -m` | Ubuntu 24.04, `x86_64`가 보인다. |
| `[HOST]` | GPU·드라이버 | `nvidia-smi` | 지원 NVIDIA RTX GPU와 드라이버가 오류 없이 보인다. 5.1 문서의 테스트 Linux 드라이버는 `580.65.06`이다. |
| `[HOST]` | Vulkan 장치 | `vulkaninfo --summary` | NVIDIA GPU가 Vulkan 물리 장치로 보인다. 명령이 없으면 `sudo apt install vulkan-tools`로 설치한다. |
| `[HOST]` | 메모리·디스크 | `free -h; df -h "$HOME"` | 설치·캐시·장면을 위한 여유 공간이 있다. |
| `[HOST]` | 설치 파일 | `test -x ~/isaacsim/isaac-sim.sh && test -x ~/isaacsim/python.sh && echo OK` | `OK`가 출력된다. |
| `[SIM]` | 공식 호환성 검사 | `cd ~/isaacsim && ./isaac-sim.compatibility_check.sh` | 검사 창의 필수 항목이 통과한다. 통과는 목표 장면의 성능 보장이 아니다. |
| `[SIM]` | 무창 호환성 검사 | `cd ~/isaacsim && ./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window` | 서버에서도 검사가 끝나고 치명 오류가 없다. |

GPU 상태를 계속 관찰할 때 사용한다.

```bash
# [HOST]
watch -n 1 nvidia-smi
```

## 2. Isaac Sim 실행

| 터미널 | 사용 목적 | 명령 |
|---|---|---|
| `[SIM]` | App Selector | `cd ~/isaacsim && ./isaac-sim.selector.sh` |
| `[SIM]` | 전체 GUI | `cd ~/isaacsim && ./isaac-sim.sh` |
| `[SIM]` | 사용자 설정을 초기화해 GUI 실행 | `cd ~/isaacsim && ./isaac-sim.sh --reset-user` |
| `[SIM]` | 자세한 로그와 함께 실행 | `cd ~/isaacsim && ./isaac-sim.sh -v` |
| `[SIM]` | 활성화 가능한 extension 목록 | `cd ~/isaacsim && ./isaac-sim.sh --list-exts` |
| `[SIM]` | 시작과 함께 extension 활성화 | `cd ~/isaacsim && ./isaac-sim.sh --enable isaacsim.ros2.bridge` |
| `[SIM]` | 셰이더 캐시 사전 준비 | `cd ~/isaacsim && ./warmup.sh` |
| `[SIM]` | WebRTC 스트리밍 앱 | `cd ~/isaacsim && ./isaac-sim.streaming.sh` |

첫 실행은 셰이더 컴파일 때문에 수 분 이상 걸릴 수 있다. `warmup.sh`도 시스템에 따라 15분 이상 걸릴 수 있으므로 멈췄다고 단정하지 않고 CPU·GPU·로그를 함께 확인한다. `isaac-sim.streaming.sh`는 원격 WebRTC 화면을 위한 실행기이며, GUI 없는 배치 계산 전체를 뜻하는 일반적인 `headless` 실행기와 같지 않다.

### Standalone Python과 진짜 headless 스크립트

Isaac Sim API를 import하기 전에 `SimulationApp`을 만들고 마지막에 닫는다.

```python
# /tmp/minimal_headless.py
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

# Kit가 시작된 뒤 omni.*, isaacsim.* 모듈을 import하다.
from pxr import Usd

stage = Usd.Stage.CreateInMemory()
stage.DefinePrim("/World", "Xform")
print(stage.GetRootLayer().ExportToString())

simulation_app.update()
simulation_app.close()
```

```bash
# [SIM]
cd ~/isaacsim
./python.sh /tmp/minimal_headless.py
```

| 터미널 | 목적 | 명령 |
|---|---|---|
| `[SIM]` | 번들 Python 버전 | `cd ~/isaacsim && ./python.sh -c 'import sys; print(sys.version)'` |
| `[SIM]` | pxr import 확인 | `cd ~/isaacsim && ./python.sh -c 'from pxr import Usd; print(Usd.GetVersion())'` |
| `[SIM]` | 스크립트 인자 전달 | `cd ~/isaacsim && ./python.sh /절대/경로/job.py --headless` |

마지막 명령의 `--headless`는 자동으로 창을 끄는 마법 옵션이 아니다. 스크립트가 해당 인자를 해석해 `SimulationApp({"headless": True})`를 생성해야 한다.

## 3. 캐시·설정·로그

| 항목 | 기본 경로 |
|---|---|
| Kit 로그 | `~/.nvidia-omniverse/logs/Kit/Isaac-Sim/` |
| 셰이더·Kit 캐시 | `~/.cache/ov/Kit/` |
| Isaac Sim 사용자 설정·데이터 | `~/.local/share/ov/data/Kit/Isaac-Sim/` |
| 독립형 설치 | `~/isaacsim/` |

| 터미널 | 목적 | 명령·주의 |
|---|---|---|
| `[SIM]` | 지원 스크립트로 캐시 삭제 | Isaac Sim을 닫고 `cd ~/isaacsim && ./clear_caches.sh`를 실행한다. 다음 실행에서 셰이더를 다시 만들므로 오래 걸릴 수 있다. |
| `[SIM]` | 캐시만 지우고 실행 | `cd ~/isaacsim && ./isaac-sim.sh --clear-cache` |
| `[SIM]` | 사용자 설정 초기화 | `cd ~/isaacsim && ./isaac-sim.sh --reset-user` |
| `[HOST]` | 최근 로그 찾기 | `find ~/.nvidia-omniverse/logs/Kit/Isaac-Sim -type f -printf '%T@ %p\n' 2>/dev/null \| sort -nr \| head` |
| `[HOST]` | 로그의 ERROR/WARN 검색 | `rg -n -i 'error\|warn\|fatal\|traceback' ~/.nvidia-omniverse/logs/Kit/Isaac-Sim/` |
| `[HOST]` | 캐시 크기 확인 | `du -sh ~/.cache/ov/Kit ~/.local/share/ov/data/Kit/Isaac-Sim 2>/dev/null` |

`--clear-data`는 사용자 데이터를 지우는 범위가 더 넓다. 빠른 진단 명령처럼 습관적으로 실행하지 말고, 필요한 파일을 백업한 뒤 공식 Setup Tips의 의미를 확인하고 사용한다.

최근 로그 하나를 따라갈 때 사용한다.

```bash
# [HOST]
latest_isaac_log=$(find ~/.nvidia-omniverse/logs/Kit/Isaac-Sim \
  -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-)
test -n "$latest_isaac_log" && tail -F "$latest_isaac_log"
```

## 4. ROS 2 Jazzy와 Bridge

### 두 터미널을 분리하다

동일 PC에서 Fast DDS를 쓸 때의 권장 시작점이다. 두 터미널의 `ROS_DOMAIN_ID`를 동일하게 맞춘다.

```bash
# [SIM] 시스템 ROS를 source하지 않은 새 터미널
# 아래 명령이 ROS 경로를 출력하면 이 터미널을 닫고 깨끗한 셸을 열다.
printenv | rg '^(ROS_DISTRO|AMENT_PREFIX_PATH|COLCON_PREFIX_PATH)=' || true
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
cd ~/isaacsim
./isaac-sim.sh
```

```bash
# [ROS]
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 doctor --report
```

Isaac Sim 5.1은 호스트에 다른 ROS 환경이 source되지 않았으면 내부 Jazzy 라이브러리를 기본으로 사용할 수 있다. 명시적으로 내부 라이브러리를 지정해야 할 때만 다음을 새 `[SIM]` 터미널에서 한 번 실행한다.

```bash
# [SIM]
export isaac_sim_package_path="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}${isaac_sim_package_path}/exts/isaacsim.ros2.bridge/jazzy/lib"
"${isaac_sim_package_path}/isaac-sim.sh"
```

같은 터미널에서 위 블록을 반복 실행하면 `LD_LIBRARY_PATH`가 중복된다. 새 터미널을 사용한다. GUI에서는 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 찾아 활성 상태를 확인한다. 예전 문서의 `omni.isaac.ros2_bridge` ID를 5.1 명령에 그대로 쓰지 않는다.

### 그래프·토픽·메시지

| 터미널 | 확인할 것 | 명령 |
|---|---|---|
| `[ROS]` | 노드 목록 | `ros2 node list` |
| `[ROS]` | 토픽과 타입 | `ros2 topic list -t` |
| `[ROS]` | publisher/subscriber와 QoS | `ros2 topic info /clock -v` |
| `[ROS]` | 한 메시지만 보기 | `ros2 topic echo /clock --once` |
| `[ROS]` | 발행 주기 | `ros2 topic hz /camera/image_raw` |
| `[ROS]` | 대역폭 | `ros2 topic bw /camera/image_raw` |
| `[ROS]` | 메시지 정의 | `ros2 interface show geometry_msgs/msg/Twist` |
| `[ROS]` | 한 번 발행 | `ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.1}}'` |
| `[ROS]` | 노드 상세 | `ros2 node info /노드_이름` |
| `[ROS]` | 서비스 목록 | `ros2 service list -t` |

`/clock`이나 센서 토픽이 보이지 않을 때는 Isaac Sim Timeline이 **Play** 상태인지, Action Graph의 publisher가 실행되는지, Bridge extension이 활성인지 차례로 확인한다.

### QoS

먼저 실제 endpoint QoS를 확인한 뒤 subscriber 측을 맞춘다.

```bash
# [ROS]
ros2 topic info /camera/image_raw -v
ros2 topic echo /camera/image_raw --once \
  --qos-reliability best_effort \
  --qos-durability volatile
```

Jazzy CLI의 정확한 지원 옵션은 다음으로 확인한다.

```bash
# [ROS]
ros2 topic echo --help | rg 'qos|reliability|durability'
```

QoS가 맞지 않으면 토픽 이름과 타입이 맞아도 데이터를 받지 못할 수 있다. 이미지·LiDAR 같은 고주기 센서에는 `best_effort`가 흔하지만, 실제 Action Graph 또는 publisher 설정을 기준으로 판단한다.

### TF

| 터미널 | 목적 | 명령 |
|---|---|---|
| `[ROS]` | 동적 TF 원문 | `ros2 topic echo /tf --once` |
| `[ROS]` | 정적 TF 원문 | `ros2 topic echo /tf_static --once` |
| `[ROS]` | 두 frame 관계 추적 | `ros2 run tf2_ros tf2_echo map base_link` |
| `[ROS]` | TF 트리 파일 생성 | `ros2 run tf2_tools view_frames` |

`tf2_tools`가 없다면 `[HOST] sudo apt install ros-jazzy-tf2-tools`로 설치한다. `map`, `base_link`는 실제 frame ID로 바꾼다.

### Discovery·Domain 진단

| 터미널 | 목적 | 명령 |
|---|---|---|
| `[SIM]`, `[ROS]` | 핵심 환경 비교 | `printenv \| rg '^(ROS_DISTRO\|RMW_IMPLEMENTATION\|ROS_DOMAIN_ID\|FASTRTPS_DEFAULT_PROFILES_FILE)='` |
| `[ROS]` | ROS daemon 갱신 | `ros2 daemon stop && ros2 daemon start` |
| `[ROS]` | RMW 구현 확인 | `ros2 doctor --report \| rg -i 'middleware\|rmw'` |

여러 PC나 Docker 사이에서 Fast DDS discovery profile을 사용할 때는 모든 관련 터미널에 같은 파일을 지정한다.

```bash
# [SIM], [ROS], 필요하면 [CTR]
export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/IsaacSim-ros_workspaces/fastdds.xml"
test -r "$FASTRTPS_DEFAULT_PROFILES_FILE" && echo "Fast DDS profile: OK"
```

경로만 같게 쓰는 것이 아니라 각 머신·컨테이너에서 실제 파일을 읽을 수 있어야 한다.

## 5. USD CLI와 Python

OpenUSD CLI는 USD 파일 구조와 composition을 빠르게 확인하는 도구이다. `usdchecker` 통과가 Isaac Sim의 PhysX collider, articulation, 센서 설정까지 올바르다는 뜻은 아니다.

### CLI 존재 확인

```bash
# [USD]
command -v usdcat usdchecker usdview usdtree usdresolve
```

명령이 없다면 별도로 빌드·설치한 OpenUSD toolset의 `bin`을 `PATH`에 추가한다. Isaac Sim ZIP 내부에서 이름이 같은 실행 파일을 추측해 직접 호출하지 않는다.

| 터미널 | 목적 | 명령 |
|---|---|---|
| `[USD]` | ASCII로 내용 출력 | `usdcat robot.usd` |
| `[USD]` | layer metadata만 출력 | `usdcat -l robot.usd` |
| `[USD]` | USDA → USDC | `usdcat robot.usda -o robot.usdc` |
| `[USD]` | USDC → USDA | `usdcat robot.usdc -o robot.usda` |
| `[USD]` | composition flatten | `usdcat root.usd --flatten -o flattened.usda` |
| `[USD]` | 기본 검증 | `usdchecker robot.usd` |
| `[USD]` | 상세 검증 | `usdchecker -v robot.usd` |
| `[USD]` | stage 트리 | `usdtree robot.usd` |
| `[USD]` | asset 경로 resolve | `usdresolve ./robot.usd` |
| `[USD]` | 두 stage 비교 | `usddiff before.usd after.usd` |
| `[USD]` | 대화형 보기 | `usdview warehouse.usd --select /World/Robot` |

`--flatten`은 reference·payload·layer 구조를 하나의 결과로 굽는다. 디버깅 또는 전달용 복사본에 사용하고 원본 authoring 구조의 대체물로 무심코 덮어쓰지 않는다.

Isaac Sim 번들 Python에서 prim을 한눈에 나열한다.

```bash
# [SIM]
cd ~/isaacsim
./python.sh - <<'PY'
from pxr import Usd

stage = Usd.Stage.Open("/절대/경로/scene.usd")
if not stage:
    raise RuntimeError("USD stage를 열지 못했다")
for prim in stage.Traverse():
    print(prim.GetPath(), prim.GetTypeName())
PY
```

URDF·Xacro·MJCF 변환은 단순 CLI 파일 포맷 변환이 아니다. 링크·joint·material·actuator 의미를 importer/exporter가 재해석한다. [USD 도구와 Python](../01-foundations/03-usd-tools-and-python.md) 및 변환 장을 따라 결과의 scale, axis, articulation root, drive, collider를 반드시 검증한다.

## 6. 컨테이너

Isaac Sim 5.1 컨테이너는 Linux에서 NVIDIA Container Toolkit이 설정되어 있어야 한다. EULA를 읽고 동의한 경우에만 `ACCEPT_EULA=Y`를 전달한다.

### 이미지와 GPU 확인

```bash
# [HOST]
docker pull nvcr.io/nvidia/isaac-sim:5.1.0
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

### 최소 임시 셸

```bash
# [HOST]
docker run --name isaac-sim --rm -it --gpus all \
  --network=host \
  -e ACCEPT_EULA=Y \
  --entrypoint bash \
  nvcr.io/nvidia/isaac-sim:5.1.0
```

컨테이너 안에서 검사하거나 스트리밍 앱을 시작한다.

```bash
# [CTR]
cd /isaac-sim
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window

# WebRTC 스트리밍이 필요할 때만 실행하다.
./runheadless.sh -v
```

`runheadless.sh`는 WebRTC 스트리밍 앱 진입점이다. 배치 standalone 스크립트는 컨테이너 안에서 `/isaac-sim/python.sh /작업/job.py`처럼 별도로 실행한다. 5.1 aarch64 컨테이너에서는 livestreaming이 지원되지 않는다.

### 캐시를 유지하는 공식 UID 방식의 핵심

```bash
# [HOST]
mkdir -p ~/docker/isaac-sim/{cache/main/{ov,warp},cache/computecache,config,data/{documents,Kit},logs,pkg}
sudo chown -R 1234:1234 ~/docker/isaac-sim
```

공식 Container Installation 예제의 volume mapping과 `-u 1234:1234`를 함께 사용한다. 일부 volume만 연결하면 캐시·로그·설정이 컨테이너 종료 시 사라질 수 있다. 소유권 변경 대상이 정확히 `~/docker/isaac-sim`인지 확인한 뒤 실행한다.

| 터미널 | 목적 | 명령 |
|---|---|---|
| `[HOST]` | 실행 컨테이너 | `docker ps --filter name=isaac-sim` |
| `[HOST]` | 최근 로그 | `docker logs --tail 200 isaac-sim` |
| `[HOST]` | 자원 사용량 | `docker stats isaac-sim` |
| `[HOST]` | 스트리밍 포트 | `ss -lntup \| rg '(:49100\|:47998)'` |
| `[HOST]` | 중지 | `docker stop isaac-sim` |

기본 WebRTC 접속에는 TCP `49100`, UDP `47998` 경로가 필요하다. 동일한 호스트에서 둘 이상의 스트리밍 인스턴스를 동시에 띄우는 구성은 기본 포트 충돌을 별도로 해결해야 한다.

## 7. 자주 쓰는 GUI 메뉴

| 목적 | 메뉴·위치 | 확인할 것 |
|---|---|---|
| Extension 관리 | **Window > Extensions** | `isaacsim.ros2.bridge` 등 ID와 활성 상태를 확인한다. |
| Content Browser | **Window > Browsers > Content** | 로컬·Nucleus·asset 경로에서 USD를 찾는다. |
| Action Graph | **Window > Graph Editors > Action Graph** | 노드, 연결, 실행 tick과 ROS publisher를 편집한다. |
| Script Editor | **Window > Script Editor** | GUI가 이미 실행 중인 context에서 짧은 Python을 실험한다. |
| Console | **Window > Console** | extension 로딩, Python 예외, asset resolve 오류를 확인한다. |
| Physics Scene | **Create > Physics > Simulation Scene** | 중력, solver, time step의 stage 설정을 확인한다. |
| Ground Plane | **Create > Physics > Ground Plane** | 바닥 collider가 생겼는지 Stage와 Property에서 확인한다. |
| 예제 | **Window > Examples > Robotics Examples** | 예제를 먼저 실행해 설치·센서·ROS 경로를 검증한다. |
| collider 시각화 | Viewport의 **Show By Type > Physics > Colliders > All** | render mesh와 충돌 형상의 불일치를 찾는다. |

메뉴 이름은 workspace 배치나 활성 extension에 따라 일부 다르게 보일 수 있다. 메뉴가 없으면 먼저 **Window > Extensions**에서 관련 extension이 활성인지 확인한다.

### Viewport·편집 단축키

| 입력 | 동작 | 입력 | 동작 |
|---|---|---|---|
| `W` | 이동 도구 | `E` | 회전 도구 |
| `R` | 크기 조절 도구 | `Esc` | 선택 해제 |
| `F` | 선택 prim에 프레임 맞추기 | `H` | 선택 prim 표시·숨김 |
| `Ctrl+S` | stage 저장 | `Ctrl+O` | stage 열기 |
| `Ctrl+D` | 선택 prim 복제 | `Delete` | 선택 prim 삭제 |
| `Ctrl+G` | 선택 prim 그룹화 | `Space` | Timeline 재생·일시정지 |
| `RMB`+`W/A/S/D` | 카메라 비행 | `RMB`+`Q/E` | 카메라 아래·위 이동 |
| `MMB` 드래그 | 카메라 평행 이동 | 휠 | 확대·축소 |
| `F7` | UI 표시 전환 | `F10` | 스크린샷 |
| `F11` | 전체 화면 |  |  |

텍스트 입력란에 포커스가 있으면 단축키가 Viewport로 전달되지 않을 수 있다. 삭제·복제 전에 Stage에서 선택한 prim 경로를 확인한다.

## 8. 고장 진단 명령

### 60초 진단 순서

| 순서 | 터미널 | 명령 | 해석 |
|---:|---|---|---|
| 1 | `[HOST]` | `nvidia-smi` | GPU가 없거나 드라이버 오류이면 앱보다 먼저 호스트를 고친다. |
| 2 | `[HOST]` | `df -h "$HOME"; free -h` | 디스크 부족·메모리 압박을 배제한다. |
| 3 | `[SIM]` | `cd ~/isaacsim && ./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window` | 공식 검사 결과를 확보한다. |
| 4 | `[HOST]` | `pgrep -af 'kit\|isaac-sim'` | 중복·좀비 프로세스를 찾는다. 보인다는 이유만으로 강제 종료하지 않는다. |
| 5 | `[HOST]` | `journalctl -k -b \| rg -i 'nvrm\|nvidia\|xid\|oom' \| tail -n 100` | GPU Xid 또는 OOM 흔적을 찾는다. |
| 6 | `[HOST]` | `rg -n -i 'error\|fatal\|traceback' ~/.nvidia-omniverse/logs/Kit/Isaac-Sim/` | Kit·extension·Python 실패 지점을 찾는다. |
| 7 | `[ROS]` | `ros2 node list; ros2 topic list -t` | ROS graph가 실제로 발견되는지 확인한다. |
| 8 | `[SIM]`, `[ROS]` | `echo "domain=$ROS_DOMAIN_ID rmw=$RMW_IMPLEMENTATION"` | 양쪽 domain과 RMW를 비교한다. |

### 증상별 한 줄 명령

| 증상 | 터미널 | 명령 | 다음 판단 |
|---|---|---|---|
| GPU가 갑자기 사라짐 | `[HOST]` | `nvidia-smi; lspci -nnk \| rg -A3 -i 'vga\|3d controller'` | PCI 장치와 kernel driver를 비교한다. |
| Vulkan이 잘못된 GPU를 봄 | `[HOST]` | `vulkaninfo --summary` | NVIDIA 장치가 없으면 Vulkan ICD·드라이버를 점검한다. |
| GUI가 시작 중 멈춤 | `[SIM]` | `cd ~/isaacsim && ./isaac-sim.sh -v` | 동시에 최근 Kit 로그를 따라간다. |
| 레이아웃·설정이 깨짐 | `[SIM]` | `cd ~/isaacsim && ./isaac-sim.sh --reset-user` | 사용자 UI 설정을 초기화한 결과를 비교한다. |
| 셰이더·캐시 의심 | `[SIM]` | `cd ~/isaacsim && ./clear_caches.sh` | 앱을 닫고 실행한다. 다음 시작은 느리다. |
| Extension ID 확인 | `[SIM]` | `cd ~/isaacsim && ./isaac-sim.sh --list-exts \| rg 'ros2\|sensor\|replicator'` | 5.1의 실제 ID를 사용한다. |
| ROS 토픽은 있으나 무데이터 | `[ROS]` | `ros2 topic info /토픽 -v; ros2 topic hz /토픽` | Timeline, publisher, QoS를 확인한다. |
| ROS discovery가 오래된 상태 | `[ROS]` | `ros2 daemon stop && ros2 daemon start` | 다시 `ros2 node list`로 확인한다. |
| TF frame 누락 | `[ROS]` | `ros2 run tf2_ros tf2_echo 부모_frame 자식_frame` | frame 이름·연결·publisher를 확인한다. |
| Docker GPU 실패 | `[HOST]` | `docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi` | 실패하면 Isaac Sim보다 Container Toolkit을 먼저 점검한다. |
| Docker 앱 종료 | `[HOST]` | `docker inspect isaac-sim --format '{{.State.ExitCode}} {{.State.Error}}'` | exit code와 `docker logs`를 함께 본다. |
| WebRTC 접속 실패 | `[HOST]` | `ss -lntup \| rg '(:49100\|:47998)'` | 프로세스 listen, 방화벽, NAT, 클라이언트 주소를 확인한다. |

문제 보고에는 최소한 `nvidia-smi`, Compatibility Checker 결과, 재현 명령, 최근 Kit 로그, 장면 규모, ROS 환경 변수를 함께 남긴다. 비밀번호·토큰·사설 서버 주소는 공유 전에 제거한다.

## 출처

- [Isaac Sim 5.1.0 — Isaac Sim Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [Isaac Sim 5.1.0 — Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_workstation.html)
- [Isaac Sim 5.1.0 — Setup Tips](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_faq.html)
- [Isaac Sim 5.1.0 — Standalone Python](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
- [Isaac Sim 5.1.0 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1.0 — ROS 2 QoS](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html)
- [Isaac Sim 5.1.0 — ROS 2 Transform Trees and Odometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_tf.html)
- [Isaac Sim 5.1.0 — Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)
- [Isaac Sim 5.1.0 — Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)
- [Isaac Sim 5.1.0 — User Interface Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_user_interface.html)
- [Isaac Sim 5.1.0 — Keyboard Shortcuts Reference](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/gui/reference_keyboard_shortcuts.html)
- [Isaac Sim 5.1.0 — Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Isaac Sim 5.1.0 — USD Tools](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/usd_tools.html)
- [OpenUSD — USD Toolset](https://openusd.org/release/toolset.html)
- [ROS 2 Jazzy — Understanding ROS 2 Topics](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
