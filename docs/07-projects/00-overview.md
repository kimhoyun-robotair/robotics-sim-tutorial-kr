# 미니 프로젝트 운영 방법

각 프로젝트는 앞 장의 실습을 연결해 하나의 결과물을 만드는 과정이다. 준비 단계와 기준 예제를 먼저 완료하고, 조건 하나를 바꾼 뒤 결과를 다시 확인한다. 프로젝트 3은 세 목표의 실제 Nav2 결과를 저장하고, 프로젝트 4는 RGB-D 좌표 계산부터 로봇 입력 교체까지 단계적으로 진행한다.

| 번호 | 난이도 | 주제 | 핵심 산출물 |
| --- | --- | --- | --- |
| 1 | 입문 | [USD 물리 실험실](01-usd-physics-lab.md) | 레이어를 나눈 장면과 물리 상태 검사 |
| 2 | 초중급 | [이동 로봇](02-custom-mobile-robot.md) | 실제 URDF 가져오기, 바퀴 제어, 센서와 TF |
| 3 | 중급 | [창고 자율주행](03-warehouse-navigation.md) | 지도와 세 목표 주행 결과 |
| 4 | 중상급 | [시각 기반 집기](04-vision-pick-place.md) | RGB-D 위치 추정과 집기 평가 |
| 5 | 고급 | [정책 학습·평가](05-isaac-lab-policy.md) | 체크포인트 재실행과 정책 배포 조건 |

## 공통 제출 구조

```text
project-N/
├── README.md                 # 재현 명령과 설계 결정
├── config/                   # YAML/JSON/robot config
├── scripts/                  # 생성·검증·실행 script
├── assets/manifest.yaml      # 대형 asset의 URL/hash/license
├── stages/                   # 직접 작성한 USD layer
├── tests/                    # headless/ROS smoke test
└── results/
    ├── metrics.json
    └── screenshots-or-video.md
```

대형 NVIDIA 자산과 생성 데이터셋은 소스 저장소와 별도로 관리한다. 공식 자산 경로, 라이선스, 사용 버전과 파일 해시를 기록해 같은 입력으로 다시 실행할 수 있게 한다.

## 공통 채점 기준

| 항목 | 비율 | 통과 기준 |
| --- | ---: | --- |
| 재현성 | 25 | 새 터미널에서 문서의 명령만으로 실행한다. |
| 물리·좌표 정확성 | 20 | 단위, 축, 관절, TF를 수치로 확인한다. |
| 자동 검증 | 20 | 물리 또는 ROS 검사에서 의도적으로 넣은 오류를 검출한다. |
| 구조·유지보수 | 15 | 원본 자산, 설정, 실행 결과를 나누어 관리한다. |
| 분석 | 10 | 성공과 실패를 모두 수치로 기록한다. |
| 문서·출처 | 10 | 결정 이유와 공식 출처를 남긴다. |

실행한 환경과 검증 범위를 결과에 함께 적는다. 문법 검사만 했다면 물리·렌더링·ROS 통신을 통과했다고 기록하지 않는다.

## 출처

- [Isaac Sim Quick Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_index.html)
- [Standalone Examples Reference List](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/standalone_examples_list.html)
- [Isaac Sim Conventions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_conventions.html)
