# 03. 로봇 기본: Franka와 Nova Carter 불러오기·조사·제어

권장 학습 순서 **03** · 첫 실행과 로봇 만나기 · 출처 ID `t002`

Isaac Sim 5.1 공식 **Basic Robot Tutorial**의 GUI, Script Editor, 독립 Python 워크플로를 한 패키지에 담았다. 장면이 처음인 사용자도 아래 준비부터 시작하면 된다. 다른 로컬 패키지를 가져오거나 먼저 읽지 않는다.

## 준비와 결과

Isaac Sim **5.1.0**, 지원 NVIDIA GPU/드라이버, 5.1 자산 루트에 대한 접근이 필요하다. 로봇 메시·텍스처·관절 설정은 NVIDIA 제공 USD를 참조하며 여기에 복제하지 않았다. 로봇 USD와 그 종속 파일 모두 접근 가능해야 한다.

| 로봇 | 5.1 자산 루트 아래 경로 |
|---|---|
| Franka Panda | `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd` |
| Nova Carter | `/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd` |

`get_assets_root_path()`는 설치에서 설정한 자산 루트를 찾는다. 로컬 자산을 설치했다면 아래 옵션으로 해당 USD의 절대 경로를 명시할 수 있다. 개별 USD만 복사하면 상대 참조가 깨질 수 있으므로 자산 디렉터리 구조를 유지한다.

예상 결과는 Franka의 자세 변경, Nova Carter의 정지/주행 전환, 각 관절의 이름·한계·실제 상태 출력이다. 이 예제는 내비게이션이나 경로계획을 수행하지 않고 관절 수준 API를 익힌다.

## 1. 독립 Python 실습

이 패키지 폴더를 현재 디렉터리로 사용한다. 설치 위치가 다르면 `~/isaacsim` 부분을 바꾼다.

```bash
python3 run.py --help
~/isaacsim/python.sh run.py
~/isaacsim/python.sh run.py --headless --steps 480 --wheel-speed 0.5
```

자산 경로를 직접 지정하는 형식은 다음과 같다. `/실제/` 부분을 본인 자산 경로로 바꾼다.

```bash
~/isaacsim/python.sh run.py --arm-usd /실제/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd --car-usd /실제/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd
```

1. `SimulationApp` 생성 후 `World`와 지면·광원을 만든다. `/World/Arm`과 `/World/Car`에 각각 USD reference를 추가한다.
2. 로봇의 초기 위치를 Y=+1.2 m와 −1.2 m로 벌려 겹치지 않게 한다. `Articulation`을 `world.scene`에 등록하고 `world.reset()`으로 물리 핸들을 초기화한다.
3. 관절 수, 자유도 수, 자유도 이름, 한계, 초기 위치를 `joint_info.json`에 기록한다. 회전 자유도는 rad, 손가락처럼 직선 이동하는 자유도는 m 단위다. 전체 joint 개수와 제어 가능한 DOF 개수가 항상 같지는 않다.
4. `--steps`를 명시하면 총 스텝을 네 구간으로 나눈다. 0번은 초기 자세/정지, 1번은 팔 자세 변경/주행, 2번은 초기 자세/정지, 3번은 자세 변경/주행이다. `--steps`를 생략한 GUI에서는 구간마다 120스텝씩 네 구간을 반복한다. `--headless`에서 생략하면 480스텝(물리 시간 8초) 후 종료한다.
5. `states.csv`의 `phase`, `car_x_m`, `car_y_m`, `arm_q`, `car_q`를 비교한다. 주행 구간에서 바퀴 관절과 차체 위치가 변하는지 확인한다. 정지 명령 직후 감속 구간은 있을 수 있다.
6. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI와 제어가 유지된다. 양수 `--steps N`을 지정하면 N스텝 후 종료한다. 예외가 발생하면 앱을 정리하고 종료한다.

