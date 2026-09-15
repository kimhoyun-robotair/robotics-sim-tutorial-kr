# 153. Macro — 한국어 실습

권장 학습 순서 **153** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t067`

전역 값, 같은 객체의 값, 리스트 항목, 프레임 seed를 참조하는 매크로를 한 장면에서 비교한다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/153_events_ext_replicator_object_macro  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
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

1. spacing 130과 subject의 translate 식을 읽는다. 절대 참조 $[/spacing]가 세 객체의 간격에 공통으로 적용된다.
2. subject의 own_height는 같은 mutable의 index를 사용한다. transform_operators 안에서는 $[../own_height]로 한 단계 위 mutable에 접근한다.
3. palette는 세 색의 리스트다. $[/palette~$[index]]는 먼저 내부 index를 계산한 다음 해당 리스트 항목 전체를 가져온다.
4. Simulate 후 descriptions의 카메라 파라미터가 문자열이 아닌 사전으로 해석되었는지 확인한다. dome_light 강도가 key_light보다 50..100 큰지도 비교한다.

## 개념과 사용한 설정

매크로는 셸 변수나 Python f-string이 아닌 IRO의 $[...] 문법이다. /로 시작하면 설정 루트, ../는 부모, ~0은 리스트 인덱스다. 값 전체가 하나의 참조이면 사전/리스트를 그대로 전달할 수 있다. 표현식 속 참조는 산술 계산에 사용된다. count는 사전들을 확장하고 index를 붙인다. $[seed]는 시작 seed + 프레임 인덱스, 5.1 문서는 출력 이름의 $[frame]/$[camera]도 소개하지만 설치된 0.4.13에서는 이 두 심볼이 정의되지 않는다. 이 패키지는 실제 writer가 치환하는 $(camera_name)을 사용한다. 의존 관계에 순환이 생기면 해석 오류가 난다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 관찰과 성공 기준

세 큐브의 색은 palette와 대응하고 높이는 40,60,80이다. 회전은 frame seed에 따라 순환한다. key_light의 값을 먼저 구해야 dome_light 범위를 구할 수 있으므로 파일에 적힌 순서가 실행 순서가 아니다.

spacing만 130에서 180으로 바꿔 모든 큐브 사이 간격이 함께 커지는지 본다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

안전한 오류 실습은 별도 YAML 복사본에서 spacing: $[/spacing]로 자기 참조를 만드는 것이다. parser가 순환을 보고해야 하며 이는 난수 범위 오류와 구별된다. 실행 완료 여부를 성공 로그 문구만으로 판단하지 말고 출력된 description 값을 확인한다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Macro](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/macro.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
