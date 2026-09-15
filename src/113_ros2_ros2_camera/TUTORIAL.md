# 113. 두 카메라의 RGB·깊이·인식 결과를 ROS 2로 보내기

권장 학습 순서 **113** · ROS 2 연결과 기본 통신 · 출처 ID `t011`

이 패키지는 Isaac Sim 5.1의 **ROS 2 Cameras**를 독립 실행 가능한 작은 실험실로 재구성했다. 두 카메라와 색이 다른 물체를 직접 만들고, 각각 RGB, 깊이, 깊이 기반 점군, CameraInfo를 발행한다. 원문은 TurtleBot이 있는 장면에서 GUI로 진행한다. 여기서는 로봇 모델과 창고 다운로드 없이 같은 카메라 그래프를 관찰할 수 있다. 아래 GUI 실습은 원문의 카메라 배치, 그래프 작성, 단축 메뉴까지 다룬다.

**실행 종료:** `--steps`를 생략한 GUI 실행은 창을 직접 닫을 때까지 시뮬레이션 스텝과 ROS 통신을 계속합니다. `--steps 1200`처럼 양수를 지정하면 해당 횟수 뒤 종료합니다. `--headless`만 지정하면 기존 기본값 1800회를 사용합니다. 이전 `--frames` 옵션은 `--steps` 없는 headless 실행의 횟수만 정하며, GUI 종료에는 영향을 주지 않습니다. `--steps`를 지정하면 `--frames`보다 우선하며 0과 음수는 허용하지 않습니다.

## 준비와 실행

- NVIDIA RTX GPU와 Isaac Sim **5.1.0**이 필요하다. 일반 Python은 `--help`만 실행할 수 있다.
- Ubuntu 22.04라면 ROS 2 Humble, Ubuntu 24.04라면 Jazzy를 사용한다. 두 배포판을 같은 셸에서 source하지 않는다. ROS 2의 `sensor_msgs`, `rviz2`, `rqt_image_view`가 필요하다. 경계 상자에는 `vision_msgs`도 필요하다.
- 토픽은 이름이 있는 통신 통로다. Isaac Sim은 publisher, `ros2 topic echo`와 RViz는 subscriber다. 서로 같은 `ROS_DOMAIN_ID`를 사용해야 DDS가 상대를 발견한다.
- 이 폴더만 복사해도 실행된다. 다른 로컬 튜토리얼을 읽거나 가져올 필요가 없다.

시뮬레이터 터미널에서 설치 위치와 ROS 배포판을 자기 환경에 맞춘다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ISAAC_SIM=/home/hoyunkim/isaacsim
"$ISAAC_SIM/python.sh" run.py
```

다른 터미널도 같은 ROS 환경을 source한 뒤 실행한다.

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
ros2 topic list
ros2 topic echo /camera_1/camera_info --once
ros2 topic hz /camera_1/rgb
ros2 run rqt_image_view rqt_image_view /camera_1/depth
```

GUI에서는 창을 직접 닫을 때까지 렌더링과 토픽 발행이 계속된다. `--steps 1800`은 1800번의 시뮬레이션 스텝 뒤 종료한다. 화면 없는 실험은 `--headless`를 사용하며 소요 벽시계 시간은 GPU 성능에 따라 달라진다.

## 단계별 관찰

