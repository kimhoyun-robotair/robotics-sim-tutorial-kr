# 실제 실행 검증

확인일: 2026-09-14. 환경: Isaac Sim 5.1.0-rc.19+release.26219.9c81211b.gl, Ubuntu 24.04, RTX 5070 Ti (16 GiB).

이 기록은 아래 실행 조건에서 실제 프로그램과 출력 파일을 확인한 결과입니다. 이 패키지의 모든 선택 모드·GUI 조작·외부 통합을 검증했다는 뜻은 아닙니다. 필요한 설치·자산·실습 절차는 같은 폴더의 [TUTORIAL.md](TUTORIAL.md)에 있습니다.

## 재현 명령

이 폴더에서 실행합니다. `ISAAC_SIM_PATH`는 자신의 5.1 설치 디렉터리로 지정하고 출력은 존재하지 않는 새 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --frames 1 --output /tmp/isaac-tutorial-new-output
```

해당 명령의 기본 모드만 확인했습니다. 실행 중 GUI 클릭은 검사하지 않았습니다.

## 관찰 결과

```json
{
  "frame": 0,
  "time_s": 0.03333333507180214,
  "target_position": [
    0.12191428520636083,
    -0.1587321074991621,
    0.902993325101275
  ],
  "orbit_position": [
    -0.3812491508768334,
    0.7033129352967238,
    1.8
  ],
  "light_intensity": 14904.982421875
}
```

## 판정

- process_exit: 통과
- behavior_outputs: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "83c108bc0d2d19d88c6f4c9e798bad5e862341836fc28dc64968d6edde36e562",
  "orbit_behavior.py": "f9f7e086b0267b4926ae58f08b3af5581b8eaacc3d27e2fb7011c12e0f07745e"
}
```
