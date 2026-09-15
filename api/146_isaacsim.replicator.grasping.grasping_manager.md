# isaacsim.replicator.grasping.grasping_manager

첫 등장: [168번 튜토리얼](../src/168_sdg_extra_replicator_grasping_sdg/TUTORIAL.md) · [run.py:39](../src/168_sdg_extra_replicator_grasping_sdg/run.py#L39)

`GraspingManager`는 물체를 잡을 후보 자세를 생성하고 물리 시뮬레이션으로 평가하는 클래스이다.

- `load_config()`로 YAML 설정을 읽고 대상 물체와 그리퍼 경로를 확인한다.
- `sampler_config`, `generate_grasp_poses()`, `get_grasp_poses()`로 후보 수를 지정하고 월드 좌표의 잡기 자세를 얻는다.
- `store_initial_gripper_pose()`로 초기 자세를 보관하고, `evaluate_grasp_poses()`로 후보를 비동기 평가한다.
- `set_results_output_dir()`, `set_overwrite_results_output()`으로 저장 위치를 정한다. 튜토리얼의 YAML 결과는 그리퍼 상태 기록이다.
- `clear()`로 관리자가 사용한 상태를 정리한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [공식 Grasping SDG — GraspingManager 코드 예제](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/synthetic_data_generation/tutorial_replicator_grasping_sdg.html#code-example)
