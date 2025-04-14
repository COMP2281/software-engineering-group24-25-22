from celery.exceptions import Ignore as Ignore, Retry as Retry
from celery.utils.time import get_exponential_backoff_interval as get_exponential_backoff_interval

def add_autoretry_behaviour(task, **options): ...
