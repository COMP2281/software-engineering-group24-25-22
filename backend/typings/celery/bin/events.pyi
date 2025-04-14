from celery.bin.base import CeleryDaemonCommand as CeleryDaemonCommand, CeleryOption as CeleryOption, LOG_LEVEL as LOG_LEVEL, handle_preload_options as handle_preload_options
from celery.platforms import detached as detached, set_process_title as set_process_title, strargv as strargv

def events(ctx, dump, camera, detach, frequency, maxrate, loglevel, **kwargs): ...
