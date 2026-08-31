# 설치·실행·GUI·ROS 2 문제 해결

문제 해결의 목표는 옵션을 무작정 바꾸는 것이 아니라 **처음 실패한 계층을 찾는 것**이다. 다음 순서로 범위를 좁히다.

```text
하드웨어/드라이버 → Vulkan/Kit → Isaac Sim 앱 → 에셋/확장 → Stage/PhysX → ROS 2/DDS
```

위 계층이 실패한 상태에서 아래 계층을 디버깅하지 않다. 예를 들어 Vulkan 장치가 열리지 않는데 ROS 토픽부터 확인하는 것은 도움이 되지 않는다.

## 진단 기록 먼저 만들기

다음 결과를 텍스트 파일에 기록하면 재현과 도움 요청이 쉬워지다. 비밀번호, 토큰, 사설 URL과 사용자 경로의 민감 정보는 공유 전에 지우다.

```bash
mkdir -p ~/isaacsim-diagnostics

{
  date -Is
  cat /etc/os-release
  uname -a
  nvidia-smi
  nvidia-smi --query-gpu=name,driver_version,memory.total \
    --format=csv,noheader
  free -h
  df -h "$HOME"
  printf 'DISPLAY=%s\n' "$DISPLAY"
  printf 'XDG_SESSION_TYPE=%s\n' "$XDG_SESSION_TYPE"
} > ~/isaacsim-diagnostics/system.txt 2>&1

cd ~/isaacsim
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window \
  > ~/isaacsim-diagnostics/compatibility-check.txt 2>&1
```

`compatibility-check.txt`가 생겼다는 사실과 검사가 통과했다는 사실은 다르다. 종료 코드와 마지막 결과를 확인하다.

```bash
tail -n 40 ~/isaacsim-diagnostics/compatibility-check.txt
```

## 로그 위치와 읽는 방법

워크스테이션 공식 경로는 다음과 같다.

| 데이터 | 경로 |
|---|---|
| Isaac Sim 로그 | `~/.nvidia-omniverse/logs/Kit/Isaac-Sim` |
| 셰이더 캐시 | `~/.cache/ov/Kit` |
| 사용자 설정 | `~/.local/share/ov/data/Kit/Isaac-Sim` |

최근 로그 파일을 찾다.

```bash
find ~/.nvidia-omniverse/logs/Kit/Isaac-Sim -type f \
  -printf '%T@ %p\n' | sort -nr | head -n 10
```

목록에서 최신 로그 경로를 골라 읽다.

```bash
tail -n 200 <LATEST_LOG_PATH>
grep -nEi 'fatal|error|failed|out.of.(memory|device)|vulkan' \
  <LATEST_LOG_PATH> | head -n 100
```

마지막 오류만 보지 말고 그보다 앞에서 처음 발생한 로드 실패를 찾다. 후속 오류 수십 개가 하나의 누락 라이브러리에서 파생될 수 있다.

컨테이너는 host bind mount를 사용했다면 `~/docker/isaac-sim/logs`를 확인하다.

```bash
docker ps --filter name=isaac-sim
docker logs --tail 200 isaac-sim
find ~/docker/isaac-sim/logs -type f -printf '%T@ %p\n' \
  | sort -nr | head
```

## 증상 1: `nvidia-smi`가 실패하다

```bash
command -v nvidia-smi
nvidia-smi
lsmod | grep '^nvidia'
journalctl -k -b | grep -iE 'nvrm|nvidia|xid' | tail -n 100
```

가능한 원인은 드라이버 미설치, 커널 업데이트 뒤 모듈 빌드 실패, Secure Boot 서명 문제, 컨테이너에서 GPU 미전달 등이다. Isaac Sim을 재설치해도 커널 드라이버는 고쳐지지 않는다.

드라이버를 변경하기 전에 다음을 기록하다.

```bash
ubuntu-drivers devices
dpkg -l | grep -E 'nvidia-(driver|dkms)|libnvidia' | sed -n '1,120p'
```

apt 패키지와 NVIDIA `.run` 설치를 섞지 않다. 새 GPU 또는 현 드라이버 문제 때문에 버전을 바꾼다면 Isaac Sim 요구사항의 테스트 버전과 NVIDIA Production Branch 권장을 먼저 확인하다.

## 증상 2: `nvidia-smi`는 되지만 Vulkan/Kit가 시작하지 못하다

```bash
vulkaninfo --summary
printenv | grep -E '^(VK_|__GLX_|__NV_)' || true
```

다음을 확인하다.