1. Play 상태에서 `/World/Camera_1`, `/World/Camera_2`를 Stage에서 찾는다. 두 번째 카메라는 x축으로 1 m 이동했으므로 같은 큐브를 다른 위치에서 본다.
2. **Window > Viewports > Viewport 2**를 연다. 각 Viewport의 왼쪽 위 Camera 메뉴에서 Camera_1과 Camera_2를 각각 선택한다. 기본 Perspective는 사용자가 장면을 탐색하는 카메라이며, 센서 Camera prim과 다르다.
3. **Window > Graph Editors > Action Graph**에서 `/World/CameraGraph_1`을 선택한다. Tick → Once → Render → 각 Helper의 실행 연결과 Render → Helper의 renderProductPath 데이터 연결을 구별한다.
4. `rviz2`를 실행하고 **Add > Image**의 Topic을 `/camera_1/rgb`로 지정한다. 다른 Image를 추가하고 `/camera_2/rgb`로 지정한다. 두 영상에서 큐브가 차지하는 위치가 달라야 한다.
5. **PointCloud2** 표시를 추가하고 토픽을 `/camera_1/depth_pcl`, Fixed Frame을 `camera_1`로 설정한다. 이 작은 실험은 TF를 발행하지 않으므로 다른 좌표계를 Fixed Frame으로 고르면 변환 오류가 정상이다.
6. CameraInfo의 `width=640`, `height=480`과 9개 K 행렬 원소를 확인한다. 중심점은 `(320,240)`이고, `fx=width*focalLength/horizontalAperture`, `fy=height*focalLength/verticalAperture`다. 코드의 조리개와 초점거리로 fx와 fy는 약 549.75 pixel이다.

## 직접 같은 그래프 만들기

1. 실행 중인 시뮬레이션을 Stop하고 `/World/CameraGraph_2`를 삭제한다. Camera_2는 남긴다. 그래프의 변경은 이 임시 장면에만 적용된다.
2. **Window > Graph Editors > Action Graph > New Action Graph**에서 `/World/MyCameraGraph`를 만든다. 검색창에서 **On Playback Tick**, **ROS2 Context**, **Isaac Run One Simulation Frame**, **Isaac Create Render Product**, **ROS2 Camera Helper**, **ROS2 Camera Info Helper**를 추가한다.
3. Tick의 `tick` → Run One의 `execIn`, Run One의 `step` → Render의 `execIn`을 잇는다. Render의 `execOut`을 두 Helper의 `execIn`에, `renderProductPath`를 두 Helper의 같은 입력에 연결한다. Context의 `context`도 두 Helper의 `context`에 연결한다.
4. Render의 `cameraPrim=/World/Camera_2`, `width=640`, `height=480`, `enabled=True`를 설정한다. Camera Helper는 `type=rgb`, `topicName=manual_rgb`, `frameId=camera_2`로 설정한다. Info Helper는 `topicName=manual_camera_info`, 같은 frameId를 사용한다. Context는 **Use Domain ID Env Var**를 켠다.
5. Play 후 `ros2 topic echo /manual_camera_info --once`로 확인한다. 이미지가 실제 렌더링되는 것은 별도 Render Product가 있기 때문이다. Viewport를 다른 카메라로 바꾸어도 이 토픽의 카메라는 바뀌지 않는다.
6. 단축 경로도 실습한다. Stop 후 **Tools > Robotics > ROS 2 OmniGraphs > Camera**에서 Graph Path=`/World/ShortcutCamera`, Camera Prim=`/World/Camera_2`, Frame ID=`camera_2`, Node Namespace=`shortcut`을 입력하고 RGB와 Depth를 선택한다. 기존 그래프에 붙일 때만 **Add to an existing graph?**를 선택한다. Play 후 `/shortcut`으로 시작하는 토픽을 확인한다.

## 깊이와 인식 데이터

Helper 하나는 한 종류의 데이터만 담당한다. `rgb`는 색, `depth`는 영상 평면까지의 거리(m), `depth_pcl`은 깊이와 내부 파라미터를 이용해 역투영한 점군이다. `bbox_2d_tight`, `bbox_2d_loose`, `bbox_3d`, `semantic_segmentation`, `instance_segmentation`도 선택할 수 있다.

```bash
"$ISAAC_SIM/python.sh" run.py --perception semantic_segmentation
"$ISAAC_SIM/python.sh" run.py --perception bbox_3d
```

