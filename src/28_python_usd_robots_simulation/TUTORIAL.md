# 28. 두 로봇의 관절을 배열로 제어하기

## 이번에 배우는 것

**Franka 두 대를 하나의 Articulation 조회·제어 객체로 다루고, 위치·속도·토크 명령이 각각 무엇을 뜻하는지 비교합니다.**

로봇이 여러 대여도 같은 관절 명령을 배열로 한 번에 보낼 수 있습니다. 이때 배열의 행은 로봇, 열은 선택한 관절입니다. 두 로봇은 여전히 각각의 물리 articulation이며, 하나의 기구로 연결하는 것은 아닙니다. 이번에는 두 Franka를 같은 초기 자세로 놓고, 움직임을 직접 설정하는 것과 물리 드라이브의 목표를 설정하는 것을 구분합니다.

| `--control` | 명령할 관절 | `--target`의 의미 |
|---|---|---|
| `position` | 팔 관절 7개 | 초기 자세에 더할 사인파 진폭, rad |
| `single-position` | `panda_joint2` | 위와 같은 위치 진폭, rad |
| `velocity` | 팔 관절 7개 | 일정한 속도 목표, rad/s |
| `single-velocity` | `panda_joint2` | 일정한 속도 목표, rad/s |
| `effort` | `panda_joint2` | 직접 적용할 토크, N·m |

기본 `--target`은 0.2입니다. 숫자가 같아도 선택한 모드에 따라 단위와 동작이 달라집니다.

## 1. 두 Franka에 위치 목표 보내기

Isaac Sim 5.1, 지원 NVIDIA GPU, Franka 에셋 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`와 종속 파일이 필요합니다. 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/28_python_usd_robots_simulation/run.py --control position --steps 120
```

`~/isaacsim`은 실제 설치 위치로 바꾸세요. 두 로봇을 x=-1 m와 x=1 m에 놓고 물리 120단계를 진행한 뒤 종료합니다. `--headless`를 추가하면 창 없이 실행합니다. 단계 수를 생략하면 GUI는 계속 제어·기록하고 headless는 120단계에 종료합니다.

### 코드에서 볼 부분

각 로봇 USD를 참조한 뒤 경로 표현식 하나로 두 로봇을 묶습니다.

```python
Articulation(
    "/World/Franka_[1-2]",
    name="frankas",
    positions=np.array([[-1, 0, 0], [1, 0, 0]]),
)
```

`[1-2]`는 `/World/Franka_1`과 `/World/Franka_2`를 선택합니다. 초기 위치 배열도 두 행입니다. `world.reset()` 후 물리 핸들을 확인하고, 실제 `dof_names`에 원하는 관절이 있는지 검사합니다. DOF는 독립적으로 움직일 수 있는 자유도이며, Franka에서는 팔 관절 7개와 손가락 관절 2개를 읽습니다.

초기 자세는 `set_joint_positions()`로 설정합니다. 이후 반복에서는 `set_joint_position_targets()`를 사용합니다. 앞 호출은 현재 상태를 바로 바꾸는 초기화이고, 뒤 호출은 물리 드라이브가 따라갈 목표를 보내는 제어입니다.

위치 목표는 관절별 초기값에 `args.target * sin(step / 60)`을 더합니다. 첫 반복의 `step=0`에서는 추가량이 0입니다. 목표가 곧바로 0.2 rad가 되는 것이 아니라 시간에 따라 초기 자세 주변으로 움직입니다.

### 실행 결과 확인하기

이 폴더의 `output/날짜-시간/`에서 `robot_info.json`과 `states.csv`를 확인하세요.

| 결과 | 확인할 내용 |
|---|---|
| `count` | 선택한 로봇 수, 기본 2 |
| `dof_names`, `limits` | 상태 배열의 관절 순서와 범위 |
| `controlled_joints` | 이번 실행에서 목표를 보내는 관절 이름 |
| `variants` | USD 자산에 존재하는 variant 선택지, 이 코드는 선택을 변경하지 않음 |
| CSV `step`, `robot` | 한 단계마다 로봇 0·1이 각각 한 행 |
| CSV `positions`, `velocities`, `applied_efforts` | 그 로봇의 전체 관절 값 배열 |

