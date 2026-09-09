# 모바일 로봇과 매니퓰레이터

이 튜토리얼에서는 articulation이라는 공통 기반 위에서 모바일 로봇과 매니퓰레이터가 어떻게 다른 명령을 사용하는지 익힌다. 모바일 로봇은 베이스 속도를 바퀴 관절 속도로 바꾸고, 매니퓰레이터는 작업 공간 목표를 관절 명령과 그리퍼 상태로 바꾼다.

## 1. 모바일 로봇의 운동학 모델과 단위

차동 구동에서 원하는 선속도 \(V\), yaw 각속도 \(\omega\), 바퀴 반지름 \(r\), 좌우 바퀴 간 거리 \(l\)가 주어지면 다음 바퀴 각속도를 사용한다.

\[
\omega_R=\frac{2V+\omega l}{2r},\qquad
\omega_L=\frac{2V-\omega l}{2r}
\]

입력은 `m/s`, `rad/s`, 출력 바퀴 속도는 `rad/s`이다. 바퀴 반지름과 좌우 바퀴 간 거리를 시각 메시가 아니라 실제 접촉 충돌 형상과 관절 위치에서 측정한다.

## 2. Jetbot 차동 구동 standalone 예제

이 절은 저장소의 [drive_jetbot.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/drive_jetbot.py)를 실행한다. 아래 명령만큼은 Isaac Sim 설치 폴더가 아닌 **이 저장소의 루트**에서 실행한다.

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/drive_jetbot.py \
  --gui --output-dir outputs/core-jetbot
```

파일은 로봇의 충돌 형상이 바닥과 겹치지 않는지 먼저 검사한다. 정지 명령으로 3초간 자세를 안정시킨 뒤, 속도를 서서히 높여 직진하고 다시 감속해 멈춘다. 전진 거리, 옆으로 벗어난 거리, 차체 기울기, 바퀴 잔류 속도와 reset 결과를 검사하며 실패하면 정상 완료로 처리하지 않는다. `drive.csv`에서 명령 속도와 실제 위치를 비교한다.

핵심 계산은 다음과 같다. 이 코드는 기존 프로그램의 제어기 계산 부분만 발췌한 것으로, `robot`이 초기화된 뒤 사용한다.

```python
from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController

controller = DifferentialController(name="diff", wheel_radius=0.03, wheel_base=0.1125)
action = controller.forward([0.12, 0.0])  # 전진 0.12 m/s, 회전 0 rad/s
robot.apply_wheel_actions(action)
```

바퀴 명령은 매 물리 스텝마다 적용한다. 먼저 직진·정지 검사를 통과한 뒤 작은 회전 명령을 추가한다. 이 파일의 실행 절차를 갖췄다는 것과 실제 장비에서 통과했다는 것은 별개이며, 로그와 출력 파일로 결과를 확인해야 한다.

### 검증 포인트

- 양의 선속도에서 좌우 바퀴가 같은 방향으로 도는가?
- 양의 yaw 명령에서 기대한 방향으로 회전하는가?
- 정지 명령 뒤 바퀴 속도가 0으로 수렴하는가?
- 바닥 마찰을 바꾸면 미끄러짐과 오도메트리 오차가 예상대로 변하는가?

좌우가 바뀌거나 한 바퀴가 반대로 돌면 제어기 수식을 바꾸기 전에 관절 축과 `wheel_dof_names` 순서를 확인한다.

## 3. 목표 자세로 이동하기

`DifferentialController`는 순간 베이스 속도를 바퀴 동작으로 변환할 뿐 목표 위치에 도달하기 위한 피드백 제어는 제공하지 않는다. `WheelBasePoseController`는 현재 자세와 목표 자세를 받아 전진 속도와 회전 각속도를 계산한 뒤 차동 구동 제어기에 전달한다. 다음은 앞의 프로그램에서 `robot`과 `controller`를 초기화한 뒤에 적용하는 코드 조각이다.

```python
from isaacsim.robot.wheeled_robots.controllers.wheel_base_pose_controller import (
    WheelBasePoseController,
)

