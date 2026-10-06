# Physics Simulation Fundamentals
## Physics in USD Schema
우리는 이미 이전 강의에서, **Schema란 USD의 데이터 구조와 해석 규칙을 규정해놓은 것**이라고 학습을 했다. 이 중에서 [**USD Physics Schema**](https://openusd.org/release/api/usd_physics_page_front.html) 같은 경우, USD의 여러 Schema 중에서 물리법칙과 관련된 Schema들을 지정해놓으며, 일반적으로 **UsdPhysics** API를 사용해서 활용이 되는 타입들이다. 한편, 엔비디아에서 PhysX 엔진을 개발하면서 기존 USD Physics Schema에 더해서 PhysX 엔진에 특화되도록 Schema를 확장할 필요가 있었고, 그에 따라서 개발된 **PhysX Schemas**가 있다. 이런 Schema들 같은 경우 기본적으로 C++을 통한 Access 방식을 취하지만, 파이썬 API로도 개발이 되어서 파이썬에서도 쉽게 접근할 수 있다. 예를 들어서:
```
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
import omni.usd

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/Path/To/Prim")
physics_api_prim = UsdPhysics.SomePhysicsAPI(prim)
physx_api_prim = PhysxSchema.AnotherPhysxAPI(prim)

# Check if the API is Applied, if not, Apply it.
if not physics_api_prim:
    physics_api_prim = UsdPhysics.SomePhysicsAPI.Apply(prim)

physics_attr = physics_api_prim.GetSomePhysicsAttr()
physx_attr = physx_api_prim.GetPhysxAttr()

# Check if Attribute is authored, otherwise create it
if not physics_attr:
    physics_attr = physics_api_prim.CreateSomePhysicsAttr(1.0)
print(physics_attr.Get())
physics_attr.Set(10.0)
```

## Simulation Timeline
통상적으로 시뮬레이션 시간과 실제 시간(real time)은 당연히 다르다. 시스템 설정과, 시뮬레이션 환경의 크기(그리고 그거에 드는 리소스에 따라) 각 time step을 계산하는데 걸리는 실제 시간은 그 time step이 나타내는 시뮬레이션 시간보다 더 짧을 수도, 더 길 수도 있다. 따라서 시뮬레잇녀 결과를 순서대로 그대로 보여주게 된다면 실제보다 더 빠르거나, 혹은 더 느리게 재생될수도 있다. 이러한 문제를 방지하기 위해서 Isaac Sim 내부에는 기본적으로 시뮬레ㅣ션 속도를 실제 시간과 맞추기 위한 **Limiter**를 사용하도록 설정이 되어있다.  
  
그리고 시뮬레이션은 당연히 렌더링보다 더 빠른 주기로 실행이 될 수 있다 (화면이 한 프레임 렌더링 되는 동안, 백그라운드에서는 여러 번의 Physics simulation time step이 돌아갈 수 있다는 뜻).  
아래 예시는 물리 시뮬레이션은 초당 120 step으로 설정되어 있고, 렌더링은 초당 60 frame인 예제이다. 따라서 렌더링 프레임 하나당 물리 시뮬레이션이 2번 수행된다.
![alt text](../00_asset/07_Physics/SimulationTimeline.png)
- Physics simulation : 120 step/s
- Rendering : 60 frames/s
- 결과 : 2 physics step / 1 rendered frame
이상적인 경우라면 simulation frequency와 rendering frequency가 서로 같거나, 정수배 관계를 가지는 것이 좋다.  
  
이렇듯 Isaac Sim의 Timeline에는 여러 종류의 event stream이 존재하며, 그 중에서 가장 중요하게 취급되는 것들을 사용자는 쉽게 subscribe해서 이벤트를 확인할 수 있다.
- Simulation Events
- Frame Update Events
  - pre-render
  - post-render
Omnigraph Node의 경우 일반적으로 **pre-render event**가 발생할 때 업데이트가 이루어진다. 다만 필요하다면, Omnigraph node가 다른 종류의 event에서도 업데이트 되도록 설정할 수 있ㄷ. 예를 들어서 화면이 렌더링 될때가 아니라 Physics simulation step마다 업데이트를 한다거나.

### Configuring Frame Rate
시뮬레이션의 Rendering Frame Rate는 현재 Stage의 메타데이터를 조정해서 설정할 수 있다. Isaac Sim GUI에서의 경우, **Layer** 탭의 **Root Layer**를 선택한 다음에 **Properties** 패널에서 **Timecodes per second** 속성을 수정하면 된다 (이거 동작 원리를 정확히 이해하지 못했다면 USD에 대해서 다시 공부를 하고 오길 추천한다).
![alt text](../00_asset/07_Physics/ConfigFrameRate.png)

### Configuring Simulation Timesteps
**Simulation Steps per Second** 값은 **Physics Scene**에서 결정이 된다. 현재 Stage 내부에 Physics Scene이 존재하지 않는다면, 기본값으로 초당 60 step이 사용이 된다. 만약 사용자가 Simulation Scene 요소를 추가하고 싶다면 다음과 같은 절차를 따르면 된다.
1. Create > Physics > Simulation Scene을 클릭
2. 생성된 Simulation Scene을 선택
3. Properties 패널에서 Simulation Steps per Second 항목을 확인
![alt text](../00_asset/07_Physics/ConfigureSimulationTimesteop.png)

## Simulation Components
