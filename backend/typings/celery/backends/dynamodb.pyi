from .base import KeyValueStoreBackend
from _typeshed import Incomplete
from typing import NamedTuple

__all__ = ['DynamoDBBackend']

class DynamoDBAttribute(NamedTuple):
    name: Incomplete
    data_type: Incomplete

class DynamoDBBackend(KeyValueStoreBackend):
    table_name: str
    read_capacity_units: int
    write_capacity_units: int
    aws_region: Incomplete
    endpoint_url: Incomplete
    time_to_live_seconds: Incomplete
    supports_autoexpire: bool
    implements_incr: bool
    url: Incomplete
    def __init__(self, url: Incomplete | None = None, table_name: Incomplete | None = None, *args, **kwargs) -> None: ...
    @property
    def client(self): ...
    def get(self, key): ...
    def set(self, key, value) -> None: ...
    def mget(self, keys): ...
    def delete(self, key) -> None: ...
    def incr(self, key: bytes) -> int: ...
