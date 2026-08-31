# Isaac Sim 5.1 워크스테이션 설치와 첫 실행

이 장에서는 Ubuntu 24.04 x86_64 워크스테이션에 NVIDIA 공식 독립형 패키지를 설치하다. 설치 위치는 공식 예제와 같은 `~/isaacsim`으로 통일하다.

## 5.1에서 달라진 배포 방식

예전 튜토리얼에서 자주 보이는 **Omniverse Launcher로 Isaac Sim을 설치하라**는 절차를 5.1에 적용하지 않다.

- Isaac Sim 5.1 워크스테이션 배포물은 플랫폼별 독립형 ZIP으로 제공하다.
- 압축을 푼 뒤 `isaac-sim.selector.sh`라는 **Isaac Sim App Selector**로 모드를 고르거나 `isaac-sim.sh`를 직접 실행하다.
- NVIDIA는 Omniverse Launcher, Nucleus Workstation, Nucleus Cache가 2025년 10월 1일부터 더 이상 제공되지 않는다고 5.1 문서에 명시하다.
- Nucleus Cache의 후속은 Hub Workstation Cache이지만, Isaac Sim 자체 실행에는 Nucleus·Cache·Hub가 필수가 아니다.
- Nucleus와 Live Sync가 필요한 조직은 Enterprise Nucleus Server를 별도로 검토하다.

`Omniverse Launcher`와 이름이 비슷하지만 `isaac-sim.selector.sh`는 압축 패키지 안에 든 작은 실행 모드 선택기이다. 둘을 혼동하지 않다.

## 1단계: 공식 배포물 내려받기

[Isaac Sim Download](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html)에서 5.1.0 Linux x86_64 독립형 패키지를 내려받다. 로그인 또는 이용 조건 확인이 필요할 수 있다. 임시·서명 URL을 문서에 고정하지 않고 공식 다운로드 페이지에서 직접 받다.

예상 파일명은 다음과 같다.

```text
isaac-sim-standalone-5.1.0-linux-x86_64.zip
```

다운로드가 끝났는지 확인하다.

```bash
ls -lh ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip
unzip -t ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip | tail
```

`unzip -t`의 마지막에 오류가 없다는 문구가 나와야 하다. 제공 페이지에 체크섬이 표시된 경우에는 그 값도 비교하다.

## 2단계: 압축 해제와 후처리

```bash
sudo apt update
sudo apt install -y unzip

mkdir -p ~/isaacsim
unzip ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip \
  -d ~/isaacsim
cd ~/isaacsim
./post_install.sh
```

`post_install.sh`는 튜토리얼용 `extension_examples` 심볼릭 링크 같은 설치 후 연결을 만들다. 한 번 실행하면 되며, 오류가 났다면 다음을 확인하다.

```bash
pwd
test -x ./isaac-sim.sh && echo "launcher script: OK"
test -x ./python.sh && echo "bundled Python: OK"
ls -l extension_examples 2>/dev/null || true
```

압축 해제 중간에 다른 버전을 같은 디렉터리에 덮어쓰지 않다. 버전을 병행해야 한다면 `~/isaacsim-5.1.0`처럼 별도 디렉터리를 만들고 이후 명령의 경로도 바꾸다.

## 3단계: Compatibility Checker

```bash
cd ~/isaacsim
./isaac-sim.compatibility_check.sh
```

창이 열리지 않는 서버에서는 다음처럼 실행하다.

```bash
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window
```

빨간 항목이 있으면 [시스템 요구사항](01-system-requirements.md)과 [문제 해결](07-troubleshooting.md)을 먼저 확인하다. Checker가 통과해도 목표 장면의 성능까지 보장하는 것은 아니다.

## 4단계: App Selector 또는 직접 실행

초보자는 App Selector를 실행하다.

```bash
cd ~/isaacsim
./isaac-sim.selector.sh
```

창에서 **Isaac Sim Full**을 고르고 **START**를 누르다. 같은 앱을 직접 시작하려면 다음 명령을 사용하다.

```bash
cd ~/isaacsim
./isaac-sim.sh
```

주요 실행 스크립트는 다음과 같다.

| 스크립트 | 역할 |
|---|---|
| `isaac-sim.selector.sh` | 실행 모드를 고르는 App Selector |
| `isaac-sim.sh` | 전체 GUI 앱 |
| `isaac-sim.streaming.sh` | WebRTC 서비스를 포함한 헤드리스 전체 앱 |
| `python.sh` | Isaac Sim에 포함된 Python 3.11 실행기 |
| `warmup.sh` | 셰이더 캐시 사전 준비 |
| `clear_caches.sh` | 로컬 캐시 삭제 |
| `post_install.sh` | 설치 후 링크 구성 |

## 첫 실행, 셰이더 캐시와 빈 창

