# 튜토리얼 검증 기록

## 무엇을 검증했는가

이번 수정은 Ubuntu 24.04 LTS · ROS 2 Jazzy · Isaac Sim 5.1.0을 대상으로 한다. NVIDIA 5.1.0 문서와 해당 버전 공개 소스를 대조하고 문서·코드 정적 검사를 수행한다. 수정 환경에는 RTX GPU, NVIDIA 드라이버, Isaac Sim, ROS 2가 없다. **물리·렌더링·ROS 통신이 실제로 정상 동작했다고 확인한 결과는 아니다.**

정적 검사는 import에 필요한 모든 확장이 설치됐는지, 실제 에셋이 내려받아지는지, GPU에서 프레임이 생성되는지까지 확인하지 못한다. 아래 장비 검증을 실제 실행하기 전까지 로봇이 무너지지 않는다거나 모든 센서에서 노이즈·블랙아웃이 없다고 보장할 수 없다.

## 검증 결과

검사일은 2026-09-09이다. 아래 정적 검사는 수정된 작업 트리에서 실행했다.

| 검사 | 실행 환경 | 결과 |
| --- | --- | --- |
| 문서 구조·로컬 링크·36단계 순서 | 문서용 Python | 통과 |
| Python 파일·본문 코드의 3.11 문법 | Python AST | 통과 |
| Extension TOML | Python tomllib | 통과 |
| MkDocs strict 빌드·문서 내 anchor | MkDocs 1.6.1 | 통과 |
| RGB-D 좌표 복원과 무효 입력 거부 | NumPy 합성 데이터 | 6개 테스트 통과 |
| 설치·GPU가 없는 경우의 실행기 처리 | 시스템 Python | `NOT_RUN`, 종료 코드 2 확인 |
| 중복 검사명·NaN/Inf timeout 거부 | 시스템 Python | 잘못된 입력 4건 거부 확인 |
| 강체·로봇 제어 | Isaac Sim 5.1 + RTX 필요 | 미실행 |
| RGB·depth·IMU·RTX LiDAR | Isaac Sim 5.1 + RTX 필요 | 미실행 |
| ROS 2·Nav2·MoveIt 2 | Jazzy와 실행 중인 Isaac Sim 필요 | 미실행 |

## 검사 명령

저장소 루트에서 실행한다. 문서 빌드는 README의 문서용 가상환경을 사용하고, 수학 검사는 NumPy가 설치된 Python에서 실행한다.

```bash
python3 scripts/audit_tutorial.py
mkdocs build --strict
python3 -m unittest discover -s tests -v
git diff --check
```

장비 검사는 다음 명령으로 별도 실행한다. 이 환경에서는 설치본·GPU가 없어 `NOT_RUN`으로 종료했다. [실제 사전 검사 JSON](runtime-preflight.json)에 환경 확인 결과와 검사하지 못한 네 예제를 기록했다. GUI Extension·ROS 노드·학습 정책은 이 네 개 standalone 검사에도 포함되지 않으므로 각각의 실습에서 확인한다.

```bash
python3 scripts/validate_runtime.py --isaacsim-path "$ISAACSIM_PATH"
```

카메라 출력의 정밀한 주파수 보정, IMU 축·부호·외부 파라미터 정합성, 장시간 안정성, 다중 GPU 동작은 기본 smoke 검사의 범위 밖이다. 프레임 시각을 저장하고 정지 IMU의 크기를 확인하는 것만으로 이 항목들이 검증됐다고 판단하지 않는다.

## 수정한 주요 위험 요소

- USD 수정 레이어보다 원본 레이어가 강해 이동값이 덮이는 구성을 수정했다. 새 transform만 만들고 적용 순서에 넣지 않는 실수도 구분한다.
- 최소 URDF·Xacro에서 링크·질량·관절 축과 변환 결과를 확인한다.
- 카메라에는 명시 조명·표적·준비 프레임을 두고 depth 출력을 초기화한다. headless에서 렌더링을 생략하지 않는다.
- 센서의 현재 데이터가 이전 프레임인지 구별하도록 수정했다. IMU 유효 상태와 시간 증가를 함께 검사한다.
- 로봇은 물리 핸들을 초기화하고 정지 상태부터 확인한 뒤 작은 제어 명령을 준다.
- GUI Python은 비동기 실행과 구독 해제를 사용한다. 긴 동기 반복문이 앱 갱신을 막지 않도록 한다.
- ROS 실습 workspace는 `IsaacSim-5.1.0` 태그로 고정하고 Python 3.11/3.12 환경을 나눈다.

## 장비에서 확인하는 순서

1. [시스템 점검](../02-getting-started/01-system-requirements.md)으로 GPU·드라이버·Vulkan을 확인한다.
2. [물리·센서 검증 절차](../05-customization/04-validation-performance.md)에 따라 예제를 별도 프로세스에서 실행한다. 제한 시간 초과와 검사 실패를 정상 종료로 처리하지 않는다.
3. 예제가 출력한 JSON 수치와 RGB/depth·point cloud 산출물을 확인한다. 정량 검사만 통과하고 영상에 줄무늬·떨림이 있는 경우도 실패 사례로 기록한다.
4. GUI 모드로 같은 장면을 열어 로봇 자세·바닥 접촉·카메라 방향을 살펴본다.
5. 그다음 ROS 2 Bridge·TF·센서 토픽, Nav2·MoveIt 2를 연결한다. 앞선 단독 센서 검사와 외부 ROS 전달 검사는 별도다.
6. 앱을 닫고 같은 명령으로 다시 시작해 결과를 비교한다. 센서 수·해상도·환경을 바꾸면 그 조건에서 반복한다.

## 결과를 남기는 방법

```text
Isaac Sim: 5.1.0
Ubuntu / kernel:
GPU / VRAM / driver:
저장소 commit:
실행 명령:
종료 코드:
센서 해상도 / 물리 주기:
JSON / 이미지 / 로그 경로:
정지 자세 / 직진 / 정지 결과:
영상·depth·point cloud 확인:
ROS 토픽·TF·QoS 확인:
통과 / 실패 / 미실행:
```

여기서 ‘통과’는 기록한 장면·장비·조건에 한정한다. 렌더링의 노이즈를 숨기기 위해 필터를 먼저 켜거나, 로봇을 강제로 고정해 붕괴 검사를 통과시키지 않는다. 기능을 하나씩 켜서 처음 문제가 생긴 조건을 찾는다.

## 출처

- [Isaac Sim 5.1.0 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/known_issues.html)
- [Isaac Sim 5.1.0 Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [Robot Setup Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/troubleshooting.html)
- [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)
