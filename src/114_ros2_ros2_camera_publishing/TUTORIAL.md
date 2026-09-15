# 114. Python으로 카메라 데이터·내부 파라미터·TF 발행하기

권장 학습 순서 **114** · ROS 2 연결과 기본 통신 · 출처 ID `t013`

이 패키지는 Isaac Sim 5.1 **Publishing Camera’s Data**의 분리된 함수 예제를 하나의 실행 가능한 프로그램으로 구성했다. 같은 카메라에서 RGB, 깊이, 깊이 기반 PointCloud2, CameraInfo를 발행하고 `/clock`과 `/tf`도 만든다. 원문의 창고 자산은 직접 생성한 벽·바닥·큐브로 바꾸었다. 다른 패키지, 공통 모듈, 로봇 파일은 필요 없다.

## 이 실습의 의도

Python에서 카메라의 Render Product에 ROS writer를 붙이고, 영상·점군·CameraInfo·TF·시계를 함께 발행하는 흐름을 확인한다. 큐브와 벽은 같은 표면을 RGB, 깊이, TF로 world에 표시한 점군으로 비교하기 위한 기준물이다. 기본 실행은 네 가지 카메라 데이터의 발행 간격을 Gate로 조절하며, 카메라 pose와 축 변환 및 `/clock`은 별도 playback tick 그래프에서 발행한다.

## 실행 후 확인할 것

- `/camera_rgb`와 `/camera_depth`를 Image 표시로 실제 수신하고 같은 큐브·벽의 색과 깊이 표현을 비교한다. 타입은 `sensor_msgs/msg/Image`이며 `/camera_pointcloud`는 `sensor_msgs/msg/PointCloud2`다.
- `/camera_camera_info`의 `sensor_msgs/msg/CameraInfo`에서 width=640, height=480, `header.frame_id=camera`, K/R/P 배열을 확인한다. 콘솔 fx·fy는 카메라에서 읽은 내부 파라미터이므로 다른 예제의 고정값을 정답으로 쓰지 않는다.
- 기본 `--frequency 30`에서 콘솔 `Gate step=2`와 이론값 30 Hz를 확인한 뒤 ROS 수신 Hz를 별도로 측정한다. `--frequency 25`도 정수 간격 때문에 step=2가 되며, 요청값 25 Hz를 그대로 구현한 것으로 해석하지 않는다.
- `/clock`의 `rosgraph_msgs/msg/Clock`을 수신하고 RViz를 `use_sim_time=true`로 설정한다. `/tf`의 `tf2_msgs/msg/TFMessage`와 `tf2_echo world camera`로 카메라 pose를 확인한 뒤 Fixed Frame=`world`에서 점군 표면이 보이는지 본다.
- RViz TF에서 `camera → camera_world`는 위치가 같고 축 방향이 다른 변환이어야 한다. PointCloud의 frame은 `camera`이므로 두 frame을 물리적으로 떨어진 두 센서로 해석하지 않는다.
- RGB·깊이·점군·CameraInfo의 Gate와 별개로 Clock/TF는 매 playback tick에 연결된다. 깊이와 점군은 같은 Gate를 공유하므로 서로 독립적인 주기를 설정하는 실습으로 해석하지 않는다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 시뮬레이션 스텝과 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 지정하면 해당 횟수 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1800회를 사용합니다. 이전 `--frames` 옵션은 `--steps` 없는 headless 실행의 횟수만 정하며, GUI 종료에는 영향을 주지 않습니다. `--steps`를 지정하면 `--frames`보다 우선하며 0과 음수는 허용하지 않습니다.

## 준비와 실행

Isaac Sim 5.1.0, RTX GPU, ROS 2 Humble(Ubuntu 22.04) 또는 Jazzy(Ubuntu 24.04), `sensor_msgs`, `tf2_ros`, RViz2가 필요하다. Isaac Sim을 띄우기 전에 ROS 환경을 source한다. 배포판을 섞지 않는다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ISAAC_SIM=/home/hoyunkim/isaacsim
"$ISAAC_SIM/python.sh" run.py --frequency 30
```

수신 터미널도 같은 ROS 배포판과 Domain ID를 사용한다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
ros2 topic list
ros2 topic echo /camera_camera_info --once
ros2 topic hz /camera_rgb
ros2 topic echo /clock --once
ros2 run tf2_ros tf2_echo world camera
rviz2 --ros-args -p use_sim_time:=true
```

