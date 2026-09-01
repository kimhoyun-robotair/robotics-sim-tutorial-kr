## 전체 요약
---
본 패키지는 F1TENTH를 위한 Gazebo classic 베이스의 시뮬레이터를 개발하는 것을 목적을 개발되었습니다. 본 패키지는 여러 패키지를 포함하고 있는 메타-패키지기 때문에 사용이 상당히 복잡하므로, 여러 설명서를 포함하고 있습니다. 따라서 설명서를 주의 깊게 읽고 진행하는 것을 추천드립니다.

또한, 본 패키지는 다음과 같은 센서들에 대한 시뮬레이션 기능을 제공합니다.
- 2D LiDAR
- Depth Camera
- Stereo Camera
- 3D LiDAR
- IMU and GPS

만약, 사용에 문제점 혹은 의문점이 있다면
**alpha12334@naver.com** 혹은 **suberkut76@gmail.com** 으로 연락 부탁드립니다.

본 패키지는 다음과 같은 구성으로 되어 있습니다.
- **f1_robot_model** : F1TENTH 모델링 및 각종 launch, 설정 파일이 담긴 패키지
- **velodyne_simulator** : 3D LiDAR 시뮬레이션을 위한 의존성 패키지

본 패키지를 개발하는데 있어서, 매우 큰 도움이 되었던 다음 오픈소스 개발진들에게 감사하다는 말씀을 드리고 싶습니다.
- [f1tenth_gtc_tutorial](https://github.com/linklab-uva/f1tenth_gtc_tutorial)
- [f1_robot_model](https://github.com/armando-genis/f1_robot_model)
- [velodyne_simulator](https://bitbucket.org/DataspeedInc/velodyne_simulator.git/src)
