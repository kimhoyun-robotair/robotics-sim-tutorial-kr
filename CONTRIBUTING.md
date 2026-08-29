# 기여 가이드

이 저장소는 Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic 조합을 다루는 한국어 튜토리얼이다. 문서와 예제는 하나의 학습 단위로 함께 변경하며, 문서에 적은 명령은 가능한 한 실제 환경에서 실행해 확인한다.

기여하는 코드는 저장소의 [Apache License 2.0](LICENSE) 조건으로 배포할 수 있어야 한다.

## 작업 브랜치

Jazzy/Harmonic 관련 변경은 `Jazzy`를 기준으로 새 브랜치를 만든다. `main`에 직접 커밋하지 않는다.

```bash
git switch Jazzy
git pull --ff-only
git switch -c docs/<topic>
```

## 문서 작성 원칙

- 한국어 설명은 자연스러운 `~한다`, `~이다` 체로 작성한다. 명령 출력, 코드, 외부 인용은 원문 표기를 유지한다.
- 패키지명, 토픽명, 프레임명, CLI 명령은 코드 서식과 원문 철자를 유지한다.
- 새 문서는 `docs/` 아래에 영문 소문자 kebab-case 파일명으로 만든다.
- 각 실습은 학습 목표, 개념, 코드, 실행, 결과 확인, 문제 해결, 다음 단계를 포함한다.
- 설명 바로 아래에는 설명과 대응하는 최소 코드 조각을 둔다. 전체 구현은 저장소의 실제 파일 경로로 연결한다.
- 이미지와 다이어그램은 `docs/assets/` 아래에 두고, 본문만 읽어도 핵심 절차를 이해할 수 있게 대체 설명을 작성한다.

좋은 코드 예시는 태그 이름만 나열하지 않고 값이 어떤 동작을 결정하는지 보여준다. 예를 들어 DiffDrive 설명은 다음과 같이 실제 plugin 설정과 바퀴 치수를 함께 제시한다.

```xml
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>0.38</wheel_separation>
  <wheel_radius>0.06</wheel_radius>
  <odom_publish_frequency>30</odom_publish_frequency>
</plugin>
```

코드 다음에는 독자가 관찰할 수 있는 검증 명령을 둔다.

```bash
gz topic -l | grep -E 'cmd_vel|odometry'
ros2 topic echo /odom --once
```

## 예제 작성 원칙

- 공통 로봇은 `tutorial_bot`이며, 학습 목적이 겹치는 별도 로봇을 추가하지 않는다.
- 순수 Gazebo 예제는 `examples/gazebo/`, ROS 2 예제는 `examples/ros2_ws/`에 둔다.
- URDF/Xacro를 로봇 설명의 원본으로 사용하고, 동일한 로봇의 별도 SDF 원본을 중복 관리하지 않는다.
- 반복되는 링크·joint·센서 정의는 Xacro macro로 분리하고 인자로 크기, pose, topic을 주입한다.
- `build/`, `install/`, `log/`, `site/`는 커밋하지 않는다.

문서 속 코드와 실제 파일은 이름과 수치가 일치해야 한다. 다음 명령으로 대표 Xacro와 SDF를 빠르게 검사한다.

```bash
source /opt/ros/jazzy/setup.bash
xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro \
  > /tmp/tutorial_bot.urdf
check_urdf /tmp/tutorial_bot.urdf
gz sdf -k examples/gazebo/worlds/first-world.sdf
```

## 외부 자료 사용 원칙

외부 저장소는 주제 순서와 학습 난이도를 이해하는 참고 자료로만 사용한다. 복제본이 필요하면 Git에서 제외된 `ref/`에 두며 이 경로의 파일은 편집하지 않는다. 외부 코드, 이미지, 문장을 복사하지 않고 이 저장소의 로봇과 Jazzy/Harmonic API에 맞는 예제를 직접 작성한다.

## 변경 확인

문서 변경은 최소한 다음 정적 검사를 통과해야 한다.

```bash
python3 -m mkdocs build --strict
python3 scripts/audit_course_evidence.py --help
```

ROS 2 또는 Gazebo 예제를 변경하면 의존성을 설치하고 workspace를 다시 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Pull Request에는 변경한 학습 목표, 실행한 검증 명령, 실제로 관찰한 결과, 실행하지 못한 항목과 이유를 기록한다.
