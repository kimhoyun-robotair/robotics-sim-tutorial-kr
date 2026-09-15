# 38. 로봇 몸체에 카메라 부착하기

권장 학습 순서 **38** · 로봇 자산 가져오기와 제작 · 출처 ID `t122`

공식 Add Camera and Sensors to a Robot은 이 단계에서 **카메라 부착과 프레임 확인**을 다룬다. 이 패키지는 Isaac Sim 5.1 assets root의 `/Isaac/Samples/Rigging/MockRobot/mock_robot_rigged.usd`를 로컬 편집 layer로 열고, `attach_camera.py`로 실제 mounted camera를 추가한다. 외부 센서를 가짜로 대체하지 않는다.


## 이 실습의 의도

카메라를 움직이는 로봇의 실제 강체 자식으로 부착하여, 외부 시점과 로봇에 고정된 시점의 차이를 확인한다. body 아래 mount에 장착 자세를 두고 camera 자체의 local transform을 identity로 유지하면 장착 위치와 카메라 조작을 구분해 복구할 수 있다. `run.py`는 rigged robot만 열며, 카메라는 사용자가 GUI에서 만들거나 Script Editor에서 `attach_camera.py`를 실행해야 추가된다.

## 실행 후 확인할 것

- **카메라 생성 여부:** 실행기만 열었을 때 새 `car_camera`가 없어도 정상이다. `attach_camera.py` 실행 후 출력되는 `Camera attached:` 경로와 Stage의 실제 body 강체 아래 `camera_mount/car_camera` 구조를 확인한다.
- **장착 자세:** mount의 translation `(-6,0,2.2)`, rotation `(0,-80,-90)`과 camera의 local identity를 Property에서 확인한다. 이 수치는 해당 mock robot용이며, body 부모 Xform이 아니라 실제 움직이는 강체 아래에 붙어야 한다.
- **두 시점의 차이:** Viewport 2를 새 `car_camera`로 전환하고 다른 viewport는 Perspective로 둔다. Play하여 body가 움직일 때 외부 화면에서는 로봇이 이동하고, camera는 body에 대한 장착 위치·방향을 유지하는지 본다. 부착 출력만으로 영상 방향까지 맞았다고 판단하지 않는다.
- **투영 변화:** camera의 focalLength를 24→48로 바꾸면 장착 pose를 유지하면서 시야가 좁아지는지 비교한다. 잘못된 영상은 active camera와 mount 방향·clipping을 함께 조사한다.
- **범위와 저장:** 이 실습의 결과는 USD 카메라와 viewport 시점이다. 이미지 파일·ROS 토픽은 생성하지 않는다. 편집한 local layer를 저장하고, 기존 `camera_mount`가 있을 때 스크립트가 재생성을 거절하면 이전 장착을 먼저 조사한다.

## 실행 환경과 파일

Isaac Sim **5.1.0**, 지원되는 RTX GPU와 GUI가 필요하다. `ISAAC_SIM_PATH`는 `python.sh`가 있는 설치 디렉터리다. Python CLI 도움말은 일반 Python에서도 열린다. 이 패키지는 자체 코드/설정을 가지며 다른 로컬 튜토리얼을 import하지 않는다.

