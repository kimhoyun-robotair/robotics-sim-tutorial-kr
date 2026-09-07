# tutorial_bot_control

`gz_ros2_control`이 사용하는 컨트롤러 설정을 설치하는 `ament_cmake` 패키지이다.

| 컨트롤러 | 역할 | 기본 상태 |
|---|---|---|
| `joint_state_broadcaster` | 바퀴 조인트 상태를 `/joint_states`로 발행 | active |
| `diff_drive_controller` | 좌우 바퀴 속도, 오도메트리와 TF 계산 | active |
| `joint_trajectory_controller` | 바퀴 위치를 명령하는 전환 실습 | inactive |

바퀴 반지름 `0.06 m`와 좌우 바퀴 중심 간격 `0.38 m`는 Xacro와 `config/controllers.yaml`에서 같아야 한다. Jazzy의 DiffDrive 입력은 `/diff_drive_controller/cmd_vel`의 `geometry_msgs/msg/TwistStamped`이다. 예전 배포판의 `use_stamped_vel` 설정은 사용하지 않는다.

두 로봇 설정은 `config/multi_robot_controllers.yaml`에 있다. 프레임 이름을 `robot1/base_link`처럼 직접 지정하므로 `tf_frame_prefix_enable: false`로 네임스페이스가 이중으로 붙지 않게 한다.

## 확인

[중급 제어 실습](../../../../docs/04_intermediate/07-gz-ros2-control.md)의 launch를 실행하고 새 터미널에서 환경을 불러온 뒤 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

명령은 저장소 루트에서 실행한다. DiffDrive가 `active`이고 바퀴의 `velocity` 명령 인터페이스가 `[claimed]`이면 제어 준비가 된 것이다. 궤적 컨트롤러를 사용할 때는 DiffDrive를 먼저 비활성화하고, 실습 뒤 다시 활성화한다.
