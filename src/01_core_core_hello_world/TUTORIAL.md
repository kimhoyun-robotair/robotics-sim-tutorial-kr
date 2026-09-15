# 01. 처음 만드는 물리 세계: 낙하하는 큐브 살펴보기

## 이번에 배우는 것

**큐브를 떨어뜨리고 매 물리 단계의 위치와 속도를 기록하며, World의 초기화와 콜백이 어떻게 연결되는지 배웁니다.**

00번에서 큐브에 강체와 충돌 속성을 붙였습니다. 이번에는 움직이는 모습을 보는 데서 한 걸음 더 나아가, 얼마나 내려왔고 얼마나 빠르게 움직이는지 숫자로 읽습니다. 한 변이 0.5 m인 파란 큐브를 중심 높이 1 m에서 떨어뜨립니다.

| 코드 속 이름 | 이 실습에서 맡은 역할 |
|---|---|
| `SimulationApp` | Isaac Sim 앱과 확장을 시작하고 종료합니다. |
| `World` | 물리 시간, 객체 초기화, 콜백과 단계 진행을 관리합니다. |
| `world.scene` | Python 객체를 이름으로 등록해 관리합니다. |
| `/World/FallingCube` | USD 장면에서 큐브를 찾는 경로입니다. |
| `falling_cube` | Scene에 등록한 같은 큐브의 이름입니다. |
| `observe(step_size)` | 물리 단계 직전에 위치와 속도를 기록하는 함수입니다. |

Stage는 Prim과 속성을 담은 USD 장면 전체입니다. `World`는 그 장면을 시뮬레이션하는 데 필요한 Python 관리 객체입니다.

## 1. 큐브를 떨어뜨리고 기록하기

Isaac Sim 5.1과 지원 GPU·드라이버가 준비된 환경에서 실행합니다. 외부 로봇 자산은 필요하지 않습니다. 아래는 저장소 루트에서 실행하는 Linux 명령입니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/01_core_core_hello_world/run.py --steps 300
```

300 step이 끝나면 결과를 저장하고 앱이 종료됩니다. 창을 유지하려면 `--steps 300`을 빼세요. `--headless`를 추가하면 창 없이 실행하며, 이때 단계 수를 생략하면 마찬가지로 300 step입니다. Windows에서는 설치의 `python.bat`을 사용합니다.

### 코드에서 볼 부분

```python
world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
world.scene.add_default_ground_plane()
cube = world.scene.add(DynamicCuboid(
    prim_path="/World/FallingCube", name="falling_cube", size=0.5,
    position=np.array([0.0, 0.0, args.height]), color=np.array([0.1, 0.2, 0.9])))
world.reset()
```

`DynamicCuboid`는 큐브의 외형·강체·충돌을 함께 만듭니다. `scene.add()`는 이 Python 객체를 등록하고, `world.reset()`은 등록된 객체의 물리 상태를 다룰 준비를 합니다. **Stage Scene에 큐브를 작성한 시점과 물리 엔진에서 상태를 읽을 수 있는 시점은 구분해야 합니다.**

바로 뒤의 `assert World.instance() is world`는 현재 프로세스에서 조회한 World가 방금 만든 객체인지 확인합니다. 다른 함수에서 `World.instance()`를 호출해도 이 World에 접근할 수 있습니다.

### 실행 결과 확인하기

Stage에서 `/World/FallingCube`를 선택하고 `F`로 화면을 맞춰 보세요. 큐브가 낙하한 뒤 지면 위에 놓이는 흐름을 관찰합니다. 터미널에는 60번의 반복마다 `position_m`과 `velocity_mps`가 출력됩니다.

결과 파일은 이 폴더의 `output/고유번호/`에 생깁니다.

| 결과 | 읽을 부분 | 기본 실행의 기대 흐름 |
|---|---|---|
| `fall.csv` | `z_m`, `vz_mps` | 높이가 감소하고, 낙하 중 수직 속도가 음수가 됩니다. |
| `fall.csv` | `time_s` | 실제 시계가 아닌 시뮬레이션 시간을 나타냅니다. |
| `result.json` | `samples` | 300단계를 완료하면 관찰값이 300개입니다. |
| `result.json` | `final_position_m[2]` | 충분히 정착하면 약 0.25 m입니다. |
| `result.json` | `final_velocity_mps` | 정착 후 각 성분이 0 근처로 줄어듭니다. |

큐브 중심이 0까지 내려가지 않는 이유는 크기 때문입니다. 한 변이 0.5 m이므로 바닥에 놓인 중심은 **0.5 ÷ 2 = 0.25 m** 높이에 있습니다. 접촉 계산의 작은 오차는 있을 수 있습니다.

## 2. 물리 콜백은 언제 값을 읽을까요?

`run.py`에서 `observe()`와 그 아래 반복문을 함께 읽어 보세요. 관찰하는 함수와 물리를 진행시키는 코드가 서로 다른 곳에 있습니다.

### 코드에서 볼 부분

```python
def observe(step_size):
    nonlocal sample_count
    position, quaternion = cube.get_world_pose()
    velocity = cube.get_linear_velocity()
    writer.writerow([world.current_time, *position.tolist(), *velocity.tolist()])
    sample_count += 1

