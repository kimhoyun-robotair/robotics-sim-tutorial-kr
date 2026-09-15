# 167. 한 번 기록한 주행에서 여러 센서 데이터를 만들기

## 이번에 배우는 것

**실제 로봇 궤적을 기록하고, 저장한 상태를 다시 불러 RGB·segmentation·depth를 생성합니다.**

주행과 렌더링을 분리하면 같은 움직임을 유지한 채 센서 종류나 영상 간격을 바꿀 수 있습니다. 먼저 창고의 이동 영역 지도를 만들고 H1을 움직여 기록합니다. 그 기록을 재생해 같은 자세의 여러 센서 결과를 비교합니다.

| 파일·단계 | 입력 | 결과 |
|---|---|---|
| Occupancy Map GUI | 실제 창고 Stage | 지도 PNG와 YAML |
| `prepare_map.py` | GUI에서 내보낸 두 파일 | `map.png`, `map.yaml` |
| MobilityGen 기록 | 지도·장면·로봇·조작 | 상태가 담긴 recording 폴더 |
| `inspect_recording.py` | 단일 recording | 상태 수와 step 범위 |
| `replay.py` | 같은 recording | 센서 파일과 `summary.json` |

`map_recipe.json`은 지도 생성에 사용할 설정을 적어 둔 파일입니다. 지도나 주행 기록 자체를 포함하지 않습니다.

## 1. 지도를 만들고 H1 주행 기록하기

Isaac Sim 5.1, RTX GPU, `isaacsim.replicator.mobility_gen`, `.examples`, `.ui` 확장과 5.1 창고·H1 정책 자산이 필요합니다. ROS 프로세스는 사용하지 않습니다. “ROS map YAML”은 여기서 파일 형식의 이름입니다.

저장소 루트에서 `~/isaacsim/isaac-sim.sh`를 실행하고 필요한 확장을 활성화하세요. Content Browser에서 다음 창고를 엽니다.

```text
https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd
```

1. **Tools > Robotics > Occupancy Map**에서 Origin=`(2,0,0)`, Upper Bound=`(10,20,2)`, Lower Bound=`(-14,-18,0.1)`을 넣습니다. 숫자 칸은 Ctrl+왼쪽 클릭으로 직접 입력할 수 있습니다.
2. **Calculate → Visualize Image**를 누릅니다. Rotate Image=`180`, Coordinate Type=`ROS Occupancy Map Parameters File YAML`로 선택하고 **Regenerate Image**를 누릅니다.
3. 표시된 YAML과 **Save Image**의 PNG를 이 폴더의 `output/exported_map.yaml`, `output/exported_map.png`로 저장합니다. 없는 출력 폴더는 먼저 만드세요.
4. 저장소 루트 터미널에서 실제 export를 묶습니다.

```bash
~/isaacsim/python.sh src/167_sdg_extra_replicator_mobility_gen/prepare_map.py --yaml src/167_sdg_extra_replicator_mobility_gen/output/exported_map.yaml --image src/167_sdg_extra_replicator_mobility_gen/output/exported_map.png --output src/167_sdg_extra_replicator_mobility_gen/output/maps/warehouse
```

### 설정에서 볼 부분

`prepare_map.py`는 지도 계산기가 아닙니다. YAML의 양수 `resolution`, 세 값의 `origin`, PNG 파일 서명을 검사하고 이미지 이름을 `map.png`로 맞춥니다.

- `resolution`: 지도 한 픽셀이 나타내는 거리(m/pixel)
- `origin`: 지도 기준 위치 X·Y와 회전 yaw
- Z 범위 0.1~2 m: 지도 계산에 포함할 높이 구간

0.1 m 아래를 제외했다는 사실만으로 로봇이 그 높이의 턱을 넘을 수 있다고 보장하지는 않습니다. 지도와 실제 통과 가능성은 장면에서 함께 확인해야 합니다.

이제 MobilityGen UI에서 Stage에 위 창고 URL, Occupancy Map에 생성된 `map.yaml`의 **절대 경로**를 넣습니다. Robot=`H1Robot`, Scenario=`KeyboardTeleoperationScenario`를 선택하고 **Build**하세요. W로 전진하고 A·D로 회전하며 지도의 통로와 로봇 위치가 맞는지 봅니다.

