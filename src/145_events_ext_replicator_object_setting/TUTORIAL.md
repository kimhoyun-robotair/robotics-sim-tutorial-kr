# 145. Setting — 한국어 실습

권장 학습 순서 **145** · 물체 시뮬레이션과 YAML 무작위화 · 출처 ID `t059`

동일한 장면에 대해 출력 스위치, 해상도와 프레임 seed가 어떤 파일을 결정하는지 비교한다.

## 이 실습의 의도

같은 큐브 장면을 유지하면서 전역 해상도·출력 스위치·seed가 저장 결과를 어떻게 바꾸는지 비교하는 실습이다. 기본 `scene.yaml`은 RGB와 여러 정답을, `rgb_only.yaml`은 작은 RGB와 description을 저장하도록 구성해 출력 설정의 역할을 구분한다. `run.py`만 실행하면 설정 준비까지 진행하며, 아래 파일 비교는 native 생성 또는 GUI Simulate를 마친 뒤 수행한다.

## 실행 후 확인할 것

- **준비 결과:** `prepared.yaml`에서 선택한 설정의 `screen_width`, `screen_height`, `output_switches`, `num_frames`를 확인한다. `@OUTPUT@` 같은 경로 표식은 해소되지만 `$[/screen_width]` 등 IRO 매크로가 남는 것은 정상이다. 준비 단계가 이미지 렌더링까지 수행한 것은 아니다.
- **기본 설정:** 실제 `scene.yaml` 생성 후 `images/`의 기본 3장 RGB가 640×480인지 확인하고 라벨·분할·depth·normal 출력도 확인한다. 빨간 큐브와 바닥 모두 tracked 대상이므로 큐브 하나만 있다고 라벨도 하나여야 한다고 판단하지 않는다.
- **비교 설정:** 새 출력으로 `rgb_only.yaml`을 실제 생성하면 RGB는 320×240이며 description은 유지되고 라벨·분할·depth·normal 데이터는 생성되지 않아야 한다. 이름의 `rgb_only`는 description까지 끈다는 뜻이 아니다.
- **카메라와 파일명:** 저장 description에서 카메라 해상도가 전역 설정과 함께 바뀌었는지 확인한다. 기본 시작 seed=11·3프레임이면 파일명은 seed 11·12·13과 카메라 이름을 반영하며, description은 전체 장면의 GLOBAL 이름으로 기록된다.
- **정적인 부분과 난수:** 기본 장면은 `gravity=0`, `simulation_time=0`이고 큐브의 Y 회전만 -90–90도에서 선택한다. 낙하가 없는 것은 정상이며, 같은 seed의 대응은 먼저 description의 선택값으로 비교한다. GPU·렌더 설정이 다른 이미지의 완전 일치를 성공 기준으로 삼지 않는다.

## 준비와 실행 방식

Isaac Sim **5.1.0**, NVIDIA RTX 지원 GPU/드라이버, `isaacsim.replicator.object` 확장이 필요하다. Linux 설치 경로를 아래 `ISAAC_ROOT`에 지정한다. YAML 준비 도구는 Isaac Sim에 포함된 PyYAML을 사용하며 GPU를 시작하지 않는다. 일반 Python에 PyYAML이 이미 있으면 `python3 run.py`도 된다. 다른 튜토리얼 패키지나 공통 Python 모듈은 필요 없다. 이 폴더 전체만 복사해 사용할 수 있다.

이 학습은 공식 **IRO 확장의 native YAML workflow**다. `run.py`는 전체 설정을 가진 로컬 YAML의 경로를 정리하고 실제 Isaac Sim을 실행하는 도구다. 렌더러나 물리를 자체적으로 흉내 내지 않는다. `@PACKAGE@`와 `@OUTPUT@`는 준비 단계의 경로 표식이고, `$[...]`는 실행 시 IRO가 처리하는 매크로다. 원본 `scene.yaml` 대신 준비된 `prepared.yaml`을 IRO에 입력한다.

```bash
cd src/145_events_ext_replicator_object_setting  # 저장소 루트에서 실행; 폴더를 복사했다면 그 위치로 이동
ISAAC_ROOT="$HOME/isaacsim"
"$ISAAC_ROOT/python.sh" run.py --frames 3
# GUI 실행: configuration: 뒤의 절대 경로를 복사한다.
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch
# 파일로 생성하고 끝내는 native 실행:
"$ISAAC_ROOT/python.sh" run.py --isaac-root "$ISAAC_ROOT" --launch --headless --frames 3
```

`--config rgb_only.yaml`처럼 이 폴더의 다른 설정을 선택할 수 있다(아래 파일 목록 참조). 기본 출력은 이 폴더의 `output/<UTC시간>-<고유값>/`이다. `--output /절대/새폴더`로 지정할 수 있으며 기존 경로를 덮어쓰지 않는다. 출력 폴더 안 `prepared.yaml`은 사용한 설정이고, `images/`, `labels/`, `3d_labels/`, `segmentation/`, `descriptions/` 등이 IRO 결과다. 비활성화한 스위치의 데이터는 생성되지 않는다.

GUI에서 **Window > Extensions**를 열어 확장을 켠 후 **Tools > Action and Event Data Generation > Object SDG**로 간다. 공식 5.1 문서에는 이 패널이 **Object Detection SDG**로 표시되어 있지만 5.1에 설치된 0.4.13 확장 메뉴 이름은 Object SDG다. **Description File**에 `configuration:` 경로를 넣는다. **Initialize scene randomization**과 **Randomize scene**은 미리보기, **Simulate**는 결과 저장이다. 데이터 생성은 현재 stage를 새 장면으로 바꾸므로 작업 중인 stage는 먼저 별도로 저장한다.