120단계를 모두 기록하면 데이터 행은 240개입니다. `positions`에는 팔의 rad 값과 손가락의 m 값이 함께 있으므로 이름과 대응해서 읽으세요. `applied_efforts`는 직접 적용한 effort를 조회한 값이며, 모든 드라이브 토크·접촉 반력을 측정한 센서값으로 해석하지 않습니다.

## 2. 속도 목표와 직접 토크 비교하기

한 관절만 관찰할 수 있도록 다음 명령을 차례대로 실행해 보세요.

```bash
~/isaacsim/python.sh src/28_python_usd_robots_simulation/run.py --control single-velocity --target 0.1 --steps 120
~/isaacsim/python.sh src/28_python_usd_robots_simulation/run.py --control effort --target 0.2 --steps 120
```

첫 실행은 두 로봇의 `panda_joint2`에 0.1 rad/s 속도 목표를 보냅니다. 둘째는 같은 관절에 0.2 N·m 토크를 직접 보냅니다. 토크 명령에는 도달할 위치나 속도가 포함되지 않습니다.

### 코드에서 볼 부분

속도 제어에서는 위치 오차에 반응하는 stiffness를 끄고, 속도 오차에 반응하는 damping을 남깁니다.

```python
robots.set_gains(
    kps=np.zeros((2, len(controlled))),
    kds=np.full((2, len(controlled)), 20.0),
    joint_names=controlled,
)
```

단일 관절 모드라면 gain 배열은 `(2, 1)`입니다. 위치를 붙잡는 작용이 남아 있으면 속도 명령과 함께 작동할 수 있기 때문에, 제어할 관절의 gain을 명시적으로 바꿉니다. effort 모드는 그 관절의 stiffness와 damping을 모두 0으로 만들어 직접 토크를 적용합니다.

이 변경은 `controlled`로 지정한 관절에만 적용됩니다. 다른 관절의 gain을 모두 끄는 것은 아닙니다. 또한 effort 모드에는 중력 보상이 없으므로 작은 양의 토크를 주었다고 반드시 예상한 방향으로만 움직이지는 않습니다.

### 실행 결과 확인하기

`robot_info.json`의 `controlled_joints`에서 `panda_joint2`를 확인한 뒤, `dof_names`에서 그 열을 찾아 CSV의 위치·속도를 읽으세요. single 모드는 명령 대상이 하나라는 뜻이며, 다른 관절의 실제 움직임이 모두 0이라는 뜻은 아닙니다. 로봇 전체가 연결된 물리 시스템이기 때문입니다.

### 원문의 핸들 기반 API와 비교하기

5.1의 `omni.isaac.dynamic_control` 확장이 제공되는 환경에서는 원문의 상태 조회 방식도 비교할 수 있습니다. 단계 수를 생략한 실행에서 **Window > Extensions**의 해당 확장을 켜세요. **Play 상태를 유지**하고 **Window > Script Editor**에 다음을 실행합니다.

```python
from omni.isaac.dynamic_control import _dynamic_control
dc = _dynamic_control.acquire_dynamic_control_interface()
handle = dc.get_articulation("/World/Franka_1")
print("Object type:", dc.peek_object_type("/World/Franka_1"))
print("Joint / DOF / body counts:", dc.get_articulation_joint_count(handle),
      dc.get_articulation_dof_count(handle), dc.get_articulation_body_count(handle))
dof = dc.find_articulation_dof(handle, "panda_joint2")
print("Joint state:", dc.get_dof_state(dof, _dynamic_control.STATE_ALL))
```

여기서 handle은 물리 객체를 찾은 뒤 사용하는 식별자입니다. Core `Articulation`의 이름·배열 조회와 달리 로봇 handle에서 특정 DOF handle을 찾아 상태를 읽습니다. 두 방식에서 `panda_joint2`의 상태가 같은 로봇을 가리키는지 비교하세요.

