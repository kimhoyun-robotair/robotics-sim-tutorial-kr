# 58. Cobotta의 관절과 그리퍼에 맞춰 RMPflow 설정하기

## 이번에 배우는 것

**6축 Cobotta의 입력 파일을 만들고, 그리퍼 중심과 충돌 근사 크기가 목표 추종에 어떤 의미를 갖는지 확인합니다.**

다른 로봇의 설정을 가져와도 관절 수와 말단 기준점이 다르면 그대로 사용할 수 없습니다. 이번에는 Franka 기반 template을 Cobotta Pro 900에 맞추고, 손가락 한쪽 대신 집게 중심을 목표에 맞추도록 frame을 추가합니다.

| 파일·도구 | 역할 |
|---|---|
| `prepare_config.py` | URDF와 YAML을 읽어 새 설정 세 파일 생성 |
| `cobotta_gripper_frame.urdf` | 운동학 연결과 새 `gripper_center` frame |
| `robot_description.yaml` | 제어할 6축, 기본 자세와 collision sphere |
| `rmpflow.yaml` | 관절 제한 여유, 속도 반응, 몸체 충돌 근사 |
| Cobotta USD | 실제 장면의 물리 로봇 |
| Lula Test Widget | 위 설정을 실제 articulation에 연결해 시험 |

설정 생성 도구는 시뮬레이터를 켜거나 로봇을 움직이지 않습니다. **파일 준비와 GUI 추종 시험을 순서대로** 진행합니다.

## 1. 원본 파일에서 실행용 설정 만들기

Isaac Sim 5.1, GUI와 지원 GPU, 설치 Python의 PyYAML이 필요합니다. [공식 Cobotta 자산 압축 파일](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/_downloads/43f1f07841f3ef71cc54f320218ced44/Cobotta_Pro_900_Assets.zip)을 내려받아 이 폴더의 `input/` 아래에 풀어 두세요.

압축 파일에는 URDF와 descriptor, RMPflow YAML들이 있습니다. **USD는 포함되어 있지 않습니다.** GUI 실습에는 5.1 Assets의 `Isaac/Robots/Denso/CobottaPro900/cobotta_pro_900.usd`를 별도로 사용합니다. 해당 USD의 mesh·재질 참조에도 접근할 수 있어야 합니다.

다음은 **저장소 루트** 기준입니다. 압축을 풀면 아래의 `Cobotta_Pro_900_Assets` 폴더가 생깁니다. 위치를 달리했다면 첫 변수만 맞추세요.

```bash
COBOTTA_INPUT="$PWD/src/58_motion_manipulators_configure_rmpflow_denso/input/Cobotta_Pro_900_Assets"

~/isaacsim/python.sh src/58_motion_manipulators_configure_rmpflow_denso/prepare_config.py \
  --template "$COBOTTA_INPUT/rmpflow_configs/template_rmpflow_config.yaml" \
  --urdf "$COBOTTA_INPUT/cobotta_pro_900.urdf" \
  --descriptor "$COBOTTA_INPUT/robot_description.yaml" \
  --output src/58_motion_manipulators_configure_rmpflow_denso/output/basic
```

설치 위치가 다르면 `~/isaacsim`을 바꾸세요. 원본 URDF를 입력으로 선택해야 합니다. 압축에 함께 있는 `cobotta_pro_900_gripper_frame.urdf`는 이미 새 frame이 있어 이 도구의 입력으로 쓰면 중복 오류가 납니다. 출력 폴더는 새 경로여야 합니다.

### 코드에서 볼 부분

생성 URDF에는 다음 구조가 추가됩니다.

```xml
<link name="gripper_center" />
<joint name="gripper_center_joint" type="fixed">
  <origin rpy="0 0 0" xyz="0 0 0.24" />
  <parent link="onrobot_rg6_base_link" />
  <child link="gripper_center" />
</joint>
```

그리퍼 base에서 로컬 Z 방향으로 0.24 m 떨어진 점을 기준으로 삼습니다. **fixed joint이므로 제어할 자유도는 늘지 않습니다.** 새로운 운동 부품을 만드는 대신 집게 중심을 계산할 좌표계를 추가하는 것입니다.

