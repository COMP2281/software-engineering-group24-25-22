from _typeshed import Incomplete
from celery import bootsteps

__all__ = ['Events']

class Events(bootsteps.StartStopStep):
    requires: Incomplete
    groups: Incomplete
    send_events: Incomplete
    enabled: Incomplete
    def __init__(self, c, task_events: bool = True, without_heartbeat: bool = False, without_gossip: bool = False, **kwargs) -> None: ...
    def start(self, c) -> None: ...
    def stop(self, c) -> None: ...
    def shutdown(self, c) -> None: ...