파일은 기본적으로 패키지 내부 `output/날짜-시간/`에 생성된다. `--output /새/폴더`로 경로를 지정할 수 있고 기존 폴더는 거부한다. 기록은 시뮬레이터에서 읽은 값이며 측정 없이 성공값을 만들지 않는다.

원본의 네 구간 구조는 유지했다. 초심자가 모든 Carter 관절에 같은 속도를 넣지 않도록 `joint_wheel_left`, `joint_wheel_right`만 이름으로 지정하고 속도 **목표값**을 반복 전달한다. 팔은 원본처럼 `set_joint_positions`로 직접 상태를 바꾼다. 원문의 전체 영점 자세 대신 관절 한계 안의 초기 자세를 사용한다. 이 차이를 정상적인 물리 제어와 혼동하지 않도록 아래 API 설명을 읽는다.

## 2. GUI에서 로봇과 그래프 조사

1. `~/isaacsim/isaac-sim.selector.sh`로 GUI를 열고 **File > New**를 선택한다. **Create > Physics > Ground Plane**, **Create > Lights > Distant Light**로 바닥과 조명을 추가한다.
2. **Create > Robots > Franka Emika Panda Arm**으로 로봇을 추가한다. Stage 트리의 로봇 루트를 선택하고 **Tools > Physics > Physics Inspector**를 연다.
3. Physics Inspector에서 각 관절의 lower/upper limit와 기본 위치를 확인한다. 오른쪽 위 메뉴에서 stiffness/damping 열을 표시한다. 회전 관절 하나만 한계 안에서 바꿔 자세가 변하는지 본다. 변경값을 새 기본값으로 확정하려면 초록 체크를 누른다.
4. **Tools > Robotics > Omnigraph Controllers > Joint Position**을 연다. **Robot Prim > Add**에서 방금 추가한 Franka를 선택하고 **OK**를 누른다.
5. Stage의 **Graph > Position_Controller > JointCommandArray**를 선택한다. Property의 Construct Array 입력값이 관절 순서와 어떻게 대응하는지 확인한다. 일곱 팔 관절과 두 손가락의 수치 단위가 다르므로 한계값을 먼저 확인한다.
6. **Play**를 누르고 첫 번째 팔 관절 값만 작은 각도(예: 0.2 rad)로 바꾼다. 움직임을 관찰한 뒤 원래 값으로 복원한다. 다른 관절은 한계 안의 초기값을 유지한다.
7. **Window > Graph Editors > Action Graph > Edit Action Graph**에서 생성된 그래프를 선택한다. 실행 신호가 Articulation Controller로 전달되고 JointCommandArray의 값이 position command 입력으로 연결되는 경로를 따라가 본다. 그래프의 로봇 대상 경로가 실제 Stage 경로와 일치하는지 확인한다.

이 GUI 방법은 NVIDIA의 기본 그래프 생성 도구를 사용한다. 패키지가 그 도구 자체를 복제하는 것은 아니며, 필드 수정·연결 검사·실행 확인이 로컬 실습 내용이다.

## 3. Script Editor: 한 번 읽기와 매 스텝 읽기

새 GUI 인스턴스의 빈 Stage에서 **Window > Script Editor**를 열고 `script_editor.py` 전체 내용을 붙여 넣어 실행한다. 비동기 초기화 후 `Ready`가 출력될 때까지 기다린다. 이 파일은 바닥과 조명까지 만들고 Franka를 초기화하므로 다른 파일 실행이 필요하지 않다.

같은 탭에서 다음 명령을 하나씩 실행한다. **Play** 상태를 유지한다.

```python
inspect_robot()
move_robot()
inspect_robot()
start_logging()
```

`inspect_robot()`은 실행한 순간의 상태만 출력한다. `start_logging()`은 이름 있는 물리 콜백을 등록하므로 매 물리 스텝마다 `dt`와 관절 위치가 출력된다. 출력이 많아지면 다음을 실행한다.

```python
stop_logging()
```

