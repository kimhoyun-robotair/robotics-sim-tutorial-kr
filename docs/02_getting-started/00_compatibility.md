# 지원 환경과 호환성

> **난이도:** 시작하기  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **Ubuntu:** 24.04 LTS  
> **검증 기준:** amd64 · headless/software 렌더링

## 튜토리얼의 기준 환경

문서와 예제, 자동 검사는 다음 조합을 기준으로 한다. 아직 설치하지 않았다면 표를 확인한 뒤 [설치 안내](02_installation-jazzy.md)를 먼저 진행한다. 아래 확인 명령은 설치를 마친 뒤 실행한다.

| 계층 | 기준 | 확인할 값 |
| --- | --- | --- |
| 운영체제 | Ubuntu 24.04 LTS | `VERSION_ID="24.04"`, `VERSION_CODENAME=noble` |
| ROS 2 | Jazzy Jalisco | `ROS_DISTRO=jazzy` |
| Gazebo 배포판 | Harmonic | Gazebo Sim 8 계열 |
| SDFormat | 14 계열 | SDF 1.10 예제를 파싱할 수 있어야 한다. |
| ROS-Gazebo 연동 | Jazzy용 `ros_gz` | `ros_gz_sim`, `ros_gz_bridge`, `ros_gz_image` |
| 제어 연동 | Jazzy용 `gz_ros2_control` | `gz_ros2_control/GazeboSimSystem` |

Gazebo의 [ROS 2 설치 호환성 문서](https://gazebosim.org/docs/harmonic/ros_installation/)는 ROS 2 Jazzy와 Gazebo Harmonic을 권장 조합으로 제시한다. ROS 2 Jazzy의 Ubuntu deb도 [Ubuntu 24.04 Noble](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)을 기준으로 제공한다.

`ros-jazzy-ros-gz`는 단순한 브리지 하나가 아니라 Jazzy와 짝이 맞는 Gazebo 연동 패키지를 묶은 메타 패키지이다. 이 튜토리얼에서는 개별 Gazebo 라이브러리 버전을 임의로 고정하지 않고 이 조합을 따른다.

## 한 번에 환경 설정 확인하기

새 터미널에서 다음 명령을 순서대로 실행한다.

```bash
source /opt/ros/jazzy/setup.bash

. /etc/os-release
printf 'Ubuntu=%s (%s)\n' "$VERSION_ID" "$VERSION_CODENAME"
printf 'Architecture=%s\n' "$(dpkg --print-architecture)"
printf 'ROS_DISTRO=%s\n' "${ROS_DISTRO:-unset}"

gz sim --versions
ros2 pkg prefix ros_gz_sim
ros2 pkg prefix ros_gz_bridge
ros2 pkg prefix gz_ros2_control
```

본편 기준에서는 Ubuntu가 `24.04 (noble)`, CPU 아키텍처가 `amd64`, `ROS_DISTRO`가 `jazzy`로 출력되어야 한다. `gz sim --versions`에는 Gazebo Sim 8 계열이 표시되어야 한다. 마지막 세 개의 명령은 각 패키지의 설치 경로를 출력해야 한다.

설치된 deb 패키지도 확인할 수 있다.

```bash
dpkg-query -W \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-gz-ros2-control
```

패키지의 세부 버전은 보안 수정과 저장소 갱신에 따라 달라질 수 있다. Jazzy apt 저장소가 제공하는 버전을 사용하되 Gazebo Sim의 주 버전이 8인지 확인한다.

## 지원 환경과 직접 확인해야 하는 환경

ROS 2 Jazzy는 amd64 외의 플랫폼도 지원한다. 이 저장소의 실행 검사 기준은 Ubuntu 24.04 amd64이다. 아래 환경에서는 설치나 실행이 가능하더라도 그래픽 설정과 실습 결과를 별도로 확인해야 한다.

- aarch64와 ARM 기반 단일 보드 컴퓨터는 본편 실행 환경 검증 범위가 아니다.
- WSL, 가상 머신, 컨테이너 내부 GUI는 디스플레이와 GPU 전달 방식이 달라 별도 조정이 필요하다.
- Ubuntu 이외의 운영체제와 소스 빌드 조합은 본편 설치 절차에서 다루지 않는다.
- NVIDIA, AMD, Intel GPU 가속은 선택 사항이며 필수 조건이 아니다.
- GUI가 없어도 서버 전용과 소프트웨어 렌더링으로 기본 동작을 검증할 수 있어야 한다.

## Classic과 Harmonic 명령 구분하기

Gazebo Classic 11과 Gazebo Harmonic은 이름이 비슷하지만 실행 파일, ROS 통합 방식, 플러그인 이름이 다르다.

| 목적 | 이 과정에서 사용하는 방식 | 섞지 않는 Classic 방식 |
| --- | --- | --- |
| 시뮬레이터 실행 | `gz sim world.sdf` | `gazebo world.world` |
| ROS 연동 | `ros_gz_bridge`, `ros_gz_sim` | `gazebo_ros_pkgs` |
| 모델 생성 | `ros2 run ros_gz_sim create ...` | `spawn_entity.py` |
| DiffDrive | `gz-sim-diff-drive-system` | `libgazebo_ros_diff_drive.so` |
| ROS 2 제어 | `gz_ros2_control` | `gazebo_ros2_control` |

셸에 여러 설치가 섞였는지 다음 명령으로 확인한다.

```bash
type -a ros2
type -a gz
printf '%s\n' "${AMENT_PREFIX_PATH:-unset}" | tr ':' '\n'
printf '%s\n' "${GZ_SIM_SYSTEM_PLUGIN_PATH:-unset}" | tr ':' '\n'
```

`ros2`는 `/opt/ros/jazzy` 아래 설치를 가리켜야 한다. 별도의 소스 빌드나 다른 ROS 배포판 작업 공간 환경이 앞에 있으면 새 터미널을 열고 Jazzy 기본 ROS 환경만 불러온 뒤 다시 검사한다.

## 첫 월드로 실행 확인하기

환경 변수가 맞아도 SDF 해석이나 Gazebo 실행 중 오류가 날 수 있다. [설치 안내의 저장소 준비 단계](02_installation-jazzy.md)를 마친 뒤 저장소 루트에서 실행한다.

```bash
cd ~/robotics-sim-tutorial-kr
source /opt/ros/jazzy/setup.bash
gz sdf -k examples/gazebo/worlds/first-world.sdf
gz sim -s -r examples/gazebo/worlds/first-world.sdf
```

`gz sdf -k`가 성공하면 SDF 구조 검사를 통과한 것이다. `gz sim`은 계속 실행되며 로그를 출력한다. 프로세스가 살아 있다는 사실만으로 성공을 판단하지 말고, 아래 토픽과 서비스도 확인한다. 다른 터미널에서 다음 명령으로 Transport 통신 그래프를 확인한다.

```bash
gz topic -l | sort
gz service -l | sort
```

확인을 마치면 서버 터미널에서 `Ctrl+C`를 눌러 종료한다.

## 다음 단계

조합이 맞으면 [Gazebo Harmonic 소개](01_gazebo-harmonic.md)에서 서버·GUI·Transport 구조를 확인한다. 패키지가 없으면 [ROS 2 Jazzy와 Gazebo Harmonic 설치](02_installation-jazzy.md)를 진행한다.
