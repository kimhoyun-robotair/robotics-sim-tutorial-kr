# 프로젝트 4: 카메라로 물체 위치를 구하고 집어 옮긴다

이 프로젝트는 세 부분으로 나누어 진행한다. 먼저 공식 Franka 예제로 로봇 동작을 확인하고, 별도 RGB-D 장면에서 좌표 계산을 검증한다. 마지막으로 같은 카메라 계산을 Franka 장면에 넣고, 정답 위치를 읽던 부분을 카메라 추정값으로 바꾼다. 영상에 상자가 보이는 것과 카메라를 이용해 물체를 집는 것은 서로 다른 완료 조건이다.

## 준비할 것

- [관절과 제어기](../03-core/04-articulation-joints-controllers.md), [카메라와 센서](../05-customization/03-custom-sensors.md)를 완료한다.
- 처음에는 Isaac Sim에 포함된 Franka와 기본 그리퍼를 사용한다. 새 로봇을 가져오는 작업은 마지막 확장으로 남긴다.
- 아래 명령의 시작 위치는 이 저장소 루트이다. `ISAACSIM_PATH`는 Isaac Sim **5.1.0** 설치 폴더로 설정한다.

```bash
export ISAACSIM_PATH="$HOME/isaacsim"
mkdir -p project-4/scripts project-4/results project-4/config
```

## 1단계: 공식 Franka 동작부터 확인한다

GUI에서 `Window > Examples > Robotics Examples > Manipulation > Franka Pick Place`를 연다. `LOAD`로 장면을 불러오고, `START PICK PLACE`를 누른다. 로봇이 실제로 상자를 들어 올리는지 관찰한 뒤 `RESET`으로 초기 상태를 확인한다.

독립 Python 실행도 확인한다.

```bash
cd "$ISAACSIM_PATH"
test -f standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py
./python.sh standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py
```