- Vulkan 장치 목록에 NVIDIA RTX GPU가 있는가?
- 오래된 `VK_ICD_FILENAMES`가 특정 JSON을 강제로 가리키지 않는가?
- 하이브리드 그래픽에서 iGPU나 소프트웨어 렌더러만 선택되지 않았는가?
- 다중 GPU라면 `nvidia-smi -L`과 Vulkan 열거 결과가 일치하는가?

환경 변수 강제 설정이 원인으로 의심되면 현재 셸을 오염시키지 말고 새 터미널에서 테스트하다. 시스템 Vulkan 파일을 임의 삭제하지 않다. Omniverse Linux 가이드에 따르면 다중 GPU Vulkan 열거에는 충분히 최신 Xorg도 필요하다.

Compatibility Checker를 창 없이 실행해 Kit 최소 앱까지 시험하다.

```bash
cd ~/isaacsim
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window
```

## 증상 3: 첫 실행이 빈 창이거나 매우 느리다

5.1 공식 워크스테이션 문서는 첫 실행이 셰이더 캐시 때문에 5~10분 걸릴 수 있다고 안내하다. 클라우드 예제의 `warmup.sh`는 15분 이상 걸릴 수도 있다. 다음 세 가지를 동시에 보며 기다릴지 판단하다.

```bash
watch -n 1 nvidia-smi
```

1. 실행 터미널 또는 앱 로그의 timestamp가 계속 증가하다.
2. CPU/GPU 또는 디스크 작업이 계속되다.
3. 동일한 fatal 오류가 반복되지 않다.

로그가 갱신되지 않고 같은 위치에서 반복 실패하면 앱을 정상 종료한 뒤 사용자 설정을 무시해 보다.

```bash
cd ~/isaacsim
./isaac-sim.sh --reset-user
```

그래도 캐시 손상의 구체적 징후가 있으면 앱을 모두 종료하고 공식 스크립트를 사용하다.

```bash
pgrep -af 'kit|isaac-sim'
cd ~/isaacsim
./clear_caches.sh
./warmup.sh
```

`clear_caches.sh` 뒤 첫 실행은 다시 느려지다. 캐시 삭제를 습관적으로 반복하면 원인을 가리고 시간만 늘다.

## 증상 4: GUI 레이아웃이나 패널이 사라지다

1. `Window` 메뉴에서 Stage, Property, Content, Console 등을 다시 열다.
2. 특정 패널만 닫혔는지, 전체 UI가 숨겨졌는지 확인하다. `F7`은 UI 가시성을 전환하다.
3. `F11` 전체 화면 상태를 확인하다.
4. 사용자 설정 문제라면 `./isaac-sim.sh --reset-user`로 비교하다.

`--reset-user`로 정상화되면 GPU 문제보다 사용자 레이아웃·확장 설정 문제일 가능성이 높다.

## 증상 5: Extensions에서 기능을 찾을 수 없다

- 검색창의 `@feature` 등 자동 필터를 제거하다.
- 이름뿐 아니라 새 5.1 확장 ID로 검색하다. 예: `isaacsim.ros2.bridge`.
- 4.5부터 많은 `omni.isaac.*` ID가 `isaacsim.*`로 바뀌었다. 오래된 블로그의 ID를 그대로 가정하지 않다.
- Console에서 extension dependency 또는 registry 접속 오류를 확인하다.
- `--list-exts`로 로컬 확장을 나열할 수 있다.

```bash
cd ~/isaacsim
./isaac-sim.sh --list-exts > ~/isaacsim-diagnostics/extensions.txt 2>&1
grep -i 'ros2\|urdf\|physics' ~/isaacsim-diagnostics/extensions.txt
```

필요한 확장을 발견했다고 모두 Autoload하지 말고, 하나씩 Enable해 재현하다.

## 증상 6: Content Browser 에셋이 비어 있거나 로드되지 않는다

5.1의 기본 에셋 루트는 다음 온라인 경로를 사용하다.

```text
https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1
```

Isaac Sim Assets Browser의 Gear 메뉴에서 `Check Default Assets Root Path`를 실행하고 로그에서 다음 형태를 확인하다.

```text
Isaac Sim assets found: <asset-root>
```

인터넷·프록시·TLS 검사 정책으로 막힐 수 있다. 브라우저에 목록이 안 보인다고 GPU 문제로 결론내리지 않다. 폐쇄망이라면 공식 Local Assets Packs를 내려받아 풀고 다음처럼 명시적으로 에셋 루트를 지정하다.

