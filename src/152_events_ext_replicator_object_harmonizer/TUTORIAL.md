# 152. Harmonizer — 한국어 실습

권장 학습 순서 **152** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t066`

순열로 네 물체의 자리만 바꾸고, bin packing으로 열두 큐브의 부피를 고려해 겹침 없이 배치한다.

## 이 실습의 의도

여러 물체의 난수를 함께 조정해야 하는 경우를 순열과 공간 배치로 보여 줍니다. 기본 `scene.yaml`은 물체의 색·회전은 유지하면서 네 자리를 중복 없이 배정하고, `bin_pack.yaml`은 큐브 12개의 경계 상자를 받아 정해진 공간 안에 배치합니다. `run.py` 기본 호출은 설정 준비만 수행하며 실제 배치와 출력은 IRO 실행에서 만들어지고, 두 설정 모두 물리 진행 시간이 0이므로 packing 결과는 낙하 후 쌓인 모습이 아닙니다.

## 실행 후 확인할 것

- **실제 생성 결과:** **Simulate** 또는 `--launch --headless` 후 `images/`와 `descriptions/`를 확인합니다. `prepared.yaml`만 생겼다면 아직 harmonizer의 결과를 관찰한 단계가 아닙니다.
- **중복 없는 자리:** 기본 description에서 네 subject의 `slot`을 모아 정렬하면 `[0,1,2,3]`이어야 합니다. 각각의 X 좌표는 `(slot-1.5)*125`에 따라 -187.5, -62.5, 62.5, 187.5(cm)를 하나씩 차지합니다.
- **물체 식별과 자리 구분:** 같은 subject의 색은 `[index/3,0.2,1-index/3]`, Y 회전은 `index*25`도입니다. 프레임을 비교할 때 색과 회전은 해당 물체를 따라가고 자리 배정이 바뀌는지 봅니다. 연속 두 번 같은 순열이 나오는 것은 실패가 아닙니다.
- **packing 비교:** `--config bin_pack.yaml`에서 `pack.bin_size=[300,220,300]`, 각 pitch의 최소/최대가 `[-30,-30,-30]`/`[30,30,30]`인지 확인하고, Stage에서 60 cm 큐브 12개의 초기 배치를 봅니다. bin은 공간 제약이며 컨테이너 메시가 없고, 전체 배치에는 `[0,120,0]` 이동이 추가됩니다.
- **기존 검증의 범위:** [RUNTIME_CHECK.md](RUNTIME_CHECK.md)는 기본 순열 설정의 1프레임 이미지와 주석 생성 기록입니다. 이 기록만으로 bin packing이나 GUI 조작까지 실행 검증된 것으로 판단하지 않습니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/152_events_ext_replicator_object_harmonizer  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config bin_pack.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml에서 subject의 slot은 harmonized이고 pitch는 원래 index다.
2. Randomize scene을 반복하고 빨강/파랑 계열의 물체가 자리를 바꾸되 회전과 색은 자신의 index를 따라가는지 본다.
3. 출력 description에서 네 slot을 정렬하면 항상 0,1,2,3이어야 한다. 독립 set 분포라면 중복이 생길 수 있지만 순열은 중복 없이 자리를 배정한다.
4. --config bin_pack.yaml을 실행한다. bin_size는 [300,220,300], pitch는 한 변 60 큐브의 로컬 AABB다. 이 상자는 공간 제약이며 눈에 보이는 컨테이너 메시를 자동 생성하지 않는다.

## 개념과 사용한 설정

harmonizer는 각 객체에서 제출한 pitch를 모두 받은 후 값을 계산한다. 최초 해석에서 AWAITING_HARMONIZATION 상태가 생기고, 입력 수집 → 조정 → 재해석 순서를 거친다. permutate는 입력들을 섞어 반환한다. bin_pack은 AABB(축과 나란한 최소/최대 경계) 크기를 기준으로 로컬 transform을 돌려준다. scale이 0.6인 기본 100 단위 큐브의 AABB는 ±30이다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수 실험

bin_pack.yaml에서 bin_size만 [300,220,300]에서 [120,120,120]으로 줄인다. 공간 부족 시 모든 객체를 원하는 대로 배치할 수 없는 결과와 로그를 확인한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

실제 USD 메시의 크기가 매번 달라지는 경우 pitch: local_aabb로 런타임 경계를 얻을 수 있다. 이 경로는 USD 장면 초기화가 필요한데, 본 실습의 고정 큐브는 독립적으로 검산 가능한 ±30을 명시한다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `bin_pack.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Harmonizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/harmonizer.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
