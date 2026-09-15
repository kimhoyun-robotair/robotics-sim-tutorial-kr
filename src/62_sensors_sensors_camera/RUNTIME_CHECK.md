# 실제 실행 검증

확인일: 2026-09-14. 환경: Isaac Sim 5.1.0-rc.19+release.26219.9c81211b.gl, Ubuntu 24.04, RTX 5070 Ti (16 GiB).

이 기록은 아래 실행 조건에서 실제 프로그램과 출력 파일을 확인한 결과입니다. 이 패키지의 모든 선택 모드·GUI 조작·외부 통합을 검증했다는 뜻은 아닙니다. 필요한 설치·자산·실습 절차는 같은 폴더의 [TUTORIAL.md](TUTORIAL.md)에 있습니다.

## 재현 명령

이 폴더에서 실행합니다. `ISAAC_SIM_PATH`는 자신의 5.1 설치 디렉터리로 지정하고 출력은 존재하지 않는 새 경로를 사용합니다.

```bash
"$ISAAC_SIM_PATH/python.sh" run.py --headless --steps 60 --output /tmp/isaac-tutorial-new-output
```

해당 명령의 기본 모드만 확인했습니다. 실행 중 GUI 클릭은 검사하지 않았습니다.

## 관찰 결과

```json
{
  "image_shape": [
    480,
    640,
    4
  ],
  "projected_points": [
    [
      320.00000267149596,
      318.0487804878049
    ],
    [
      320.0,
      240.00000000000003
    ],
    [
      319.9999973285041,
      161.95121951219514
    ]
  ],
  "lower_pixel_rgb": [
    64,
    218,
    246
  ],
  "upper_pixel_rgb": [
    246,
    218,
    64
  ]
}
```

## 판정

- shape: 통과
- blue_cube_at_projected_pixel: 통과
- red_cube_at_projected_pixel: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "42def3dc5e9560c3e8b50390f392187a735a5cba7aa3fd090249b514cdbd8512"
}
```
