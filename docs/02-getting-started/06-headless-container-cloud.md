# Headless, Docker와 클라우드 실행

이 장에서는 화면이 없는 서버에서 Isaac Sim 5.1을 실행하는 방법을 구분하다. **headless**라는 말은 한 가지 실행 모드를 뜻하지 않는다. 자동 배치 시뮬레이션인지, 원격 GUI 스트리밍인지부터 정하다.

## 실행 방식 선택

| 목표 | 권장 방식 | 화면 출력 |
|---|---|---|
| 로컬에서 개발·디버깅 | 워크스테이션 `isaac-sim.sh` | 로컬 GUI |
| Python 실험·CI·데이터 생성 | standalone 스크립트의 `SimulationApp({"headless": True})` | 없음 |
| 원격 서버에서 GUI 조작 | 워크스테이션 `isaac-sim.streaming.sh` 또는 컨테이너 `runheadless.sh` | WebRTC 클라이언트 |
| 재현 가능한 서버 배포 | `nvcr.io/nvidia/isaac-sim:5.1.0` 컨테이너 | 없음 또는 WebRTC |
| 관리형 GPU 인프라 | 공식 클라우드 배포 가이드 + 컨테이너/워크스테이션 | 제공 방식에 따름 |

`runheadless.sh`는 단순히 창만 없애는 배치 실행기가 아니라 WebRTC Streaming 서비스를 포함한 전체 앱을 시작하는 스크립트이다. 자동 테스트는 Python 스크립트가 스스로 종료하도록 작성하는 편이 적합하다.

## 워크스테이션 패키지에서 창 없이 실행

### 배치 Python

[첫 Stage 실습](05-first-scene-and-physics.md)의 스크립트를 headless로 실행하다.

```bash
cd ~/isaacsim
./python.sh ~/isaacsim-projects/first-scene/first_scene.py --headless
echo "exit_code=$?"
```

CI에서는 무한 루프를 막기 위해 스크립트 안에 종료 조건을 두고, 바깥에도 제한 시간을 둘 수 있다.

```bash
timeout 10m ~/isaacsim/python.sh \
  ~/isaacsim-projects/first-scene/first_scene.py --headless
```

`timeout`의 종료 코드 `124`는 제한 시간 초과를 뜻하다. 정상 완료와 같은 것으로 처리하지 않다.

### WebRTC 원격 GUI

워크스테이션 패키지에서 스트리밍 앱을 시작하다.

```bash
cd ~/isaacsim
./isaac-sim.streaming.sh
```

같은 LAN의 다른 컴퓨터에서는 Isaac Sim WebRTC Streaming Client에 서버의 사설 IP를 입력하다. 인터넷을 경유해야 할 때는 공식 플래그로 공개 endpoint와 포트를 지정하다.

```bash
cd ~/isaacsim
./isaac-sim.streaming.sh \
  --/app/livestream/publicEndpointAddress=<PUBLIC_IP> \
  --/app/livestream/port=49100
```

기본적으로 확인할 포트는 UDP `47998`, TCP `49100`이다. 방화벽과 클라우드 보안 그룹에서는 가능한 한 신뢰할 수 있는 클라이언트 IP만 허용하다. NAT, 회사 VPN, 대칭형 방화벽에서는 포트를 열어도 연결되지 않을 수 있다.

한 Isaac Sim 인스턴스에는 한 번에 하나의 스트리밍 방식과 한 클라이언트만 사용한다는 공식 제한이 있다. A100에는 NVENC가 없어 스트리밍을 지원하지 않으며, 5.1.0 aarch64도 라이브스트리밍을 지원하지 않는다.

## Docker 사전 조건

컨테이너는 Linux에서만 공식 지원하다. Docker Engine과 최신 NVIDIA Container Toolkit을 설치한 뒤 GPU 전달을 먼저 확인하다. 설치 방식은 Docker와 NVIDIA Container Toolkit 공식 문서를 우선하다.

```bash
docker --version
nvidia-smi
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

마지막 명령에서 호스트와 같은 GPU가 보여야 하다. 권한 오류라면 무작정 모든 명령에 `sudo`를 붙이기 전에 Docker 그룹과 조직 보안 정책을 확인하다.

## Isaac Sim 5.1 이미지 받기

```bash
docker pull nvcr.io/nvidia/isaac-sim:5.1.0
docker image inspect nvcr.io/nvidia/isaac-sim:5.1.0 \
  --format '{{.Id}} {{.Architecture}}'
