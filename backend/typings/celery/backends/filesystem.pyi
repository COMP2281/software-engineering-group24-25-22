from _typeshed import Incomplete
from celery import uuid as uuid
from celery.backends.base import KeyValueStoreBackend as KeyValueStoreBackend
from celery.exceptions import ImproperlyConfigured as ImproperlyConfigured
from collections.abc import Generator

default_encoding: Incomplete
E_NO_PATH_SET: str
E_PATH_NON_CONFORMING_SCHEME: str
E_PATH_INVALID: str

class FilesystemBackend(KeyValueStoreBackend):
    url: Incomplete
    path: Incomplete
    sep: Incomplete
    open: Incomplete
    unlink: Incomplete
    def __init__(self, url: Incomplete | None = None, open=..., unlink=..., sep=..., encoding=..., *args, **kwargs) -> None: ...
    def __reduce__(self, args=(), kwargs: Incomplete | None = None): ...
    def get(self, key): ...
    def set(self, key, value) -> None: ...
    def mget(self, keys) -> Generator[Incomplete]: ...
    def delete(self, key) -> None: ...
    def cleanup(self) -> None: ...
