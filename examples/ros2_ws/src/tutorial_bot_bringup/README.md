# tutorial_bot_bringup

ROS 2 launch, bridge YAML, RViz 설정, wheel-odom Path node를 설치하는 `ament_cmake` package이다.

- `config/bridge.yaml`: native DiffDrive 기본 robot용 bridge이다.
- `config/bridge-sensor-gallery.yaml`: mono·stereo·RGB-D·fisheye·2D/3D LiDAR gallery용 bridge이다.
- `launch/simulation.launch.py`: Gazebo, `gz_ros2_control`, 센서 bridge, TF, RViz를 함께 실행한다.
- `launch/rover.launch.py`: 4륜 skid-steer와 Ackermann rover 가운데 하나를 선택해 실행한다.
- `scripts/odom_to_path`: `/odom` pose를 `/wheel_odom_path`로 누적한다.
- `rviz/tutorial_bot.rviz`: sensor와 wheel odom trajectory display를 제공한다.
- `rviz/rover.rviz`: 4륜 rover의 odometry와 trajectory를 `odom` 기준으로 표시한다.
