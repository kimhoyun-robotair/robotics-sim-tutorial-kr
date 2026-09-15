# 164. t144 · 공식 강화학습 정책 예제를 실행하고 비교하기

권장 학습 순서 **164** · 병렬 환경과 학습 정책 활용 · 출처 ID `t144`

공식 5.1 예제 모음에는 H1 보행, Spot 보행, Franka 서랍 열기, ANYmal standalone 예제가 있다. 이 패키지의 `run.py`는 설치된 H1/Spot 정책을 직접 실행하고 시간에 따른 이동 기록을 남긴다. Franka와 ANYmal은 아래의 공식 native workflow로 실습한다. 어떤 경우에도 가짜 추론값으로 성공을 표시하지 않는다.

## 준비와 실행

Isaac Sim **5.1.0**, RTX GPU와 호환 드라이버, 5.1 자산 팩/서버가 필요하다. 정책 extension의 실제 설치 이름은 `isaacsim.robot.policy.examples`다. UI에서 예제가 보이지 않으면 Window > Extensions에서 해당 이름을 활성화한다. 각 패키지는 독립적이며 별도 공통 코드가 없다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/164_motion_robot_policy_example
"$ISAAC_SIM/python.sh" run.py --robot spot
"$ISAAC_SIM/python.sh" run.py --robot h1 --robots 3 --output output/h1.csv
```

1. Spot은 500 Hz, H1은 200 Hz 물리로 실행한다. 2초마다 전진 `(0.4,0,0)` → 전진+회전 `(0.3,0,0.4)` → 정지 `(0,0,0)`를 반복한다.
2. `trajectory.csv`에서 명령과 실제 몸통 위치를 비교한다. `vx`, `vy`는 로봇 몸체 좌표 m/s, yaw는 rad/s다. 회전 후 +X 명령의 월드 방향이 달라짐을 관찰한다.
3. 로봇 간 간격은 2 m다. `--robots 1`과 `3`만 바꿔 각 로봇이 별도 prim, articulation, 정책 내부 상태를 갖는지 확인한다. 이는 성능 벤치마크가 아니다.
4. 종료 시 실제 최종 world pose가 출력된다. z가 지면에 가깝게 붕괴했으면 정상 보행으로 판정하지 않는다. 파일이 있으면 다른 `--output`을 쓴다.

`--steps`를 생략하면 GUI에서 사용자가 창을 닫을 때까지 시뮬레이션을 계속합니다. `--steps 2000`처럼 횟수를 지정하면 자동 종료합니다. `--headless` 실행에서 생략하면 2000회로 제한됩니다.


## H1·Spot·Franka GUI 실습

새 stage를 만들고 **Window(s) > Examples > Robotics Examples > POLICY**를 연다.

1. **Humanoid > LOAD**로 H1을 불러온다. 위 화살표/NUM 8로 전진, 좌·우 화살표/NUM 4·6으로 회전한다. 키를 놓았을 때와 계속 누를 때를 비교한다.
2. 새 stage에서 **Quadruped > LOAD**로 Spot을 불러온다. 위/아래는 전후, 좌/우는 측면 이동, `N`/`M`은 좌우 회전이다. H1의 좌우키 의미와 다르다.
3. 새 stage에서 **Franka > LOAD**를 누른다. 팔이 손잡이에 접근하고 서랍을 연 뒤 유지하는지 관찰한다. RESET 후 같은 동작이 반복되는지 확인한다. 팔의 임의 초기 위치를 바꾸면 훈련 분포 밖이 될 수 있다.
4. 동일한 예제를 다시 실행할 때는 RESET 또는 새 stage를 사용한다. GUI 재생/정지와 정책 초기화를 임의로 섞으면 articulation handle이 무효화될 수 있다.

## ANYmal 및 원본 standalone 실습

아래 명령은 **Isaac Sim 설치 폴더에서** 실행한다. 파일은 이 저장소가 복사한 코드가 아니라 5.1에 제공되는 native 예제다. 창을 닫으면 종료된다.

```bash
cd "$ISAAC_SIM"
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/h1_standalone.py --num-robots 5 --env-url /Isaac/Environments/Grid/default_environment.usd
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/spot_standalone.py
./python.sh standalone_examples/api/isaacsim.robot.policy.examples/anymal_standalone.py
```

ANYmal 예제는 거친 지형 정책이며 상태·속도 명령·주변 지형을 입력으로 사용한다. 키는 Spot과 같은 전후/좌우 및 `N`/`M` 회전이다. 정책 파일 표의 ANYmal **flat** 정책과 rough terrain standalone을 동일하게 간주하지 않는다. 원본 H1에서 `--num-robots`만 1→5로 바꾸고 prim 수를 확인한다.

## API, 자산, 정책 파일

`World`는 물리 step과 지면을 관리한다. `H1FlatTerrainPolicy`/`SpotFlatTerrainPolicy` 생성자가 로봇 USD를 reference하고 신경망을 불러온다. `initialize()`는 첫 물리 callback에서 호출하며 `forward(dt, command)`가 관측→추론→관절 목표 적용을 수행한다. 각 로봇의 `_previous_action`은 자기 이전 출력을 저장하므로 서로 공유하지 않는다. `robot.get_world_pose()`는 월드 기준의 실제 위치와 WXYZ quaternion이다.

USD는 화면 mesh 외에 관절과 collider를 포함한다. `/World/Robot_0` 등의 **prim 경로**는 로봇을 식별하며 정책 파일 경로와 다르다. 정책은 USD 자체가 아니라 학습된 함수다. 정책의 관측 layout, 관절 이름 순서, default position, gain, physics dt가 로봇과 일치해야 한다.

5.1 자산 루트 기준 파일은 다음과 같다. Content Browser에서 각 파일을 우클릭 > Download로 저장할 수 있다.

| 로봇/과제 | 정책 디렉터리와 파일 |
|---|---|
| H1 flat | `/Isaac/Samples/Policies/H1_Policies/`: `h1_policy.pt`, `h1_env.yaml`, `agent.yaml` |
| Spot flat | `/Isaac/Samples/Policies/Spot_Policies/`: `spot_policy.pt`, `spot_env.yaml`, `agent.yaml` |
| ANYmal C flat | `/Isaac/Samples/Policies/Anymal_Policies/`: `anymal_policy.pt`, `sea_net_jit2.pt`, `anymal_env.yaml`, `agent.yaml` |
| Franka drawer | `/Isaac/Samples/Policies/Franka_Policies/Open_Drawer_Policy/`: `policy.pt`, `env.yaml` |

## 막힐 때와 검증 범위

정책 다운로드 실패는 자산 루트/네트워크 문제부터 확인한다. 넘어지면 500/200 Hz 차이와 joint 순서/gain을 확인한다. 화면이 보이지 않으면 `--headless`를 제거한다. CLI 파싱과 문법은 확인했지만 이 패키지의 보행·서랍·ANYmal GPU 실행은 아직 검증하지 않았다.

## 출처

[Isaac Sim 5.1 Reinforcement Learning Policies Examples](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html), [정책 파일 표](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html#policies-files), [standalone 실행](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_simulation/ext_isaacsim_robot_policy_example.html#standalone-examples). API 경로는 설치된 `exts/isaacsim.robot.policy.examples`와 대조했다.
