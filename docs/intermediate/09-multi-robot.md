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

<figure class="course-figure" id="intermediate-namespace-isolation">
  <img src="../../assets/intermediate/namespace-isolation.svg" alt="robot1과 robot2의 entity topic controller TF frame 격리도" loading="lazy">
  <figcaption>그림 1. 두 로봇은 clock만 공유하고 entity, topic, controller, TF frame을 분리합니다.</figcaption>
</figure>

## 계산 예제: 교차 영향 판정

<div class="course-worked" data-worked-example="namespace-isolation">
robot1 명령 전후 변위를 \(d_1\), 명령하지 않은 robot2 변위를 \(d_2\)라 두고 \(d_1\ge0.60\,\mathrm{m}\), \(d_2\le0.02\,\mathrm{m}\)를 요구합니다. 관측값이 각각 0.69 m와 0.004 m라면 이동과 격리가 동시에 합격합니다. TF 역시 `robot1/base_link`와 `robot2/base_link`의 parent 집합 교집합이 없어야 합니다.
</div>

## 문제 해결

동일 entity 이름이나 namespace를 주면 launch가 준비 단계 전에 실패해야 정상입니다. TF가 섞이면 `frame_prefix`와 sensor `frame_id`가 같은 접두사를 쓰는지 확인합니다.

## 정리

다중 로봇의 핵심은 프로세스 수가 아니라 이름, 토픽, controller, TF의 완전한 격리입니다.

[이전: 센서 심화](08-advanced-sensors.md) · [다음: Nav2 연동](10-nav2.md)
