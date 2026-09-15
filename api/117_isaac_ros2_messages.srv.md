# isaac_ros2_messages.srv

첫 등장: [128번 튜토리얼](../src/128_ros2_ros2_prim_service/TUTORIAL.md) · [attribute_client.py:12](../src/128_ros2_ros2_prim_service/attribute_client.py#L12)

`isaac_ros2_messages.srv`는 Isaac Sim의 Prim 속성 서비스에 사용하는 요청·응답 타입이다.

- `GetPrimAttribute.Request(path=..., attribute=...)`: `/World/Cube`의 `xformOp:translate` 값을 조회한다.
- `SetPrimAttribute.Request(...)`: 바꿀 위치를 JSON 문자열인 `value`로 전달한다.
- 응답의 `success`와 `message`를 확인하고, 속성을 다시 읽어 요청한 위치와 일치하는지 검증한다.

[전체 API 색인](INDEX.md) · [튜토리얼별 사용 목록](TUTORIAL_INDEX.md)

## 공식 문서

- [Isaac Sim 5.1 Prim 속성 서비스 메시지 정의](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/ros2_tutorials/tutorial_ros2_prim_service.html#service-message-types)
