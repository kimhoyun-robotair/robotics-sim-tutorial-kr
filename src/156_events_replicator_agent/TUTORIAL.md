# 156. 사람의 행동이 영상과 주석이 되기까지

## 이번에 배우는 것

**창고에 사람 두 명과 카메라 한 대를 배치하고, 행동 명령이 RGB 영상과 객체 주석으로 기록되는 과정을 따라갑니다.**

사람이 보이는 장면을 학습 데이터로 사용하려면 “어느 영상에 누가 보이는가”도 남겨야 합니다. Actor SDG는 장면과 행동을 구성하고, writer는 카메라가 본 영상과 객체 정보를 저장합니다. 이번에는 기본 자세 변화를 먼저 관찰하고 그 사람을 주석에서 찾아봅니다.

| 파일·설정 | 이번 실습에서 맡는 일 |
|---|---|
| `lesson.json` | 창고, 사람 수, 카메라 수, writer를 선택합니다. |
| `character_commands.txt` | 두 사람이 수행할 행동과 시간을 적습니다. |
| `prepare.py` | 경로를 채워 실행용 `config.yaml`을 만듭니다. |
| `IRABasicWriter` | RGB, 카메라 정보, 객체의 2D 경계 상자를 저장합니다. |
| `run_scheduler.py` | 준비한 설정을 설치본의 배치 실행기에 전달합니다. |

기본 명령은 `Idle`과 `LookAround`입니다. 사람이 걷지 않더라도 고개와 자세가 명령에 맞게 바뀌는지 확인할 수 있습니다.

## 1. 설정을 만들고 Actor SDG에서 실행하기

Isaac Sim 5.1, RTX GPU와 호환 드라이버, 5.1 Assets 접근이 필요합니다. 아래 명령은 저장소 루트에서 실행합니다. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
python3 src/156_events_replicator_agent/prepare.py --output src/156_events_replicator_agent/output/run_01 --frames 90
~/isaacsim/isaac-sim.sh
```

첫 명령은 설정을 만든 뒤 종료합니다. 화면을 열거나 영상을 생성하지 않습니다. 출력 폴더는 새 경로여야 합니다. 오프라인 자산팩을 사용한다면 `--assets-root /절대경로/Assets/Isaac/5.1`을 추가하세요.

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화하고 필요한 재시작을 마칩니다.
2. **Tools > Action and Event Data Generation > Actor SDG**를 열고 **Config File Path**에서 생성한 `output/run_01/config.yaml`을 선택합니다.
3. Scene의 `Simple_Warehouse/full_warehouse.usd`에 NavMesh가 준비되어 있는지 확인합니다. NavMesh는 사람이 서거나 이동할 수 있는 바닥 영역입니다. 없으면 창고를 열어 **Create > Navigation > NavMesh Include Volume**으로 바닥을 덮고, **Window > Navigation > NavMesh**에서 Bake하세요. 새 USD로 저장해 **Scene > Asset Path**에 지정하고 설정을 저장합니다.
4. **Set Up Simulation**을 누르고 자산 로딩을 기다립니다. Character 탭과 `/World/Characters`의 실제 이름을 확인해 명령의 `Character_01`, `Character_02`와 맞춥니다.
5. **Save Commands**, 설정 **Save**, **Start Data Generation** 순서로 실행합니다.

90프레임의 생성이 끝나도 GUI는 남습니다. 저장이 끝난 뒤 창을 직접 닫으세요. 30 FPS에서 90프레임은 시뮬레이션 시간 3초이며 자산 로딩을 포함한 실제 대기 시간과 다릅니다.

### 설정에서 볼 부분

```text
character.num = 2                         → 장면에 사람 두 명
sensor.camera_num = 1                     → 촬영 카메라 한 대
character.command_file                   → 사람별 행동 순서
replicator.parameters.output_dir         → 촬영 결과 저장 위치
object_info_bounding_box_2d_tight = true   → 객체의 영상 속 경계 상자
```

`prepare.py`는 `{ASSETS}`를 자산 루트로, `{OUTPUT}`을 새 출력 폴더의 절대 경로로 치환합니다. 생성된 `config.yaml`은 JSON 문법으로 쓴 YAML 1.2 문서입니다. `version: 0.7.0`은 IRA 설정 형식의 버전이며 Isaac Sim 5.1.0과 구분합니다.

### 실행 결과 확인하기

실제 주석은 `capture/<카메라ID>/object_detection/object_detection_<sequence><frame>.json`에 저장됩니다. 카메라 ID는 Prim 경로의 `/`를 `_`로 바꾼 이름이며 RGB도 같은 카메라 아래의 `rgb/`에서 찾습니다. 파일명의 프레임 번호를 맞추고 JSON의 `agents` 안에서 해당 사람의 Prim 경로·id·상자 정보를 읽으세요.

`output/run_01/capture`의 RGB와 같은 프레임 `object_detection_*.json`을 비교하세요.

| 관찰 대상 | 읽는 방법 |
|---|---|
| Character_01 | 처음 1초는 Idle, 이어서 2초는 LookAround입니다. |
| Character_02 | 3초 동안 LookAround를 수행합니다. |
| RGB | 몸 위치가 거의 고정되어도 얼굴·자세 변화가 있는지 봅니다. |
| 객체 주석 | actor id와 bbox가 해당 영상의 사람과 대응하는지 봅니다. |

**사람 수 2와 매 프레임의 bbox 수 2는 같은 조건이 아닙니다.** 카메라 밖에 있거나 가려진 사람의 주석 포함 상태는 달라질 수 있습니다. 설정만 만든 상태에는 RGB가 아직 없습니다.

## 2. 행동 명령과 배치 실행 연결하기

### 코드에서 볼 부분

```text
Character_01 Idle 1
Character_01 LookAround 2
Character_02 LookAround 3
```

첫 항목은 행동할 사람, 두 번째는 명령, 마지막은 지속 시간(초)입니다. 파일의 모든 줄을 한 사람이 읽는 것이 아니라 각 사람에게 해당 명령을 나눠 전달합니다.

보행을 추가하려면 Character 탭의 **Generate Random Commands**를 사용하고 생성된 `GoTo x y z yaw`를 읽어 보세요. 목적지가 NavMesh 위인지 확인한 뒤 저장합니다. `Idle 2`의 2는 시간이고 `GoTo 2 0 0 _`의 2는 X 좌표입니다. `_`는 도착 방향을 강제하지 않는 자리입니다.

GUI에서 장면과 명령을 확인했다면 배치 실행도 가능합니다. 다음은 새 설정을 만드는 명령입니다. GUI에서 준비한 NavMesh 장면 경로와 명령을 이 설정에도 반영한 뒤 scheduler를 실행하세요.

```bash
python3 src/156_events_replicator_agent/prepare.py --output src/156_events_replicator_agent/output/batch_01 --frames 90
python3 src/156_events_replicator_agent/run_scheduler.py --isaac-root ~/isaacsim --config src/156_events_replicator_agent/output/batch_01/config.yaml --save-usd
```

래퍼는 설치된 `tools/actor_sdg/sdg_scheduler.py`에 설정을 전달하고 `--save-usd`를 `--save_usd`로 바꿉니다. 완료 후 실제 RGB·주석과 저장된 setup USD를 확인하세요. 래퍼 호출 자체가 NavMesh 준비 문제를 해결하지는 않습니다.

로봇도 비교하려면 새 출력 설정에서 `robot.nova_carter_num`을 1로 바꾸고 다시 Setup하세요. 기본값 0에서는 로봇 명령 파일이 있어도 로봇이 생기지 않습니다. Robot 탭의 실제 이름을 확인한 뒤 다음처럼 명령을 넣고 **Save Commands → Save → Start Data Generation**으로 진행합니다.

```text
Nova_Carter_01 Idle 2
Nova_Carter_01 GoTo 2 0 0
```

목적지 `(2,0,0)` m가 NavMesh 위인지 먼저 확인하세요. 사람의 GoTo와 달리 로봇 명령에는 마지막 yaw 인수가 없습니다. 이동 전체를 보려면 관찰 프레임 수를 늘릴 수 있습니다. `robot.write_data: true`는 로봇 자체 카메라 기록을 추가하는 설정이므로 창고 카메라의 `rgb`와 별도로 선택합니다.

## 3. 장면·행동·저장 흐름 정리

```text
창고 USD + NavMesh + 사람 자산
    → Setup으로 사람과 카메라 배치
    → 사람 이름에 맞는 명령 실행
    → 카메라가 장면 관찰
    → writer가 RGB와 해당 프레임 주석 저장
