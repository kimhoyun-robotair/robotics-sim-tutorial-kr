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
  "lights": [
    {
      "position": [
        -1.9508870104080982,
        -1.5504045556790569,
        2.785674723101485
      ],
      "intensity": 13257.964101799003,
      "temperature_K": 3521.19285271608
    },
    {
      "position": [
        -1.4103951161588864,
        0.9626207957600244,
        3.3243333110305264
      ],
      "intensity": 5048.677865173951,
      "temperature_K": 5585.441087248501
    },
    {
      "position": [
        -1.627554442937726,
        -1.9185341665074858,
        3.879603831286267
      ],
      "intensity": 9044.187174163748,
      "temperature_K": 3832.187687388241
    }
  ]
}
```

## 판정

- process_exit: 통과
- lights: 통과

## 실행 입력 파일 SHA-256

```json
{
  "run.py": "ef89435d9da71e7ba001090cffd769a31cba9a02b8db4c260ee7093d8d8e9712",
  "simready_lab.py": "80f0be4a86333c72ca69178cf1c1dc2a1835a65c6e58d1840d0012206315c2d3"
}
```
