# gz_ros2_control과 controller

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** TF·Joint State·RViz

## 학습 목표

- Gazebo hardware interface와 controller manager의 관계를 이해합니다.
- joint state, diff drive, trajectory controller를 전환합니다.
- position, velocity state와 command interface를 확인합니다.

## 배경 지식

`gz_ros2_control`은 Harmonic의 simulated joint를 `ros2_control` hardware interface로 노출합니다. controller manager는 한 interface를 동시에 주장하는 controller 충돌을 막고 lifecycle을 관리합니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_control/config/controllers.yaml`

## 실행

```bash
./scripts/check_intermediate_control_tf.sh --launch
```

실행 중 controller를 확인합니다.

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

## 결과 확인

`joint_state_broadcaster`와 `diff_drive_controller`가 활성 상태이고 wheel position·velocity interface가 보여야 합니다. 자동 검증은 trajectory controller로 전환해 joint 위치 명령을 확인한 뒤 diff drive로 되돌립니다.

## 동작 원리

diff drive는 바퀴 velocity command를, trajectory controller는 position command를 사용합니다. controller YAML의 wheel separation 0.38 m와 radius 0.06 m는 Xacro의 기하와 일치해야 합니다.

<figure class="course-figure" id="intermediate-controller-kinematics">
  <img src="../../assets/intermediate/controller-kinematics.svg" alt="차동구동 바퀴 운동학과 controller lifecycle 상태도" loading="lazy">
  <figcaption>그림 1. 바퀴 속도는 선속도와 각속도로 변환되고 lifecycle이 interface 소유권을 제한합니다.</figcaption>
</figure>

## 계산 예제: 바퀴 속도에서 차체 속도로

<div class="course-worked" data-worked-example="controller-kinematics">
반지름 \(r=0.06\,\mathrm{m}\), 바퀴 간격 \(L=0.38\,\mathrm{m}\), \(\omega_r=8\), \(\omega_l=4\,\mathrm{rad/s}\)이면 \(v=r(\omega_r+\omega_l)/2=0.36\,\mathrm{m/s}\), \(\Omega=r(\omega_r-\omega_l)/L=0.632\,\mathrm{rad/s}\)입니다. trajectory controller를 활성화하기 전 diff drive를 비활성화해야 같은 command interface의 중복 claim을 피할 수 있습니다.
</div>

## 문제 해결

`gz_ros2_control` 패키지를 찾지 못하면 먼저 워크스페이스의 `package.xml` 의존성을 설치했는지 확인합니다. ROS 2 Jazzy와 Gazebo Harmonic 조합에서 `rosdep`이 확인하는 시스템 패키지 이름은 `ros-jazzy-gz-ros2-control`입니다. `pip` 패키지나 Gazebo Classic용 `gazebo_ros2_control`로 대체하지 않습니다.

controller가 활성화되지 않으면 interface claim과 joint 이름을 확인합니다. `gazebo_ros2_control`은 Gazebo Classic 계열 이름이며, 이 과정은 Harmonic의 `gz_ros2_control`을 사용합니다.

## 정리

`gz_ros2_control`은 물리 joint와 ROS 2 controller 사이의 검증 가능한 경계입니다.

[이전: TF·Joint State·RViz](06-tf-rviz.md) · [다음: 센서 심화](08-advanced-sensors.md)
