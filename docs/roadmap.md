# 학습 로드맵

`tutorial_bot` 하나를 다음 세 단계에서 누적해 완성합니다.

| 단계 | 완성 상태 | 핵심 산출물 |
| --- | --- | --- |
| 초급 | 두 바퀴, DiffDrive, LiDAR, 카메라, IMU | SDF world와 기본 로봇, ROS 2 bridge |
| 중급 | TF, controller, RViz, Nav2 | 하나의 ROS 2 launch로 구동하는 simulation stack |
| 고급 | System Plugin, headless test, CI | 검증 가능한 production-style simulation stack |

각 장은 앞 장의 파일을 대체하기보다 필요한 기능을 추가합니다. 로봇의 형상과 링크 구조는 URDF/Xacro를 원본으로 관리하고, SDF는 world와 Gazebo 전용 설정에 사용합니다.

## 현재 시작 지점

현재는 기반 문서와 초급의 첫 실습을 제공합니다. 다음 실습부터 `tutorial_bot`의 URDF/Xacro와 바퀴를 만들며, `examples/ros2_ws/src/`의 패키지 디렉터리를 실제 구현에 맞춰 채웁니다.
