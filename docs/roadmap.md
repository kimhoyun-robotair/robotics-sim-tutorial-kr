# 학습 로드맵

`tutorial_bot` 하나를 다음 세 단계에서 누적해 완성합니다.

| 단계 | 완성 상태 | 핵심 산출물 |
| --- | --- | --- |
| 초급 | 두 바퀴, DiffDrive, LiDAR, 카메라, IMU | SDF world와 기본 로봇, ROS 2 bridge |
| 중급 | TF, controller, RViz, Nav2 | 하나의 ROS 2 launch로 구동하는 simulation stack |
| 고급 | System Plugin, headless test, CI | 검증 가능한 production-style simulation stack |

각 장은 앞 장의 파일을 대체하기보다 필요한 기능을 추가합니다. 로봇의 형상과 링크 구조는 URDF/Xacro를 원본으로 관리하고, SDF는 world와 Gazebo 전용 설정에 사용합니다.

## 현재 과정 계약

초급 12개, 중급 12개, 고급 7개 경로를 `docs/course-manifest.yaml`에서 고정합니다.
실행 결과는 source SHA와 cleanup receipt가 일치할 때만 현재 증거로 인정합니다.

## 검증 상태

세 과정의 필수 runtime은 nominal과 fault mode를 모두 실행하며, 각 scenario의 파싱된 observable과 owned-process cleanup receipt가 함께 통과해야 완료입니다. 정적 문서만 통과하거나 runtime을 건너뛴 결과는 완료로 표시하지 않습니다.
