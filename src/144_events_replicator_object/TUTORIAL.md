# 144. Object Simulation and Synthetic Data Generation — 한국어 실습

권장 학습 순서 **144** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t058`

정적인 받침 위로 색과 초기 자세가 다른 큐브 여섯 개를 떨어뜨리고 RGB·경계 상자·분할·재현용 description을 함께 저장한다. 공식 표/상자 예제의 파이프라인을 기본 도형으로 재작성하여 외부 모델 없이 실행한다.

## 이 실습의 의도

IRO의 YAML 규칙이 초기 배치, 물리 낙하, 센서 촬영, 라벨 저장으로 이어지는 전체 흐름을 배우는 실습이다. 바닥에는 정적 충돌을, 여섯 큐브에는 강체 물리를 부여하여 무작위 배치 직후와 1.5초 물리 진행 후의 차이를 관찰한다. 기본 `run.py`는 3프레임용 `prepared.yaml`만 만들며, 실제 데이터 생성에는 `--launch --headless` 또는 GUI의 Description File 지정과 Simulate가 필요하다.

## 실행 후 확인할 것

- **준비 단계:** 터미널의 `configuration:` 경로에 `prepared.yaml`이 생기고 `num_frames=3`, 출력 절대경로가 반영되었는지 확인한다. 이 파일만 있고 RGB가 없는 것은 `--launch` 없는 실행의 정상 결과다.
- **초기 배치와 물리:** GUI의 Initialize/Randomize 미리보기에서 `subject` 큐브 6개의 색·자세·초기 높이가 달라지는지 본다. 시작 Y 높이는 130–230 cm이며, Simulate에서는 중력 981 cm/s²로 1.5초 진행한 뒤 촬영한다. 바닥은 떨어지지 않으며 큐브가 바닥·서로와 충돌하는지 확인한다.
- **저장 결과:** native 생성 완료 후 `images/`에서 기본 카메라의 640×480 RGB 3장과 `labels/`, `3d_labels/`, `segmentation/`, `descriptions/`의 대응 결과를 확인한다. Randomize scene 미리보기만으로 저장 파일이 생기지는 않는다.
- **라벨 해석:** 보이는 tracked 큐브를 RGB와 경계 상자·분할에 대조한다. 바닥도 `tracked:true`이므로 전체 라벨 줄 수를 큐브 수 6과 같다고 요구하지 않는다. 가림·시야와 라벨 필터에 따라 보이는 큐브 라벨 수는 줄어들 수 있다.
- **시간과 재현:** `simulation_time=0`인 별도 실행에서는 낙하 전 배치를 촬영하는지 비교한다. 1.5초 실행도 모든 큐브의 완전 정착을 보장하지 않으며, 기록된 description으로 선택된 장면 값을 확인한다. 짧은 `--steps` 종료만으로 요청한 데이터 생성이 완료됐다고 판단하지 않는다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/144_events_replicator_object  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

`--config scene.yaml`로 이 폴더의 완전한 설정을 선택한다. 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

## 실습

1. 아래 명령으로 설정을 준비하고 출력된 configuration 절대 경로를 Object SDG의 Description File에 붙인다.
2. Initialize scene randomization을 누른 뒤 Randomize scene을 세 번 눌러 시작 자세를 비교한다. 이 미리보기 단계는 이미지 저장이 아니다.
3. Simulate를 눌러 세 프레임을 생성한다. 중력은 각 프레임의 무작위 배치 이후 1.5초 동안 계산된다.
4. 출력 descriptions의 한 YAML을 새 실행의 --config로 지정해 한 장면을 다시 생성한다. 재현 시에도 별도 output 디렉터리가 생성된다.
5. Scene Editing 실습: 초기화된 장면에서 Create > Mesh > Cube를 만들고 Translate와 Scale로 두 물체를 감싼다. 그 큐브를 선택한 상태로 Toggle visibility of selected region을 눌러 선택 범위 안 물체의 가시성을 확인한다.

## 개념과 사용한 설정

YAML은 장면의 확률 규칙이고 USD stage는 그 규칙을 적용한 실제 장면이다. parser가 매 프레임 값을 정하고, geometry prim을 배치하고, PhysX를 계산한 뒤 Replicator writer가 센서 결과를 기록한다. tracked는 라벨 수집 대상 여부이며 rigidbody는 실제 동역학 대상 여부다. 둘은 독립 설정이다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수만 바꾸는 실험

simulation_time만 0으로 바꿔 다시 실행한다. 큐브가 떨어지기 전 공중에 있는 영상과 비교한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

공식 파이프라인의 모델 학습/배포는 TAO 6.0의 별도 작업이다. 이 패키지는 데이터를 실제 IRO로 생성하는 단계까지 구현한다. Docker에서도 폴더 전체를 /work로 마운트하고 같은 run.py로 /work 안 출력 경로를 준비하면 된다. 기본 도형의 색상 재질은 Isaac Sim의 내장 OmniPBR를 사용한다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Object Simulation and Synthetic Data Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
