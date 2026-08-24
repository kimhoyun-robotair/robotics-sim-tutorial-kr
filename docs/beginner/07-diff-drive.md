# DiffDrive로 `tutorial_bot` 움직이기

> **난이도:** 초급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 바퀴와 Joint

## 학습 목표

- Differential Drive의 선속도·각속도 입력을 이해합니다.
- Gazebo DiffDrive System이 좌우 continuous joint를 제어하도록 설정합니다.
- Gazebo Transport의 `cmd_vel`과 odometry 토픽을 확인합니다.

## 배경 지식

Differential Drive는 왼쪽과 오른쪽 바퀴의 회전 속도 차이로 이동합니다. 전진은 두 바퀴를 같은 방향으로 돌리고, 회전은 두 바퀴를 서로 다른 속도로 돌립니다.

Gazebo DiffDrive System은 `cmd_vel` Twist 메시지를 받아 좌우 joint 속도로 변환합니다. 이 예제의 wheel separation은 0.38 m이고 wheel radius는 0.06 m입니다. ROS 2가 아닌 Gazebo Transport 토픽을 먼저 사용하므로, 이 장에서는 `gz topic`으로 제어합니다.

## 예제 파일

DiffDrive plugin 설정은 로봇 원본에 포함됩니다.

`examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

headless smoke test는 Xacro를 임시 SDF로 변환해 `first-world.sdf`에 spawn합니다.

`scripts/check_diff_drive.sh`

## 실행

저장소 루트에서 다음 명령을 실행합니다.

```bash
./scripts/check_diff_drive.sh
```

스크립트는 Gazebo server를 headless로 시작하고 `tutorial_bot`을 spawn한 뒤 다음 토픽의 존재를 확인합니다.

```text
/model/tutorial_bot/cmd_vel
/model/tutorial_bot/odometry
```

## Gazebo Transport로 제어하기

GUI를 포함한 시뮬레이션을 따로 실행했다면 다음 명령으로 전진 Twist를 발행합니다.

```bash
gz topic -t /model/tutorial_bot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}'
```

odometry를 관찰하려면 다음을 사용합니다.

```bash
gz topic -e -t /model/tutorial_bot/odometry
```

## 결과 확인

smoke test는 `linear.x = 0.2` 명령 뒤 odometry의 `pose.position.x > 0.05`와 `twist.linear.x > 0.15`를 검사합니다. `DiffDrive motion verified.`가 출력되면 plugin이 로드됐고, 모델별 `cmd_vel` 입력이 실제 전진 운동과 odometry 출력까지 전달된 것입니다.

## 동작 원리

Xacro의 `<gazebo>` 확장은 URDF를 SDF로 변환할 때 model plugin으로 전달됩니다. DiffDrive System은 `left_wheel_joint`, `right_wheel_joint` 이름으로 joint를 찾고, wheel separation·radius 값을 사용해 Twist를 바퀴 속도로 환산합니다.

## 정리

`tutorial_bot`은 Gazebo Transport에서 속도 명령을 받을 수 있습니다. 다음 초급 단계에서는 LiDAR, Camera, IMU를 추가해 주변 환경을 관측합니다.
