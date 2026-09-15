# 실제 실행 검증

확인일: 2026-09-14. 환경: Isaac Sim 5.1.0-rc.19+release.26219.9c81211b.gl, Ubuntu 24.04, RTX 5070 Ti (16 GiB).

이 기록은 아래 실행 조건에서 실제 프로그램과 출력 파일을 확인한 결과입니다. 이 패키지의 모든 선택 모드·GUI 조작·외부 통합을 검증했다는 뜻은 아닙니다. 필요한 설치·자산·실습 절차는 같은 폴더의 [TUTORIAL.md](TUTORIAL.md)에 있습니다.

## 재현 명령

이 폴더에서 실행합니다. `ISAAC_SIM_PATH`는 자신의 5.1 설치 디렉터리로 지정하고 출력은 존재하지 않는 새 경로를 사용합니다.

```bash
ROS_DOMAIN_ID=87 "$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 240
```

실제 실행의 원래 명령과 파일별 입력 해시는 아래 기록을 따릅니다. ROS Clock은 별도 ROS 2 Jazzy 수신 노드로 ROS_DOMAIN_ID=87에서 `/clock` 100개를 수신했습니다.

## 관찰 결과

```json
{
  "received": 100,
  "first": 0.050000002,
  "last": 1.700000088,
  "strictly_increasing": true
}
```

## 판정

- real_ROS_receiver: 통과
- monotonic: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "f8ed8b465afb2f96b615a4d46e05c9e0cc4c294bc9e8f724eee0449b5168cc2f"
}
```
