# 과정 사용법과 실습 규칙

## 대상 독자

ROS 2의 node, topic, TF라는 용어를 들어 보았지만 Isaac Sim은 처음인 사용자를 대상으로 한다. Python의 함수·class를 읽고 터미널 명령을 실행할 수 있다고 가정한다. USD나 그래픽스 경험은 요구하지 않는다.

## 권장 학습 시간

| 구간 | 권장 시간 | 산출물 |
| --- | ---: | --- |
| 생태계·USD | 6시간 | layer가 분리된 작은 USD stage |
| 설치·GUI | 5시간 | 저장·재실행 가능한 물리 scene |
| 물리·로봇·제어 | 12시간 | controller로 움직이는 articulation |
| ROS 2 | 10시간 | TF·sensor·control ROS graph |
| 커스터마이징 | 10시간 | 자체 robot/environment/sensor package |
| 개발자 과정 | 14시간 | extension 또는 SDG/RL pipeline |
| 미니 프로젝트 | 20시간 이상 | 재현 가능한 프로젝트 보고서 5개 |

## 터미널을 구분하다

이 과정은 다음 세 환경을 명시적으로 구분한다.

```text
[SIM]  Isaac Sim의 python.sh와 extension 환경 (Python 3.11)
[ROS]  /opt/ros/jazzy와 colcon workspace (기본 Python 3.12)
[DOC]  MkDocs 및 정적 검사 환경
```

명령 블록 위의 표기가 다르면 같은 터미널을 재사용하지 않는다. 특히 `[ROS]` 환경을 source한 뒤 `[SIM]`을 실행하는 것은 해당 장에서 요구할 때만 한다.

## 실습 디렉터리 규칙

```bash
mkdir -p "$HOME/isaacsim-course"/{assets,stages,ros2_ws,logs,outputs}
export ISAACSIM_COURSE="$HOME/isaacsim-course"
```

원본 asset은 `assets`, 사람이 저장한 USD는 `stages`, ROS package는 `ros2_ws/src`, 실행 로그는 `logs`, 합성 데이터는 `outputs`에 둔다. 대형 USD와 생성 데이터는 Git에 직접 넣지 않고 manifest와 생성 스크립트를 추적한다.

## 장별 완료 조건

각 실습은 다음 네 가지를 남겨야 완료한 것으로 본다.

1. 재현 명령 또는 launch file을 남기다.
2. 예상 stage 경로, ROS topic, 파일 개수 등 기계적으로 확인할 조건을 남기다.
3. 오류가 났다면 로그와 해결 이유를 남기다.
4. GUI 캡처만이 아니라 USD, Python, graph 또는 ROS 설정 중 하나를 버전 관리하다.

## 단위와 좌표계

- 길이는 meter, 질량은 kilogram, 시간은 second로 정규화하다.
- 각도는 API가 radian인지 degree인지 호출 지점마다 확인하다.
- ROS는 REP-103 관례를 따르고, USD asset의 up axis와 forward axis는 import 때 확인하다.
- sensor frame과 optical frame을 구분하고 TF tree에서 직접 검사하다.

## 실패를 기록하는 방법

```bash
mkdir -p "$ISAACSIM_COURSE/logs"
"$ISAACSIM_PATH/isaac-sim.sh" \
  --/log/file="$ISAACSIM_COURSE/logs/isaac-sim.log"
```

문제를 보고할 때는 Isaac Sim 버전, GPU·driver, 실행 방식, extension 목록, 재현 stage, 전체 오류 앞뒤 문맥을 함께 남긴다. 토큰, 사내 Nucleus 주소, 사용자 경로 같은 비밀 정보는 먼저 지운다.

## 출처

- [Isaac Sim Conventions](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/reference_conventions.html)
- [Troubleshooting](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/overview/troubleshooting.html)
- [Performance Optimization Handbook](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_material/sim_performance_optimization_handbook.html)

