# 128. ROS에서 USD 속성을 읽고 바꾼 값 다시 확인하기

## 이번에 배우는 것

**ROS 서비스로 큐브의 USD 속성을 탐색하고 위치를 바꾼 다음, 다시 조회한 값으로 변경을 확인합니다.**

USD 장면의 물체는 prim 경로로 찾고, 물체의 값은 attribute 이름으로 찾습니다. 이번에는 `/World/Cube`라는 대상과 `xformOp:translate`라는 속성을 ROS 요청에 넣어 큐브를 옮깁니다.

| 구성 | 실행 장소 | 역할 |
|---|---|---|
| `setup_stage.py` | Isaac Sim Script Editor | 파란 큐브와 `/PrimServices` 생성 |
| `ROS2ServicePrim` | Play 중 Action Graph | prim·속성 조회 및 기존 값 변경 |
| `attribute_client.py` | 시스템 ROS Python | 위치 읽기 → 쓰기 → 재조회 |
| `isaac_ros2_messages` | 양쪽 ROS 환경 | 같은 서비스 요청·응답 타입 정의 |

큐브에는 강체가 없습니다. 바뀌는 것은 USD 변환 속성이며, 힘이나 속도를 적용하여 움직이는 실습은 아닙니다.

## 1. 서비스 그래프와 메시지 패키지 준비하기

**Ubuntu 24.04, ROS 2 Jazzy, Isaac Sim 5.1.0**과 지원 GPU가 필요합니다. 먼저 저장소 루트의 ROS용 Bash에서 외부 서비스 정의를 빌드합니다. `rosdep`, `colcon`은 설치·초기화된 상태여야 합니다.

