# 60. 닫기 명령은 언제 실제 흡착이 되나요?

## 이번에 배우는 것

**Surface Gripper로 큐브를 잡고 들어 올린 뒤 놓으면서, 닫기 명령과 실제 물체 부착을 구별합니다.**

그리퍼에 닫기 명령을 보냈다고 물체가 바로 붙는 것은 아닙니다. 접촉점이 물체를 찾을 수 있는 위치에 있어야 하고, 붙인 뒤에는 연결이 하중을 견뎌야 합니다. 이번에는 Isaac Sim 설치에 포함된 gantry 장면으로 이 과정을 살펴봅니다. Gantry는 x·y·z 방향의 직선 관절로 흡착부를 옮기는 장치입니다.

| 구성 | 이 실습에서의 역할 |
|---|---|
| `SurfaceGripper_gantry.usda` | gantry, 큐브, 부착용 관절이 들어 있는 설치 예제 장면 |
| `/World/SurfaceGripper` | 닫기·열기와 부착 상태를 관리하는 prim |
| `/World/Surface_Gripper_Joints` | 물체와 연결할 접촉점의 관절 목록 |
| `GripperView` | 그리퍼 속성을 설정하고 상태를 읽는 Python API |
| `output/gripper.csv` | 물리 10단계마다 남기는 상태와 잡힌 물체 경로 |

흡착은 접촉점에 관절 제약을 만들어 구현합니다. 따라서 여기서 관찰하는 것은 **물체의 연결과 해제**이며 진공 압력이나 공기 흐름을 계산하는 과정은 아닙니다.

## 1. 닫기·들기·열기를 한 번 실행하기

Isaac Sim 5.1과 지원 NVIDIA GPU가 필요합니다. 저장소 루트에서 실행하세요. 설치 위치가 다르면 `~/isaacsim`을 바꾸세요.

```bash
~/isaacsim/python.sh src/60_motion_robot_surface_gripper/run.py --steps 420
```

약 7초의 시뮬레이션을 진행한 뒤 창이 닫힙니다. 앱을 시작하는 시간까지 포함한 실제 실행 시간은 더 길 수 있습니다. 화면을 계속 보려면 `--steps 420`을 빼고, 창 없이 실행하려면 `--headless`를 추가하세요. Headless 실행에서 단계 수를 생략하면 420단계입니다.

기본 CSV가 이미 있으면 덮어쓰지 않고 중단합니다. 다시 실행할 때는 `--output src/60_motion_robot_surface_gripper/output/gripper-02.csv`처럼 새 파일을 지정하세요.

### 실행 결과 확인하기

화면의 큐브 움직임과 CSV를 다음 순서로 대조해 보세요.

| CSV의 `step` | 코드가 보내는 동작 | 확인할 결과 |
|---|---|---|
| 0~110 | x·y 목표 0, z 관절 목표 0.140으로 접근 | 흡착부가 큐브 가까이 이동 |
| 120 이후 | 닫기 명령 `0.5` | `Closed` 상태와 비어 있지 않은 `gripped_objects` |
| 240 이후 | z 관절 목표를 0.05로 변경 | 잡힌 큐브가 흡착부를 따라 상승 |
| 360 이후 | 열기 명령 `-0.5` | `Open` 상태와 빈 물체 목록 |

`Closing`은 물체를 찾으며 닫기를 시도하는 상태입니다. **`Closed`와 물체 경로가 함께 있어야 실제 부착을 확인한 것입니다.** CSV의 `gripped_objects`에는 여러 경로가 있으면 `|`로 구분해 저장합니다.

`step`은 0부터 시작하는 반복문 번호이고 행은 물리 계산 뒤 기록합니다. 예를 들어 `step=120` 행은 닫기 명령을 보낸 뒤 한 물리 단계가 지난 상태입니다. 명령 직후에 항상 `Closed`가 될 필요는 없으므로 뒤의 행도 읽어 보세요.

## 2. 부착점과 관절 목표가 연결되는 과정 보기

