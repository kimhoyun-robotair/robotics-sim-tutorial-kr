## 기본적인 안내
- `cartographer` : Google에서 작성한, SLAM을 위한 C++ 라이브러리
- `cartographer_ros` : cartographer의 ROS2 Wrapper
- `f1_robot_model` : Gazebo classic 시뮬레이션을 위한 `URDF, SDF` 파일, cartographer 시뮬레이션을 위한 `lua, pbstream` 파일 등을 제공
- `velodyne_simulator` : 3D LiDAR인 Velodyne을 Gazebo classic에서 시뮬레이션 하기 위한 각종 플러그인 및 코드 파일 제공
- 기본적으로 모든 launch 파일에 `joy_node` 및 `teleop_twist_joy` 통합 (필요시 주석을 해제하고 사용할 것)

### 1. 설치 방법
---
```bash
# step 1.
$ sudo apt update
$ sudo apt install -y \
    cmake g++ git google-mock libceres-dev liblua5.3-dev \
    libprotobuf-dev libsuitesparse-dev libwebp-dev ninja-build \
    protobuf-compiler python3-sphinx libgflags-dev stow
$ git clone https://github.com/kimhoyun-robotair/F1TENTH_Simulation.git
$ cd F1TENTH_Simulation/src/cartographer/scripts
$ ./install_abseil.sh

# step 2.
$ cd && cd F1TENTH_Simulation
$ colcon build --symlink-install
# It takse few minute
$ source install/setup.bash
# or source install/local_setup.bash
```

### 2. gazebo classic simulation 사용 방법
---
**1. 순수하게 로봇만 `gazebo`에 `spawn`하고 싶다면**
```bash
$ ros2 launch f1_robot_model robot_spawn.launch.py
```

**2. 내가 작성한 `world 파일(.sdf)`까지 `spawn`하고 싶다면**
```bash
$ ros2 launch f1_robot_model display.launch.py
```
- `~/src/f1_robot_model/world` 파일 내부, 그리고 `display.launch.py` 파일의 `world_path` 부분을 수정해서 커스텀 `world` 파일을 upload 및 spawn 할 수 있음

**3. URDF 파일로부터 odom 토픽과 odom 프레임이 자동으로 나오게 하려면**
- `~/src/f1_robot_model/urdf/racecar.gazebo` 내부 코드 수정
```xml
      <!-- output -->
      <publish_odom>true</publish_odom>
      <publish_odom_tf>true</publish_odom_tf>
      <publish_wheel_tf>true</publish_wheel_tf>
      <publish_distance>true</publish_distance>

      <odometry_frame>odom</odometry_frame>
      <robot_base_frame>base_link</robot_base_frame>
```
- `cartographer` 동작을 위해서는 `odom_tf`를 `false`로 해야하며, `odom` 토픽은 필요에 따라서 정해쓸 것

### 3. AMCL을 사용하고 싶다면
---
**1. AMCL 사용하기**
```bash
$ ros2 launch f1_robot_model amcl.launch.py
```
- 관련해서 `~/f1_robot_model/map` 과 `~/f1_robot_model/config` 내부에 AMCL 관련된 설정 파일 및 demomap 파일이 들어있음