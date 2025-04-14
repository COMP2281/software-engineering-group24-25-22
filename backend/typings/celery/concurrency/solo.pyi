from .base import BasePool
from _typeshed import Incomplete

__all__ = ['TaskPool']

class TaskPool(BasePool):
    body_can_be_buffer: bool
    on_apply: Incomplete
    limit: int
    def __init__(self, *args, **kwargs) -> None: ...
