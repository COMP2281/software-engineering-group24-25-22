from _typeshed import Incomplete
from celery import bootsteps

__all__ = ['Heart']

class Heart(bootsteps.StartStopStep):
    requires: Incomplete
    enabled: Incomplete
    heartbeat_interval: Incomplete
    def __init__(self, c, without_heartbeat: bool = False, heartbeat_interval: Incomplete | None = None, **kwargs) -> None: ...
    def start(self, c) -> None: ...
    def stop(self, c) -> None: ...
    shutdown = stop
