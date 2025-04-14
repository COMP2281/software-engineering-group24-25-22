from _typeshed import Incomplete
from celery import Celery, beat
from typing import Any

__all__ = ['Beat']

class Beat:
    Service: Incomplete
    app: Celery
    loglevel: Incomplete
    logfile: Incomplete
    schedule: Incomplete
    scheduler_cls: Incomplete
    redirect_stdouts: Incomplete
    redirect_stdouts_level: Incomplete
    quiet: Incomplete
    max_interval: Incomplete
    socket_timeout: Incomplete
    no_color: Incomplete
    colored: Incomplete
    pidfile: Incomplete
    def __init__(self, max_interval: int | None = None, app: Celery | None = None, socket_timeout: int = 30, pidfile: str | None = None, no_color: bool | None = None, loglevel: str = 'WARN', logfile: str | None = None, schedule: str | None = None, scheduler: str | None = None, scheduler_cls: str | None = None, redirect_stdouts: bool | None = None, redirect_stdouts_level: str | None = None, quiet: bool = False, **kwargs: Any) -> None: ...
    def run(self) -> None: ...
    def setup_logging(self, colorize: bool | None = None) -> None: ...
    def start_scheduler(self) -> None: ...
    def banner(self, service: beat.Service) -> str: ...
    def init_loader(self) -> None: ...
    def startup_info(self, service: beat.Service) -> str: ...
    def set_process_title(self) -> None: ...
    def install_sync_handler(self, service: beat.Service) -> None: ...
