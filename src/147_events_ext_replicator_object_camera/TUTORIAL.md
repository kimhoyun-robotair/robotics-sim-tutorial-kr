# 147. Camera — 한국어 실습

권장 학습 순서 **147** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t061`

같은 위치에서 초점거리만 다른 두 pinhole camera가 동일한 큐브를 촬영한다.

## 이 실습의 의도

카메라 위치를 유지한 채 초점거리만 바꾸면 물체의 영상 크기와 화각이 어떻게 달라지는지 비교하는 실습이다. 두 카메라를 모두 `(0,50,500)` cm에 두고 같은 고정 큐브를 보게 하여, 거리 변화나 스테레오 시차와 초점거리 효과를 구분한다. 기본 준비 설정은 두 카메라·3프레임이며 `run.py` 뒤에 native 실행 또는 GUI Simulate를 해야 실제 영상이 생긴다.

## 실행 후 확인할 것

- **두 카메라 설정:** `prepared.yaml`과 IRO 초기화 후 카메라 속성에서 `default_camera`는 focal_length=24, `zoom_camera`는 48인지 확인한다. 둘의 위치·방향·640×480 해상도·horizontal_aperture=24는 동일해야 한다.
- **대응 파일:** native 생성 완료 후 `images/`에서 카메라 이름으로 RGB를 짝짓는다. 기본값은 카메라마다 3장, 총 6장이며, description은 카메라별 이미지 수와 같은 개수라고 가정하지 않는다.
- **초점거리 효과:** 같은 seed의 두 영상에서 빨간 큐브 너비를 픽셀로 비교한다. 현재 중앙 배치에서는 `zoom_camera`에서 약 두 배 크기로 보이고 주변 영역은 좁아져야 한다. 두 영상의 차이는 카메라 간 위치 차이에서 생긴 시차가 아니다.
- **움직이지 않는 프레임:** 이 설정에는 장면 무작위화나 물리 진행이 없으므로 같은 카메라의 연속 프레임이 비슷하게 보이는 것이 정상이다. seed가 바뀐다는 이유만으로 큐브 자세가 바뀔 필요는 없다.
- **clipping 실험:** 기본 near_clip=1에서는 큐브가 보여야 한다. 뒤의 near_clip=550 실험은 앞쪽 표면을 가려 물체를 잘라내거나 사라지게 만드는 비교이며 밝기 조절이 아니다. `zoom_camera`에는 near_clip이 별도로 있으므로 전역 값만 바꾸면 기본 카메라에만 적용된다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/147_events_ext_replicator_object_camera  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config scene.yaml`로 이 폴더의 완전한 설정을 선택한다. 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. default_camera의 focal_length는 전역 camera_parameters의 24를 참조한다. zoom_camera는 같은 파라미터를 복제하고 48로 지정했다.
2. Simulate로 두 카메라 × 세 프레임을 생성한다. 파일명 카메라 부분으로 짝을 맞춘다.
3. 각 영상에서 큐브 너비를 픽셀 단위로 비교한다. 중심축과 물체 깊이가 같을 때 48 카메라에서 약 두 배 크기로 보인다.
4. near_clip을 550으로 바꾸어 500 거리 부근의 큐브가 clip plane 앞에 놓이는 상황을 관찰한다. 이 실험 후 값을 1로 되돌린다.

## 개념과 사용한 설정

pinhole은 한 점을 통과하는 광선으로 3D를 2D에 투영한다. 가로 화각은 2 atan(horizontal_aperture / (2 focal_length))다. 두 길이는 같은 단위를 사용하므로 비율이 중요하다. USD 카메라의 기본 축은 X 오른쪽, Y 위, -Z 전방이다. camera_parameters의 screen_width/height는 픽셀 수이고 near_clip/far_clip은 장면 거리다. 카메라가 원점을 바라보려면 +Z 쪽으로 이동시킨다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수만 바꾸는 실험

horizontal_aperture만 24에서 48로 바꾸어 focal_length 증가와 반대로 보이는 영역이 넓어지는지 확인한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.



## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Camera](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/camera.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
