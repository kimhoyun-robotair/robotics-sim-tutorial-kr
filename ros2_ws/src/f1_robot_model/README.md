# f1_robot_model

ROS 2 Humble과 Gazebo Classic 11에서 F1TENTH 차량을 실행하는 패키지입니다. 처음 사용하는 경우 저장소 루트의 [F1TENTH 개요](../../../F1TENTH.md)와 [사용 안내](../../../F1TENTH_USERGUIDE.md)를 순서대로 읽으세요.

빌드한 작업 공간에서 환경을 적용한 뒤 실행합니다.

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch f1_robot_model robot_spawn.launch.py
```

기본 실행에서는 Building Editor로 만든 기존 `world/demomap_2/model.sdf`에 차량이 나타납니다. 차량의 초기 위치와 방향은 `x=0`, `y=0`, `z=0`, `yaw=0`이며, 바퀴·IMU·2D 라이다를 사용합니다. `display.launch.py`도 같은 기본 구성을 실행합니다.

RGB-D 카메라와 3D 라이다는 필요할 때 따로 켭니다. 기존 실행을 `Ctrl+C`로 종료한 뒤 아래 명령 중 하나를 실행하세요.

```bash
# RGB-D 카메라만 추가
ros2 launch f1_robot_model robot_spawn.launch.py depth_camera:=true

# 3D 라이다만 추가
ros2 launch f1_robot_model robot_spawn.launch.py lidar_3d:=true

# 두 센서를 함께 추가
ros2 launch f1_robot_model robot_spawn.launch.py depth_camera:=true lidar_3d:=true
```

기본 RViz 설정은 선택한 센서에 맞춰 표시를 켭니다. `depth_camera`, `lidar_3d`, `stereo_camera`, `gps`는 모두 기본값이 `false`입니다. 기본 실행에서 카메라·3D 라이다·GPS 토픽이 없는 것은 정상입니다. 좌우 카메라와 GPS가 필요한 경우에만 `stereo_camera:=true`, `gps:=true`를 추가하세요.

`gui:=false rviz:=false`를 붙이면 Gazebo와 RViz 창을 열지 않습니다. `/drive`의 메시지 형식은 `ackermann_msgs/msg/AckermannDriveStamped`입니다. 조향각과 각속도를 혼동하지 않도록 사용 안내의 주행 절을 확인하세요.

원본 모델 작성자: [armando-genis](https://github.com/armando-genis). 원본과 수정 범위, 라이선스 정보는 [UPSTREAM.md](UPSTREAM.md)에 있습니다.
