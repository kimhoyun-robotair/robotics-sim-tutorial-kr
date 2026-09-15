# 133. GUI Recorder, 사용자 Writer, 카메라 무작위화

권장 학습 순서 **133** · Replicator 합성 데이터 기초와 확장 · 출처 ID `t036`

이 패키지는 **실제 Synthetic Data Recorder**를 이용하는 두 가지 실행을 제공합니다. GUI에서는 사용자가 Writer/Control 상태를 조작하며, `--headless`는 같은 확장의 `SyntheticRecorder` 클래스로 정해진 프레임을 기록합니다. 외부 창고를 받기 전에도 동작을 배울 수 있도록 class 라벨이 있는 상자와 키프레임 카메라를 로컬에서 만듭니다. 공식 창고 장면으로 반복하는 절차도 아래에 포함됩니다.

## GUI 실행과 종료

GUI에서는 Recorder를 직접 조작하며, `--steps`를 생략하면 사용자가 창을 닫을 때까지 유지됩니다. `--steps N`을 주면 장면 준비 후 최대 N번 app update하고 종료합니다. `--headless`는 정해진 프레임을 자동 기록하며, `--steps` 생략 시 기존 10000 app update 제한을 사용합니다.

이 패키지 폴더에서 다음과 같이 실행합니다. 설치 경로는 자신의 환경에 맞추고, 이미 사용한 출력 폴더는 새 경로로 바꿉니다.

```bash
~/isaacsim/python.sh run.py --output output/gui
```

## 준비와 명령