Script Editor는 앱의 이벤트 루프가 시간을 전진시키므로 `await reset_async()`를 사용한다. 독립 Python에서는 자신의 반복문에서 `world.step()`을 호출한다. 본 파일을 다시 실행하려면 새 GUI 인스턴스를 사용한다. 이미 존재하는 `World`를 다른 예제와 섞어 초기화하지 않도록 검사한다.

## API와 Omniverse/USD 개념

| API/개념 | 설명 |
|---|---|
| USD reference | 원본 로봇 파일을 장면에 조합한다. `/World/Arm`은 현재 Stage의 경로이고 외부 USD 파일 경로와 다르다. |
| Articulation | 여러 강체가 관절로 연결된 하나의 물리 시스템이다. 시각적인 로봇 Prim이 존재해도 물리 초기화 전에는 관절 상태를 읽을 수 없다. |
| `Articulation` 배열 | 한 객체라도 위치는 `(1, 3)`, 관절 명령은 `(1, K)` 배열이다. 여러 로봇을 한 view에 담을 수 있기 때문이다. |
| `dof_names`, `get_dof_limits()` | 제어 가능한 자유도의 이름과 범위를 확인한다. 자산마다 순서가 달라질 수 있어 이 코드는 관절 이름을 명시한다. |
| `set_joint_positions` | 관절 상태를 즉시 지정하는 API다. 모터가 경로를 따라 이동하는 제어 명령과 같지 않다. |
| `set_joint_velocity_targets` | 물리 드라이브가 추종할 속도를 지정한다. 바퀴에는 속도 제어에 적합한 stiffness/damping 설정이 필요하며 제공 Carter 자산의 드라이브를 사용한다. |
| `World.reset`, `world.step` | 물리 시스템 초기화와 일정 시간 전진을 담당한다. 콜백 방식은 GUI가, 반복문 방식은 독립 스크립트가 스텝을 소유한다. |
| OmniGraph | 노드와 연결로 데이터·실행 흐름을 만든다. 로봇 USD와 별개인 제어 그래프가 그 로봇을 대상으로 명령을 보낸다. |

## 한 가지 변수 실험과 문제 해결

`--wheel-speed`만 1.0에서 0.5로 바꾸고 동일한 스텝 수에서 차체 이동 거리를 비교한다. 마찰과 초기 과도응답이 있어 정확히 절반이라고 가정하지 말고 CSV에서 확인한다.

로봇이 보이지 않으면 자산 루트와 모든 종속 USD 접근을 확인한다. `joint_info.json`은 생성되지만 관절 이름 오류가 나면 다른 로봇 버전이 지정되었는지 확인한다. 핸들 초기화 오류에는 Play/Reset과 USD의 Articulation Root가 관련된다. Script Editor에서 Stop 이후 핸들이 무효가 되면 새 인스턴스로 실습을 다시 시작한다. 일반 Python/LSP가 `omni`를 찾지 못하는 것은 설치 Python으로 실행했는지와 별도로 판단한다. 이 패키지의 정적 검사는 로봇 자산 로딩이나 GPU 시뮬레이션 실행을 보증하지 않는다.

## 출처

- NVIDIA, Isaac Sim **5.1.0**, [Basic Robot Tutorial — Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim_robot.html#tutorial): Franka 삽입, Physics Inspector, Joint Position 그래프, Script Editor 콜백, Franka/Carter의 네 구간 실행.
- NVIDIA, Isaac Sim **5.1.0**, [Core API Overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/core_api_overview.html), [Workflows](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/workflows.html): World와 실행 방식.
- 설치본 `standalone_examples/tutorials/getting_started_robot.py`, `exts/isaacsim.core.prims/isaacsim/core/prims/impl/articulation.py`, `exts/isaacsim.robot.wheeled_robots/isaacsim/robot/wheeled_robots/robots/wheeled_robot.py`에서 자산 경로·관절 이름·5.1 API 시그니처를 대조했다.
