# F1TENTH 미니 프로젝트

앞바퀴의 방향을 바꿔 움직이는 소형 자동차를 Gazebo Classic 11에서 다뤄봅니다. ROS 2 Humble을 사용하며, 차동 구동 로봇 실습에서 익힌 모델·센서·TF를 차량에 적용합니다.

처음에는 기본 월드에서 차를 전진시키고 정지합니다. 그다음 RViz에서 라이다와 카메라가 같은 벽을 가리키는지 확인하고, 선택 센서를 켭니다. 마지막에는 기존 지도와 AMCL을 연결해 차량의 위치를 표시합니다. 빌드부터 종료까지의 명령은 [F1TENTH 사용 안내](F1TENTH_USERGUIDE.md)에 있습니다.

| 구성 | 역할 |
|---|---|
| `f1_robot_model` | 차량 URDF, 센서, 조향 명령 변환 노드, launch, 월드, RViz 설정 |
| `velodyne_simulator` 안의 세 패키지 | 3D 라이다 모델과 Gazebo Classic용 점군 플러그인 |
| 기본 센서 | 2D 라이다, RGB-D 카메라, IMU, GPS |
| 선택 센서 | 좌우 카메라 두 대, 3D 라이다 |

기본 월드는 외부 모델 다운로드 없이 실행됩니다. 좌우 카메라는 각각 영상과 보정 정보를 발행하며, 두 영상을 이용해 깊이를 계산하는 스테레오 처리 노드는 포함하지 않습니다. AMCL 예제는 지도 위 위치 추정까지 다룹니다. 자율 경로 계획이나 고속 레이싱 제어가 완성된 예제는 아닙니다.

이 차량의 Gazebo 플러그인은 `/cmd_vel`의 `angular.z`를 **조향각(rad)** 으로 읽습니다. 일반 ROS `Twist`의 각속도(rad/s)와 의미가 다르므로, 다른 주행 노드의 출력을 그대로 연결하기 전에 [명령 인터페이스 설명](F1TENTH_USERGUIDE.md#3-차량-주행하기)을 확인하세요.

원본 모델과 플러그인은 다음 프로젝트를 바탕으로 합니다. 원본 자산과 저작권 표시는 유지했으며, 수정 범위는 [UPSTREAM.md](ros2_ws/src/f1_robot_model/UPSTREAM.md)에 정리했습니다.

- [f1tenth_gtc_tutorial](https://github.com/linklab-uva/f1tenth_gtc_tutorial)
- [armando-genis/f1_robot_model](https://github.com/armando-genis/f1_robot_model)
- [Dataspeed velodyne_simulator](https://bitbucket.org/DataspeedInc/velodyne_simulator/src)
