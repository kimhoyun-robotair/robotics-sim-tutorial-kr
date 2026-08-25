from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol


class LifecycleBoundary(Protocol):
    def current_state(self, node_name: str) -> int | None: ...

    def request_transition(self, node_name: str, transition_id: int) -> bool | None: ...

    def idle(self, seconds: float) -> None: ...


def reach_state(
    boundary: LifecycleBoundary,
    node_name: str,
    transition_id: int,
    target_state: int,
    deadline: float,
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    while clock() < deadline:
        if boundary.current_state(node_name) == target_state:
            return True
        boundary.request_transition(node_name, transition_id)
        if boundary.current_state(node_name) == target_state:
            return True
        boundary.idle(0.2)
    return False
