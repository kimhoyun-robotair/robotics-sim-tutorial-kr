# ROS 2 Jazzy와 Gazebo Harmonic 설치

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 없음

## 학습 목표

- 본편이 요구하는 설치 조합을 확인합니다.
- ROS 2와 Gazebo를 연결하는 `ros_gz` 패키지를 설치합니다.
- 설치 결과를 명령으로 검증합니다.

## 설치 원칙

Ubuntu 24.04에서 ROS 2 Jazzy를 먼저 설치합니다. ROS 2 설치 절차와 저장소 설정은 [ROS 2 Jazzy 공식 설치 문서](https://docs.ros.org/en/jazzy/Installation.html)를 따릅니다.

Jazzy에서는 ROS 저장소의 `ros-jazzy-ros-gz`가 권장 Gazebo Harmonic 조합을 설치합니다. Gazebo 공식 문서도 이 조합을 권장하며, 별도의 OSRF Gazebo 저장소는 이 조합에 필수는 아닙니다.

```bash
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-ros-gz
```

이미 ROS 2가 설치되어 있다면 필요한 통합 패키지만 설치합니다.

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz
```

!!! warning "설치 경로를 섞지 마세요"

    Jazzy와 Harmonic을 사용 중이면, 다른 Gazebo 릴리스나 Gazebo Classic용 ROS 통합 패키지를 추가 설치하지 마세요. 서로 다른 ABI와 플러그인 의존성이 섞이면 실행 시점 오류로 이어질 수 있습니다.

## 실행

새 터미널마다 사용 중인 셸에 맞는 ROS 환경을 불러옵니다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    gz --commands
    ros2 pkg list | grep '^ros_gz'
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    gz --commands
    ros2 pkg list | grep '^ros_gz'
    ```

`ros_gz_bridge`, `ros_gz_sim` 등의 패키지명이 출력되면 ROS 2 통합 패키지를 찾을 수 있습니다.

## 결과 확인

다음 장의 SDF 예제를 실행해 `gz sim`이 실제로 시작하는지 확인합니다. 설치 명령 자체만으로는 그래픽 드라이버와 런타임이 정상인지 알 수 없기 때문입니다.

## 자주 발생하는 문제

Gazebo GUI가 열리지 않거나 렌더링 오류가 나면 [문제 해결](03_troubleshooting.md)을 확인합니다. 이 저장소의 공식 지원 범위는 native Ubuntu, amd64, NVIDIA입니다.
