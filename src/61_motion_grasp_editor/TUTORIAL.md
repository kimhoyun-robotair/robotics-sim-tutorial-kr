# 61. 한 번 만든 파지 자세를 다른 물체 위치에 사용하기

## 이번에 배우는 것

**Grasp Editor에서 머그를 잡는 자세를 저장하고, 물체의 월드 위치가 바뀌었을 때 그리퍼의 목표 자세를 계산합니다.**

머그가 테이블 위에서 옮겨졌다고 매번 손가락과 머그의 관계를 다시 만들 필요는 없습니다. “머그를 기준으로 손이 어디에 있어야 하는가”를 저장하면, 새 머그 위치에 같은 파지를 적용할 수 있습니다. 여기서 기준 위치와 축을 가진 좌표를 **프레임(frame)**이라고 부릅니다.

| 파일 또는 데이터 | 기준과 역할 |
|---|---|
| `run.py` | 공식 장면과 Grasp Editor를 여는 실행기 |
| `authored_grasps.yaml` | 사용자가 작성한 물체 기준 파지 자세와 손가락 관절값 |
| `--object-position`, `--object-quaternion` | 계산에 제공하는 물체의 월드 자세 |
| `compute_pose.py` | 저장된 상대 자세를 월드 목표 자세로 변환 |
| `target.json` | 그리퍼의 월드 위치와 WXYZ 순서 회전 |

이 실습은 파지를 작성하고 목표 자세를 계산하는 데까지 진행합니다. 목표까지 팔을 움직이는 경로 계획은 별도의 작업입니다.

## 1. 공식 장면에서 파지 하나 작성하기

Isaac Sim 5.1 GUI와 지원 NVIDIA GPU가 필요합니다. 공식 [Grasp Editor 실습 ZIP](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/4d1aeb9e29208ad4bf35f0a38d105e49/Grasp_Editor_Tutorial_Stage.zip)을 내려받아 이 튜토리얼의 `input/`에 두세요. 아래 명령은 저장소 루트 기준입니다.

```bash
mkdir -p src/61_motion_grasp_editor/input src/61_motion_grasp_editor/output
unzip -n src/61_motion_grasp_editor/input/Grasp_Editor_Tutorial_Stage.zip -d src/61_motion_grasp_editor/input
~/isaacsim/python.sh src/61_motion_grasp_editor/run.py --stage src/61_motion_grasp_editor/input/Grasp_Editor_Tutorial_Stage/grasp_editor_tutorial.usd
```

압축 안의 `Isaac/`, `Library/`와 USD 사이 상대 경로를 유지하세요. 설치 위치가 다르면 `~/isaacsim`을 바꿉니다. 창은 직접 닫을 때까지 열려 있습니다. 이 실행기는 `app.update()`로 편집 작업을 받을 뿐, 파지를 자동 작성하지 않습니다.

1. **Tools > Robotics > Grasp Editor**를 엽니다. Selection Frame에서 Panda hand articulation과 `/World/mug`를 선택하세요. 실제 경로는 Stage에서 우클릭한 뒤 **Copy Prim Path**로 확인할 수 있습니다.
2. Export 경로를 이 튜토리얼의 `output/authored_grasps.yaml`에 해당하는 **절대 경로**로 지정합니다. 편집기는 기존 파일을 덮어쓰므로 아직 없는 이름을 사용하세요.
3. **Ready**를 누릅니다. 편집기는 머그에 강체와 충돌 설정을 적용해 힘을 받을 수 있게 준비합니다.
4. **Select Frames of Reference**에서 물체는 `/World/mug`, 그리퍼는 `panda_hand`의 기준 prim을 선택하고 **Finalize**합니다. 손목 대신 팔 전체의 base를 기준으로 고르면 저장하는 상대 자세가 달라집니다.
5. **Joint Settings**에서 `panda_finger_joint1`을 Part of Gripper로 지정합니다. 열린 위치 0.04 m, 닫힌 위치 0 m로 시작하세요. 반대 손가락은 mimic 관계를 확인하고 중복 제어하지 않습니다. 시험 시작값으로 Grasp Speed 0.02 m/s, Max Effort Magnitude 10 N을 사용할 수 있습니다.
6. **Utils > Mask Collision**으로 배치 중 충돌을 잠시 가리고 머그의 잡을 부분을 손가락 사이에 놓습니다. **Show Physics Colliders**로 손가락이 실제로 닿을 표면을 확인하세요.
7. **Author a Grasp > Simulate**를 실행합니다. 손가락이 닫히고 머그가 유지되는지 봅니다. **Add External Rigid Body Forces**에서 force 0.5 N, torque 0으로 시험해 작은 외력이 가해질 때도 유지되는지 살펴보세요.
8. Confidence를 자신의 평가값으로 입력하고 **Export**합니다. 첫 파지 이름을 확인해 두세요. 아래 계산 예제는 `grasp_0`을 사용합니다.