YAML에서는 다음 값을 맞춥니다.

```python
config['joint_limit_buffers'] = [0.01] * 6
config['rmp_params']['joint_velocity_cap_rmp'].update(
    max_velocity=1.0, velocity_damping_region=0.3)
```

관절 제한 안쪽으로 둘 여유는 여섯 관절 각각 0.01 rad입니다. 최대 속도 반응은 1 rad/s, 한계에 접근하며 감속을 시작할 영역은 0.3 rad/s로 정합니다. template의 7개 buffer를 Cobotta의 6축에 맞추는 것이 중요한 변경입니다.

### 실행 결과 확인하기

이 튜토리얼 폴더의 `output/basic`에 있는 파일 세 개와 터미널의 `설정 생성:` 경로를 확인하세요. descriptor의 `cspace`와 정책의 `joint_limit_buffers`가 각각 6개인지, 생성 URDF에 `gripper_center`가 한 번만 정의되는지 읽어 봅니다.

생성 URDF는 Lula의 운동학 입력입니다. 출력 폴더로 옮겨진 URDF의 상대 mesh 참조까지 복사하는 도구는 아니므로 이를 그대로 시각 로봇 재수입용 파일로 사용하지 않습니다. 화면의 로봇은 별도의 Cobotta USD에서 읽습니다.

## 2. Lula Test Widget에서 새 frame 추종하기

`~/isaacsim/isaac-sim.sh`로 새 창을 열고 다음 순서로 진행하세요.

1. 빈 Stage에 5.1 Assets의 Cobotta USD를 reference로 추가합니다.
2. **Window > Extensions**에서 Lula Test Widget을 활성화하고 **Tools > Robotics > Lula Test Widget**을 엽니다.
3. Play한 뒤 **Select Articulation**에서 Cobotta를 선택하세요.
4. **Robot Description YAML**에는 `output/basic/robot_description.yaml`, **Robot URDF**에는 `output/basic/cobotta_gripper_frame.urdf`의 절대 경로를 선택하고 **Load Selected Config > Load**를 누릅니다.
5. **Select End Effector Frame**에서 `gripper_center`를 선택합니다. RmpFlow 패널의 **RmpFlow Config YAML**에는 `output/basic/rmpflow.yaml`을 지정하세요.
6. **Follow Target**을 실행하고 그리퍼 앞쪽의 도달 가능한 위치로 target을 조금 옮겨 보세요.

### 설정에서 볼 부분

basic 설정의 `body_cylinders`는 base 원점부터 z=0.333 m까지 반지름 0.05 m인 capsule을 정의합니다. `body_collision_controllers`는 `right_inner_finger` frame에 반지름 0.05 m인 구를 둡니다. 이 구와 base 근사가 가까워질 때 회피 반응이 생기는 구조입니다.

더 넓은 근사를 준비하려면 1절 생성 명령의 `--output` 경로 끝에서 `basic`을 `conservative`로 바꾸고 `--conservative`를 추가하세요. 다른 입력 파일은 그대로 사용합니다.

| 구성 | basic | conservative |
|---|---|---|
| base capsule | 반지름 0.05 m, z=0~0.333 m | 반지름 0.08 m, z=0~0.12 m |
| `second_link` 근사 | 없음 | `(0, 0, 0.12)` m 중심, 반지름 0.16 m 구 |
| 움직이는 회피 구 | 오른쪽 finger 하나 | J5·J6, 양쪽 finger·knuckle |

`second_link`는 근사의 이름입니다. `pt1`과 `pt2`가 같아 구 모양이 되며, 실제 J2 링크에 자동 부착되어 따라다니는 형상이 아닙니다. base 좌표계에서 두 번째 링크 부근을 넓게 덮습니다. `body_collision_controllers`의 이름들은 실제 URDF frame이어야 하므로 생성 코드가 존재 여부를 검사합니다.

### 실행 결과 확인하기

