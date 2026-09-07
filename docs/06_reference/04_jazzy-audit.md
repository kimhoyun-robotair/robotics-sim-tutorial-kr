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

RGB-D 점군 보정은 좌표 값을 돌리지 않는다. Gazebo가 내보내는 XYZ의 실제 축에 맞는 프레임명을 붙이는 수정이다. 영상에 같은 프레임을 붙이면 Camera 표시가 틀어지므로 두 데이터의 프레임을 구분한다. 근거는 [Gazebo RGB-D 센서 소스](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/RgbdCameraSensor.cc), [점군 변환 소스](https://github.com/gazebosim/gz-sensors/blob/4b9fdfc05892c38e7a855f63b56737fe5d591a5f/src/PointCloudUtil.cc), [깊이 렌더러 소스](https://github.com/gazebosim/gz-rendering/blob/0a299835b2b83ae240a5657dbdde50b7ba476d52/ogre2/src/Ogre2DepthCamera.cc)다.

현재 YAML의 `frame_id`와 `qos_profile` 기능을 사용하려면 `ros_gz_bridge >= 1.0.22`가 필요하다. [Jazzy 변경 기록](https://github.com/gazebosim/ros_gz/blob/0fa70cb7c15f7500c495190020dd6292188c8e54/ros_gz_bridge/CHANGELOG.rst)과 패키지 의존성에 이 기준을 명시했다.

## 검증 범위

수정 전 코드를 별도 폴더에 펼쳐 새 센서 회귀 검사를 실행했을 때 10개 중 9개가 실패했다. 수정 후에는 10개가 모두 통과했다. 점군 축, 다중 로봇 프레임, 충돌 외곽선, LiDAR 기준 거리, RViz QoS에 대한 검사다. 단순히 파일에 특정 문자열이 있는지만 확인하지 않고 Xacro를 펼친 로봇의 치수와 좌표 변환, 실제 월드 물체를 대조한다.

이후 실제 실행에서 발견한 차체 기울어짐을 재현하기 위해 기본 모델과 단계별 모델 5개의 무게중심 검사도 추가했다. 수정 전에는 모두 실패했고, 관성 중심을 옮긴 뒤 모두 통과했다.

최종 로컬 검사에서는 실행 환경이 필요하지 않은 문서·수식·Xacro·센서·Rover·검증 도구 테스트 **92개가 통과**했다. 바퀴를 포함한 실제 충돌 형상이 Nav2 외곽선 안에 들어가는지도 검사한다. ROS 설치, 실제 프로세스 정보, 브라우저 실행이 필요한 항목은 이 숫자에 포함하지 않았다. `mkdocs build --strict`, 기존 과정 31개와 파이널 프로젝트 6개 페이지의 연결 검사, Python/XML/셸 문법 검사도 통과했다.

로컬 작업 환경에는 ROS 2, Gazebo, Docker, RViz가 없다. 따라서 로컬 정적 검사 통과를 **실제 시뮬레이터 실행이나 RViz 화면 검수 완료로 해석하면 안 된다.** 기존 프로세스 관리 검사도 이 환경에서 제공하지 않는 `/proc` 정보와 프로세스 제어 기능에 의존하므로 전체 테스트 통과를 주장하지 않는다.

실제 실행 검사는 `Jazzy` 전용 [전체 작업 공간·센서 워크플로](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/actions/workflows/jazzy-validation.yml)에서 다음 항목을 확인하도록 구성했다.

1. 작업 공간 전체의 의존성 설치와 빌드
2. 기존 센서 예제의 영상·깊이·점군·LiDAR·IMU 측정값
3. 이식한 두 차량의 센서 프레임과 해당 측정 시각의 TF 연결
4. RGB-D 중앙 점의 +X 거리와 깊이 영상의 거리 일치, optical 축 방향
5. 주행 명령 후 odometry 변화와 모든 가동 관절의 상태 수신
6. RViz 화면 캡처와 실행 로그 저장
7. Rover의 선택 센서인 3D 라이다 점군과 GNSS의 좌표·프레임·TF 연결
8. 기본 월드의 충돌 형상으로 만든 검사 지도에서 AMCL·Nav2를 실행하고, 실제 `navigate_to_pose` 프로그램의 목표 도달과 이동량 확인

워크플로가 존재한다는 것만으로 통과한 것은 아니다. 해당 커밋의 실행 상태와 `jazzy-rendered-sensor-evidence` 파일을 확인한다. 수치 검사를 통과했더라도 RViz 캡처의 시각 검토와 지도 작성·Nav2의 끝까지 주행하는 실습은 별도 확인 항목이다. 기존 `pages.yml`의 고급 플러그인 검사도 센서 렌더링 검사를 대신하지 않는다.

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
```

검사 결과는 각 경로의 `result.json` 또는 `collection.json`과 로그로 확인한다. ROS 의존성이 없을 때는 성공 대신 종료 코드 69를 반환한다. 화면이 있는 환경에서는 `--rviz`를 추가하면 RViz를 열고 `rviz.png`를 저장한다. 화면 캡처 도구는 다음과 같이 설치한다.

```bash
sudo apt install -y imagemagick xdotool
python3 scripts/check_final_project_runtime.py \
  --package simple_rover --evidence /tmp/simple-rover-rviz-check --rviz
```

화면 없는 CI에서는 `xvfb-run`으로 가상 화면을 준비한다. 센서 검사 도구는 종료 시 Gazebo와 bridge를 정리하며, 본래 검사에 성공했더라도 프로세스를 정리하지 못하면 종료 코드 70으로 실패를 보고한다.

원본 Rover 커밋과 이식한 기능의 범위는 [이식 기록](../07_final-project/05_porting-notes.md)을 참고한다.
