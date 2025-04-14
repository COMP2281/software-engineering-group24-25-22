from celery.bin.base import CeleryCommand as CeleryCommand, CeleryOption as CeleryOption, handle_preload_options as handle_preload_options
from celery.contrib.migrate import migrate_tasks as migrate_tasks

def migrate(ctx, source, destination, **kwargs) -> None: ...
