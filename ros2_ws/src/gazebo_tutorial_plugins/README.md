# gazebo_tutorial_plugins

ROS 2 Humble과 Gazebo Classic 11에서 사용하는 교육용 C++ ModelPlugin 패키지입니다.
`ground_truth_path_plugin`은 모델의 Gazebo world pose를 읽어 상대 ROS 이름
`ground_truth_path`에 `nav_msgs/msg/Path`로 발행합니다.

```bash
cd ~/gazebo-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select gazebo_tutorial_plugins
source install/setup.bash
colcon test --packages-select gazebo_tutorial_plugins
colcon test-result --verbose
```

삽입 가능한 Xacro 매크로는
`urdf/ground_truth_path_plugin.gazebo.xacro`에 있습니다. 설정과 RViz 확인,
플러그인 로딩 문제 해결은 저장소의 `docs/07_custom_plugin.md`를 참고하세요.
