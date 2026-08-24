# 지원 환경과 호환성

> **난이도:** 시작하기  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **Ubuntu:** 24.04 LTS  
> **Architecture / GPU:** amd64 / NVIDIA

## 본편 지원 범위

이 저장소의 명령, 예제, CI는 다음 조합만 기준으로 작성하고 검증합니다.

- Ubuntu: 24.04 LTS
- ROS 2: Jazzy
- Gazebo: Harmonic
- Architecture / GPU: amd64 / NVIDIA
- 지원 수준: 본편 지원 및 검증

Gazebo 공식 문서도 ROS 2 Jazzy와 Gazebo Harmonic을 권장 조합으로 표시합니다. [공식 호환성 표](https://gazebosim.org/docs/harmonic/ros_installation/)를 확인할 수 있습니다.

## 지원하지 않는 환경

ARM64, AMD/Intel GPU, WSL, 가상 머신, 다른 운영체제와 다른 ROS/Gazebo 조합은 이 본편의 지원 및 검증 대상이 아닙니다. 해당 환경에서 동작할 수는 있지만, 이 문서의 결과 화면·성능·패키지 이름을 보장하지 않습니다.

## 버전 확인

새 터미널에서 사용 중인 셸에 맞는 ROS 환경을 불러온 뒤 확인합니다.

=== "Bash"

    ```bash
    source /opt/ros/jazzy/setup.bash
    printenv ROS_DISTRO
    gz --versions
    ```

=== "Zsh"

    ```zsh
    source /opt/ros/jazzy/setup.zsh
    printenv ROS_DISTRO
    gz --versions
    ```

첫 명령의 출력은 `jazzy`여야 합니다. `gz --versions` 출력에는 Harmonic에 해당하는 Gazebo 라이브러리 버전이 표시됩니다. 패키지 상태는 다음으로도 확인할 수 있습니다.

```bash
dpkg-query -W 'ros-jazzy-ros-gz*' 'gz-harmonic*'
```

## 혼용하지 않을 명령

이 튜토리얼에서 시뮬레이터 실행 명령은 `gz sim`입니다. Gazebo Classic의 `gazebo`, 구형 명칭의 `ign gazebo`, ROS 1 전용 패키지와 명령은 사용하지 않습니다.