world.add_physics_callback("observe_fall", callback_fn=observe)
```

`get_world_pose()`는 월드 위치와 회전을 반환합니다. 여기서는 위치의 x·y·z만 CSV에 기록합니다. 회전은 `[w, x, y, z]` 순서의 쿼터니언이며 세 축의 각도 배열과 다릅니다. `get_linear_velocity()`는 실제 선속도를 m/s 단위로 읽습니다.

`step_size`는 이번 물리 간격이지만, 이 코드는 시간 열에 `world.current_time`을 사용합니다. `nonlocal`은 함수 바깥의 `sample_count`를 갱신하기 위해 필요합니다. `*position.tolist()`는 세 위치 성분을 각각 CSV 열로 펼칩니다.

콜백 등록 다음의 반복문이 `world.step(render=not args.headless)`를 호출합니다. 콜백 등록만 하고 코드 진행을 멈추면 관찰값도 더 이상 쌓이지 않습니다.

### 실행 결과 확인하기

```text
world.step() 시작
    → observe()가 이번 물리 계산 전의 상태를 CSV에 기록
    → 물리 계산으로 위치·속도 갱신
    → world.step() 반환
    → 필요하면 터미널에 갱신된 상태 출력
```

CSV 마지막 행과 JSON의 최종 위치가 조금 달라도 곧바로 오류라고 판단하지 마세요. CSV는 마지막 물리 단계 **직전**, `result.json`은 마지막 단계가 **끝난 후**의 값입니다. 아직 낙하 중인 짧은 실행에서 이 차이가 더 잘 보입니다.

관찰이 끝나면 `remove_physics_callback("observe_fall")`로 등록을 해제합니다. 파일을 닫은 후에도 콜백이 그 파일에 기록하려는 일을 막는 순서입니다.

## 3. 장면 생성부터 관찰까지 정리

```text
앱 시작 → World 생성 → 큐브를 Scene에 등록 → reset으로 초기화
       → 콜백 등록 → step 반복 → 콜백 해제 → 최종 상태 저장 → 앱 종료
```

300단계의 물리 시간은 **300 × 1/60 = 5초**입니다. 앱 시작과 화면 그리기에 걸린 실제 시간은 여기에 포함되지 않습니다. 높이만 보면 낙하 여부를 알 수 있고, 속도까지 읽으면 낙하 중인지 접촉 후 진정되는 중인지 구분할 수 있습니다.

## 4. 간단한 확인 실험

단계 수만 300에서 10으로 바꿔 실행해 보세요.

```bash
~/isaacsim/python.sh src/01_core_core_hello_world/run.py --steps 10
```

물리 진행 시간은 약 0.167초입니다. 기본 높이에서는 아직 낙하 중이므로 최종 높이가 0.25 m보다 높고 수직 속도가 음수일 것으로 예상할 수 있습니다. `samples`가 10인지 확인한 다음 CSV 마지막 행과 JSON의 최종 높이를 비교하세요.

## 실행할 때 막히면

- **`No module named isaacsim`**: 설치의 `python.sh`로 실행하세요. 일반 Python의 `--help`는 옵션만 확인하며 앱을 시작하지 않습니다.
- **큐브를 찾기 어려움**: Stage에서 `/World/FallingCube`를 선택한 뒤 `F`로 화면을 맞추세요.
- **바닥에 도달하기 전에 종료됨**: 정착을 보려면 `--steps 300`으로 다시 실행하세요.
- **출력 폴더가 이미 있다는 오류**: `--output`은 새 경로만 받습니다. 옵션을 생략하거나 존재하지 않는 폴더를 지정하세요.
- **Stop/Play 후 상태가 예상과 달라짐**: 이 파일은 GUI 리셋 조작을 별도로 처리하지 않습니다. 초기 상태부터 비교하려면 프로그램을 다시 실행하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)에 대응합니다. 원문의 World 공유, 객체 등록, 물리 콜백, 독립 실행 개념을 한 낙하 실험으로 연결했습니다. CSV와 최종 JSON 기록은 이 폴더의 학습용 구성입니다.

`tutorial.json`에는 120개 표본과 중심 높이 약 0.25 m를 확인한 부분 실행 기록이 있습니다. 위 300단계·10단계의 값은 실행 시 확인할 기준이며, 기존 기록이 다른 실행 길이와 GUI 조작까지 검증한 것은 아닙니다.
