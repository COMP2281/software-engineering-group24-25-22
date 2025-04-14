from .base import BaseBackend
from _typeshed import Incomplete

__all__ = ['CassandraBackend']

class CassandraBackend(BaseBackend):
    servers: Incomplete
    bundle_path: Incomplete
    supports_autoexpire: bool
    port: Incomplete
    keyspace: Incomplete
    table: Incomplete
    cassandra_options: Incomplete
    cqlexpires: Incomplete
    read_consistency: Incomplete
    write_consistency: Incomplete
    auth_provider: Incomplete
    def __init__(self, servers: Incomplete | None = None, keyspace: Incomplete | None = None, table: Incomplete | None = None, entry_ttl: Incomplete | None = None, port: int = 9042, bundle_path: Incomplete | None = None, **kwargs) -> None: ...
    def as_uri(self, include_password: bool = True): ...
    def __reduce__(self, args=(), kwargs: Incomplete | None = None): ...
