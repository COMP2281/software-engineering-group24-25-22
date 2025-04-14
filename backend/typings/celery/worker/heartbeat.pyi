from _typeshed import Incomplete

__all__ = ['Heart']

class Heart:
    timer: Incomplete
    eventer: Incomplete
    interval: Incomplete
    tref: Incomplete
    def __init__(self, timer, eventer, interval: Incomplete | None = None) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
