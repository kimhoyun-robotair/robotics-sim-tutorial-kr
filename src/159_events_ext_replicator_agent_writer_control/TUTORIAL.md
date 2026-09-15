# 159. 같은 장면에서 어떤 데이터를 저장할까요?

## 이번에 배우는 것

**writer가 저장할 주석을 결정하는 방식을 익히고, 카메라 두 대를 스테레오 데이터로 연결합니다.**

영상에 사람이 보이는 것과 그 사람의 3D 상자·관절 정보까지 저장되는 것은 별개입니다. writer는 렌더 결과에서 필요한 정보를 골라 파일이나 스트림으로 내보냅니다. 이번에는 기본 RGB·2D 상자를 읽고, 좌우 카메라의 간격이 출력 파라미터로 이어지는 과정을 살펴봅니다.

| writer | 이 폴더에서 비교할 내용 | 추가 준비 |
|---|---|---|
| `IRABasicWriter` | RGB, 객체 정보, 선택한 주석 | 기본 장면 |
| `TaoWriter` | 가림 정도에 따른 bbox 포함 | 가림을 관찰할 장면 |
| `StereoWriter` | 좌우 영상, baseline, 깊이 | 실제 카메라 쌍 |
| `RTSPWriter` | 파일 대신 실시간 스트림 | FFmpeg와 RTSP 서버 |

`writer_presets.json`은 선택할 설정 예시입니다. 기본 실행에 네 writer가 동시에 적용되지는 않습니다.

## 1. 기본 RGB와 경계 상자 저장하기

Isaac Sim 5.1, RTX GPU, 5.1 창고·사람 자산이 필요합니다. 저장소 루트에서 다음을 실행하세요.

```bash
python3 src/159_events_ext_replicator_agent_writer_control/prepare.py --output src/159_events_ext_replicator_agent_writer_control/output/basic --frames 90
~/isaacsim/isaac-sim.sh
```

1. **Window > Extensions**에서 `isaacsim.replicator.agent.core`, `isaacsim.replicator.agent.ui`를 활성화하고 필요한 재시작을 마칩니다.
2. **Tools > Action and Event Data Generation > Actor SDG**에서 생성한 `output/basic/config.yaml`을 선택합니다.
3. Scene의 창고에 NavMesh가 없으면 창고를 열고 **Create > Navigation > NavMesh Include Volume**으로 바닥을 덮습니다. **Window > Navigation > NavMesh**에서 Bake한 복사본을 저장해 **Scene > Asset Path**에 지정하세요.
4. **Set Up Simulation** 후 카메라 뷰에 사람이 보이는지 확인합니다. 실제 사람 이름에 맞춘 명령을 **Save Commands**하고 설정도 저장합니다.
5. **Start Data Generation**으로 90프레임을 생성합니다. GUI는 작업 후 남으며 저장 완료 후 직접 닫습니다.

### 설정에서 볼 부분

기본 `lesson.json`은 다음 주석만 켭니다.

```json
{
  "writer": "IRABasicWriter",
  "parameters": {
    "output_dir": "{OUTPUT}/capture",
    "rgb": true,
    "camera_params": true,
    "object_info_bounding_box_2d_tight": true,
    "semantic_filter_predicate": "class:character|robot;id:*"
  }
}
```

`output_dir`은 `prepare.py`가 절대 경로로 바꿉니다. `object_info_bounding_box_2d_tight`는 IRA 객체 정보용 키입니다. 다른 writer의 비슷한 bbox 옵션 이름을 그대로 섞으면 같은 결과가 된다고 가정할 수 없습니다.

### 실행 결과 확인하기

실제 주석은 `capture/<카메라ID>/object_detection/object_detection_<sequence><frame>.json`에 저장됩니다. 카메라 ID는 Prim 경로의 `/`를 `_`로 바꾼 이름이며 RGB도 같은 카메라 아래의 `rgb/`에서 찾습니다. 파일명의 프레임 번호를 맞추고 JSON의 `agents` 안에서 해당 사람의 Prim 경로·id·상자 정보를 읽으세요.

