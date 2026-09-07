# gazebo_tutorial_plugins

ROS 2 Humble과 Gazebo Classic 11에서 실행되는 교육용 C++ 플러그인 패키지다.
`ground_truth_path_plugin`은 Gazebo가 계산한 모델의 위치와 자세를 읽고
`nav_msgs/msg/Path`로 발행한다. 기본 출력은 `/ground_truth_path`이며 좌표계는
`world`다. RViz에서 바퀴 오도메트리 경로와 비교하는 용도로 사용한다.

## 빌드하고 실행하기

[환경 설정](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/docs/01_setup.md)을
마치고 저장소를 `~/robotics-sim-tutorial-kr`에 내려받았다고 가정한다.
실행에 필요한 다른 패키지도 함께 빌드한다.

```bash
cd ~/robotics-sim-tutorial-kr/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
colcon test --packages-select gazebo_tutorial_plugins
colcon test-result --verbose
ros2 launch gazebo_tutorial_bringup diffbot.launch.py
```

빌드·검사 결과에 실패가 없어야 한다. 마지막 명령은 Gazebo와 RViz를 실행하므로
이 터미널을 켜 둔 채 새 터미널에서 메시지를 확인한다.

```bash
source /opt/ros/humble/setup.bash
source ~/robotics-sim-tutorial-kr/ros2_ws/install/setup.bash
ros2 topic info /ground_truth_path --verbose
ros2 topic echo /ground_truth_path --once --field header \
  --qos-reliability reliable --qos-durability transient_local
```

자료형은 `nav_msgs/msg/Path`, 프레임은 `world`여야 한다. 데이터가 오지 않으면
`Ctrl+C`로 대기를 중단하고 첫 터미널의 플러그인 로드 로그를 확인한다.
실습을 마치면 첫 터미널의 launch도 `Ctrl+C`로 종료한다.

## 설정과 연결

| 설정 | 기본값 | 의미 |
|---|---:|---|
| `update_rate` | `10.0` | 시뮬레이션 시간 기준 발행 주파수(Hz), 유한한 양수 |
| `topic` | `ground_truth_path` | 네임스페이스에 따라 달라지는 상대 토픽 이름 |
| `frame` | `world` | 참값을 계산한 좌표계. 다른 프레임으로 변환하는 기능은 없음 |
| `max_points` | `2000` | 보관할 최근 위치·자세 기록 수, 양의 정수 |

플러그인은 `frame`이 `world`인 설정만 받는다. 프레임 이름만 바꿔 좌표 변환을
대신할 수 없다. 출력 QoS는 `Reliable + Transient Local`이고, 시간이 뒤로 돌아가면
이전 경로를 비운다.

삽입용 Xacro 매크로는 `urdf/ground_truth_path_plugin.gazebo.xacro`에 있다.
기본 로봇에는 이미 연결되어 있으므로 중복으로 추가하지 않는다.
공유 라이브러리 검색 설정은 다음과 같다. `${prefix}`는 설치된 패키지의 share 폴더다.

```xml
<gazebo_ros plugin_path="${prefix}/../../lib" />
```

C++ 구현, 좌표계 비교, RViz 설정과 로딩 문제 해결은
[7장 플러그인 개발](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/Humble/docs/07_custom_plugin.md)을 참고한다.
