from _typeshed import Incomplete
from collections import defaultdict
from typing import Mapping
from weakref import WeakSet

__all__ = ['Worker', 'Task', 'State', 'heartbeat_expires']

class CallableDefaultdict(defaultdict):
    fun: Incomplete
    def __init__(self, fun, *args, **kwargs) -> None: ...
    def __call__(self, *args, **kwargs): ...

def heartbeat_expires(timestamp, freq: int = 60, expire_window=..., Decimal=..., float=..., isinstance=...): ...

class Worker:
    heartbeat_max: int
    expire_window = HEARTBEAT_EXPIRE_WINDOW
    hostname: Incomplete
    pid: Incomplete
    freq: Incomplete
    heartbeats: Incomplete
    clock: Incomplete
    active: Incomplete
    processed: Incomplete
    loadavg: Incomplete
    sw_ident: Incomplete
    sw_ver: Incomplete
    sw_sys: Incomplete
    event: Incomplete
    def __init__(self, hostname: Incomplete | None = None, pid: Incomplete | None = None, freq: int = 60, heartbeats: Incomplete | None = None, clock: int = 0, active: Incomplete | None = None, processed: Incomplete | None = None, loadavg: Incomplete | None = None, sw_ident: Incomplete | None = None, sw_ver: Incomplete | None = None, sw_sys: Incomplete | None = None) -> None: ...
    def __reduce__(self): ...
    def update(self, f, **kw) -> None: ...
    @property
    def status_string(self): ...
    @property
    def heartbeat_expires(self): ...
    @property
    def alive(self, nowfun=...): ...
    @property
    def id(self): ...

class Task:
    name: Incomplete
    received: Incomplete
    sent: Incomplete
    started: Incomplete
    succeeded: Incomplete
    failed: Incomplete
    retried: Incomplete
    revoked: Incomplete
    rejected: Incomplete
    args: Incomplete
    kwargs: Incomplete
    eta: Incomplete
    expires: Incomplete
    retries: Incomplete
    worker: Incomplete
    result: Incomplete
    exception: Incomplete
    timestamp: Incomplete
    runtime: Incomplete
    traceback: Incomplete
    exchange: Incomplete
    routing_key: Incomplete
    root_id: Incomplete
    parent_id: Incomplete
    client: Incomplete
    state: Incomplete
    clock: int
    merge_rules: Incomplete
    uuid: Incomplete
    cluster_state: Incomplete
    children: Incomplete
    def __init__(self, uuid: Incomplete | None = None, cluster_state: Incomplete | None = None, children: Incomplete | None = None, **kwargs) -> None: ...
    def event(self, type_, timestamp: Incomplete | None = None, local_received: Incomplete | None = None, fields: Incomplete | None = None, precedence=..., setattr=..., task_event_to_state=..., RETRY=...) -> None: ...
    def info(self, fields: Incomplete | None = None, extra: Incomplete | None = None): ...
    def as_dict(self): ...
    def __reduce__(self): ...
    @property
    def id(self): ...
    @property
    def origin(self): ...
    @property
    def ready(self): ...
    def parent(self): ...
    def root(self): ...

class State:
    Worker = Worker
    Task = Task
    event_count: int
    task_count: int
    heap_multiplier: int
    event_callback: Incomplete
    workers: Incomplete
    tasks: Incomplete
    max_workers_in_memory: Incomplete
    max_tasks_in_memory: Incomplete
    on_node_join: Incomplete
    on_node_leave: Incomplete
    handlers: Incomplete
    tasks_by_type: Mapping[str, WeakSet[Task]]
    tasks_by_worker: Mapping[str, WeakSet[Task]]
    def __init__(self, callback: Incomplete | None = None, workers: Incomplete | None = None, tasks: Incomplete | None = None, taskheap: Incomplete | None = None, max_workers_in_memory: int = 5000, max_tasks_in_memory: int = 10000, on_node_join: Incomplete | None = None, on_node_leave: Incomplete | None = None, tasks_by_type: Incomplete | None = None, tasks_by_worker: Incomplete | None = None) -> None: ...
    def freeze_while(self, fun, *args, **kwargs): ...
    def clear_tasks(self, ready: bool = True): ...
    def clear(self, ready: bool = True): ...
    def get_or_create_worker(self, hostname, **kwargs): ...
    def get_or_create_task(self, uuid): ...
    def event(self, event): ...
    def task_event(self, type_, fields): ...
    def worker_event(self, type_, fields): ...
    def rebuild_taskheap(self, timetuple=...) -> None: ...
    def itertasks(self, limit: int | None = None): ...
    def tasks_by_time(self, limit: Incomplete | None = None, reverse: bool = True): ...
    tasks_by_timestamp = tasks_by_time
    def task_types(self): ...
    def alive_workers(self): ...
    def __reduce__(self): ...