### 설정에서 볼 부분

저장한 YAML에서 다음 항목의 의미를 구분해 보세요.

| 항목 | 무엇을 저장하나요? |
|---|---|
| `position`, `orientation` | 물체 프레임에서 본 그리퍼 프레임의 위치와 회전 |
| `pregrasp_cspace_position` | 접근할 때의 열린 손가락 관절값 |
| `cspace_position` | 물체를 잡고 있을 때의 관절값 |
| `confidence` | 작성자가 입력한 평가값 |
| `object_frame_link`, `gripper_frame_link` | 파지 작성에 사용한 프레임 경로 |

손가락의 최종 관절값은 물체와 접촉한 위치에 따라 달라집니다. 닫힌 목표를 0으로 두어도 접촉 후의 `cspace_position`이 반드시 0일 필요는 없습니다. Confidence도 시뮬레이터가 계산한 성공 확률은 아닙니다.

### 실행 결과 확인하기

Export한 파일이 생겼는지 확인하고 **Import**에서 다시 읽어 같은 파지를 표시해 보세요. 작성 때와 같은 물체·그리퍼 프레임을 선택하면 상대 자세가 복원되어야 합니다. 파일에 프레임 경로가 적혀 있어도 Import 시 자동으로 올바른 프레임을 선택해 주지는 않습니다.

`Skip Sim`은 시뮬레이션 없이 현재 자세를 저장할 때 사용합니다. 이 경우 파일 생성은 확인할 수 있지만 접촉 안정성을 시험한 결과로 해석하지 마세요.

## 2. 작성한 파지를 월드 목표 자세로 계산하기

편집 창을 닫은 뒤, 저장소 루트에서 실행하세요.

```bash
~/isaacsim/python.sh src/61_motion_grasp_editor/compute_pose.py --grasp-file src/61_motion_grasp_editor/output/authored_grasps.yaml --name grasp_0 --object-position 0.5 0 0.2
```

물체 프레임이 월드의 `(0.5, 0, 0.2)` m에 있다고 가정합니다. 회전을 지정하지 않으면 WXYZ 순서의 `(1, 0, 0, 0)`, 즉 회전 없음입니다. 스크립트는 headless 앱에서 계산하고 콘솔과 `output/target.json`에 결과를 쓴 뒤 종료합니다.

### 코드에서 볼 부분

```python
spec = import_grasps_from_file(str(args.grasp_file.resolve()))
position, quaternion = spec.compute_gripper_pose_from_rigid_body_pose(
    args.name, np.array(args.object_position), np.array(args.object_quaternion)
)
```

첫 호출은 실제 YAML의 파지 목록을 읽습니다. 두 번째 호출은 선택한 파지의 상대 자세와 입력한 물체 자세를 합성합니다. 설치된 5.1 구현의 위치 계산은 다음 관계입니다.