pose_controller = WheelBasePoseController(
    name="go_to_pose",
    open_loop_wheel_controller=controller,
    is_holonomic=False,
)

position, orientation = robot.get_world_pose()
action = pose_controller.forward(
    start_position=position,
    start_orientation=orientation,
    goal_position=np.array([1.0, 0.5]),
)
robot.apply_wheel_actions(action)
```

API 인자와 정지 판정의 허용 오차는 사용하는 5.1 제어기 문서에서 확인한다. 실제 주행에는 장애물 지도, 전역 경로 계획기, 위치 추정, 복구가 더 필요하다. 이 제어기만으로 Nav2의 기능을 대체할 수는 없다.

## 4. Holonomic과 Ackermann

### Holonomic

메카넘 휠이나 옴니 휠을 사용하는 로봇은 `[forward, lateral, yaw]` 속도를 명령할 수 있다. `HolonomicController`는 바퀴 위치, 방향, 반지름과 롤러 각도로 관절 드라이브 명령을 계산한다. 로봇 USD의 바퀴 관절에 메카넘 휠의 반지름과 각도 속성이 필요하며 `HolonomicRobotUsdSetup`으로 작성을 자동화할 수 있다.

```python
from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import (
    HolonomicController,
)

holonomic = HolonomicController(
    name="omni_base",
    wheel_radius=[0.04, 0.04, 0.04],
    wheel_positions=[
        [-0.098, 0.001, -0.051],
        [0.049, -0.085, -0.051],
        [0.050, 0.086, -0.051],
    ],
    wheel_orientations=[
        [0.0, 0.0, 0.0, 1.0],
        [0.866, 0.0, 0.0, -0.5],
        [0.866, 0.0, 0.0, 0.5],
    ],
    mecanum_angles=[90.0, 90.0, 90.0],
)
wheel_action = holonomic.forward([0.3, 0.1, 0.2])
```

방향 쿼터니언의 순서는 해당 제어기 예제에서 정한 순서를 따른다. 사용자 로봇 값은 CAD/관절 프레임에서 산출해 검증한다.

### Ackermann

Ackermann 차량은 조향 관절의 위치와 바퀴 관절의 속도를 별도로 제어한다. 축거, 윤거, 회전 반경과 조향각의 관계가 중요하다. `AckermannController`의 결과를 조향 관절과 구동 바퀴의 인덱스에 맞춰 나누어 적용한다.

```python
from isaacsim.robot.wheeled_robots.controllers.ackermann_controller import (
    AckermannController,
)

