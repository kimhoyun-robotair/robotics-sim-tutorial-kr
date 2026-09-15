# 159. IRA writer: 주석, 가림 필터, 스테레오와 RTSP

권장 학습 순서 **159** · 액터와 공간 이벤트 데이터 · 출처 ID `t056`

이 패키지의 GUI 실습은 사용자가 실행한 Isaac Sim의 native 패널에서 진행합니다. 데이터 생성 프레임 수는 작업 분량이며, 작업 완료가 GUI를 닫지는 않습니다. 창은 사용자가 직접 닫습니다. 설정 생성용 Python 도구는 GUI를 실행하지 않고 설정 파일을 만든 뒤 종료합니다.

## 이 실습의 의도

같은 actor 장면에서 writer 선택과 매개변수가 저장 주석·스테레오 데이터·스트리밍 출력을 어떻게 바꾸는지 비교합니다. 기본 실행 구성은 카메라 한 대의 IRABasicWriter로 RGB·카메라 파라미터·tight bbox만 활성화하며, `writer_presets.json`에 있는 다른 writer와 추가 주석은 직접 설정을 교체해야 적용됩니다. `prepare.py`는 설정 파일만 만들고, 스테레오는 카메라 쌍 생성과 새 설정이, RTSP는 별도 FFmpeg·수신 서버가 준비되어야 실제 출력을 확인할 수 있습니다.

## 실행 후 확인할 것

- **기본 출력:** GUI 데이터 생성 후 `capture`의 RGB와 같은 프레임 `object_detection.json`에서 actor와 tight bbox를 비교합니다. 기본 `lesson.json`은 skeleton·3D bbox를 켜지 않으므로 해당 데이터가 필요하면 IRABasicWriter preset의 옵션을 적용한 새 실행을 사용합니다.
- **TaoWriter 비교:** `output_dir`을 유지하면서 preset을 적용하고 배우 앞에 가림 물체를 놓은 결과를 확인합니다. 높이·폭 threshold를 만족하는 bbox의 포함 여부를 영상과 대조하고, 카메라 경계에서 잘린 경우와 물체에 가린 경우를 따로 비교합니다.
- **스테레오 구성:** `make_stereo(left_path,0.12)` 실행 후 원래 카메라와 `_R` 카메라가 실제로 존재하는지 확인합니다. 두 카메라의 중심 간 거리는 stage 단위를 m로 환산해 0.12 m이어야 하고, 오른쪽 이동 방향은 왼쪽 카메라의 로컬 +X입니다.
- **스테레오 출력:** 저장한 USD와 두 `camera_list` 경로로 StereoWriter를 실행한 뒤 좌우 RGB, `fx_fy_cx_cy`, `stereo_baseline`, PFM 깊이를 확인합니다. 카메라를 복사한 것만으로 IRA가 두 뷰를 기록하지 않으므로 `camera_num`을 삭제한 새 설정까지 확인합니다.
- **RTSP를 선택한 경우:** FFmpeg·서버를 준비하고 RTSPWriter의 실제 stream URL을 플레이어로 열어 배우 장면이 수신되는지 확인합니다. 기본 실행에 스트림이 없는 것은 정상이며 파일 writer 성공은 RTSP 수신 성공을 대신하지 않습니다.

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

## 네 가지 writer 실습

1. 기본 IRABasicWriter에서 RGB와 `object_detection.json`을 엽니다. `object_info_bounding_box_2d_tight`, `object_info_bounding_box_2d_loose`, `object_info_bounding_box_3d`는 BasicWriter의 bbox 키를 대체합니다. `agent_info_skeleton_data`는 skeleton 정보를 추가합니다. 잘못된 기본 bbox 키를 혼용하지 않습니다. 출력은 annotator별 폴더로 분리되며 actor/object 통합 주석은 `object_detection.json`입니다.
2. `writer_presets.json`에서 TaoWriter를 골라 `lesson.json`의 `replicator.writer` 및 `parameters`를 교체합니다. 기존 `output_dir`은 유지하고 새 출력 설정을 생성합니다. actor 앞에 상자를 배치해 부분 가림을 만든 후 bbox가 포함되는지 비교합니다. 가림 객체는 높이 조건과 폭 조건을 모두 만족해야 합니다. 프레임 밖으로 잘린 actor는 둘 중 하나만 만족해도 포함될 수 있으므로 occlusion과 truncation을 구분합니다. 높이는 상체 `shoulder_height_ratio` 또는 전체 `valid_height_unoccluded_threshold`, 폭은 `valid_width_unoccluded_threshold`로 판단합니다.
3. 스테레오는 IRA가 자동 생성하지 않습니다. Setup 후 Script Editor에서 아래를 실행하고 Scene을 `output/stereo_scene.usd`로 Save As 합니다. 실제 왼쪽 카메라 이름에 맞게 경로를 바꿉니다.

```python
exec(open('/절대경로/159_events_ext_replicator_agent_writer_control/make_stereo.py').read())
make_stereo('/World/Cameras/Camera', 0.12)
```

