# 111. USD 관절 이름을 유지하며 ROS 별칭 사용하기

## 이번에 배우는 것

**Franka의 첫 관절을 ROS에서는 `shoulder_pan`으로 부르고, 그 별칭으로 보낸 명령이 실제 관절에 적용되는 과정을 확인합니다.**

로봇 파일의 관절 이름과 외부 제어 프로그램이 기대하는 이름이 다를 때가 있습니다. USD prim을 직접 바꾸면 관절 연결이나 참조 경로까지 수정해야 할 수 있습니다. `isaac:nameOverride`는 원래 장면 주소를 유지하면서 ROS에 공개할 이름을 따로 지정합니다.

| 이름이 쓰이는 곳 | 이번 예제의 값 | 의미 |
|---|---|---|
| 실제 관절 | `panda_joint1` | 물리 articulation 내부의 이름 |
| ROS 관절 별칭 | `shoulder_pan` | JointState 발행·명령에 사용할 이름 |
| 실제 베이스 링크 | `/panda/panda_link0` | Stage의 링크 주소 |
| ROS 링크 별칭 | `robot_base` | TF 메시지에서 사용할 frame 이름 |

관절 이름과 링크 이름은 역할이 다릅니다. `shoulder_pan`은 관절 명령에, `robot_base`는 좌표계 관계에 사용합니다.

## 1. 이름을 바꾼 상태와 TF 받아 보기

Isaac Sim 5.1, 지원 GPU, 공식 Franka Panda 자산, ROS 2 Humble 또는 Jazzy가 필요합니다. 아래 명령은 저장소 루트의 Bash에서 실행합니다. 기본 환경은 Ubuntu 24.04의 Jazzy입니다. Ubuntu 22.04/Humble에서는 `jazzy` 이름과 경로를 모두 `humble`로 바꾸세요.

터미널 A는 시스템 ROS를 source하지 않은 새 셸에서 준비합니다. 설치 위치가 다르면 `ISAAC_SIM`을 바꾸세요.

```bash
export ISAAC_SIM="$HOME/isaacsim"
export ROS_DISTRO=jazzy
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export LD_LIBRARY_PATH="$ISAAC_SIM/exts/isaacsim.ros2.bridge/jazzy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$ISAAC_SIM/python.sh" src/111_ros2_ros2_name_override/run.py
```

코드는 `Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`를 `/panda`에 불러옵니다. 5.1 asset 서버 또는 로컬 asset pack에 접근할 수 있어야 합니다. GUI는 창을 닫을 때까지 실행됩니다. `--steps 1200`을 추가하면 1200스텝 뒤 종료하고, `--headless`만 추가하면 3600스텝을 사용합니다.

터미널 B에서는 시스템 ROS의 CLI와 Python을 사용합니다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ros2 topic echo /joint_states --once
ros2 topic echo /tf --once
```

### 코드에서 볼 부분

`run.py`는 Stage를 순회해 이름이 `panda_joint1`인 실제 joint prim을 찾습니다. 정확히 하나가 아니면 잘못된 관절을 수정하지 않고 중단합니다.

```python
matches[0].CreateAttribute("isaac:nameOverride", Sdf.ValueTypeNames.String).Set("shoulder_pan")
```

이 코드는 prim의 이름을 변경하지 않습니다. prim에 문자열 속성 하나를 추가합니다. `/panda/panda_link0`에도 같은 방식으로 `robot_base`를 지정합니다. Joint State와 Transform Tree 발행기가 그 속성을 읽어 ROS 이름을 정합니다.

### 실행 결과 확인하기

- 콘솔의 `USD path remains`에서 원래 `panda_joint1` 경로를 확인합니다.
- `actual_joint_names`는 물리 모델의 원래 관절 이름 배열입니다.
- `/joint_states.name`에서는 `shoulder_pan`을 찾습니다. 같은 인덱스의 `position`이 해당 관절의 각도(rad)입니다.
- `/tf`의 frame 이름에서는 `robot_base`를 찾습니다. `shoulder_pan`이 TF 링크 이름으로 나타나야 하는 것은 아닙니다.

Stage Tree의 관절·링크 이름도 그대로인지 확인해 보세요. **장면 주소는 유지되고 외부 표현만 달라졌는지**를 세 곳에서 대조하는 단계입니다.

## 2. ROS 별칭으로 실제 관절 움직이기

터미널 B에서 다음 명령을 실행합니다. `rclpy`와 `sensor_msgs`는 source한 시스템 ROS 환경에서 가져옵니다.

```bash
python3 src/111_ros2_ros2_name_override/send_command.py --joint shoulder_pan --position 0.3 --seconds 10
```

송신기는 10초 동안 `/joint_command`에 JointState를 반복 발행합니다. `position=0.3`은 약 17.2°입니다. 다른 ROS 터미널에서 `/joint_states`를 계속 읽거나 Isaac Sim 콘솔과 관절 회전을 함께 관찰하세요.

### 코드에서 볼 부분

```text
외부 JointState: name=[shoulder_pan], position=[0.3]
    → ROS2 Subscribe Joint State
    → Isaac Joint Name Resolver: shoulder_pan → panda_joint1
    → Articulation Controller
    → 실제 관절 운동