ackermann = AckermannController(
    "car_controller",
    wheel_base=1.65,
    track_width=1.25,
    front_wheel_radius=0.25,
    back_wheel_radius=0.25,
)
action = ackermann.forward(
    [
        0.1,  # desired steering angle
        0.0,  # steering velocity
        1.1,  # desired forward velocity
        0.0,  # acceleration
        0.0,  # dt: acceleration limit을 쓰지 않는 예제
    ]
)
```

5.1 제어기의 입력 순서는 `[steering_angle, steering_velocity, forward_velocity, acceleration, dt]`이다. 가속도 제한을 사용하면 실제 물리 dt를 마지막 원소에 넣는다. 제어기 출력에서 조향 목표와 바퀴 속도를 어느 관절에 보낼지 이름 기반으로 매핑한다.

## 5. 모바일 로봇 튜닝 순서

1. 바퀴 충돌 형상의 반지름와 관절 축을 확정한다.
2. 베이스 질량, 질량 중심과 관성을 확인한다.
3. 바퀴/바닥 물리 재질을 설정한다.
4. 공중에서 바퀴 속도 명령을 시험해 부호와 순서를 확인한다.
5. 평면에서 직진·제자리 회전을 시험한다.
6. 명령 속도와 실제 베이스 속도를 기록한다.
7. 가속도·감속도과 최대 바퀴 속도 제한을 적용한다.
8. 경사, 턱, 적재물에서 미끄러짐과 접촉 안정성을 시험한다.

시각적으로 경로가 비슷한지만 보지 말고 다음 지표를 남긴다.

```python
position, _ = robot.get_world_pose()
linear_velocity = robot.get_linear_velocity()
wheel_velocity = robot.get_joint_velocities()
```

## 6. 매니퓰레이터 API 객체의 역할

일반 `SingleArticulation`도 로봇 팔 관절을 제어할 수 있지만 특정 로봇용 매니퓰레이터 API 객체는 다음 정보를 함께 제공한다.

- `end_effector` prim API 객체
- 평행 그리퍼 또는 흡착 그리퍼 객체
- 열림·닫힘 상태의 관절 위치
- 해당 로봇용 제어기와 작업
- 기본 USD와 관절 이름 규칙

`Franka` API 객체와 `PickPlaceController`는 Core API에서 각 역할을 나누는 방식을 보여 준다. 다음 절의 공식 5.1.0 예제는 다른 실행 구조를 사용하므로 소스에서 객체 구성을 확인한다.

## 7. Franka 집기·놓기 공식 예제

Isaac Sim 5.1.0 설치본에 포함된 전체 프로그램부터 실행한다.

```bash
cd "$ISAACSIM_PATH"
test -f standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py
./python.sh standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py
```

GUI에서는 **Window > Examples > Robotics Examples > Manipulation > Franka Pick Place**를 열고 `LOAD`, `START PICK PLACE` 순서로 실행한다. 물체를 실제로 집고 놓는지 확인한 뒤 `RESET`으로 초기 상태를 다시 확인한다.

5.1.0의 공식 실행 파일은 `FrankaPickPlace`와 `SimulationManager`를 사용한다. 앞에서 설명한 Core API의 `Franka` 객체나 `PickPlaceController`를 공부할 때도, 서로 다른 실행 구조의 코드 조각을 공식 파일에 그대로 섞지 않는다. 구체적인 소스와 수정 위치는 [프로젝트 4의 공식 Franka 실행 절차](../07-projects/04-vision-pick-place.md)에서 확인한다.

집기·놓기 제어는 접근, 하강, 집기, 상승, 이동, 놓기의 순서로 진행된다. 제어기의 `is_done()`은 단계가 끝났다는 뜻이며 물체를 놓쳤어도 참이 될 수 있다. 성공 여부는 다음 기준으로 별도로 확인한다.

- 물체가 바닥이나 로봇과 겹치지 않는 초기 위치에서 시작한다.
- 로봇과 물체의 자세가 안정된 뒤 집기를 시작한다.
- 집기 중 물체가 실제로 들어 올려지고 그리퍼에서 빠지지 않는다.
- 놓은 뒤 충분히 기다려 물체가 목표 위치에 정착했는지 측정한다.
- 관절이나 물체의 위치에 NaN/Inf가 없으며, 정해진 시간 안에 완료되지 않으면 실패로 기록한다.

카메라로 물체 위치를 추정해 같은 작업에 연결하는 과정은 [프로젝트 4](../07-projects/04-vision-pick-place.md)로 이어진다.

## 8. 그리퍼를 이해하기

### 평행 그리퍼

- 손가락 관절 이름과 열림·닫힘 위치를 정의한다.
- 연동 관절이 있으면 주 관절과 관계를 확인한다.
- 손가락 끝의 충돌 형상과 마찰을 별도 튜닝한다.
- 물체의 폭이 그리퍼의 가동 범위 안에 있는지 확인한다.

### 표면 그리퍼

표면 그리퍼 Extension은 흡착형 말단 장치를 모델링한다. 부모 경로, 오프셋, 흡착 판정 임곗값과 힘/토크 제한을 설정하고 접촉 조건에 따라 흡착하거나 놓는다. 강제로 물체를 순간 이동시키는 방식과 다르므로 그리퍼 프레임, 충돌 형상과 접근 자세가 중요하다.

Grasp Editor는 파지 자세를 작성하는 데 유용하다. 어떤 그리퍼든 “제어기가 close를 호출했다”와 “물체가 실제로 부착되었다”를 별도 상태로 검사한다.

## 9. 작업으로 장면과 평가 분리하기

Core `BaseTask`는 다음 책임을 나눈다.

```python
from isaacsim.core.api.tasks import BaseTask


