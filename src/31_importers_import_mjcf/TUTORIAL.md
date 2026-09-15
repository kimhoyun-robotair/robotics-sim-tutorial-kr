# 31. t113 · MJCF의 body/joint를 USD로 변환하기

권장 학습 순서 **31** · 로봇 자산 가져오기와 제작 · 출처 ID `t113`

Isaac Sim **5.1.0** MJCF importer를 사용해 실제 MJCF를 articulation으로 바꾼다. `pendulum.xml`은 이 패키지가 작성한 질량 0.3 kg의 한 관절 진자다. `--model ant`와 `humanoid`는 설치 extension의 공식 입력 파일을 직접 사용한다. 제어 정책을 추가하지 않으므로 Ant/Humanoid가 스스로 서거나 걷는 것은 기대 결과가 아니다.

## 이 실습의 의도

MJCF의 중첩 body와 hinge가 USD의 강체·joint 관계로 변환되는 과정을 한 관절 진자로 확인한다. 기본 입력은 높이 1 m의 mount를 고정하고 비스듬한 capsule을 연결해 관절 위치와 축을 쉽게 조사하도록 구성했다. 실행기는 모델을 가져와 물리를 진행하지만 별도 관절 목표나 보행 정책을 적용하지 않으므로, 이 실습의 핵심은 변환된 구조와 그 구조가 허용하는 운동을 확인하는 것이다.

## 실행 후 확인할 것

- **변환된 관절:** 기본 실행의 Stage에서 `/World/Imported`와 그 아래 `joints/hinge`를 찾는다. 종료 후 `report.json`의 `joints`에 hinge가 있어야 하며, local 모델의 world 고정 연결도 조사한다. 목록이 비어 있으면 실행기가 오류를 반환한다.
- **좌표와 단위:** `pendulum.xml`의 mount 위치 `(0,0,1)`, hinge의 Y축·범위 `-1.5..1.5 rad`를 USD Property와 대조한다. `report.json`의 `stage_meters_per_unit`은 `1.0`이어야 하며, USD 각도 표시가 degree인 경우 변환해서 비교한다.
- **진자의 움직임:** Play 중 고정 mount는 제자리에 있고 rod의 운동은 hinge 연결을 따라야 한다. 낙하·진동의 크기는 importer가 만든 drive와 damping에도 좌우되므로 특정 진폭·주기를 정답으로 두지 않는다.
- **모델별 해석:** `--model ant`와 `humanoid`는 고정하지 않은 base로 가져온다. 별도 제어가 없어 주저앉거나 넘어지는 것은 보행 실패 판정 대상이 아니며, joint 생성과 collider·링크 연결부터 확인한다.
- **결과의 범위:** `imported.usda`는 물리 루프 전 변환 장면, `report.json`은 joint 경로와 stage 단위 기록이다. joint 목록이 있다는 사실은 MuJoCo와 PhysX의 actuator·동역학 결과가 같다는 증거가 아니다.

## 준비와 실행

Isaac Sim 5.1, RTX GPU/드라이버, `isaacsim.asset.importer.mjcf`가 필요하다. 기본 fixture는 외부 mesh/ROS/MuJoCo 설치 없이 importer를 학습한다.

```bash
export ISAAC_SIM=/home/hoyunkim/isaacsim
cd src/31_importers_import_mjcf
"$ISAAC_SIM/python.sh" run.py --model local
"$ISAAC_SIM/python.sh" run.py --model ant --output output/ant
"$ISAAC_SIM/python.sh" run.py --model humanoid --output output/humanoid
```

`--steps`를 생략한 GUI 실행은 사용자가 창을 닫을 때까지 유지된다. `--steps 120`처럼 양수를 지정하면 해당 횟수 후 자동 종료하며, `--steps 0`도 GUI를 계속 유지한다. `--headless`에서 생략하면 기존 300회 한도를 사용한다. 실행 중에도 물리·제어가 계속 진행되며, 결과 요약은 실행을 마칠 때 기록한다.