```

태그는 재현에 편리하지만 레지스트리 정책에 따라 같은 태그의 digest가 바뀔 가능성을 고려하다. 엄격한 재현이 필요하면 실제로 검증한 image digest도 실험 기록에 남기다.

## 캐시와 로그를 호스트에 유지하기

컨테이너는 rootless 사용자 UID/GID `1234:1234`로 실행되다. 공식 5.1 예제와 같은 디렉터리를 만들다.

```bash
mkdir -p ~/docker/isaac-sim/cache/main/ov
mkdir -p ~/docker/isaac-sim/cache/main/warp
mkdir -p ~/docker/isaac-sim/cache/computecache
mkdir -p ~/docker/isaac-sim/config
mkdir -p ~/docker/isaac-sim/data/documents
mkdir -p ~/docker/isaac-sim/data/Kit
mkdir -p ~/docker/isaac-sim/logs
mkdir -p ~/docker/isaac-sim/pkg
sudo chown -R 1234:1234 ~/docker/isaac-sim
```

소유권 변경 대상이 정확히 `~/docker/isaac-sim`인지 `pwd`와 `realpath`로 확인한 뒤 실행하다.

```bash
realpath ~/docker/isaac-sim
```

## 대화형 컨테이너와 Compatibility Checker

다음 명령은 컨테이너 안의 Bash를 열다.

```bash
docker run --name isaac-sim --entrypoint bash -it --gpus all \
  -e ACCEPT_EULA=Y --rm --network=host \
  -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
  -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
  -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
  -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
  -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
  -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
  -u 1234:1234 \
  nvcr.io/nvidia/isaac-sim:5.1.0
```

`ACCEPT_EULA=Y`는 링크된 NVIDIA Omniverse 라이선스를 읽고 수락한 경우에만 사용하다. 데이터 수집에 동의한다면 별도로 `-e PRIVACY_CONSENT=Y`를 추가할 수 있고, 동의하지 않는다면 생략하다. 두 설정을 같은 것으로 보지 않다.

컨테이너 프롬프트에서 호환성을 검사하다.

```bash
cd /isaac-sim
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window
```

공식 성공 문구는 다음과 같다.

```text
System checking result: PASSED
```

이 문구가 없으면 위쪽 로그에서 첫 오류를 찾다. Checker가 끝나지 않아 임의로 종료했다면 통과한 것으로 기록하지 않다.

## 컨테이너에서 WebRTC 시작

같은 컨테이너 프롬프트에서 실행하다.

```bash
cd /isaac-sim
./runheadless.sh -v
```

`-v`는 셰이더 캐시 준비 중 추가 로그를 보여 주다. 앱이 준비되기 전에 클라이언트가 접속하면 빈 화면이나 연결 실패가 나올 수 있다. 터미널에서 다음 준비 메시지를 찾다.

```text
Isaac Sim Full Streaming App is loaded.
```

PIP 또는 일부 Python 샘플에서는 이 정확한 문구가 나오지 않을 수 있다. 프로세스, 로그와 포트를 함께 확인하다.

인터넷 경유 공개 endpoint가 필요할 때만 다음 형태를 사용하다.

```bash
./runheadless.sh \
  --/app/livestream/publicEndpointAddress=<PUBLIC_IP> \
  --/app/livestream/port=49100
```

공개 IP를 자동 조회하는 공식 예제도 있지만, 다중 NIC·프록시·NAT 환경에서는 조회 결과가 실제 접속 주소와 다를 수 있으므로 배포자가 명시적으로 확인하다.

## 컨테이너 상태와 로그 확인

호스트의 다른 터미널에서 다음을 사용하다.

```bash
docker ps --filter name=isaac-sim
docker stats isaac-sim
docker logs --tail 200 isaac-sim
find ~/docker/isaac-sim/logs -type f -printf '%T@ %p\n' \
  | sort -nr | head