**Start recording**을 누르고 약 10초 이동한 뒤 **Stop recording**합니다. 기본 위치는 `~/MobilityGenData/recordings`입니다. 앱 실행 전에 `MOBILITY_GEN_DATA`를 설정하면 저장 루트를 바꿀 수 있습니다.

### 실행 결과 확인하기

실제 생성된 **단일 기록 폴더**를 확인합니다. 상위 `recordings` 폴더를 넣지 마세요.

```bash
python3 src/167_sdg_extra_replicator_mobility_gen/inspect_recording.py /절대경로/MobilityGenData/recordings/기록폴더
```

`state_count`, `first_step`, `last_step`을 읽고 `config.json`, `stage.usd`, `occupancy_map/`, `state/common/*.npy`가 있는지 확인하세요. 검사기는 config 필드와 상태 파일을 조사하지만 실제 로봇이 이동했는지까지 판정하지 않습니다. GUI에서 이동을 관찰한 기록과 함께 판단합니다.

## 2. 같은 기록을 센서 데이터로 재생하기

기록 저장을 마치고 GUI를 닫은 뒤 다음 명령을 저장소 루트에서 실행합니다. 재생 명령은 별도의 Isaac Sim 앱을 시작합니다.

```bash
~/isaacsim/python.sh src/167_sdg_extra_replicator_mobility_gen/replay.py --input /절대경로/MobilityGenData/recordings/기록폴더 --output src/167_sdg_extra_replicator_mobility_gen/output/replay_01 --headless --frames 30 --render-interval 40 --segmentation --depth
```

RGB는 기본으로 켜져 있습니다. 위 명령은 RGB·segmentation·depth를 모두 저장합니다. Headless에서는 저장이 끝나면 종료합니다. GUI 실행은 저장 후 마지막 장면을 유지하며, `--steps 120`을 추가하면 **저장 이후 앱 업데이트 120회** 뒤 종료합니다. 이 옵션은 촬영 표본 수를 늘리지 않습니다.

### 코드에서 볼 부분

표본 선택은 다음 한 줄에서 결정합니다.

```python
indices = list(range(0, len(reader), args.render_interval))[:args.frames]
```

`--render-interval 40`은 기록 **인덱스** 0, 40, 80, …을 고릅니다. 40초 간격도 아니고 원본 step ID가 반드시 40씩 차이 난다는 뜻도 아닙니다. 원본 기록이 짧으면 최대 개수 `--frames 30`을 채우지 못할 수 있습니다.

각 표본에서는 저장한 상태를 불러오고 로봇·센서에 적용합니다.

```python
original = reader.read_state_dict(index=index)
scenario.load_state_dict(original)
scenario.write_replay_data()
```

그 뒤 `rep.orchestrator.step(..., delta_time=0.0, ...)`으로 지정한 자세를 렌더링합니다. writer에 전달하는 번호는 `reader.steps[index]`이므로 출력 이름에는 원본의 실제 step ID를 보존합니다. 재생 영상과 원래 상태를 연결할 수 있는 이유입니다.

### 실행 결과 확인하기

| `summary.json` 필드 | 의미 |
|---|---|
| `recorded_steps` | 읽을 수 있는 원본 상태 개수 |
| `rendered_samples` | 이번에 선택해 렌더링한 표본 개수 |
| `source_step_ids` | 출력과 대응하는 원본 step ID |
| `sensor_file_counts` | 선택한 센서 형식별 실제 파일 수 |

같은 step ID의 RGB·segmentation·depth를 열어 같은 자세와 장면인지 비교하세요. 카메라가 여러 대면 센서 파일 수가 표본 수보다 많을 수 있습니다. 선택한 형식에서 파일이 하나도 생기지 않으면 스크립트는 오류를 냅니다. 양수 파일 수만으로 모든 이미지 내용이 올바르다고 보증하지는 않습니다.

depth는 16-bit PNG의 역깊이 표현입니다. 설치본 writer는 대략 `65535 / (1 + depth)`를 저장하므로 픽셀 정수를 미터 거리로 읽으면 안 됩니다. 설치본 `MobilityGenReader.read_depth()`의 역변환을 사용하세요. RGB는 JPG, segmentation·depth는 PNG, `--normals`로 추가한 법선은 NPY로 기록합니다.

### 자동 주행과 사용자 로봇으로 확장하기

