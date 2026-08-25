# ros_gz_bridge YAML 심화

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** Robot Spawn

## 학습 목표

- YAML로 여러 bridge를 일괄 구성합니다.
- `ROS_TO_GZ`, `GZ_TO_ROS`, `BIDIRECTIONAL`을 구분합니다.
- 센서와 clock에 알맞은 QoS를 사용합니다.

## 배경 지식

bridge는 ROS 2 메시지와 Gazebo Transport 메시지를 변환합니다. 센서는 주로 `GZ_TO_ROS`, 속도 명령은 `ROS_TO_GZ`가 적합합니다. `/clock`과 sensor data는 지연보다 최신 표본이 중요하므로 지정 QoS를 사용합니다.

## 예제 파일

`examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml`

## 실행

```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args -p config_file:=$(pwd)/examples/ros2_ws/src/tutorial_bot_bringup/config/bridge-intermediate.yaml
```

## 결과 확인

```bash
ros2 topic list | grep -E '^/(clock|scan|imu|camera)'
ros2 topic info /scan -v
```

`/clock`, `/scan`, `/imu`, camera 관련 토픽이 보이면 YAML이 적용된 것입니다.

## 동작 원리

각 항목은 ROS 토픽명, Gazebo 토픽명, 양쪽 타입, 방향과 QoS를 선언합니다. image payload는 `ros_gz_image`가 담당하고 CameraInfo·PointCloud 등은 parameter bridge가 담당할 수 있습니다.

<figure class="course-figure" id="intermediate-bridge-qos">
  <img src="../../assets/intermediate/bridge-qos.svg" alt="ROS 2와 Gazebo Transport 사이 bridge 방향과 QoS 선택도" loading="lazy">
  <figcaption>그림 1. 명령은 ROS에서 Gazebo로, 센서와 clock은 Gazebo에서 ROS로 흐릅니다.</figcaption>
</figure>

## 계산 예제: queue 지연과 방향

<div class="course-worked" data-worked-example="bridge-qos">
30 Hz LaserScan에서 queue depth가 5라면 소비자가 밀렸을 때 오래된 표본의 최대 대기량은 대략 \((5-1)/30=0.133\,\mathrm{s}\)입니다. 센서는 작은 depth와 best-effort로 최신성을 택하고, `/cmd_vel`은 `ROS_TO_GZ`로만 선언해 되먹임 loop를 막습니다. `ros2 topic info /scan -v`로 실제 QoS endpoint를 확인합니다.
</div>

## 문제 해결

타입 이름이 틀리면 bridge가 생성되지 않습니다. Gazebo Classic의 `ros_gz_bridge` 이전 이름이나 `gazebo_ros_pkgs` 예제를 섞지 말고 Harmonic 타입을 확인합니다.

## 정리

YAML bridge는 토픽 계약을 코드와 분리하고 방향·namespace·QoS를 검토 가능하게 만듭니다.