```bash
cd src/38_robot_setup_gui_camera_sensors
export ISAAC_SIM_PATH="$HOME/isaacsim"
python3 run.py --help
"$ISAAC_SIM_PATH/python.sh" run.py --output output/first
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. 창이 없는 `--headless` 실행에는 양수 `--steps`를 반드시 지정한다.

기본 실행은 창을 계속 열어 두므로 아래 GUI 실습을 수행하고 **Ctrl+S**로 로컬 root layer를 저장한 뒤 창을 닫는다. `output/first/stage.usda`와 `initial_inventory.json`이 생긴다. 기존 output은 덮어쓰지 않으므로 다음 실행은 `output/second`처럼 새 경로를 쓴다. 저장한 실습을 다시 열려면 `--stage "$PWD/output/first/stage.usda" --output output/reopen`을 사용한다. 재개 시에도 새 로컬 layer가 이전 결과를 참조한다.

GPU/UI 자동 점검을 위한 한정 실행은 `--headless --steps 120 --output output/check`다. 이는 장면 로드 확인만 하며 GUI 작업이나 로봇 동작의 성공을 증명하지 않는다. 패키지 작성 과정에서는 문법·CLI를 확인했으며 GPU와 실제 GUI 조작은 미검증이다.


## 단계별 실습

1. Stage에서 rigged mock robot의 body rigid body와 두 wheel joint를 찾는다. Play/Stop으로 robot이 움직일 수 있는지 확인한다. 카메라 실습 전 다른 로컬 파일을 가져올 필요가 없다.
2. 수동 방식: **Create → Camera**로 camera를 만들고 `car_camera`로 이름을 바꾼다. eye 메뉴 **Show By Type → Cameras**로 camera wireframe을 표시한다. 또는 원하는 Perspective view에서 camera 메뉴 **Camera → Create from View**를 선택한다.
3. **Tools → Robotics → Camera Inspector**를 열고 Refresh 후 카메라를 고른다. **Window → Viewports → Viewport 2**로 두 번째 viewport를 열어 하나는 Perspective, 다른 하나는 Camera → car_camera로 둔다.
4. camera를 실제 `body` rigid body의 자식으로 옮긴다. 원문 mounting pose는 translation=(-6,0,2.2), rotation XYZ=(0,-80,-90), scale=(1,1,1)이다. 이 숫자는 **이 mock robot**의 크기·좌표계에 맞춘 값이며 일반 로봇의 기본 센서 오프셋이 아니다.
5. 권장 코드 방식은 임시 car_camera를 지운 뒤 **Window → Script Editor**에서 이 패키지 `attach_camera.py`를 열어 Run하는 것이다. 파일 chooser를 쓰거나 파일 내용을 붙여 실행한다. `body/camera_mount/car_camera` 구조를 만든다. camera 자체는 local identity이고 pose는 mount에 있다.
6. Camera Inspector에서 Refresh하고 새 카메라로 viewport를 전환한다. Play: 외부 시점에서는 robot이 움직이고 onboard 시점은 body와의 위치 관계를 유지해야 한다. 로봇 몸체와 지면이 화면에 함께 보이는지 확인한다.
7. camera view를 마우스로 움직이면 camera transform 자체가 바뀔 수 있다. mount를 유지한 채 camera의 local transform만 identity로 되돌려 장착 pose를 복구한다. Ctrl+S로 로컬 layer를 저장한다.

## 카메라/변환 API 해설

`UsdGeom.Camera`는 USD camera schema, `focalLength`와 aperture는 투영 geometry를 정의한다. 이 스크립트는 focal length=24, horizontal aperture=20.955, vertical aperture=15.2908로 설정한다. `clippingRange=(0.01,10000)`은 너무 가까운/먼 geometry가 잘리는 구간이다. 이는 ROS CameraInfo나 sensor frame publication을 만드는 코드가 아니다.

USD 카메라 local 축은 **-Z 전방, +Y 위**다. 로봇 좌표축을 그대로 camera 축이라고 생각하면 90/180도 어긋날 수 있다. 자식 camera의 world transform은 body, mount, camera local transform을 조합한 값이다. `attach_camera.py`는 이름이 body인 **RigidBodyAPI가 있는 prim 하나**를 찾아 붙이고, 중복/애매한 장면이면 오류를 내어 잘못된 장착을 막는다.

한 변수 실험: camera focalLength만 24→48로 바꾸고 시야가 좁아지는지 확인한다. mount 위치는 유지한다. 검은 영상은 wrong active camera, clipping, 지면 아래 pose를 확인한다. body가 움직여도 camera가 남아 있으면 실제 rigid body 밑에 parent되어 있는지 확인한다.

## 출처

- [Isaac Sim 5.1 Tutorial 4: Add Camera and Sensors to a Robot](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_gui_camera_sensors.html)
- 로컬 설명/코드는 해당 버전의 실제 GUI 작업을 재구성한 실습이며 NVIDIA 문서 전문을 복제하지 않는다.
