from _typeshed import Incomplete
from collections import deque
from typing import Any, Callable, Iterator, NamedTuple

__all__ = ['saferepr', 'reprstream']

class _literal(NamedTuple):
    value: Incomplete
    truncate: Incomplete
    direction: Incomplete

class _key(NamedTuple):
    value: Incomplete

class _quoted(NamedTuple):
    value: Incomplete

class _dirty(NamedTuple):
    objid: Incomplete

def saferepr(o: Any, maxlen: int = None, maxlevels: int = 3, seen: set = None) -> str: ...
def reprstream(stack: deque, seen: set | None = None, maxlevels: int = 3, level: int = 0, isinstance: Callable = ...) -> Iterator[Any]: ...
