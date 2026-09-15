# isaacsim.replicator.behavior.behaviors

첫 등장: [141번 튜토리얼](../src/141_replicator_replicator_modular_scripting/TUTORIAL.md) · [run.py:40](../src/141_replicator_replicator_modular_scripting/run.py#L40)

Prim에 붙여 장면 속성을 바꾸거나 대상을 바라보게 하는 Replicator behavior 클래스 모음이다.

- `LocationRandomizer`, `RotationRandomizer`, `TextureRandomizer`로 물체의 위치·회전·텍스처를 바꾼다.
- `LightRandomizer`로 조명 세기를 바꾸고, `LookAtBehavior`로 카메라가 지정 대상을 바라보게 한다.
- `VolumeStackRandomizer`는 상자를 쌓는 선택 실행에 사용하며, 입력·출력 이벤트로 진행 상태를 주고받는다.
- 각 클래스의 `BEHAVIOR_NS`를 이용해 `exposedVar:` USD 속성 이름을 만들고 실행 간격과 범위를 설정한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 Behavior 확장 문서](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.replicator.behavior/docs/index.html)
- [공식 Modular Behavior Scripting — 실제 클래스 사용 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_modular_scripting.html)
