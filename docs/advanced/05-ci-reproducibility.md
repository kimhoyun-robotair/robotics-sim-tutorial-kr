# CI 재현성

> **목표:** Ubuntu 24.04·ROS 2 Jazzy·Gazebo Harmonic 입력을 고정하고 Pages와 headless runtime gate를 독립적으로 재현합니다.
> **선행 학습:** [Headless 통합 테스트](04-headless-integration.md)

## 같은 SHA, 분리된 gate

문서 배포와 simulation 검증은 같은 source SHA를 사용하지만 서로 다른 job입니다. Pages job은 strict MkDocs 결과를 배포하고, ROS job은 지원 저장소에서 의존성을 설치한 뒤 선택 패키지를 build·test하고 server-only nominal scenario를 실행합니다. runtime job은 GPU, secret, write permission을 요구하지 않습니다.

<figure class="course-figure" id="advanced-ci-reproducibility" style="box-sizing: border-box; max-width: 100%; overflow-x: auto; padding-bottom: 0.5rem; width: 100%;">
  <span style="display: block; font-size: 0.75rem;">모바일에서는 도식을 좌우로 스크롤하세요.</span>
  <img src="../../assets/advanced/ci-reproducibility.svg" alt="같은 source SHA에서 strict MkDocs Pages와 ROS Gazebo headless 검증이 독립적으로 evidence를 만드는 CI 구조도" loading="lazy" style="min-width: 720px;">
  <figcaption>그림 1. 문서와 runtime gate는 독립적으로 실패하지만 같은 source SHA와 artifact 보존 계약을 공유합니다.</figcaption>
</figure>

## 설치 결과와 도구 버전 확인

<!-- course-command -->
```bash
: "${TUTORIAL_INSTALL_BASE:?fresh install 경로가 필요합니다}"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
test -f "$TUTORIAL_INSTALL_BASE/tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
gz sim --versions | sed -n '1,4p'
printf 'ci-inputs=installed\n'
```

`gz sim --versions`는 runner에 실제로 resolve된 Gazebo library를 기록합니다. CI에서는 ROS distribution, compiler, apt package version, source SHA도 metadata에 함께 보존합니다.

## 재현성 checklist

- runner는 `ubuntu-24.04`, job timeout은 30분입니다.
- checkout과 action은 고정된 major를 사용합니다.
- dependency cache는 build/install/runtime evidence를 섞지 않습니다.
- headless checker는 bounded timeout과 cleanup receipt를 남깁니다.
- 실패해도 logs와 JSON evidence를 artifact로 업로드합니다.
- Pages 권한과 배포 dependency는 runtime job 추가 뒤에도 유지합니다.

## 문제 해결

로컬은 통과하고 CI만 실패하면 metadata의 apt·Gazebo·compiler 버전을 먼저 비교합니다. Pages가 막히면 runtime job이 아니라 Pages의 permission과 artifact dependency를 확인합니다. artifact가 비어 있으면 success banner를 만들기 전에 failure path에서도 evidence upload가 실행되는지 확인합니다.

## 출처

- [Gazebo Harmonic with ROS 2 Jazzy](https://gazebosim.org/docs/harmonic/ros_installation/)
- [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [MkDocs Material publishing guide](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)

[이전: Headless 통합 테스트](04-headless-integration.md) · [다음: Production Stack 프로젝트](project-production-stack.md)
