# isaacsim.core.api.tasks

첫 등장: [24번 튜토리얼](../src/24_core_core_adding_manipulator/TUTORIAL.md) · [pick_task.py:3](../src/24_core_core_adding_manipulator/pick_task.py#L3)

로봇과 물체 배치, 관측값, 매 스텝 처리 등을 작업 단위로 구성하는 BaseTask를 제공한다.

- `BaseTask`: 집기·이동·쌓기 작업을 구현할 때 상속한다.
- `set_up_scene()`: 지면, 로봇, 작업 대상 물체를 장면에 배치한다.
- `get_params()` / `get_observations()`: 객체 이름·설정과 제어에 필요한 현재 상태를 반환한다.
- `pre_step()` / `post_reset()`: 물리 스텝 전 상태를 확인하고 리셋 후 그리퍼·물체 상태를 초기화한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [BaseTask API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.api/docs/index.html#isaacsim.core.api.tasks.BaseTask)
