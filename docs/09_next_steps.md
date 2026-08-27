# 꼭 알아야 할 설계 원칙과 다음 단계

예제를 한 번 움직이는 것과 재현 가능한 시뮬레이션 시스템을 만드는 것은 다릅니다. 이 장은 실습을 실제 로봇 프로젝트로 확장할 때 가장 먼저 부딪히는 경계를 정리합니다.

## 1. wheel odom, ground truth, state estimate를 구분한다

이 과정에는 의도적으로 서로 다른 두 궤적이 있습니다.

| 값 | 출처 | 장점 | 한계 |
| --- | --- | --- | --- |
| `/odom` → `/wheel_odom_path` | drive plugin의 wheel 운동학 | 실제 로봇에서도 얻을 수 있는 형태 | slip, wheel radius/track 오차가 누적됨 |
| `/ground_truth_path` | diffbot의 custom plugin, 또는 Ackermann built-in world odom 변환 | 시뮬레이터의 기준값 | 실제 로봇에서는 직접 얻을 수 없음 |
| 향후 `/odometry/filtered` | `robot_localization` EKF/UKF | wheel odom과 IMU 등 융합 | 모델·공분산·시간 동기 설정이 필요 |

`ground truth`를 localization 입력으로 사용하면 알고리즘이 잘 되는 것처럼 보이지만 실제 센서 조건을 재현하지 못합니다. ground truth는 평가와 디버깅에만 두고, 로봇 알고리즘에는 실제 장비에서 얻을 수 있는 토픽만 입력하는 습관이 좋습니다.

다음 확장으로 `robot_localization`을 설치하고 `/odom`과 `/imu/data`를 융합해 보세요. RViz에서 `/wheel_odom_path`, `/odometry/filtered`를 변환한 Path, `/ground_truth_path` 세 개를 다른 색으로 겹치면 오차의 성격이 잘 보입니다.

## 2. 플러그인 직접 구동과 `ros2_control`

이 과정은 기구학을 눈으로 이해하기 위해 `gazebo_ros_diff_drive`와 `gazebo_ros_ackermann_drive`가 joint를 직접 구동합니다. 제품 수준의 제어 스택에서는 다음 구조가 더 적합할 수 있습니다.

```text
cmd_vel → controller_manager → diff_drive_controller
         → gazebo_ros2_control → Gazebo joint
```

`ros2_control`을 쓰면 controller와 hardware interface의 경계가 실제 로봇과 유사해지고 joint limit, controller switching, command/state interface를 명시할 수 있습니다. 다만 같은 joint에 drive plugin과 `gazebo_ros2_control`을 동시에 연결하면 두 제어기가 충돌합니다. 전환 실습을 할 때는 기존 drive plugin을 Xacro arg로 완전히 끄세요.

## 3. TF edge의 소유자는 하나만 둔다

TF 문제의 대부분은 “변환이 없다”보다 “같은 변환을 둘이 publish한다”에서 시작합니다.

| TF edge | 이 과정의 소유자 |
| --- | --- |
| `world → odom` | bringup static publisher; spawn 원점 비교용 |
| `odom → base_footprint` | DiffDrive plugin; Ackermann은 `ackermann_odom` 노드 |
| `base_footprint → base_link` | URDF fixed joint → `robot_state_publisher` |
| `base_link → wheel/sensor frame` | URDF joint → `robot_state_publisher` |
| `map → odom` | 없음; 향후 localization/Nav2가 소유 |

EKF가 `odom→base_footprint`를 publish하도록 바꾸면 differential model은 drive plugin의
`<publish_odom_tf>`를 `false`로, Ackermann launch는 `ackermann_publish_tf:=false`로 바꿔야
합니다. localization이 `map→odom`을 소유할 때는 같은 child `odom`을 두 parent가 소유하지
않도록 bringup의 `world→odom`도 `publish_world_odom_tf:=false`로 끍니다. “둘 다 같은
값일 것”이라고 기대하지 마세요. timestamp가 조금만 달라도 RViz에서 흔들림과 과거
extrapolation이 생깁니다.

## 4. simulation time은 시스템 전체의 계약이다

Gazebo는 `/clock`을 publish합니다. simulation이 pause되면 `/clock`도 멈추고, real-time factor가 0.5이면 wall clock 2초 동안 simulation time은 약 1초 흐릅니다.

시뮬레이션 데이터를 소비하는 노드는 모두 다음 parameter를 사용해야 합니다.

```bash
ros2 param get /odom_to_path use_sim_time
ros2 param get /robot_state_publisher use_sim_time
```

둘 다 `Boolean value is: True`여야 합니다. 한 노드만 wall time을 쓰면 “데이터는 오는데 RViz에 보이지 않는” 문제가 생깁니다. timer도 simulation time의 영향을 받는지, pause 중에 반드시 동작해야 하는 watchdog인지 의도를 나눠 설계하세요.

## 5. 센서 QoS는 토픽 이름만큼 중요하다

카메라, LaserScan, PointCloud2 같은 고속 센서의 구독자는 보통 sensor-data QoS(`best_effort`, 작은 depth)를 사용합니다. Humble `gazebo_ros_pkgs`의 예제 publisher는 Reliable을 사용하지만 Best Effort subscriber 요청을 만족하므로 연결됩니다. 다른 드라이버로 바꾼 뒤 토픽은 보이는데 데이터가 없다면 publisher와 subscriber의 reliability·durability 호환성을 먼저 확인하세요.

```bash
ros2 topic info --verbose /points
ros2 topic echo /points --qos-reliability best_effort --once
```

RViz의 해당 Display에서 Reliability Policy를 `Best Effort`로 맞추고, 네트워크를 건너는 경우 bandwidth와 queue depth를 함께 고려합니다.

