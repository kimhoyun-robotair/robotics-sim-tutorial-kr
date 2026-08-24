# TF·Joint State·RViz 검증

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `ros_gz_bridge` 심화

## 학습 목표

- `odom → base_link → sensor_link` TF 트리를 확인합니다.
- joint state와 TF의 역할을 구분합니다.
- RViz에서 RobotModel, LaserScan, PointCloud2를 관찰합니다.

## 배경 지식

Gazebo는 물리를 계산하고 RViz는 ROS 메시지와 TF를 시각화합니다. `robot_state_publisher`는 URDF와 joint state로 link TF를 만들며, diff drive controller는 `odom → base_link`를 제공합니다. Nav2 전 단계에서는 `map → odom`이 없어도 정상입니다.

## 예제 파일

- `examples/ros2_ws/src/tutorial_bot_bringup/rviz/tutorial_bot.rviz`
- `examples/ros2_ws/src/tutorial_bot_bringup/launch/simulation.launch.py`

## 실행

```bash
./scripts/check_intermediate_control_tf.sh --launch
```

GUI로 관찰하려면 다음 launch 인자를 사용합니다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py nav2:=false gui:=true rviz:=true
```

## 결과 확인

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 topic echo /joint_states --once
```

검증 스크립트는 여섯 frame의 반복 표본, 중복 parent 부재, controller 전환과 실제 변위를 확인합니다.

## 동작 원리

고정 joint는 URDF에서 정적 TF가 되고 바퀴 joint는 `/joint_states`를 통해 갱신됩니다. RViz의 fixed frame은 Nav2 전에는 `odom`, Nav2 사용 시에는 `map`입니다.

## 문제 해결

RViz의 Message Filter 오류는 토픽 자체보다 frame 연결이나 timestamp 문제일 수 있습니다. `use_sim_time`과 `/clock`, 메시지의 `frame_id`를 함께 확인합니다.

## 정리

TF와 joint state를 함께 검사해야 Gazebo의 운동이 ROS 2 시각화까지 올바르게 전달됐다고 말할 수 있습니다.