```

같은 동작도 카메라가 달라지면 영상과 bbox가 달라집니다. writer를 바꿔도 사람의 명령 자체는 바뀌지 않습니다. 문제가 생겼을 때 장면, 행동, 저장 중 어느 연결이 끊겼는지 나누어 보세요.

## 4. 간단한 확인 실험

새 출력에서 `--frames 90`만 `--frames 180`으로 바꿔 보세요. 나머지 설정과 명령은 유지합니다.

- 30 FPS를 유지하면 생성 구간은 3초에서 6초가 됩니다.
- 출력의 마지막 프레임 번호와 RGB 수를 비교하세요.
- 기본 명령은 여전히 3초 분량입니다. 기록 구간을 늘리는 것과 새로운 행동을 추가하는 것이 별개임을 확인합니다.

## 실행할 때 막히면

- **Setup에서 자산을 찾지 못함**: `scene.asset_path`, `character.asset_path`의 5.1 자산이 Content Browser에서 열리는지 확인하세요. 로컬 자산 루트에는 `Isaac` 하위 폴더가 있어야 합니다.
- **사람이 걷지 않음**: 기본 명령에 GoTo가 없습니다. 보행 명령을 넣었다면 실제 사람 이름, NavMesh, Save Commands 순서로 확인하세요.
- **RGB에 사람이 있지만 주석이 없음**: 같은 프레임을 비교하고 semantic filter `class:character|robot;id:*`에 필요한 class와 id가 있는지 확인하세요.
- **출력 경로 오류**: `prepare.py`는 기존 폴더를 거부합니다. 새 이름으로 실행하세요.
- **배치 실행 실패**: 설치 루트 아래 `python.sh`, `tools/actor_sdg/sdg_scheduler.py`와 설정 내부의 Scene·명령 파일 경로를 확인하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Actor Simulation and Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html)에 대응합니다. 공식 GUI와 scheduler를 사용하고, 로컬 코드는 설정 생성과 실행 인수 전달을 담당합니다.

두 사람의 짧은 명령과 90프레임 구성은 기록 과정을 이해하기 위한 실습 설정입니다. `tutorial.json`은 `not_run`이며 영상·주석 설명은 실행 시 확인할 기준입니다. 설정 생성 성공을 GPU 데이터 생성 완료로 보지 않습니다.
