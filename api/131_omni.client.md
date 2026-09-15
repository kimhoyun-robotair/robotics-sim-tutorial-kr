# omni.client

첫 등장: [142번 튜토리얼](../src/142_replicator_replicator_amr_navigation/TUTORIAL.md) · [navigation.py:23](../src/142_replicator_replicator_amr_navigation/navigation.py#L23)

애셋 저장 위치의 파일 목록을 읽어 장면에 추가할 USD 파일을 찾는다.

- `list()`로 AMR 내비게이션 예제의 소품 폴더를 조회한다.
- `Result.OK`로 조회 성공을 확인하고, 결과 항목의 `relative_path`에서 USD 파일을 골라 사용한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 공식 실습](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/tutorial_replicator_amr_navigation.html)
- [omni.client API](https://docs.omniverse.nvidia.com/kit/docs/client_library/latest/docs/python.html#module-omni.client)
