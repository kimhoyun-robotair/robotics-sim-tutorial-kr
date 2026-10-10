# Physics
> 출처 : [**Physics**](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/index.html)  
  
Isaac Sim 시뮬레이션을 돌려보면, High-level에서는 Omniverse Physics work는 다음과 같이 돌아가고 있다.
- The USD Physics schema of robot and environment assets are parsed and corresponding objects are created in the PhysX SDK Backend.
- Then, for each discrete-time step of the simulation, Physics advances the PhysX SDK objects given their current state and additional inputs such as, for example, control-policy torques.
- The updated state is written back to USD by default, where the state can be further processed by the user, a reinforcement-learning policy, or other extensions such as Omniverse RTX Renderer.
- Omniverse Physics propagates runtime changes to physics parameters in USD to the PhysX SDK objects.

쉽게 얘기하면 Isaac Sim 렌더러 뒤에서 PhysX 물리 연산 엔진이 돌아가면서 물리 시뮬레이션이 진행되는 것이라고 할 수 있다.