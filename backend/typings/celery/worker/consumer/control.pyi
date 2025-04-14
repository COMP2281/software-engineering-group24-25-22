from _typeshed import Incomplete
from celery import bootsteps

__all__ = ['Control']

class Control(bootsteps.StartStopStep):
    requires: Incomplete
    is_green: Incomplete
    box: Incomplete
    start: Incomplete
    stop: Incomplete
    shutdown: Incomplete
    def __init__(self, c, **kwargs) -> None: ...
    def include_if(self, c): ...