테스트를 멈추고 conservative의 세 파일을 로드해 같은 target 위치를 시험하세요. base 근처에서 더 일찍 피하는지, 접근 가능한 공간도 줄어드는지 관찰합니다. 다음으로 end-effector frame을 `right_inner_finger`로 바꿔 보면 집게 중심과 손가락 frame이 서로 다른 위치를 맞춘다는 점을 확인할 수 있습니다.

이 GUI는 로컬 도구의 결과 JSON을 자동으로 만들지 않습니다. 선택 파일·frame·target 위치를 기록하고 화면의 추종을 직접 확인하세요. 구체적인 설정 배경은 [공식 Cobotta RMPflow 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)을 참고할 수 있습니다.

## 3. 로봇에 맞게 바꿔야 할 것 정리

```text
관절 수 → cspace와 buffer 길이
관절 속도 → velocity cap과 감속 영역
집게의 제어 지점 → URDF의 end-effector frame
피해야 할 몸체 부위 → capsule과 frame별 구
실제 로봇 응답 → USD drive와 물리 상태
```

큰 충돌 근사는 더 넓은 여유를 만들지만 정상 작업 자세도 제한할 수 있습니다. 이 구성은 모든 링크 쌍의 mesh 충돌을 검사하는 방식이 아닙니다. 실제 접촉 여부와 필요한 작업 범위를 함께 관찰해야 합니다.

설정에서 속도 반응을 바꾸어도 USD의 drive가 그 목표를 잘 따라야 합니다. 추종이 흔들리면 RMPflow 숫자만 계속 바꾸기보다 실제 관절 응답도 확인하세요.

공식 Cobotta 예제는 속도 cap을 1 rad/s로 줄였을 때 기존 P=10000, D=1000 설정에서 진동을 관찰하고 D=10000을 사용했다고 설명합니다. 같은 증상이 보이면 테스트를 멈춘 뒤 USD 관절의 stiffness/damping을 확인하고, 로드한 자산이 어떤 값을 사용하는지 기록하세요. 이 값은 해당 로봇과 설정의 사례이며 모든 로봇에 적용할 보편적인 gain은 아닙니다.

## 4. 간단한 확인 실험

conservative의 `rmpflow.yaml`을 별도 파일로 복사하고 **`body_cylinders`의 `second_link` 반지름만 0.16에서 0.14 m로** 줄이세요. 다른 값은 유지하고 위젯에서 새 YAML을 로드합니다.

같은 목표를 base 근처로 움직여 접근 공간이 늘어나는지 보세요. 구가 줄어든 만큼 실제 링크와의 여유도 다시 살펴야 합니다. 모든 설정을 한꺼번에 바꾸는 basic/conservative 비교보다 이 실험이 반지름 하나의 영향을 읽기 쉽습니다.

## 실행할 때 막히면

- **`gripper_center`가 이미 있다는 오류**: 원본 `cobotta_pro_900.urdf`를 입력으로 사용하세요.
- **위젯에 `gripper_center`가 없음**: 생성된 URDF를 선택하고 다시 Load했는지 확인하세요. USD prim 이름 목록과는 다릅니다.
- **6개 관절 조건 오류**: Cobotta의 `robot_description.yaml`을 선택했는지 확인하세요. 다른 로봇 descriptor와 섞지 않습니다.
- **로봇 mesh가 보이지 않음**: USD의 자산 참조를 확인하세요. 설정 생성 성공은 시각 자산 로딩 성공을 뜻하지 않습니다.
- **설정을 바꿔도 이전처럼 움직임**: 기존 테스트를 멈추고 새 파일을 로드한 뒤 다시 시작하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Configuring RMPflow for a New Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)에 대응합니다. 파일 생성 도구와 실제 Cobotta의 Lula Test Widget 절차를 연결합니다.

`tutorial.json`은 `not_run` 상태입니다. 이번 개정에서 공식 zip의 파일 목록과 생성 코드를 대조했으며, Cobotta 자산 로딩·GUI 조작·추종·충돌 회피를 새로 실행해 검증하지 않았습니다.
