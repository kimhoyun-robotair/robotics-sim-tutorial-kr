# CI 재현성

> **목표:** Ubuntu 24.04·ROS 2 Jazzy·Gazebo Harmonic 입력을 명시하고, 문서 빌드와 GUI 없는 실행 검사를 같은 소스 커밋 SHA에서 독립적으로 재현한다.
> **선행 학습:** [GUI 없는 통합 테스트](04-headless-integration.md)

## 재현성의 범위를 먼저 정하기

CI에서 “같다”는 말에는 여러 수준이 있다. 이 과정은 운영체제, ROS·Gazebo의 주 버전, 소스 커밋 SHA(커밋 식별자), 실행 명령을 기록한다. 설치된 패키지와 컴파일러 버전도 남겨 실패한 환경을 비교할 수 있게 한다. apt 저장소의 패치 버전이나 GitHub Action 태그가 가리키는 코드는 나중에 바뀔 수 있으므로 파일 내용까지 완전히 같은 결과를 보장하는 구성은 아니다. 장기 재현이 필요하면 컨테이너 이미지의 내용 식별자(digest), 특정 시점의 apt 저장소, Action의 커밋 SHA도 고정한다.

문서와 시뮬레이션은 같은 커밋에서 시작하지만 서로 다른 작업으로 판정한다.

| 자동 검사 | 입력 | 핵심 명령 | 산출물 |
| --- | --- | --- | --- |
| 문서 | Markdown, MkDocs 설정 | `mkdocs build --strict` | 빌드한 문서 사이트 |
| 실행 | ROS 작업 공간, 월드, 플러그인 | colcon build/test + 정상 시나리오 | 로그, JSON 검증 결과 |

<figure class="course-figure" id="advanced-ci-reproducibility" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/ci-reproducibility.svg" alt="같은 커밋에서 문서 빌드와 ROS·Gazebo 검사가 각각 결과를 남기는 CI 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 문서 빌드와 시뮬레이션 검사는 같은 커밋에서 시작하고 각자 결과를 남긴다.</figcaption>
</figure>

## 현재 브랜치별 실행 조건 확인하기

실제 설정은 `.github/workflows/pages.yml`에 있다. 이 파일은 아래처럼 `main`과 `Jazzy` 변경에서 검사를 시작한다. **Jazzy 과정 수정은 `Jazzy`에만 커밋·푸시한다.** 여기서 다른 브랜치를 수정할 필요는 없다.

```yaml
name: Deploy documentation

on:
  push:
    branches: [main, Jazzy]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false
```

현재 Pages 업로드·배포에는 별도로 `github.ref == 'refs/heads/main'` 조건이 있다. 따라서 `Jazzy`의 문서 빌드가 성공해도 공개 Pages가 자동으로 바뀌는 구조는 아니다. Actions 화면에서 브랜치와 커밋 SHA를 확인해 어떤 코드를 검사했는지 구분한다.

Jazzy 전용 전체 검사는 `.github/workflows/jazzy-validation.yml`에서 별도로 실행한다. 전체 작업 공간 빌드, 센서·TF·이미지·점군·주행 데이터 검사와 RViz 화면 기록을 다루며, 실행 결과와 화면을 확인한 뒤 해당 커밋의 검증 완료 여부를 판단한다. 자세한 확인 범위는 [Jazzy 점검 기록](../06_reference/04_jazzy-audit.md)을 참고한다.

## 실행 작업 작성하기

실제 워크플로는 Ubuntu 24.04 실행 환경에서 컨테이너 실행 도구를 호출한다. 캐시에는 컴파일러 중간 결과만 넣고 설치 디렉터리나 실행 검증 결과는 섞지 않는다.

```yaml
jobs:
  ros-gazebo:
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions:
      contents: read
    env:
      TUTORIAL_CI_CCACHE: /tmp/tutorial-bot-ccache
    steps:
      - uses: actions/checkout@v4
      - name: Cache compiler data
        uses: actions/cache@v4
        with:
          path: /tmp/tutorial-bot-ccache
          key: ros-jazzy-harmonic-ccache-${{ runner.arch }}-${{ hashFiles('examples/ros2_ws/src/tutorial_bot_plugins/**') }}
          restore-keys: ros-jazzy-harmonic-ccache-${{ runner.arch }}-
      - name: Build, test, and run server-only smoke
        run: >-
          ./scripts/ci/run_ros_gazebo_container.sh
          --source "$GITHUB_WORKSPACE"
          --evidence "$RUNNER_TEMP/ros-gazebo"
          --scenario nominal
      - name: Upload failure evidence
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: ros-gazebo-failure
          path: ${{ runner.temp }}/ros-gazebo
          if-no-files-found: error
```

