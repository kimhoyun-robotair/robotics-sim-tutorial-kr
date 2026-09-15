# 167. MobilityGen으로 이동 궤적을 기록하고 센서 영상을 재생성하기

권장 학습 순서 **167** · 병렬 환경과 학습 정책 활용 · 출처 ID `t076`

## 기대 결과와 준비

H1 로봇을 키보드로 이동시켜 실제 궤적을 기록하고 같은 기록을 RGB·segmentation·depth로 다시 렌더링합니다. Occupancy Map은 평면에서 막힌 칸/이동 가능한 칸을 표현하며 이동 경로 선택과 충돌 종료에 쓰입니다. 궤적 기록과 센서 렌더링은 두 단계로 분리됩니다.

Isaac Sim 5.1 GUI, RTX GPU, `isaacsim.replicator.mobility_gen`, `isaacsim.replicator.mobility_gen.examples`, `isaacsim.replicator.mobility_gen.ui`가 필요합니다. H1/Spot은 설치된 `isaacsim.robot.policy.examples`의 보행 policy와 robot Assets에 접근할 수 있어야 합니다. 창고는 다음 5.1 Assets 파일입니다.

`https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd`

별도 ROS 프로세스는 필요 없습니다. ROS map YAML은 파일 형식 이름입니다. 클라우드 LLM도 사용하지 않습니다. 샘플 map이나 recording을 가짜 데이터로 대체하지 않으므로 첫 GUI 기록 작업은 반드시 수행합니다. 아래 명령은 이 패키지 디렉터리에서 실행하고 설치 경로를 맞춥니다.

## Occupancy Map을 실제 장면에서 생성

1. `./isaac-sim.sh`로 GUI를 실행하고 `Window > Browsers > Content`에서 창고 USD를 엽니다. `Tools > Robotics > Occupancy Map`을 엽니다.
2. Origin=(2,0,0), Upper Bound=(10,20,2), Lower Bound=(-14,-18,0.1)을 입력합니다. ctrl+왼쪽 클릭으로 숫자 입력 모드를 활성화합니다. 0.1 m 이하의 바닥 주변 형상과 2 m보다 높은 구조물을 지도 범위에서 제외하는 선택입니다. 이를 로봇의 실제 통과 가능 높이/턱 넘기 능력으로 검증해야 합니다. 원문은 lower bound 0.1을 주면서 5 cm 예를 들므로 두 값을 동일시하지 않습니다.
3. Calculate → Visualize Image를 누릅니다. Rotate Image=180, Coordinate Type=`ROS Occupancy Map Parameters File YAML`, Regenerate Image로 설정합니다. `map_recipe.json`은 이 값을 모아둔 실습 기록이며 생성된 지도 자체가 아닙니다.
4. 표시된 YAML을 `output/exported_map.yaml`로 저장하고 Save Image로 `output/exported_map.png`를 저장합니다. 픽셀 데이터를 직접 생성하거나 임의 origin/resolution을 넣지 않습니다. 아래 명령은 실제 export를 검사하고 image 이름만 map.png로 맞춥니다.

```bash
/home/hoyunkim/isaacsim/python.sh prepare_map.py --yaml output/exported_map.yaml --image output/exported_map.png --output output/maps/warehouse
```

PyYAML은 Isaac Sim Python에 포함되어 있습니다. 표준 Python에서는 설치 환경에 따라 별도 설치가 필요할 수 있으므로 위 실행기를 사용합니다. `output/maps/warehouse/map.yaml`과 `map.png`가 생겨야 합니다. origin은 이미지의 지리적 시작 위치(x,y,yaw), resolution은 m/pixel이며 장면의 USD 좌표와 맞아야 합니다.

## 키보드로 기록하기

1. Window > Extensions에서 MobilityGen UI를 켭니다. MobilityGen 창과 지도 창이 겹쳐 있으면 분리합니다.
2. Stage에 위 창고 URL, Occupancy Map에 생성한 map.yaml의 **절대 경로**를 넣습니다. Robot=H1Robot, Scenario=KeyboardTeleoperationScenario를 선택하고 Build합니다.
3. W=전진, A=좌회전, S=후진, D=우회전을 시험합니다. H1이 바닥 위에 서 있고 occupancy map의 위치가 맞는지 확인합니다. 정책/자산이 로드되지 않으면 정상 보행으로 간주하지 않습니다.
4. Start recording을 누르고 10초 정도 다른 위치로 이동한 뒤 Stop recording합니다. 기본 저장소는 `~/MobilityGenData/recordings`입니다. 앱 실행 전 `MOBILITY_GEN_DATA`를 이 패키지 `output/data` 절대 경로로 설정하면 기록을 패키지 안에 모을 수 있습니다.
5. 실제 생긴 단일 기록 폴더를 아래 inspector로 확인합니다. config.json, stage.usd, occupancy_map, state/common이 있어야 합니다. state 파일 수가 늘었다는 검사와 실제 로봇 이동 관찰을 함께 수행합니다.

```bash
python3 inspect_recording.py /절대경로/MobilityGenData/recordings/기록폴더
```

## 같은 궤적에서 센서를 재생성

