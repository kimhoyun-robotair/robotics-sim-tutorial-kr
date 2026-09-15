# 튜토리얼 API 간단 안내

현재 `src/00`–`src/179`의 **180개 튜토리얼**에서 만나는 Isaac Sim 관련 API를 짧게 소개한다. 역할과 실제 사용 이름을 읽고, 자세한 기능·문법은 각 문서 마지막의 공식 링크에서 확인하면 된다.

- [API 색인 — 처음 등장하는 순서](INDEX.md)
- [180개 튜토리얼별 사용 API](TUTORIAL_INDEX.md)

## 구분과 순서

`World`, `objects`, `prims`, 개별 `utils` 모듈처럼 서로 다른 API 경로는 별도 파일로 나눴다. `pxr`도 `Gf`, `UsdGeom`, `UsdLux` 등 모듈별로 분리했다. 같은 모듈의 여러 메서드·클래스는 짧게 묶으며, `Scene`처럼 반환 객체로 직접 사용하는 Core 클래스도 따로 찾을 수 있다.

파일 앞의 세 자리 숫자는 **API 색인 번호**이다. 00번 튜토리얼부터 처음 만나는 순서로 부여했다. 같은 튜토리얼에서는 `run.py` → 나머지 코드·설정 파일의 경로 순 → 안내문 코드 블록 순으로 읽고, 같은 파일에서는 등장 줄 순으로 정렬했다. import로 처음 만나거나 실행 설정에서 먼저 등장한 경우도 포함한다.

## 포함 범위

Python 파일과 안내문의 코드 블록, Script Editor·확장 소스, 실제 호출하는 Kit 명령·OmniGraph 노드, Replicator YAML/JSON 설정, C++ 확장·노드 API를 확인했다. `carb`, `usdrt`, Warp와 Isaac Sim용 ROS 인터페이스도 포함한다. GUI 메뉴만 조작하는 도구와 일반 NumPy·Python 표준 라이브러리·범용 ROS API는 별도 API 항목을 만들지 않았다. 설치본의 외부 예제를 호출만 하는 실습은 저장소에서 확인할 수 있는 API까지만 다룬다.

## 공식 문서 기준

Isaac Sim 문서는 저장소에 맞춰 **5.1.0**으로 연결했다. Kit·Carbonite·OpenUSD·USDRT 같은 기반 API는 NVIDIA의 해당 API 문서, Warp는 공식 Warp 문서로 연결했다. 일부 기반 문서는 `latest`라 설치본과 차이가 있을 수 있다. 개별 API 참조가 공개되지 않은 내부 모듈은 해당 API를 다루는 공식 확장 설명이나 활용 예제로 연결하고 링크에 구분을 적었다.

Standalone Python에서는 `SimulationApp`으로 앱을 시작한 뒤 시뮬레이터 API를 import한다. 이미 열린 GUI의 Script Editor에서는 앱을 다시 만들지 않는다. 이 색인은 실행 코드 전체를 대신하지 않으므로 연결된 튜토리얼에서 사용 맥락을 함께 확인한다.
