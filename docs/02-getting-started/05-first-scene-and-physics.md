# 첫 장면: 상자 떨어뜨리고 저장하기

이 장에서는 외부 에셋 없이 바닥·상자·조명만 사용한다. 설치와 에셋 다운로드 문제를 분리하기 쉬운 구성이다. GUI에서 만든 뒤 같은 조건을 standalone Python으로 실행한다.

## 준비와 목표값

Isaac Sim 5.1.0을 열고 `File > New`를 선택한다. 수정 중인 다른 장면이 있다면 먼저 저장한다. Timeline은 Stop 상태여야 한다.

| 항목 | 실습 값 | 의미 |
| --- | --- | --- |
| Stage | 미터, Z-up | 1은 1 m, Z가 높이 |
| 상자 경로 | `/World/Cube` | 코드에서도 같은 경로를 사용 |
| 한 변 | 0.2 m | 반 높이는 0.1 m |
| 초기 중심 | `(0, 0, 1)` m | 바닥과 겹치지 않는 위치 |
| 질량 | 1 kg | 크기만 바꿔 기본 밀도에 맡기지 않음 |
| 바닥 | Z=0 | 상자 중심이 약 0.1 m에서 정지 |
| 물리 주기 | 60 Hz | 240 step은 시뮬레이션 시간 4초 |

## GUI 실습 1: 물체의 크기와 위치 지정

1. `Create > Shape > Cube`로 상자를 만든다.
2. Stage 패널에서 Cube를 선택하고 이름과 부모 경로를 확인한다. 이 실습은 `/World/Cube`를 사용한다. 다른 경로로 만들어졌다면 `/World` 아래로 옮긴 뒤 좌표를 다시 입력한다.
3. Property의 Cube **Size**를 `0.2`로 설정한다. 항목이 안 보이면 속성 검색이나 Raw USD Properties에서 `size`를 찾는다. Transform의 **Scale**은 `(1, 1, 1)`을 유지한다. 기본 Size를 둔 채 Scale로 조절했다면 두 값을 곱한 실제 한 변이 0.2 m인지 확인한다.
4. Transform의 Translate를 `(0, 0, 1)`, Rotate를 `(0, 0, 0)`으로 설정한다.
5. 마우스를 Viewport에 올리고 `F`를 누른다. 선택한 상자가 화면에 잡힌다.

크기를 두 군데에서 줄이면 예상보다 작은 물체가 된다. 예를 들어 `size=0.2`, `scale=0.2`면 한 변은 0.04 m다. 로봇을 가져올 때도 같은 실수를 주의한다.

## GUI 실습 2: 바닥과 물리 구성

1. `Create > Physics > Ground Plane`으로 바닥을 만든다. Translate Z가 `0`인지 확인한다. 이 바닥은 기본 충돌면을 제공한다.
2. `Create > Physics > Physics Scene`으로 물리 장면을 만든다. 공식 5.1 문서에는 `Simulation Scene`이라는 표기도 있으므로 이 이름도 확인한다. 생성되는 prim 유형은 `PhysicsScene`이다.
3. Physics Scene에서 중력 방향 `(0, 0, -1)`, 크기 `9.81`, 물리 계산 빈도 `60` steps/s를 확인한다.
4. Cube를 선택하고 Property의 `+ Add > Physics`에서 **Rigid Body**와 **Collider**를 추가한다. 물리 preset이 두 API를 한꺼번에 추가했다면 중복 추가하지 않는다.
5. Cube에 **Mass** 속성을 추가해 `1.0` kg을 지정한다. 기본 상자 형태의 충돌 근사로 시작한다.
6. Viewport의 물리 충돌체 표시를 켜 상자 겉면과 충돌 형상이 맞는지 확인한다.

Rigid Body는 물체가 중력과 힘에 따라 움직이도록 한다. Collider는 다른 물체와 닿는 면을 계산한다. 강체만 있고 충돌체가 없으면 바닥을 통과할 수 있다. 반대로 강체가 없으면 물체는 움직이지 않는 장애물처럼 남는다.

## GUI 실습 3: 실제 조명 넣기

1. `Create > Lights > Dome Light`(메뉴가 `Light`로 표시되기도 한다)를 선택한다.
2. Stage에 Light prim이 추가되었는지 확인하고 강도는 우선 `700`으로 둔다.
3. 상자와 바닥이 밝게 보이는지 화면에서 확인한다. Dome Light는 장면 주위를 둘러싼 조명이다. 조명과 상자 사이를 가리는 물체는 두지 않는다.

Viewport의 편집용 조명은 센서 카메라의 조명 설정과 다를 수 있다. 이후 카메라 실습에서도 실제 Light prim을 둔다. 밝기는 장면과 렌더 설정에 영향을 받으므로 숫자 하나만으로 영상 정상 여부를 판정하지 않는다.

## GUI 실습 4: Play·Pause·Stop 비교

1. Play를 누르고 상자가 바닥으로 떨어지는 것을 본다.
2. Pause를 누르면 그 순간 위치에서 멈춘다.
3. 다시 Play해 진행한 뒤 Stop을 누른다. 이 실습에서는 초기 위치로 돌아오는지 확인한다.
4. Cube가 바닥을 통과하면 Collider를, 움직이지 않으면 Rigid Body와 Timeline 상태를 확인한다.

상자 중심은 바닥보다 반 높이만큼 높아야 한다. 이 실습에서는 약 0.1 m가 예상값이다. 접촉 허용 오차 때문에 마지막 소수점까지 정확히 0.1일 필요는 없다. 계속 음수로 떨어지거나 큰 속도로 떨리는 결과는 정상으로 처리하지 않는다.