```bash
/home/hoyunkim/isaacsim/python.sh replay.py --input /절대경로/MobilityGenData/recordings/기록폴더 --output output/replay_01 --headless --frames 30 --render-interval 40 --segmentation --depth
```

이 스크립트는 공식 `standalone_examples/replicator/mobility_gen/replay_directory.py`의 실제 MobilityGen API 흐름을 한 recording으로 한정해 구현합니다. `load_scenario()`가 저장된 stage/map/robot 설정을 복원하고 `MobilityGenReader.read_state_dict()`가 당시 상태를 읽습니다. `scenario.load_state_dict()`와 `write_replay_data()` 후 `rep.orchestrator.step(delta_time=0)`으로 시간을 추가 진행하지 않고 해당 자세를 렌더합니다. `MobilityGenWriter`는 common state와 센서별 파일을 저장합니다. 외부 공통 튜토리얼 코드는 사용하지 않습니다.

`--steps`를 생략한 GUI 실행은 정해진 재생·저장이 끝난 뒤에도 마지막 장면을 유지하며, 사용자가 창을 닫으면 종료합니다. `--steps 120`은 저장 후 GUI 업데이트 120회 뒤 종료하며 생성 샘플 수를 늘리지 않습니다. `--headless`는 저장이 끝나면 종료합니다.

`--frames`는 저장할 최대 sample 수, `--render-interval`은 기록 인덱스 간격, `--subframes`는 한 이미지의 렌더 보정 횟수입니다. 40개 물리 기록마다 한 영상을 저장하면 파일 수를 줄일 수 있습니다. 이 구현은 원 기록의 실제 step id를 출력 파일 이름에 보존합니다. `--normals`를 추가하면 표면 법선도 저장합니다. `--no-rgb`는 RGB를 끄며 하나 이상의 센서 형식은 켜야 합니다.

완료 후 `summary.json`의 rendered_samples/source_step_ids/실제 sensor_file_counts와 해당 RGB/segmentation/depth를 확인합니다. 이 버전 MobilityGen의 depth는 거리 자체 float 배열이 아니라 inverse-depth 16-bit PNG로 저장됩니다. 읽을 때 설치된 MobilityGenReader가 수행하는 변환을 사용합니다. 선택 modality가 파일을 하나도 만들지 못하면 스크립트는 성공으로 끝내지 않습니다.

## 절차적 데이터와 자신의 로봇

Scenario를 `RandomPathFollowingScenario`로 바꾸고 Build한 뒤 **Start recording**을 눌러야 자동 주행도 디스크에 남습니다. episode가 리셋되면 새 recording이 생깁니다. `RandomAccelerationScenario`는 선속도/각속도 변화량을 무작위로 적용합니다. 매 episode마다 지도 안의 시작 위치/경로/종료 상태를 확인하고 같은 replay 명령을 사용합니다.

`custom_robot.py`는 설치된 JetbotRobot을 상속해 선속도 gain과 경로 속도를 0.12 m/s로 낮춘 **실제 등록 가능한 TutorialSlowJetbot**입니다. GUI에서 MobilityGen Examples 활성화 후 Script Editor로 파일을 실행하고 UI를 다시 열어 robot 목록을 갱신합니다. NVIDIA Jetbot USD도 5.1 Assets에서 로드됩니다. 이 로봇으로 기록한 데이터를 재생할 때 `--custom-robot`을 주어 같은 이름을 등록합니다. 원 설치의 robots.py를 수정할 필요 없이 이 패키지 파일을 유지할 수 있습니다.

완전히 새로운 로봇은 MobilityGenRobot의 build()에서 Stage/센서를 만들고 write_action()에서 선속도·각속도를 actuator 명령으로 변환해야 합니다. wheel radius/base, physics_dt, occupancy_map_radius, front_camera_base_path/rotation/translation을 실제 모델에 맞춥니다. chase camera offset은 관찰용 뷰, occupancy collision radius는 종료 조건에 영향을 줍니다. 등록 API의 실제 5.1 이름은 `ROBOTS.register()`입니다(원문 일부의 ROBOT 단수 표기와 다름).

## 실험과 문제 해결

한 변수 실험은 동일 recording에 render interval만 40→20으로 바꿔 영상 수와 보행 자세 간격을 비교하는 것입니다. 원 recording을 다시 생성하면 로봇 동작도 달라져 비교 조건이 바뀝니다. 새로운 output 경로를 사용합니다.

지도가 회전/이동하면 UI export 회전 180과 origin/resolution을 점검합니다. map.png만 복사하고 YAML을 이전 것으로 유지하지 않습니다. H1이 넘어지면 policy 로딩·physics_dt·충돌 상태를 확인합니다. 입력 폴더는 recordings 상위가 아니라 config.json이 직접 들어 있는 단일 기록입니다. state가 0개면 Start/Stop recording을 실제로 수행했는지 확인합니다. 원문 GitHub reader/Gradio 시각화는 선택 도구이며 본 실습을 위해 별도 저장소를 먼저 공부할 필요 없습니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [지도 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#build-an-occupancy-map)
- [실제 궤적 기록](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#record-a-trajectory)
- [replay와 render](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#replay-and-render)
- [절차적 데이터](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#generate-procedural-data)
- [로봇 추가](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_mobility_gen.html#add-a-custom-robot)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
