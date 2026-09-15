# 151. Transformation — 한국어 실습

권장 학습 순서 **151** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t065`

회전 이후 로컬 이동을 연결하여 카메라가 물체 주위를 돌게 만들고, 동일한 원리로 작은 큐브들을 구면 일부에 배치한다.

## 이 실습의 의도

이동과 회전의 순서가 위치를 결정한다는 점을 카메라 궤도와 큐브의 구면 배치로 비교합니다. 기본 장면은 중심이 `(0,50,0)`인 비대칭 직육면체를 고정하고 카메라의 Y 회전만 샘플링하며, `shell.yaml`은 같은 변환 원리로 큐브 60개를 반지름 220인 곡면 일부에 배치합니다. `run.py`의 기본 호출은 YAML 준비까지이며 실제 장면은 Object SDG에서 생성해야 하고, 회전은 시간에 따라 연속 재생되는 궤도 애니메이션이 아니라 프레임별 무작위 시점입니다.

## 실행 후 확인할 것

- **준비와 생성 구분:** `prepared.yaml`의 `default_camera.transform_operators`에 `translate_global → rotateY → rotateX → translate_local` 순서가 유지되는지 봅니다. 영상·해석된 값은 **Simulate** 또는 `--launch --headless` 후 `images/`, `descriptions/`에서 확인합니다.
- **기본 카메라:** **Randomize scene**을 반복하거나 저장 프레임을 비교하면 빨간 직육면체의 보이는 면이 달라져야 합니다. description의 Y 회전은 -60..60도이고, 관측 중심으로부터 로컬 +Z 이동 700과 X 기울기 -20도는 유지됩니다.
- **shell의 위치와 자세:** 비교 설정에서 큐브 중심은 원점으로부터 거리 220(cm)를 유지하면서 Y -70..70도, X -30..30도 범위의 곡면 일부를 따라 배치되어야 합니다. 뒤쪽 `rotateXYZ`는 개별 큐브의 자세를 바꾸므로 중심 위치 분포와 구분해 봅니다.
- **변환 순서의 효과:** Stage의 `xformOpOrder`와 YAML 순서를 대조합니다. 두 설정은 `gravity=0`, `simulation_time=0`이므로 공중의 큐브나 바닥과 겹친 직육면체가 낙하·접촉으로 정리되지 않는 것이 정상입니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/151_events_ext_replicator_object_transformation  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config shell.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml의 변환을 위에서 아래로 읽는다: 관측 중심으로 이동 → Y 회전 → X 기울임 → 카메라 로컬 +Z로 뒤로 물러남이다.
2. Randomize scene을 누르면 카메라가 주위를 돌아도 중앙의 비대칭 직육면체를 향하는지 본다.
3. --config shell.yaml을 실행한다. 회전 두 개 다음에 translate가 있으므로 위치가 직육면체가 아닌 반지름 220의 구면 일부를 따른다.
4. Stage에서 물체의 xformOpOrder를 확인하고 YAML의 순서와 비교한다.

## 개념과 사용한 설정

USD xformOps는 교환법칙이 성립하지 않는다. R×T와 T×R은 결과가 다르다. IRO 리스트는 위쪽이 전역, 아래쪽이 로컬이며 반복 이동에는 translate_global/translate_local처럼 접미사를 붙여 이름 충돌을 피한다. rotateX/Y/Z는 도 단위이고 orient는 [w,x,y,z] quaternion이다. transform은 4×4 행렬, scale은 일반적으로 리스트 끝에 둔다. rotateXYZ의 X는 Y보다 로컬, Y는 Z보다 로컬이다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수 실험

shell.yaml에서 translate 한 항목만 rotateY 앞쪽으로 이동한다. 객체 중심이 한 위치에 모이고 회전만 달라지는 이유를 변환 순서로 설명한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.



## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `shell.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Transformation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/transformation.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
