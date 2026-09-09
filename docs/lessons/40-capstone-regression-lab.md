# 40단계 — 최종 심화 프로젝트: 로봇·센서·ROS 회귀검사 실험실

## 완성할 결과

하나의 명령으로 물리 안정성, 관절 제어, RGBD, RTX LiDAR, 데이터 생성, ROS 명령과 자동 정지를 검사하고 결과·로그·원시 데이터를 남기는 실험실을 만든다. 새로운 로봇 USD나 렌더 설정을 도입할 때 이전에 통과하던 기능이 깨지는지 찾아내는 프로젝트이다.

검사들은 원인을 구분하기 위한 독립 장면으로 실행된다. 관절 로봇의 물리 시험과 센서 검사, ROS 운동학 시험을 하나의 검증 절차로 묶는다. ROS 통신용 상자는 바퀴의 접촉을 시뮬레이션하는 차량이 아니므로 이 결과를 Nav2 주행이나 실제 로봇의 안전성 검증으로 확대 해석하지 않는다. 실제 이동 로봇은 35단계의 Carter 실습으로 별도 확인한다.

## 준비와 실행 순서

1. 39단계에서 로컬 항목이 모두 PASS인지 확인한다. GUI 중간 프로젝트 1과 Extension 중간 프로젝트 3의 저장·재실행·중복 생성 검사도 끝내 둔다.
2. 새 터미널을 연다. 이전 Isaac Sim, `ros2 topic pub`, rosbag 재생, Nav2를 종료한다. 동일 domain에서 또 다른 `/clock`과 명령 발행기가 동작하면 결과가 섞인다.
3. 아래 환경을 지정한다. `ROS_DOMAIN_ID=61`은 이 실습의 선택이며 같은 네트워크에서 사용 중이면 비어 있는 다른 값으로 양쪽을 함께 바꾼다.

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
cd "$TUTORIAL_ROOT"
.venv/bin/python scripts/preflight.py --output artifacts/preflight-final.json
.venv/bin/python scripts/runtime_suite.py \
  --isaac-path "$ISAAC_SIM_PATH" --with-ros \
  --output-dir artifacts/capstone-01
