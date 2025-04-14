from _typeshed import Incomplete
from collections import UserDict
from typing import NamedTuple

__all__ = ['Panel']

class controller_info_t(NamedTuple):
    alias: Incomplete
    type: Incomplete
    visible: Incomplete
    default_timeout: Incomplete
    help: Incomplete
    signature: Incomplete
    args: Incomplete
    variadic: Incomplete

class Panel(UserDict):
    data: Incomplete
    meta: Incomplete
    @classmethod
    def register(cls, *args, **kwargs): ...
