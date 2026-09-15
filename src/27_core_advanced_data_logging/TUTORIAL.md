# 27. 로봇에 보낸 명령과 실제 움직임을 기록하고 재생하기

## 이번에 배우는 것

**Franka가 움직이는 목표를 따라가는 동안 명령과 상태를 따로 기록하고, 두 재생 방식의 차이를 비교합니다.**

로봇에 관절 위치를 명령했다고 해서 그 순간 실제 관절이 목표 위치에 있는 것은 아닙니다. 모터 드라이브가 물리 계산을 거쳐 움직이기 때문입니다. 이번에는 `DataLogger`로 두 값을 함께 저장하고, 저장한 명령을 다시 적용했을 때 실제 상태가 얼마나 달라지는지 살펴봅니다.

| 모드 | 로봇에 적용하는 것 | 목표 물체의 움직임 |
|---|---|---|
| `record` | RMPflow가 계산한 관절 목표 | 코드가 y방향 사인파로 이동 |
| `trajectory` | 기록된 관절 목표 | 새 장면의 기본 위치 유지 |
| `scene` | 기록된 관절 목표 | 기록된 위치·자세 복원 |

`scene`도 이 실습에서 기록한 로봇 명령과 목표 물체만 복원합니다. 전체 USD 장면이나 모든 접촉·센서 상태를 저장하는 기능은 아닙니다.

## 1. 목표 추종을 기록하고 파일 읽기

Isaac Sim 5.1, 지원 NVIDIA GPU, Franka 에셋 `/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd`와 내장 Lula/RMPflow가 필요합니다. 저장소 루트에서 아래 명령을 실행하세요. `~/isaacsim`은 설치 경로입니다.

```bash
~/isaacsim/python.sh src/27_core_advanced_data_logging/run.py --mode record --steps 600 --output src/27_core_advanced_data_logging/output/record_a
python3 src/27_core_advanced_data_logging/inspect_log.py src/27_core_advanced_data_logging/output/record_a/trajectory.json
```

첫 명령이 끝난 뒤 두 번째 명령으로 실제 저장 파일을 읽습니다. `record_a`가 이미 있으면 새로운 이름을 사용하세요. `inspect_log.py`는 Python 표준 라이브러리만 사용하므로 일반 `python3`로 실행할 수 있습니다.

목표의 x·z는 0.45 m로 고정하고 y는 `0.1 * sin(step / 120)` m로 움직입니다. 600단계는 물리 간격 1/60초에서 약 10초입니다. 한 주기는 약 12.57초이므로 기본 기록이 정확히 사인파 한 주기는 아닙니다.

### 코드에서 볼 부분

기록 함수의 핵심은 현재 상태와 현재 명령을 서로 다른 키에 넣는 것입니다.

```python
return {"joint_positions": robot.get_joint_positions().tolist(),
        "applied_joint_positions": robot.get_applied_action().joint_positions.tolist(),
        "target_position": position.tolist(), "target_orientation": orientation.tolist()}
```

- `joint_positions`는 물리 상태에서 읽은 실제 관절 위치입니다.
- `applied_joint_positions`는 로봇에 보낸 관절 위치 목표입니다.
- `target_position`과 `target_orientation`은 팔이 따라가는 목표 물체의 pose입니다.
- `.tolist()`는 NumPy 배열을 JSON에 저장할 수 있는 목록으로 바꿉니다.

`logger.start()` 뒤에 물리를 진행하고, 기록할 반복을 마치면 `logger.pause()`와 `logger.save()`를 호출합니다. 수집을 멈추는 것과 이미 수집한 데이터를 파일로 저장하는 것은 별도의 동작입니다.

### 실행 결과 확인하기

`trajectory.json`의 최상위 `Isaac Sim Data` 배열이 시간순 프레임입니다. 검사기는 모든 프레임을 읽어 다음을 확인하고, 프레임 수·처음과 마지막 시각·첫 프레임을 출력합니다.