ROS desktop 설치는 [Jazzy 공식 설치 안내](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따르세요. 아래 개발 도구가 없는 환경에서는 먼저 준비합니다. rosdep을 처음 쓰는 컴퓨터에서만 `sudo rosdep init`을 한 번 실행하고, 이후에는 `rosdep update`로 목록을 갱신하세요.

```bash
sudo apt install python3-rosdep python3-colcon-common-extensions build-essential git
rosdep update
```

```bash
export LESSON_DIR="$PWD/src/128_ros2_ros2_prim_service"
source /opt/ros/jazzy/setup.bash
export ROS_WS_REPO="$HOME/IsaacSim-ros_workspaces-5.1.0"
git clone --branch IsaacSim-5.1.0 --recurse-submodules https://github.com/isaac-sim/IsaacSim-ros_workspaces.git "$ROS_WS_REPO"
cd "$ROS_WS_REPO/jazzy_ws"
rosdep install --from-paths src/isaac_ros2_messages --ignore-src --rosdistro jazzy -y
colcon build --packages-select isaac_ros2_messages
source install/local_setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 interface show isaac_ros2_messages/srv/SetPrimAttribute
```

같은 5.1.0 워크스페이스를 이미 준비했다면 clone과 빌드를 반복하지 않습니다. 시뮬레이터 내부 브리지는 이 서비스 타입을 포함하지만, 외부 CLI/Python에도 같은 정의가 있어야 요청을 만들 수 있습니다.

**시스템 ROS를 source하지 않은 새 Bash**에서 내부 Python 3.11용 브리지로 앱을 시작합니다. 앞에서 빌드한 시스템 ROS용 Python 환경을 이쪽에 섞지 않습니다.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/isaac-sim.sh" --enable isaacsim.ros2.bridge
```

1. **File > New**로 새 Stage를 열고 Stop 상태로 둡니다.
2. **Window > Script Editor**에서 이 폴더의 `setup_stage.py` 전체를 실행합니다.
3. `/World/Cube`를 선택하고 **F**로 프레이밍한 뒤 Play합니다.

### 실행 결과 확인하기

초기 Cube는 한 변이 0.5 m이고 중심 위치는 `(0,0,0.25)` m입니다. ROS용 터미널에서 대상을 탐색하세요.

```bash
ros2 service call /get_prims isaac_ros2_messages/srv/GetPrims '{path: /World}'
ros2 service call /get_prim_attributes isaac_ros2_messages/srv/GetPrimAttributes '{path: /World/Cube}'
ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute '{path: /World/Cube, attribute: "xformOp:translate"}'
```

첫 조회에서는 대상 경로, 다음 조회에서는 속성 이름, 마지막 조회에서는 위치값을 확인합니다. 응답의 `success`와 `message`도 읽으세요. 서비스 이름이 목록에 있는 것만으로 조회 성공을 판단하지 않습니다.

## 2. 위치를 쓰고 Python으로 재조회하기

다음 요청의 `value`는 **JSON 배열을 담은 문자열**입니다.

```bash
ros2 service call /set_prim_attribute isaac_ros2_messages/srv/SetPrimAttribute '{path: /World/Cube, attribute: "xformOp:translate", value: "[1, 2, 3]"}'
```

안쪽 따옴표를 없애면 ROS CLI가 문자열 대신 YAML 배열로 해석할 수 있습니다. 요청 뒤 큐브가 이동했는지 보고 `/get_prim_attribute`를 다시 호출하세요.

같은 확인을 자동으로 수행하는 로컬 클라이언트도 실행해 봅니다. `LESSON_DIR`를 설정한 ROS 터미널을 사용하세요.

```bash
python3 "$LESSON_DIR/attribute_client.py" --position 0 0 1
```

### 코드에서 볼 부분

클라이언트는 입력 숫자를 직접 이어 붙이지 않고 `json.dumps`로 직렬화합니다.

```python
SetPrimAttribute.Request(
    path='/World/Cube', attribute='xformOp:translate',
    value=json.dumps(args.position))
```

응답을 기다리는 동안 `rclpy.spin_until_future_complete`가 ROS 콜백을 처리합니다. 쓰기 응답이 성공하면 같은 속성을 다시 읽고 문자열을 숫자 배열로 복원합니다.

```python
actual = json.loads(after.value)
if len(actual) != 3 or any(abs(a-b)>1e-6 for a,b in zip(actual,args.position)):
    raise RuntimeError(f'Read-back differs: wanted {args.position}, received {actual}')
```

따라서 `verified translation:`은 보낸 인자를 그대로 출력한 문구가 아니라 **서비스에서 다시 읽은 값의 비교 결과**입니다.

장면 코드는 `AddTranslateOp()`와 `AddOrientOp()`로 속성을 실제 생성합니다. 서비스는 기존 속성을 바꾸므로 없는 이름을 임의로 써서 새 transform 연산을 만들 수는 없습니다. 방향을 다룰 때 `xformOp:orient`의 USD quaternion 순서는 `[w,x,y,z]`이며, ROS Pose 필드 나열 순서와 구분해야 합니다.

### 실행 결과 확인하기

터미널의 `before:`에는 직전에 읽은 위치가, `verified translation:`에는 `[0.0, 0.0, 1.0]`이 나타나야 합니다. 기본 옵션 없이 실행하면 목표는 `[1,2,3]`입니다. Cube는 지정한 위치에서 그대로 유지됩니다. 별도 CSV를 만들지 않고 클라이언트만 종료하며 앱과 Cube는 남습니다.


### 방향 속성도 읽고 쓰기

로컬 setup은 `xformOp:orient`도 만들어 둡니다. ROS 터미널에서 먼저 현재 값을 읽고 항등 회전을 써보세요.

```bash
ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute \
  '{path: /World/Cube, attribute: "xformOp:orient"}'
ros2 service call /set_prim_attribute isaac_ros2_messages/srv/SetPrimAttribute \
  '{path: /World/Cube, attribute: "xformOp:orient", value: "[1, 0, 0, 0]"}'
ros2 service call /get_prim_attribute isaac_ros2_messages/srv/GetPrimAttribute \
  '{path: /World/Cube, attribute: "xformOp:orient"}'
```

이 서비스는 원시 USD quaternion을 JSON 문자열로 전달하므로 **실수부가 먼저인 `[w,x,y,z]`**입니다. `geometry_msgs/Pose`의 필드 이름을 그대로 배열 순서로 사용하지 마세요. 이미 항등 회전이었다면 화면이 그대로일 수 있으며 반환값과 Property의 orient를 확인합니다. GUI로 별도 만든 Cube에 이 속성이 없다면 해당 조회는 실패할 수 있습니다. `SetPrimAttribute`는 새 회전 연산을 추가하는 서비스가 아닙니다.

## 3. prim 경로·속성 이름·좌표계 정리

```text
/World/Cube                 → 어떤 물체인가?
xformOp:translate           → 그 물체의 어떤 값인가?
"[0, 0, 1]"                 → 어떤 문자열 형식으로 보낼 것인가?
GetPrimAttribute 재조회     → 실제 적용된 값은 무엇인가?
```

`xformOp:translate`는 **로컬 변환**입니다. 이번에는 부모 `/World`에 추가 변환이 없어 world 위치와도 일치합니다. 부모를 움직이면 같은 `[0,0,1]`을 써도 world 위치는 달라질 수 있습니다. 121번의 world pose 서비스와 원시 USD 속성 편집이 만나는 경계입니다.

## 4. 간단한 확인 실험

앞의 명령에서 **Z만 1에서 2**로 바꾸어 실행해 보세요.

```bash
python3 "$LESSON_DIR/attribute_client.py" --position 0 0 2
```

`before:`는 이전 위치를, `verified translation:`은 `[0.0,0.0,2.0]`을 보여야 합니다. Cube가 1 m 높아지는지 확인하세요. 속도나 이동 시간은 설정하지 않았으므로 이 값은 위치 변경량입니다.

## 실행할 때 막히면

- **`No module named isaac_ros2_messages`**: 클라이언트 터미널에 메시지 워크스페이스의 설치 결과를 source하세요.
- **서비스 대기 또는 응답 시간 초과**: Play 상태를 확인하세요. `/PrimServices`는 Tick으로 처리되며, Pause 중에도 응답하는 sim_control 확장과 동작 조건이 다릅니다.
- **`success: false`**: `message`에서 없는 prim인지 없는 속성인지 확인하세요. Display Name 대신 실제 USD 이름을 사용합니다.
- **`value` 타입 오류**: 숫자 배열을 JSON 문자열로 감싼 따옴표를 확인하세요.
- **setup 재실행 오류**: `/PrimServices`나 `/World/Cube`가 이미 있으면 새 Stage에서 시작하세요.

Ubuntu 22.04/Humble에서는 양쪽 배포판과 워크스페이스 경로를 `humble`로 변경합니다. 마치면 Isaac Sim 창을 닫습니다.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [ROS 2 Service for Manipulating Prims Attributes](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_prim_service.html)에 대응합니다. [ROS 설치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)와 [공식 ROS 워크스페이스](https://github.com/isaac-sim/IsaacSim-ros_workspaces/tree/50de00358f220d790d17050c6368cfe9a9cb9f51)를 참고하세요.

로컬 파일은 서비스용 장면과 위치 재조회 클라이언트를 제공합니다. 외부 메시지 패키지는 별도 빌드하며, 실제 ROS 왕복과 GUI 이동은 이 개정에서 실행하지 않았습니다. `tutorial.json`은 `verification: not_run`입니다.
