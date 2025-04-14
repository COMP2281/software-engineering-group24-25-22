from celery.bin.base import COMMA_SEPARATED_LIST as COMMA_SEPARATED_LIST, CeleryCommand as CeleryCommand, CeleryOption as CeleryOption, handle_preload_options as handle_preload_options
from celery.utils import text as text

def purge(ctx, force, queues, exclude_queues, **kwargs): ...
