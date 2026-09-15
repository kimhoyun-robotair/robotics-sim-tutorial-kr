# 160. 자신의 환경·캐릭터·애니메이션을 IRA에 연결하기

권장 학습 순서 **160** · 액터와 공간 이벤트 데이터 · 출처 ID `t057`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

## 이 실습의 의도

작은 로컬 방을 기준으로 환경의 좌표·단위·NavMesh를 IRA에 연결하는 과정을 익힌 뒤, 사용자 캐릭터와 애니메이션을 연결하는 별도 과제로 확장합니다. `lesson.json`의 기본 장면은 제공된 `custom_room.usda`이고 actor는 한 명이며, 명령은 `LookAround 3`뿐이므로 기본 상태에서 걷지 않는 것이 정상입니다. `prepare.py`는 경로가 정리된 설정만 생성하고 NavMesh Bake·actor 자산 다운로드·retarget은 수행하지 않으므로 각 GUI 단계와 외부 자산 준비를 따로 마쳐야 합니다.

## 실행 후 확인할 것

- **로컬 장면과 단위:** `custom_room.usda`를 열어 `/World/Floor`의 12×12 m 바닥, `/World/Obstacle`의 주황색 2×1×2 m 상자, `/World/Light`를 확인합니다. metadata는 `metersPerUnit=1`, `upAxis=Z`이며 이 장면에는 NavMesh나 사람 자산이 포함되어 있지 않습니다.
- **NavMesh 결과:** Include Volume을 추가해 Bake한 뒤 바닥 위 이동 영역과 중앙 상자를 피하는 영역을 시각화합니다. 새 USD로 저장하고 생성된 `config.yaml`의 `scene.asset_path`가 그 복사본인지 확인합니다. 메시가 보인다는 사실만으로 이동 가능한 경로가 준비된 것은 아닙니다.
- **명령에 따른 관찰:** 기본 `LookAround 3`에서는 위치를 유지하며 둘러보는지 확인합니다. 우회 보행을 보려면 아래 300프레임 실행에서 NavMesh 위 두 목적지의 `GoTo`를 저장하고, actor가 상자 내부를 가로질러 가지 않는지 봅니다.
- **외부 캐릭터를 적용한 경우:** 사용자 자산의 크기·Z-up·전방 방향과 skeleton을 확인한 후 actor로 재생합니다. 제공된 방은 로컬이지만 사람은 기본 5.1 Assets에서 가져오므로 환경 파일이 열린 것만으로 캐릭터 준비가 끝난 것은 아닙니다.
- **retarget을 수행한 경우:** 실제 source/target Skeleton과 SkelAnimation, 관절 매핑을 준비해 `retarget_animation()`을 호출하고 출력 애니메이션을 target Biped에서 재생합니다. 발 미끄러짐·팔 꼬임을 관찰하고 Custom Command 등록·재Setup까지 확인하며, 방 보행 성공과 사용자 애니메이션 성공을 구분합니다.

## 준비와 실행 방식

Isaac Sim 5.1 GUI, NVIDIA RTX GPU/드라이버, Isaac Sim 5.1 Assets 접근이 필요합니다. GUI는 설치 디렉터리의 `./isaac-sim.sh`로 실행합니다. `Window > Extensions`에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 켜고 요구되는 재시작을 마칩니다. 사람 애니메이션은 `omni.anim.people`, `omni.anim.graph`, 경로 탐색은 `omni.anim.navigation`, 로봇은 `isaacsim.anim.robot`가 담당하며 IRA 의존성으로 활성화됩니다. 클라우드 LLM·ROS·별도 Python 설치는 필요하지 않습니다.

기본 환경은 이 폴더의 `custom_room.usda`입니다. 사람은 `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/People/Characters/`에서 가져옵니다. 오프라인 자산팩을 설치했다면 `--assets-root /절대경로/Assets/Isaac/5.1`을 지정합니다. 자산팩 자체는 이 패키지에 포함하지 않습니다.

이 패키지는 원문의 **확장 UI와 YAML 설정 방식**을 유지합니다. `prepare.py`는 해당 수업 설정과 명령 파일을 실제 생성합니다. 설정을 만드는 것만으로 사람을 시뮬레이션하거나 영상을 저장하지는 않습니다. 모든 명령은 이 패키지 디렉터리에서 실행합니다.

