from _typeshed import Incomplete
from collections.abc import Generator
from typing import NamedTuple

__all__ = ['Option', 'NAMESPACES', 'flatten', 'find']

class searchresult(NamedTuple):
    namespace: Incomplete
    key: Incomplete
    type: Incomplete

class Option:
    alt: Incomplete
    deprecate_by: Incomplete
    remove_by: Incomplete
    old: Incomplete
    typemap: Incomplete
    default: Incomplete
    type: Incomplete
    def __init__(self, default: Incomplete | None = None, *args, **kwargs) -> None: ...
    def to_python(self, value): ...

NAMESPACES: Incomplete

def flatten(d, root: str = '', keyfilter=...) -> Generator[Incomplete, Incomplete]: ...
def find(name, namespace: str = 'celery'): ...