5.1.0의 이 파일은 `FrankaPickPlace`와 `SimulationManager`를 사용한다. 과거 예제의 `World`·`PickPlaceController` 코드 조각을 그대로 끼워 넣으면 객체와 실행 방식이 맞지 않을 수 있다. 실제 출발점은 [v5.1.0 실행 파일](https://github.com/isaac-sim/IsaacSim/blob/47d886f2858d1ceed556b21c88927aa67bc81c12/source/standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py)이다.

**완료 판정:** 초기 장면이 정상적으로 보이고, 관절이 무너지지 않으며, 그리퍼가 물체를 잡고 놓는 동작을 관찰했다. 공식 클래스의 `is_done()`은 단계가 끝났다는 뜻이다. 상자를 놓쳤어도 단계가 진행될 수 있으므로 성공률 지표로 바로 사용하지 않는다. 실제 구현은 [5.1.0 FrankaPickPlace 소스](https://github.com/isaac-sim/IsaacSim/blob/47d886f2858d1ceed556b21c88927aa67bc81c12/source/extensions/isaacsim.robot.manipulators.examples/isaacsim/robot/manipulators/examples/franka/pick_place/pick_place.py)에서 확인한다.

## 2단계: RGB-D 영상이 정상인지 독립적으로 확인한다

다시 이 저장소 루트로 이동한다. [camera_imu.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/camera_imu.py)는 바닥과 빨간 상자, 위에서 아래를 보는 카메라를 만들고 RGB·깊이·내부 파라미터·카메라 위치를 저장한다.

```bash
"$ISAACSIM_PATH/python.sh" examples/standalone/camera_imu.py \
  --gui --output-dir project-4/results/camera
```

실행 뒤 `rgb.png`, `sensor_data.npz`, `result.json`을 확인한다. RGB-D 프레임 검사와 물리 검사 결과를 구분해서 읽는다. GPU가 없어서 실행하지 못했다면 이미지나 정상 결과가 생성되었다고 기록하지 않는다.

| 확인 항목 | 의미 |
|---|---|
| RGB 크기와 채널 | 영상이 실제 카메라 해상도이며 값이 전부 검정·흰색이 아닌지 확인한다. |
| 깊이 | 유효한 물체 표면에서 양의 유한값이 나오는지 확인한다. 배경의 무한대 값과 구분한다. |
| 내부 파라미터 K | `fx`, `fy`가 양수이고 해상도와 일치하는지 확인한다. |
| 카메라 위치·방향 | 저장한 위치가 m 단위이고 쿼터니언 순서가 `wxyz`인지 확인한다. |
| 시각 | 새 프레임이 생성된 뒤 RGB와 깊이를 같은 시점에 읽었는지 확인한다. |

카메라는 `Camera.initialize()`만 호출했다고 즉시 유효한 영상을 주지 않는다. 렌더링이 진행되고 센서가 새 프레임을 제공할 때까지 기다려야 한다. 물리만 진행하는 `render=False` 반복문으로 카메라를 검사하지 않는다. 카메라 초기화와 프레임 API는 [5.1.0 Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)를 기준으로 한다.

## 3단계: 빨간 영역의 위치를 계산한다

이 저장소의 [check_rgbd_target.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/ros2/check_rgbd_target.py)는 저장된 RGB-D 파일을 읽는 완성된 예제이다. ROS를 실행하지 않아도 사용할 수 있다. 색으로 구분되는 상자 하나를 대상으로 하며, 일반 물체 인식기나 학습된 검출기는 아니다.

```bash
"$ISAACSIM_PATH/python.sh" examples/ros2/check_rgbd_target.py \
  project-4/results/camera/sensor_data.npz \
  --expected-surface-z 0.5 \
  --tolerance 0.04 \
  --output project-4/results/target.json
```

이 값은 카메라 검증 장면에 있는 **한 변 0.5 m인 상자의 윗면**에 대한 검사이다. Franka가 집는 작은 상자에 이 크기를 재사용하지 않는다. 출력의 `world_surface_point_m`에서 z가 약 0.5 m여야 한다.

픽셀 `(u, v)`와 카메라 광축 방향 깊이 `Z`에서 optical 좌표를 구하는 식은 다음과 같다.

\[
X = (u-c_x)Z/f_x,\qquad Y=(v-c_y)Z/f_y
\]

```python
import numpy as np

# fx, fy, cx, cy, u, v, depth_z는 현재 영상의 값이다.
point_optical = np.array([
    (u - cx) * depth_z / fx,
    (v - cy) * depth_z / fy,
    depth_z,
])
```

여기서 깊이는 `distance_to_image_plane`이다. `distance_to_camera`처럼 카메라 중심으로부터의 거리라면 광선의 길이가 달라 같은 식에 그대로 대입할 수 없다. 카메라 optical 축은 +Z 앞, +X 오른쪽, +Y 아래이다. `Camera.get_world_pose(camera_axes="world")`의 카메라 축은 +X 앞, +Z 위이므로 회전 전에 다음과 같이 축을 바꾼다.

```python
point_camera_world_axes = np.array([
    point_optical[2], -point_optical[0], -point_optical[1]
])
point_world = camera_position + rotation_matrix @ point_camera_world_axes
```

실제 스크립트에는 `wxyz` 쿼터니언을 회전행렬로 바꾸는 계산과 입력 검사도 들어 있다. 검은 영상, 빨간 영역 누락, NaN 깊이, 잘못된 카메라 자세는 예외로 처리한다. 그 경우 임의의 위치를 반환해 로봇을 움직이지 않는다.

**완료 판정:** 저장된 RGB에서 선택된 영역이 빨간 상자이고, 계산한 표면 좌표가 알려진 상자 윗면과 허용 오차 안에서 일치한다. 상자 중심을 추정하려면 윗면에서 상자 높이의 절반을 빼야 한다. 이는 물체 크기를 이미 안다는 추가 가정이다.

## 4단계: Franka 장면에 카메라를 추가한다

2~3단계의 `target.json`은 별도 검증 장면에서 나온 값이다. 이 파일을 Franka 목표로 곧바로 보내지 않는다. 이제 **Franka 장면 안의 카메라**에서 같은 계산을 수행한다.

1. 1단계의 실행 파일을 `project-4/scripts/run_pick_place.py`로 복사한다.
2. 설치 폴더의 아래 클래스 파일도 `project-4/scripts/franka_pick_place_local.py`로 복사한다. 원본의 저작권·라이선스 주석을 보존한다.
3. 실행 파일의 `from isaacsim.robot.manipulators.examples.franka import FrankaPickPlace`를 `from franka_pick_place_local import FrankaPickPlace`로 바꾼다.

```bash
cp "$ISAACSIM_PATH/standalone_examples/api/isaacsim.robot.manipulators/franka/pick_place.py" \
  project-4/scripts/run_pick_place.py
cp "$ISAACSIM_PATH/exts/isaacsim.robot.manipulators.examples/isaacsim/robot/manipulators/examples/franka/pick_place/pick_place.py" \
  project-4/scripts/franka_pick_place_local.py
cp examples/ros2/check_rgbd_target.py project-4/scripts/check_rgbd_target.py
```

파일이 없다면 설치 버전과 [공식 소스 경로](https://github.com/isaac-sim/IsaacSim/tree/v5.1.0/source/extensions/isaacsim.robot.manipulators.examples)를 확인한다. 아직 카메라 코드를 넣지 않은 복사본이 1단계와 똑같이 동작하는지 먼저 실행한다.

로컬 클래스 `setup_scene()`에서 상자 재질의 `diffuseColor`를 `[1.0, 0.0, 0.0]`으로 바꾼다. 상자의 크기는 기존 `self.cube_size`를 유지한다. 실행 파일에서 `pick_place.setup_scene()` 바로 뒤에 아래 카메라 생성 코드를 넣는다. `SimulationApp`은 이미 만들어져 있으므로 다시 만들지 않는다.

```python
from isaacsim.sensors.camera import Camera
from isaacsim.core.utils.numpy.rotations import euler_angles_to_quats
import numpy as np

camera = Camera(
    prim_path="/World/InspectionCamera",
    position=np.array([0.5, 0.0, 1.5]),
    orientation=euler_angles_to_quats(np.array([0.0, 90.0, 0.0]), degrees=True),
    resolution=(640, 480),
    frequency=30,
)
```

카메라가 바닥을 향하는지 Viewport에서 먼저 확인한다. Timeline이 실행되고 자산이 준비된 뒤 `camera.initialize()`와 `camera.add_distance_to_image_plane_to_frame()`를 호출한다. 기존 실행 루프의 첫 `pick_place.reset()` 이후에는 곧바로 `forward()`를 부르지 말고, 새 RGB-D 프레임을 기다리는 `DETECT` 단계를 추가한다. 로봇은 초기 자세를 유지해야 한다.

카메라에서 프레임을 얻는 부분은 다음과 같다. 이 코드는 **새 프레임과 깊이가 준비되었음을 확인한 뒤** 실행하는 본문 조각이다.

```python
from check_rgbd_target import estimate_target

frame = camera.get_current_frame()
position, orientation = camera.get_world_pose(camera_axes="world")
measurement = estimate_target({
    "rgba": camera.get_rgba(),
    "depth": frame["distance_to_image_plane"],
    "intrinsics": camera.get_intrinsics_matrix(),
    "camera_position": position,
    "camera_orientation": orientation,
})
surface = np.array(measurement["world_surface_point_m"])
center = surface - np.array([0.0, 0.0, pick_place.cube_size[2] / 2])
```

한 프레임에서 실패했다고 바로 종료할 필요는 없지만, 준비 대기와 검출 실패를 구분한다. 예를 들어 렌더 프레임 180개 동안 유효한 관측을 얻지 못하면 물체 접근을 중단하고 RGB와 오류를 저장한다. 모든 예외를 무시하며 `forward()`를 계속 실행하지 않는다.

## 5단계: 정답 위치 입력을 추정 위치로 바꾼다

5.1.0 로컬 클래스의 `forward()`를 읽으면 0단계와 1단계에서 다음 코드로 물체의 정답 위치를 읽는다.

```python
cube_pos = self.cube.get_world_poses()[0].numpy()
```

이 두 곳만 그대로 두면 카메라를 추가해도 여전히 정답 위치를 사용하는 데모이다. 로컬 클래스에 아래 메서드를 추가하고 `DETECT`가 끝날 때 `pick_place.set_detected_pick_position(center)`를 호출한다.

```python
# FrankaPickPlace 클래스 안에 추가한다.
def set_detected_pick_position(self, position):
    position = np.asarray(position, dtype=float).reshape(3)
    if not np.isfinite(position).all():
        raise ValueError("유효하지 않은 관측 위치")
    self.detected_pick_position = position.copy()
```

0·1단계의 정답 위치 읽기를 다음 코드로 바꾸면 기존 `[1, 3]` 배열 모양도 유지된다.

```python
if not hasattr(self, "detected_pick_position"):
    raise RuntimeError("DETECT가 끝나기 전에 접근을 시작할 수 없다")
cube_pos = self.detected_pick_position.reshape(1, 3)
```

초기 자세를 되돌릴 때는 `detected_pick_position`도 지우고 다시 관측한다. 정답 위치는 평가 함수에서만 읽는다. 검출 좌표와 정답 좌표의 차이를 먼저 기록하고, 바닥 아래·작업영역 밖·그리퍼 폭보다 작은 허용 여유를 벗어나는 값이면 접근을 중단한다. 기본 접근 높이와 그리퍼 동작이 실제 작은 상자를 집는지 저속으로 확인하고, 실패하면 단계를 건너뛰지 않는다.

이 단계는 소스를 수정하는 심화 실습이다. 위 수정만으로 모든 물체·조명에서 집기가 보장되지는 않는다. 실제 집기와 충돌 검증을 통과한 조합만 평가에 사용한다.

## 6단계: 동작 종료와 작업 성공을 구분한다

| 상태 | 다음 단계로 넘어가는 조건 | 실패 시 처리 |
|---|---|---|
| DETECT | 새 RGB-D 프레임과 유효한 물체 좌표 | 영상 저장 후 정지 |
| PREGRASP | 물체 위 안전 높이에 도달 | 시간 초과 시 초기 자세 복귀 |
| GRASP | 그리퍼가 닫히고 물체가 유지됨 | 물체를 밀거나 놓치면 다시 관측 |
| LIFT | 물체의 높이가 실제로 증가 | 그리퍼만 올라가면 실패 |
| PLACE | 목표 영역 안에서 물체가 정지 | 영역 밖이면 실패 |
| RESET | 관절·물체·관측 상태 초기화 | 초기화 오류면 다음 반복 중단 |

완료 조건은 카운터가 끝났는지가 아니라 **물체가 목표 영역에 들어가 충분히 정지했는지**로 정의한다. 위치 오차, 속도, 접촉과 실제 소요 시간을 저장한다. ROS 2와 MoveIt 2를 사용하는 확장은 [MoveIt 워크숍](../04-ros2/13-moveit2-workshop.md)을 따른다. Isaac Sim의 작업대가 MoveIt 장애물로 자동 등록되지는 않는다.

## 7단계: 데이터 생성과 반복 평가

조명과 물체 위치를 고정해 10회 반복한 뒤 조건을 하나씩 바꾼다. 처음부터 노이즈를 추가하면 좌표 계산 오류와 노이즈 영향을 구분하기 어렵다. [Replicator 실습](../06-developer/03-replicator-and-sdg.md)으로 RGB·깊이·분할 마스크를 생성할 때는 물체의 semantic label과 출력 파일 쌍이 빠지지 않았는지 먼저 100프레임에서 검사한다.

기록 파일에는 다음을 남긴다.

```json
{
  "seed": 1,
  "detection_valid": true,
  "position_error_m": null,
  "grasp_succeeded": null,
  "place_succeeded": null,
  "failure_state": null,
  "camera_frame_id": null
}
```

`null`은 아직 측정하지 않은 항목이다. 예시 숫자를 실제 성공 결과로 채워 넣지 않는다. 각 조합의 모든 시행을 기록하고, 검출 성공률·집기 성공률·최종 배치 성공률을 따로 계산한다.

## 출처

- [Franka Pick and Place Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/examples/manipulation_franka_pick_place.html)
- [Tutorial 8: Generate Robot Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html)
- [Configuring RMPflow for a New Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/manipulators/manipulators_configure_rmpflow_denso.html)
- [Pick and Place Example: UR10e](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html)
- [Camera Sensors](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/sensors/isaacsim_sensors_camera.html)
- [Scene Based Synthetic Dataset Generation](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_scene_based_sdg.html)
