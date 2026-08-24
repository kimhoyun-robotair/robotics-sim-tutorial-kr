# 다중 로봇 namespace와 TF

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** 센서 심화

## 학습 목표

- 두 entity의 이름과 ROS namespace를 분리합니다.
- 토픽, controller, TF frame을 로봇별로 격리합니다.
- 한 로봇의 명령이 다른 로봇을 움직이지 않는지 검증합니다.

## 배경 지식

다중 로봇에서는 `/robot1`, `/robot2` namespace만으로 부족합니다. Gazebo entity, controller manager, sensor 토픽, `robot1/`·`robot2/` TF prefix까지 일관되게 분리해야 합니다. `/clock`은 world 전체에서 하나만 공유합니다.

## 예제 파일

- `examples/ros2_ws/src/tutorial_bot_bringup/launch/multi_robot.launch.py`
- `examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-multi-robot.yaml`
- `examples/ros2_ws/src/tutorial_bot_control/config/multi_robot_controllers.yaml`

## 실행

```bash
cd scripts
./check_intermediate_multi_robot.sh \
  --launch
cd ..
```

## 결과 확인

자동 검증은 두 로봇의 live sensor와 joint state, 중복 TF parent 부재, 증가하는 단일 clock을 확인합니다. 이어 robot1만 약 0.69 m, robot2만 약 0.69 m 움직여 상호 격리를 증명합니다.

## 동작 원리

launch는 각 Xacro에 model name, namespace, TF prefix와 sensor topic을 전달합니다. bridge와 controller YAML도 같은 namespace 계약을 사용합니다.

## 문제 해결

동일 entity 이름이나 namespace를 주면 launch가 준비 단계 전에 실패해야 정상입니다. TF가 섞이면 `frame_prefix`와 sensor `frame_id`가 같은 접두사를 쓰는지 확인합니다.

## 정리

다중 로봇의 핵심은 프로세스 수가 아니라 이름, 토픽, controller, TF의 완전한 격리입니다.