```bash
cd ~/isaacsim
./isaac-sim.sh \
  --/persistent/isaac/asset_root/default="/home/<USER>/isaacsim_assets/Assets/Isaac/5.1"
```

실제 `<USER>`와 압축 해제 구조로 바꾸고, 경로 끝이 `Assets/Isaac/5.1`인지 확인하다.

## 증상 7: `ERROR_OUT_OF_DEVICE_MEMORY` 또는 렌더 크래시

```bash
nvidia-smi --query-compute-apps=pid,used_memory,process_name \
  --format=csv
nvidia-smi
```

다음 순서로 워크로드를 줄이다.

1. 불필요한 다른 GPU 프로세스를 정상 종료하다.
2. 카메라/RTX 센서 수와 render product 해상도를 줄이다.
3. 동시에 활성화한 annotator와 viewport를 줄이다.
4. 에셋 인스턴싱과 장면 최적화를 검토하다.
5. 큰 해상도를 여러 작은 배치로 나누다.

5.1 알려진 이슈에는 VRAM을 넘는 viewport 해상도로 `ERROR_OUT_OF_DEVICE_MEMORY`가 난 뒤 해상도만 낮추면 크래시할 수 있다고 적혀 있다. OOM 이후에는 장면을 저장할 수 있는 상태인지 판단하고 앱을 재시작한 뒤 낮은 설정으로 다시 열다. 이미 불안정해진 프로세스에서 결과 저장이 반드시 안전하다고 가정하지 않다.

## 증상 8: 물체가 떨어지지 않거나 바닥을 통과하다

| 현상 | 우선 확인 |
|---|---|
| 공중에 정지 | Timeline Play, Rigid Body API, 중력 |
| 바닥 통과 | Cube Collider와 Ground Plane Collider |
| 일부만 움직임 | Rigid Body가 부모 Xform에 있는지 확인 |
| 얇은 벽 통과 | timestep, 속도, CCD |
| 폭발·떨림 | 초기 관통, 질량비, 관성, joint drive gain |
| 시각과 충돌 불일치 | Collider 표시와 approximation |

Viewport의 표시 메뉴에서 `Physics > Colliders > All` 계열을 켜다. Property에 Physics 섹션이 없으면 선택한 Mesh의 부모·자식을 이동하며 API가 실제 어느 prim에 적용되었는지 확인하다.

Physics Scene이 없다면 기본 60 steps/s가 적용되다. 결과 재현을 위해 Scene을 만들고 값을 명시하다. 설정을 바꾸기 전에 Stage 단위, up axis와 실제 물체 크기를 확인하다.

## 증상 9: ROS 2 토픽이 보이지 않는다

먼저 토픽 publisher가 실제로 실행 중인지 확인하다. 빈 Stage와 정지된 Timeline에서는 기대 토픽이 없을 수 있다.

### Isaac Sim 터미널

```bash
printenv | grep -E '^(ROS_DISTRO|RMW_IMPLEMENTATION|ROS_DOMAIN_ID|FASTRTPS_DEFAULT_PROFILES_FILE)='
```

Ubuntu 24.04 기본 구성에서는 시스템 ROS를 source하지 않은 새 터미널에서 Isaac Sim을 시작해 내장 Jazzy/Python 3.11을 사용하다. 시스템 `/opt/ros/jazzy`의 Python 3.12 경로가 Isaac Sim 로그에 섞이지 않았는지 확인하다.

### 외부 ROS 터미널

```bash
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0

ros2 daemon stop
ros2 daemon start
ros2 node list
ros2 topic list
```

다음을 양쪽에서 맞추다.

- 같은 `ROS_DOMAIN_ID`
- 호환되는 RMW 구현
- Timeline Play 상태와 연결된 Action Graph execution 포트
- 여러 머신/Docker라면 같은 Fast DDS UDP profile, 방화벽과 subnet 정책
- subscriber와 publisher의 QoS 호환성

토픽은 보이지만 데이터가 없으면 다음을 사용하다.

```bash
ros2 topic info /clock -v
ros2 topic echo /clock --once
```

커스텀 메시지의 shared library를 찾지 못하면 동일 인터페이스가 Isaac Sim Python 3.11용과 외부 Jazzy용으로 각각 빌드·source되었는지 확인하다.

## 증상 10: Docker에서 GPU가 안 보이다

호스트에서 순서대로 확인하다.

