from .models import Task, TaskSet
from _typeshed import Incomplete
from celery.backends.base import BaseBackend

__all__ = ['DatabaseBackend']

class DatabaseBackend(BaseBackend):
    subpolling_interval: float
    task_cls = Task
    taskset_cls = TaskSet
    url: Incomplete
    engine_options: Incomplete
    short_lived_sessions: Incomplete
    def __init__(self, dburi: Incomplete | None = None, engine_options: Incomplete | None = None, url: Incomplete | None = None, **kwargs) -> None: ...
    @property
    def extended_result(self): ...
    def ResultSession(self, session_manager=...): ...
    def cleanup(self) -> None: ...
    def __reduce__(self, args=(), kwargs: Incomplete | None = None): ...
