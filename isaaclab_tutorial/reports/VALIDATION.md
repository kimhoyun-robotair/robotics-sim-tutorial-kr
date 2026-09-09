# 작성 시점의 검증 기록

확인일: **2026-09-09**. 기준: **Isaac Lab `v3.0.0-beta2.patch1`**, 공식 소스 커밋 **`ffff603eafc6b74264a5261cc0183d6a65390d78`**.

## 실제로 수행한 검사

| 검사 | 결과 | 증거 |
| --- | --- | --- |
| 최신 공개 릴리스·태그·의존성 확인 | 3.0 Beta 2 Patch 1, Isaac Sim 6.0.1, Python 3.12 선택 | [버전 기록](../version-lock.json), [공식 릴리스](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1) |
| 공식 API와 실행 인자 대조 | PhysX 타입, XYZW, ProxyArray, reset 순서, 카메라·학습·평가 API 대조 완료 | [공식 자료 대응표](../docs/05-official-reference-map.md), [확인한 소스 해시](upstream-source-manifest.json) |
| Python 파일 문법 | 실행 코드·검사 도구·테스트 총 12개 AST 검사 통과 | [정적 검사 JSON](static-checks.json) |
| Shell 파일 문법 | 실행 검사 스크립트 1개 `bash -n` 통과 | [정적 검사 JSON](static-checks.json) |
| 본문 코드 블록 문법 | Python 38개, Bash 70개, Bash 내부 Python heredoc 5개 통과 | [본문 코드 검사 JSON](document-code-checks.json) |
| 문서 구조·경로 | 01–36단계의 중복·누락 없음, 상대 파일·단계 링크와 태그 소스 경로 확인 | [정적 검사 JSON](static-checks.json) |
| 영상 판정 함수 CPU 테스트 | 10개 통과 | [CPU 테스트 출력](cpu-tests.txt) |
| 정책 평가 집계 CPU 테스트 | 5개 통과 | [CPU 테스트 출력](cpu-tests.txt) |
| 작성 환경의 GPU 실행 사전 점검 | 실패: NVIDIA GPU 도구·CUDA·Isaac Sim 패키지가 없음 | [실제 사전 점검 결과](authoring-preflight.json) |

코드 블록 문법 검사는 import가 가능한지나 물리적으로 올바른 결과가 나오는지를 검사하지 않는다. 공식 소스와의 대조 역시 해당 환경에서 실행해 본 결과는 아니다. CPU 테스트의 영상과 에피소드 데이터는 명시적으로 만든 합성 fixture이며 시뮬레이터 실측 자료가 아니다.

영상 판정 테스트는 정상 영상, 배경의 정상 `+inf` depth, 불투명 alpha를 가진 검은 RGB, 단색 영상, NaN, 잘못된 배열 크기·거리 단위·표적 ROI를 다룬다. 평가 집계 테스트는 다른 순서의 seed 대응, 조기 실패 포함, 종료와 시간 제한 구분, 서로 다른 프로토콜·초기조건 거부, NaN·불완전 결과 거부, 원자적 JSON 저장, CSV 출력을 다룬다.

독립적인 소스 검토에서 평가 샘플이 자동 reset **이전**에 기록되는지 확인했다. 서로 다른 보상의 총합 대신 동일한 환경에서 막대 각도, 카트 이동, 명령 힘, 행동 변화, 종료 이유를 비교한다. 시간 제한까지 도달한 비율을 막대 균형 성공률로 표현하지 않는다.

## 이 환경에서 실행하지 못한 검사

| 항목 | 상태 | GPU PC에서 필요한 증거 |
| --- | --- | --- |
| Isaac Sim 첫 실행·GUI | 미실행 | 설치 로그, 실제 창과 단계별 조작 |
| p01 조명 장면 | 미실행 | 정상 종료와 GUI 관찰 |
| p02 낙하·정착·두 번의 reset | 미실행 | 높이·선속도·각속도의 연속 정착 구간 JSON |
| p03 Franka 자세 유지 | 미실행 | 팔·손가락의 단위별 오차·속도, 고정 root 이동 JSON |
| p04 RTX RGB/depth | 미실행 | RGB PNG, 원본 배열, 90개 검사 프레임의 실제 보고서 |
| 접촉 센서·RayCaster | 미실행 | 발 접촉력·유효 hit·좌표계와 화면 확인 |
| Cartpole·Franka·ANYmal 학습 | 미실행 | 실제 로그·체크포인트·학습 설정·재생 영상 |
| 두 보상의 3개 학습 seed 비교 | 미실행 | 여섯 체크포인트, 공통 평가의 JSON·CSV |
| 키보드 시연·Mimic | 미실행 | 성공 시연 기록·재생 및 데이터 파일 |
| ROS 2 Jazzy 연결 | 미실행, 필수 과정에서 사용하지 않음 | 확장 시 시계·관절 이름·좌표·QoS 별도 검증 |

**실제 렌더링이 정상이고 로봇이 무너지지 않으며 노이즈가 없다는 검증 완료 주장은 하지 않는다.** 자동 판정 기준은 명시된 작은 실습 장면의 진단 기준이다. GPU에서 보정한 범용 임계값이 아니다. 운용 환경의 GPU·드라이버·자산 다운로드·렌더러 상태를 포함한 결과는 해당 장비에서 확인해야 한다.

## 사용자 GPU에서 재현하기

01–05단계의 설치와 Python 가상환경 활성화를 마친 뒤 실행한다.

```bash
export ISAACLAB_ROOT="$HOME/IsaacLab"
export TUTORIAL_ROOT="$HOME/robotics-sim-tutorial-kr"
source "$ISAACLAB_ROOT/env_isaaclab/bin/activate"
bash "$TUTORIAL_ROOT/isaaclab_tutorial/tools/run_gpu_checks.sh"
```

이 스크립트는 사전 점검을 통과한 뒤 p01–p04를 순서대로 실행한다. 어느 하나라도 오류나 시간 초과로 끝나면 즉시 중단한다. 기본 제한은 프로그램당 900초이며, 첫 shader 준비가 느린 PC에서는 원인을 확인한 뒤 `ISAACLAB_CHECK_TIMEOUT`을 조정한다. 사전 점검 통과는 RT 코어·렌더러 호환성 인증이 아니다.

창 없이 실행한 수치 검사가 통과해도 p01–p04를 `--viz kit`으로 확인하고, 저장한 RGB PNG를 열어 화면을 검토한다. 접촉·raycast 예제는 20–22단계를 별도로 실행한다. 학습·평가는 26–36단계 순서를 따른다. 결과가 없는 항목은 계속 미실행으로 남긴다.

## 커밋 범위

대상 저장소에 `IsaacLab` 브랜치를 생성하고, 이 브랜치의 `README.md`와 `isaaclab_tutorial/`만 작성했다. 시작 커밋은 `ad8f52011630ef49488793c6c5a7fbbb03f9ecc6`이다. 다른 브랜치의 파일·참조를 수정하거나 삭제하는 작업은 수행하지 않는다.
