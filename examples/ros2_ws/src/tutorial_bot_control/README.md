# tutorial_bot_control

`gz_ros2_control`이 사용하는 controller 설정을 설치하는 `ament_cmake` package이다.

- `joint_state_broadcaster`는 wheel joint 상태를 `/joint_states`로 발행한다.
- `diff_drive_controller`는 좌우 wheel 속도와 wheel odometry를 계산한다.
- `joint_trajectory_controller`는 controller 전환 실습에서 position interface를 검증한다.

실제 반지름과 윤거는 description Xacro의 `0.06 m`, `0.38 m`와
`config/controllers.yaml`에서 같아야 한다.
