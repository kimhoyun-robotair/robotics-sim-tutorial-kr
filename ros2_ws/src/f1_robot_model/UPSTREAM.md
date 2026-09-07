# 원본과 수정 범위

차량 모델과 메시의 원본은 [armando-genis/f1_robot_model](https://github.com/armando-genis/f1_robot_model)이다. 이 저장소의 기존 파일을 바탕으로 ROS 2 Humble / Gazebo Classic 11 실행 설정과 센서 예제를 수정했다.

루트 `LICENSE`의 Apache-2.0은 이 튜토리얼에 추가한 코드에 적용한다. 가져온 차량 메시에는 이 패키지에서 확인할 수 있는 별도 라이선스 파일이 없어 메시의 라이선스를 새로 지정하지 않았다. 원본 출처와 권리 표시를 함께 확인한다. `velodyne_simulator`는 해당 디렉터리의 BSD 라이선스와 저작권 표시를 따른다.

수정한 항목은 launch 중복 제거, 센서 선택 인자, 명시적인 센서 프레임, RGB-D·스테레오 토픽, odometry·TF, Classic 전용 조향 명령 변환, RViz QoS, 기본 실습 월드다. 기존 `demomap`, `demomap_2`, `my_world.sdf`, `empty_world.sdf`와 차량 메시 파일은 보존했다.

플러그인 동작을 확인한 공식 소스:

- [Ackermann 제어와 odometry (실제 검증 환경의 gazebo_ros_pkgs 3.9.0)](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_ackermann_drive.cpp)
- [카메라 토픽·보정 정보·optical 점군 변환](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_camera.cpp)
- [IMU 프레임과 월드 기준 자세](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_imu_sensor.cpp)

Classic 카메라는 optical 좌표의 PointCloud2를 발행한다. Gazebo Harmonic의 점군 좌표 처리 방식을 여기에 그대로 적용하면 안 된다.
