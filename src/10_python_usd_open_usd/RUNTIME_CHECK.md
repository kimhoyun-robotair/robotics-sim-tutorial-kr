# 실제 실행 검증

확인일: 2026-09-14. 환경: Isaac Sim 5.1.0-rc.19+release.26219.9c81211b.gl, Ubuntu 24.04, RTX 5070 Ti (16 GiB).

이 기록은 아래 실행 조건에서 실제 프로그램과 출력 파일을 확인한 결과입니다. 이 패키지의 모든 선택 모드·GUI 조작·외부 통합을 검증했다는 뜻은 아닙니다. 필요한 설치·자산·실습 절차는 같은 폴더의 [TUTORIAL.md](TUTORIAL.md)에 있습니다.

## 재현 명령

이 폴더에서 실행합니다. `ISAAC_SIM_PATH`는 자신의 5.1 설치 디렉터리로 지정하고 출력은 존재하지 않는 새 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 2 --output /tmp/isaac-tutorial-new-output
```

해당 명령의 기본 모드만 확인했습니다. 실행 중 GUI 클릭은 검사하지 않았습니다.

## 관찰 결과

```json
{
  "session_radius": 1.0,
  "saved_radius": 0.5,
  "transform_max_error": 1.1102230246251565e-16
}
```

## 판정

- process_exit: 통과
- layer_strength: 통과
- transform: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "da6a4e1588036b0c849bd998830ce33dabe3016639623a60229ab2433a11e235"
}
```
