# 127. ROS 2 Generic Server and Client

권장 학습 순서 **127** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t028`

**목표:** `std_srvs/srv/SetBool`의 request/response를 OmniGraph 포트로 다루고, 외부 CLI와 내부 Client 양쪽에서 실제 응답을 확인합니다. 로컬 그래프는 원문의 서버/클라이언트 구성을 재현합니다. 내부 Client는 실험 시점이 분명하도록 수동 impulse로 동작합니다.

## 이 실습의 의도

하나의 서비스 요청이 Request 노드에 도착하고 같은 `serverHandle`을 가진 Response 노드에서 응답하는 연결을 배우는 실습입니다. 외부 CLI와 그래프 내부 Client가 같은 `/service_name`을 호출해 요청 경로 두 가지를 비교합니다. 기본 서버는 bool에 따라 물체나 시뮬레이션 상태를 바꾸지 않고 항상 정해진 수락 응답을 반환합니다. `setup_stage.py` 실행은 그래프 준비까지이며, Play 후 외부 요청 또는 수동 impulse가 있어야 왕복 통신이 발생합니다.

## 실행 후 확인할 것

- **서버 응답:** Play 후 `data: true`를 CLI로 요청하면 `success=True`, `message='Accepted by Isaac Sim SetBool lab'`가 실제 응답으로 돌아오는지 확인합니다. 그래프 생성 로그만으로 서비스 수신을 확인할 수는 없습니다.
- **입력과 동작의 구분:** `data: false` 요청 후 Request의 `Request:data` 출력은 바뀌지만 기본 응답은 그대로인지 봅니다. 이는 bool 제어 기능을 구현하지 않은 이 실습의 의도된 구성입니다.
- **동적 응답 필드:** Response의 `Response:message`를 `second response`로 바꾸고 다시 요청하여 바뀐 문자열이 CLI 응답에 나타나는지 확인합니다.
- **내부 호출 시점:** `/ServiceLab/Impulse.state:enableImpulse=True`를 한 번 설정한 후 Client의 `Response:success`와 `Response:message`를 확인합니다. 기본 Client는 Play만으로 매 프레임 요청하지 않습니다.
- **거절과 통신 실패 구분:** Response의 success를 False로 바꿔도 그 응답을 받았다면 왕복 통신은 된 것입니다. 응답이 아예 오지 않는 경우에는 `serverHandle`·`onReceived` 연결과 Play 상태를 확인합니다.

## 실행 환경: 이 폴더만으로 시작하기

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, Linux, ROS 2 Humble(이 문서의 명령 기준)이 필요합니다. ROS를 통해 다른 프로세스와 통신하므로 시뮬레이터와 ROS 터미널을 구분합니다. `ISAAC_SIM`은 실제 설치 디렉터리로 바꾸세요.

**터미널 A — Isaac Sim**: ROS 시스템 환경을 source하지 않은 새 Bash에서 내부 Python 3.11용 브리지를 사용합니다. `.bashrc`가 `/opt/ros`를 자동 source한다면 해당 줄을 적용하지 않은 깨끗한 셸을 사용하세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

**터미널 B — ROS CLI**: 별도 Bash에서 시스템 ROS를 사용합니다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic list
```

Humble의 기본 Python 3.10 모듈을 Isaac Sim의 Python 3.11에 넣으면 ABI 오류가 납니다. Jazzy를 사용한다면 두 터미널의 배포판 이름과 내부 라이브러리 경로를 모두 `jazzy`로 바꿉니다. 같은 컴퓨터에서 먼저 실습하세요. 여러 컴퓨터는 DDS 네트워크/방화벽 설정도 일치해야 합니다. 다른 로컬 튜토리얼이나 공통 모듈은 필요하지 않습니다.

### 로컬 Script Editor 파일 실행

새 Stage에서 시작하고 Play를 정지합니다. **Window > Script Editor**에서 이 폴더의 `setup_stage.py`를 열어 Run을 누릅니다. 파일 열기 대신 아래 코드의 경로를 이 폴더의 절대 경로로 바꿔 실행해도 됩니다.

```python
from pathlib import Path
lesson = Path("/absolute/path/to/this/package")
exec(compile((lesson / "setup_stage.py").read_text(), str(lesson / "setup_stage.py"), "exec"))
```

