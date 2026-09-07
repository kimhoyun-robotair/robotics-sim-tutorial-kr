# f1_robot_model

ROS 2 Humble과 Gazebo Classic 11에서 F1TENTH 차량을 실행하는 패키지입니다. 처음 사용하는 경우 저장소 루트의 [F1TENTH 개요](../../../F1TENTH.md)와 [사용 안내](../../../F1TENTH_USERGUIDE.md)를 순서대로 읽으세요.

빌드한 작업 공간에서 환경을 적용한 뒤 실행합니다.

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch f1_robot_model robot_spawn.launch.py
```

기본 센서는 2D 라이다, RGB-D 카메라, IMU, GPS입니다. `stereo_camera:=true`, `lidar_3d:=true`로 센서를 추가하고, `gui:=false rviz:=false`로 화면 없이 실행할 수 있습니다. `/drive`의 메시지 형식은 `ackermann_msgs/msg/AckermannDriveStamped`입니다. 조향각과 각속도를 혼동하지 않도록 사용 안내의 주행 절을 확인하세요.

원본 모델 작성자: [armando-genis](https://github.com/armando-genis). 원본과 수정 범위, 라이선스 정보는 [UPSTREAM.md](UPSTREAM.md)에 있습니다.
