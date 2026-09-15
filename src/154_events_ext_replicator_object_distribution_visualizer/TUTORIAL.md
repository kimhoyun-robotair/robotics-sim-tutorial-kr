# 154. Distribution Visualizer — 한국어 실습

권장 학습 순서 **154** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t068`

Distribution Visualizer의 점구름을 사용해 회전과 반지름 범위가 만드는 위치 분포를 보고 같은 범위를 실제 IRO description에 적용한다.

## 이 실습의 의도

Distribution Visualizer에서 변환별 난수 구간이 합성되어 어떤 위치 분포를 만드는지 먼저 보고, 같은 구간을 IRO 장면의 Torus 한 개에 적용해 비교합니다. GUI 점구름은 가능한 중심 위치의 표본이고 `scene.yaml`의 Torus는 그 분포에서 프레임마다 뽑힌 한 사례이므로 두 화면의 물체 수가 다른 것이 의도입니다. `run.py`는 기본적으로 YAML만 준비하며 `--launch --headless`도 장면 데이터 생성까지만 수행하므로 Visualizer의 선택·슬라이더 조작은 별도 GUI 실습으로 확인합니다.

## 실행 후 확인할 것

- **선택한 대상과 UI:** GUI에서 Torus를 선택하고 **Apply Preset xformOps** 후 다시 선택했을 때 Visualizer의 대상 Prim과 Stage 선택이 일치하고 `rotateY → rotateX → translate`가 보이는지 확인합니다.
- **분포 모양:** Y 회전 -120..120도, X 회전 -30..30도, 로컬 Z 이동 150..300을 적용하면 점구름이 두께가 있는 구 껍질 일부처럼 보여야 합니다. 점구름 애니메이션은 가능 위치의 표시이며 실제 Torus 여러 개를 물리 시뮬레이션한 결과가 아닙니다.
- **한 변수 비교:** translate Z의 start/end를 모두 150으로 맞추면 반지름 변화가 없어져 곡면이 얇아져야 합니다. 각도 구간을 줄이면 해당 각도 방향의 펼쳐짐이 줄어드는지 비교합니다.
- **YAML 결과와 대응:** Object SDG에 `prepared.yaml`을 로드하고 **Simulate**하면 한 프레임의 `subject` Torus가 위 구간의 한 위치에 나타납니다. `descriptions/`에서 두 회전과 translate Z 범위를 확인하고 `images/`의 Torus와 비교합니다. 기본 3프레임만으로 전체 확률 밀도가 균일한지 판단하지 않습니다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/154_events_ext_replicator_object_distribution_visualizer  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
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

1. Isaac Sim에서 Window > Extensions로 isaacsim.replicator.object를 켠다. Tools > Action and Event Data Generation > Distribution Visualizer를 연다.
2. 빈 stage에서 Create > Mesh > Torus와 Create > Light > Dome Light를 만든다. Torus를 선택하고 F로 초점을 맞추며 viewport의 렌더 모드를 Path Tracing으로 바꾼다.
3. 빈 곳을 클릭했다가 Torus를 다시 선택한다. Apply Preset xformOps를 누르고 다시 선택해 rotateY, rotateX, translate 목록이 나타나게 한다.
4. rotateY start=-120, end=120; rotateX start=-30, end=30; translate X/Y start=end=0, Z start=150, end=300으로 지정한다. value는 현재 자세, start/end는 가능한 범위다.
5. 애니메이션되는 점구름이 구 껍질 일부를 이루는지 본다. 본 패키지 scene.yaml을 Object SDG에서 초기화하고 Randomize scene을 눌러 같은 분포의 실제 Torus를 비교한다.

## 개념과 사용한 설정

한 prim은 순서 있는 xformOps를 가진다. 각 op의 값을 무작위화하면 최종 월드 위치 분포는 op별 구간의 단순 합이 아니라 행렬 합성 결과가 된다. Visualizer는 가능한 위치의 표본을 점구름으로 그리는 편집 도구다. 한 번의 점구름 표시가 확률 밀도에 대한 정량적 보증은 아니다. scene.yaml은 같은 범위를 렌더링 가능한 장면에 포함한다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수 실험

translate Z의 end만 300에서 150으로 바꾼다. 반지름 변동이 사라지고 두께 없는 곡면으로 가까워지는지 관찰한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

이 패키지의 기본 학습 경로는 GUI다. run.py --launch --headless는 YAML 기반의 실제 장면 생성만 수행하며 Distribution Visualizer UI를 검증하지 않는다. Visualizer의 조작은 위 절차로 따로 실행한다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

YAML 구문과 launcher 준비 동작은 GPU 없이 검사할 수 있다. 실제 RTX 결과, PhysX 접촉, GUI 표시 검증은 별개다. `tutorial.json`의 `verification: not_run`은 이 패키지의 simulator 실행 결과를 아직 검증하지 않았다는 뜻이다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Distribution Visualizer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/distribution_visualizer.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.
