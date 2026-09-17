# USD 예제 실행 검증

[학습 안내](README.md)

확인일: **2026-09-15**. 아래는 예제에 적힌 기대 결과와 실제 실행 결과를 비교한 기록입니다.

## 1. 일반 OpenUSD 예제 01–03

- 환경: Linux, Python **3.12.3**, PyPI **usd-core 25.5.1**, `Usd.GetVersion() == (0, 25, 5)`.
- 실행: `.venvs/usd-tutorial/bin/python`으로 각 예제의 절대경로와 새로운 `--output`을 지정. 작업 디렉터리는 `/tmp`로 두어 저장소 루트 의존 여부도 확인했습니다.
- 세 예제 모두 종료 코드 0. 생성 파일은 별도 Python 프로세스에서도 다시 열어 검사했습니다.

| 예제 | 실제 확인한 결과 |
|---|---|
| 01 | defaultPrim `/World`, 크기 `0.5`, 사용자 속성·관계 저장 유지. Default 월드 위치 `(1.25, 0, 0.25)`, 시간 코드 12의 월드 위치 `(1.5, 0, 0.25)` |
| 02 | 합성 결과 Left=`1.0`, Right=`2.0`. 원본=`1.0`, 배치 Layer의 Right=`1.5`. override를 제외하면 Right=`1.5`로 복귀. Flatten의 값은 같고 reference/sublayer 연결은 제거됨 |
| 03 | small=`0.5`, large=`1.0`. 원본 파일의 선택은 small 유지. Payload의 Body가 LoadNone에서는 없고 Load 후 나타나며 Unload 후 사라짐. 저장한 장면을 기본 Open하면 large가 로드됨 |

세 예제의 `--help`는 USD가 없는 일반 Python에서도 동작했습니다. 같은 출력 디렉터리를 재사용하면 종료 코드 2로 거부했습니다.

## 2. Isaac Sim 물리 예제 04

- 설치: Isaac Sim **5.1.0-rc.19+release.26219.9c81211b.gl** (`VERSION` 파일 표기).
- GPU: **NVIDIA GeForce RTX 5070 Ti**.
- 실행 명령: `~/isaacsim/python.sh usd/04_isaacsim_physics.py --headless --steps 240`.
- 종료 코드 0. CSV는 헤더 외 **241행**이며 측정 시작 행과 물리 240스텝을 포함합니다.

| 측정 | 첫 행 (`step=0`) | 마지막 행 (`step=240`) |
|---|---:|---:|
| `time_s` | 0.0333333 | 4.0333335 |
| `z_m` | 1.9918250 | 0.2499999 |
| `vz_m_s` | -0.3270000 | -0.0001353 |

바닥 윗면 0 m와 큐브 반높이 0.25 m에서 기대 접지 높이를 정했습니다. 마지막 높이 오차 `< 0.01 m`, 수직 속도 크기 `< 0.01 m/s`, 첫 측정 대비 낙하량 `> 1.5 m`를 만족했습니다. `reset()`의 초기화 때문에 첫 측정은 설계 시각 0과 다를 수 있습니다.

저장한 `initial_scene.usda`를 별도로 열어 설계 높이 **2 m**, 질량 **1 kg**, 큐브의 강체·충돌·질량 API, 정적 바닥, 외부 Layer 의존성 없음도 확인했습니다. `--help`, 잘못된 스텝 수(0/음수), 기존 출력 경로 거부도 확인했습니다.

**검증하지 않은 범위:** GUI의 화면·Pause·창 닫기 동작, Windows 실행, 다른 GPU·Isaac Sim 버전. Headless 물리 결과를 GUI 시각 검증으로 간주하지 않습니다.

## 3. 문서·코드 확인

- Python 네 파일의 구문과 문서의 실행 명령·기대값을 확인했습니다.
- Stage/Prim/Layer, 합성·저장, URDF 비교는 별도의 읽기 전용 검토에서도 수정이 필요한 문제를 찾지 못했습니다.
- 설명 문서와 Python 출처 링크의 응답, 문서 사이의 로컬 연결을 확인했습니다.

실행 산출물은 로컬의 `outputs/` 또는 `/tmp`에 있으며 저장소에는 추가하지 않습니다. 동일 결과를 재현하려면 [학습 안내의 명령](README.md)을 실행하세요.

## 출처

- [ISAAC_SIM.md](ISAAC_SIM.md): 물리 계산의 기대값과 초기화 설명, 관련 공식 문서.
- [LIBRARIES.md](LIBRARIES.md): 실행 환경과 OpenUSD 설치 출처.
