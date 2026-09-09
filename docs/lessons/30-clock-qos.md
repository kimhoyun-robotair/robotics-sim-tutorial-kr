# 30. `/clock`, 시뮬레이션 시간, QoS

[전체 목차](../../README.md) · [이전](29-ros2-bridge.md) · [다음](31-tf-odometry-joints.md)

## 이번 단계에서 할 일

시뮬레이터가 발행하는 시간을 받아 보고, 화면이 느려질 때 컴퓨터 시계와 시뮬레이션 시계가 왜 달라지는지 확인한다. 29단계의 터미널 설정이 필요하다. **GUI 방식과 Python 방식은 하나씩 실행한다. 같은 Domain에서 `/clock` publisher를 두 개 실행하지 않는다.**

벽시계 시간은 컴퓨터에서 실제로 지난 시간이다. 시뮬레이션 시간은 물리 계산이 진행한 시간이다. 1/60초씩 60번 계산했다면 시뮬레이션에서는 1초가 지났지만, 계산에 실제 2초가 걸릴 수 있다. 그때 실시간 비율인 RTF는 대략 0.5이다. 센서의 `header.stamp`, odometry, TF가 같은 시뮬레이션 시간 기준을 써야 메시지를 올바르게 맞출 수 있다.

## 1. GUI로 clock 그래프를 만든다

1. 새 장면에서 **Tools > Robotics > ROS 2 OmniGraphs > Clock**을 연다.
2. 그래프 경로를 `/World/ClockGraph`로 정하고 생성한다.
3. **Window > Graph Editors > Action Graph**에서 생성된 그래프를 연다.
4. `ROS2 Context`의 **Use Domain ID Env Var**를 켜서 터미널의 61을 사용한다.
5. 아래 연결과 publisher의 topicName `/clock`을 확인한다.
6. **Play**를 누른다.

| 출발 노드·출력 | 도착 노드·입력 | 의미 |
|---|---|---|
| On Playback Tick · tick | ROS2 Publish Clock · execIn | 실행할 시점 |
| Isaac Read Simulation Time · simulationTime | ROS2 Publish Clock · timeStamp | 보낼 시뮬레이션 시간 |
| ROS2 Context · context | ROS2 Publish Clock · context | 사용할 ROS 환경 |

터미널 B에서 다음 명령을 실행한다.

```bash
ros2 topic info /clock --verbose
timeout 5s ros2 topic echo /clock --qos-reliability best_effort
```

`timeout`이 5초 후 종료 코드 124를 내는 것은 관찰 시간을 제한한 결과이다. 실제 publisher 동작의 성공 여부는 그 안에 메시지가 출력되었는지로 판단한다. `clock: {sec: ..., nanosec: ...}`가 증가해야 한다.

`Isaac Read Simulation Time`의 `resetOnStop` 기본 동작은 재생을 중단했다가 시작할 때도 시간의 증가를 유지하도록 설계되어 있다. 이를 켜서 0부터 시작하게 만들면 TF와 시간 기반 필터도 함께 새 실행으로 초기화해야 한다. 센서 시간을 만들 때 `omni.timeline`의 화면 시간 값을 대신 가져오지 않는다. [공식 clock 실습](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_clock.html)

## 2. 같은 원리를 Python으로 실행한다

GUI를 종료한 뒤 터미널 A에서 실행한다.

```bash
cd "$TUTORIAL_ROOT"
"$ISAAC_SIM_PATH/python.sh" examples/06_ros_clock.py --seconds 120
```

이 파일은 `rclpy`로 ROS 메시지를 직접 생성한다. 물리 계산 뒤의 `world.current_time`을 사용하며, 매번 시스템 시간을 복사하지 않는다.

```python
world.step(render=True)
stamp_ns = round(world.current_time * 1_000_000_000)
message = Clock()
message.clock.sec, message.clock.nanosec = divmod(stamp_ns, 1_000_000_000)
publisher.publish(message)
```