Isaac Sim 5.1.0 전체 설치, RTX GPU/드라이버, GUI 실습용 디스플레이가 필요합니다. 기본 장면에는 외부 자산이 없습니다. `run.py`의 `SimulationApp` 생성 후 recorder 확장을 활성화하고 로컬 `custom_writer.py`를 등록합니다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
cd src/133_replicator_replicator_recorder
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py
# 동일 recorder 엔진의 화면 없는 유한 캡처
"$ISAAC_SIM_PATH/python.sh" run.py --headless --frames 10 --output output_headless
```

`--steps` 없는 GUI는 직접 창을 닫을 때 종료합니다. 기본 출력 폴더 `output`이 있으면 새 `--output`을 지정합니다. 자동 실행은 10프레임과 최대 10000 app update 제한을 사용하고, 파일이 없으면 실패합니다.

## Writer와 Control을 직접 조작하기

1. **Tools > Replicator > Synthetic Data Recorder**를 엽니다. Stage에서 `/World/AnimatedCamera`를 선택한 다음 **Writer > Render Products > Add New Render Product**를 누릅니다. 카메라 경로 `/World/AnimatedCamera`, 해상도 512×512를 입력합니다. 같은 카메라를 다시 추가하고 256×256로 바꾸면 시점은 같고 해상도만 다른 두 출력이 됩니다.
2. **Writer > Parameters**에서 BasicWriter를 선택하고 RGB, Semantic Segmentation, Bounding Box 2D Tight를 켭니다. **Output**의 Working Directory를 출력 폴더의 절대경로, Folder Name을 `manual`로 설정합니다. Increment 방식은 재실행 시 이전 데이터를 보존합니다. S3는 별도 AWS 인증·버킷이 필요한 선택 기능이며 이 로컬 실습은 S3를 사용하지 않습니다.
3. **Control**에서 Number of Frames=10, RTSubframes=4, Control Timeline=true, Verbose=true로 설정하고 **Start**를 누릅니다. 카메라는 0~120 time code 사이 x=-1에서 x=1로 움직입니다. Stage의 60 time codes/s에서 전체 애니메이션 길이는 2초입니다.
4. 상태 전이를 관찰하려면 Number of Frames=120으로 늘리고 Start → Pause → Resume → Stop을 누릅니다. Pause는 writer를 유지하지만 Stop은 writer를 해제합니다. Number of Frames=0은 무한 기록이므로 이 실습에서는 사용하지 않습니다.
5. **Writer > Config**에서 상태를 저장하고 다시 불러옵니다. 실행기가 만든 `output/recorder_config.json`도 불러올 수 있습니다. 로드 후 Output 경로를 확인합니다. 설정 파일은 USD 장면을 포함하지 않으므로 `recorder_stage.usda`는 별도로 열어야 합니다.
6. **Custom Writer**에 `BeginnerNormalWriter`, **Parameters Path**에 이 패키지의 `custom_writer_params.json` 절대경로를 지정합니다. 새 출력 폴더에서 3프레임 기록합니다. RGB와 법선 시각화 PNG가 annotator별 하위 폴더에 생겨야 합니다.
7. DataVisualizationWriter를 쓰려면 Script Editor에서 `from isaacsim.replicator.writers import DataVisualizationWriter`를 실행합니다. Custom Writer 이름을 `DataVisualizationWriter`, Parameters Path를 `visualization_params.json`으로 바꾸고 기록합니다. RGB 위 녹색 tight box, normals 위 빨간 loose box, RGB 위 3D box를 비교합니다.
8. Script Editor에서 `randomize_camera.py` 내용을 실행합니다. Stage에 생성된 `RandomRecorderCamera` 아래 Camera prim을 선택해 새 render product로 추가합니다. Start마다 카메라가 지정된 범위에서 상자를 보도록 변합니다. 기존 키프레임 카메라와 랜덤 카메라를 별도 출력으로 비교합니다.

## 공식 창고 장면으로 반복

새 장면에서 Content Browser의 **Isaac Sim > Samples > Replicator > Stage > full_warehouse_worker_and_anim_cameras.usd**를 엽니다. 정확한 원격 자산 URL은 다음과 같습니다.

```text
https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd
```

이 단계만 5.1 asset 서버 연결 또는 로컬 자산 미러가 필요합니다. Stage에서 실제 Camera prim을 선택해 Recorder에 추가하고 Control Timeline을 켜야 애니메이션이 진행됩니다. 로컬 `randomize_camera.py`의 look_at은 `/World/Carton`이므로 창고에서 사용하려면 실제 상자 prim 경로로 바꿉니다.

## API·USD 해설과 성공 기준

Camera prim의 transform time sample은 시간에 따라 보간되는 위치입니다. Recorder의 Control Timeline은 기록과 시간 진행을 함께 제어합니다. `step_async`는 UI를 멈추지 않고 렌더 완료와 writer 처리를 기다립니다. RTSubframes는 한 정답 프레임의 렌더 안정화를 늘리는 값이며 저장 프레임 수가 아닙니다.

`WriterRegistry.register`는 GUI가 이름으로 writer를 찾게 합니다. `BeginnerNormalWriter`는 `rgb`, `normals` annotator를 요청하고 `BackendDispatch.write_image`로 PNG를 씁니다. 법선의 [-1,1] 성분을 [0,255]로 선형 매핑한 그림이며 깊이/거리 데이터가 아닙니다. 다중 카메라의 annotator key를 파일 경로에 유지해 서로 덮어쓰지 않습니다. Parameters JSON에는 생성자 인자만 쓰며 recorder가 output_dir을 추가합니다.

성공 기준은 10프레임 녹화가 자동 종료하고 RGB/의미 정답이 존재하며, custom writer 실행에서는 표면 방향에 따라 법선 색이 달라지는 것입니다. **RTSubframes만 4→16**으로 바꾸어 빠른 카메라 이동의 잔상과 시간을 비교합니다. 두 실행의 해상도·프레임 수는 고정합니다.

Custom Writer not found라면 같은 Kit 세션에서 `custom_writer.py`를 실행/등록했는지 확인합니다. 라벨이 없으면 recorder는 일부 semantics annotator를 비활성화할 수 있습니다. 파일이 아직 쓰이는 동안 창을 닫지 않습니다. 자동 실행 검사는 GUI Pause/Resume 버튼 동작의 검증을 대신하지 않습니다.

## 출처와 버전

이 해설은 NVIDIA Isaac Sim **5.1.0** 문서와 해당 설치본을 기준으로 새로 작성했습니다. 원문의 전체 문장을 번역 복제한 것이 아니라 해당 워크플로를 독립적으로 실습하도록 설명했습니다.

- [공식 Synthetic Data Recorder](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html)
- [writer frame](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#writer-frame)
- [control frame](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#control-frame)
- [custom writer example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#custom-writer-example)
- [data visualization writer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#data-visualization-writer)
- [replicator randomized cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#replicator-randomized-cameras)
- [recording loop overview](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_recorder.html#recording-loop-overview)
