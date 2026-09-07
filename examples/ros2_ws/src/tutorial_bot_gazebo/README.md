# tutorial_bot_gazebo

Gazebo 월드, 지도, 센서 검증 기준을 설치하는 `ament_cmake` 패키지이다.

| 파일 | 용도 |
|---|---|
| `worlds/training.sdf` | 주행·Nav2 통합 실습 |
| `worlds/sensor-test.sdf` | 벽과 정면 표적을 이용한 센서 검증 |
| `maps/training.yaml`, `training.pgm` | `training.sdf`에 맞춘 Nav2 지도 |
| `config/sensor_expectations.yaml` | 센서 프레임, 해상도, 발행 빈도와 측정값의 기준 |

월드에는 물리, 물체 생성, 장면 전달, 렌더링 센서(`ogre2`), IMU 시스템 플러그인을 포함한다. 센서 태그가 로봇 모델에 있어도 필요한 월드 플러그인이 빠지면 데이터가 나오지 않는다.

## 확인

[중급 실행 준비](../../../../docs/04_intermediate/index.md#intermediate-setup)를 마친 뒤 저장소 루트에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
source examples/ros2_ws/install/setup.bash
world="$(ros2 pkg prefix --share tutorial_bot_gazebo)/worlds/sensor-test.sdf"
gz sdf -k "$world"
gz sim -r "$world"
```

이 명령은 월드만 실행한다. 로봇 생성, 브리지, RViz 실행은 [센서 실습](../../../../docs/04_intermediate/08-advanced-sensors.md)의 터미널별 순서를 따른다. `-s`를 추가하면 GUI 없이 서버만 실행하지만, 카메라와 GPU LiDAR에는 여전히 렌더링을 지원하는 환경이 필요하다.
