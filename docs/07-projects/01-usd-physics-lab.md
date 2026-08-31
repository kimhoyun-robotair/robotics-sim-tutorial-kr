# 프로젝트 1: 재현 가능한 USD 물리 실험실

## 목표

GUI에서 만든 scene을 USD layer로 분리하고, 같은 scene을 standalone Python으로 headless 실행해 물리 결과를 검증하다. USD가 단순 mesh container가 아니라 scene composition과 simulation configuration을 함께 다루는 기반임을 확인하다.

## 요구사항

- ground plane, 서로 다른 질량의 dynamic cube 세 개, static obstacle, light, camera를 포함하다.
- geometry, physics override, experiment session을 최소 세 layer로 나누다.
- 240 physics step 뒤 cube가 유효한 위치에 있고 서로 폭발적으로 튀지 않았음을 자동 검증하다.
- stage unit, up axis, timeCodesPerSecond를 README에 기록하다.

## 1단계: layer 설계를 먼저 하다

```text
lab_root.usda
  subLayers = [
    @layers/geometry.usda@,
    @layers/physics.usda@,
    @layers/overrides.usda@
  ]
```

geometry layer는 prim hierarchy와 shape를, physics layer는 mass·collision·material을, overrides layer는 초기 pose와 실험 조건을 author하다. 여기서 `overrides.usda`는 파일로 저장하는 일반 sublayer이며, USD stage가 별도로 가질 수 있는 익명 session layer와 다르다. Layer panel에서 edit target을 바꿀 때 현재 layer를 항상 확인하다.

## 2단계: GUI smoke test

1. 새 stage에 Physics Scene과 ground를 만들다.
2. cube를 세 개 만들고 Rigid Body, Collider, Mass API를 적용하다.
3. cube가 서로 겹치지 않게 배치하고 timeline을 2초 실행하다.
4. collision shape visualization과 Physics Inspector로 collider를 확인하다.
5. 각 layer를 저장하고 application을 재시작한 뒤 root stage만 열어 동일하게 보이는지 확인하다.

## 3단계: headless 검증 script

```python
from isaacsim import SimulationApp

app = SimulationApp({"headless": True, "disable_viewport_updates": True})
try:
    from isaacsim.core.api import World
    from isaacsim.core.utils.stage import open_stage
    from pxr import UsdGeom

    if not open_stage("/absolute/path/to/lab_root.usda"):
        raise RuntimeError("stage를 열지 못했다")
    world = World(stage_units_in_meters=1.0)
    world.reset()
    for _ in range(240):
        world.step(render=False)

    stage = world.stage
    for path in ("/World/Cubes/CubeA", "/World/Cubes/CubeB", "/World/Cubes/CubeC"):
        prim = stage.GetPrimAtPath(path)
        assert prim.IsValid(), path
        xyz = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0).ExtractTranslation()
        assert all(abs(v) < 100.0 for v in xyz), (path, xyz)
        assert xyz[2] >= -0.05, (path, xyz)
finally:
    app.close()
```

동기 `open_stage`는 성공 여부를 `bool`로 반환하다. 다만 reference나 texture가 streaming되는 stage는 추가 resource가 아직 loading 중일 수 있으므로, 그런 asset을 사용하면 5.1 예제처럼 app update loop에서 loading 상태가 끝날 때까지 기다린 뒤 physics를 시작하다.

## 완료 조건

```bash
"$ISAACSIM_PATH/python.sh" project-1/tests/test_stage.py
```

- 종료 code가 0이다.
- root layer를 다른 디렉터리로 복사해도 상대 asset path가 해석되다.
- 어떤 layer를 mute하면 무엇이 사라지는지 README에서 설명하다.
- mass를 10배 바꾼 실험과 friction을 바꾼 실험의 결과를 `metrics.json`에 비교하다.

## 확장 과제

variant set으로 `low_friction`과 `high_friction` 실험을 전환하다. payload로 무거운 visual asset을 지연 load하고 headless physics만 실행할 때 load time 차이를 재다.

## 출처

- [Working with USD](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/intro_to_usd.html)
- [Physics Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/simulation_fundamentals.html)
- [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)
- [Hello World](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core_api_tutorials/tutorial_core_hello_world.html)
