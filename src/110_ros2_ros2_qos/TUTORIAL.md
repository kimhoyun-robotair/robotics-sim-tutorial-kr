# 110. QoS: 센서 전달 정책과 늦게 접속한 subscriber

권장 학습 순서 **110** · ROS 2 연결과 기본 통신 · 출처 ID `t017`

예상 결과는 `/topic`의 QoS를 실제로 확인하고, 한 번만 보낸 String을 나중에 시작한 두 subscriber가 각각 받을 수 있는 것이다. 원문의 Generic Publisher/Countdown GUI 실습에 `qos_profile.json`과 시간 제한이 있는 실제 ROS 수신기 `listen.py`를 포함했다.

## 이 폴더에서 시작하기

다른 로컬 튜토리얼을 먼저 읽거나 `tutorial_common`을 설치할 필요가 없다. 이 폴더를 통째로 복사해도 된다. 아래 명령은 이 폴더에서 실행한다. Isaac Sim 5.1.0과 지원되는 NVIDIA GPU/드라이버가 필요하다. ROS 2는 Ubuntu 22.04의 Humble 또는 Ubuntu 24.04의 Jazzy를 사용한다. ROS 패키지가 아직 없다면 [5.1 ROS 설치 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)대로 준비한다. 이 실습은 패키지 설치를 자동 실행하지 않는다.

Bash 터미널 A와 ROS 명령을 실행할 터미널 B 각각에서 같은 설정을 적용한다.

```bash
source /opt/ros/humble/setup.bash
# Ubuntu 24.04에서는 위 한 줄 대신 source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM="$HOME/isaacsim"
```

`ISAAC_SIM`은 실제 5.1.0 설치 경로로 바꾼다. ROS_DOMAIN_ID는 DDS 통신 그룹 번호이므로 두 프로세스가 같아야 한다. GUI 사용 시 터미널 A에서 `"$ISAAC_SIM/isaac-sim.sh"`를 실행하고 **Window > Extensions**에서 `isaacsim.ros2.bridge`를 활성화한다. Standalone `run.py`는 이 확장을 직접 활성화한다. 외부 ROS 노드는 시스템 `python3`, 시뮬레이터 스크립트는 `"$ISAAC_SIM/python.sh"`를 쓴다. 여러 컴퓨터를 연결할 때에는 양쪽의 `FASTRTPS_DEFAULT_PROFILES_FILE`을 5.1 설치 문서에 맞게 지정한다.

Stage는 현재 열어 둔 USD 장면이고, prim은 `/World/Robot`처럼 경로로 찾는 장면 객체이다. Action Graph는 prim으로 저장되는 실행 그래프다. `execIn/execOut` 연결은 **언제 실행하는가**, 숫자·문자열 연결은 **무슨 데이터를 전달하는가**를 결정한다. 메시지 발행 여부는 아래 ROS 명령으로 직접 확인한다. 코드 생성과 실제 DDS 수신은 서로 다른 확인 단계이다.

## Sensor Data QoS부터 확인하기

1. 새 Stage를 연다. **Tools > Robotics > ROS 2 OmniGraphs > Generic Publisher**에서 **Publish String**을 선택하고 OK를 누른다. `/Graph/ROS_GenericPub`를 오른쪽 클릭해 **Open Graph**를 연다.
2. String 상수 노드의 value를 `qos_lesson`으로 바꾼다. Publisher가 `std_msgs/msg/String`, topicName=`/topic`인지 확인한다. Tick과 Context가 각각 execIn/context에 연결되어 있다.
3. **ROS2 QoS Profile** 노드를 추가하고 출력 `qosProfile`을 publisher의 같은 입력에 연결한다. `createProfile=Sensor Data`로 선택한다. 노드를 다시 선택해 UI의 policy 값이 갱신되었는지 본다.
4. Play 후 외부 ROS 터미널에서 실제 publisher 정책을 확인한다.

   ```bash
   ros2 topic info /topic -v
   python3 listen.py --volatile --best-effort --timeout 10
   ```

   Sensor Data는 낮은 지연을 중시하는 best effort/volatile 정책이다. reliable 수신기를 무조건 붙이면 offered/requested QoS가 맞지 않아 연결되지 않을 수 있다.

## 한 번 보낸 메시지를 보존하는 정적 publisher

