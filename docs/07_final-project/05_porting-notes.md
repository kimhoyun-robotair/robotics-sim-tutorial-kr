# 5. 포팅 내용과 검증 범위

이 프로젝트의 기준 소스는
[Gazebo_Harmonic_Rover 커밋 `aa7d135`](https://github.com/kimhoyun-robotair/Gazebo_Harmonic_Rover/tree/aa7d1358348f6ff064380704eedb4e898bd75bec)입니다.
원본은 ROS 2 Humble + Gazebo Harmonic을 설명합니다. 이 저장소의 통합 버전은
**Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic, ros_gz_bridge 1.0.22 이상**을 대상으로 합니다.

## 무엇을 가져왔는가

| 원본 패키지 | 통합 위치 | 보존한 내용 |
|---|---|---|
| `simple_rover` | `examples/ros2_ws/src/simple_rover` | 바퀴 4개 rover, 2D/3D 라이다, RGB/RGB-D 카메라, IMU/GNSS, 원본 월드·지도, Cartographer/AMCL/Nav2 구성 |
| `f1tenth_sim` | `examples/ros2_ws/src/f1tenth_sim` | 차체·바퀴·조향 메쉬, Ackermann 모델, 라이다/IMU, 원본 월드 |
| `nav2_programming` | `examples/ros2_ws/src/nav2_programming` | 단일 목표, 다중 목표, 경유점 순회 실행 파일 |

각 패키지의 `LICENSE`에 Apache-2.0 전문을 복사했으며 `UPSTREAM.md`에 출처와 수정 사실을 기록했습니다.
원본의 MOGI-ROS와 Gazebo_Harmonic_Rover 기여자 저작권 안내는 유지합니다.
[원본 README 사본](upstream-readme.txt)은 당시 설명을 보존하기 위한 자료이며 현재 실행 안내는 이 장을 따릅니다.
[파일별 출처 기록](upstream-source.json)에는 원본 경로, 크기, SHA-256과 통합 경로가 있습니다.

## 주요 수정 내역

| 발견한 문제 | 수정 | 확인 방법 |
|---|---|---|
| 환경 변수가 없는 상태에서 `GZ_SIM_RESOURCE_PATH`를 바로 덧셈 | 기존 값이 없으면 빈 문자열로 처리하고 설치 경로를 추가 | 깨끗한 터미널에서 launch |
| 개인 홈 디렉터리와 Fuel 캐시 경로 사용 | 패키지 share 경로, `models_path` 인자, `model://` URI로 변경 | 다른 사용자 환경에서 빌드/실행 |
| 기본 월드가 외부 모델에 의존 | 도형만 사용하는 `rover_arena.sdf` 추가 | 모델 다운로드 없이 기본 launch |
| 센서와 TF가 양방향 bridge | 명령은 ROS→Gazebo, 상태와 센서는 Gazebo→ROS로 고정 | bridge YAML 검사, `/tf` 발행자 확인 |
| `qos_profile: DEFAULT`를 Jazzy bridge가 인식하지 못함 | 명령·odometry·TF 항목에서 이 값을 생략해 기본 Reliable QoS 사용 | 실제 메시지 수신, 주행, 지원 프로필 이름 검사 |
| RGB-D optical frame에 존재하지 않거나 잘못된 링크 지정 | 실제 `camera_link_optical` TF와 정확한 회전 사용 | Xacro 전개, `tf2_echo`, CameraInfo |
| Harmonic RGB-D 점군 XYZ와 optical 헤더 축 불일치 | `/camera/points`에만 `frame_id: depth_link` 적용 | 정면 벽 점군 방향/거리, XYZ·depth 대조 |
| 카메라 정보 relay가 원본 토픽 없이 실행됨 | CameraInfo를 직접 bridge; 불필요한 relay 제거 | `/camera/camera_info` 수신 |
| 2D/3D 라이다가 같은 링크·관절·토픽 사용 | 3D용 `lidar3d_link`, `/lidar3d/points` 분리 | 두 센서를 동시에 전개/실행 |
| 라이다와 RGB-D 지지대 위치 중첩 | 기본 2D 라이다를 차체 중앙 위로 이동 | URDF 위치, Gazebo 충돌/센서 시야 |
| GNSS 시스템과 월드 기준 좌표가 빠짐 | NavSat 플러그인과 spherical coordinates 추가 | `gps:=true`로 `/navsat` 수신 |
| F1Tenth IMU의 링크와 header 이름 불일치 | `imu_link`로 통일 | TF와 메시지 header 대조 |
| F1Tenth 바퀴 반경 누락, 축 거리 불일치 | 반경 0.05 m, 축 거리 0.325 m, 바퀴 중심 간격 0.245 m 명시 | 실제 URDF 형상과 회귀 검사 |
| F1Tenth 일부 마찰 값이 잘못된 XML 형식, 조향 관절 제한 무효 | 요소 내용으로 수정, 양쪽 조향 관절을 revolute로 통일 | XML/URDF 및 조향 동작 |
| ROS 1 transmission 정의가 Harmonic 시스템 구동과 함께 남음 | 사용하지 않는 transmission 제거 | 전개한 URDF 검사 |
| Nav2 구형 plugin 이름·수동 서버 구성 | 설치된 Jazzy Nav2 launch와 기본 YAML 병합 사용 | lifecycle, 목표 주행 |
| rover보다 작은 Nav2 충돌 반경 | 사각형 footprint와 DWB ObstacleFootprint 검사 | costmap footprint/회전 시 모서리 확인 |
| Cartographer와 구동 플러그인이 odom TF 중복 발행 | Cartographer는 `map → odom`만 담당 | TF 트리와 발행자 확인 |
| 예제 quaternion이 모두 0, 고정된 경유점/초기 위치 | yaw 변환, 좌표 파라미터, 초기 위치 덮어쓰기 제거 | 입력 검사, 실제 목표 도달 |
| 조이스틱이 없어도 장치 노드를 항상 실행 | `joy:=true`일 때만 실행 | 기본 launch에 장치 오류 없음 |

## 원본 월드와 지도 사용

기본 실습은 `rover_arena.sdf`를 사용합니다. 원본 `world.sdf`, `home.sdf`,
`turtlebot3_world.sdf`, `turtlebot3_house.sdf`, `warehouse.sdf`도 패키지에 남아 있습니다.
이 월드 일부는 원본 저장소가 별도로 요구했던 모델과 텍스처를 필요로 합니다.
그 자산 전체가 원본 저장소에 포함된 것은 아니므로 이 포팅에도 자동으로 추가되지는 않습니다.

원본 월드를 사용할 때는 모델 디렉터리를 준비하고 `models_path`로 전달합니다.
디렉터리 안에는 각 모델의 `model.config`, SDF, 메쉬가 있어야 합니다.
필요한 URI와 월드 내부 이름은 설치된 파일에서 확인할 수 있습니다.

```bash
WORLD_FILE="$(ros2 pkg prefix simple_rover)/share/simple_rover/worlds/world.sdf"
python3 - "$WORLD_FILE" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
print('world_name:', root.find('world').attrib['name'])
print('외부 리소스:')
for uri in sorted({element.text for element in root.iter('uri')}):
    print(uri)
PY
```

출력된 `world_name`을 사용해야 합니다. 파일 이름과 SDF 내부의 world 이름은 다를 수 있습니다.
예를 들어 `world_name` 출력이 `empty`이고 모델을 `~/gazebo_models`에 준비했다면 다음과 같이 실행합니다.

```bash
ros2 launch simple_rover spawn_robot.launch.py \
  world:=world.sdf world_name:=empty models_path:="$HOME/gazebo_models"
```

Gazebo 로그에 리소스 오류가 남으면 그 월드의 실행 확인을 완료한 것으로 기록하지 않습니다.
원본 `map/demomap.*`, `map/warehouse.*`는 해당 원본 환경용 참고 자료이며,
새 월드나 수정한 장애물 배치에는 [지도 작성 단계](03_mapping-and-navigation.md)에서 직접 만든 지도를 사용합니다.

`config/localization.lua`는 Cartographer pure localization의 선택용 설정으로 남겼습니다.
이를 사용하려면 저장된 `.pbstream`을 불러오는 launch 구성도 필요합니다.
이 프로젝트의 기본 저장 지도 실습은 AMCL을 사용합니다.

## 정적 검사

저장소 루트에서 실행합니다. ROS가 없는 환경에서도 Xacro의 package 경로만 소스 디렉터리로
해석하여 모델 구조를 검사할 수 있습니다.

```bash
cd ~/robotics-sim-tutorial-kr
python3 -m venv .venv-final-check
source .venv-final-check/bin/activate
python -m pip install pytest xacro PyYAML
python -m pytest scripts/test_final_project.py -q
```

검사 항목은 다음과 같습니다.

- RGB/RGB-D/카메라 없음과 선택 센서 조합의 Xacro 전개 및 연결된 단일 TF 트리.
- 센서 frame이 실제 링크인지, optical 회전이 맞는지, 참조 메쉬가 존재하는지.
- URDF 바퀴 크기·관절 위치와 구동 플러그인 치수가 같은지.
- bridge 방향, 센서 QoS, RGB-D 점군 frame 보정, RViz 수신 QoS.
- 기본 월드의 필수 플러그인과 외부 URI 부재, 패키지 라이선스·개인 경로 제거.

이 검사는 ROS 프로세스, Gazebo 물리 엔진이나 RViz 렌더러를 실행하지 않습니다.
Gazebo가 설치된 환경에서는 빌드 후 다음 명령도 실행해 실제 URDF→SDF 변환 결과를 확인합니다.

```bash
# 가상환경 검사 후 새 ROS 터미널에서 실행
source /opt/ros/jazzy/setup.bash
source ~/robotics-sim-tutorial-kr/examples/ros2_ws/install/setup.bash
xacro "$(ros2 pkg prefix simple_rover)/share/simple_rover/urdf/simple_rover.urdf" \
  > /tmp/simple_rover.urdf
gz sdf -p /tmp/simple_rover.urdf > /tmp/simple_rover.sdf
gz sdf -k /tmp/simple_rover.sdf
```

## 실행 결과 기록 {#runtime-results}

이 저장소에서 수행한 검사 결과와 재실행 명령은 [Jazzy 점검 기록](../06_reference/04_jazzy-audit.md)에 정리했습니다.
자신의 환경에서 실습할 때는 아래 항목을 함께 기록하세요.

| 항목 | 확인 방법 | 결과에 적을 내용 |
|---|---|---|
| 환경 | `printenv ROS_DISTRO`, `gz sim --versions`, bridge 패키지 버전 | Ubuntu/ROS/Gazebo/bridge/GPU 정보 |
| 기본 실행 | `simple_rover spawn_robot.launch.py` | 월드·로봇 생성, 리소스 오류 유무 |
| 제어 | 전진·회전·정지 | 실제 이동, `/odom`, 바퀴 TF |
| 센서 | 2장 토픽·TF·RViz 절차 | frame, 수신, 점군 방향, 카메라 투영 |
| 선택 센서 | `lidar_3d:=true gps:=true` | 추가 토픽 수신, 올바른 frame |
| 지도 | SLAM 후 지도 저장 | YAML/PGM 생성, 벽 중복 여부 |
| Nav2 | 재실행·초기 위치·목표 지정 | lifecycle active, 도달/실패 메시지 |
| F1Tenth | `f1tenth_sim spawn_robot.launch.py` | 조향 관절, 원호 이동, 센서 위치 |

정적 검사만 통과했다면 **정적 검사 통과 / 런타임 미실행**으로 기록합니다.
Headless 센서 검사만 실행했다면 **센서 메시지·TF 확인 / RViz 화면 미확인**으로 구분합니다.
실제 화면을 보지 않은 상태에서 RViz 렌더링까지 검증했다고 쓰지 않습니다.

## 참고한 공식 자료

- [ROS 2 Jazzy와 Harmonic 조합](https://gazebosim.org/docs/harmonic/ros_installation/)
- [ros_gz Jazzy bridge 설정과 변경 이력](https://github.com/gazebosim/ros_gz/tree/jazzy/ros_gz_bridge)
- [Harmonic RGB-D sensor 코드](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/RgbdCameraSensor.cc)
- [Harmonic AckermannSteering](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1AckermannSteering.html)
- [Nav2 Jazzy navigation launch](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/launch/navigation_launch.py)
- [Nav2 Jazzy Simple Commander API](https://docs.nav2.org/jazzy/configuration_and_development/simple_commander_api/simple_commander_api/)
