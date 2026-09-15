# 11. USD 저장과 참조: 로봇만 재사용하는 defaultPrim

권장 학습 순서 **11** · Python 실행 환경과 USD 기초 · 출처 ID `t174`

## 독립 패키지 준비와 실행 규칙

이 폴더 하나만 복사해도 실행되도록 작성했다. 다른 튜토리얼, 공통 Python 모듈, 저장소 루트 자산을 가져오지 않는다. Isaac Sim **5.1.0**과 지원 NVIDIA GPU/드라이버가 필요하다. 아래 Linux 명령의 `~/isaacsim`을 실제 설치 경로로 바꾼다. Windows에서는 설치 폴더의 `python.bat`을 사용한다.

이 패키지 폴더에서 `python3 run.py --help`로 옵션을 확인한다. 실제 실행은 `~/isaacsim/python.sh run.py`로 한다. 기본 출력은 이 폴더의 `output/날짜-시간/`이다. `--output /새/폴더`로 지정할 수 있고 기존 경로를 덮어쓰지 않는다. `--steps`를 생략하면 사용자가 창을 닫을 때까지 GUI가 유지된다. 양수 `--steps N`을 지정하면 N번 실행 후 종료한다. `--headless`에서 `--steps`를 생략하면 기존 기본값인 120번 실행 후 종료한다. `--headless`는 창을 숨기며 GPU가 필요 없다는 뜻은 아니다.

## 목표와 예상 결과

몸체 Cube와 두 Cylinder 바퀴로 시각적 mock robot을 만든다. 물리적으로 주행하는 로봇이 아니라 **파일 구성과 reference 실습용 모델**이다. 환경과 로봇을 나란한 루트에 두고 defaultPrim으로 로봇만 재사용한다. 결과는 `robot.usda`, `assembly.usda`, `flattened.usda`, `composition.json`이다.

## 순서대로 실습

1. `~/isaacsim/python.sh run.py`를 실행한다. `robot.usda`의 루트에는 `/mock_robot`과 `/World`가 있으며 `/World`에는 PhysicsScene/Light가 있다.
2. `/mock_robot` 아래 `body`, `wheel_left`, `wheel_right`를 찾는다. defaultPrim은 `/mock_robot`이다. 자산 내부를 본인에게 의미 있는 이름으로 정리하는 것이 재사용의 시작이다.
3. `assembly.usda`를 연다. `/World/RobotA`와 `/World/RobotB`가 같은 `robot.usda`를 reference하면서 다른 위치에 놓인다. 환경 PhysicsScene이 각 로봇 밑에 복제되지 않는지 확인한다.
4. RobotB의 body에는 현재 assembly layer에서 파란색 override를 작성한다. 원본 robot 파일을 편집하지 않아도 참조 위에 더 강한 의견을 쓸 수 있다. `robot.usda`를 따로 열어 원본에 파란색이 저장되지 않았음을 확인한다.
5. `flattened.usda`와 assembly의 Prim 목록을 `composition.json`에서 비교한다. Flatten은 참조/레이어의 합성 결과를 평탄화한다. **메시들을 하나의 메시로 병합하는 기능은 아니다.** 원문 설명의 표현과 구분해야 한다.
6. 파일을 옮길 때는 `assembly.usda`와 참조 `robot.usda`를 함께 옮긴다. 이 패키지는 외부 텍스처가 없지만 실제 자산에서는 texture/MDL 종속성도 남을 수 있다.

## GUI로 동일한 구조 만들기

1. 새 GUI에서 **File > New**를 선택한다. **Create > Xform**으로 `mock_robot`을 만들고 Cube와 Cylinder 두 개를 그 아래로 드래그한다. 각각 `body`, `wheel_left`, `wheel_right`로 바꾼다.
2. Property에서 body 한 변 0.6 m, 중심 Z=0.4 m, 바퀴 반지름 0.2 m·높이 0.1 m·축 Y·위치 Y=±0.4 m, Z=0.2 m로 맞춘다. 필요하면 Cube의 Size와 Scale을 함께 확인한다.
3. 지면/조명/PhysicsScene은 `/World` 아래에 둔다. 로봇이 World의 자식이면 로봇을 선택하고 **Edit > Unparent**로 루트 수준으로 옮긴다.
4. `mock_robot`을 우클릭해 **Set as a Default Prim**을 지정한다. **File > Save As**로 새 `.usda` 파일에 저장한다.
5. **File > New**, **File > Add Reference**로 방금 저장한 파일을 넣는다. 또는 Content에서 파일을 viewport로 드래그한다. 로봇만 들어오고 환경은 들어오지 않는지 확인한다.
6. defaultPrim을 World로 바꾼 원본 복사본을 만들어 참조 결과를 비교한다. 어떤 루트가 선택되는지 직접 확인한 후 원래 파일은 유지한다.
7. 실제 자산을 모으려면 저장한 USD를 Content에서 우클릭하고 **Collect Asset**을 사용한다. 폴더만 이동하기 전에 수집 경로와 결과 자산을 다시 열어 참조가 해결되는지 검사한다.

## 저장과 로딩 선택

`Open`은 Stage 자체를 편집한다. `Add Reference`는 현재 장면에 외부 자산을 합성하며 root layer의 override로 모습을 바꿀 수 있다. 참조 원본의 Prim을 현재 레이어에서 곧바로 삭제하는 것과 비활성화 의견을 쓰는 것은 다르다. `Save`는 해당 레이어를 저장하고, `Save As`는 새 이름을 사용한다. `Save Flattened As`는 합성된 장면을 저장하지만 텍스처 파일을 자동으로 전부 내장하지 않는다.

## 한 가지 변수 실험과 문제 해결

RobotB의 위치 X만 1.0에서 2.0으로 바꾸고 두 인스턴스가 독립 배치되는지 본다. 장면이 비어 보이면 자산 경로와 defaultPrim 존재를 확인한다. 로봇마다 빛/중력이 중복되면 환경이 defaultPrim의 자식인지 확인한다. 원본이 읽기 전용이어도 현재 작업 레이어에 override를 쓸 수 있다.

## 출처와 검증 범위

- NVIDIA Isaac Sim **5.1.0**, [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html): 이 패키지가 대응하는 공식 페이지. 문장과 실행 코드는 초심자용으로 재구성했다.
- 구현 API는 로컬 Isaac Sim 5.1 설치의 해당 `isaacsim`/Kit/USD 소스와 대조했다. 원문의 외부 최신 버전 링크는 5.1 설치와 UI/API가 다를 수 있다.

현재 확인한 실행 조건과 실제 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)에 기록했습니다. `tutorial.json`의 `partial_runtime_verified`는 그 조건에 한정된 검증이며, 다른 모드와 GUI·외부 통합 전체의 검증을 뜻하지 않습니다.