```

별칭을 부여했다고 물리 제어기가 새 문자열을 바로 이해하는 것은 아닙니다. `/JointGraph/Resolver`가 `/panda` 내부에서 별칭을 찾아 원래 관절 이름으로 변환합니다.

```python
("Subscribe.outputs:jointNames", "Resolver.inputs:jointNames")
("Resolver.outputs:jointNames", "Actuator.inputs:jointNames")
("Resolver.outputs:execOut", "Actuator.inputs:execIn")
```

이름 배열은 Resolver를 통과하지만 `positionCommand`, `velocityCommand`, `effortCommand`는 Subscriber에서 Actuator로 직접 연결됩니다. **값과 배열 순서는 유지하면서 이름만 해석**하는 구성입니다. Resolver의 실행 출력 뒤에 Actuator를 연결해 해석된 이름을 준비한 후 제어하도록 합니다.

GUI에서는 **Window > Graph Editors > Action Graph**에서 `/JointGraph`를 열어 위 연결을 확인하세요. NameOverride를 직접 적용하려면 Stop 상태에서 joint prim을 선택하고 **Property > Add > Isaac > NameOverride**를 사용합니다. 이미 속성이 있다면 값을 수정하면 됩니다.

### 실행 결과 확인하기

`/joint_states.name`에서 `shoulder_pan`의 인덱스를 찾고 `position`이 0.3 rad 쪽으로 접근하는지 확인합니다. 콘솔의 `joint_positions_rad`는 원래 `actual_joint_names` 순서로 출력되므로 두 배열의 순서를 각각 확인해야 합니다.

명령은 목표이며 즉시 같은 각도가 되는 보장은 없습니다. 물리 drive가 목표에 접근하는 모습을 관찰하세요. 송신기 종료도 원위치 복귀를 뜻하지 않습니다. 복귀시키려면 다음 목표를 보냅니다.

```bash
python3 src/111_ros2_ros2_name_override/send_command.py --joint shoulder_pan --position 0.0 --seconds 5
```

## 3. 발행과 명령의 이름 변환 정리

| 방향 | 변환 | 담당 |
|---|---|---|
| 상태를 밖으로 보냄 | 실제 관절 → ROS 별칭 | Joint State Publisher |
| 명령을 안으로 받음 | ROS 별칭 → 실제 관절 | Joint Name Resolver |
| 좌표계를 밖으로 보냄 | 실제 링크 → ROS frame 별칭 | Transform Tree Publisher |

상태 메시지에 새 이름이 나타났다는 사실은 발행 방향만 확인한 것입니다. 별칭 명령으로 관절이 움직여야 반대 방향도 연결된 것입니다. 두 관절에 같은 별칭을 부여하면 명령 대상이 모호해지므로 별칭은 구별되게 정하세요.

## 4. 간단한 확인 실험

앱을 종료하고 `run.py`에서 **베이스 링크의 별칭 `robot_base`만 `bench_base`로 바꿔 보세요.** 해당 줄은 다음과 같습니다.

```python
link.CreateAttribute("isaac:nameOverride", Sdf.ValueTypeNames.String).Set("bench_base")
```

다시 실행해 `/tf`의 베이스 frame 이름이 바뀌는지 확인합니다. Stage 주소 `/panda/panda_link0`과 관절 별칭 `shoulder_pan`은 유지되어야 합니다. 앞에서 사용한 `--joint shoulder_pan` 명령도 같은 첫 관절에 적용되어야 합니다. 링크 좌표계의 이름과 관절 명령 이름을 따로 관리한다는 점을 확인하는 실험입니다.

## 실행할 때 막히면

- **상태에 별칭은 보이지만 명령이 적용되지 않음**: Resolver의 `robotPath=/panda`, 이름 배열 연결, Resolver → Actuator 실행 연결을 확인하세요.
- **`Expected one panda_joint1` 오류**: 기대한 Franka 5.1 자산인지 확인하세요. 찾은 첫 prim을 임의로 선택하도록 코드를 바꾸지 않습니다.
- **TF에서는 원하는 이름을 못 찾음**: 관절 별칭과 링크 별칭을 구분하세요. `robot_base`는 `panda_link0`에 적용됩니다.
- **이름을 수정해도 이전 이름이 보임**: Stop/Play로 발행기와 Resolver를 다시 초기화하세요. 다른 실행의 publisher가 남아 있는지도 확인합니다.
- **ROS 명령을 보낼 때 앱이 이미 종료됨**: 관찰에는 `--steps` 없는 GUI 실행이 편리합니다. 짧은 headless 실행은 DDS 발견이 끝나기 전에 종료될 수 있습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [NameOverride Attribute](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_name_override.html)에 대응합니다. 터미널 환경은 [ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)을 따릅니다.

Franka 로딩, 관절·링크 별칭, Resolver와 외부 송신기를 하나의 실습으로 구성했습니다. `tutorial.json`의 `verification`은 `not_run`입니다. 설명한 상태·명령 결과는 실제 GUI·ROS 통신에서 확인할 기준이며 이 개정에서 물리 운동을 실측하지 않았습니다.
