from _typeshed import Incomplete

__all__ = ['PENDING', 'RECEIVED', 'STARTED', 'SUCCESS', 'FAILURE', 'REVOKED', 'RETRY', 'IGNORED', 'READY_STATES', 'UNREADY_STATES', 'EXCEPTION_STATES', 'PROPAGATE_STATES', 'precedence', 'state']

NONE_PRECEDENCE = PRECEDENCE_LOOKUP[None]

def precedence(state: str) -> int: ...

class state(str):
    def __gt__(self, other: str) -> bool: ...
    def __ge__(self, other: str) -> bool: ...
    def __lt__(self, other: str) -> bool: ...
    def __le__(self, other: str) -> bool: ...

PENDING: str
RECEIVED: str
STARTED: str
SUCCESS: str
FAILURE: str
REVOKED: str
RETRY: str
IGNORED: str
READY_STATES: Incomplete
UNREADY_STATES: Incomplete
EXCEPTION_STATES: Incomplete
PROPAGATE_STATES: Incomplete
