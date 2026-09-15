# 150. Mutable Attribute — 한국어 실습

권장 학습 순서 **150** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t064`

폴더에서 로컬 USD를 뽑고, 이산 회전 집합과 연속 위치 범위를 조합한다. 별도 frustum 설정은 카메라가 보는 공간 안에서 객체 중심을 샘플링한다.

## 이 실습의 의도

같은 `subject` 정의에서 USD 파일 선택(`folder`), 회전 선택(`set`), 위치 샘플링(`range`)을 독립적으로 바꾸며 각 분포가 실제 장면의 무엇을 바꾸는지 구분합니다. 비교 설정 `frustum.yaml`은 카메라 시야를 기준으로 중심 위치를 뽑는 예이며, 두 설정 모두 중력과 물리 진행 시간이 0이어서 물체가 공중에 유지되는 것이 의도입니다. `run.py`만 실행하면 경로를 치환한 `prepared.yaml`을 만들고 종료하며, 실제 영상·description은 Object SDG의 **Simulate** 또는 `--launch --headless` 실행에서 생성합니다.

## 실행 후 확인할 것

- **설정 준비:** 콘솔의 `configuration:` 경로를 열어 기본 `subject.count=4`, `models`의 절대 경로, 요청한 `num_frames`를 확인합니다. 이 파일에 `$[...]`가 남아 있는 것은 정상이며 IRO가 실행할 때 해석합니다.
- **기본 장면의 선택값:** native 생성 후 `descriptions/`에서 각 subject의 `usd_path`가 `box.usda` 또는 `pyramid.usda`인지, `rotateY`가 -45·0·45 중 하나인지 확인합니다. 같은 파일이나 회전이 여러 번 선택되어도 정상이며 세 프레임에 모든 선택지가 나올 필요는 없습니다.
- **위치와 영상의 대응:** 기본 subject의 초기 `translate`가 X -160..160, Y 50..150, Z -100..100(cm)에 있는지 확인하고 같은 프레임 RGB와 비교합니다. 위치와 모양뿐 아니라 `dome_light.intensity`도 300..900에서 바뀌므로 밝기 변화가 예상됩니다.
- **시야 안 샘플링 비교:** `--config frustum.yaml`로 별도 생성하면 빨간 큐브 10개의 중심이 `distance_min=250`, `distance_max=650`, `screen_space_range=0.65`로 제한된 영역에 배치됩니다. 카메라 뷰와 description을 함께 보고, 큰 물체의 외곽 전체가 영상 안에 들어온다는 보장으로 해석하지 않습니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/150_events_ext_replicator_object_mutable_attribute  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config frustum.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml의 folder 분포는 models/*.usda에서 파일 하나를 선택한다. set은 -45/0/45도 중 하나, range는 start와 end 사이 값이다.
2. 세 프레임을 생성하고 descriptions에서 usd_path, rotateY, translate를 찾아 실제 선택값이 범위를 만족하는지 확인한다.
3. --config frustum.yaml을 실행한다. 카메라 변환을 비워 카메라 로컬 좌표와 월드 좌표를 일치시켰다.
4. screen_space_range 0.65와 거리 250..650을 확인하고 큐브 중심이 화면 중앙 영역에 모이는지 관찰한다.

## 개념과 사용한 설정

분포가 있는 값은 초기화 시 symbol이 되고 매 프레임 숫자·경로로 해석된다. folder는 일치하는 파일이 있어야 하고 set은 미리 정한 선택지, range는 숫자 구간이다. camera_frustum은 화면 투영 크기가 고르게 분포하도록 거리를 단순 균등 샘플링하지 않는다. 공식 식 d=dmin*dmax/(dmin+(dmax-dmin)*u)를 사용한다. harmonized는 독립 난수 대신 harmonizer가 조정한 값을 받는 다섯 번째 방식이다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수 실험

frustum.yaml의 screen_space_range만 0.65에서 0.25로 바꾸어 중심 분포가 화면 중앙으로 좁아지는지 비교한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

5.1 문서 본문에서는 frustum이라고 축약하지만 실행 키는 camera_frustum이다. 원문 코드의 $(camera_parameters)는 IRO 매크로 문법과 맞지 않으므로 이 설정은 실제 파서가 지원하는 $[/camera_parameters]를 사용한다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `frustum.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Mutable Attribute](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable_attribute.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
