# 148. Geometry — 한국어 실습

권장 학습 순서 **148** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t062`

기본 도형의 정적 충돌체와 동적 강체를 구분하고, 로컬 USD 메시와 변형 병을 각각 독립 설정으로 실행한다.

## 이 실습의 의도

보이는 도형의 종류와 물리 참여 방식을 별도로 설정하는 법을 배우는 실습이다. 기본 장면은 정적 바닥·녹색 큰 큐브와 동적인 빨간 구·파란 작은 큐브를 대비시켜, `collision`만 있는 물체와 `rigidbody`의 낙하·충돌 반응을 구분한다. 기본 `run.py`는 3프레임 설정을 준비하며 실제 물리·렌더링에는 native 실행 또는 GUI Simulate가 필요하고, 메시와 병은 별도 YAML을 선택한다.

## 실행 후 확인할 것

- **고정된 받침:** 기본 `scene.yaml`의 `floor`와 녹색 `static_cube`는 `physics: collision`이다. 물리 전후 큰 큐브 중심 `(100,50,0)` cm가 유지되는지 보고, 정적 충돌체가 중력으로 떨어지지 않는 이유를 설명한다.
- **동적 도형:** 빨간 구는 YAML 이름 `subject`로 `(-130,180,0)` cm에서, 파란 `falling_cube`는 `(100,210,0)` cm에서 시작한다. `gravity=981`, `simulation_time=1` 적용 후 구는 바닥 쪽으로, 작은 큐브는 큰 큐브 위로 내려와 충돌하는지 확인한다. 1초가 모든 물체의 완전 정착을 보장하는 기준은 아니다.
- **파일과 미리보기:** 초기화 화면의 공중 배치와 Simulate 후 `images/`의 기본 640×480 RGB 3장 및 라벨·분할 결과를 비교한다. `prepared.yaml`만 생성한 상태에서는 낙하나 결과 이미지가 없어도 정상이다.
- **메시 선택 시:** `mesh.yaml`의 `subject` 참조를 펼쳐 `models/box.usda`의 Mesh와 Material을 확인한다. 배율 `(1,1.5,0.7)`에 따라 세 축 길이가 달라지며, 이 설정에는 메시 강체 물리가 없어 바닥과 겹쳐 보이더라도 자동으로 밀려나지 않는다.
- **병 선택 시:** `bottle.yaml`은 청록색 체크무늬 병의 네 effector를 바꾼다. description에서 base=0.2–0.7, neck·horizontal·vertical=0.2–0.8 범위를 확인하고 Randomize scene에서 형상 차이를 본다. 병에 physics를 지정하지 않았으므로 낙하·충돌·물리 변형은 이 실습의 확인 대상이 아니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/148_events_ext_replicator_object_geometry  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config bottle.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml을 실행한다. 구인 subject와 falling_cube는 rigidbody이며 floor와 static_cube는 collision이다.
2. gravity 981, simulation_time 1의 결과에서 구가 바닥으로 떨어지고 작은 큐브가 큰 큐브와 충돌하는지 확인한다.
3. --config mesh.yaml을 실행하여 models/box.usda의 Mesh를 참조한다. stage에서 참조를 펼쳐 Mesh와 Material을 확인한다.
4. --config bottle.yaml을 embedded interface로 초기화하고 Randomize scene을 반복한다. 네 effector가 병의 몸통·목·바닥 모양을 어떻게 바꾸는지 관찰한다. 병에는 physics를 설정하지 않았다.

## 개념과 사용한 설정

subtype은 cone/cube/cylinder/disk/torus/plane/sphere, bottle, mesh를 구분한다. collision은 부딪힘만 제공하는 정적 장애물이고 rigidbody는 중력·속도·충돌 반응이 있는 물체다. mesh의 usd_path는 기존 USD 모델을 참조한다. USD reference는 모델의 형상과 재질을 합성하는 기능이며 파일 자체를 Python으로 import하는 것이 아니다. bottle은 내부 변형 모델의 effector를 제어한다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수만 바꾸는 실험

scene.yaml에서 구인 subject의 physics만 rigidbody에서 collision으로 바꾸어 구가 공중에 고정되는지 비교한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

bottle은 isaacsim.replicator.object 확장에 포함된 bottle 자원을 사용한다. 확장 설치 없이 병의 변형을 재현할 수 없다. 원문 예제 중 rigidbody가 적힌 병 설정도 있지만 지원 범위 설명에 맞춰 이 패키지는 병에 물리를 부여하지 않는다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `mesh.yaml`: 위 실습 단계에서 설명한 비교 설정
- `bottle.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Geometry](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/geometry.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
