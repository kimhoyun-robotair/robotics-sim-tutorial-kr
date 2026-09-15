# 109. 발행 주기: 물리 FPS, Gate, 센서 frame skip 구분하기

권장 학습 순서 **109** · ROS 2 연결과 기본 통신 · 출처 ID `t016`

예상 결과는 같은 Stage에서 `/clock`, `/imu`, `/scan`, RGB, CameraInfo가 서로 다른 비율로 발행되는 것이다. 공식 multi-sensor scene을 직접 구성·수정하는 실습이며 `configure_rates.py`는 그 scene의 실제 속성을 검증한 뒤 설정한다.

## 이 실습의 의도

발행 주기를 바꾸는 세 위치인 앱 진행 빈도, 일반 그래프의 Simulation Gate, 센서 Helper의 frame skip을 구별한다. 같은 multi-sensor Stage에서 일부 출력을 끄고 서로 다른 간격을 적용해 센서별 비율을 비교한다. `configure_rates.py`는 지정된 sample의 속성과 목표 FPS를 설정하는 보조 도구이며, Stage 로드·IMU 그래프 생성·Play·실제 수신 측정은 아래 절차에서 수행한다.

## 실행 후 확인할 것

- 첫 Play 전에 스크립트를 실행하면 콘솔에 LaserScan skip=11, RGB skip=3, CameraInfo skip=5와 목표 FPS=60이 출력되어야 한다. 해당 속성이 없다는 오류는 대상 sample 경로를 재확인하라는 뜻이며, 스크립트가 다른 Stage를 자동 구성한 것은 아니다.
- `/clock`, `/imu`, `/scan`, `/camera_1/rgb/image_raw`, `/camera_1/rgb/camera_info`를 각각 10초 이상 수신 측정한다. `ros2 topic list -t`로 타입이 순서대로 `rosgraph_msgs/msg/Clock`, `sensor_msgs/msg/Imu`, `LaserScan`, `Image`, `CameraInfo`인지도 확인한다.
- 실제 기준 진행률이 60 FPS일 때 목표는 순서대로 약 60/30/5/15/10 Hz다. IMU는 sample 또는 수동 그래프의 Gate.step=2가 필요하며, 스크립트는 IMU Gate를 새로 만들거나 그 값을 변경하지 않는다.
- Action Graph에서 PointCloudPublish, 두 번째 카메라 Render Product, depth Helper가 비활성화되어 있는지 확인한다. 이 출력들이 멈추는 것은 비교할 토픽을 줄이기 위한 의도된 설정이다.
- 새로 로드한 Stage에서 `RGB_SKIP`만 3에서 7로 바꾸면 RGB가 기준 진행률의 1/4에서 1/8로 줄어드는지 비교한다. 나머지 센서의 설정 간격은 유지된다.
- HUD FPS와 ROS 수신 Hz를 함께 기록한다. 목표 60과 실제 처리량은 다를 수 있고, 센서 스캔 주기·DDS 손실·QoS 불일치도 결과에 영향을 주므로 메시지 미수신을 성능 0 Hz로 판정하지 않는다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## 완성 scene으로 시작하기

Isaac Sim Content Browser에서 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial_multi_sensor_publish_rates.usd**를 연다. 카메라·Lidar·IMU와 그래프가 들어 있어 다른 로컬 패키지를 먼저 공부할 필요가 없다. scene을 로드한 후 **첫 Play 전에** 아래 작업을 한다.

1. `output/rates_01.usd`처럼 새 이름으로 저장한다.
2. **Window > Script Editor**에 `configure_rates.py` 내용을 붙여 실행한다. 스크립트는 예상하는 공식 prim/노드 속성이 전부 있는지 먼저 확인한다. scene이 다르면 경로 오류를 내고 수정을 시작하지 않는다.
3. Play 후 viewport의 눈 아이콘 **Show/Hide > Heads Up Display > FPS**를 켠다. 목표 FPS=60과 실제 FPS를 구별한다.
4. 각 명령을 서로 다른 ROS 터미널에서 10초 이상 실행한다.

   ```bash
   ros2 topic hz /clock
   ros2 topic hz /imu
   ros2 topic hz /scan
   ros2 topic hz /camera_1/rgb/image_raw
   ros2 topic hz /camera_1/rgb/camera_info
   ```

   ROS CLI QoS가 맞지 않으면 `ros2 topic hz --help`로 설치 버전 옵션을 확인하거나 topic info의 QoS를 따르는 subscriber로 측정한다. 메시지가 안 오는 것을 0Hz 성능으로 기록하지 않는다.

## 처음부터 Gate와 sensor skip 만들기

원문 기본 scene **Samples/ROS2/Scenario/turtlebot_tutorial.usd**로 시작할 수도 있다. 이 경우 아래 작업을 모두 수행한다.