```bash
python3 prepare.py --output ./output/run_01 --frames 90
/home/hoyunkim/isaacsim/isaac-sim.sh
```

설치 경로는 자신의 환경에 맞게 바꿉니다. `output/run_01/config.yaml`은 JSON 문법으로 작성한 유효한 YAML 1.2 파일이며 Isaac Sim의 YAML 로더가 읽습니다. `lesson.json`의 `{ASSETS}`, `{OUTPUT}`, `{PACKAGE}`는 준비 스크립트가 절대 경로로 치환합니다. `isaacsim.replicator.agent` 아래에 설정을 중첩하는 구조는 설치된 5.1 기본 설정과 같습니다. 설정 버전 `0.7.0`은 Sim 버전 `5.1.0`과 다른 IRA 설정 호환성 버전입니다.

1. `Tools > Action and Event Data Generation > Actor SDG`를 엽니다. `Config File Path`에서 생성한 `config.yaml`을 선택합니다.
2. 기본 로컬 방에는 NavMesh가 없으므로 아래 **로컬 환경 만들기** 절차로 `custom_room.usda`를 열어 Bake하고 `output/room_nav.usd`로 저장합니다. `Scene > Asset Path`를 그 복사본으로 바꾸고 설정을 저장합니다. NavMesh는 사람이 서거나 걸을 수 있는 표면입니다.
3. `Set Up Simulation`을 누르고 사람/카메라 자산 로딩이 끝날 때까지 기다립니다. Stage의 `/World/Characters`, `/World/Cameras`에서 실제 이름을 확인합니다. 명령의 `Character_01` 같은 이름은 실제 탭 이름과 일치시킵니다.
4. Character 패널에서 명령을 확인하고 디스크 아이콘으로 **Save Commands**합니다. UI의 파란색은 미저장, 빨간색은 잘못된 입력입니다. 설정만 바꾸면 화면 값과 디스크 파일이 달라질 수 있으므로 `Save`도 누릅니다.
5. 아래 수업별 조작을 진행한 다음 `Start Data Generation`을 누릅니다. 기본 90프레임은 30 FPS 기준 3초입니다. 완료 후 `output/run_01/capture`를 확인합니다. 중단 후 재실행할 때는 저장 종료를 기다립니다.

## 로컬 환경 만들기: 자산 없이 구조부터 실습

이 패키지의 기본 `lesson.json`은 제공한 `custom_room.usda`를 참조합니다. 위 공통 준비 단계의 NavMesh 작업을 다음 순서로 진행합니다. 바닥과 주황색 상자, Dome Light는 패키지 자체에 있어 환경 다운로드가 필요 없습니다. IRA 사람 자산은 별도로 필요합니다.

1. File > Open으로 `custom_room.usda`를 엽니다. Layer 탭에서 Root Layer의 `metersPerUnit=1`, `upAxis=Z`를 확인합니다. 바닥은 12×12 m, 장애물은 가운데 2×1×2 m입니다.
2. Stage 우클릭 `Create > Navigation > NavMesh Include Volume`으로 볼륨을 만들고 중심 (0,0,1), scale (6,6,2) 정도로 바닥을 덮게 조절합니다. `Window > Navigation > NavMesh`에서 설정을 확인하고 Bake를 실행합니다. NavMesh가 바닥에 생성되고 상자 주변을 우회하는지 시각화합니다. 볼륨은 폴리곤 교차 방식이므로 볼륨을 줄여도 큰 한 장짜리 바닥 전체가 포함될 수 있습니다.
3. `output/room_nav.usd`로 Save As 합니다. 원본 `custom_room.usda`는 반복 실습용으로 남깁니다. `prepare.py --scene /절대경로/output/room_nav.usd --output output/room_run --frames 300`을 실행하고 Actor SDG에서 설정을 로드합니다.
4. Setup 후 Character의 Generate Random Commands로 생성하고 저장합니다. GoTo가 없으면 직접 NavMesh 위 두 지점을 골라 `GoTo 4 4 0 _`, `GoTo -4 -4 0 _`로 이동시킵니다. 기본 짧은 정지 명령을 사용했다면 걷기가 안 보이는 것이 정상입니다.
5. NavMesh의 Areas에서 Walkable 영역을 만들었다면 해당 이름을 `spawn_area`, `navigation_area` 배열에 넣어 각각 시작 위치와 목적지 선택을 제한합니다. 영역 이름이 없는 상태에서는 빈 배열을 유지합니다.

