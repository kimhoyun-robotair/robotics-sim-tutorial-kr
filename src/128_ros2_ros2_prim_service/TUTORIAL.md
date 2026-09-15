# 128. ROS 2 Service for Manipulating Prims Attributes

권장 학습 순서 **128** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t029`

**목표:** ROS 서비스로 USD prim과 attribute를 탐색하고 Cube의 위치를 실제로 읽기→쓰기→다시 읽기로 확인합니다. `setup_stage.py`는 원문의 ROS2 Service Prim 그래프를 만들고, `attribute_client.py`는 별도 ROS 프로세스에서 왕복 검증합니다.

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


## 준비할 메시지 패키지

시뮬레이터 내부 브리지는 `isaac_ros2_messages` 서비스를 이미 포함합니다. 터미널 B에는 동일한 정의가 필요합니다. [NVIDIA IsaacSim-ros_workspaces](https://github.com/isaac-sim/IsaacSim-ros_workspaces)의 `5.1.0` 버전을 별도 디렉터리에 준비합니다.

```bash
# 터미널 B; 기존 작업공간이 있으면 새로 clone하지 않고 해당 5.1.0 checkout을 사용
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/humble_ws"
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select isaac_ros2_messages
source install/local_setup.bash
ros2 interface show isaac_ros2_messages/srv/SetPrimAttribute
```

이것은 외부 메시지 정의의 빌드입니다. 이 패키지의 로컬 코드는 `attribute_client.py`이며 외부 workspace 구현을 포함했다고 주장하지 않습니다. 시스템 ROS용 빌드를 시뮬레이터 터미널 A에 source하지 않습니다.

## 실습 순서

1. `setup_stage.py` 실행 후 `/World/Cube`를 선택하고 F로 프레이밍합니다. **Window > Graph Editors > Action Graph**에서 `/PrimServices`를 엽니다. Tick→Prims `execIn`, Context→Prims `context` 연결을 확인하고 Play합니다.
2. 터미널 B에서 네 가지 인터페이스를 탐색합니다.

   ```bash
   ros2 service list
   ros2 service call /get_prims isaac_ros2_messages/srv/GetPrims '{path: /World}'
   ros2 service call /get_prim_attributes isaac_ros2_messages/srv/GetPrimAttributes '{path: /World/Cube}'
   ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute '{path: /World/Cube, attribute: "xformOp:translate"}'
   ```

3. 위치 쓰기의 `value`는 **JSON을 담는 문자열**입니다. CLI YAML이 숫자 배열로 해석하지 않도록 내부 따옴표를 유지합니다.

   ```bash
   ros2 service call /set_prim_attribute isaac_ros2_messages/srv/SetPrimAttribute '{path: /World/Cube, attribute: "xformOp:translate", value: "[1, 2, 3]"}'
   ```

4. 이 패키지 폴더로 돌아와 `python3 attribute_client.py --position 0 0 1`을 실행합니다. 실제 응답의 `success`를 확인하고 다시 읽은 값이 `[0,0,1]`인지 검증합니다. 화면에서도 Cube가 이동합니다.
5. 방향도 같은 방법으로 `xformOp:orient`를 조회합니다. USD quaternion의 직렬화 순서는 `[w,x,y,z]`입니다. 항등 방향을 쓰려면 `value: "[1,0,0,0]"`를 사용합니다.

## API와 USD 이해

Prim은 Stage의 객체(`/World/Cube`)이고 attribute는 그 객체의 값(`xformOp:translate`)입니다. `GetPrims`는 자식 경로와 타입, `GetPrimAttributes`는 attribute 이름과 타입, `GetPrimAttribute`는 값과 타입을 반환합니다. `SetPrimAttribute`는 **이미 존재하는 attribute의 값**을 바꿉니다. 사용자에게 보이는 Display Name 대신 실제 USD attribute 이름을 사용합니다.

`UsdGeom.Cube`는 형상 스키마, `AddTranslateOp`/`AddOrientOp`는 변환 스택을 만듭니다. 원문의 GUI Cube가 Euler 회전만 가진 경우 `xformOp:orient`가 없을 수 있어 로컬 코드는 이를 명시적으로 생성합니다. Stage의 meter 단위와 ROS 위치 단위를 맞춥니다. 이 실습은 동적 강체 제어가 아닌 USD 변환 값 편집입니다.

`rclpy.create_client`는 원격 서비스 연결, `call_async`는 요청 발송, `spin_until_future_complete`는 응답 처리를 담당합니다. 그래프 서비스는 Play 중 Tick을 받아야 처리되므로 Stop 상태에서는 서비스가 보이더라도 요청이 완료되지 않을 수 있습니다.

## 한 가지 변수 실험과 문제 해결

`--position`의 Z만 1에서 2로 바꿔 새 read-back과 화면을 비교하세요. 다른 Cube 이름을 사용했다면 클라이언트 경로도 일치해야 합니다. `ModuleNotFoundError: isaac_ros2_messages`는 터미널 B workspace source 누락, 서비스 대기 시간 초과는 Play/Domain ID/브리지 상태를 먼저 확인합니다. `success: false`의 `message`를 버리지 말고 없는 prim/attribute인지 읽어 보세요.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_prim_service.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