새 출력 폴더에 `imported.usda`와 실제 joint prim 목록 `report.json`을 만든다. `--headless`도 가능하다. 모델이 로드되고 physics joint가 생성되지 않으면 오류를 반환한다. 이것은 XML→USD 변환 검사이며 동역학 동일성 인증은 아니다.

## 코드와 파일을 함께 읽기

1. `pendulum.xml`에서 `worldbody > body mount > body pendulum` 계층을 찾는다. MJCF는 중첩 body로 부모/자식 좌표계를 표현한다.
2. hinge axis는 Y이고 범위는 -1.5~1.5 rad다. `compiler angle="radian"`을 명시했다. capsule `fromto`는 두 끝점을 부모 body 기준으로 표현한다.
3. `MJCFCreateImportConfig`에서 local 진자만 `fix_base=True`로 가져온다. ant/humanoid는 움직이는 base다. `MJCFCreateAsset(mjcf_path, import_config, prim_path)`가 stage에 실제 물리 prim을 작성한다.
4. `World(stage_units_in_meters=1, physics_dt=0.01)`로 SI 단위를 일치시킨다. 중력은 m 단위에서 9.81 m/s²다. 원문 Script Editor 예제의 981.0은 cm 장면에 해당하는 수치이며 본 m 장면에 그대로 복사하지 않는다.
5. 기본 실행에서 진자가 지면 위 1 m mount에 연결되는지, collider와 hinge가 생성되는지 확인한다. importer가 생성한 drive에 따라 자유 낙하/진동이 달라질 수 있으므로 drive stiffness/damping도 조사한다.
6. 변수 하나: XML의 hinge damping만 0.1→0.5로 바꾸어 별도 출력으로 가져온다. joint 속도 감쇠와 importer의 drive 설정을 함께 관찰한다.

## 공식 GUI 절차

1. **Window > Extensions**에서 `isaacsim.asset.importer.mjcf` 활성화를 확인한다. AUTOLOAD 옆 폴더 아이콘을 열면 `data/mjcf/nv_humanoid.xml`, `nv_ant.xml`을 찾을 수 있다.
2. **File > Import**에서 humanoid XML을 선택한다. 출력 위치를 자신의 쓰기 가능한 폴더로 지정하고 movable base를 유지해 Import한다.
3. Stage의 robot prim과 ArticulationRootAPI를 확인한다. 지면은 **Create > Physics > Ground Plane**으로 추가하고 Play한다. viewport collider 표시로 보이는 mesh와 물리 형상을 구분한다.
4. 원문의 Python 예제는 `nv_ant.xml`을 가져온다. 이 패키지의 `--model ant`가 같은 native importer 경로를 사용한다. GUI를 humanoid로 시작했다는 이유로 둘을 같은 입력이라고 가정하지 않는다.

## 막힐 때와 확인 범위

MJCF가 File > Import 형식에 없으면 extension이 꺼져 있다. 외부 MJCF의 mesh가 빠지면 XML 기준 상대 경로/asset meshdir를 확인한다. 값이 100배 다르면 metersPerUnit과 distance/중력을 맞춘다. 파일을 가져왔다고 모든 MuJoCo solver/actuator 기능이 PhysX에서 동일하게 재현되는 것은 아니다. 아래 `RUNTIME_CHECK.md`는 local 모델의 headless 60 step 실행에서 hinge 생성과 단위를 확인한 기록이며, 진자 궤적의 정확성·Ant/Humanoid·GUI import를 검증한 기록은 아니다.

## 출처

[Isaac Sim 5.1 Import MJCF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_mjcf.html), [Python API 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_mjcf.html#importing-mjcf-using-python). 5.1 `isaacsim.asset.importer.mjcf/impl/commands.py`와 호출 인자를 대조했다.

## 실제 실행 기록

확인한 조건과 측정 결과는 [RUNTIME_CHECK.md](RUNTIME_CHECK.md)를 보세요. 검증은 해당 실행 모드에 한정됩니다.
