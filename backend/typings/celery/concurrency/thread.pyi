from .base import BasePool
from _typeshed import Incomplete
from concurrent.futures import Future
from typing import Any, Callable, TypedDict

__all__ = ['TaskPool']

PoolInfo = TypedDict('PoolInfo', {'max-concurrency': int, 'threads': int})
TargetFunction = Callable[..., Any]

class ApplyResult:
    f: Incomplete
    get: Incomplete
    def __init__(self, future: Future) -> None: ...
    def wait(self, timeout: float | None = None) -> None: ...

class TaskPool(BasePool):
    limit: int
    body_can_be_buffer: bool
    signal_safe: bool
    executor: Incomplete
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def on_stop(self) -> None: ...
    def on_apply(self, target: TargetFunction, args: tuple[Any, ...] | None = None, kwargs: dict[str, Any] | None = None, callback: Callable[..., Any] | None = None, accept_callback: Callable[..., Any] | None = None, **_: Any) -> ApplyResult: ...
