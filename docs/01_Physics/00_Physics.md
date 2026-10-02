# Physics
Isaac Sim 시뮬레이션을 돌려보면, High-level에서는 Omniverse Physics work는 다음과 같이 돌아가고 있다.
- The USD Physics schema of robot and environment assets are parsed and corresponding objects are created in the PhysX SDK Backend.
- Then, for each discrete-time step of the simulation, Physics advances the PhysX SDK objects given their current state and additional inputs such as, for example, control-policy torques.
- The updated state is written back to USD by default, where the state can be further processed by the user, a reinforcement-learning policy, or other extensions such as Omniverse RTX Renderer.
- Omniverse Physics propagates runtime changes to physics parameters in USD to the PhysX SDK objects.