코드는 Red와 Blue prim에 `red`, `blue` 의미 라벨을 붙인다. `/camera_1/labels`에는 색/객체 ID를 해석할 라벨 정보가 발행된다. 다른 실행으로 바꿀 때는 기존 프로그램을 종료한다. **Helper가 한번 활성화된 뒤에는 type만 바꾸어 재사용하지 않는다.** 새 노드를 만들거나 장면을 다시 로드해야 내부 파이프라인이 올바르게 생성된다. 경계 상자 사용 전 ROS 환경에 `vision_msgs`가 있는지 `ros2 interface show vision_msgs/msg/Detection3DArray`로 확인한다.

## API와 USD 개념

- **Stage / prim**: Stage는 장면 전체, prim은 `/World/Camera_1` 같은 경로로 식별되는 객체다. `UsdGeom.Camera.Define`은 카메라 prim을 만들고 `XformCommonAPI`는 위치·회전·크기를 설정한다. USD 카메라는 로컬 -Z 방향으로 보며 +Y가 위다.
- **Render Product**: 카메라, 해상도, 렌더 출력의 묶음이다. 카메라 prim만 존재한다고 ROS 이미지가 생기지는 않는다.
- **`og.Controller.edit`**: 노드를 생성하고 값을 넣고 포트를 연결한다. 실행 포트는 언제 처리할지, 데이터 포트는 무엇을 처리할지 정한다.
- **Camera Helper**: 렌더 결과를 ROS 메시지로 바꾸는 `/Render/PostProcessing/SDGPipeline`을 세션 안에서 구성한다. 이 생성된 파이프라인은 Stage 파일에 영구 저장되는 모델 데이터가 아니다.
- **CameraInfo**: K는 3×3 내부 파라미터, P는 3×4 투영 행렬, R은 스테레오 정렬 회전이다. 단안에서는 P의 평행이동 항이 0이다. 두 Render Product를 Info Helper의 좌/우 입력에 넣으면 스테레오 baseline을 반영할 수 있다.

## 성공 기준과 작은 실험

두 RGB 토픽에서 서로 다른 시점의 영상이 보이고, 깊이 토픽이 발행되며, CameraInfo 해상도가 640×480이면 기본 경로를 확인한 것이다. `ros2 topic list`에 이름만 보이는 것은 영상 수신 검증을 대신하지 않는다.

변수 하나만 바꾸는 실험: 코드의 `camera.CreateFocalLengthAttr(18)`을 `36`으로 바꾸고 재실행한다. 큐브가 더 크게 보이고 CameraInfo의 fx, fy가 두 배가 되는지 비교한다. 다른 위치·해상도는 그대로 둔다.

## 문제 해결

- 토픽이 없다: 프로그램이 실행 중인지, Bridge 확장 로드 오류가 없는지, 양쪽 ROS_DOMAIN_ID가 같은지 확인한다.
- 이름은 보이는데 영상이 없다: RViz Image의 Reliability를 Best Effort로 바꾸고 다시 확인한다. `ros2 topic info -v /camera_1/rgb`로 실제 publisher QoS를 확인한다.
- 깊이가 흑백 두 구역뿐이다: 무한대 배경이 자동 대비 범위를 넓힐 수 있다. 카메라가 바닥·벽을 향하게 하고 유한한 거리 범위를 관찰한다.
- ROS 단축 메뉴가 없다: **Window > Extensions**에서 `isaacsim.ros2.bridge`를 켠다.
- 별도 TurtleBot 예제를 재현하려면 Content Browser의 **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd**를 연다. 이는 외부 NVIDIA 자산이 필요한 원문 확장 실습이며 본 코드의 실행 조건은 아니다.

## 출처와 검증 범위

[Isaac Sim 5.1 ROS 2 Cameras](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html), [카메라 그래프](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html#building-the-graph-for-an-rgb-publisher), [CameraInfo](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html#camera-info-helper-node), [그래프 단축 메뉴](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_camera.html#graph-shortcut).

해설과 실험 장면은 이 저장소에서 새로 작성했다. 설치된 5.1 노드 스키마와 대조했으며 GPU 렌더링·ROS 수신 실측 상태는 `tutorial.json`의 verification을 확인한다.
