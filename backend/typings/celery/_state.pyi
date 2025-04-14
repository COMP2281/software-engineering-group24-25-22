import threading
from _typeshed import Incomplete

__all__ = ['set_default_app', 'get_current_app', 'get_current_task', 'get_current_worker_task', 'current_app', 'current_task', 'connect_on_app_finalize']

def connect_on_app_finalize(callback): ...

class _TLS(threading.local):
    current_app: Incomplete

def set_default_app(app) -> None: ...
def get_current_app() -> None: ...

get_current_app: Incomplete

def get_current_task(): ...
def get_current_worker_task(): ...

current_app: Incomplete
current_task: Incomplete
