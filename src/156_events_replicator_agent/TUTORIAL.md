# 156. 사람이 움직이는 창고 장면과 RGB·주석 만들기

권장 학습 순서 **156** · 액터와 공간 이벤트 데이터 · 출처 ID `t053`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다. `run_scheduler.py`는 별도의 headless 배치 도구이며 GUI 유지 대상이 아닙니다.

## 이 실습의 의도

창고의 사람 두 명, 카메라 한 대, IRABasicWriter를 연결하여 actor 명령이 RGB와 객체 주석으로 기록되는 전체 절차를 익힙니다. 기본 명령은 `Idle`과 `LookAround`만 사용하므로 위치가 거의 고정된 채 자세가 바뀌는 것이 정상이며, 보행과 로봇 카메라는 별도 설정 변경으로 실습합니다. `prepare.py`는 설정과 명령 파일을 만들고 종료하므로 자산 로딩·NavMesh 준비·데이터 생성은 Actor SDG GUI 또는 준비가 끝난 설정의 scheduler 실행에서 확인합니다.

## 실행 후 확인할 것

- **준비 파일:** 출력의 `config.yaml`에서 사람 2명, 카메라 1대, 로봇 0대, `simulation_length=90`과 `capture`의 절대 경로를 확인합니다. `prepare.py`가 capture 경로를 출력해도 RGB가 이미 생성된 것은 아닙니다.
- **실제 actor 명령:** **Set Up Simulation** 후 `/World/Characters`의 실제 이름과 명령 파일 이름을 맞춥니다. 기본 3초 구간에서 Character_01은 `Idle 1 → LookAround 2`, Character_02는 `LookAround 3`을 수행하는지 보고, 걷지 않는 것을 명령 실패로 판단하지 않습니다.
- **영상과 주석:** **Start Data Generation** 완료 후 `capture`의 RGB와 같은 프레임 `object_detection.json`에서 actor id·bbox가 보이는 배우와 대응하는지 확인합니다. actor 수는 장면 구성값이고 bbox는 카메라 안에 잡힌 대상의 주석이므로 단순히 모든 프레임에 두 박스가 있는지만 보지 않습니다.
- **확장 실습의 경계:** 무작위 `GoTo`는 NavMesh 위 목적지와 **Save Commands**가 준비된 경우에 확인합니다. Nova Carter는 기본값 0이므로 별도로 1대로 설정해야 나타나고, `write_data=true`를 켜야 로봇 카메라 출력까지 비교할 수 있습니다.
- **배치 실행:** `run_scheduler.py --save-usd`를 사용한 경우에도 새 출력의 실제 RGB·actor 주석·setup USD를 확인합니다. GUI에서 확인하지 않은 NavMesh나 자산 문제가 scheduler 호출 자체로 해결되지는 않습니다.

## 준비와 실행 방식

Isaac Sim 5.1 GUI, NVIDIA RTX GPU/드라이버, Isaac Sim 5.1 Assets 접근이 필요합니다. GUI는 설치 디렉터리의 `./isaac-sim.sh`로 실행합니다. `Window > Extensions`에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 켜고 요구되는 재시작을 마칩니다. 사람 애니메이션은 `omni.anim.people`, `omni.anim.graph`, 경로 탐색은 `omni.anim.navigation`, 로봇은 `isaacsim.anim.robot`가 담당하며 IRA 의존성으로 활성화됩니다. 클라우드 LLM·ROS·별도 Python 설치는 필요하지 않습니다.

기본 환경은 `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Environments/Simple_Warehouse/full_warehouse.usd`, 사람은 같은 Assets 루트의 `/Isaac/People/Characters/`입니다. 오프라인 자산팩을 설치했다면 `--assets-root /절대경로/Assets/Isaac/5.1`을 지정합니다. 자산팩 자체는 이 패키지에 포함하지 않습니다.

이 패키지는 원문의 **확장 UI와 YAML 설정 방식**을 유지합니다. `prepare.py`는 해당 수업 설정과 명령 파일을 실제 생성합니다. 설정을 만드는 것만으로 사람을 시뮬레이션하거나 영상을 저장하지는 않습니다. 모든 명령은 이 패키지 디렉터리에서 실행합니다.

```bash
python3 prepare.py --output ./output/run_01 --frames 90
/home/hoyunkim/isaacsim/isaac-sim.sh
```

