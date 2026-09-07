# 기여 가이드

이 저장소는 Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic 조합을 다루는 한국어 튜토리얼이다. 문서와 예제는 하나의 학습 단위로 함께 변경하며, 문서에 적은 명령은 가능한 한 실제 환경에서 실행해 확인한다.

기여하는 코드는 저장소의 [Apache License 2.0](LICENSE) 조건으로 배포할 수 있어야 한다.

## 작업 브랜치

Jazzy/Harmonic 과정은 `Jazzy` 브랜치에서 관리한다. 이 브랜치만 수정하도록 요청받은 작업에서는 새 브랜치를 만들지 않고 `Jazzy`에 직접 커밋·푸시한다. 다른 브랜치의 내용이나 기록을 바꾸거나 삭제하지 않는다.

작업을 시작할 때 현재 브랜치와 변경 사항을 확인한다.

```bash
git status --short
git branch --show-current
git remote -v
```

다른 브랜치에 있다면 기존 작업을 보존한 상태에서 `Jazzy`로 이동한다. 작업 디렉터리가 정리되어 있을 때만 최신 원격 변경을 반영한다.

```bash
git switch Jazzy
git pull --ff-only origin Jazzy
```

푸시 전에도 브랜치를 다시 확인하고 목적지를 명시한다. `--all`, `--mirror`, `--force`는 사용하지 않는다.

```bash
test "$(git branch --show-current)" = Jazzy && git push origin HEAD:refs/heads/Jazzy
```

## 문서 작성 원칙

- 한국어 설명은 자연스러운 `~한다`, `~이다` 체로 작성한다. 명령 출력, 코드, 외부 인용은 원문 표기를 유지한다.
- 패키지명, 토픽명, 프레임명, CLI 명령은 코드 서식과 원문 철자를 유지한다.
- 새 문서는 `docs/` 아래에 영문 소문자 kebab-case 파일명으로 만든다.
- 각 실습은 학습 목표, 준비 사항, 개념, 코드, 실행, 결과 확인, 문제 해결, 다음 단계를 포함한다.
- 명령을 실행할 디렉터리와 터미널을 명시한다. 환경 변수는 사용 전에 정의하고, 계속 실행되는 명령은 중단 방법을 적는다.
- 영어는 패키지·API 이름처럼 필요한 경우에 유지하고 처음 나올 때 뜻을 설명한다. `observable`, `cleanup receipt` 같은 검증 용어는 관측값·종료 확인 기록처럼 풀어 쓴다.
- 설명 바로 아래에는 대응하는 코드 조각을 둔다. 발췌라면 생략한 부분과 전체 구현의 경로를 적는다. 그대로 실행할 코드와 구조만 설명하는 코드를 구분한다.
- 이미지와 다이어그램은 `docs/assets/` 아래에 두고, 본문만 읽어도 핵심 절차를 이해할 수 있게 대체 설명을 작성한다.

좋은 코드 예시는 태그 이름만 나열하지 않고 값이 어떤 동작을 결정하는지 보여준다. 예를 들어 DiffDrive 설명은 다음과 같이 실제 플러그인 설정과 바퀴 치수를 함께 제시한다.

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

- 초급·중급 공통 로봇은 `tutorial_bot`이다. 외부 로봇을 이식하는 파이널 프로젝트는 학습 목적과 출처를 명시하고 별도 패키지로 구성한다.
- 순수 Gazebo 예제는 `examples/gazebo/`, ROS 2 예제는 `examples/ros2_ws/`에 둔다.
- URDF/Xacro를 로봇 설명의 원본으로 사용하고, 동일한 로봇의 별도 SDF 원본을 중복 관리하지 않는다.
- 반복되는 링크·관절·센서 정의는 Xacro 매크로로 분리하고 인자로 크기, 자세, 토픽을 주입한다.
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

외부 자료는 출처와 버전을 기록하고 이 저장소의 환경에서 실제로 동작하는지 확인한다. 사용자가 요청한 `Gazebo_Harmonic_Rover` 이식처럼 외부 코드를 통합하는 프로젝트는 원본 저장소 URL·기준 커밋·변경 내용을 남기고 기존 라이선스와 저작권 표시를 보존한다. 제삼자 메시·텍스처·문서의 조건도 각각 확인한다. 출처가 외부라는 이유만으로 이 저장소의 라이선스를 일괄 적용하지 않는다.

참고용 복제본은 Git에서 제외한 `ref/`에 둘 수 있다. 실제 이식·수정은 통합 대상 패키지에서 수행하고, 어떤 파일을 가져오거나 다시 작성했는지 이식 기록에 구분한다.

## 변경 확인

문서 변경은 최소한 다음 정적 검사를 통과해야 한다.

```bash
python3 -m mkdocs build --strict
python3 scripts/audit_course_evidence.py --help
```

ROS 2 또는 Gazebo 예제를 변경하면 의존성을 설치하고 작업 공간을 다시 빌드한다.

```bash
source /opt/ros/jazzy/setup.bash
cd examples/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

센서나 시각화 예제를 바꿨다면 토픽 수신뿐 아니라 메시지의 `header.frame_id`, TF 연결, 광학 좌표축, QoS, 시뮬레이션 시간을 함께 확인한다. RViz에서는 로봇·스캔·점군과 Gazebo의 실제 장애물 위치가 맞는지 본다.

변경 기록에는 학습 목표, 실행한 검증 명령, 실제 관찰 결과, 실행하지 못한 항목과 이유를 적는다. 정적 검사 통과를 Gazebo 실행이나 RViz 화면 확인 완료로 표현하지 않는다.
