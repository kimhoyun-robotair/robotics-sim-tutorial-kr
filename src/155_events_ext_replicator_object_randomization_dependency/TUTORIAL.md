# 155. Randomization Dependency: Incremental Examples — 한국어 실습

권장 학습 순서 **155** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t069`

독립 색상 난수 → 크기와 색을 공유하는 의존 난수 → 전체 그룹을 함께 움직이는 bin packing 순서로 세 완전한 설정을 비교한다.

## 이 실습의 의도

같은 큐브 여덟 개에 대해 독립적인 색 난수, 크기와 색이 연결된 난수, 공유 이동과 packing까지 연결한 난수를 차례로 비교합니다. `dependent.yaml`은 물체별 계수 하나를 크기와 빨강·파랑 채널에 함께 쓰고, `packed.yaml`은 모든 물체가 같은 `bin_translate`와 `bin_rotate`를 참조하게 하여 그룹 배치를 유지합니다. `run.py` 기본 호출은 YAML 준비만 수행하며, native IRO 생성에서는 각 설정의 0.5초 물리 진행 후 영상을 저장하므로 description의 샘플링 값과 최종 물리 위치를 구분해야 합니다.

## 실행 후 확인할 것

- **독립 설정의 기준:** 기본 `scene.yaml`을 native 실행한 뒤 description에서 subject가 8개이고 모두 scale 0.7인지 확인합니다. 각 RGB 채널은 0..1의 독립 난수이며 큰 물체일수록 붉다는 관계는 이 설정에 없습니다.
- **크기·색 의존성:** `--config dependent.yaml`의 같은 subject에서 `size=0.35+size_coef_i*(0.85-0.35)`, `R=size_coef_i`, `G=0`, `B=1-size_coef_i`를 검산합니다. 큰 큐브일수록 R이 크고 R+B=1이어야 하며, 조명 때문에 화면 픽셀값은 이 재질 색과 같지 않을 수 있습니다.
- **높이의 의미:** dependent의 초기 Y 위치는 `size*50`으로, 한 변 `size*100`인 큐브의 바닥을 지면에 맞춘 값입니다. 최종 RGB나 Stage 위치가 초기 위치와 다르면 먼저 물리 접촉·초기 겹침의 영향을 확인합니다.
- **그룹 공유와 packing:** `--config packed.yaml`의 description에서 모든 subject의 첫 translate와 `rotateY`가 같은 `bin_translate`, `bin_rotate` 값인지 확인합니다. 그 뒤의 harmonized transform은 물체별 배치이며 각 큐브의 size에 맞춘 AABB를 사용합니다.
- **물리 전후 구분:** packed는 초기 그룹 중심 Y를 130(cm)에 두고 중력 981로 0.5초 진행합니다. 초기 packing 배치와 저장 시점의 낙하·접촉 배치를 따로 관찰하며, 모든 물체가 원래 bin 안에 영구히 고정되거나 0.5초 안에 완전히 안정된다고 기대하지 않습니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/155_events_ext_replicator_object_randomization_dependency  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config packed.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml을 실행하면 여덟 큐브의 크기는 같고 색은 독립 난수다.
2. --config dependent.yaml을 실행한다. size_coef_0..7이 각각 크기와 빨강/파랑 채널을 함께 결정하므로 큰 물체가 붉어진다.
3. description에서 subject_i의 size가 size_min + size_coef_i × (size_max-size_min)인지, R+B=1인지 직접 두 물체를 골라 검산한다.
4. --config packed.yaml을 실행한다. bin_translate와 bin_rotate를 mutable 밖에 한 번 정의해 모든 물체가 같은 그룹 이동을 참조한다.
5. embedded interface에서 physics Play 전후를 비교한다. packing이 만든 초기 배치와 중력 후 접촉 배치는 구분해야 한다.

## 개념과 사용한 설정

의존성은 DAG(방향이 있고 순환이 없는 그래프)로 이해할 수 있다: size_coef → size/색 → AABB pitch → harmonizer transform → USD pose다. count:8은 난수 계수에도 적용되므로 nested macro $[/size_coef_$[index]]가 해당 물체와 계수를 연결한다. harmonized 속성은 모든 pitch가 모일 때까지 대기한다. bin 전역 이동을 물체 내부의 range로 옮기면 각 큐브가 서로 다른 이동을 갖게 되어 한 그룹으로 움직이지 않는다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수 실험

dependent.yaml의 size_max만 0.85에서 1.2로 바꾼다. 색 계수 범위는 그대로이지만 크기의 범위가 넓어지고 충돌 가능성이 커지는지 확인한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.



## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `dependent.yaml`: 위 실습 단계에서 설명한 비교 설정
- `packed.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Randomization Dependency: Incremental Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/randomization_dependency.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
