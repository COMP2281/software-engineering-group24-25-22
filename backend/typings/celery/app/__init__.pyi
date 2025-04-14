from .base import Celery as Celery
from .utils import AppPickler as AppPickler
from _typeshed import Incomplete
from celery._state import app_or_default as app_or_default, disable_trace as disable_trace, enable_trace as enable_trace, pop_current_task as pop_current_task, push_current_task as push_current_task

__all__ = ['Celery', 'AppPickler', 'app_or_default', 'default_app', 'bugreport', 'enable_trace', 'disable_trace', 'shared_task', 'push_current_task', 'pop_current_task']

default_app: Incomplete

def bugreport(app: Incomplete | None = None): ...
def shared_task(*args, **kwargs): ...