### 코드에서 볼 부분

장면을 불러온 다음, 코드는 그리퍼 prim을 만들고 기존 부착 관절들을 연결합니다.

```python
robot_schema.CreateSurfaceGripper(stage, path)
joints = stage.GetPrimAtPath("/World/Surface_Gripper_Joints")
stage.GetPrimAtPath(path).GetRelationship(
    robot_schema.Relations.ATTACHMENT_POINTS.name
).SetTargets([joint.GetPath() for joint in joints.GetChildren()])
```

USD relationship은 다른 prim을 가리키는 연결입니다. 여기에는 잡을 큐브의 mesh를 넣는 것이 아니라 **흡착부의 접촉점에 배치한 관절 경로**를 넣습니다. 대상 물체는 닫기 시도 중에 찾습니다. 공식 Surface Gripper는 이 D6 관절들을 관리해 부모 강체와 대상 강체를 연결합니다.

```python
gripper.set_surface_gripper_properties(
    max_grip_distance=[args.grip_distance], coaxial_force_limit=[0.005],
    shear_force_limit=[5], retry_interval=[1.0],
)
```

- `max_grip_distance`: 접촉을 받아들일 거리입니다. 기본 0.02는 2 cm입니다.
- `retry_interval`: 닫기 시도를 계속할 시간입니다. 여기서는 1초입니다.
- `coaxial_force_limit`, `shear_force_limit`: 축 방향과 옆 방향의 하중 제한입니다. 연결이 만들어진 뒤 유지되는 조건에 관여합니다.
- 값이 대괄호에 들어 있는 이유는 `GripperView`가 여러 그리퍼를 함께 처리하는 API이기 때문입니다. 이 장면에는 하나만 있습니다.

관절 목표는 다음 속성에 씁니다.

```python
stage.GetPrimAtPath("/World/Joints/z_joint").GetAttribute(
    "drive:linear:physics:targetPosition"
).Set(0.05)
```

이 0.05는 큐브의 월드 높이가 아닙니다. gantry의 z 관절이 이동할 목표량입니다. 이 장면에서는 0.140에서 0.05로 줄일 때 흡착부가 올라갑니다. 숫자의 증감만 보지 말고 관절 축과 실제 움직임을 함께 보세요.

### 상태 검사에서 볼 부분

```python
closed_seen |= state == GripperStatus.Closed and bool(objects)
```

코드는 기록 시점에 실제 부착을 한 번이라도 보았는지 기억합니다. 400단계 이상 실행했는데 한 번도 관측하지 못하면 오류를 냅니다. 다만 이 검사는 최종 해제까지 판정하지 않습니다. **들기와 열기의 결과는 CSV 뒤쪽과 화면에서 따로 확인**하세요.

### GUI에서 직접 닫고 부착점 확인하기

자동 일정과 비교하려면 위 실행을 종료하고 `~/isaacsim/isaac-sim.sh`로 새 창을 여세요.

1. **Window > Examples > Robotics Examples > Manipulation > Surface Gripper**에서 **Load**를 누릅니다. 설치 예제의 gantry 장면이 재생됩니다.
2. gantry 관절의 target position을 조절해 흡착부를 큐브 가까이 내리고 **Open/Close**를 누르세요. 닫힌 상태에서 gantry를 올려 물체가 함께 움직이는지 확인합니다.
3. Stage의 Surface Gripper prim에서 **Attachment Points**에 연결된 관절을 선택하세요. D6 타입, Enabled, 같은 부모 강체를 가리키는 Body 0, Exclude from Articulation을 확인합니다. 이 조건들이 있어야 접촉점들을 하나의 그리퍼로 관리할 수 있습니다.
4. 관절의 **Properties > + Add > Edit API Schema**에서 `AttachmentPointAPI`를 확인하고 Forward Axis와 ClearanceOffset을 살펴보세요. 이 값은 표면 탐색 방향과 자기 collider를 피하는 광선 시작점을 정합니다.
5. 예제의 Action Graph에서 **Surface Gripper** 노드가 제어하는 gripper prim을 확인하세요. UI 버튼·그래프·Python 모두 같은 prim의 상태를 바꾸는 다른 입력 방식입니다.

