# 127. 하나의 서비스 요청에 하나의 응답 연결하기

## 이번에 배우는 것

**SetBool 서비스를 그래프로 만들고, 외부 ROS 명령과 내부 Client가 같은 서버의 응답을 받는 과정을 비교합니다.**

토픽은 계속 흐르는 데이터를 전달할 때 편리합니다. 서비스는 “이 요청을 처리했나요?”처럼 한 번의 요청에 대응하는 답을 받고 싶을 때 사용합니다. 이번 그래프는 `bool data`를 받고 성공 여부와 문자열을 돌려줍니다.

| 노드 | 역할 | 중요 연결 |
|---|---|---|
| Request | `/service_name`의 요청 수신 | `serverHandle`, `onReceived` 출력 |
| Response | 받은 요청에 응답 | 같은 핸들과 도착 신호 입력 |
| Client | 그래프 안에서 요청 전송 | 수동 Impulse로 한 번 실행 |
| Tick | Play 중 서버 처리 | Request 실행 입력 |

기본 응답은 입력 bool과 관계없이 고정입니다. 이 실습은 요청·응답 연결을 배우며, bool에 따라 물체나 시뮬레이션 상태를 바꾸는 제어 기능은 구현하지 않습니다.

## 1. 서버를 만들고 외부에서 요청하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0** 및 지원 GPU가 필요합니다. Bash 터미널을 두 개 사용합니다.

시스템 ROS를 source하지 않은 **터미널 A**에서 시뮬레이터용 내부 라이브러리를 설정합니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

**File > New**로 Stop 상태의 빈 Stage를 열고 **Window > Script Editor**에서 이 폴더의 `setup_stage.py` 전체를 실행하세요. `Press Play.` 출력이 나오면 `/ServiceLab` 그래프가 만들어진 상태입니다. Play를 누릅니다.

**터미널 B**에서 요청 타입과 실제 응답을 확인합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 interface show std_srvs/srv/SetBool
ros2 service call /service_name std_srvs/srv/SetBool '{data: true}'
```

인터페이스 출력의 `---` 앞 `bool data`가 요청이고, 뒤의 `bool success`, `string message`가 응답입니다.

### 실행 결과 확인하기

응답에 `success=True`와 `message='Accepted by Isaac Sim SetBool lab'`가 오는지 확인하세요. 서비스 호출 명령은 응답을 받은 뒤 끝나고 Isaac Sim 창은 남습니다. Cube나 출력 파일은 만들지 않습니다.

`data: false`로도 요청해 보세요. 응답이 여전히 같다면 현재 구성에 맞는 동작입니다. Request의 bool 값을 읽어 동작을 분기하는 노드가 연결되어 있지 않기 때문입니다.

## 2. 같은 서버를 그래프 안에서 호출하기

**Window > Graph Editors > Action Graph**에서 `/ServiceLab`을 엽니다. Play 중 Script Editor에서 다음을 한 번 실행하세요.

```python
import omni.graph.core as og
og.Controller.attribute('/ServiceLab/Impulse.state:enableImpulse').set(True)
```

Client 노드의 `Request:data` 기본값은 True입니다. 요청이 끝나면 Property의 `Response:success`, `Response:message`에서 외부 CLI와 같은 응답을 확인합니다. 다시 요청할 때는 Impulse를 한 번 더 보냅니다. Play만으로 Client가 매 프레임 요청하지는 않습니다.

### 코드에서 볼 부분

세 서비스 노드는 모두 타입을 `std_srvs / srv / SetBool`로 설정합니다. 타입 지정 후 동적 포트가 만들어지도록 앱 업데이트를 기다리고 응답을 채웁니다.

```python
await omni.kit.app.get_app().next_update_async()
og.Controller.attribute('/ServiceLab/Response.inputs:Response:success').set(True)
og.Controller.attribute('/ServiceLab/Response.inputs:Response:message').set(
    'Accepted by Isaac Sim SetBool lab')
```

서비스의 연결에서 가장 중요한 것은 다음 두 선입니다.

```text
Request.serverHandle ─────────→ Response.serverHandle
Request.onReceived ───────────→ Response.onReceived
```

`serverHandle`은 어느 서버의 요청에 응답할지 나타내는 핸들입니다. `onReceived`는 요청을 받았을 때 응답 동작을 시작하는 실행 신호입니다. 값만 연결하거나 매 Tick에 응답하도록 바꾸면 원래 의도한 요청·응답 관계가 깨집니다.

외부 CLI와 내부 Client의 시작 위치는 다르지만 결국 같은 Request → Response 경로를 통과합니다. `/ServiceLab`은 USD 안의 그래프 경로이고 `/service_name`은 ROS 통신 이름이므로 두 문자열은 같을 필요가 없습니다.

### 실행 결과 확인하기

Response의 `Response:message`를 `second response`로 바꾸고 외부 CLI를 다시 호출한 다음 내부 Impulse도 보내 보세요. 두 곳 모두 새 문자열을 받는지 확인합니다. Property에 이전 값이 남아 있다는 사실만으로 새 요청이 처리됐다고 판단하지 말고, 이렇게 구분되는 응답으로 확인할 수 있습니다.

## 3. 토픽과 서비스, 두 클라이언트의 차이 정리

```text
외부 CLI ───────────┐
                  ├─ /service_name → Request → Response → 요청한 클라이언트
내부 Impulse→Client┘
```

**응답의 `success`와 통신의 성공은 서로 다른 정보입니다.** `success=False` 응답을 받았다면 서버까지 요청이 도착하고 답도 돌아온 것입니다. 다만 서버가 표현하는 작업 결과가 실패 또는 거절이라는 뜻입니다. 응답을 전혀 받지 못하는 시간 초과와 구분해서 읽으세요.

## 4. 간단한 확인 실험

Response 노드의 **`Response:success`만 False**로 바꾸고 같은 `data: true` 요청을 보내 보세요. 문자열과 다른 연결은 유지합니다.

CLI와 내부 Client에 success=False가 돌아와야 합니다. 이번 그래프에는 실제 작업이 없으므로 이 값은 직접 설정한 응답 값입니다. 나중에 작업을 추가한다면 그 작업의 결과를 이 포트에 연결하면 됩니다.

## 실행할 때 막히면

- **`waiting for service`가 계속됨**: Play, 브리지 활성화, 두 터미널 Domain ID를 확인하세요.
- **요청은 보이는데 응답이 없음**: `serverHandle`과 `onReceived` 두 연결을 확인하세요. Response의 타입도 SetBool이어야 합니다.
- **내부 Client 값이 안 바뀜**: Impulse를 보냈는지 확인하세요. 외부 요청의 응답이 내부 Client 출력에 자동 복사되는 구조는 아닙니다.
- **동적 포트가 없음**: Package=`std_srvs`, Subfolder=`srv`, Name=`SetBool` 순으로 확인하고 앱 업데이트를 기다리세요.
- **`Use a new stage` 오류**: `/ServiceLab`이 이미 있습니다. 새 Stage에서 setup을 한 번 실행합니다.

Ubuntu 22.04/Humble에서는 위 환경의 `jazzy`를 `humble`로 맞춥니다. 실습을 마치면 앱을 닫아 서버를 종료하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Generic Server and Client](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_server_client.html)에 대응합니다. [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 함께 참고하세요.

로컬 그래프는 서버와 Client를 함께 만들며 내부 요청 시점을 수동 Impulse로 지정합니다. `setup_stage.py`와 포트 설정을 대조했지만 GUI 활성화와 서비스 왕복은 이 개정에서 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
