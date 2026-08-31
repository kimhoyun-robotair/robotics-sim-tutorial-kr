# Ubuntu 24.04 시스템 요구사항과 사전 점검

이 장에서는 Isaac Sim 5.1.0을 설치하기 전에 운영체제, GPU, 드라이버, 메모리와 저장 공간을 확인하다. 여기서 점검을 통과하지 못했다면 설치 파일을 내려받기 전에 원인을 해결하는 편이 낫다.

> **버전 상태**
>
> NVIDIA의 5.1.0 문서에는 현재 이 릴리스가 지원 종료 상태라고 표시되어 있다. 즉, 5.1.0에 대한 새 버그 수정이나 보안·기능 업데이트는 제공되지 않는다. 이 튜토리얼은 재현성을 위해 5.1.0을 고정해서 사용하지만, 새 프로젝트에서는 최신 지원 릴리스도 함께 검토하다.

## 공식 요구사항 읽기

Isaac Sim 5.1.0의 x86_64 공식 표는 다음과 같다. `최소`는 모든 장면이 원활하다는 뜻이 아니라 제품이 제시하는 하한이다.

| 항목 | 최소 | 권장(Good) | 이상적(Ideal) |
|---|---:|---:|---:|
| 운영체제 | Ubuntu 22.04/24.04 | Ubuntu 22.04/24.04 | Ubuntu 22.04/24.04 |
| CPU | Intel Core i7 7세대 / Ryzen 5 | Intel Core i7 9세대 / Ryzen 7 | Core i9·X-series / Ryzen 9·Threadripper 이상 |
| CPU 코어 | 4 | 8 | 16 |
| RAM | 32 GB | 64 GB | 64 GB |
| 저장장치 | 50 GB SSD | 500 GB SSD | 1 TB NVMe SSD |
| GPU | GeForce RTX 4080 | GeForce RTX 5080 | RTX PRO 6000 Blackwell |
| VRAM | 16 GB | 16 GB | 48 GB |
| Linux 테스트 드라이버 | 580.65.06 | 580.65.06 | 580.65.06 |

이 표의 드라이버 번호는 NVIDIA가 5.1.0을 시험한 버전이다. 다른 버전이 무조건 실패한다는 의미로 확대 해석하지 말고, 문제가 생기면 우선 공식 테스트 버전과 현재 Production Branch 권장 버전을 대조하다.

다음 제한도 중요하다.

- RTX 코어가 없는 A100·H100은 Isaac Sim 렌더링 GPU로 지원하지 않는다.
- 인터넷 연결이 있어야 온라인 Isaac Sim 에셋과 일부 확장 기능을 사용할 수 있다.
- 센서를 여러 개 사용하거나 한 프레임에 16 MP를 넘게 렌더링하면 16 GB 미만 VRAM에서 특히 부족해질 수 있다.
- Isaac Lab의 대규모 병렬 강화학습은 기본 Isaac Sim보다 RAM과 VRAM을 더 요구하다.
- Isaac Sim 컨테이너는 Linux에서만 공식 지원하다.

## 1단계: Ubuntu와 CPU 아키텍처 확인

```bash
cat /etc/os-release
uname -m
uname -r
```

다음을 확인하다.

- `VERSION_ID="24.04"`가 출력되다.
- 일반 PC 워크스테이션은 `x86_64`가 출력되다.
- `aarch64` 빌드는 5.1.0에서 DGX Spark만 공식 지원하며 App Selector와 라이브스트리밍 등에도 제한이 있다. 이 튜토리얼의 일반 PC 절차를 그대로 적용하지 않다.

## 2단계: NVIDIA GPU와 드라이버 확인

```bash
lspci -nn | grep -iE 'vga|3d|display'
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total,pci.bus_id \
  --format=csv,noheader
```

정상이라면 마지막 명령에서 GPU 이름, 드라이버 버전, 총 VRAM과 PCI 주소가 한 줄씩 출력되다. `nvidia-smi`가 실패하면 Isaac Sim 설치보다 드라이버 문제를 먼저 해결하다.

Ubuntu가 인식하는 드라이버 후보도 확인할 수 있다.

```bash
ubuntu-drivers devices
```