class ReachTask(BaseTask):
    def set_up_scene(self, scene):
        super().set_up_scene(scene)
        # 로봇, 목표와 환경을 추가한다.

    def get_observations(self):
        # controller에 필요한 상태를 dict로 반환한다.
        return {}

    def pre_step(self, control_index, simulation_time):
        # 매 step metric/종료 조건을 갱신한다.
        pass

    def post_reset(self):
        # episode 상태와 gripper/controller를 초기화한다.
        pass

    def calculate_metrics(self):
        return {"position_error": 0.0}

    def is_done(self):
        return False
```

작업은 장면 생성, 관측값, 평가 지표와 종료 조건을 묶고 제어기는 관측값을 제어 명령으로 바꾼다. 이 둘을 분리하면 같은 작업에 서로 다른 제어기를 비교할 수 있다.

## 10. 여러 로봇과 여러 작업

각 로봇과 작업에 고유한 네임스페이스와 `offset`을 둔다.

```text
/World/envs/env_0/Franka
/World/envs/env_0/Target
/World/envs/env_1/Jetbot
/World/envs/env_1/Goal
```

- 객체 이름과 prim 경로를 모두 고유하게 만든다.
- 물리 콜백 이름도 고유하게 만든다.
- 관측값 딕셔너리에서 사용하는 키와 값의 의미를 문서화한다.
- 여러 작업이 같은 관절에 동시에 명령을 보내지 않도록 제어 권한을 조정한다.
- 다수 환경에서는 여러 객체를 배열 단위로 처리하는 `Articulation`/`RigidPrim` view와 Cloner를 고려한다.

## 11. 실패를 계층별로 나누기

| 증상 | 운동학/제어기 | 물리/자산 |
|---|---|---|
| EE가 목표 반대편으로 감 | EE 프레임, 관절 순서, 쿼터니언 | 관절 축/가져오기 변환 |
| 경로는 맞는데 크게 뒤처짐 | 목표 속도, 제어 dt | 게인, 토크·힘/속도 제한 |
| 물체를 끼웠는데 빠짐 | 그리퍼를 닫는 시점, 파지 자세 | 손가락 끝의 마찰, 충돌 형상, 토크·힘 |
| 모바일 로봇이 원을 그림 | 바퀴 반지름과 순서 보정 | 좌우 마찰·질량 비대칭 |
| 정지 명령에도 움직임 | 이전 명령의 유지 여부, 제어기 초기화 | 감쇠, 경사, 접촉 |

## 12. 검증 체크포인트

- [ ] Jetbot이 0.1 m 이상 이동하고 유한한 자세를 반환했다.
- [ ] 바퀴 반지름, 베이스와 DOF 순서를 자산에서 확인했다.
- [ ] 차동 구동, 전방향 구동, Ackermann 제어기의 입력 차이를 안다.
- [ ] Franka API 객체의 그리퍼와 end-effector가 초기화되었다.
- [ ] pick-and-place 제어기의 단계와 `is_done()`을 검사했다.
- [ ] 작업, 제어기, 로봇 자산의 책임을 분리했다.
- [ ] 여러 로봇이 같은 prim/name/콜백을 공유하지 않는다.

## 출처

- [Hello Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_robot.html)
- [Adding a Controller](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_controller.html)
- [Mobile Robot Controllers](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/mobile_robot_controllers.html)
- [Adding a Manipulator Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_manipulator.html)
- [Adding Multiple Robots](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_adding_multiple_robots.html)
- [Multiple Tasks](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_multiple_tasks.html)
- [Surface Gripper Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html)
- [Grasp Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html)
