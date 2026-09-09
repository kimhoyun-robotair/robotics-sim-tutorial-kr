# 작성·검증 보고서

검사 기준일은 2026-09-09이다. 대상은 `IsaacSim6.0.1` 브랜치의 Ubuntu 24.04 LTS / ROS 2 Jazzy / Isaac Sim 6.0.1 튜토리얼이다. 다른 브랜치의 코드는 이 검사의 대상이 아니다.

## 수행한 검사와 한계

| 항목 | 수행 환경 | 상태와 의미 |
|---|---|---|
| 공식 문서·API 대조 | NVIDIA 6.0.1 문서 | 설치, 새 센서 API, ROS Extension·노드, import, Replicator 구성 확인 |
| Python 파일·본문 예제 구문 | Ubuntu 24.04 CPU | `scripts/check_repo.py`로 검사; import와 GPU 실행 성공을 뜻하지 않음 |
| 문서 연결·40단계·중간 프로젝트 8개 | 같은 환경 | 상대 파일 링크와 구성 검사 |
| URDF XML·관성·연결과 TOML/YAML | 같은 환경 | 파싱, 양의 질량, 관성 주값·삼각 조건, 링크 참조 검사 |
| 센서·데이터·명령 제한 함수 | 합성 NumPy 배열·파일 | 정상 입력과 의도적으로 잘못된 입력을 함께 검사 |
| 환경 사전 확인 | Ubuntu 24.04.3 LTS, x86_64 | OS만 충족; Isaac Sim `VERSION`·`python.sh`, ROS 2, `nvidia-smi` 없음 |
| PhysX 로봇 안정성·실제 RTX 영상 | 지원 GPU 필요 | **NOT_RUN** |
| 실제 ROS DDS 전달·Nav2·rosbag | Jazzy+Isaac Sim 필요 | **NOT_RUN** |
| GUI·Extension·로봇 외형 시각 검사 | Isaac Sim GUI 필요 | **NOT_RUN** |

현재 작성 환경에서는 시뮬레이션을 실제로 실행하지 못했다. 따라서 무노이즈, 무블랙아웃, 로봇 붕괴 없음, 모든 예제의 실행 성공을 주장하지 않는다. 아래 실행 절차는 사용자가 실제 GPU에서 결과를 얻을 수 있도록 제공하는 검증 도구이다. 실측 결과인 것처럼 만든 스크린샷이나 정상 센서 배열은 포함하지 않았다.

## 정적 검사 재실행

이번 작성에서 실행한 검사 수와 결과는 [validation-results.json](validation-results.json)에 남긴다. 공식 문서 링크의 HTTP 상태·최종 URL·제목은 [sources-checked.json](sources-checked.json)에 기록했다. 링크 접근 성공과 API의 실제 실행 성공은 서로 다른 확인이다.

저장소 루트에서 실행한다. 검사 전용 환경에만 의존성을 설치하고 Isaac Sim 내장 Python을 일괄 업그레이드하지 않는다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_repo.py
.venv/bin/python -m unittest discover -s tests -v
```

GitHub Actions의 `Isaac Sim 6.0.1 static checks`도 이 두 명령을 실행한다. workflow는 `IsaacSim6.0.1`을 대상으로 한다. CI가 통과하더라도 GPU 시뮬레이션이 검증된 것은 아니다.

## 실패를 잡기 위한 검사

다음 경우를 통과시키지 않는지 단위 테스트로 확인한다. 이 테스트의 입력은 의도적으로 만든 검사 데이터이며 Isaac Sim에서 수집한 센서 결과가 아니다.

- 비어 있는 배열, 해상도 불일치, NaN·무한대, 검은 RGB와 opaque alpha
- 픽셀은 모두 같은데 채널 간 색 차이만 있는 단색 RGB
- 깊이 유효 비율 부족, 장면 높이에 맞지 않는 깊이, 불완전한 LiDAR 각도 범위
- 비정상 쿼터니언, 유한하지 않은 명령, 속도 제한 초과
- 누락된 RGB·분할·라벨·장면 파일과 서로 어긋난 프레임 번호
- 라벨 JSON에 이름만 있고 실제 분할 영상에 해당 색의 픽셀이 없는 경우
- `passed`가 boolean이 아닌 값, 실패 오류와 성공 표시가 함께 들어 있는 결과

문제 없이 끝났다는 프로세스 종료 코드만으로 통과하지 않는다. 실제 검사 결과 JSON도 성공이어야 한다. 이전 실행 파일이 새 실행을 통과시키지 않도록 종합 검사는 빈 출력 폴더를 요구한다. ROS를 실행하지 않으면 전체 결과는 PARTIAL이다.

## GPU에서 실행할 절차

개별 실습의 GUI 실행을 먼저 완료한다. 자세한 준비·예상 결과·진단은 [40단계](lessons/40-capstone-regression-lab.md)에 있다.

```bash
source /opt/ros/jazzy/setup.bash
export ISAAC_SIM_PATH="$HOME/isaacsim-6.0.1"
export ROS_DOMAIN_ID=61
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
.venv/bin/python scripts/preflight.py --output artifacts/preflight.json
.venv/bin/python scripts/runtime_suite.py --isaac-path "$ISAAC_SIM_PATH" \
  --with-ros --output-dir artifacts/validation-01
```

이 과정에서 실제로 생성된 `suite.json`, 개별 report, raw 배열, PNG, 로그를 보관한다. 시각 검토에는 로봇의 base 고정·관절 방향·충돌 관통, RGB 구도·밝기, 깊이와 점군의 위치 대응, 분할 경계를 포함한다. GUI·Extension의 저장과 반복 실행도 따로 확인한다.

임계값은 제공한 작은 실험 장면에 맞춘 것이다. 다른 로봇·환경·센서로 바꾸면 요구 동작과 정상 범위를 다시 정의해야 한다. 드라이버·GPU·VRAM·장면 복잡도에 따른 제한은 [6.0.1 Known Issues](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/overview/known_issues.html)와 [Requirements](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)에서 확인한다.