1. Stop한다. Tick → Publisher.execIn 연결을 제거한다. **On Stage Event**, **Countdown** 노드를 추가한다.
2. On Stage Event의 eventName을 **Simulation Start Play**로 둔다. `On Stage Event.execOut → Countdown.execIn`, `Countdown.tick → Publisher.execIn`으로 연결한다. Countdown duration=3, period=1이다. 공식 흐름은 초기 두 frame에서 generic publisher를 준비하고 세 번째 실행에 메시지를 발행한다.
3. ROS2 QoS Profile의 `createProfile`을 **Custom**으로 **먼저** 바꾼다. 그 뒤 history=keepLast, depth=1, reliability=reliable, durability=transientLocal, deadline=0.0, lifespan=0.0, liveliness=systemDefault, leaseDuration=0.0을 설정한다. custom을 먼저 선택해야 수정한 정책이 USD에 저장되지 않는 5.1 알려진 문제를 피한다.
4. 같은 값을 직접 문자열로 입력할 때에는 이 폴더의 `qos_profile.json` 내용을 publisher.qosProfile에 붙인다. QoS 노드 출력과 직접값 입력 중 하나만 사용한다. depth는 정수, 세 시간 필드는 소수점이 있는 실수이다.
5. 장면을 `output/qos_01.usd`처럼 새 이름으로 저장한다. Play하고 초기 카운트다운이 끝날 때까지 기다린다. 타임라인은 Play 상태로 유지해 publisher가 살아 있도록 한다.
6. 이제 두 터미널에서 각각 다음을 실행한다. 둘 다 `received_data='qos_lesson'`을 출력해야 한다.

   ```bash
   python3 listen.py --timeout 10
   ```

   ROS CLI로 확인하려면 수신 정책도 명시한다.

   ```bash
   ros2 topic echo /topic --qos-durability transient_local --qos-reliability reliable --once
   ```

7. 비교로 `python3 listen.py --volatile --timeout 3`을 **카운트다운 이후** 시작한다. 새 발행이 없다면 보존된 과거 메시지를 요청하지 않으므로 timeout이 예상된다. 이 실패는 실험의 관찰값이다. 타임아웃 오류를 숨기지 않는다.

## QoS/API 해설

History/Depth는 저장할 최근 샘플 수, Reliability는 재전송 보장 수준, Durability는 늦게 붙은 수신자에게 과거 샘플을 제공할지를 정한다. `transientLocal` 데이터는 살아 있는 publisher가 보존한다. 시뮬레이터를 닫아도 영구 파일처럼 남는 기능은 아니다. QoS 설정만으로 발행 횟수가 한 번으로 줄지는 않는다. Countdown 실행 연결과 durability 설정을 함께 사용한다.

USD Action Graph에는 정책 JSON 문자열 또는 정책 노드의 속성이 저장된다. ROS2 Publisher가 이를 실제 DDS QoS로 해석한다. `listen.py`의 `rclpy.create_subscription`에도 동일한 요청 정책을 주므로 늦게 시작한 수신 실험이 명확해진다. `time.monotonic()` 기반 제한은 `/clock` 없이도 timeout을 작동시키고 수신 메시지를 직접 출력한다.

## 하나만 바꾸기·문제 해결

publisher의 durability만 transientLocal에서 volatile로 바꾸고 새로 Play한 뒤 늦게 수신기를 붙인다. 과거 샘플이 사라지는지 비교한다. `ros2 topic info -v`에 depth가 UNKNOWN으로 보이는 것은 Fast DDS의 보고 특성일 수 있으므로 곧바로 잘못 저장되었다고 단정하지 않는다. Cyclone DDS 비교도 같은 RMW를 양쪽에 준비한 경우에만 한다.

문자열이 계속 오면 기존 Tick 연결이나 다른 `/topic` publisher를 확인한다. 한 번도 안 오면 Countdown의 출력 실행 포트, 세 번 초기 실행, String 상수 연결, 두 쪽 QoS 호환성을 확인한다. 단순 topic 목록보다 실제 두 늦은 subscriber의 수신 결과가 성공 기준이다.

## 출처와 검증 범위

- [공식 5.1 QoS 설정](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html#setting-qos-profile-for-ros-2-omnigraph-nodes)
- [공식 5.1 정적 발행](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_qos.html#creating-static-publishers)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