이 코드는 이미 실행 중인 Kit 안에서 쓰는 코드입니다. 시스템 `python3 setup_stage.py`로 실행하지 않습니다. 재실행할 때는 **File > New**로 새 Stage를 열어 기존 실습 Stage와 구분하세요. 결과를 보존하려면 이 폴더 아래 새 이름의 USD로 **File > Save As**합니다.


## 실습 순서

1. 터미널 B에서 `ros2 interface show std_srvs/srv/SetBool`을 실행합니다. `---` 앞 `bool data`가 요청, 뒤의 `bool success`와 `string message`가 응답입니다. `ros2 interface list --only-srvs`로 사용 가능한 타입을 확인합니다.
2. `setup_stage.py` 실행 후 **Window > Graph Editors > Action Graph**에서 `/ServiceLab`을 엽니다. Request, Response, Client의 `messagePackage=std_srvs`, `messageSubfolder=srv`, `messageName=SetBool`이 모두 같은지 확인합니다.
3. Play 후 터미널 B에서 다음 요청을 보냅니다.

   ```bash
   ros2 service call /service_name std_srvs/srv/SetBool '{data: true}'
   ```

   `success=True`, `message='Accepted by Isaac Sim SetBool lab'`가 반환되어야 합니다. `data: false`도 보내 Request 출력이 바뀌는지 봅니다. 현재 응답은 입력과 관계없이 수락 메시지를 반환하는 실습용 서비스입니다.
4. Response의 `Response:message`를 `second response`로 변경하고 다시 CLI 요청합니다. 변경된 메시지가 응답으로 돌아오면 동적 응답 포트가 실제 사용된 것입니다.
5. 내부 Client 실험: Play 중 Script Editor에서 아래 명령을 한 번 실행합니다.

   ```python
   import omni.graph.core as og
   og.Controller.attribute('/ServiceLab/Impulse.state:enableImpulse').set(True)
   ```

   이후 Client 노드 Property의 `Response:success`와 `Response:message`를 봅니다. 매 프레임 보내려면 `Tick.outputs:tick`을 `Client.inputs:execIn`에 연결해 보되, 실험 종료 후 연결을 원래대로 돌립니다.

## 그래프/API 해설

Request의 `outputs:serverHandle`은 서버 객체를 식별하는 핸들입니다. Response의 `inputs:serverHandle`에 연결해야 같은 요청에 응답할 수 있습니다. Request의 `outputs:onReceived`는 **요청 도착 때만** 실행되며 Response의 `inputs:onReceived`를 트리거합니다. 이 선을 Tick으로 대체하면 요청/응답의 인과관계가 사라집니다.

타입 지정 후 생성되는 `outputs:Request:data`, `inputs:Response:success`, `inputs:Response:message`는 고정 포트와 다릅니다. `await next_update_async()`로 UI/동적 타입 구성이 반영된 후 값을 설정합니다. 설치 5.1 노드 ID는 `isaacsim.ros2.bridge.OgnROS2ServiceServerRequest`, `...OgnROS2ServiceServerResponse`, `...OgnROS2ServiceClient`입니다. UI 이름과 Python에서 등록된 ID를 구분하세요.

USD Stage 안의 `/ServiceLab`은 그래프를 저장할 장소입니다. ROS의 `/service_name`은 외부 통신 이름이며 동일할 필요가 없습니다. 토픽은 지속적인 데이터 스트림, 서비스는 특정 요청에 대한 단일 응답에 적합합니다.

## 한 가지 변수 실험과 문제 해결

Response의 `success`만 False로 바꿔 CLI 응답을 비교합니다. 이 값은 통신 실패와 다릅니다. 요청은 성공적으로 왕복했지만 서비스가 작업을 거절했다는 뜻입니다. `waiting for service`가 계속되면 Play/ROS_DOMAIN_ID/브리지를 확인합니다. Request는 보이지만 응답이 없으면 `serverHandle`, `onReceived` 두 연결과 세 노드 타입 일치를 확인합니다. 동적 포트가 안 보이면 타입을 지웠다가 Package→Subfolder→Name 순서로 다시 넣습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_server_client.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
