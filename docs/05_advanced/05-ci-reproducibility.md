# CI 재현성

> **목표:** Ubuntu 24.04·ROS 2 Jazzy·Gazebo Harmonic 입력을 명시하고, 문서 build와 headless runtime gate를 같은 source SHA에서 독립적으로 재현한다.
> **선행 학습:** [Headless 통합 테스트](04-headless-integration.md)

## 재현성의 범위를 먼저 정하기

CI에서 “같다”는 말에는 여러 수준이 있다. 이 과정은 OS와 ROS/Gazebo major ABI, source SHA, 실행 명령을 고정하고 실제로 설치된 apt와 compiler 버전을 증거에 기록한다. apt 저장소의 최신 patch와 major tag 형태의 GitHub Action은 시간이 지나면 달라질 수 있으므로 bit-for-bit 재현을 보장하지는 않는다. 장기 보존이 필요하면 container digest, apt snapshot, action commit SHA까지 추가로 고정한다.

문서와 simulation은 같은 commit에서 시작하지만 서로 다른 job으로 판정한다.

| gate | 입력 | 핵심 명령 | 산출물 |
| --- | --- | --- | --- |
| 문서 | Markdown, MkDocs 설정 | `mkdocs build --strict` | Pages artifact |
| runtime | ROS workspace, world, plugin | colcon build/test + nominal scenario | logs, JSON evidence |

<figure class="course-figure" id="advanced-ci-reproducibility" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤한다.</span>
  <img src="../../assets/advanced/ci-reproducibility.svg" alt="같은 source SHA에서 strict MkDocs Pages와 ROS Gazebo headless 검증이 독립적으로 evidence를 만드는 CI 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 문서와 runtime gate는 독립적으로 실패하지만 같은 source SHA와 artifact 보존 계약을 공유한다.</figcaption>
</figure>

## Jazzy 브랜치 workflow 구성하기

branch trigger와 최소 권한을 먼저 선언한다. runtime job은 repository 읽기만 필요하고 Pages 배포 job만 Pages와 OIDC 쓰기 권한을 사용한다.

```yaml
name: Deploy documentation

on:
  push:
    branches: [Jazzy]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages-jazzy
  cancel-in-progress: false
```

`main`을 배포 대상으로 유지하는 저장소라면 trigger를 무조건 바꾸지 말고 branch별 preview workflow와 production Pages workflow를 분리한다. 중요한 점은 어떤 SHA를 검증하고 배포하는지 실행 화면에서 명확히 보이게 하는 것이다.

## runtime job 작성하기

실제 workflow는 Ubuntu 24.04 runner에서 container harness를 호출한다. cache에는 compiler 중간 결과만 넣고 install tree나 runtime evidence는 섞지 않는다.

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
          key: ros-jazzy-harmonic-${{ runner.arch }}-${{ hashFiles('examples/ros2_ws/src/tutorial_bot_plugins/**') }}
          restore-keys: ros-jazzy-harmonic-${{ runner.arch }}-
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

성공 증거도 장기간 비교할 계획이라면 마지막 step의 조건을 `if: always()`로 바꾸고 artifact 보존 기간을 조직 정책에 맞게 지정한다. 실패 분석만 목적이라면 현재처럼 `failure()`가 저장 공간을 줄인다.

## container에 플랫폼 명시하기

container는 Ubuntu 24.04 위에 Jazzy와 Harmonic ABI 패키지를 설치한다. 전체 Dockerfile을 복사하기보다 핵심 의존성을 보면 플랫폼 경계를 이해하기 쉽다.

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

Gazebo Harmonic의 `gz-sim8`과 플러그인의 `find_package(gz-sim8 REQUIRED)`가 일치해야 한다. build container에서만 우연히 구버전 library를 찾는 일을 막으려면 이전 install 디렉터리를 mount하지 않고 매 실행에서 `/work/install`을 새로 만든다.

container 실행도 권한과 쓰기 범위를 제한한다.

```bash
docker run --name "$container" \
  --network bridge \
  --read-only \
  --tmpfs /work:exec,size=4g \
  --tmpfs /tmp:exec,size=512m \
  -v "$source_root:/source:ro" \
  -v "$evidence:/evidence" \
  -v "$cache:/ccache" \
  "$image" --source /source --evidence /evidence --scenario nominal
```

## build, test, smoke를 순서대로 묶기

container 내부에서는 대상 package만 명시적으로 build하고 테스트 결과를 확인한 뒤 headless scenario를 실행한다.

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
  --packages-select tutorial_bot_plugins tutorial_bot_tests
colcon test-result --test-result-base /work/build --verbose

./scripts/check_advanced_course.sh \
  --scenario nominal \
  --install-base /work/install \
  --evidence /evidence/smoke
```

`colcon test` 명령이 0이어도 `colcon test-result --verbose`로 실패 결과가 없는지 확인한다. smoke는 source world가 아니라 `/work/install`의 world와 library를 사용해 install 규칙까지 검증한다.

## 문서 job과 배포 job 분리하기

```yaml
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements-docs.txt
      - run: mkdocs build --strict
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build-docs
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

runtime 실패도 배포를 막아야 한다면 `deploy.needs`를 `[build-docs, ros-gazebo]`로 지정한다. 문서 미리보기와 runtime gate를 독립적으로 운영하려면 현재처럼 dependency를 분리한다. 선택은 repository 보호 규칙과 배포 정책에 맞춰 명시한다.

## 설치 결과와 버전 확인하기

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요하다}"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim --versions | sed -n '1,4p'
printf 'ci-inputs=installed\n'
```

CI는 다음 metadata를 `resolved-versions.txt`에 기록한다.

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

- runner는 `ubuntu-24.04`, job timeout은 30분으로 설정한다.
- ROS distribution은 Jazzy, Gazebo ABI는 Harmonic의 `gz-sim8`로 맞춘다.
- source SHA와 resolved apt·compiler·Gazebo 버전을 함께 남긴다.
- cache는 build 가속용이며 install과 판정 evidence를 대신하지 않는다.
- headless checker는 내부 deadline과 workflow timeout을 구분한다.
- 실패 경로에서도 logs, JSON, cleanup receipt를 artifact로 업로드한다.
- Pages 권한은 deploy 범위에만 두고 runtime job에는 `contents: read`만 둔다.
- 장기 재현이 필요하면 action tag와 base image를 digest 또는 commit SHA로 고정한다.

## 문제 해결

| 증상 | 먼저 비교할 값 | 해결 방향 |
| --- | --- | --- |
| 로컬만 통과 | apt·Gazebo·compiler 버전 | `resolved-versions.txt`와 로컬 출력을 비교한다. |
| cache 사용 시만 실패 | install/build 디렉터리 혼입 | ccache 외 산출물을 cache에서 제거한다. |
| Pages 권한 오류 | workflow와 environment 권한 | runtime job이 아니라 deploy 권한을 확인한다. |
| artifact가 비어 있음 | 실패 step 뒤 upload 조건 | `if: failure()` 또는 `always()`와 evidence 경로를 확인한다. |
| CI가 무기한 대기 | 내부 timeout과 process cleanup | harness deadline이 workflow timeout보다 먼저 끝나게 한다. |

## 출처

- [Gazebo Harmonic with ROS 2 Jazzy](https://gazebosim.org/docs/harmonic/ros_installation/)
- [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [MkDocs Material publishing guide](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)

[이전: Headless 통합 테스트](04-headless-integration.md) · [다음: Production Stack 프로젝트](06_project-production-stack.md)
