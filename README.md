# Gazebo Sim 튜토리얼 (한국어)

Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic 조합에서 Gazebo Sim을 처음 실행하는 단계부터 ROS 2 연동, 센서, 주행 제어, System Plugin, 자동화 테스트까지 학습하는 실행 중심 튜토리얼이다.

이 저장소의 `Jazzy` 브랜치는 ROS 2 Jazzy와 Gazebo Harmonic 전용 과정이다. 튜토리얼 전체에서는 공통 로봇 `tutorial_bot`을 한 단계씩 확장한다.

```text
SDF world → URDF/Xacro 로봇 → 주행·센서 → ros_gz bridge
→ TF·RViz·ros2_control·Nav2 → C++ System Plugin·headless test·CI
```

## 지원 환경

| 항목 | 본편 기준 |
| --- | --- |
| 운영체제 | Ubuntu 24.04 LTS (Noble) |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (`gz sim` 8 계열) |
| SDFormat | 14 계열 |
| 검증 아키텍처 | amd64 |
| 렌더링 | headless/software rendering을 기본 검증 경로로 사용하며 GPU는 선택 사항이다. |

다른 조합은 동작하지 않는 환경이 아니라 이 저장소에서 지속적으로 검증하지 않는 환경이다. 자세한 범위는 [지원 환경과 호환성](docs/02_getting-started/00_compatibility.md)에서 확인한다.

## 5분 안에 시작하기

저장소를 받은 뒤 `Jazzy` 브랜치로 전환하고 작업 위치를 확인한다.

```bash
git switch Jazzy
pwd
```

ROS 2 환경과 설치된 Gazebo 조합을 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
test "$ROS_DISTRO" = jazzy
gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
```

첫 world는 ROS 2 workspace를 빌드하지 않아도 실행할 수 있다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -r examples/gazebo/worlds/first-world.sdf
```

첫 명령은 SDF 스키마와 참조를 검사한다. 두 번째 명령은 물리 server와 GUI를 실행한다. 창을 닫거나 터미널에서 `Ctrl+C`를 눌러 종료한다.

## 전체 ROS 2 예제 빌드

설치가 끝난 뒤 workspace 의존성을 설치하고 모든 예제를 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

GUI와 Nav2를 제외한 통합 stack은 다음과 같이 실행한다.

```bash
ros2 launch tutorial_bot_bringup simulation.launch.py \
  gui:=false rviz:=false nav2:=false
```

다른 터미널에서 동일한 underlay와 overlay를 불러온 뒤 토픽을 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
ros2 topic list
ros2 topic echo /odom --once
```

## 문서 보기

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-docs.txt
mkdocs serve
```

브라우저에서 터미널에 표시된 주소를 연다. 링크와 코드 블록을 포함한 정적 빌드를 엄격하게 검사하려면 다음 명령을 실행한다.

```bash
mkdocs build --strict
```

## 저장소 구성

- `docs/`는 MkDocs 문서 원본을 보관한다.
- `docs/assets/`는 문서에서 사용하는 그림, 캡처, asset manifest를 보관한다.
- `examples/gazebo/`는 ROS 2 없이 실행하는 SDF 예제를 보관한다.
- `examples/ros2_ws/`는 ROS 2와 Gazebo를 함께 사용하는 workspace를 보관한다.
- `scripts/`는 반복 가능한 정적 검사와 runtime 검증을 보관한다.

전체 과정의 정적·실행 증거는 `scripts/run_course_matrix.py`와 `scripts/audit_course_evidence.py`로 검사한다. 실행을 건너뛴 결과는 통과로 인정하지 않는다.

`ref/`는 외부 자료의 학습 흐름을 조사하기 위한 로컬 참고 경로이며 Git에서 제외한다. 외부 문장과 코드를 복제하지 않고 Jazzy/Harmonic 환경에 맞게 독자적으로 설명한다.

## 라이선스

이 저장소는 [Apache License 2.0](LICENSE)을 따른다.
