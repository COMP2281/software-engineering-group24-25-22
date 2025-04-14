from _typeshed import Incomplete
from celery.bin.base import CeleryDaemonCommand as CeleryDaemonCommand, CeleryOption as CeleryOption, LOG_LEVEL as LOG_LEVEL, handle_preload_options as handle_preload_options
from celery.platforms import detached as detached, maybe_drop_privileges as maybe_drop_privileges

def beat(ctx, detach: bool = False, logfile: Incomplete | None = None, pidfile: Incomplete | None = None, uid: Incomplete | None = None, gid: Incomplete | None = None, umask: Incomplete | None = None, workdir: Incomplete | None = None, **kwargs): ...