## 외부 환경을 가져오는 방법

Content Browser의 USD를 기본 빈 Stage에 드래그하면 Xform reference로 들어갑니다. USD reference는 원본 메시를 복사하지 않고 외부 파일을 연결하는 장치입니다. 비-USD 자산은 해당 제작 도구의 Omniverse Connector나 USD 변환기로 변환해야 합니다. 외부 유료 자산은 포함하지 않습니다.

단위 metadata만 cm에서 m로 바꾸면 메시 좌표 숫자는 자동으로 1/100이 되지 않습니다. 빈 미터/Z-up Stage에 자산을 넣어 변환을 확인하거나 자산 root Xform의 scale/rotation을 조절합니다. 이미 skeleton이 있는 캐릭터의 mesh 점만 0.01배 하면 bind/rest pose와 어긋납니다. 제작 도구에서 mesh·skeleton·애니메이션을 함께 meter로 내보내는 방법을 우선 사용합니다. 밝기가 안 맞으면 Dome Light부터 추가하고 실제 사람(약 1.7 m)을 옆에 놓아 스케일을 비교합니다. 모든 환경에 NavMesh를 다시 Bake합니다.

## 커스텀 캐릭터와 애니메이션

1. 자체 제작/사용 권한이 있는 캐릭터 USD를 준비합니다. 단위는 m, up은 Z, forward는 -Y로 맞추고 NVIDIA Biped skeleton에 retarget합니다. 폴더는 `characters/person_a/person_a.usd`, `characters/person_b/person_b.usd`처럼 하위 폴더마다 캐릭터 USD 하나를 둡니다. `character.asset_path`를 `characters`의 절대 경로로 바꿉니다.
2. Unreal에서 가져오면 Unreal Omniverse Connector로 USD export한 뒤 centimeter 단위를 먼저 확인합니다. skeleton 계층이 NVIDIA Biped와 다르므로 단위 변환 이후 Animation Retargeting 도구에서 source/target 관절 매핑과 retarget pose를 설정합니다. Connector, Unreal, 사용자 캐릭터는 별도 준비물입니다.
3. 한 Stage에 source Skeleton, target NVIDIA Biped Skeleton, source SkelAnimation을 둡니다. 관절 매핑/retarget pose를 GUI에서 준비한 후 Script Editor에서 `retarget_animation.py`를 열어 실행하고 다음 함수를 실제 Prim 경로로 호출합니다.

```python
retarget_animation('/World/Source/Skeleton', '/World/Biped/Skeleton',
                   '/World/Source/Walk', '/World/RetargetedWalk')
```

4. 생성된 애니메이션을 target Biped로 재생해 발 미끄러짐·팔 꼬임을 확인합니다. SkelAnimation을 별도 USD로 저장한 뒤 `CustomCommandName`, `CustomCommandTemplate`(Timing/TimingToObject/GoToBlend)을 추가하고 Command Settings의 Custom Command Panel에 등록합니다. Setup을 다시 실행한 후 해당 명령으로 움직입니다. 임의 skeleton 파일을 등록하는 것만으로 retarget이 해결되지 않습니다.

완료 기준은 로컬 방의 NavMesh 우회 경로와 커스텀 캐릭터의 올바른 방향/크기/관절 움직임입니다. 방 실습만으로 retarget 완료를 주장하지 않습니다. 한 변수 실험은 NavMesh agent radius만 키워 상자 모서리와의 여유 거리가 늘어나는지 확인하는 것입니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [환경 단위와 좌표](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html#unit-and-coordinates-system)
- [NavMesh 생성](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html#building-the-navmesh)
- [커스텀 캐릭터](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html#custom-character-assets)
- [애니메이션 retarget](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/customization.html#custom-character-animations)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