## 6. `rosbag2`로 회귀 데이터를 남긴다

센서와 odometry를 녹화해 두면 모델을 바꾼 뒤 동일한 분석 노드를 반복 검증할 수 있습니다.

```bash
mkdir -p ~/bags
cd ~/bags
ros2 bag record \
  /clock /tf /tf_static /joint_states \
  /cmd_vel /odom /imu/data /scan /points
```

카메라까지 한꺼번에 저장하면 용량이 빠르게 증가합니다. 필요한 profile만 실행하고 토픽을 선택하세요. 재생할 때는 실행 중인 Gazebo의 `/clock`과 bag의 `/clock`을 동시에 publish하지 않습니다.

```bash
ros2 bag info <bag_directory>
ros2 bag play <bag_directory> --clock
```

bag을 알고리즘 회귀 입력으로 쓰고, pose 오차·토픽 주기·drop 수를 자동 측정하면 화면 캡처보다 훨씬 강한 테스트가 됩니다.

## 7. 물리 정확도와 속도를 숫자로 관리한다

센서를 모두 켠 `sensor_profile:=all`은 GPU와 CPU 부하가 큽니다. 먼저 필요한 센서만 켜고 다음 값을 관찰하세요.

```bash
gz stats -p
ros2 topic hz /scan
ros2 topic hz /imu/data
ros2 topic bw /points
```

- real-time factor가 낮다면 카메라 해상도·update rate, 3D LiDAR sample 수를 먼저 줄입니다.
- 물리가 불안정하다면 `max_step_size`를 줄이고 solver iteration을 늘리되 계산 비용을 측정합니다.
- collision mesh를 단순화하고 작은 질량/극단적인 관성비를 피합니다.
- 결과 비교에는 wall time이 아니라 message header의 simulation timestamp를 사용합니다.

센서 주기를 높이는 것이 항상 정확도를 높이지는 않습니다. 제어·추정 알고리즘이 실제로 처리할 수 있는 rate와 지연을 목표로 정하세요.

## 8. 다중 로봇은 namespace만 붙인다고 끝나지 않는다

두 로봇을 spawn하려면 다음 자원이 모두 고유해야 합니다.

- Gazebo entity name
- ROS namespace와 노드 이름
- `/cmd_vel`, `/odom`, 센서 토픽
- TF frame (`robot1/base_link`처럼 prefix 적용)
- `robot_description`과 parameter namespace

절대 토픽(`/odom`)을 플러그인 내부에 고정하면 namespace가 무시됩니다. `<ros><namespace>...</namespace>`와 상대 토픽을 사용하고, launch에서 `frame_prefix`를 일관되게 전달하세요. RViz Fixed Frame도 각 로봇 TF tree를 연결하는 상위 frame이 있을 때만 공유할 수 있습니다.

## 9. 자동 검증의 최소선

GUI를 사람이 바라보는 테스트만으로는 회귀를 잡기 어렵습니다. 최소한 다음 검사를 CI 또는 로컬 스크립트로 반복하세요.

1. 모든 Xacro variant 전개 및 `check_urdf`
2. world SDF의 `gz sdf -k`
3. `colcon build`와 package test
4. `gzserver` headless launch 후 제한 시간 내 entity spawn 확인
5. `/clock`, `/odom`, 필수 센서 토픽에서 한 message 수신
6. `odom→base_footprint` TF lookup
7. 짧은 `/cmd_vel` 입력 뒤 pose 또는 odometry가 임계값 이상 변했는지 확인
8. 종료 뒤 `gzserver`, ROS 노드가 남지 않았는지 확인

CI에서는 Ubuntu/ROS/Gazebo 버전을 container image 또는 apt snapshot으로 고정하고, random seed와 world physics 설정을 기록하세요. 수치 오차를 bitwise equality로 비교하지 말고 의미 있는 허용 오차를 둡니다.

## 10. 추천 확장 실습

### 초급 확장

- wheel radius를 실제 값과 플러그인 값에서 각각 5% 바꾸고 `/wheel_odom_path` 차이 설명하기
- 바퀴 `mu1`, `mu2`를 낮추고 skid가 커지는 조건 찾기
- camera update rate를 바꾸고 `ros2 topic hz`로 측정하기

### 중급 확장

- `robot_localization`으로 `/odom` + `/imu/data` 융합
- `slam_toolbox`와 2D LiDAR로 map 생성
- Nav2가 사용할 `map→odom→base_footprint` TF tree 완성
- `gazebo_ros2_control` + `diff_drive_controller`로 구동 계층 교체

### 고급 확장

- 커스텀 ground-truth plugin에 reset service와 covariance/noise 모델 추가
- 여러 robot namespace와 TF prefix를 launch에서 생성
- headless integration test에서 command 입력과 trajectory error 자동 판정
- 실제 센서 rosbag을 재생해 simulation sensor와 message contract 비교

## 11. 새 Gazebo로 이전할 때

URDF의 link/joint 구조와 ROS message/TF 설계는 상당 부분 재사용할 수 있지만 다음은 다시 구현하거나 변환해야 합니다.

- Classic ModelPlugin/WorldPlugin → 새 Gazebo System plugin
- `gazebo_ros_pkgs` sensor/drive plugin → 새 Gazebo system + `ros_gz_bridge` 또는 `gz_ros2_control`
- Classic launch → `ros_gz_sim` launch
- `GAZEBO_MODEL_PATH`, `GAZEBO_PLUGIN_PATH` → 새 Gazebo resource/system plugin 경로

먼저 외부 contract(`/cmd_vel`, `/odom`, sensor topics, TF frames)를 문서화하고, 시뮬레이터 종속 구현을 그 뒤에 숨기면 이전 비용이 줄어듭니다.
