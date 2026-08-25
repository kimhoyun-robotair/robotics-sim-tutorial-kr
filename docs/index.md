# Gazebo Sim 튜토리얼에 오신 것을 환영합니다

> **기준 환경:** Ubuntu 24.04 LTS · ROS 2 Jazzy · Gazebo Harmonic · amd64 · headless/software rendering

이 튜토리얼은 Gazebo Sim을 단순한 GUI 도구가 아니라, 재현 가능한 로봇 시뮬레이션 프로젝트로 사용하는 방법을 다룹니다. 설명을 읽은 뒤 바로 저장소의 예제를 실행하고, 결과를 토픽과 시각화로 확인하는 흐름을 유지합니다.

## 무엇을 만들까요?

처음에는 바닥·조명·상자로 된 작은 SDF world를 실행합니다. 이후 같은 `tutorial_bot`에 두 바퀴, DiffDrive, LiDAR, 카메라, IMU를 순서대로 더합니다. 중급에서는 ROS 2 launch와 TF, RViz, `ros_gz_bridge`, `gz_ros2_control`, Nav2를 연결하고, 고급에서는 Gazebo ECS와 C++ System Plugin, headless 테스트, CI까지 확장합니다.

## 시작 전 확인

터미널에서 다음 두 명령이 동작해야 합니다.

```bash
gz --commands
ros2 --help
```

설치가 끝난 환경이라도 새 터미널에서는 사용 중인 셸에 맞는 ROS 환경을 불러와야 합니다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    ```

`gz sim`은 Gazebo Harmonic의 명령이고, Gazebo Classic의 `gazebo` 명령과 섞어 쓰지 않습니다.

## 학습 순서

1. [호환성](compatibility.md)과 [Harmonic 소개](getting-started/gazebo-harmonic.md)를 읽습니다.
2. [SDF 기초](beginner/03-sdf-basics.md)와 [첫 World](beginner/04-first-world.md)를 실행해 Gazebo server를 확인합니다.
3. 초급에서 `tutorial_bot`의 이동과 센서를 완성합니다.
4. 중급과 고급에서 ROS 2 프로젝트 구조와 자동 검증을 더합니다.

전체 학습 경로는 초급 12개, 중급 12개, 고급 7개입니다. 각 경로의 선행 조건과
후속 구현 작업은 `docs/course-manifest.yaml`에 고정되어 있습니다.

!!! tip "명령 실행 원칙"

    예제는 저장소 루트에서 실행하는 것을 기준으로 합니다. 경로가 긴 명령은 그대로 복사하기보다 먼저 현재 위치를 `pwd`로 확인하세요.