직접 위치 명령까지 시험하려면 독립 실행 창을 닫고 `~/isaacsim/isaac-sim.sh`로 새 GUI를 엽니다. Content Browser에서 앞의 Franka USD를 `/World` 아래에 끌어놓고 root 이름을 `Franka_1`로 바꿉니다. **Create > Physics > Ground Plane**을 추가한 뒤 Play하세요. Extensions에서 `omni.isaac.dynamic_control`을 활성화하고 같은 조회 코드를 실행한 다음 아래 두 줄을 실행합니다.

```python
dc.wake_up_articulation(handle)
dc.set_dof_position_target(dof, -0.4)
```

기존 `run.py` 창은 매 단계 자기 목표를 다시 쓰므로 이 단발 명령을 유지하는 비교 환경으로 적합하지 않습니다. 별도 GUI에서는 `panda_joint2`의 위치 drive가 켜져 있는지 확인하고 -0.4 rad 목표로의 반응을 관찰하세요. 원문의 전체 위치·속도·effort API도 같은 핸들 방식을 사용하며, 속도 제어는 stiffness=0, 직접 effort는 해당 drive gain=0이라는 조건이 같습니다.

## 3. 상태 설정과 세 제어 방식 정리

```text
초기화: 현재 관절 위치를 설정 → 물리 시작 자세 준비
위치 제어: 위치 목표 → 드라이브 응답 → 실제 위치
속도 제어: 속도 목표 + 위치 stiffness 0 → 실제 속도
토크 제어: 직접 토크 + 해당 drive gain 0 → 물리 운동
```

배열 크기가 맞는 것과 명령의 의미가 맞는 것은 별개입니다. 어떤 관절을 선택했는지, 값의 단위가 무엇인지, 드라이브가 어떻게 설정되어 있는지 함께 확인해야 결과를 해석할 수 있습니다.

## 4. 간단한 확인 실험

앞의 single-velocity 실행에서 `--target` 부호만 바꿔 보세요.

```bash
~/isaacsim/python.sh src/28_python_usd_robots_simulation/run.py --control single-velocity --target -0.1 --steps 120
```

`panda_joint2`가 따르는 속도 목표의 방향이 반대로 바뀝니다. 처음 몇 단계의 응답과 관절 한계 때문에 즉시 정확히 -0.1 rad/s가 되리라고 단정하지 말고, CSV 속도 열의 부호와 시간에 따른 위치 변화를 비교하세요. 나머지 조건을 유지해야 부호 변화의 영향을 읽기 쉽습니다.

## 실행할 때 막히면

- **Franka 경로를 읽지 못함**: `--usd /실제/경로/franka.usd`로 로컬 자산을 지정할 수 있습니다. 참조된 mesh·재질도 함께 있어야 합니다.
- **관절 이름이 다르다는 오류**: 이 초기 자세와 제어 대상은 Franka Panda의 관절 이름을 전제로 합니다. 다른 로봇을 같은 옵션에 넣어 실행하지 마세요.
- **`--target` 값 오류**: 작은 움직임을 비교하도록 유한한 값이면서 절댓값 0.5 이하만 허용합니다. 모드에 맞는 단위도 확인하세요.
- **실행 중 CSV 행이 적어 보임**: GUI 무제한 실행은 파일을 연 채 계속 씁니다. 단계 수를 지정해 종료한 후 완성된 파일을 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Robot Simulation Snippets](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/robots_simulation.html)에 대응합니다. 기본 실행은 Core `Articulation`으로 다섯 제어 방식을 비교하고, 선택적인 Script Editor 실습에서 원문의 Dynamic Control 조회·위치 명령을 대조합니다. 자산 variant는 조사만 하며 집기 작업이나 추종 성공 판정은 구현하지 않습니다.

`tutorial.json`의 상태는 `not_run`입니다. 배열과 명령의 설명은 실행 시 확인할 기준이며, 두 로봇의 실제 물리 응답은 아직 실행 검증하지 않았습니다.
