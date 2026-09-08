# 원본과 수정 범위

차량 모델과 메시의 원본은 [armando-genis/f1_robot_model](https://github.com/armando-genis/f1_robot_model)이다. 이 저장소의 기존 파일을 바탕으로 ROS 2 Humble / Gazebo Classic 11 실행 설정과 센서 예제를 수정했다.

루트 `LICENSE`의 Apache-2.0은 이 튜토리얼에 추가한 코드에 적용한다. 가져온 차량 메시에는 이 패키지에서 확인할 수 있는 별도 라이선스 파일이 없어 메시의 라이선스를 새로 지정하지 않았다. 원본 출처와 권리 표시를 함께 확인한다. `velodyne_simulator`는 해당 디렉터리의 BSD 라이선스와 저작권 표시를 따른다.

기본 실습은 재점검 전 커밋 `d1b01698b16af03616a62b414a132926989091a6`의 `display.launch.py`를 기준으로 복원했다. Building Editor로 만든 `world/demomap_2/model.sdf`와 지도, 차량 메시·차축 위치·바퀴 치수는 원본 그대로 사용한다. `robot_spawn.launch.py`와 `display.launch.py` 모두 이 월드의 원점 `(0, 0, 0)`에 차량을 생성한다. 이전 재점검에서 추가한 센서 시험용 월드와 차체 충돌 상자는 제거했다.

기본 구성은 네 바퀴, IMU, 2D 라이다다. 원본 파일에는 GPS 플러그인도 켜져 있었지만, 이번에 지정한 기본 구성에 맞춰 GPS의 링크와 플러그인을 함께 끈다. RGB-D 카메라와 3D 라이다는 `depth_camera:=true`, `lidar_3d:=true`로 각각 추가한다. 좌우 카메라와 GPS의 기존 선택 기능도 남아 있으며 모두 기본값은 `false`다.

주행과 센서 표시가 올바르게 동작하는 데 필요한 수정은 유지했다. 여기에는 유효한 URDF material 위치와 메시 경로, 조향 조인트 제한, 실제 조인트 상태를 이용한 단일 TF 발행, odometry, Classic 플러그인에 맞춘 조향각 변환, 센서 프레임·카메라 보정값·RViz QoS가 포함된다. RGB-D 점군과 3D 라이다는 켠 경우에만 RViz에서도 자동으로 표시한다. 사용자가 직접 지정한 RViz 설정 파일은 수정하지 않는다.

플러그인 동작을 확인한 공식 소스:

- [Ackermann 제어와 odometry (실제 검증 환경의 gazebo_ros_pkgs 3.9.0)](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_ackermann_drive.cpp)
- [카메라 토픽·보정 정보·optical 점군 변환](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_camera.cpp)
- [IMU 프레임과 월드 기준 자세](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/3.9.0/gazebo_plugins/src/gazebo_ros_imu_sensor.cpp)

Classic 카메라는 optical 좌표의 PointCloud2를 발행한다. Gazebo Harmonic의 점군 좌표 처리 방식을 여기에 그대로 적용하면 안 된다.
