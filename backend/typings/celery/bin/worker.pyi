import click
from _typeshed import Incomplete
from celery import concurrency as concurrency
from celery.bin.base import COMMA_SEPARATED_LIST as COMMA_SEPARATED_LIST, CeleryDaemonCommand as CeleryDaemonCommand, CeleryOption as CeleryOption, LOG_LEVEL as LOG_LEVEL, handle_preload_options as handle_preload_options
from celery.concurrency.base import BasePool as BasePool
from celery.exceptions import SecurityError as SecurityError
from celery.platforms import EX_FAILURE as EX_FAILURE, EX_OK as EX_OK, detached as detached, maybe_drop_privileges as maybe_drop_privileges
from celery.utils.log import get_logger as get_logger
from celery.utils.nodenames import default_nodename as default_nodename, host_format as host_format, node_format as node_format
from click import ParamType
from click.types import StringParamType

logger: Incomplete

class CeleryBeat(ParamType):
    name: str
    def convert(self, value, param, ctx): ...

class WorkersPool(click.Choice):
    name: str
    def __init__(self) -> None: ...
    def convert(self, value, param, ctx): ...

class Hostname(StringParamType):
    name: str
    def convert(self, value, param, ctx): ...

class Autoscale(ParamType):
    name: str
    def convert(self, value, param, ctx): ...

CELERY_BEAT: Incomplete
WORKERS_POOL: Incomplete
HOSTNAME: Incomplete
AUTOSCALE: Incomplete
C_FAKEFORK: Incomplete

def detach(path, argv, logfile: Incomplete | None = None, pidfile: Incomplete | None = None, uid: Incomplete | None = None, gid: Incomplete | None = None, umask: Incomplete | None = None, workdir: Incomplete | None = None, fake: bool = False, app: Incomplete | None = None, executable: Incomplete | None = None, hostname: Incomplete | None = None): ...
def worker(ctx, hostname: Incomplete | None = None, pool_cls: Incomplete | None = None, app: Incomplete | None = None, uid: Incomplete | None = None, gid: Incomplete | None = None, loglevel: Incomplete | None = None, logfile: Incomplete | None = None, pidfile: Incomplete | None = None, statedb: Incomplete | None = None, **kwargs): ...