`output/basic/capture`에서 RGB와 같은 프레임의 `object_detection_*.json`을 여세요. actor id와 경계 상자가 화면의 사람과 대응하는지 확인합니다. 기본 설정에는 skeleton과 3D bbox가 없으므로 그 항목이 없는 것이 정상입니다.

더 많은 정보를 기록하려면 새 설정의 `replicator.writer`와 `parameters`를 `writer_presets.json`의 IRABasicWriter 항목에 맞춥니다. preset에는 `output_dir`이 없으므로 새 결과 경로를 직접 유지해야 합니다. 이 preset은 `object_info_bounding_box_3d`, `agent_info_skeleton_data`를 추가합니다. RGB가 같더라도 저장하는 정답 데이터의 범위는 달라집니다.

## 2. 좌우 카메라를 StereoWriter에 연결하기

### 코드에서 볼 부분

기본 장면의 Setup을 마친 상태에서 Script Editor로 `make_stereo.py`를 실행하고 실제 왼쪽 카메라 경로를 넣어 호출하세요.

```python
exec(open('/절대경로/저장소/src/159_events_ext_replicator_agent_writer_control/make_stereo.py').read())
make_stereo('/World/Cameras/Camera', 0.12)
```

함수는 원래 카메라를 복사해 이름 뒤에 `_R`을 붙이고 오른쪽으로 0.12 m 옮깁니다. 여기서 오른쪽은 월드 X가 아니라 **왼쪽 카메라의 로컬 +X**입니다.

```python
world_offset = left_world.TransformDir(Gf.Vec3d(1, 0, 0)).GetNormalized()
baseline_m / UsdGeom.GetStageMetersPerUnit(stage)
```

첫 줄은 카메라의 오른쪽을 월드 방향으로 바꾸고, 둘째 줄은 미터 단위 간격을 Stage 좌표 단위로 바꿉니다. 부모 Xform이 회전되어 있어도 카메라 기준의 좌우 관계를 유지하려는 계산입니다. 두 카메라의 방향과 렌즈는 복사되어 동일합니다. `_R`은 단순한 표시 이름을 넘어 설치 StereoWriter가 좌우 쌍을 찾는 규칙입니다. 오른쪽 카메라를 임의의 다른 이름으로 바꾸면 baseline이 계산되지 않을 수 있습니다.

1. 카메라 쌍을 만든 장면을 새 `output/stereo_scene.usd`로 **Save As**합니다.
2. `prepare.py`로 새 출력 설정을 만들고 Scene을 저장한 USD로 바꿉니다.
3. `sensor.camera_num`을 삭제하고 `camera_list`에 왼쪽과 오른쪽의 실제 Prim 경로 두 개를 넣습니다.
4. writer를 `StereoWriter`로 바꾸고 preset의 매개변수와 새 `output_dir`을 지정합니다.
5. 새 설정을 로드해 Setup·저장·데이터 생성을 진행합니다.

카메라 복사만 하고 `camera_list`를 바꾸지 않으면 IRA가 두 뷰를 기록하도록 요청한 상태가 아닙니다.

### 실행 결과 확인하기

| 출력 | 확인할 내용 |
|---|---|
| 좌우 RGB | 같은 프레임, 같은 물체가 약간 다른 수평 위치에 보이는지 봅니다. |
| `fx_fy_cx_cy` | 투영에 사용하는 초점·주점 정보를 확인합니다. |
| `stereo_baseline` | 카메라 사이 간격이 0.12 m와 맞는지 봅니다. |
| PFM 깊이 | `customized_distance_to_image_plane`를 켠 깊이 출력인지 확인합니다. |

TaoWriter는 다른 비교 축입니다. preset을 적용한 새 실행에서 사람 앞에 가림 물체를 놓고 bbox 포함 여부를 RGB와 비교하세요. 가려짐과 화면 경계에서 잘림은 서로 다른 조건으로 처리되므로 구분합니다. preset의 높이·폭 threshold는 각각 0.5이며 `shoulder_height_ratio`는 0.25입니다. 화면 안의 가려진 대상은 폭·높이 조건을 모두 만족해야 하지만 화면 가장자리에서 잘린 대상은 둘 중 하나만 만족해도 포함될 수 있습니다. 따라서 같은 정도로 보이는 두 사람도 가림인지 화면 절단인지에 따라 bbox 포함 결과가 달라질 수 있습니다.

