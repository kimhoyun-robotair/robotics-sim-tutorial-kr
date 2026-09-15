# 14. Omniverse Commands Tool Extension

권장 학습 순서 **14** · Python 실행 환경과 USD 기초 · 출처 ID `t169`

UI로 Cube를 생성·이동한 기록을 Python command로 복원한다. Commands 창이 UI 작업과 `omni.kit.commands` 호출 사이를 연결한다는 것을 실제 재생으로 확인한다.

## 준비

Isaac Sim **5.1.0** GUI와 지원 NVIDIA GPU가 필요하다. 이 폴더만 복사해서 사용하며 다른 로컬 패키지나 공통 모듈을 참조하지 않는다. 터미널에서 다음으로 실행한다. 설치 위치가 다르면 변수만 바꾼다.

```bash
export ISAAC_SIM_PATH="$HOME/isaacsim"
"$ISAAC_SIM_PATH/isaac-sim.sh"
```

Stage는 현재 USD 장면 전체이고 prim은 그 안의 `/World/Cube` 같은 경로로 식별하는 요소다. `File > New`는 새 장면을 여므로 보관할 작업은 먼저 저장한다. 이 패키지는 `asset/`, `docs/`, 저장소 README를 필요로 하지 않는다.

## 1. 기록

1. `File > New`로 새 Stage를 열고 `Window > Commands`를 연다. 메뉴가 없으면 Extensions에서 Commands 관련 UI 확장을 검색해 켠다.
2. **Clear History**를 눌러 기존 command 기록만 비운다. 이 버튼은 Stage의 물체를 삭제하는 기능이 아니다.
3. `Create > Shape > Cube`를 선택한다. Stage에서 생성 Cube를 선택하고 Property의 Translate X=`1`, Y=`0`, Z=`0.5`, Scale=`(0.5,0.5,0.5)`로 바꾼다.
4. Commands 목록에서 생성과 transform에 대응하는 command 이름/인자를 읽는다. Search commands는 실행 가능한 명령 검색이며 history 필터와 구분한다.

## 2. Python 재생

1. **Selected commands**로 Cube 생성과 transform 행만 선택하여 코드를 clipboard에 복사한다. **Top-level commands**는 전체 최상위 command를 복사하므로 중첩 command까지 중복 실행하지 않게 한다.
2. 이 패키지 `output/replay.py`라는 새 파일에 코드를 붙이고 저장한다. 실제 UI가 생성한 경로/행렬을 그대로 읽어본다.
3. 기록을 지우지 않은 채 **File > New**로 빈 Stage를 연다. `Window > Script Editor`에 복사 코드를 붙여 Run한다.
4. Cube prim, X=1/Z=0.5 위치와 Scale=0.5가 원래 UI 작업과 같은지 Property에서 확인한다.
5. Ctrl+Z로 마지막 transform을 undo하고 Ctrl+Y로 redo하여 command 기반 동작을 관찰한다.

## API와 한 변수 실험

`omni.kit.commands.execute("명령명", ...)`는 등록된 command를 실행하며 많은 command가 undo/redo 동작을 제공한다. 직접 `UsdGeom` attribute를 수정하는 코드와는 command history 처리 방식이 다를 수 있다. USD의 Transform은 위치/회전/스케일이며 생성 command는 prim path를 대상으로 한다.

한 변수 실험: 재생 코드의 **위치 X 인자만** 바꾼 사본을 새 Stage에서 실행하여 Cube 위치만 달라지는지 본다. 명령이 행렬로 기록되었다면 GUI에서 X만 다시 편집해 새 기록을 비교한다. 성공은 기록 복사 자체가 아니라 빈 Stage에서 같은 형상이 재현되는 것이다. `prim already exists`면 새 Stage에서 실행하고, 출력에 잡다한 command가 많으면 선택한 top-level 작업 범위를 줄인다.

## 검증 범위

제공된 Python/JSON/TOML의 문법과 5.1 설치 소스/API를 대조했다. GPU/Kit에서 화면과 동작은 아직 실행하지 않았으므로 manifest는 `verification: not_run`이다. 아래 성공 기준을 실제 실행 후 확인해야 한다.

## 출처

- [Isaac Sim 5.1 공식 원문](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/utilities/debugging/ext_omni_kit_commands.html).
