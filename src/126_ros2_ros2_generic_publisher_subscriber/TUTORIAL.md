# 126. ROS 2 Generic Publisher and Subscriber

권장 학습 순서 **126** · ROS 2 응용과 사용자 인터페이스 · 출처 ID `t027`

**목표:** 타입을 지정하면 포트가 자동으로 생기는 Generic Publisher/Subscriber를 익힙니다. 로컬 그래프는 Cube의 **위치와 방향**을 `/object_pose`로 받아 적용하고 실제 pose를 `/object_pose_observed`로 발행합니다. 아래에는 방향을 표현하는 포트와 원문의 JointState 실습도 포함합니다.

## 이 실습의 의도

`geometry_msgs/msg/Pose`의 중첩 필드가 Generic 노드의 동적 포트로 펼쳐지고 USD transform과 왕복하는 과정을 배우는 실습입니다. 명령 토픽과 관측 토픽을 분리해, 수신한 값을 적용한 뒤 실제 Cube 속성을 읽어 보내는 경로를 확인합니다. 기본 Cube에는 강체가 없어 중력으로 떨어지지 않으며 ROS 명령으로 위치와 방향을 직접 바꿉니다. `setup_stage.py`는 이미 실행 중인 Kit에 장면·그래프만 만들고, Play와 외부 ROS 명령 전송은 사용자가 수행합니다.

## 실행 후 확인할 것

- **타입과 초기 상태:** `/GenericPose`의 Pub/Sub에 `geometry_msgs / msg / Pose`와 `position:x/y/z`, `orientation:x/y/z/w` 포트가 생성되는지 봅니다. 처음 `/World/Cube`의 위치는 `(0,0,0.5)`, 회전은 항등이며 정지 상태를 유지합니다.
- **위치 왕복:** Play 후 `/object_pose`에 `(1,2,3)`과 `orientation.w=1`을 보내고 Cube의 Translate와 `/object_pose_observed`의 위치가 모두 갱신되는지 확인합니다. 실행 순서 때문에 관측값은 다음 프레임에 반영될 수 있습니다.
- **방향 왕복:** Z축 90° 명령의 ROS quaternion `(x,y,z,w)=(0,0,0.70710678,0.70710678)`이 관측 토픽과 USD `xformOp:orient`에 맞게 반영되는지 봅니다. 정육면체는 90° 회전 전후 외형이 같을 수 있으므로 화면 모양만으로 회전을 판단하지 않습니다.
- **수치 순서:** 방향 연결에서 ROS의 `w,x,y,z`가 Make/Break 4-Vector의 X/Y/Z/W 슬롯에 대응하는지 확인합니다. 모든 quaternion 성분이 0인 명령은 항등 회전이 아니므로 `w`를 생략하지 않습니다.
- **확장 실습 구분:** 낙하 관측은 강체를 추가하고 Write 경로를 제거한 별도 장면, JointState 발행은 Franka와 새 그래프를 준비한 별도 장면에서 확인합니다. 기본 Pose 왕복만 실행해서는 이 두 동작이 나타나지 않습니다.

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


## 위치 메시지 왕복

1. `setup_stage.py`를 실행하고 `/World/Cube`를 선택한 뒤 F를 누릅니다. `/GenericPose` Action Graph에서 Pub/Sub의 메시지 세 필드가 `geometry_msgs / msg / Pose`인지 봅니다. 원문의 일부 본문에 `msgs` 표기가 있지만 실제 ROS 패키지 하위 디렉터리는 **msg**입니다.
2. Play 후 터미널 B에서 실행합니다.

   ```bash
   ros2 topic echo /object_pose_observed
   # 다른 ROS 터미널
   ros2 topic pub --once /object_pose geometry_msgs/msg/Pose '{position: {x: 1.0, y: 2.0, z: 3.0}, orientation: {w: 1.0}}'
   ```

3. Cube가 `(1,2,3)`으로 이동하고 관측 토픽에도 그 위치가 나타나야 합니다. 발행/명령을 다른 토픽으로 구분한 것은 한 토픽의 두 publisher가 값을 경쟁하는 일을 피하려는 로컬 구성입니다. 방향의 `(x,y,z,w)=(0,0,0,1)`은 항등 회전입니다. 메시지에 `orientation.w`를 생략하면 유효하지 않은 전부 0 quaternion이 되므로 명시합니다.

## 원문의 전체 Pose 포트 살펴보기

로컬 스크립트가 이미 만든 방향 연결을 Stop 상태에서 아래 순서로 추적합니다. GUI에서 직접 재구성하려면 새 그래프에서 같은 노드를 추가합니다.

