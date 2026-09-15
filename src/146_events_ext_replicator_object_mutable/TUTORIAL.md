# 146. Mutable — 한국어 실습

권장 학습 순서 **146** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t060`

count로 생성한 네 큐브와 라벨을 수집하지 않는 구를 비교하고, 별도 설정에서는 패키지 안의 텍스처 메시에 셰이더 무작위화를 적용한다.

## 이 실습의 의도

하나의 mutable 기술서에서 여러 객체를 만들 때 개체 번호·무작위 속성·라벨 수집 여부가 각각 어떤 역할을 하는지 배우는 실습이다. 기본 장면은 네 큐브의 간격을 고정하고 색·회전만 바꾸며, 녹색 구는 보이지만 라벨 대상에서 제외해 가시성과 tracked 설정을 구분한다. `shader.yaml`과 `shader_image.yaml`은 별도 재질 실험이며, 기본 `run.py`는 선택한 YAML을 준비할 뿐 실제 렌더링에는 native 실행 또는 GUI Simulate가 필요하다.

## 실행 후 확인할 것

- **기본 객체 구성:** IRO 초기화 후 `/World/Shapes`의 `subject_0`부터 `subject_3`에 대응하는 네 큐브를 찾는다. index 식에 따른 X 위치는 -195, -65, 65, 195 cm로 130 cm 간격이며, 난수화 후에도 이 간격이 유지되어야 한다.
- **달라지는 속성:** Randomize scene과 저장 description을 비교해 큐브의 색 성분은 0–1, Y 회전은 -45–45도 범위에서 선택되는지 확인한다. 매번 네 색이 모두 다르거나 구간 끝값이 나올 필요는 없으며, `simulation_time=0`이므로 물리 낙하도 요구하지 않는다.
- **보이지만 추적하지 않는 구:** 녹색 `untracked` 구가 시야 안에 있을 때 RGB에는 나타나지만 객체 라벨의 수집 대상에서 제외되는지 확인한다. 구는 다른 물체를 가릴 수 있고 바닥은 tracked 대상이므로 전체 라벨 개수를 네 큐브 수와 같다고 요구하지 않는다.
- **셰이더 설정 선택 시:** `shader.yaml`의 `subject`는 네 기본 큐브가 아닌 `models/textured.usda` 메시 하나다. 생성된 description과 재질에서 `texture_rotate` -90–90도, `texture_scale` 각 성분 0.5–2, `diffuse_tint` 각 성분 0.2–1을 대조하고 고정 형상 위의 체크무늬만 바뀌는지 본다.
- **이미지 변환 선택 시:** `shader_image.yaml`은 같은 셰이더 무작위화에 `diffuse_texture: <invert_color>`를 추가한다. 원본 `checker.png`와 생성 이미지의 색 반전 효과를 비교한다. `prepared.yaml`에서 로컬 USD 경로가 해소된 것과 실제 텍스처가 렌더링된 것은 따로 확인한다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/146_events_ext_replicator_object_mutable  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config shader.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml을 준비해 embedded interface로 초기화한다. Stage의 /World/Shapes 아래 subject_0부터 subject_3에 해당하는 prim을 찾는다.
2. Randomize scene을 누른다. 네 객체의 index 기반 위치는 유지되고 각각의 색과 Y 회전은 바뀌는지 관찰한다.
3. Simulate 후 녹색 untracked 구가 RGB에는 보이지만 라벨 수집 대상에서 제외되는지 확인한다.
4. --config shader.yaml을 실행한다. 제공된 models/textured.usda와 checker.png가 있는지 확인하고 체크무늬 회전·타일 크기·색조가 프레임마다 바뀌는지 본다.

## 개념과 사용한 설정

mutable의 type은 camera/geometry/light 중 하나다. count: 4는 같은 기술서에서 네 객체를 만들고 index 0..3을 부여한다. transform_operators는 USD의 xformOpOrder로 표현되는 순서 있는 변환이다. shader_attributes는 물체의 위치가 아닌 OmniPBR의 diffuse_tint, texture_rotate, texture_scale 입력을 바꾼다. 로컬 USD의 MaterialBindingAPI가 Mesh와 MDL 재질을 연결한다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수만 바꾸는 실험

scene.yaml에서 count만 4에서 2로 바꿔 subject_0, subject_1만 생성되는지 확인한다. 식의 중앙 기준 1.5는 그대로이므로 두 객체가 왼쪽에 남는 이유를 설명한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

원문은 diffuse_texture의 color_map, transform, add_noise, apply_blur, color_shift, invert_color, sobel_edges, random_mutation도 소개한다. `--config shader_image.yaml`은 로컬 체크무늬에 색 반전을 실제 적용한다. 원문의 `distribution_type: texture` 사전 문법은 설치된 0.4.13 parser가 받지 않으므로, 이 설정은 `GMesh.step()`이 처리하는 `diffuse_texture: <invert_color>` 문자열을 사용한다. 이 연산은 이미지 변환이며 물리 텍스처 특성을 측정하지 않는다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `shader.yaml`: 위 실습 단계에서 설명한 비교 설정
- `shader_image.yaml`: 로컬 텍스처 색 반전
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Mutable](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/mutable.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
