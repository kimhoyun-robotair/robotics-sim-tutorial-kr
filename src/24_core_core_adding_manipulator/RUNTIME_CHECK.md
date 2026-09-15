# 실제 실행 검증

확인일: 2026-09-14. 환경: Isaac Sim 5.1.0-rc.19+release.26219.9c81211b.gl, Ubuntu 24.04, RTX 5070 Ti (16 GiB).

이 기록은 아래 실행 조건에서 실제 프로그램과 출력 파일을 확인한 결과입니다. 이 패키지의 모든 선택 모드·GUI 조작·외부 통합을 검증했다는 뜻은 아닙니다. 필요한 설치·자산·실습 절차는 같은 폴더의 [TUTORIAL.md](TUTORIAL.md)에 있습니다.

## 재현 명령

이 폴더에서 실행합니다. `ISAAC_SIM_PATH`는 자신의 5.1 설치 디렉터리로 지정하고 출력은 존재하지 않는 새 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 1800 --output /tmp/isaac-tutorial-new-output
```

해당 명령의 기본 모드만 확인했습니다. 실행 중 GUI 클릭은 검사하지 않았습니다.

## 관찰 결과

```json
{
  "cube_target_error_m": 0.002613832367330498
}
```

## 판정

- controller_done: 통과
- actual_cube_at_target: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "750ffe9cdc75a3c7db921848c02cac51b572ed705deedb1dbbf7ba68adba8d5a",
  "pick_task.py": "62f3d41d877b9492ffbc1edf280c99958924033f88e28ee41bfae590ed603cdd"
}
```
