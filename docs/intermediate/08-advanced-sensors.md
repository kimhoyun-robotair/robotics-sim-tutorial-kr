# 센서 심화: 노이즈와 주기

> **난이도:** 중급  
> **Gazebo:** Harmonic  
> **ROS 2:** Jazzy  
> **선행 학습:** `gz_ros2_control`

## 학습 목표

- LiDAR, RGB·Depth Camera, IMU의 핵심 파라미터를 해석합니다.
- rate, 해상도, intrinsic, frame, 유한값을 실제 메시지에서 검증합니다.
- 설정값과 관찰값을 분리합니다.

## 배경 지식

센서 설정이 존재한다는 사실만으로 정상 동작을 보장할 수 없습니다. update rate, FOV, 해상도, camera intrinsic, noise 분포와 frame ID를 실제 ROS 메시지로 측정해야 합니다.

## 예제 파일

- `examples/ros2_ws/src/tutorial_bot_gazebo/worlds/sensor-test.sdf`
- `examples/ros2_ws/src/tutorial_bot_gazebo/config/sensor_expectations.yaml`
- `examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro`

## 실행

```bash
./scripts/check_intermediate_sensors.sh --launch
```

## 결과 확인

검증은 20초 준비 뒤 10초 동안 표본을 모아 LiDAR 360개 표본, RGB·depth 320×240, frame ID, intrinsic, 유한값, rate와 noise를 검사합니다. 종료 코드 0이 성공 조건입니다.

## 동작 원리

world는 재현 가능한 시험 환경을 제공하고, Xacro의 Gazebo sensor 확장은 로봇 link에 센서를 붙입니다. `sensor_expectations.yaml`은 기대값을 명시해 단순 토픽 존재 확인보다 강한 계약을 만듭니다.

<figure class="course-figure" id="intermediate-sensor-statistics">
  <img src="../../assets/intermediate/sensor-statistics.svg" alt="센서의 가우시안 노이즈 분포와 메시지 수신률 계산도" loading="lazy">
  <figcaption>그림 1. 센서 품질은 설정값이 아니라 실제 표본의 rate, 평균, 표준편차로 판정합니다.</figcaption>
</figure>

## 계산 예제: rate와 노이즈

<div class="course-worked" data-worked-example="sensor-statistics">
10초 동안 30 Hz 센서를 검사하면 기대 표본은 300개이고 95% 기준은 285개입니다. retained finite 표본이 296개, 첫·끝 stamp 차가 9.84초면 관측 rate는 \((296-1)/9.84=29.98\,\mathrm{Hz}\)입니다. 노이즈 \(\sigma=0.01\), \(n=296\)이면 평균 오차 허용항 \(5\sigma/\sqrt n=0.00291\)이며, sample standard deviation도 \([0.005,0.015]\) 안이어야 합니다.
</div>

## 문제 해결

rate가 낮으면 simulation real-time factor와 bridge 처리량을 확인합니다. PointCloud가 RViz에 보이지 않으면 `camera_optical_frame`까지의 TF와 depth 유한값을 확인합니다.

## 정리

센서는 설정 텍스트가 아니라 실제 표본의 크기·시간·frame·통계로 검증합니다.
