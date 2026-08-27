# Gazebo Sim 튜토리얼 (한국어)

Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic 환경에서 Gazebo Sim을 처음 실행하는 단계부터 ROS 2 연동, 시스템 플러그인과 자동화 테스트까지 학습하는 실행 중심 튜토리얼입니다.

튜토리얼 전체는 하나의 공통 로봇 `tutorial_bot`을 점진적으로 발전시킵니다.

현재 과정은 초급 12개, 중급 12개, 고급 7개 경로로 완성되어 있으며, nominal/fault 실행과 cleanup receipt를 함께 검증합니다.

```text
SDF World → tutorial_bot의 URDF/Xacro → 센서·DiffDrive → ROS 2 bridge
→ TF·ros2_control·Nav2 → System Plugin·headless test·CI
```

## 지원 환경

| 항목 | 본편 지원 환경 |
| --- | --- |
| 운영체제 | Ubuntu 24.04 LTS |
| ROS 2 | Jazzy |
| Gazebo | Harmonic |
| 아키텍처 / GPU | amd64 / NVIDIA |

다른 조합은 본편의 검증 대상이 아닙니다. 자세한 정책은 [호환성 문서](docs/02_getting-started/00_compatibility.md)를 확인하세요.

## 문서 보기

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

브라우저에서 표시되는 주소를 열면 됩니다. 정적 빌드만 확인하려면 `mkdocs build --strict`를 실행합니다.

## 저장소 구성

- `docs/`: MkDocs 문서 원본
- `docs/images/`: 문서에서 사용하는 미디어
- `examples/gazebo/`: ROS 2 없이 실행하는 SDF 예제
- `examples/ros2_ws/`: ROS 2와 Gazebo를 함께 사용하는 workspace
- `scripts/`: 반복 검증 자동화

전체 과정의 정적·실행 증거는 `scripts/run_course_matrix.py`와 `scripts/audit_course_evidence.py`로 검사합니다. 실행을 건너뛴 결과는 통과로 인정하지 않습니다.

`ref/`는 로컬 참고용 외부 저장소 경로이며 Git에서 제외됩니다. 그 안의 파일은 수정하지 않습니다.

## 라이선스

이 저장소는 [Apache License 2.0](LICENSE)를 따릅니다.