```text
그리퍼 월드 위치 = 물체 월드 회전 × 물체 기준 그리퍼 위치 + 물체 월드 위치
```

먼저 상대 위치를 물체 방향에 맞춰 회전하고, 그 다음 물체의 월드 위치만큼 옮깁니다. 물체가 회전하면 손의 접근 방향과 상대 위치도 함께 돌아가야 하기 때문입니다.

### 실행 결과 확인하기

`target.json`의 `grasp`가 선택한 이름인지, `position`이 세 값인지, `quaternion_wxyz`가 네 값인지 확인하세요. 수치는 직접 작성한 파지에 따라 달라집니다. 이 파일의 위치는 손가락 끝의 임의 점이 아니라 **작성 때 선택한 그리퍼 프레임의 목표**입니다.

## 3. 상대 자세를 재사용하는 흐름 정리

```text
머그와 손의 프레임 선택
    → 머그 기준 파지 자세를 YAML에 저장
    → 새 머그의 월드 자세 입력
    → 그리퍼의 새 월드 목표 자세 계산
```

좌표 변환을 정확히 하려면 물체 인식 결과의 기준 프레임과 파지 파일의 물체 프레임이 같아야 합니다. 예를 들어 인식기는 머그 바닥 중심을 주는데 파지는 머그 몸통 중심을 기준으로 만들었다면, 그 차이를 먼저 변환해야 손이 의도한 곳에 놓입니다.

## 4. 간단한 확인 실험

동일한 파지에서 물체의 x 위치만 0.5 m에서 0.6 m로 바꿔 보세요.

```bash
~/isaacsim/python.sh src/61_motion_grasp_editor/compute_pose.py --grasp-file src/61_motion_grasp_editor/output/authored_grasps.yaml --name grasp_0 --object-position 0.6 0 0.2 --output src/61_motion_grasp_editor/output/shifted.json
```

`shifted.json`의 `position[0]`은 첫 결과보다 0.1 m 커지고, y·z와 회전은 같아야 합니다. 손의 절대 위치는 달라져도 **머그를 잡는 상대 관계는 그대로**입니다. 파지 모양을 눈으로만 비교하기 어려울 때 이 차이를 숫자로 확인할 수 있습니다.

## 실행할 때 막히면

- **`Missing USD` 또는 머그·손 자산이 보이지 않음**: 압축을 푼 USD 경로와 함께 제공된 상대 경로 폴더를 확인하세요.
- **Ready에서 진행되지 않음**: articulation과 물체 선택, `.yaml` 확장자, 쓰기 가능한 export 경로를 확인하세요.
- **손가락은 닫히는데 머그가 빠짐**: mesh 모습과 collider를 대조하고 접촉 위치·최대 effort를 확인하세요. Confidence를 높여도 접촉은 바뀌지 않습니다.
- **`Unknown grasp`**: 오류에 표시된 사용 가능한 이름과 YAML의 `grasps` 아래 이름을 확인하세요.
- **회전 입력을 거부함**: `--object-quaternion`은 W X Y Z 순서이며 길이가 1인 quaternion이어야 합니다.
- **목표가 엉뚱한 위치에 생김**: Import와 작성 때 고른 기준 프레임이 같은지 먼저 확인하세요. 계산기의 기존 JSON은 덮어쓰지 않으므로 새 `--output`도 지정합니다.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Grasp Editor](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/grasp_editor.html)에 대응합니다. 공식 장면에서 파지를 작성하는 절차에 로컬 실행기와 목표 자세 계산기를 연결했습니다.

이번 개정에서는 공식 편집 절차와 설치된 `grasp_importer.py`의 변환식을 대조했습니다. 실제 GUI 파지 작성·Export·Import는 실행하지 않았으며 `tutorial.json`은 `not_run`입니다. 위 위치 차이는 좌표 변환의 확인 기준이고, 로봇 팔의 도달이나 물체 들기를 검증한 결과는 아닙니다.