1초는 10억 나노초이다. 나눗셈의 몫을 `sec`, 나머지를 `nanosec`에 넣어 부동소수점 값을 ROS의 시간 구조로 바꾼다. 코드 전체에서는 Play 상태와 이전 stamp도 검사한다. 루프 끝의 짧은 `sleep`은 컴퓨터의 CPU를 계속 점유하지 않도록 실행 속도를 제한할 뿐, 메시지의 시간값을 만들지는 않는다.

터미널 B에서 실제 수신 검사를 실행한다.

```bash
python3 scripts/ros_acceptance.py --mode clock --duration 10 \
  --output artifacts/clock-acceptance.json
cat artifacts/clock-acceptance.json
```

정상 실행에서는 `clock_received`와 `clock_strictly_increasing`이 `true`, 최종 `status`가 `PASS`가 된다. 예제를 실행하지 않고 검사기만 실행하면 10초 뒤 `FAIL`로 끝난다. 이 결과는 clock 수신 검사이며 카메라 렌더링 검사까지 뜻하지 않는다.

## 3. 외부 노드에 시뮬레이션 시간을 선택한다

```bash
rviz2 --ros-args -p use_sim_time:=true
ros2 node list
```

RViz가 이미 실행 중이라면 목록에서 이름을 확인한다. `/rviz2`라면 다음과 같이 설정한다. 실제 이름이 다르면 출력된 이름을 사용한다.

```bash
ros2 param set /rviz2 use_sim_time true
ros2 param get /rviz2 use_sim_time
```

`use_sim_time`은 모든 ROS 노드에 한 번에 적용하는 전역 스위치가 아니다. Nav2, RViz, 기록기 등 시간을 사용하는 각 노드에 적용한다. 반대로 명령 수신이 끊겼는지 감시하는 watchdog은 시뮬레이션을 잠시 멈춰도 동작해야 하므로 `time.monotonic()` 같은 벽시계 기준을 사용한다.

## 4. QoS를 맞춘다

QoS는 전달 신뢰성, 저장할 메시지 수, 나중에 연결된 구독자에게 데이터를 다시 줄지 등의 약속이다. 메시지 이름과 자료형이 맞아도 QoS가 호환되지 않으면 데이터를 받지 못할 수 있다.

| 자료 | 이 튜토리얼의 선택 | 이유 |
|---|---|---|
| `/clock` | clock용 QoS, best effort | 가장 최근의 시간을 계속 받는 용도 |
| RGB·LiDAR 수신 | sensor data QoS, best effort | 오래된 대량 센서 데이터가 쌓이지 않도록 함 |
| 속도 명령 | reliable, depth 1 | 최신 명령만 유지하고 수신 측 watchdog과 함께 사용 |
| `/tf_static` | transient local | 늦게 실행한 구독자도 고정 변환을 받을 수 있도록 함 |

```python
from rclpy.qos import qos_profile_sensor_data
subscription = node.create_subscription(
    Image, "/camera/rgb", image_callback, qos_profile_sensor_data
)
```

RViz의 Image나 LaserScan 항목도 **Topic > Reliability Policy > Best Effort**로 맞춘다. Reliable publisher를 best-effort subscriber가 받는 조합과, 그 반대 조합은 같지 않다. 실제 publisher 설정은 `ros2 topic info <토픽> --verbose`로 확인한다. [NVIDIA QoS 실습](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_qos.html)

## 완료 기준과 과제

clock 검사 JSON이 `PASS`이고, RViz의 시뮬레이션 시간이 Isaac Sim의 Play/Pause에 맞춰 진행·정지하면 완료한다. 과제로 `--seconds 30` 실행을 마친 뒤 검사기만 실행해 `FAIL` 결과를 남긴다. 성공한 검사와 publisher 부재를 검사기가 구별하는지 확인하는 실험이다.

메시지가 없으면 29단계의 환경, publisher 수, Play 상태, QoS 순으로 확인한다. 시간 역행 오류가 있으면 `/clock` publisher가 중복되었는지, 실행 도중 Reset했는지 확인하고 모든 시간 소비 노드를 새로 시작한다.
