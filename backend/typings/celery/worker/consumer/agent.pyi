from _typeshed import Incomplete
from celery import bootsteps

__all__ = ['Agent']

class Agent(bootsteps.StartStopStep):
    conditional: bool
    requires: Incomplete
    agent_cls: Incomplete
    def __init__(self, c, **kwargs) -> None: ...
    def create(self, c): ...