첫 실행은 셰이더를 컴파일하고 확장 기능을 불러오기 때문에 오래 걸리다. 공식 워크스테이션 문서는 GUI가 비어 보이는 동안 포함해 5~10분이 걸릴 수 있다고 안내하다. 다음을 기준으로 판단하다.

1. 실행한 터미널의 로그가 계속 갱신되는지 확인하다.
2. 별도 터미널에서 CPU·GPU 사용량을 관찰하다.

   ```bash
   watch -n 1 nvidia-smi
   ```

3. 오류 없이 셰이더 컴파일이 진행 중이면 창을 강제 종료하지 않고 기다리다.
4. 반복 실행도 매번 같은 지점에서 멈추고 로그가 더 이상 갱신되지 않을 때 문제로 분류하다.

원한다면 GUI 실행 전에 캐시를 미리 준비하다.

```bash
cd ~/isaacsim
./warmup.sh
```

공식 클라우드 설치 문서는 warmup이 15분 이상 걸릴 수 있다고 경고하다. 진행 시간이 길다는 사실만으로 실패라고 단정하지 않다.

## 이용 조건과 개인정보 설정

공식 다운로드·라이선스 페이지의 Isaac Sim 및 Omniverse 이용 조건을 읽고 조직 정책에 맞게 수락하다. 컨테이너의 `ACCEPT_EULA=Y`는 라이선스 수락을 명시하는 별도 환경 변수이며 워크스테이션 ZIP 실행 명령에 무작정 붙이는 옵션이 아니다.

컨테이너에서 `PRIVACY_CONSENT=Y`는 데이터 수집에 동의하는 선택 사항이다. 이를 EULA 수락과 같은 것으로 취급하지 않다. 워크스테이션에서는 실행 시 표시되는 선택과 `Data Collection & Usage` 문서를 확인하다.

## 설정을 초기화해야 할 때

레이아웃이나 사용자 설정 때문에 시작이 꼬였다고 판단되면, 먼저 설정을 무시하고 한 번 실행하다.

```bash
cd ~/isaacsim
./isaac-sim.sh --reset-user
```

`--reset-user`는 영구 사용자 설정 파일을 로드하지 않고 기본값으로 시작하다. 캐시 자체가 손상되었다는 근거가 있을 때만 앱을 완전히 종료한 뒤 다음을 사용하다.

```bash
cd ~/isaacsim
./clear_caches.sh
```

캐시를 지우면 다음 시작 때 셰이더와 확장을 다시 준비하므로 느려지다. 프로젝트 USD 파일을 지우는 명령은 아니지만, 실행 중에는 사용하지 않다.

공식 기본 경로는 다음과 같다.

| 종류 | Linux 경로 |
|---|---|
| 앱 | `~/isaacsim` |
| 로그 | `~/.nvidia-omniverse/logs/Kit/Isaac-Sim` |
| 셰이더 캐시 | `~/.cache/ov/Kit` |
| 설정·데이터 | `~/.local/share/ov/data/Kit/Isaac-Sim` |

## 설치 검증

GUI가 열린 뒤 다음을 확인하다.

1. `Help > About` 또는 시작 로그에서 5.1.0/Kit 107.3.3 계열인지 확인하다.
2. `Window > Extensions`가 열리는지 확인하다.
3. `File > New`로 빈 Stage를 만들다.
4. `Create > Environments > Simple Room`을 선택하고 에셋이 로드되는지 확인하다. 최초 온라인 에셋 로드는 네트워크 때문에 지연될 수 있다.
5. 터미널에서 치명적 오류가 반복되지 않는지 확인하다.

버전이 다른 설치를 실행한 것 같다면 프로세스와 실행 경로부터 확인하다.

```bash
readlink -f ~/isaacsim/isaac-sim.sh
pgrep -af 'kit|isaac-sim'
```

## 완료 체크포인트

- [ ] 5.1.0 x86_64 ZIP의 무결성을 확인하고 `~/isaacsim`에만 풀었다.
- [ ] `post_install.sh`와 Compatibility Checker를 실행했다.
- [ ] App Selector와 Omniverse Launcher가 다른 것임을 이해했다.
- [ ] Isaac Sim Full GUI와 온라인 에셋 하나를 열었다.
- [ ] 로그·캐시·설정 경로와 `--reset-user`의 용도를 이해했다.

## 출처

- [Isaac Sim 5.1.0 — Download Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html)
- [Isaac Sim 5.1.0 — Workstation Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_workstation.html)
- [Isaac Sim 5.1.0 — Quick Install](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/quick-install.html)
- [Isaac Sim 5.1.0 — Setup Tips](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_faq.html)
- [Isaac Sim 5.1.0 — Licenses](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/common/licenses.html)
- [Isaac Sim 5.1.0 — Data Collection & Usage](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/common/data-collection.html)