```

앞의 예제는 `--rm`과 대화형 Bash를 사용하므로 Bash를 끝내면 컨테이너가 삭제되다. 그러나 bind mount한 캐시·로그·데이터는 호스트에 남다. 장기 서비스에서는 restart 정책, 상태 확인, 로그 순환과 종료 신호를 별도로 설계하다.

## 컨테이너에서 자동 Python 작업 실행

프로젝트를 읽기 전용으로 mount하고 결과 디렉터리만 쓰기 가능하게 분리하는 패턴을 권장하다. 예시는 스크립트가 `SimulationApp({"headless": True})`를 설정했다고 가정하다.

```bash
mkdir -p ~/isaacsim-batch-output
sudo chown 1234:1234 ~/isaacsim-batch-output

docker run --rm --gpus all --network=host \
  --entrypoint /isaac-sim/python.sh \
  -u 1234:1234 \
  -e ACCEPT_EULA=Y \
  -e ISAAC_TUTORIAL_OUTPUT=/output/falling_cube_python.usda \
  -v ~/isaacsim-projects:/workspace:ro \
  -v ~/isaacsim-batch-output:/output:rw \
  nvcr.io/nvidia/isaac-sim:5.1.0 \
  /workspace/first-scene/first_scene.py --headless
```

앞 장의 예제는 `ISAAC_TUTORIAL_OUTPUT`을 읽으므로 결과가 host의 `~/isaacsim-batch-output/falling_cube_python.usda`에 남다. 일반 스크립트도 출력 경로를 인자나 환경 변수로 받아 `/output`에 쓰도록 설계하다. mount가 있다는 이유만으로 코드의 저장 경로가 자동 변경되지는 않는다.

## 클라우드 배포 개요

Isaac Sim 5.1 공식 문서는 Isaac Launchable, NVIDIA Brev, AWS, Azure, Google Cloud와 여러 지역 클라우드에 대한 절차를 제공하다. 공급자가 달라도 다음 기준은 같다.

1. **RTX 지원 GPU를 선택하다.** A100/H100처럼 RTX 코어가 없는 가속기는 지원 GPU가 아니다.
2. **드라이버와 VRAM을 확인하다.** 인스턴스 이름에 GPU가 있다고 Isaac Sim 요구사항을 자동 충족하는 것은 아니다.
3. **스토리지를 지속화하다.** 이미지, 에셋, 셰이더 캐시, 결과 데이터의 용량을 계산하다.
4. **접근 경로를 정하다.** SSH, DCV/원격 데스크톱, WebRTC 중 필요한 것만 열다.
5. **보안 그룹을 최소화하다.** SSH TCP 22와 스트리밍 UDP 47998/TCP 49100 등을 전 세계에 상시 공개하지 않다.
6. **비용과 종료 정책을 두다.** GPU 인스턴스와 영구 디스크, egress 비용을 함께 추적하다.
7. **버전과 image digest를 기록하다.** 호스트 드라이버도 실험 메타데이터에 남기다.

AWS 공식 예제는 RTX GPU 지원 EC2, SSH 22, DCV 8443, WebRTC TCP 49100/UDP 47998을 요구하다. 다른 공급자에도 같은 포트를 기계적으로 적용하지 말고 해당 공식 5.1 배포 페이지와 네트워크 구성을 확인하다.

## 완료 체크포인트

- [ ] 배치 headless와 WebRTC streaming headless의 차이를 설명할 수 있다.
- [ ] 호스트와 컨테이너 양쪽에서 `nvidia-smi`를 확인했다.
- [ ] 캐시·로그 bind mount와 UID `1234:1234`를 구성했다.
- [ ] 컨테이너 Checker의 실제 결과를 기록했다.
- [ ] WebRTC 포트와 접근 IP를 최소 범위로 제한했다.
- [ ] 자동 스크립트에 종료 조건·시간 제한·출력 경로를 두었다.

## 출처

- [Isaac Sim 5.1.0 — Container Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_container.html)
- [Isaac Sim 5.1.0 — Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/manual_livestream_clients.html)
- [Isaac Sim 5.1.0 — Setup Tips](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_faq.html)
- [Isaac Sim 5.1.0 — Cloud Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_cloud.html)
- [Isaac Sim 5.1.0 — Remote Workstation Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_advanced_remote_setup.html)
- [Isaac Sim 5.1.0 — AWS Deployment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_advanced_cloud_setup_aws.html)
- [NVIDIA Container Toolkit — Install Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
