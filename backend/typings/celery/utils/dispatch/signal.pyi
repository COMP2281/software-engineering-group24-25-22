from _typeshed import Incomplete

__all__ = ['Signal']

class Signal:
    receivers: Incomplete
    providing_args: Incomplete
    lock: Incomplete
    use_caching: Incomplete
    name: Incomplete
    sender_receivers_cache: Incomplete
    def __init__(self, providing_args: Incomplete | None = None, use_caching: bool = False, name: Incomplete | None = None) -> None: ...
    def connect(self, *args, **kwargs): ...
    def disconnect(self, receiver: Incomplete | None = None, sender: Incomplete | None = None, weak: Incomplete | None = None, dispatch_uid: Incomplete | None = None): ...
    def has_listeners(self, sender: Incomplete | None = None): ...
    def send(self, sender, **named): ...
    send_robust = send
