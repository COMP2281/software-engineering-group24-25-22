from .base import KeyValueStoreBackend
from _typeshed import Incomplete

__all__ = ['S3Backend']

class S3Backend(KeyValueStoreBackend):
    endpoint_url: Incomplete
    aws_region: Incomplete
    aws_access_key_id: Incomplete
    aws_secret_access_key: Incomplete
    bucket_name: Incomplete
    base_path: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def get(self, key): ...
    def set(self, key, value) -> None: ...
    def delete(self, key) -> None: ...
