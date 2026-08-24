# 초급: Gazebo Sim으로 `tutorial_bot` 시작하기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 시작하기

## 목표

초급 과정에서는 SDF world와 URDF/Xacro를 읽고 작성한 뒤, 같은 `tutorial_bot`에 바퀴·DiffDrive·LiDAR·카메라·IMU를 추가합니다. 마지막에는 `ros_gz_bridge`로 `/cmd_vel`, `/scan`, `/imu`, 이미지, `/clock`을 ROS 2에 연결합니다.

## 장 구성

1. Gazebo Sim의 실행 모델과 GUI를 익힙니다.
2. SDF로 첫 world를 작성하고, 물리·좌표·충돌을 확인합니다.
3. URDF/Xacro로 `tutorial_bot`의 base link와 좌우 바퀴를 만듭니다.
4. DiffDrive를 추가하고 Gazebo Transport 토픽을 관찰합니다.
5. `ros_gz_bridge`로 ROS 2 토픽과 연결합니다.

## 첫 실습

[SDF 기초](03-sdf-basics.md)와 [첫 World](04-first-world.md)에서 순수 Gazebo 예제를 실행합니다. 이어서 [첫 Robot](05-first-robot.md)과 [바퀴와 Joint](06-joints.md)에서 이동 기반 `tutorial_bot`을 만듭니다.