| 데이터 | 검사 기준 |
|---|---|
| `current_time` | 유한한 숫자이며 앞 프레임보다 큼, 단위 초 |
| `joint_positions`, `applied_joint_positions` | 각각 9개 숫자 |
| `target_position` | 3개 숫자, 단위 m |
| `target_orientation` | 쿼터니언 4개 숫자 |

9개 관절 값에는 회전하는 팔 관절과 직선 이동하는 손가락이 함께 들어 있습니다. 파일 구조가 정상이라고 추종 오차가 작다는 뜻은 아닙니다. 같은 프레임의 두 관절 배열을 비교해 명령과 실제 응답이 구분되어 기록되는지 보세요.

`result.json`의 record 결과에서 `replayed_frames=0`, `mean_joint_state_L2_error=null`은 정상입니다. 아직 재생을 수행하지 않았기 때문입니다.

## 2. 같은 로그를 두 방식으로 재생하기

앞에서 만든 로그를 그대로 사용합니다. 두 명령을 차례대로 실행해 목표 물체의 움직임을 비교하세요.

```bash
~/isaacsim/python.sh src/27_core_advanced_data_logging/run.py --mode trajectory --steps 600 --input src/27_core_advanced_data_logging/output/record_a/trajectory.json
~/isaacsim/python.sh src/27_core_advanced_data_logging/run.py --mode scene --steps 600 --input src/27_core_advanced_data_logging/output/record_a/trajectory.json
```

각 실행의 결과는 기본적으로 이 폴더의 새 `output/<고유번호>/`에 저장됩니다. trajectory에서는 팔이 기록된 명령을 따라가지만 목표 물체는 새 장면의 기본 위치에 남습니다. scene에서는 목표 물체도 기록된 경로를 따라 움직입니다.

### 코드에서 볼 부분

재생은 저장된 **측정 상태로 매번 순간이동**시키는 방식이 아닙니다. 처음에만 첫 프레임의 관절 위치를 설정하고, 이후에는 저장된 목표를 보냅니다.

```python
robot.apply_action(ArticulationAction(
    joint_positions=np.array(frame.data["applied_joint_positions"])))
```

scene 분기에서는 여기에 `target.set_world_pose()`를 추가합니다. 그 뒤 `world.step()`을 진행하고, 재생한 실제 관절 위치와 기록된 관절 위치의 차이를 측정합니다. 배열 인덱스는 0부터 순서대로 읽으며 프레임에 저장된 `current_time`도 콘솔에 별도로 표시합니다.

### 실행 결과 확인하기

`data_frames`는 입력 로그 전체 길이이고 `replayed_frames`는 이번에 실제 재생한 길이입니다. `--steps`가 더 작으면 둘은 달라집니다. 재생 중 출력되는 `joint_state_L2_error`와 결과의 `mean_joint_state_L2_error`는 관절 배열 차이의 크기이며, 손끝의 거리 오차(m)가 아닙니다. 회전 관절과 손가락 값이 섞이므로 하나의 물리 단위로 부르기도 어렵습니다.

GUI에서 `--steps`를 생략하면 record는 600단계만 저장하고 목표 추종을 계속합니다. 재생은 입력 전체를 한 번 재생한 뒤 창을 유지합니다. Headless는 생략 시 최대 600단계를 사용하므로 긴 로그를 모두 재생하려면 `--steps`를 명시하세요.

### 같은 기록 과정을 GUI에서 해보기

앞의 독립 실행을 종료한 뒤 `~/isaacsim/isaac-sim.sh`로 새 앱을 열면 공식 GUI 예제의 기록 과정도 비교할 수 있습니다.

1. **Window > Examples > Robotics Examples**에서 **Manipulation > Follow Target Task**를 선택합니다.
2. **LOAD**로 Franka와 목표 큐브를 만들고 Data Logging의 출력 경로를 새 JSON 파일로 지정합니다.
3. **FOLLOW TARGET**을 시작하고 **Start Logging** 항목의 **START**를 누른 뒤 목표 큐브를 움직입니다.
4. 같은 항목의 **PAUSE**로 기록을 멈추고 **Save Data**로 저장합니다. 저장 파일을 열어 `joint_positions`와 `applied_joint_positions`가 따로 있는지 확인하세요.

