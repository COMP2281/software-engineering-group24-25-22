from _typeshed import Incomplete

__all__ = ['EventDispatcher']

class EventDispatcher:
    DISABLED_TRANSPORTS: Incomplete
    app: Incomplete
    on_enabled: Incomplete
    on_disabled: Incomplete
    connection: Incomplete
    channel: Incomplete
    hostname: Incomplete
    buffer_while_offline: Incomplete
    buffer_group: Incomplete
    buffer_limit: Incomplete
    on_send_buffered: Incomplete
    mutex: Incomplete
    producer: Incomplete
    serializer: Incomplete
    groups: Incomplete
    tzoffset: Incomplete
    clock: Incomplete
    delivery_mode: Incomplete
    enabled: Incomplete
    exchange: Incomplete
    headers: Incomplete
    pid: Incomplete
    def __init__(self, connection: Incomplete | None = None, hostname: Incomplete | None = None, enabled: bool = True, channel: Incomplete | None = None, buffer_while_offline: bool = True, app: Incomplete | None = None, serializer: Incomplete | None = None, groups: Incomplete | None = None, delivery_mode: int = 1, buffer_group: Incomplete | None = None, buffer_limit: int = 24, on_send_buffered: Incomplete | None = None) -> None: ...
    def __enter__(self): ...
    def __exit__(self, *exc_info) -> None: ...
    def enable(self) -> None: ...
    def disable(self) -> None: ...
    def publish(self, type, fields, producer, blind: bool = False, Event=..., **kwargs): ...
    def send(self, type, blind: bool = False, utcoffset=..., retry: bool = False, retry_policy: Incomplete | None = None, Event=..., **fields): ...
    def flush(self, errors: bool = True, groups: bool = True) -> None: ...
    def extend_buffer(self, other) -> None: ...
    def close(self) -> None: ...
    publisher: Incomplete
