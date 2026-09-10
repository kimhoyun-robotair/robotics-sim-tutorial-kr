# Jazzy 문서·예제 점검 기록

이번 점검은 `Jazzy` 브랜치의 문서와 실습 코드를 대상으로 한다. 기준은 Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic이다. 원본 Rover의 세 패키지를 파이널 프로젝트로 이식했다.

## 확인한 문제와 수정

| 구간 | 문제 | 수정 |
| --- | --- | --- |
| 시작하기·초급 | 저장소 받기와 새 터미널 환경 설정 누락, 빌드 후 잘못된 상대 경로 | `Jazzy` 전용 clone, 작업 폴더, 기본 ROS 환경과 작업 공간 환경을 불러오는 순서 명시 |
| 전체 문서 | 번역투와 설명 없는 영문 용어, 실행 코드와 발췌 구분 부족 | 자연스러운 한국어 설명, 용어 풀이, 단계별 명령과 예상 결과 보강 |
| ROS 2 실습 | 종료되지 않는 `echo`, `hz`, `tf2_echo` 뒤에 후속 명령 배치 | 별도 터미널·`Ctrl+C`·`--once` 안내, 필수 `--evidence` 인자 추가 |
| RGB-D 점군 | +X 전방인 XYZ 데이터를 optical 좌표계로 표시 | 점군 브리지의 `frame_id`를 센서 본체 링크로 설정. 영상과 CameraInfo의 optical 프레임은 유지 |
| RViz 로봇 모델 | RViz를 늦게 켜면 로봇 설명을 놓칠 수 있는 QoS | `/robot_description` 구독에 `Transient Local` 설정 |
| 다중 로봇 TF | 제어기가 `robot1/robot1/base_link`처럼 접두사를 중복 추가 | 이미 완성된 프레임명에 `tf_frame_prefix_enable: false` 적용 |
| 센서 검사 | LiDAR 기준 거리에 센서 위치와 전방 장애물이 반영되지 않음 | 월드의 실제 물체와 센서 장착 위치를 기준으로 거리 계산 수정 |
| 차체의 물리 모델 | 전방 센서 질량 때문에 무게중심이 바퀴·뒤 캐스터의 지지 영역을 벗어나 약 15도 기울어짐 | 차체 관성 중심을 뒤로 4 cm 옮겨 배터리 배치를 근사하고, 전체 무게중심이 지지 영역 안에 있는지 검사 |
| 제어·Nav2 | Jazzy에서 제거된 `use_stamped_vel`, 바퀴를 충분히 감싸지 않는 외곽선 | 제거된 설정 삭제, 충돌 외곽선 보정, 시간 포함 주행 명령 설명 수정 |
| 화면 없는 실행 | 서버 실행만 지정하고 센서 렌더링 경로를 누락 | `--headless-rendering` 적용, 느린 렌더링에서도 시뮬레이션 시간을 기준으로 센서 수집 |
| 통합 시험의 준비 순서 | Gazebo 이동량만 보고 ROS 기준 위치 수신 전에 측정을 종료할 수 있음 | 정지한 ROS 기준 표본을 받은 뒤 주행하고, ROS와 Gazebo 양쪽의 이동량을 기다려 판정 |
| 첫 월드 | 1 kg 정육면체 관성 미지정 | 1 m 정육면체의 관성 모멘트 `1/6 kg·m²` 명시 |
| C++ 플러그인 빌드 | ROS 설치만으로 해결되지 않는 외부 Gazebo 개발 패키지 의존성 | Jazzy의 `gz_*_vendor` 패키지와 공식 CMake 대상으로 전환 |
| Rover 이식 | 개인 PC 절대 경로, 빠진 좌표계·의존성, Humble 설정 | 설치된 패키지 경로, 독립 기본 월드, Jazzy 설정과 실행 절차 제공 |
| Rover의 명령·odometry·TF bridge | 지원하지 않는 `qos_profile: DEFAULT` 때문에 세 연결이 생성되지 않음 | 해당 값은 생략하여 Reliable 기본 QoS를 사용하고, 허용되는 프로필 이름을 검사 |
| 저장 지도 주행 | 지도 서버의 노드별 빈 설정이 전달한 지도 경로를 가림 | 검증한 절대 경로를 최종 `map_server.ros__parameters.yaml_filename`에도 기록하고, 실제 지도 로드와 Nav2 목표 도달 확인 |