직접 그리퍼를 새로 구성할 때는 **Create > Robots > Surface Gripper**로 prim을 만든 뒤 위 조건의 D6 접촉점을 Attachment Points에 연결합니다. 기존 그리퍼와 같은 관절을 동시에 제어하지 않도록 별도 장면에서 구성하세요. GUI 시험은 로컬 `gripper.csv`를 자동으로 만들지 않으므로 상태 표시와 물체 움직임으로 확인합니다. [공식 GUI 및 부착점 절차](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html#attachment-joints)를 함께 볼 수 있습니다.

## 3. 명령과 물리 상태의 관계 정리

```text
닫기 명령
    → 부착점 방향으로 허용 거리 안의 물체 탐색
    → 접촉점의 관절로 물체 연결
    → gantry 이동과 하중에 따라 연결 유지 또는 끊김
    → 열기 명령으로 연결 해제
```

닫기 명령은 동작의 시작이고, `status`와 `gripped_objects`는 그 결과입니다. 같은 명령이라도 거리·방향·하중이 달라지면 결과가 달라집니다. 이 차이를 이해하면 “제어 명령은 보냈는데 물체가 따라오지 않는다”는 상황을 단계별로 살펴볼 수 있습니다.

## 4. 간단한 확인 실험

허용 거리만 2 cm에서 5 mm로 줄여 보세요.

```bash
~/isaacsim/python.sh src/60_motion_robot_surface_gripper/run.py --steps 420 --grip-distance 0.005 --output src/60_motion_robot_surface_gripper/output/distance-5mm.csv
```

기본 실행과 접근 자세, 닫기 시점, 하중 제한은 같습니다. `step=120` 이후 `Closed`에 도달하는지, 잡힌 물체 경로가 생기는지 비교하세요. 허용 거리가 짧아지면 부착이 어려워질 수 있지만, 실제 접촉점이 이미 충분히 가까우면 두 실행 모두 성공할 수도 있습니다. 이 실험의 관찰값은 창의 종료 여부보다 **부착 상태의 변화**입니다.

## 실행할 때 막히면

- **`SurfaceGripper_gantry.usda`를 찾지 못함**: `isaacsim.robot.surface_gripper` 확장 설치와 그 안의 `data/`를 확인하세요. 이 실습은 그 설치 장면을 직접 참조합니다.
- **계속 `Closing`이거나 물체 목록이 비어 있음**: `/World/Surface_Gripper_Joints`의 위치와 대상 collider를 확인하세요. 부착점의 Forward Axis와 ClearanceOffset은 탐색 방향과 자기 몸체를 피하는 시작 위치에 관여합니다.
- **붙었다가 상승 중에 놓침**: 닫기 자체보다 연결 유지 조건을 살펴보세요. CSV에서 물체 경로가 사라지는 시점과 gantry의 상승 시점을 대조합니다.
- **CSV는 있지만 닫기 기록이 없음**: 120단계 전에 종료했을 수 있습니다. 전체 과정은 위의 420단계로 확인하세요.
- **`Output exists`**: `--output`으로 아직 없는 CSV 파일명을 지정하세요.

## 공식 문서와 실습 범위

이 폴더는 Isaac Sim **5.1.0**의 [Surface Gripper Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_surface_gripper.html)에 대응합니다. 부착점의 구성과 GUI에서 직접 만드는 방법은 공식 문서의 Attachment Joints 및 Attachment Point API 절을 참고하세요.

로컬 코드는 설치 gantry 장면에 자동 닫기·상승·해제 일정과 CSV 기록을 더한 실습입니다. 코드와 공식 속성 설명을 대조했으며 이번 문서 개정에서는 실제 흡착을 실행하지 않았습니다. `tutorial.json`의 검증 상태는 `not_run`입니다.
