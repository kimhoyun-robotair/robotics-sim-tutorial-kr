# Isaac Sim 5.1 한국어 실습 튜토리얼

Ubuntu 24.04 LTS, ROS 2 Jazzy, NVIDIA Isaac Sim 5.1.0 조합을 처음 설치하는 단계부터 USD, 로봇·센서 구성, ROS 2, Python/OmniGraph 확장, 합성 데이터, Isaac Lab까지 학습하는 실행 중심 과정이다.

> NVIDIA는 현재 5.1.0 문서를 지원 종료 버전으로 표시한다. 이 브랜치는 재현성이 필요한 기존 프로젝트를 위해 **5.1.0에 고정**한다. 새 프로젝트는 최신 Isaac Sim도 함께 평가해야 한다.

## 기준 환경

| 항목 | 본편 기준 |
| --- | --- |
| 운영체제 | Ubuntu 24.04 LTS (Noble), x86_64 |
| ROS 2 | Jazzy Jalisco |
| 시뮬레이터 | Isaac Sim 5.1.0 |
| Isaac Sim 내장 Python | 3.11 |
| Ubuntu 24.04 ROS 2 Jazzy Python | 3.12 |
| GPU | RT Core가 있는 NVIDIA RTX GPU |
| 문서 언어 | 자연스러운 한국어 `-하다`체 |

Python 버전이 다른 두 프로세스를 억지로 한 환경에 섞지 않는다. 기본 ROS 메시지는 DDS로 통신하므로 외부 ROS 2 노드는 Python 3.12를 사용해도 된다. Isaac Sim 프로세스에서 `rclpy` 또는 커스텀 인터페이스를 직접 불러올 때만 Python 3.11용 별도 workspace가 필요하다.

## 처음 시작하기

1. [36단계 학습 과정](docs/course-guide.md)을 순서대로 따른다. GUI의 마우스 조작부터 시작해 로봇·센서·ROS 2와 심화 프로젝트까지 진행한다.
2. [첫 물리 장면](docs/02-getting-started/05-first-scene-and-physics.md)에서 상자를 만든 뒤, [실행 방식 비교](docs/06-developer/01-python-workflows.md)에서 같은 장면을 GUI·Script Editor·Extension·standalone Python으로 구성한다.
3. 이전 버전 코드가 있다면 [4.x→5.0→5.1 변경사항](docs/appendices/release-notes-4x-to-5-1.md)을 함께 읽는다. 기능이 처음 추가된 버전과 5.1에서 수정·제거된 항목을 구분한다.
4. 각 단계의 완료 기준을 확인한 뒤 [다섯 프로젝트](docs/07-projects/00-overview.md)에서 USD·자체 로봇·창고 주행·비전 집기·학습 정책을 적용한다.

[공식 문서 대응표](docs/appendices/official-docs-coverage.md)에서 NVIDIA 5.1.0 원문과 관련 실습을 찾을 수 있다.

## 예제와 검증

`examples/standalone/`에는 기본 물리, 이동 로봇, 카메라·IMU, RTX LiDAR 예제를 제공한다. `examples/script_editor/`와 `examples/extensions/`에는 앱 안에서 실행할 예제를 제공한다. 실행 위치와 전체 코드는 각 실습 본문을 따른다.

**이번 수정에서는 정적 검사를 수행했으며, 실제 Isaac Sim·RTX GPU·ROS 2 실행은 검증하지 못했다.** [검증 기록](docs/appendices/validation-report.md)에 검사 결과와 제한을 남겼다. [장비 검증 절차](docs/05-customization/04-validation-performance.md)는 검은 영상·빈 프레임·잘못된 센서 값·로봇 자세를 확인하는 실행 명령과 결과 판정 방법을 설명한다.

## 빠른 확인

Isaac Sim을 설치한 디렉터리를 `ISAACSIM_PATH`로 지정한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
test -x "$ISAACSIM_PATH/isaac-sim.sh"
"$ISAACSIM_PATH/python.sh" - <<'PY'
import sys
print(sys.version)
PY
nvidia-smi
```

ROS 2 Jazzy는 별도 터미널에서 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
test "$ROS_DISTRO" = jazzy
python3 --version
ros2 doctor --report
```

첫 실행과 ROS 2 Bridge 활성화 방법은 설치 장을 따른다. 시스템 ROS 환경을 source한 터미널에서 무조건 Isaac Sim을 실행하면 Python ABI 충돌이 날 수 있으므로, 어떤 워크플로를 사용하는지 먼저 결정한다.

## 문서 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-docs.txt
mkdocs serve
```

정적 빌드와 과정 규칙 검사는 다음과 같이 실행한다.

```bash
mkdocs build --strict
python3 scripts/audit_tutorial.py
```

## 저장소 구성

- `docs/01-foundations/`는 Omniverse·Isaac 계층과 USD를 설명한다.
- `docs/02-getting-started/`는 설치, GUI, 첫 씬과 실행 방식을 설명한다.
- `docs/03-core/`는 물리, 로봇, 제어, 모션 생성을 설명한다.
- `docs/04-ros2/`는 ROS 2 Jazzy Bridge와 로봇 스택 연동을 설명한다.
- `docs/05-customization/`는 커스텀 로봇, 환경, 센서를 만드는 방법을 설명한다.
- `docs/06-developer/`는 Extension, OmniGraph, Replicator, Isaac Lab을 설명한다.
- `docs/07-projects/`는 난이도별 미니 프로젝트 5개를 제공한다.
- `docs/appendices/`는 공식 문서 커버리지, 용어, 점검표를 제공한다.
- `examples/`는 복사해 실행할 수 있는 최소 예제를 보관한다.
- `scripts/`는 문서의 출처·링크·구조를 검사한다.

## 문서 원칙

각 설명 페이지 끝에는 `출처` 단락을 두고 NVIDIA 5.1.0 공식 페이지 또는 해당 기술의 1차 문서를 연결한다. 공식 문서를 그대로 복제하지 않고, 초보자가 실습할 수 있도록 한국어로 재구성한다. 메뉴 이름, API, 파일명은 5.1.0을 기준으로 하며 버전 의존적인 내용은 본문에서 명시한다.

## 출처

- [NVIDIA Isaac Sim 5.1.0 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)
- [Isaac Sim 5.1.0 Release Notes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/release_notes.html)
- [Isaac Sim 5.1.0 ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