설치가 Jazzy라면 source 경로만 바꾼다. `--headless`를 넣어도 별도 Render Product가 카메라를 렌더링한다. GUI는 `--steps`를 생략하면 직접 닫을 때까지 유지되어 RViz를 계속 조작할 수 있다.

## 순서대로 결과 확인

1. Stage에서 `/World/camera`를 찾는다. 코드는 위치 `(4,0,2)` m와 world 축 기준 Euler 회전 `(0,15,180)`°를 넣는다. 카메라는 바닥 위 큐브와 벽을 바라본다.
2. CameraInfo를 수신해 640×480 해상도, K/P/R 배열, `header.frame_id=camera`를 확인한다. 실행 로그도 실제 카메라에서 읽은 fx, fy를 출력한다. 이는 고정된 정답을 출력하는 코드가 아니라 `read_camera_info`가 읽은 값이다.
3. RViz에서 **Add > Image**, Topic=`/camera_rgb`로 RGB를 확인한다. 두 번째 Image는 `/camera_depth`로 설정한다. 깊이 영상은 색 사진이 아니라 각 픽셀의 거리 데이터다.
4. **Add > PointCloud2**, Topic=`/camera_pointcloud`, Fixed Frame=`world`로 설정한다. TF가 정상 발행되면 카메라가 보는 벽과 큐브의 표면이 world 좌표에서 나타난다. TF 오류를 분리하려면 Fixed Frame을 `camera`로 바꾸어 센서 좌표에서 먼저 확인한다.
5. **Add > TF**로 `camera`와 `camera_world`를 확인한다. 둘은 위치는 같고 축 방향이 다르다. 메시지에 쓰인 optical frame과 사람이 로봇에서 자주 쓰는 world 축 표현을 구분하기 위한 보조 변환이다.
6. `/camera_rgb`, `/camera_depth`, `/camera_pointcloud`, `/camera_camera_info`, `/clock`, `/tf`가 실제 데이터를 보내는지 확인한다. `/parameter_events`, `/rosout`은 ROS 자체 토픽이므로 카메라 성공 증거가 아니다.

## API 설명: 생성에서 ROS 메시지까지

**USD**는 장면의 객체·계층·속성을 표현한다. `/World/camera`는 카메라 prim 경로다. `Camera(...)`는 이 prim을 센서 객체로 다루는 Isaac Sim 클래스이며 `initialize()`가 렌더 제품을 준비한다. `get_render_product_path()`로 해당 Render Product를 얻는다. 원문에 사용된 `_render_product_path` 대신 5.1의 공개 getter를 사용했다.

**Render Product**는 렌더할 카메라와 해상도를 연결한다. **Replicator writer**는 여기서 얻은 렌더 결과를 특정 출력으로 내보낸다. `rep.writers.get(...)`로 writer를 얻고, `initialize`로 ROS 토픽/frame/queue를 설정하고, `attach([product])`로 실행 파이프라인에 연결한다.

| writer | 토픽 | 데이터 의미 |
|---|---|---|
| `RgbROS2PublishImage` | `/camera_rgb` | RGB 색 영상 |
| `DistanceToImagePlaneROS2PublishImage` | `/camera_depth` | 카메라 영상 평면 기준 깊이(m) |
| `DistanceToImagePlaneROS2PublishPointCloud` | `/camera_pointcloud` | 깊이를 내부 파라미터로 역투영한 3D 점 |
| `ROS2PublishCameraInfo` | `/camera_camera_info` | 해상도, K/R/P, 왜곡 정보 |

깊이 점군은 픽셀 `(u,v)`와 깊이 `z`에 대해 `x=(u-cx)*z/fx`, `y=(v-cy)*z/fy`를 사용한다. 깊이 센서의 optical 축은 +Z 전방, +X 오른쪽, +Y 아래다. 이 점군 생성은 의미 라벨을 포함하지 않는다. semantic point cloud와 혼동하지 않는다.