드라이버를 바꾸기 전에는 현재 커널, Secure Boot 사용 여부, 기존 CUDA·컨테이너 환경을 함께 점검하다. 패키지 방식과 NVIDIA `.run` 설치 방식을 섞으면 파일 소유권과 커널 모듈이 충돌할 수 있으므로 한 가지 관리 방식만 사용하다. NVIDIA는 새 GPU이거나 현 드라이버에 문제가 있을 때 Unix Driver Archive의 최신 Production Branch 드라이버를 검토하도록 안내하다.

### Vulkan 확인

Isaac Sim의 RTX 렌더러는 Vulkan 장치 열거가 정상이어야 하다. 진단 도구를 설치하고 요약을 확인하다.

```bash
sudo apt update
sudo apt install -y vulkan-tools
vulkaninfo --summary
```

`vulkaninfo`에 NVIDIA GPU가 보이지 않거나 소프트웨어 렌더러만 보이면 Isaac Sim을 실행하기 전에 Vulkan ICD와 드라이버 설치를 점검하다. 하이브리드 그래픽 노트북이나 다중 GPU 시스템에서는 `nvidia-smi`에 보이는 GPU와 Vulkan에 보이는 GPU가 같은지도 확인하다.

## 3단계: RAM, CPU와 디스크 확인

```bash
lscpu | sed -n '1,25p'
free -h
df -h "$HOME"
```

설치 ZIP, 압축 해제본, 셰이더 캐시, 에셋과 프로젝트 파일이 동시에 공간을 사용하다. 공식 최소 설치 공간 50 GB만 정확히 비워 두기보다 여유 공간을 더 확보하는 편이 안전하다. 온라인 에셋을 로컬 에셋 팩으로 내려받으면 추가 공간이 필요하다.

현재 사용 가능한 메모리와 GPU 메모리를 관찰하려면 별도 터미널에서 다음 명령을 사용하다.

```bash
watch -n 1 nvidia-smi
```

## 4단계: 디스플레이 세션 확인

로컬 GUI를 실행할 때는 디스플레이 세션이 필요하다.

```bash
printf 'DISPLAY=%s\n' "$DISPLAY"
printf 'XDG_SESSION_TYPE=%s\n' "$XDG_SESSION_TYPE"
```

SSH 터미널처럼 `DISPLAY`가 비어 있는 환경에서는 일반 GUI 대신 헤드리스·컨테이너·WebRTC 스트리밍 구성을 선택하다. 단순한 X11 포워딩이 고성능 RTX 뷰포트에 적합하다고 가정하지 않다.

## 5단계: 설치 후 공식 Compatibility Checker 실행

독립형 패키지를 설치한 뒤 설치 루트에서 실행하다.

```bash
cd ~/isaacsim
./isaac-sim.compatibility_check.sh
```

창을 열 수 없는 환경에서는 자동 종료 옵션을 사용하다.

```bash
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window
```

Checker는 GPU·드라이버·RTX 기능·VRAM, CPU·코어·RAM·저장 공간, 운영체제와 디스플레이를 검사하다. 색상 결과는 `green=excellent`, `light-green=good`, `orange=동작 가능하나 상향 권장`, `red=부족 또는 미지원`을 뜻하다. 컨테이너 검사에서 공식 성공 문구는 `System checking result: PASSED`이다.

> Checker의 통과는 특정 대형 장면이나 다중 센서 워크로드의 성능을 보장하지 않는다. 실제 목표 장면으로 VRAM, 프레임 시간과 실시간 계수를 다시 측정하다.

## 완료 체크포인트

- [ ] Ubuntu 24.04와 올바른 CPU 아키텍처를 확인했다.
- [ ] `nvidia-smi`와 `vulkaninfo --summary`에서 RTX GPU를 확인했다.
- [ ] RAM, VRAM과 SSD 여유 공간을 공식 하한과 비교했다.
- [ ] 로컬 GUI인지 헤드리스인지 실행 방식을 정했다.
- [ ] 설치 후 Compatibility Checker 결과를 보관했다.

## 출처

- [Isaac Sim 5.1.0 — Isaac Sim Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [Isaac Sim 5.1.0 — Workstation Installation / Compatibility Checker](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_workstation.html)
- [Omniverse Developer Guide — Linux Troubleshooting](https://docs.omniverse.nvidia.com/dev-guide/latest/linux-troubleshooting.html)
- [Isaac Sim 5.1.0 — Release Notes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)
