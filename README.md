# Robotics Simulation 튜토리얼

| 항목 | 항목내용 |
| --- | --- |
| 작성자 | [kimhoyun-robotair](https://github.com/kimhoyun-robotair) |
| 유지보수 | [kimhoyun-robotair](https://github.com/kimhoyun-robotair) |
| 작성일 | 2026.8.30 |
| 수정일 | 2026.09.02 |

로봇을 개발하는데 있어서 시뮬레이션의 중요성은 갈수록 커지고 있다고 생각한다.
특히나 알고리즘의 소프트웨어적인 강건성을 확인하는 것, 그리고 Sim-to-Real 관점에서 더욱 그렇다.
따라서 시뮬레이션 기초에 대해서 공부를 하고, 본인 연구에 활용하는 것 역시 중요하다고 생각한다.
(당연히 시뮬레이션이 필수적이지 않은 연구에 대해서 얘기하는게 아니다).

따라서 Robotics 분야에서 많이, 널리 쓰이는 두 시뮬레이션 툴인 **Gazebo**, **Isaac Sim**에 대해서,
다음 환경에 대해서 튜토리얼을 정리해두려고 한다 (추후 MuJoCo, Chrono 등이 추가될 수 있다).

## Gazebo & Isaac Sim 튜토리얼 개관

| | Gazebo | Isaac Sim |
| --- | --- | --- |
| 운영체제 | Ubuntu 22.04 LTS & Ubuntu 24.04 LTS | Ubuntu 24.04 LTS|
| ROS 2 | Humble & Jazzy | Jazzy |
| Version | Gazebo11 & Harmonic | Isaac Sim 5.1 & 6.0 .. |

**Gazebo 튜토리얼**의 경우는 다음 브랜치에 정리한다.
- `Humble` : Ubuntu 22.04 LTS / ROS2 Humble / Gazebo11 조합의 튜토리얼
- `Jazzy` : Ubuntu 24.04 LTS / ROS2 Jazzy / Gazebo Harmonic 조합의 튜토리얼
  
**Isaac Sim (Isaac Lab) 튜토리얼**의 경우 다음 브랜치에 정리한다.
- `IsaacSim5.1` : Ubuntu 24.04 LTS / ROS2 Jazzy / Isaac Sim 5.1.0 조합의 튜토리얼
- `IsaacSim6.0.1` : Ubuntu 24.04 LTS / ROS2 Jazzy / Isaac Sim 6.0.0 + Isaac Sim 6.0.1 조합의 튜토리얼

따라서 원하는 버젼의 시뮬레이터 혹은 원하는 버젼의 ROS2 연동 튜토리얼을 보고 싶으면 `git clone`을 할 때 `branch`를 바꿔서 `clone` 하거나 혹은 `main` 브랜치에서 `swtich` 하기를 바란다.

추가적으로, 시뮬레이션 관련해서 유용하다고 생각하는 자료들을 리스트 업해서 기록하려고 한다.
해당 모음집들은 다음과 같다.

## 유용한 시뮬레이션 관련 자료 모음집

### 내꺼
| 이름 | 내용 |
| --- | --- |
| MarsLab | Accepted to [iSapRo 2026](https://www.isairas-isparo.de/).<br> 화성 로봇 Navigation 시뮬레이터 |

### URDF, 오픈소스 로봇 관련 유용한 자료집
| 이름 | 내용 |
| --- | --- |
| [**awesome-urdf**](https://github.com/gbionics/awesome-urdf) | URDF에 관련된 교육자료, 라이브러리, Extension 등을 모아놓은 자료집 |
| [**awesome-open-source-robots**](https://github.com/stephane-caron/awesome-open-source-robots) | 다양한 오픈소스 로봇 하드웨어 + 소프트웨어 자료링크를 모아둔 자료집 |

### 시뮬레이션용 Asset 모음집
| 이름 | 내용 |
| --- | --- |
| [**robot_descriptions.py**](https://github.com/robot-descriptions/robot_descriptions.py) | MuJoCo, PyBullet 등 다양한 시뮬레이터에 호환되는 robot description을 바로 뽑을 수 있는 패키지 + URDF 파일 예시 다수 보유 |
| [**robot_description.cpp**](https://github.com/mayataka/robot_descriptions.cpp) | 위 패키지를 C++ 버젼으로 migration 해서 사용 가능하게 만든 패키지 |
| [**mujoco_menagerie**](https://github.com/google-deepmind/mujoco_menagerie) | 구글 딥마인드에서 MuJoCo에서 사용 가능한, 다수의 로봇 asset을 큐레이션 해놓은 자료집 |
| [**models**](https://github.com/RobotLocomotion/models) | RobotLocomotion Group에서 [Drake](https://drake.mit.edu/)를 포함해서 다양한 로봇 모델링을 모아놓은 패키지 |
| [**awesome-robot-descriptions**](https://github.com/robot-descriptions/awesome-robot-descriptions) | 다양한 로봇에 대해 Xacro, URDF, MJCF를 모아두고, Visual/Inertial/Collision까지 분류해둔 친절한 자료집 |
| [**m2020-urdf-models**](https://github.com/nasa-jpl/m2020-urdf-models) | 퍼서비어런스 화성 로버와 잉게뉴이티 화성 드론에 대한 Visual URDF 파일을 제공하는 NASA 공식 리포 |
| [**PLUME**](https://github.com/Gabryss/P.L.U.M.E) | Accepted to iSpaRo 2025. 시뮬레이션용 초고화질 동굴 Mesh를 생성하는 패키지. 저자에 따르면 현재 업그레이드 버젼 개발 중 |
| [**rock-generator**](https://github.com/LeLocTai/rock-generator) | 유니티를 통해서 다양한 Rock을 생성하는 패키지 |
| [**infigen**](https://github.com/princeton-vl/infinigen) | Accepted to CVPR 2023/2024. 블렌더 기반으로 엄청나게 다양한 Photorealistic 3D asset을 생성할 수 있는 패키지 |
| [**MOGI-ROS**](https://github.com/MOGI-ROS) | ROS2 + Gazebo 기반 (내가 본 것 중에는) 가장 완벽한 튜토리얼을 제공하는 리포지터리 모음집 |
| [**Dynamic_World_Generator**](https://github.com/ali-pahlevani/Dynamic_World_Generator) | PyQt5 기반 Gazebo에 호환되는 다양한 Dynamic World를 쉽게 만들 수 있게 도와주는 도구 |

### 이런저런 시뮬레이터들 (추후 확장되면 분류 추가 예정)
| 이름 | 내용 |
| --- | --- |
| [**alphasim**](https://github.com/NVlabs/alpasim) | NVIDIA에서 공개한 자율주행 시뮬레이터 |
| [**GRADE-RR**](https://github.com/eliabntt/GRADE-RR) | Accepted to IJRR 2026. 다양한 Dynamic Env를 생성할 수 있는 시뮬레이션 패키지 |
| [**ROS2-Self-Driving-Car-AI-using-OpenCV**](https://github.com/noshluk2/ROS2-Self-Driving-Car-AI-using-OpenCV) | ROS2와 Gazebo를 활용한 자율주행 시뮬레이터 |
| [**robomaster_mujoco**](https://github.com/12B-theDon/robomaster_mujoco) | MuJoCo에서 RoboMaster 로봇을 시뮬레이션 할 수 있는 패키지 |
| [**MARSIM**](https://github.com/hku-mars/MARSIM) | LiDAR 기반 UAV 시뮬레이션 (HKUST에서 엄청 많이 씀) |
| [**UAVS**](https://github.com/wangwei39120157028/UAVS) | 다양한 드론 시뮬레이터 |
| [**asv_wave_sim**](https://github.com/srmainwaring/asv_wave_sim) | Gazebo 기반 수상 로봇 시뮬레이터 |
| [**gazebo_ros_battery**](https://github.com/nilseuropa/gazebo_ros_battery) | Gazebo Classic에서 배터리의 수학적 모델링에 따라 시뮬레이션 하는 플러그인 |
| [**gazebo_ros_motor**](https://github.com/nilseuropa/gazebo_ros_motors) | Gazebo Classic에서 모터의 수학적 모델링에 따라 시뮬레이션 하는 플러그인 |
| [**car_sim**](https://github.com/CihatAltiparmak/car_sim) | Gazebo Classic에서 Ackermann 기반의 차량 시뮬레이션 |
| [**rmf_demo**](https://github.com/open-rmf/rmf_demos) | Gazebo 기반 Multi-Floor 등 다양한 환경 시뮬레이션을 제공하는 패키지 |
| [**ProjectAirSim**](https://github.com/iamaisim/ProjectAirSim) | UE5 기반, 드론 시뮬레이션 GOAT |

### 우주 로봇 시뮬레이터
| 이름 | 내용 |
| --- | --- |
| [**martian**](https://github.com/nasa-jpl/martian) | Accepted to ICRA 2026 WS. 화성에서 localization 연구를 위한 Drone-View 시뮬레이터 |
| [**astro_navigation**](https://github.com/rsasaki0109/astro_navigation) | GNSS Denied 인 천체 환경에서 다양한 navigation을 테스트 해볼 수 있는 시뮬레이터 |
| [**oaisys**](https://github.com/DLR-RM/oaisys) | Accepted to IROS 2021. DLR에서 개발한 Planetary Robotics 시뮬레이터 |
| [**OmniLRS**](https://github.com/OmniLRS/OmniLRS) | Accepted to ICRA 2024. Isaac Sim 기반 월면 로버 시뮬레이터 |
| [**MarsSim**](https://github.com/MorpheusPD/MarsSim) | Accepted to IEEE MetroAeroSpace 2020. Gazebo 기반 화성 시뮬레이터 |
| [**LuSeg**](https://github.com/nubot-nudt/LuSeg) | Accepted to IROS 2025. 언리얼 엔진 기반 월면 로버 시뮬레이터 |