`read_camera_info(render_product_path=...)`는 현재 카메라 설정에서 정보 객체를 얻는다. K는 3×3 내부 파라미터, R은 정렬 회전, P는 3×4 투영 행렬이다. writer가 요구하는 형태에 맞춰 K/R을 `[1,9]`, P를 `[1,12]`로 바꾼다. `physicalDistortionModel`과 `physicalDistortionCoefficients`도 전달한다. 카메라 설정을 나중에 바꾸면 저장해 둔 CameraInfo 값도 다시 읽어 writer를 재설정해야 한다.

## 발행 빈도가 “근사”인 이유

시뮬레이터의 physics/rendering dt는 모두 1/60 s다. `IsaacSimulationGate.inputs:step`을 N으로 설정하면 N번째 렌더 프레임마다 downstream writer가 실행된다. 코드에서는 공식 예제처럼 `N=int(60/요청빈도)`를 사용하되 1보다 작아지지 않게 제한한다.

- 요청 30 Hz → N=2 → 시뮬레이션 시간 기준 30 Hz.
- 요청 20 Hz → N=3 → 20 Hz.
- 요청 25 Hz → N=2 → 30 Hz. 정수 프레임 간격 때문에 정확한 25 Hz가 아니다.

RGB는 `RgbIsaacSimulationGate`, 깊이와 점군은 `DistanceToImagePlaneIsaacSimulationGate`, CameraInfo는 `PostProcessDispatchIsaacSimulationGate`를 사용한다. 깊이와 점군은 같은 상류 gate를 공유하므로 각각 독립된 빈도를 설정하는 예제로 해석하면 안 된다. `_get_node_path`는 5.1 예제의 내부 SDG 경로 접근 방식이므로 다른 버전에서는 재검토해야 한다.

`ros2 topic hz`는 수신기의 벽시계 기준 빈도를 재므로 GPU가 실시간보다 느리면 값이 낮아질 수 있다. 출력 로그의 이론 빈도와 실제 수신 빈도를 구분한다.

## TF와 시간

`ROS2PublishTransformTree`가 카메라 prim의 pose를 읽어 `/tf`로 내보낸다. `ROS2PublishRawTransformTree`는 `camera → camera_world` 회전을 추가한다. 이 노드의 quaternion 입력은 `(x,y,z,w)` 순서이며 `[0.5,-0.5,0.5,0.5]`이다. USD의 `Gf.Quatd`가 `(w,x,y,z)` 순서인 것과 구별해야 한다.

`IsaacReadSimulationTime` 출력이 Clock 및 두 TF publisher의 timestamp에 연결된다. 카메라 writer도 기본적으로 시뮬레이션 시간을 사용한다. RViz에 `use_sim_time=true`를 설정하면 `/clock`으로 시간을 맞추며, 물체가 움직이는 장면에서 TF를 잘못된 시각에 조회하는 문제를 줄일 수 있다.

## 실험과 문제 해결

변수 하나만 바꾸기: `--frequency 30`, `20`, `25`만 바꾸어 실행하고, 로그의 gate step과 `ros2 topic hz /camera_rgb`를 기록한다. 25 요청이 30 이론값으로 양자화되는지 확인한다. 카메라 해상도·장면은 그대로 둔다.

- PointCloud만 보이지 않으면 먼저 Fixed Frame=`camera`로 확인하고 `/tf`와 `/clock`을 점검한다.
- 이미지 구독이 연결되지 않으면 `ros2 topic info -v /camera_rgb`로 QoS를 읽고 RViz Reliability를 맞춘다.
- Gate 경로를 찾을 수 없다면 Isaac Sim 버전과 Bridge 로드 상태를 확인한다. writer를 attach하기 전에 gate를 찾으면 파이프라인이 아직 없을 수 있다.
- 일반 Python에서 simulator 모듈을 찾지 못하는 것은 예상되는 환경 차이다. `python3 run.py --help`는 Kit 없이 옵션 확인용으로만 쓴다.

## 출처와 검증 범위

[Isaac Sim 5.1 Publishing Camera’s Data](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html), [CameraInfo](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html#publish-camera-intrinsics-to-camerainfo-topic), [깊이 점군](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html#publish-pointcloud-from-depth-images), [카메라 TF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera_publishing.html#publish-a-tf-tree-for-the-camera-pose).

이 패키지는 원문의 카메라 생성과 다섯 publisher 함수를 통합한 교육용 구현이다. 구문/API 대조와 실제 GPU·ROS 실행 검증을 구분하며 런타임 검증 상태는 `tutorial.json`에 기록한다.