`--steps`를 생략한 `--launch` GUI 실행은 데이터 생성이 끝나도 사용자가 창을 닫을 때까지 유지됩니다. `--frames`는 저장할 데이터 프레임 수이며 창의 수명과 별개입니다. `--steps 600`처럼 지정하면 native Kit 업데이트 600회 후 종료합니다. 시작·장면 로딩도 이 횟수에 포함되므로 짧게 제한하면 생성이 끝나기 전에 종료될 수 있습니다. `--headless`는 기존처럼 정해진 데이터 생성 후 종료합니다. 이 설정은 Kit의 공식 [`/app/quitAfter`](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.0.3/guide/configuring.html#app-quitafter-default-1)를 사용합니다.

## 실습

1. scene.yaml의 필수 키 여섯 개(version, num_frames, seed, output_path, screen_width, screen_height)를 찾는다.
2. scene.yaml을 실행해 640×480 RGB와 depth/normal 출력을 확인한다.
3. --config rgb_only.yaml로 다시 실행한다. 생성된 description에서 카메라의 screen_width도 320으로 바뀌었는지 확인한다.
4. output_name의 $[seed]와 $(camera_name)을 파일명과 대조한다. 시작 seed 11이면 프레임별 seed는 11, 12, 13이다.

## 개념과 사용한 설정

settings는 type 또는 harmonizer_type을 가진 객체 외의 설정이다. output_switches의 생략된 키는 기본적으로 켜질 수 있으므로 이 패키지는 모든 주요 스위치를 명시한다. camera_parameters가 전역 해상도를 매크로로 참조하므로 영상과 카메라 모델을 함께 바꾼다. parent_config는 상속을 위한 문법이지만 여기서는 각 YAML에 전체 설정을 반복하여 외부 파일에 의존하지 않는다.

IRO는 자체 장면에서 **Y-up, 1 단위 = 1 cm**를 사용한다. 일반적인 Isaac Sim 로봇 예제의 Z-up/미터 값을 그대로 가져오지 않는다. 기본 cube의 변 길이는 100 단위이며 scale 0.6이면 60 cm다. 중력 981은 이 좌표 단위에서 9.81 m/s²에 해당한다. 카메라 기본 시선은 -Z, 영상의 위는 +Y다. `tracked`는 라벨 대상이며 보이는 물체 모두가 자동으로 라벨 대상이 되는 것은 아니다.

## 한 변수만 바꾸는 실험

seed만 11에서 12로 바꿔 첫 프레임을 비교한다. 나머지 설정과 설치 환경이 동일할 때 이전 실행의 두 번째 seed와 대응하는지 관찰한다.

## 문제 해결

- `mapping values are not allowed here`는 YAML 들여쓰기/콜론을 먼저 확인한다. 탭 대신 공백을 사용한다.
- `ModuleNotFoundError: yaml`이면 위 명령의 Isaac Sim `python.sh`로 준비한다. `--help`는 PyYAML 없이도 실행된다.
- 카메라/물체가 안 보이면 F로 선택 물체에 초점을 맞추고, 시선 -Z와 단위 cm, clip 범위, transform 순서를 확인한다. 물리를 켠 장면은 초기 겹침 때문에 물체가 튀어나갈 수도 있다.
- 확장 메뉴가 없으면 Extensions에서 `isaacsim.replicator.object`가 실제로 활성화되었는지 확인한다. RGB 파일이 없으면 오류 로그와 카메라 존재 여부를 확인한다. 창이 떠 있다는 사실은 데이터 생성 성공이 아니다.
- 같은 seed는 장면 난수 재현을 돕지만 GPU/렌더 모드/자산 버전이 다르면 픽셀의 완전한 일치를 보장하지 않는다.

simulation_time은 물리 적분 시간, extra_rendering_time은 렌더링을 기다리는 시간이다. friction은 마찰, linear_damping/angular_damping은 운동 감쇠다. occlusion_threshold, min_area_threshold, max_area_threshold는 라벨 포함 조건을 바꾼다. skip_frames_with_no_visible_tracked_mutables를 켜면 빈 장면을 건너뛴다. 서로 다른 USD를 가져올 때 같은 basename을 쓰면 라벨 이름 충돌이 생길 수 있다.

## 포함 파일과 검증 범위

- `scene.yaml`: 기본 실습 설정
- `rgb_only.yaml`: 위 실습 단계에서 설명한 비교 설정
- `run.py`: 설정 준비 및 실제 확장 실행. `--help`로 옵션을 본다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.

## 출처

- [NVIDIA Isaac Sim 5.1 — Setting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/ext_replicator-object/setting.html)
- [IRO native 실행, embedded interface 및 출력 설명](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/action_and_event_data_generation/tutorial_replicator_object.html#run-from-the-ui)

설정과 한국어 실습은 위 문서를 기준으로 새로 작성했다. 설치된 5.1의 `isaacsim.replicator.object` 0.4.13 소스(`description/symbol.py`, `mutables/scene_dev.py`, `ui/object_detection_sdg_window.py`)에서 입력 키·장면 단위·UI 명칭을 대조했다.

설치 버전 차이: 공식 문서의 output_name 예시 $[camera] 대신, 0.4.13 `simple_writer.py`가 처리하는 $(camera_name)을 사용한다. `frame_$[seed]_$(camera_name)`은 IRO에서 seed를 먼저 정하고 writer에서 카메라 이름을 나중에 치환한다. descriptions는 카메라별 파일 대신 GLOBAL 이름으로 전체 장면을 기록한다.