UI에서 `RandomPathFollowingScenario`를 선택해 Build해도 **Start recording**을 눌러야 데이터가 남습니다. episode가 바뀌면 새 기록이 생길 수 있으므로 재생할 단일 기록을 확인하세요. `RandomAccelerationScenario`는 선속도·각속도의 변화량을 무작위로 적용하는 다른 자동 주행 방식입니다. 같은 지도에서 이 Scenario를 선택해 Build하고 Start/Stop recording한 뒤, 지도 안의 시작 위치·충돌·종료 시점과 기록 폴더를 확인합니다. 경로 추종과 무작위 가속 기록을 같은 주행으로 섞지 말고 단일 recording씩 재생하세요.

`custom_robot.py`는 JetbotRobot을 상속한 `TutorialSlowJetbot`을 등록합니다. keyboard·gamepad 선속도 gain과 경로 속도를 0.12로 설정합니다. MobilityGen Examples 활성화 후 Script Editor에서 실행하고 UI 목록을 갱신하세요. 이 로봇의 recording을 재생할 때는 `--custom-robot`으로 같은 클래스를 등록합니다. Jetbot USD는 외부 5.1 자산입니다.

완전히 새로운 로봇을 연결한다면 `MobilityGenRobot`의 `build()`에서 로봇·센서를 구성하고 `write_action()`에서 선속도·각속도를 실제 actuator 명령으로 변환해야 합니다. 바퀴 반지름·축간 거리, `physics_dt`, `occupancy_map_radius`, 전방 카메라의 위치·회전을 모델과 대조하세요. 관찰용 chase camera와 지도 충돌 반경은 역할이 다릅니다. 등록은 실제 API인 `ROBOTS.register()`로 수행하며, 이름만 등록한다고 이런 물리·센서 연결이 자동 작성되지는 않습니다.

## 3. 기록 간격과 렌더링 간격 정리

```text
실제 지도 + 주행 → 매 시점의 상태 기록
같은 recording → 일부 인덱스 선택 → 상태 복원 → 센서 렌더링
```

기록을 새로 만들면 로봇 궤적도 바뀔 수 있습니다. 렌더링 설정만 비교하려면 원본 recording을 유지해야 합니다. `--subframes`는 한 표본의 렌더링 품질을 위한 갱신 횟수이며 궤적 표본 간격과 별개입니다.

## 4. 간단한 확인 실험

**같은 recording**에서 `--render-interval 40`만 `20`으로 바꾸고 새 출력으로 재생하세요. 최대 표본 수는 30으로 유지합니다.

- `source_step_ids`와 영상에서 연속 표본 사이 자세 변화가 더 촘촘해지는지 봅니다.
- 기록이 충분히 길면 두 실행 모두 30표본일 수 있습니다. 이때는 수보다 포함한 궤적 범위가 달라집니다.
- 기록이 짧다면 간격 20에서 표본 수가 늘 수 있습니다. `rendered_samples`로 실제 선택 결과를 확인하세요.

## 실행할 때 막히면

- **지도 위치나 방향이 틀림**: export 회전 180과 YAML의 origin·resolution을 확인하세요. PNG만 교체하고 이전 YAML을 사용하지 않습니다.
- **기록 상태가 0개**: Build 후 Start/Stop recording을 실제로 수행했는지 확인하세요.
- **`Recording lacks ...`**: `config.json`이 바로 들어 있는 단일 기록을 입력했는지 확인하세요. 지도·Stage도 함께 보존해야 합니다.
- **30표본보다 적게 생성됨**: 원본 길이와 인덱스 간격을 확인하세요. `--frames`는 최소 개수가 아니라 최대 개수입니다.
- **사용자 로봇을 찾지 못함**: `TutorialSlowJetbot` 기록에는 재생 시 `--custom-robot`을 추가하세요.
- **재생 후 화면이 멈춤**: 저장 완료 뒤 마지막 자세를 유지하는 정상 동작일 수 있습니다. GUI를 오래 열어도 새 주행이나 센서 표본이 추가되지는 않습니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Data Generation with MobilityGen](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html)에 대응합니다. 로컬 도구는 실제 지도 export를 정리하고 단일 recording을 검사·재생합니다. depth 해석은 설치본 reader·writer와 대조했습니다.

`tutorial.json`은 `not_run`입니다. 실제 지도와 recording을 이 폴더에 제공하지 않으므로 GUI 생성·주행·센서 재생을 별도로 수행해야 합니다. 파일 검사나 코드 읽기를 그 실행 성공으로 대신하지 않습니다.