성공 증거도 장기간 비교할 계획이라면 마지막 단계의 조건을 `if: always()`로 바꾸고 보관 파일 보존 기간을 조직 정책에 맞게 지정한다. 실패 분석만 목적이라면 현재처럼 `failure()`가 저장 공간을 줄인다.

## 컨테이너에 플랫폼 명시하기

컨테이너는 Ubuntu 24.04 위에 Jazzy와 Harmonic 개발 패키지를 설치한다. 아래는 `scripts/ci/Dockerfile.ubuntu24.04`의 의존성 부분을 설명하는 발췌다. ROS·Gazebo apt 저장소 등록 단계가 생략되어 있으므로 이 블록만 별도 Dockerfile로 저장하면 설치에 실패한다. 실제 빌드는 저장소의 전체 Dockerfile을 사용한다.

```dockerfile
FROM ubuntu:24.04

ENV ROS_DISTRO=jazzy

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential ccache python3-colcon-common-extensions python3-rosdep \
      ros-jazzy-ros-base ros-jazzy-ros-gz-bridge \
      gz-sim8-cli libgz-sim8-dev libgz-msgs10-dev \
      libgz-plugin2-dev libgz-transport13-dev \
 && rm -rf /var/lib/apt/lists/*
```

플러그인은 `gz_sim_vendor`를 먼저 찾고 버전 번호 없는 `find_package(gz-sim REQUIRED)`를 사용한다. Jazzy vendor 패키지가 Harmonic 계열 라이브러리를 선택한다. 빌드 컨테이너에서만 우연히 구버전 라이브러리를 찾는 일을 막으려면 이전 설치 디렉터리를 마운트하지 않고 매 실행에서 `/work/install`을 새로 만든다.

Docker를 사용할 수 있는 Ubuntu 환경에서는 저장소 최상위에서 다음 명령으로 CI와 같은 실행 도구를 호출한다. 검증 결과는 임시 디렉터리에 남겨 바로 확인한다.

```bash
ci_evidence="$(mktemp -d)"
./scripts/ci/run_ros_gazebo_container.sh \
  --source "$PWD" \
  --evidence "$ci_evidence" \
  --scenario nominal
printf '검증 결과: %s\n' "$ci_evidence"
```

이 스크립트가 컨테이너 이름, 이미지, 소스 경로를 정하고 읽기 전용 소스와 별도의 빌드·설치 경로를 연결한다. 실행이 실패하면 출력된 검증 결과 경로에서 로그를 확인한다.

## 빌드와 테스트의 실행 순서 읽기

`scripts/ci/run_ros_gazebo_ci.sh`는 대상 패키지를 빌드하고, 선택한 테스트 결과를 확인한 뒤 정상 시나리오를 실행한다. 아래는 순서를 설명하는 발췌이며 `/work/source`와 `/evidence`는 앞의 컨테이너 실행 도구가 준비하는 경로다. 일반 터미널에서 이 경로를 새로 만들 필요는 없다.

```bash
source /opt/ros/jazzy/setup.bash
cd /work/source/examples/ros2_ws

packages=(
  tutorial_bot_plugins
  tutorial_bot_description
  tutorial_bot_control
  tutorial_bot_gazebo
  tutorial_bot_bringup
  tutorial_bot_tests
)
colcon build \
  --build-base /work/build \
  --install-base /work/install \
  --packages-select "${packages[@]}" \
  --cmake-args -DBUILD_TESTING=ON

source /work/install/setup.bash
colcon test \
  --build-base /work/build \
  --install-base /work/install \
  --executor sequential \
  --packages-select tutorial_bot_plugins tutorial_bot_tests \
  --ctest-args -R \
  '^(advanced_contract|advanced_framework_cli|advanced_headless_integration|rover_examples|diagnostics_distance|diagnostics_enable_reset|diagnostics_enable_reset_concurrency|diagnostics_model_lifecycle|diagnostics_physics_cadence)$'
colcon test-result --test-result-base /work/build --verbose

/work/source/scripts/check_advanced_course.sh \
  --scenario nominal \
  --install-base /work/install \
  --evidence /evidence/smoke
```

