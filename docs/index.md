# Isaac Sim 5.1 한국어 실습 튜토리얼

Ubuntu 24.04 LTS · ROS 2 Jazzy · Isaac Sim 5.1.0을 사용한다. Isaac Sim을 처음 켜는 사람도 따라올 수 있도록, 상자를 만드는 GUI 실습부터 로봇·센서·ROS 2·심화 프로젝트까지 **36단계**로 구성했다.

## 어디서 시작하면 되는가

| 상황 | 읽을 문서 |
| --- | --- |
| Isaac Sim이 처음이다 | [36단계 학습 과정](course-guide.md) |
| 설치부터 진행하고 싶다 | [사전 점검](02-getting-started/01-system-requirements.md), [설치](02-getting-started/02-workstation-installation.md) |
| 화면 조작을 모르겠다 | [GUI 기초](02-getting-started/04-gui-interface.md), [첫 물리 장면](02-getting-started/05-first-scene-and-physics.md) |
| GUI·Extension·Python 중 무엇을 쓸지 모르겠다 | [실행 방식 비교와 같은 장면 예제](06-developer/01-python-workflows.md) |
| 4.x나 5.0 코드를 옮기고 있다 | [버전별 변경사항과 이관 예제](appendices/release-notes-4x-to-5-1.md) |
| 로봇이 무너지거나 센서 출력이 이상하다 | [검증 방법](05-customization/04-validation-performance.md), [실제 검증 범위](appendices/validation-report.md) |
| 최종 프로젝트를 진행하고 싶다 | [다섯 프로젝트](07-projects/00-overview.md) |
| 공식 원문을 찾아보고 싶다 | [공식 문서 대응표](appendices/official-docs-coverage.md) |

## 이 과정에서 만드는 것

처음에는 바닥에 떨어지는 상자를 저장하고 다시 연다. 이후 공식 로봇을 제어하고 RGB·depth·IMU·RTX LiDAR 데이터를 읽는다. ROS 2의 시간·TF·센서·제어를 연결한 뒤 창고 자율주행, 비전 집기, 학습된 정책 적용으로 확장한다. 같은 작업을 GUI, Script Editor, Extension, standalone Python에서 어떻게 구성하는지도 비교한다.

전체 파일로 제공하는 실행 예제와 설명을 위한 부분 코드를 구분한다. 각 실습은 준비 조건, 실행 위치, 예상 결과와 실패 시 확인할 항목을 설명한다. 카메라는 배열이 반환됐는지뿐 아니라 실제 영상도 확인하고, 로봇은 화면에 나타났는지뿐 아니라 자세와 제어 결과도 검사한다.

## 버전과 검증 범위

NVIDIA는 현재 5.1.0을 지원 종료 버전으로 표시한다. 이 과정은 요청한 조합을 재현하기 위해 5.1.0에 고정한다. `/latest/` 문서나 다른 버전 코드를 섞지 않는다.

정적 검사와 GPU 실행 검사는 별개다. 이번 수정 환경에는 Isaac Sim·RTX GPU·ROS 2가 없어 물리·렌더·DDS 실행 결과를 확인하지 못했다. [검증 기록](appendices/validation-report.md)에 실행한 검사와 남은 검사를 구분했다. 예제에는 실제 장비에서 결과를 판정하고 기록할 수 있는 검사 코드를 제공한다.

## 출처

- [NVIDIA Isaac Sim 5.1.0](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)
- [Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
