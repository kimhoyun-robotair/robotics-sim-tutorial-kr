# 158. 배우를 바라보는 카메라 무작위 배치

권장 학습 순서 **158** · 액터와 공간 이벤트 데이터 · 출처 ID `t055`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

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

## 설정 적용과 관찰

1. `Set Up Simulation` **이전**에 `Window > Script Editor`를 열어 아래 두 줄을 실행합니다. 두 파일의 경로를 현재 패키지의 절대 경로로 바꿉니다. 설정은 현재 앱의 persistent 영역에 저장되므로 실험 후 원래 JSON을 재적용합니다.

```python
exec(open('/절대경로/158_events_ext_replicator_agent_camera_control/apply_camera_settings.py').read())
apply_camera_settings('/절대경로/158_events_ext_replicator_agent_camera_control/camera_settings.json')
```

2. 기본값은 배우 발 위치보다 0.7 m 높은 곳을 바라보며, 카메라 높이는 2–3 m, 배우까지 거리는 6.5–14 m, 내려다보는 각도는 0–60도입니다. 높이 최소값이 초점 높이보다 커야 하고 최대 높이가 최대 거리보다 작아야 합니다. 유효 공간이 없거나 NavMesh가 없으면 원점을 바라보는 배치로 돌아갈 수 있으므로 정상 랜덤 배치로 오해하지 않습니다.
3. `Set Up Simulation` 후 카메라 뷰를 선택해 실제 배우가 화면에 있는지 봅니다. Script Editor에서 `inspect_cameras.py`를 열어 실행하면 USD world 좌표와 focalLength가 출력됩니다. XformCache는 부모 변환까지 합친 좌표를 구합니다. USD 카메라의 시선은 로컬 -Z입니다.
4. `min_camera_height`와 `max_camera_height`를 모두 2.5로 맞추고 새 설정·새 stage에서 다시 Setup합니다. 이전 카메라가 이미 충분하면 IRA가 그대로 재사용하므로 File > New 후 반복합니다. 모든 카메라 높이가 2.5 m로 고정되는지 비교합니다.
5. `aim_camera_to_character=false`로 바꾸면 배우 추적용 무작위 배치를 끄고 원점을 향합니다. `randomize_camera_info=false`는 초점거리를 통일하는 별개 스위치입니다. 고정된 실제 카메라만 쓰려면 `sensor.camera_num`을 없애고 `camera_list: ["/World/Cameras/Camera"]`를 설정합니다. 두 키는 동시에 사용하지 않습니다.

카메라 focalLength와 aperture는 USD 카메라 단위 규칙을 따릅니다. 공식 카메라 배치 문서가 focalLength 수치에 meter 표기를 붙였지만 13–23을 카메라가 배우에서 13–23 m 떨어지는 거리로 해석하면 안 됩니다. 이 수업은 설치된 IRA 기본 수치와 설정 키를 사용합니다. 원문 마지막 코드의 `isaacsim/replicator.agent` 경로 오타를 설치된 `extension.toml`의 `isaacsim.replicator.agent` 경로로 바로잡았습니다.

완료 기준은 실제 카메라 world 높이와 영상에서 설정 효과를 함께 확인하는 것입니다. 한 변수 실험은 모든 높이를 2.5로 고정해 높이 변화만 제거하는 위 4번입니다. 추가 내·외부 파라미터 보정은 `isaacsim.sensors.rtx.placement` 확장으로 할 수 있지만 이 패키지를 실행하는 데 필요하지 않습니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [무작위 카메라 배치](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/camera_control.html#camera-placement-randomization)
- [설정 API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/camera_control.html#from-the-script)
- [고급 도구](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/camera_control.html#advanced-camera-tools)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