```

4. 자동 검사는 로컬 장면들을 차례로 실행한 뒤 ROS 장면의 `READY`를 기다린다. 이어 Jazzy 시스템 Python의 검사기가 짧은 이동 명령을 발행하고 명령 중단 후 정지하는지 관찰한다. 별도 조종 노드를 실행하지 않는다.
5. 종료 후 `artifacts/capstone-01/suite.json`을 연다. FAIL이면 실패 항목의 세부 JSON과 로그를 읽고, 수정한 다음 새 폴더에서 다시 실행한다. 이전 성공 결과를 새 실행의 증거로 쓰지 않는다.

## 무엇을 검증하는가

| 항목 | 입력 | 확인할 결과 |
|---|---|---|
| 낙하 실험 | 고정 시간 간격, 물체와 지면 | 제한 스텝 동안 유한한 위치, 지면에 정착 |
| 관절 실험 | 제공 URDF, 제한된 목표·토크 | 관절 순서, 제한, 고정 base, 자세 안정성 |
| RGBD 검사 | 조명과 색상 기준 물체 | 비어 있지 않은 RGB, 암전 여부, 유효 깊이 |
| LiDAR 검사 | 벽과 상자 | 유효 hit, 유한 거리, 공간 범위 |
| 데이터셋 | seed 601, 12프레임 | RGB·분할·라벨 대응, 프레임 누락 여부 |
| ROS 통신 | `/tutorial/cmd_vel` | clock/odom/TF, 이동 발생, watchdog 정지 |

시간 초과와 비정상 종료도 FAIL이다. 센서가 비어 있거나 검사가 아예 실행되지 않은 상태는 PASS가 아니다. 이러한 규칙을 [runtime_suite.py](../../scripts/runtime_suite.py)의 `passed()`와 결과 집계 부분에서 확인할 수 있다.

```python
# 결과 파일을 읽었다고 성공한 것은 아니다.
ok = result["returncode"] == 0 and passed(evidence)
status = "PASS" if ok else "FAIL"
```

## 사람이 확인할 부분을 마무리하다

자동 검사 뒤에는 다음 관찰 내용을 `visual-review.md`에 직접 적는다. 수치가 정상 범위에 있어도 로봇이 의도한 방향으로 움직이는지, 색상이 맞는지, 라벨 경계가 맞는지는 직접 보아야 한다.

```markdown
# 시각 검토
- 날짜 / GPU / 드라이버 / VERSION 전체 문자열:
- 확인한 실행 폴더:
- GUI 실험실 저장 후 다시 열기:
- Extension 버튼 반복과 비활성화:
- 관절 로봇: base 고정, 관절 방향, 충돌 관통 여부:
- RGBD: 첫/중간/마지막 프레임의 구도·밝기·깊이:
- LiDAR: 벽 위치와 점군 방향 대응:
- 데이터셋: RGB와 분할 경계 대응:
- 남은 문제와 로그 경로:
```

GUI를 보면서 다시 확인하려면 개별 예제에서 `--headless`만 뺀다. 수동 실행도 별도 결과 폴더를 쓴다. 창이 너무 빨리 닫히는 예제는 저장된 `scene.usda` 또는 해당 예제의 `*_scene.usda`를 GUI에서 열고 Play 이전의 구성부터 확인한다. 런타임 Python 센서 객체는 USD에 저장되지 않을 수 있으므로 저장 장면을 여는 일과 센서 수집 코드를 다시 실행하는 일을 구분한다.

## 통과 기준과 비교 실험

완료 조건은 `suite.json`의 모든 자동 항목이 PASS이고, 시각 검토에 미해결 문제가 없는 상태이다. GPU에서 실제로 실행한 결과가 없다면 이 프로젝트는 준비만 끝난 것이며 실행 검증 완료라고 쓰지 않는다.

첫 성공 결과는 기준으로 보관한다. 다음에는 한 번에 한 가지 조건만 바꾼다. 예를 들어 카메라 해상도만 올리거나 로봇의 damping만 바꾸고 새 결과 폴더를 만든다. 바뀐 조건, 통과 여부, 처리 시간과 메모리를 같이 적는다. 그림만 좋아졌는데 센서 누락이 늘었다면 개선이라고 판단하기 어렵다.

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('artifacts/capstone-01')
r = json.loads((root/'suite.json').read_text())
assert r['status'] == 'PASS', '미완료/실패 항목을 먼저 해결한다'
assert all(e['status'] == 'PASS' for e in r['entries'])
print(r['version'])
print([(e['name'], e['status']) for e in r['entries']])
PY
```

## 더 확장하는 방향

새 로봇은 URDF를 바로 전체 자동 검사에 넣기보다 19~22단계 순서로 관절과 충돌을 검증한 뒤 추가한다. 이동 로봇은 Carter 기본 Nav2 성공률과 충돌 여부를 따로 측정한다. Isaac Lab으로 확장할 때에는 학습에 사용하는 행동 차원·관절 순서·단위·관측 정규화와 정책 실행 주기가 일치하는지 확인한다. 이 튜토리얼의 한 관절 로봇에 다른 로봇의 정책을 그대로 적용하지 않는다.

6.0의 Newton backend를 실험하려면 PhysX로 얻은 기준 결과를 먼저 보관하고 지원되는 기능을 공식 문서에서 확인한다. backend 변경은 스위치 하나의 성능 비교를 넘어 물리 모델과 지원 센서의 차이를 확인해야 하는 실험이다. 본 과정의 합격 기준을 Newton에서 검증했다고 가정하지 않는다.

## 공식 참고

[Newton Physics Backend](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/newton_physics.html), [Deploying Policies](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/isaac_lab_tutorials/tutorial_policy_deployment.html), [ROS 2 Putting It All Together](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/ros2_tutorials/tutorial_ros2_putting_it_all_together.html)를 다음 확장 방향으로 읽는다. 이 단계의 검사 설계와 임계값은 본 튜토리얼의 소형 실험 장면을 위해 작성한 것이다.
