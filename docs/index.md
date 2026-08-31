# Isaac Sim 5.1 한국어 과정

이 과정은 단순한 메뉴 번역이 아니라, Ubuntu 24.04와 ROS 2 Jazzy에서 로봇 시뮬레이션을 설계·구현·검증하는 능력을 기르는 실습서이다. 처음에는 GUI로 같은 장면을 눈으로 확인하고, 이후 USD와 Python, OmniGraph, ROS 2로 같은 작업을 자동화한다.

## 수료 후 할 수 있는 일

- Omniverse, Kit, OpenUSD, Isaac Sim, Isaac Lab의 경계를 설명하고 필요한 계층을 선택하다.
- USD stage와 layer composition을 안전하게 편집하고 URDF/Xacro/MJCF 자산을 가져오다.
- 강체·관절·articulation·drive를 구성하고 물리 오류를 진단하다.
- 카메라, RTX LiDAR·Radar, IMU, contact·effort 센서를 장착하고 데이터를 읽다.
- ROS 2 Jazzy와 clock, TF, odometry, control, Nav2, MoveIt 2를 연결하다.
- Python Extension, OmniGraph node, Replicator 파이프라인을 만들다.
- Isaac Lab의 환경·task·policy 학습 흐름과 Isaac Sim 배포 경계를 이해하다.

## 권장 순서

| 단계 | 디렉터리 | 목표 |
| --- | --- | --- |
| 0 | `course-guide` | 환경과 검증 규칙을 정하다. |
| 1 | `01-foundations` | 생태계와 USD mental model을 만들다. |
| 2 | `02-getting-started` | 설치하고 GUI에서 첫 stage를 완성하다. |
| 3 | `03-core` | 물리·로봇·제어를 코드로 재현하다. |
| 4 | `04-ros2` | Jazzy 그래프와 시뮬레이션을 연결하다. |
| 5 | `05-customization` | 자신의 로봇·환경·센서를 통합하다. |
| 6 | `06-developer` | 확장·데이터·학습 파이프라인을 만들다. |
| 7 | `07-projects` | 명세만 보고 다섯 프로젝트를 완성하다. |

## 버전 고정에 관한 경고

공식 사이트는 Isaac Sim 5.1.0을 지원 종료 릴리스로 표시한다. 이 과정은 5.1.0 재현을 우선하므로 최신 문서의 명령을 섞지 않는다. 링크가 최신 버전으로 자동 전환되었는지 URL의 `/5.1.0/`을 확인한다.

## 출처

- [What Is Isaac Sim?](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/index.html)
- [Reference Architecture and Task Groupings](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/reference_architecture.html)
- [Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)