RTSPWriter를 선택하려면 호스트의 `ffmpeg -version`이 동작하고 수신 RTSP 서버가 실행 중이어야 합니다. preset의 `rtsp_stream_url`을 서버에 맞춘 뒤 콘솔에 표시되는 실제 stream URL을 VLC나 `ffplay`로 여세요. 예를 들어 로컬 서버의 TCP 8554를 사용하고 카메라 경로가 `/World/Cameras/Camera`라면 RGB URL은 `rtsp://localhost:8554/RTSPWriter_World_Cameras_Camera_rgb` 형태입니다. 실제 출력 URL을 복사해 접속하고 초기 스트림이 안정된 뒤 연속 프레임을 확인하세요. FFmpeg·서버는 이 폴더에 포함되어 있지 않습니다. 파일 writer의 성공만으로 스트림 수신도 확인한 것은 아닙니다.

## 3. 카메라와 writer의 역할 정리

```text
카메라 위치·렌즈 → 무엇이 어떻게 보이는가
writer와 매개변수 → 그 관찰에서 무엇을 저장하는가
출력 경로·RTSP URL → 어디에 결과를 전달하는가
```

스테레오에서는 같은 프레임의 좌우 대응이 중요합니다. 평행한 카메라 쌍과 같은 투영 조건에서 가까운 물체는 더 큰 시차를 보입니다. baseline이 출력 파라미터와 맞아야 이 시차를 거리와 연결할 수 있습니다.

직접 만든 writer는 Python 클래스를 `WriterRegistry.register()`로 등록한 뒤 설정에서 선택합니다. 설정에 클래스 이름을 쓰는 것만으로 구현 파일이 자동 로드되지는 않습니다.

## 4. 간단한 확인 실험

스테레오 **baseline만** 0.12 m에서 0.24 m로 바꿔 보세요. 왼쪽 카메라의 위치·방향·렌즈와 장면은 유지합니다. 기존 `_R`을 제거한 실습 복사본 또는 오른쪽 카메라 생성 전 장면에서 새 쌍을 만드세요.

- 출력 `stereo_baseline`이 변경됐는지 먼저 확인합니다.
- 같은 깊이의 물체에서 좌우 수평 위치 차이가 더 커지는지 봅니다.
- 새 출력 경로를 사용하고 같은 프레임끼리 비교하세요. 사람 자세가 달라진 프레임은 시차 비교에 적합하지 않습니다.

## 실행할 때 막히면

- **preset 적용 후 저장 위치 오류**: preset에는 `output_dir`이 없습니다. 파일 writer의 매개변수에 새 경로를 넣으세요.
- **`Right camera already exists`**: 함수는 기존 오른쪽 카메라를 덮어쓰지 않습니다. 실습 복사본에서 기존 `_R`을 정리하거나 쌍 생성 전 Stage를 여세요.
- **스테레오 한쪽 영상이 없음**: `camera_num` 제거 여부와 `camera_list`의 두 실제 경로를 확인하세요.
- **기본 실행에 관절 정보가 없음**: `agent_info_skeleton_data`가 켜진 preset을 적용했는지 확인하세요.
- **RTSP 접속 실패**: 서버 주소·포트와 FFmpeg를 먼저 확인한 뒤 writer가 출력한 전체 URL로 접속하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Writer Control](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-agent/writer_control.html)에 대응합니다. 로컬 preset과 카메라 복사 도구가 실제 설치된 writer를 선택하고 준비하도록 돕습니다.

`tutorial.json`은 `not_run`입니다. 주석 저장, 스테레오 깊이, RTSP 수신은 각각 실제 출력으로 확인해야 하며 카메라 복사나 설정 저장만으로 완료했다고 판단하지 않습니다.
