# 107. ROS 2로 실제 Real Time Factor 발행하기

권장 학습 순서 **107** · ROS 2 연결과 기본 통신 · 출처 ID `t010`

예상 결과는 `/topic`의 Float32 값이 시뮬레이션의 실측 시간 비율을 나타내는 것이다. 공식 Generic Publisher 메뉴가 만드는 그래프를 `run.py`가 구성한다. 상수 1.0을 발행하는 예제가 아니다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 물리와 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 명시하면 해당 스텝 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1200스텝으로 종료하며, `--steps 0`과 음수는 허용하지 않습니다.

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

## 실행과 관찰

1. 터미널 A에서 실행한다.

   ```bash
   "$ISAAC_SIM/python.sh" run.py
   ```

2. 터미널 B에서 자료형과 값을 확인한다.

   ```bash
   ros2 topic type /topic
   ros2 topic echo /topic
   ```

   자료형은 `std_msgs/msg/Float32`이고 메시지의 `data`가 RTF다. A 터미널의 `measured_rtf`도 동일 측정 노드에서 읽는다. 기기·화면·초기 로딩에 따라 1.0보다 작거나 클 수 있으며 1.0 일치를 성공 조건으로 삼지 않는다.
3. 첫 프로세스를 종료하고 `"$ISAAC_SIM/python.sh" run.py --delay 0.04`을 실행한다. 추가 대기 시간은 실제 경과 시간만 늘리므로 안정화 후 평균 RTF가 낮아지는지 비교한다.

## 메뉴로 같은 발행기 만들기

1. 새 Stage에서 **Tools > Robotics > ROS 2 OmniGraphs > Generic Publisher**를 연다.
2. **Publish RTF as Float32**를 고르고 OK를 누른다.
3. `/Graph/ROS_GenericPub`를 오른쪽 클릭하여 **Open Graph**를 연다. **Isaac Real Time Factor**의 `rtf` 출력이 **ROS2 Publisher**의 `data`에 연결되는지 확인한다.
4. Publisher에서 `messagePackage=std_msgs`, `messageSubfolder=msg`, `messageName=Float32`, `topicName=/topic`을 확인한다. Context 출력은 Publisher의 context, Tick 출력은 execIn에 연결한다.
5. Play 후 `/topic`을 확인한다. GUI에서 소품을 추가해 부하를 바꾸려면 먼저 새 이름으로 장면을 저장한다.

## API와 시간 개념

RTF는 `시뮬레이션에서 흐른 초 / 실제 경과 초`다. 0.5이면 시뮬레이션 1초를 계산하는 데 실제 약 2초가 걸린다. `IsaacRealTimeFactor.outputs:rtf`가 이를 측정한다. 프레임 수 자체와는 다르다. 물리 dt가 1/60초일 때 FPS와 관련이 생기지만 FPS라는 단위를 RTF에 붙이지 않는다.

`ROS2Publisher`는 지정한 ROS 메시지 스키마에 맞추어 `inputs:data` 같은 속성을 동적으로 만든다. 따라서 코드에서는 메시지 이름을 설정하고 앱 업데이트를 거친 뒤 `og.Controller.connect`로 RTF를 연결한다. `World`는 1/60초 물리 간격을 설정하고, `--delay`는 `time.sleep`으로 각 프레임 뒤의 실제 시간을 늘리는 실험 변수다.

## 문제 해결과 성공 기준

`ros2 topic type /topic`이 다르면 이전 실습의 발행기를 종료한다. `inputs:data`가 없다는 오류는 메시지 이름·패키지 철자와 Bridge 로딩을 확인한다. 첫 프레임의 0이나 일시적 큰 값은 안정화 이후 값과 구분한다. Float32 메시지가 실제 도착하고 부하 변화에 따른 측정 변화가 관찰되면 성공이다.

## 출처와 검증 범위

- [공식 5.1 RTF 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_rtf.html#publish-rtf)

공식 절차를 바탕으로 이 패키지의 설명과 보조 코드를 독립적으로 작성했다. `tutorial.json`의 `verification: not_run`은 GPU·GUI·외부 ROS 통신의 통합 실행을 아직 확인하지 않았다는 뜻이다. 아래 성공 기준을 실제 환경에서 관찰해야 완료한 것이다.
