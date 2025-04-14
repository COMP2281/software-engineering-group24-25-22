from .base import KeyValueStoreBackend
from _typeshed import Incomplete

__all__ = ['CouchbaseBackend']

class CouchbaseBackend(KeyValueStoreBackend):
    bucket: str
    host: str
    port: int
    username: Incomplete
    password: Incomplete
    quiet: bool
    supports_autoexpire: bool
    timeout: float
    key_t = str
    url: Incomplete
    def __init__(self, url: Incomplete | None = None, *args, **kwargs) -> None: ...
    @property
    def connection(self): ...
    def get(self, key): ...
    def set(self, key, value) -> None: ...
    def mget(self, keys): ...
    def delete(self, key) -> None: ...