`colcon test` 명령이 0이어도 `colcon test-result --verbose`로 실패 결과가 없는지 확인한다. 기본 동작 검사는 소스 월드가 아니라 `/work/install`의 월드와 라이브러리를 사용해 설치 규칙까지 검증한다.

## 문서 작업과 배포 작업 분리하기

```yaml
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements-docs.txt
      - run: mkdocs build --strict
      - if: github.ref == 'refs/heads/main'
        uses: actions/configure-pages@v5
      - if: github.ref == 'refs/heads/main'
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

현재 `deploy.needs: build`이므로 문서 빌드와 ROS·Gazebo 검사는 별도로 판정된다. 즉, 문서 사이트 배포 성공만으로 시뮬레이션 테스트까지 통과했다고 볼 수 없다. Jazzy 변경을 확인할 때는 Actions 화면에서 `build`와 `ros-gazebo` 결과를 각각 확인한다.

## 설치 결과와 버전 확인하기

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so" || exit 1
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf" || exit 1
gz sim --versions | sed -n '1,4p'
printf 'ci-inputs=installed\n'
```

이 블록은 개요에서 설정한 `TUTORIAL_INSTALL_BASE`를 사용한다. CI는 다음 버전 정보를 `resolved-versions.txt`에 기록한다.

```bash
printf 'ros_distro=%s\n' "$ROS_DISTRO"
dpkg-query -W -f='${Package}=${Version}\n' \
  ros-jazzy-ros-base ros-jazzy-ros-gz-bridge \
  gz-sim8-cli libgz-sim8-dev
gz sim --versions
gcc --version | head -n 1
g++ --version | head -n 1
```

## 재현성 점검표

- ROS·Gazebo 작업은 `ubuntu-24.04`에서 최대 30분 동안 실행한다.
- ROS 배포판은 Jazzy, Gazebo ABI는 Harmonic의 `gz-sim8`로 맞춘다.
- 소스 커밋 SHA와 실제 설치된 apt 패키지·컴파일러·Gazebo 버전을 함께 남긴다.
- 캐시는 빌드 가속용이며 설치 파일과 검증 결과를 대신하지 않는다.
- GUI 없는 검증 도구는 내부 제한 시간과 워크플로 시간 초과를 구분한다.
- 실패 경로에서도 로그, JSON, 프로세스 종료 기록을 보관 파일로 업로드한다.
- ROS·Gazebo 작업은 `contents: read`만 사용한다. Pages 관련 권한은 워크플로 상위에 선언되어 있다.
- 장기 재현이 필요하면 Action과 기본 이미지를 내용 식별자 또는 커밋 SHA로 고정한다.

## 문제 해결

| 증상 | 먼저 비교할 값 | 해결 방향 |
| --- | --- | --- |
| 로컬만 통과 | apt·Gazebo·컴파일러 버전 | `resolved-versions.txt`와 로컬 출력을 비교한다. |
| 캐시 사용 시만 실패 | 설치·빌드 디렉터리가 캐시에 섞임 | ccache 외 산출물을 캐시에서 제거한다. |
| Pages 권한 오류 | 워크플로와 배포 환경 권한 | 실행 작업이 아니라 배포 작업 권한을 확인한다. |
| 보관 파일이 비어 있음 | 실패 단계 뒤 업로드 조건 | `if: failure()` 또는 `always()`와 검증 결과 경로를 확인한다. |
| CI가 무기한 대기 | 내부 제한 시간과 프로세스 종료 처리 | 실행 도구 제한 시간이 워크플로 시간 초과보다 먼저 끝나게 한다. |

## 출처

- [Gazebo Harmonic with ROS 2 Jazzy](https://gazebosim.org/docs/harmonic/ros_installation/)
- [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [MkDocs Material publishing guide](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)

[이전: GUI 없는 통합 테스트](04-headless-integration.md) · [다음: 시뮬레이션 통합 검증 프로젝트](06_project-production-stack.md)