RGB-D 점군 보정은 좌표 값을 돌리지 않는다. Gazebo가 내보내는 XYZ의 실제 축에 맞는 프레임명을 붙이는 수정이다. 영상에 같은 프레임을 붙이면 Camera 표시가 틀어지므로 두 데이터의 프레임을 구분한다. 근거는 [Gazebo RGB-D 센서 소스](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/RgbdCameraSensor.cc), [점군 변환 소스](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/PointCloudUtil.cc), [깊이 렌더러 소스](https://github.com/gazebosim/gz-rendering/blob/0a299835b2b83ae240a5657dbdde50b7ba476d52/ogre2/src/Ogre2DepthCamera.cc)다.

현재 YAML의 `frame_id`와 `qos_profile` 기능을 사용하려면 `ros_gz_bridge >= 1.0.22`가 필요하다. [Jazzy 변경 기록](https://github.com/gazebosim/ros_gz/blob/0fa70cb7c15f7500c495190020dd6292188c8e54/ros_gz_bridge/CHANGELOG.rst)과 패키지 의존성에 이 기준을 명시했다.

## 검증 범위와 실제 실행 결과

### 로컬 정적 검사

초기 센서 회귀 검사는 수정 전 코드에서 10개 중 9개가 실패했고, 수정 후 10개가 모두 통과했다. 점군 축, 다중 로봇 프레임, 충돌 외곽선, LiDAR 기준 거리, RViz QoS를 확인한다. 파일의 문자열만 검색하지 않고 Xacro를 펼친 로봇의 치수·좌표 변환과 실제 월드 물체를 대조했다. 이후 차체 기울어짐을 재현하는 무게중심 검사도 추가해 수정 전 실패와 수정 후 통과를 확인했다.

최종 로컬 검사에서는 문서·수식·Xacro·센서·Rover·검증 도구 테스트 **98개가 통과**했다. 이 숫자는 실제 Gazebo 실행과 RViz 화면 검수를 포함하지 않는다. `mkdocs build --strict`, 기존 과정 31개와 파이널 프로젝트 6개 페이지의 연결 검사, Python/XML/셸 문법 검사도 통과했다.

### Jazzy/Harmonic 실제 실행

[GitHub Actions 실행 34077737389](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/runs/34077737389)은 커밋 `cbb56b5e962a251f7c4d30d8c70854c17ea7ea2b`에서 **성공**했다. 전체 패키지 빌드, 센서·TF·직진·F1Tenth 좌회전, Rover의 지도 로드·AMCL·Nav2 목표 도달을 실제 실행으로 확인했다.

실행 환경은 Ubuntu 24.04·ROS 2 Jazzy·Gazebo Sim 8.11.0이며, 설치된 주요 패키지는 `ros_gz_bridge 1.0.22`, `rviz2 14.1.22`, `nav2_bringup 1.3.12`다.

| 확인 항목 | 실제 결과 | 판정 |
| --- | --- | --- |
| 전체 작업 공간 빌드 | 9개 패키지 빌드 완료 | 통과 |
| `colcon test-result` | 57개 결과, 오류 0·실패 0·건너뜀 1 | 실패 없음, 1개 미실행 |
| 별도 회귀 검사 | 44개 통과 | 통과 |
| `tutorial_bot` 센서 | RGB·깊이·점군 320 × 240, 스캔 360개. 영상 약 30.30 Hz·LiDAR 10 Hz·IMU 100 Hz. LiDAR 가장자리 조건 위반 5,080개 중 0개 | 통과 |
| `simple_rover` 센서·TF | 선택 센서를 포함한 8개 센서 토픽의 프레임과 측정 시각 TF, 링크 14개와 가동 관절 4개 확인 | 통과 |
| `simple_rover` 직진 | odometry 이동량 0.12090 m, 센서로 관측한 전방 벽 거리 감소 0.13146 m | 통과 |
| Rover RGB-D·3D LiDAR·GNSS | 중앙 깊이와 점군 x가 모두 4.65000 m. 3D 점군 23,040개 중 유한값 22,904개. GNSS 수평 오차 0 m | 통과 |
| `f1tenth_sim` 센서·TF·직진 | LiDAR·IMU의 측정 시각 TF, 링크 11개·가동 관절 6개 확인. 직진 0.12090 m, 전방 벽 거리 감소 0.12097 m | 통과 |
| F1Tenth 좌회전 | 방향 변화 +0.151990 rad, 왼쪽 변위 +0.01502 m. 좌·우 조향각 +0.306737 / +0.254286 rad | 통과 |
| Nav2 준비·목표 주행 | 지도 로드와 노드 12개 활성화. Action 상태 실행 중(2) → 성공(4), 주행 프로그램 종료 코드 0 | 통과 |
| Nav2 도착 오차 | 위치 0.190580 m ≤ 설정값 0.2 m, 방향 0.005343 rad ≤ 설정값 0.2 rad | 통과 |
| 실행 종료 | 두 차량과 내비게이션 검사 모두 오류 없음, 남은 프로세스 없음 | 통과 |
| RViz 화면 검수 | 두 차량의 1280 × 800 전체 화면 확인. `Global Status: Ok`, 로봇과 센서 표시 확인 | 확인 완료 |

센서 주파수는 메시지의 시뮬레이션 시간을 기준으로 계산한 값이다. 위 수치는 이 실행에서 수집한 결과이며 매번 같은 마지막 자리까지 재현된다는 뜻은 아니다. 근거 파일은 실행에 첨부된 `jazzy-rendered-sensor-evidence`의 `packages.txt`, `colcon-test-result.log`, `regressions.log`, `tutorial-sensors/collection.json`, 두 차량의 `result.json`, `navigation/result.json`과 RViz 캡처다.

Nav2 검사는 기본 월드에서 목표 `(x, y, yaw) = (0.6 m, 0 m, 0 rad)`를 보내고 18.364초에 검사를 마쳤다. 실제 odometry 이동량은 0.414360 m, 최종 map 좌표는 `(0.409504 m, −0.005635 m, −0.005343 rad)`였다. 목표 좌표와 정확히 일치한 것은 아니며, 설정된 위치·방향 허용 오차 안에 들어와 성공했다. 이전 [실행 34076990223](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/runs/34076990223)의 빈 `yaml_filename` 문제를 수정한 뒤 지도 경로와 목표 도달을 함께 확인한 결과다.

### RViz 화면 확인

Rover의 전체 화면에서 로봇 모델, LiDAR, RGB-D 점군, RGB 카메라 영상이 표시되며 붉은 상자의 점군과 LiDAR 위치가 맞는지 확인했다. 캡처는 [센서와 RViz](../07_final-project/02_sensors-and-rviz.md)에 있다. F1Tenth 화면에서는 파란 차체, 바퀴 4개, 붉은 스캔이 표시된다. 캡처는 [F1Tenth 차량](../07_final-project/04_f1tenth.md)에서 확인할 수 있다.

두 화면 모두 정지 상태의 표시 결과다. F1Tenth 조향 동작은 정지 화면만으로 판단하지 않고 위 표의 실제 조향각·방향 변화·왼쪽 이동량으로 확인했다.

### 차체 기울어짐 수정 전후

차체의 관성 중심을 뒤로 4 cm 옮긴 뒤, 기존에 잘못 나오던 카메라·IMU·LiDAR 값이 함께 정상 범위로 돌아왔다. [수정 전 실행](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/runs/34074482188)과 수정 후 커밋 `6bd8ccb`의 [실행 34076990223](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/runs/34076990223)을 비교하면 다음과 같다. 아래 표는 수정 효과를 확인한 당시의 기록이다.

| 측정값 | 수정 전 | 수정 후 (`6bd8ccb`) |
| --- | ---: | ---: |
| 카메라 중앙 점의 전방 거리 | 약 0.27236 m | 1.5600003 m |
| 정지 상태 IMU x축 가속도의 평균 오차 | 약 −2.615 m/s² | 약 −0.000002786 m/s² |
| LiDAR 가장자리 거리의 기하 조건 위반 | 4,800개 중 3,360개 | 4,920개 중 0개 |

수정 후 카메라 중앙 점의 거리는 전방 물체까지의 예상 거리 1.56 m와 일치했다. LiDAR 비교는 수집 시간이 달라 표본 수가 다르므로 전체 개수와 위반 개수를 함께 표시했다.

### 별도로 확인할 범위

이번 실행으로 확인하지 않은 범위는 직접 주행하며 SLAM으로 전체 지도를 작성하는 과정, 외부 자료에 의존하는 추가 월드, 선택 기능인 Cartographer, F1Tenth의 자율주행이다. Rover의 Nav2 검사는 기본 월드의 충돌 형상으로 만든 검사 지도를 사용했다. 직접 작성한 지도와 다른 환경에서는 해당 실습을 다시 확인한다.

재검사는 `Jazzy` 전용 [전체 작업 공간·센서 워크플로](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/workflows/jazzy-validation.yml) 또는 아래 명령으로 실행할 수 있다. 결과를 비교할 때는 소스 커밋과 실제 설치된 패키지 버전을 함께 확인한다.

## 직접 재검사하기

먼저 저장소 루트로 이동하고 [환경 설치](../02_getting-started/02_installation-jazzy.md)를 마친다. 전체 빌드 후 새 터미널에서도 환경을 불러온다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
python3 -m pytest -q scripts/test_final_project.py scripts/test_sensor_rendering_contract.py
bash scripts/check_intermediate_sensors.sh --launch --evidence /tmp/tutorial-sensor-check
python3 scripts/check_final_project_runtime.py \
  --package simple_rover --extra-sensors --evidence /tmp/simple-rover-check
python3 scripts/check_final_project_runtime.py \
  --package f1tenth_sim --evidence /tmp/f1tenth-check
python3 scripts/check_final_project_navigation.py \
  --evidence /tmp/simple-rover-navigation-check
```

검사 결과는 각 경로의 `result.json` 또는 `collection.json`과 로그로 확인한다. ROS 의존성이 없을 때는 성공 대신 종료 코드 69를 반환한다. 화면이 있는 환경에서는 `--rviz`를 추가하면 RViz를 열고 `rviz.png`를 저장한다. 화면 캡처 도구는 다음과 같이 설치한다.

```bash
sudo apt install -y imagemagick xdotool
python3 scripts/check_final_project_runtime.py \
  --package simple_rover --evidence /tmp/simple-rover-rviz-check --rviz
```

화면 없는 CI에서는 `xvfb-run`으로 가상 화면을 준비한다. 센서 검사 도구는 종료 시 Gazebo와 bridge를 정리하며, 본래 검사에 성공했더라도 프로세스를 정리하지 못하면 종료 코드 70으로 실패를 보고한다.

내비게이션 검사 도구는 기본 월드의 실제 충돌 형상으로 임시 지도를 만들고, AMCL·Nav2가 활성화된 뒤 `(0.6, 0, 0)` 목표를 보낸다. `nav2_programming`의 성공 종료, ROS action 성공 상태, 실제 이동량과 최종 위치를 함께 검사한다. 이 지도는 검사 조건을 일정하게 만드는 용도다. SLAM으로 지도를 작성하는 실습은 [파이널 프로젝트 3장](../07_final-project/03_mapping-and-navigation.md)의 절차로 별도 확인한다.

원본 Rover 커밋과 이식한 기능의 범위는 이식 기록을 참고한다.