GUI 버튼도 DataLogger의 수집과 저장을 호출합니다. 차이는 목표를 손으로 움직이고 버튼으로 수집 구간을 선택한다는 점입니다. 설치된 5.1 GUI 예제의 기본 기록 함수는 `target_orientation`을 저장하지 않습니다. **이 폴더의 검사기와 scene 재생은 그 필드를 요구하므로, GUI에서 만든 JSON을 앞의 `trajectory.json` 대신 바로 넣지 마세요.** 재생 실습은 이 폴더의 record 결과로 진행하고 GUI 파일은 실제 필드를 비교하는 자료로 사용합니다.

## 3. 기록과 재생의 연결 정리

```text
기록: 목표 물체 → RMPflow 명령 → 물리 응답
                       └ 명령 + 실제 관절 상태 + 목표 pose 저장

재생: 저장된 명령 → 새 물리 응답 → 저장된 상태와 비교
      scene 모드에서는 목표 pose도 함께 복원
```

명령은 로봇에게 요청한 값이고, 상태는 그 요청 뒤 실제로 나타난 값입니다. 두 값을 함께 기록해야 재생 결과가 달라졌을 때 명령이 달라진 것인지, 물리 응답이 달라진 것인지 구분할 수 있습니다.

## 4. 간단한 확인 실험

기록 진폭만 0.1 m에서 0.05 m로 줄여 보세요.

```bash
~/isaacsim/python.sh src/27_core_advanced_data_logging/run.py --mode record --steps 600 --amplitude 0.05 --output src/27_core_advanced_data_logging/output/record_small
```

같은 프레임 번호에서 `target_position[1]`이 이전 기록의 절반이어야 합니다. x·z와 시간 간격은 그대로입니다. 손끝이나 관절 움직임까지 정확히 절반이라고 예상하지 마세요. 목표의 직선 이동을 관절 운동으로 바꾸는 과정과 물리 응답이 있기 때문입니다.

## 실행할 때 막히면

- **`Replay requires --input` 오류**: 이 폴더의 record 모드로 만든 `trajectory.json`을 지정하세요. `result.json`은 요약 파일이므로 재생 입력이 아닙니다.
- **검사기에서 길이 또는 시간 오류**: 이 예제는 9관절 Franka 로그를 기대합니다. 다른 예제의 JSON인지, 기록이 비어 있거나 필드가 누락되었는지 확인하세요.
- **독립 실행 기록에 같은 시각이 반복됩니다**: 기록 중 timeline을 Pause하면 물리 시간은 멈춰도 반복문의 logger 호출이 이어질 수 있습니다. 기본 record 비교에서는 Play를 유지하고 프로그램을 새로 실행해 기록하세요. GUI 예제의 Data Logging PAUSE와 물리 timeline Pause는 다른 조작입니다.
- **기록 중인데 프레임이 더 늘지 않음**: 기본 GUI는 600단계 후 logger를 pause하고 저장합니다. 이후 움직임은 추가로 기록하지 않습니다.
- **재생 오차가 0이 아님**: 처음 위치를 맞춰도 전체 물리 상태를 복원한 것은 아닙니다. 오차 추세와 명령·측정 배열을 비교하세요.

## 공식 문서와 실습 범위

Isaac Sim **5.1.0**의 [Data Logging](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_advanced_data_logging.html)에 대응합니다. 원문의 DataLogger 기록·조회·재생 흐름에 자동 목표 이동, 로그 검사기, 실제 재생 상태 비교를 구성했습니다.

[RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 2026-09-14의 기본 record headless 120단계 실행에서 120프레임 생성을 확인한 기록입니다. trajectory·scene 재생이나 추종 정확도의 검증은 포함하지 않습니다. 120프레임 결과는 당시 실행 조건의 기록이며, 현재 코드의 기록·재생을 다시 검증한 결과는 아닙니다.