```bash
nvidia-smi
docker info | sed -n '1,120p'
nvidia-ctk --version
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

마지막 명령이 실패하면 Isaac Sim 이미지 문제가 아니라 NVIDIA Container Toolkit 구성 문제이다. Toolkit을 구성한 뒤 Docker daemon을 재시작하다. 공식 5.1 문서는 GPU 감지 문제가 있을 때 Isaac Sim 컨테이너에도 `--runtime=nvidia`를 추가해 볼 수 있다고 안내하다.

bind mount 권한도 확인하다.

```bash
stat -c '%u:%g %a %n' ~/docker/isaac-sim \
  ~/docker/isaac-sim/cache/main ~/docker/isaac-sim/logs
```

공식 5.1 컨테이너 사용자는 `1234:1234`이다. 전체 홈 디렉터리의 소유권을 바꾸지 말고 Isaac Sim용 mount 디렉터리만 조정하다.

## 증상 11: WebRTC 연결이 되지 않는다

1. 서버 로그에서 앱이 완전히 로드되었는지 확인하다.

   ```text
   Isaac Sim Full Streaming App is loaded.
   ```

2. 서버에서 포트를 확인하다.

   ```bash
   ss -lntup | grep -E '(:49100|:47998)'
   ```

3. 같은 LAN이면 서버의 사설 IP, 인터넷 경유면 명시한 public endpoint를 클라이언트에 넣다.
4. 보안 그룹과 OS 방화벽에서 TCP 49100, UDP 47998을 확인하다.
5. VPN, NAT와 회사 네트워크가 UDP를 차단하지 않는지 확인하다.
6. 이미 다른 클라이언트가 붙었거나 다른 스트리밍 방식을 동시에 실행하지 않았는지 확인하다.
7. A100과 5.1 aarch64는 공식 라이브스트리밍 지원 대상이 아니다.

UDP는 단순 TCP 포트 검사만으로 검증되지 않는다. 무작정 모든 인바운드 포트를 개방하지 않다.

## 5.1 알려진 이슈 중 초보자가 알아둘 것

- OmniGraph compound node가 크래시를 유발할 수 있어 5.1 문서는 사용을 권장하지 않는다.
- `World`/`SimulationContext`와 OmniGraph를 함께 쓸 때는 graph를 먼저 만들고 World/SimulationContext를 초기화해야 하는 알려진 제약이 있다.
- timeCodesPerSecond를 바꾼 뒤 writer가 붙은 OmniGraph 오류가 나면 Stage를 저장하고 다시 열라는 공식 우회가 있다.
- 특정 `omni.usd LoadModule` 오류는 알려진 이슈에서 무시 가능하다고 되어 있지만, 다른 USD 로드 실패까지 전부 무시하는 규칙은 아니다.

재현이 5.1 알려진 이슈라면 지원 종료된 5.1에서 수정될 것이라 기대하지 말고, 버전 고정이 필수가 아니라면 지원 중인 새 릴리스에서 재현 여부를 확인하다.

## 도움을 요청할 때 포함할 최소 정보

- Isaac Sim 정확한 버전과 설치 방식
- Ubuntu, 커널, GPU, 드라이버, VRAM
- Compatibility Checker 결과
- 가장 작은 재현 Stage 또는 스크립트
- 실행 명령 전체
- 첫 오류 앞뒤의 로그
- 재현 빈도와 기대 결과/실제 결과
- ROS 문제라면 양쪽 환경 변수, RMW, Domain ID, QoS

원본 프로젝트 전체나 비밀키를 올리지 않다. 에셋을 제거해도 재현되는 최소 예제를 새 디렉터리에서 만들다.

## 완료 체크포인트

- [ ] 하드웨어부터 ROS까지 계층 순서로 진단할 수 있다.
- [ ] 최신 로그와 첫 번째 원인 오류를 찾을 수 있다.
- [ ] `--reset-user`, `clear_caches.sh`, `warmup.sh`의 차이를 설명할 수 있다.
- [ ] OOM, 에셋, 물리, ROS 2, Docker, WebRTC 문제를 각각 분리해 검사했다.
- [ ] 민감 정보를 제외한 최소 재현 자료를 만들 수 있다.

## 출처

- [Isaac Sim 5.1.0 — Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_workstation.html)
- [Isaac Sim 5.1.0 — Setup Tips](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_faq.html)
- [Isaac Sim 5.1.0 — Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
- [Isaac Sim 5.1.0 — ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)
- [Isaac Sim 5.1.0 — ROS 2 Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/troubleshooting.html)
- [Isaac Sim 5.1.0 — Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)
- [Isaac Sim 5.1.0 — Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)
- [Omniverse Developer Guide — Linux Troubleshooting](https://docs.omniverse.nvidia.com/dev-guide/latest/linux-troubleshooting.html)