1. `/World/turtlebot3_burger/base_link/imu_link`를 선택하고 **Create > Sensors > Imu Sensor**로 `Imu_Sensor`를 만든다. 같은 imu_link 아래에 `ROS_IMU` ActionGraph를 만든다. 그래프가 robot 안에 있는 것은 자동 ROS namespace 계산에 영향을 준다.
2. Tick, Context, Read Simulation Time, **Isaac Simulation Gate**, **Isaac Read IMU**, **ROS2 Publish IMU**를 추가한다. Tick.tick → Gate.execIn → Gate.execOut → ReadIMU.execIn → ReadIMU.execOut → Publisher.execIn으로 잇는다. sensor 데이터 세 출력 linearAcceleration/angularVelocity/orientation을 publisher의 같은 입력에, Context와 simulationTime도 연결한다.
3. Gate.step=2, ReadIMU.imuPrim=`/World/turtlebot3_burger/base_link/imu_link/Imu_Sensor`, Publisher.frameId=`imu_link`, topicName=`/imu`로 둔다.
4. `/World/turtlebot3_burger/base_scan/ROS_LidarRTX/LaserScanPublish`의 frameSkipCount=11로 둔다. PointCloudPublish의 enabled=False로 하고 필요한 LaserScan만 남긴다.
5. `/World/ActionGraph_camera/isaac_create_render_product_01`의 enabled=False로 두 번째 카메라를 끈다. `ros2_camera_helper`의 frameSkipCount=3, depth용 `ros2_camera_helper_02`의 enabled=False, `ros2_camera_info_helper`의 frameSkipCount=5로 둔다.
6. `configure_rates.py`에서 작성한 Stage time code와 Timeline 목표 FPS 설정을 아래 설명에 따라 첫 Play 전에 적용한다. 그 뒤 위 실제 토픽을 측정한다.

## 숫자를 해석하기

| 메시지 | 실행 간격 | 실제 기준 FPS가 60일 때 목표 |
|---|---|---|
| /clock | 매 프레임 | 약 60Hz |
| /imu | Gate.step=2 | 약 30Hz |
| /scan | frameSkipCount=11 → 12프레임마다 | 약 5Hz |
| RGB | frameSkipCount=3 → 4프레임마다 | 약 15Hz |
| CameraInfo | frameSkipCount=5 → 6프레임마다 | 약 10Hz |

`step=N`은 N번마다 통과한다. Helper의 `frameSkipCount=K`는 K프레임을 건너뛴 후 한 번 보내므로 분모가 **K+1**이다. 공식 문서 Lidar 설명에 gate step=11이라는 문장이 있지만 같은 절의 skip11/12프레임 관계를 따라 해석해야 한다. 이 스크립트는 Helper의 frameSkipCount를 설정하고 내부 SDG 그래프를 억지로 다시 연결하지 않는다.

`stage.SetTimeCodesPerSecond(60)`은 USD 시간 코드의 초당 개수, `timeline.set_target_framerate(60)`은 목표 진행 빈도를 설정한다. Stage를 로드하고 타임라인을 멈춘 상태에서 첫 Play 전에 적용한다. 이미 재생한 scene의 값을 바꾸려면 새로 로드한 뒤 다시 설정한다.

`carb.settings`의 `/app/runLoops/main/rateLimitEnabled`, `rateLimitFrequency`, `/persistent/simulation/minFrameRate`는 앱 루프 제한을 조정하는 별도 방법이다. 원문은 Play 후 이 값을 바꾸어 OnPlaybackTick 빈도 변화를 보기도 한다. 스크립트는 초기 목표값을 함께 설정하며 Stop/Play 후 앱 설정이 재적용되는지는 별도로 확인한다. 목표 숫자는 GPU/CPU가 보장하는 실제 처리량이 아니다.

## 한 가지 바꾸기·문제 해결

첫 실험은 `RGB_SKIP=3`만 7로 바꾸고 scene을 다시 로드해 설정한다. RGB 비율은 기준 FPS/8로 바뀌고 다른 센서 비율은 유지되어야 한다. 이미지 대역폭 때문에 비율이 낮으면 Render Product width/height를 줄여 비교한다. 센서 scan 회전 주기, GPU 로딩, DDS 대역폭도 실제 rate를 제한한다.

scene 경로 오류는 임의로 무시하지 말고 지정한 multi-sensor asset이 맞는지 확인한다. CPU 부하와 기존 사용자 rate 설정도 검사한다. 원문은 `isaac-sim.sh --reset-user`를 설정 초기화 진단으로, `isaac-sim.fabric.sh --reset-user`를 실험적 성능 경로로 제시한다. 사용자 설정 초기화의 영향을 이해한 뒤 선택하며 이 스크립트가 자동 실행하지 않는다. Fabric 경로의 모든 기능 지원을 전제하지 않는다. 실제 rate와 비율을 기록하는 것이 검증이다.

## 출처와 검증 범위

- [공식 5.1 Gate](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html#isaac-simulation-gate-node)
- [공식 5.1 센서 skip](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html#setting-publish-rates-for-nodes-within-sdg-pipeline)
- [공식 5.1 FPS 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html#setting-simulation-frame-rates)
- [공식 5.1 측정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_publish_rate.html#checking-ros-2-publish-rate)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 위의 확인 항목을 실제 환경에서 관찰해야 완료한 것이다.