4. 새 설정은 Scene을 저장한 USD로, writer를 StereoWriter로 바꿉니다. `sensor.camera_num`을 삭제하고 `camera_list`를 왼쪽과 `_R` 두 Prim 경로로 설정합니다. `customized_camera_params=true`의 출력에서 `fx_fy_cx_cy`, `stereo_baseline`을 찾고 0.12 m와 대조합니다. `customized_distance_to_image_plane`은 PFM 깊이를 출력합니다. 오른쪽 카메라는 부모 Xform을 고려해 왼쪽 로컬 +X 방향으로 이동하며 세계 X축으로만 옮기지 않습니다.
5. RTSP는 추가 준비가 필요합니다. 호스트에 FFmpeg(`ffmpeg -version` 확인), 수신 가능한 RTSP 서버(예: 로컬 MediaMTX에서 TCP 8554 수신)를 직접 설치·실행합니다. 서버 프로그램/FFmpeg는 이 패키지에 포함하지 않으며 스크립트가 자동 설치하지 않습니다. RTSPWriter preset을 적용하고 서버 URL을 맞춥니다. 콘솔에 출력되는 stream URL을 VLC 또는 `ffplay`로 엽니다. 기본 카메라가 `/World/Cameras/Camera`라면 예시는 `rtsp://localhost:8554/RTSPWriter_World_Cameras_Camera_rgb`입니다. 초기 프레임이 깨지면 스트림 초기화 후 재확인합니다. CPU/GPU encoder 선택은 annotator 형식과 NVENC 지원 여부에 달립니다.

## custom writer 등록 원리

새 writer는 `omni.replicator.core.WriterRegistry.register(WriterClass)`로 등록한 **뒤** IRA 설정의 이름으로 선택합니다. UI Replicator Setting에서 Custom을 선택하고 클래스 이름과 `initialize` 매개변수를 입력합니다. IRA가 클래스 이름만으로 코드를 임의 로드하지는 않습니다. 이 패키지의 첫 실습은 설치된 네 writer를 직접 비교하며 임의의 fake writer를 사용하지 않습니다.

완료 기준은 실제 저장 주석의 bbox 존재 여부, 스테레오 baseline, 선택한 RTSP 영상입니다. 한 변수 실험은 스테레오 baseline을 0.12 → 0.24 m로 바꾸고 같은 물체 좌우 시차를 비교하는 것입니다. 기존 `_R`을 덮어쓰지 않으므로 새 Stage/새 출력 폴더에서 실행합니다. IRA의 S3 writer 설정은 5.1 문서에서 비활성 상태입니다.
## 공통 배경을 이 패키지에서 이해하기

USD Stage는 열린 장면 전체이고 Prim은 `/World/Cameras/Camera`처럼 주소를 가진 장면 요소입니다. USD 파일 경로는 디스크/서버의 파일을 가리키며 Prim 경로는 그 안의 객체를 가리킵니다. Xform은 위치·회전·크기를 계층적으로 합성합니다. NavMesh는 물리 충돌 모양 자체가 아니라 이동 가능한 바닥 영역이므로 충돌 설정을 했다고 자동으로 경로가 생기지는 않습니다.

IRA가 장면과 actor 동작을 구성하고 Replicator writer가 RGB·주석을 디스크에 기록합니다. `seed`는 무작위 선택을 재현하기 위한 값이며 같은 조작 순서도 유지해야 비교가 가능합니다. `simulation_length`는 프레임 수, `Idle 2` 같은 actor 명령 시간은 초입니다. camera 수가 많을수록 렌더 타깃이 늘어 GPU 메모리가 증가합니다.

## 문제 해결

자산을 찾지 못하면 Content Browser에서 위 USD URL이 열리는지 먼저 확인합니다. UI 초기화가 오래 걸리는 경우 공식 문서의 `--/persistent/isaac/asset_root/timeout=1.0` 실행 옵션으로 접근 실패를 빠르게 확인할 수 있습니다. 사람이 안 움직이면 NavMesh Bake, 실제 actor 이름, Save Commands 여부를 순서대로 확인합니다. 사진이 비면 카메라 뷰를 직접 선택해 배우가 화면에 있는지 봅니다. GPU 메모리 부족은 카메라 1대/인원 1명으로 줄여 원인을 분리합니다. 출력 폴더가 이미 있으면 `prepare.py`는 덮어쓰지 않으므로 새로운 `--output`을 사용합니다.


## 출처와 검증 범위

Isaac Sim **5.1.0** 공식 문서에 맞춘 독립 패키지입니다. 아래 설명과 실습은 한국어로 새로 작성했습니다. 공식 확장 기능은 설치된 Isaac Sim이 제공하며 이 패키지에 복제하지 않습니다.

- [기본 writer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html#built-in-writers)
- [스테레오](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html#stereowriter)
- [RTSP 전송](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html#rtspwriter)
- [직접 만든 writer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html#custom-writers)

설정 생성·Python 문법 확인과 실제 GPU 시뮬레이션은 별개의 검사입니다. 이 패키지의 기본 상태는 `not_run`이며 렌더링·애니메이션·외부 서비스 결과를 실행 완료로 주장하지 않습니다.