1. Subscriber의 `orientation:w/x/y/z` 출력을 **Make 4-Vector**의 X/Y/Z/W에 순서대로 연결합니다. OG quaternion은 `[real, i, j, k]`, 즉 `[w,x,y,z]`로 저장됩니다. Make 4-Vector의 X/Y/Z/W는 단순한 네 배열 슬롯의 이름이며 ROS quaternion 필드 이름과 그대로 대응하지 않습니다. 이 결과를 **To Float**의 Value에 연결하고 Role을 **Quaternion**으로 설정합니다. Quaternion role을 가진 출력이 물리적인 quaternion으로 해석됩니다.
2. **Write Prim Attribute**를 하나 더 만들고 Prim=`/World/Cube`, Attribute Name=`xformOp:orient`로 설정합니다. 변환한 quaternion을 Value로, Subscriber Exec Out을 Exec In으로 연결합니다. USD `quatf`가 요구되므로 To Float를 사용합니다.
3. 발행 쪽에도 **Read Prim Attribute**를 만들고 같은 Prim/Attribute를 읽습니다. 출력 quaternion을 **Break 4-Vector**로 나누어 X→ROS `orientation:w`, Y→`orientation:x`, Z→`orientation:y`, W→`orientation:z`로 연결합니다. OG quaternion과 USD Python `Gf.Quatf(real, imaginary)` 모두 실수부를 먼저 둡니다. 결과가 의도와 다르면 항등 `(x,y,z,w)=(0,0,0,1)`부터 확인하고 Z축 90°를 `(0,0,0.70710678,0.70710678)`로 확인합니다.
4. Publisher는 ReadOrientation에서 읽은 실제 quaternion을 발행합니다. Play 후 아래 명령으로 화면 회전과 관측 토픽을 비교합니다.

   ```bash
   ros2 topic pub --once /object_pose geometry_msgs/msg/Pose '{position: {x: 1, y: 2, z: 3}, orientation: {x: 0, y: 0, z: 0.70710678, w: 0.70710678}}'
   ```

원문의 낙하 물체 발행 실험은 새 Stage에서 Cube에 **Add > Physics > Rigid Body with Colliders Preset**을 적용하고 Translate Z를 2 m로 올린 뒤, 구독/Write 그래프를 제거하고 Read→Publisher만 남겨 실행합니다. 수신 명령으로 teleport하는 실험과 강체 시뮬레이션을 동시에 섞지 않습니다. 낙하 시 Z가 감소하는지 관측하고 바닥을 추가하면 충돌 후 높이가 안정되는지 확인합니다.

## 원문의 Generic JointState 발행

1. 새 Stage에서 **Window > Examples > Robotics Examples > Import Robots > Franka URDF**를 열고 LOAD→CONFIGURE를 누릅니다. 이는 설치된 5.1 공식 예제이며 Franka URDF/mesh asset이 필요합니다.
2. 새 Action Graph에 On Playback Tick, Isaac Read Simulation Time, Isaac Time Splitter, Articulation State, ROS2 Context, ROS2 Publisher를 추가합니다. Articulation State targetPrim=`/panda`, Publisher=`sensor_msgs / msg / JointState`, topicName=`joint_states`로 설정합니다.
3. Tick을 Articulation State와 Publisher의 Exec In으로 연결합니다. Time의 simulationTime→Time Splitter time, Splitter의 seconds/nanoseconds→Publisher의 header stamp sec/nanosec로 연결합니다. Context→Publisher context도 연결합니다.
4. Articulation State의 jointNames→Publisher name, jointPositions→position, jointVelocities→velocity, measuredJointEfforts→effort를 연결합니다. 각 배열의 길이/순서를 동일하게 유지합니다. 실제 UI에서 effort 출력의 측정 항목명을 확인하고 commanded effort와 혼동하지 않습니다.
5. Play 후 Franka 예제 MOVE를 누르고 `ros2 topic echo /joint_states`에서 이름 배열과 위치 변화를 봅니다. `resetOnStop`을 켜면 시간이 0으로 돌아가므로 외부 소비자가 시간 역행을 처리할 수 있어야 합니다.

## 메시지/API 개념

`ROS2Publisher`는 `messagePackage`, `messageSubfolder`, `messageName` 세 값으로 타입 지원을 찾습니다. 중첩 메시지는 `position:x`처럼 개별 포트로 펼쳐집니다. 중첩 메시지 **배열**은 각 요소를 JSON 문자열로 표현하는 token array가 됩니다. `ros2 interface show geometry_msgs/msg/Pose`와 `ros2 interface show sensor_msgs/msg/JointState`로 실제 타입을 먼저 봅니다.

Read/Write Prim Attribute는 USD 값과 그래프를 연결합니다. Break/Make 3-Vector는 USD의 벡터를 ROS 메시지의 세 scalar로 나눠/합칩니다. 실행 선은 언제 처리할지를, 데이터 선은 어떤 값을 쓸지를 결정합니다. 한 프레임의 처리 순서 때문에 관측 발행은 적용 직후 프레임에서 갱신될 수 있습니다.

## 한 가지 변수 실험과 문제 해결

명령의 Z만 3에서 4로 바꾸고 실제 Cube와 echo를 비교하세요. 위치가 매 프레임 원래대로 돌아오면 같은 명령 토픽에 다른 publisher가 있는지 `ros2 topic info -v /object_pose`로 봅니다. Generic 타입 포트가 생기지 않으면 메시지 철자/배포판의 타입 설치와 브리지 활성화를 확인합니다. 데이터 선이 연결돼도 실행 선이 없으면 처리되지 않습니다.

## 출처와 검증 범위

- [NVIDIA Isaac Sim 5.1.0 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_generic_publisher_subscriber.html)
- [5.1.0 ROS 설치와 Python 3.11 환경](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)

공식 원문의 실습을 이 폴더 안에 다시 구성하고 한국어 설명을 작성했습니다. Isaac Sim/ROS를 실제로 실행한 결과는 아직 검증하지 않았습니다(`verification: not_run`). 구문 검사나 `--help` 성공은 DDS 통신, 렌더링, GPU 동작의 검증이 아닙니다.
