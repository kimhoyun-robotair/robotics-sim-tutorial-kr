# 미니 프로젝트 운영 방법

다섯 프로젝트는 앞 장의 명령을 그대로 따라 쓰는 문제가 아니다. 요구사항, 완료 조건, 검증 방법을 제공하며 사용자가 설계를 선택하다. 모든 프로젝트는 작은 smoke test부터 만들고 기능을 한 번에 하나씩 추가하다.

| 번호 | 난이도 | 주제 | 핵심 산출물 |
| --- | --- | --- | --- |
| 1 | 입문 | USD 물리 실험실 | layer가 분리된 stage와 headless 검증 script |
| 2 | 초중급 | 커스텀 이동 로봇 | URDF/Xacro→USD robot과 ROS 2 control graph |
| 3 | 중급 | 창고 자율주행 | custom environment, RTX LiDAR, map, Nav2 run |
| 4 | 중상급 | vision pick-and-place | manipulator, motion generation, camera dataset |
| 5 | 고급 | Isaac Lab policy | vectorized task, 학습·평가·Isaac Sim 배포 contract |

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

대형 NVIDIA asset과 생성 dataset을 repository에 복제하지 않다. 공식 asset path, license, 사용 version, hash 또는 immutable identifier를 manifest에 남기다.

## 공통 채점 기준

| 항목 | 비율 | 통과 기준 |
| --- | ---: | --- |
| 재현성 | 25 | 새 terminal에서 문서의 명령만으로 실행하다. |
| 물리·좌표 정확성 | 20 | 단위, axis, joint, TF가 검증되다. |
| 자동 검증 | 20 | 최소 한 개 headless 또는 ROS test가 실패를 검출하다. |
| 구조·유지보수 | 15 | asset, config, runtime output이 분리되다. |
| 분석 | 10 | 성공뿐 아니라 failure case를 수치로 기록하다. |
| 문서·출처 | 10 | 결정 이유와 공식 출처를 남기다. |

## 출처

- [Isaac Sim Quick Tutorials](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_index.html)
- [Standalone Examples Reference List](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/standalone_examples_list.html)
- [Isaac Sim Conventions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_conventions.html)
