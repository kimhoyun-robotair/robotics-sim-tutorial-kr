# 시작 단계 문제 해결

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Jazzy 환경 설치

## `ros2` 명령을 찾을 수 없음

현재 셸에 ROS 2 환경이 없는 경우입니다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    printenv ROS_DISTRO
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    printenv ROS_DISTRO
    ```

출력이 `jazzy`인지 확인합니다. 자동으로 불러오도록 설정하려면 셸 설정 파일을 수정하기 전에, 사용 중인 셸과 기존 ROS 설치가 하나인지 먼저 확인하세요.

## `gz` 명령을 찾을 수 없음

Gazebo 패키지와 `ros-jazzy-ros-gz` 설치 상태를 확인합니다.

```bash
dpkg-query -W 'ros-jazzy-ros-gz*' 'gz-harmonic*'
```

패키지가 없다면 [설치 문서](02_installation-jazzy.md)의 명령을 다시 실행합니다.

## GUI가 열리지 않음

이 프로젝트는 native Ubuntu 24.04, amd64, NVIDIA를 기준으로 합니다. 먼저 headless server로 SDF가 파싱되는지 분리해서 확인합니다.

```bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -s examples/gazebo/worlds/first-world.sdf
```

첫 명령은 SDF 문법, 두 번째 명령은 server 시작을 확인합니다. server가 동작하지만 GUI만 실패한다면 GPU 드라이버·디스플레이 세션 문제일 가능성이 큽니다. 오류 전체와 `gz sim --versions` 출력을 함께 수집해 확인하세요.

## 리소스를 찾을 수 없음

World가 로컬 model 또는 mesh를 참조할 때는 해당 경로를 `GZ_SIM_RESOURCE_PATH`에 넣어야 합니다. 이 첫 예제는 외부 model을 참조하지 않으므로 설정 없이 실행됩니다. 이후 자체 model을 추가한 시점에만 필요한 경로를 명시합니다.