설치 경로는 자신의 환경에 맞게 바꿉니다. `output/run_01/config.yaml`은 JSON 문법으로 작성한 유효한 YAML 1.2 파일이며 Isaac Sim의 YAML 로더가 읽습니다. `lesson.json`의 `{ASSETS}`, `{OUTPUT}`, `{PACKAGE}`는 준비 스크립트가 절대 경로로 치환합니다. `isaacsim.replicator.agent` 아래에 설정을 중첩하는 구조는 설치된 5.1 기본 설정과 같습니다. 설정 버전 `0.7.0`은 Sim 버전 `5.1.0`과 다른 IRA 설정 호환성 버전입니다.

1. `Tools > Action and Event Data Generation > Actor SDG`를 엽니다. `Config File Path`에서 생성한 `config.yaml`을 선택합니다.
2. 환경에 NavMesh가 없으면 창고 USD를 먼저 열고, Stage 우클릭 `Create > Navigation > NavMesh Include Volume`을 추가해 바닥을 덮습니다. `Window > Navigation > NavMesh`에서 Bake 후 `Save As`로 패키지 `output/warehouse_nav.usd`에 저장합니다. `Scene > Asset Path`를 그 복사본으로 바꾸고 설정을 저장합니다. NavMesh는 사람이 서거나 걸을 수 있는 표면입니다.
3. `Set Up Simulation`을 누르고 사람/카메라 자산 로딩이 끝날 때까지 기다립니다. Stage의 `/World/Characters`, `/World/Cameras`에서 실제 이름을 확인합니다. 명령의 `Character_01` 같은 이름은 실제 탭 이름과 일치시킵니다.
4. Character 패널에서 명령을 확인하고 디스크 아이콘으로 **Save Commands**합니다. UI의 파란색은 미저장, 빨간색은 잘못된 입력입니다. 설정만 바꾸면 화면 값과 디스크 파일이 달라질 수 있으므로 `Save`도 누릅니다.
5. 아래 수업별 조작을 진행한 다음 `Start Data Generation`을 누릅니다. 기본 90프레임은 30 FPS 기준 3초입니다. 완료 후 `output/run_01/capture`를 확인합니다. 중단 후 재실행할 때는 저장 종료를 기다립니다.

## 이번 실습의 조작과 기대 결과

1. 기본 두 배우가 3초 동안 `Idle` 또는 `LookAround`를 수행하는 것을 먼저 확인합니다. 얼굴이 좌우로 움직이는 동안 몸 위치가 거의 고정되어 있으면 정상입니다.
2. Character의 `Generate Random Commands`를 누른 뒤 새 명령의 `GoTo x y z yaw`와 `Idle seconds`를 읽어 봅니다. Save Commands 후 생성하면 NavMesh 안의 목적지로 이동합니다. 첫 실습에서는 출처 파일의 기본 짧은 명령을 보존하고 새 `output/run_02`를 만듭니다.
3. `sensor.camera_num=1`, `character.num=2`, writer의 `rgb=true`, `object_info_bounding_box_2d_tight=true`가 서로 다른 역할임을 확인합니다. bbox는 배우의 픽셀 범위이고 RGB는 실제 영상입니다. `object_detection.json`에서 actor id와 박스 값을 찾아 같은 프레임 RGB와 비교합니다.
4. 로봇도 경험하려면 새로운 실행 설정에서 `nova_carter_num=1`, `character.num=1`로 바꿉니다. Robot 탭의 실제 이름에 `Idle 2`, `GoTo 2 0 0`을 입력합니다. 목적지가 NavMesh 위인지 확인하고 저장합니다. `write_data=true`로 바꾸면 로봇 자체 카메라도 출력에 포함됩니다.

GUI에서 설정과 명령을 한 번 검증한 뒤 같은 설정을 일괄 실행할 수 있습니다. 다음 도구는 설치된 `tools/actor_sdg/sdg_scheduler.py`를 호출하는 명시적 래퍼이며 내부 SDG 구현을 복제하지 않습니다. 기존 capture를 재사용하지 않도록 새로운 설정/출력 경로를 사용합니다.

```bash
python3 prepare.py --output ./output/batch_01 --frames 90
python3 run_scheduler.py --isaac-root /home/hoyunkim/isaacsim --config ./output/batch_01/config.yaml --save-usd
```

완료 기준은 RGB 파일, 실제 actor 주석, `--save-usd` 사용 시 setup 장면이 출력에 남는 것입니다. 프로세스가 켜졌다는 사실만으로 성공으로 판단하지 않습니다. 한 변수 실험은 `--frames 90`을 `--frames 180`으로 변경해 3초/6초 데이터 길이를 비교하는 것입니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [구성과 설정 필드](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html#configuration-file)
- [GUI 데이터 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html#data-generation-from-ui)
- [scheduler 일괄 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_agent.html#data-generation-from-script)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
