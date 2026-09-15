# isaacsim.cortex.framework.motion_commander

첫 등장: [98번 튜토리얼](../src/98_digital_twin_cortex_1_overview/TUTORIAL.md) · [run.py:50](../src/98_digital_twin_cortex_1_overview/run.py#L50)

`motion_commander`의 자료형은 Cortex 로봇 팔에 전달할 이동 목표를 표현합니다. 튜토리얼에서는 Peck 동작과 블록·상자 집기의 목표를 만드는 데 사용합니다.

- `PosePq`: 목표 위치와 쿼터니언을 묶으며, `to_T()`로 변환 행렬을 얻습니다.
- `ApproachParams`: 목표에 접근할 방향과 접근 조건의 `std_dev`를 지정합니다.
- `MotionCommand`: 목표 자세, 접근 조건, 관절 자세 기준인 `posture_config` 등을 묶어 팔에 전달합니다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 — isaacsim.cortex.framework](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.cortex.framework/docs/index.html)