실패 원인을 익히려면 장면 복사본에서 Collider를 제거한 경우와 Rigid Body를 제거한 경우를 한 번씩 비교한다. 실험 후 Stop하고 원래 설정으로 되돌린다. 불안정한 설정을 다음 로봇 실습에 그대로 사용하지 않는다.

## GUI 실습 5: 저장 후 다시 열기

터미널에서 장면을 보관할 디렉터리를 먼저 만든다.

```bash
mkdir -p "$HOME/isaacsim-course/stages"
```

1. Stop 상태에서 `File > Save As`를 선택한다.
2. `$HOME/isaacsim-course/stages/falling_cube.usda`에 해당하는 실제 홈 경로를 입력한다. 파일 대화상자가 환경 변수를 자동 확장한다고 가정하지 않는다.
3. `File > New`로 빈 장면을 열고, 방금 저장한 USDA를 다시 연다.
4. Play해 상자가 동일한 위치에서 떨어지는지 확인한다.

```bash
ls -lh "$HOME/isaacsim-course/stages/falling_cube.usda"
grep -nE 'Cube|PhysicsScene|mass|rigidBody|collision' \
  "$HOME/isaacsim-course/stages/falling_cube.usda"
```

이 명령은 텍스트 USDA를 읽는 보조 검사다. `.usdc`나 바이너리 `.usd`는 USD 도구로 연다. 파일이 존재하는 것만으로 재실행이 성공했다고 판단하지 않는다.

## Python 실습: 전체 예제 실행

저장소 루트에서 [hello_stage.py](https://github.com/kimhoyun-robotair/robotics-sim-tutorial-kr/blob/IsaacSim5.1/examples/standalone/hello_stage.py)를 실행한다. 이 예제는 GUI와 같은 크기의 상자를 사용하고, 제한된 횟수의 계산이 끝나면 종료한다. 옵션과 상세 결과는 [물리·센서 검증](../05-customization/04-validation-performance.md)에서 설명한다.

시스템 ROS를 source하지 않은 터미널에서 이 저장소 디렉터리로 이동한 뒤 다음 명령을 실행한다. 설치 위치가 다르면 `ISAACSIM_PATH`를 실제 위치로 바꾼다.

```bash
export TUTORIAL_REPO="$PWD"
export ISAACSIM_PATH="$HOME/isaacsim"
test -f "$TUTORIAL_REPO/examples/standalone/hello_stage.py"
"$ISAACSIM_PATH/python.sh" examples/standalone/hello_stage.py
```

핵심 생성 코드는 다음과 같다. 아래는 **설명용 부분 코드**다. 실행할 때는 import·초기화·검사·종료 처리가 포함된 위 파일을 사용한다.

```python
world = World(stage_units_in_meters=1.0,
              physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0)
world.scene.add_default_ground_plane()
cube = world.scene.add(DynamicCuboid(
    prim_path="/World/Cube",
    name="falling_cube",
    position=np.array([0.0, 0.0, 1.0]),
    size=0.2,
    mass=1.0,
    color=np.array([0.2, 0.7, 1.0]),
))
world.reset()
for _ in range(240):
    world.step(render=False)
position, orientation = cube.get_world_pose()
```

`SimulationApp` 생성 뒤에 `isaacsim.core.*`와 `omni.*`를 import해야 한다. `world.reset()`은 로봇·강체의 물리 핸들과 초기 상태를 준비한다. 렌더가 필요 없는 낙하 위치 검사에서는 `render=False`를 쓸 수 있지만 **카메라와 RTX LiDAR 검사에는 적용하면 안 된다.** `headless=True`는 창을 숨긴다는 뜻이며 렌더링을 생략한다는 뜻이 아니다.

GUI가 이미 실행 중인 Script Editor에서 같은 코드를 그대로 실행하지 않는다. Script Editor의 비동기 방식과 Extension의 버튼 방식은 [실행 방식 비교](../06-developer/01-python-workflows.md)에서 이어서 다룬다.

## 시간과 저장에 관해 기억할 점

- `physics_dt=1/60`은 물리 계산 한 번이 진행하는 시뮬레이션 시간이다. 240번 계산하면 시뮬레이션 안에서 4초가 지나지만, 실제 실행에 걸리는 시간은 컴퓨터 성능에 따라 달라진다.
- USD의 `timeCodesPerSecond`는 시간 코드를 초로 해석하는 비율이다. 이것만 바꿔 물리 주기나 카메라 출력 빈도가 자동으로 같아진다고 가정하지 않는다.
- 실행 중 PhysX의 위치와 USD 파일에 기록된 초기 Transform은 다를 수 있다. 최종 궤적이 필요하면 매 step의 pose를 별도 기록한다.
- 파일 Export, 종료 코드 0, 정적 문법 검사 중 어느 하나만으로 물리·렌더 검증을 대신할 수 없다.

## 완료 기준

- [ ] 크기·질량·좌표와 Rigid Body·Collider의 역할을 설명할 수 있다.
- [ ] 조명이 있는 장면을 저장하고 다시 실행했다.
- [ ] 상자 중심이 바닥 위 예상 높이에서 안정되는 것을 확인했다.
- [ ] standalone 예제를 실행하고 실제 검사 결과를 읽었다.
- [ ] GUI 시점, 센서 카메라, 물리 step과 렌더 frame의 차이를 이해했다.

## 출처

- [Isaac Sim 5.1.0 Basic Usage Tutorial](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/introduction/quickstart_isaacsim.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Core API Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
- [Python Environment](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/python_scripting/manual_standalone_python.html)
