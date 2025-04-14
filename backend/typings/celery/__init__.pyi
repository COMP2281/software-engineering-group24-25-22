from . import local as local
from _typeshed import Incomplete
from celery._state import current_app as current_app, current_task as current_task
from celery.app import shared_task as shared_task
from celery.app.base import Celery as Celery
from celery.app.task import Task as Task
from celery.app.utils import bugreport as bugreport
from celery.canvas import chain as chain, chord as chord, chunks as chunks, group as group, maybe_signature as maybe_signature, signature as signature, subtask as subtask, xmap as xmap, xstarmap as xstarmap
from celery.utils import uuid as uuid
from typing import NamedTuple

__all__ = ['__file__', 'uuid', 'shared_task', '__docformat__', 'subtask', 'VERSION', 'current_app', 'version_info_t', 'log', 'bugreport', 'xstarmap', 'VERSION_BANNER', 'registry', '__path__', 'maybe_signature', '__doc__', 'current_task', 'chunks', '__author__', 'xmap', 'Signature', '__homepage__', 'Celery', 'chain', '__version__', 'execute', 'maybe_patch_concurrency', 'local', '_find_option_with_arg', '__package__', 'SERIES', 'messaging', 'signature', 'version_info', 'chord', '__contact__', 'group', 'Task']

SERIES: str
__version__: str
__author__: str
__contact__: str
__homepage__: str
__docformat__: str
VERSION_BANNER: Incomplete

class version_info_t(NamedTuple):
    major: Incomplete
    minor: Incomplete
    micro: Incomplete
    releaselevel: Incomplete
    serial: Incomplete

VERSION: Incomplete

version_info: Incomplete

def _find_option_with_arg(argv, short_opts: Incomplete | None = None, long_opts: Incomplete | None = None): ...
def maybe_patch_concurrency(argv: Incomplete | None = None, short_opts: Incomplete | None = None, long_opts: Incomplete | None = None, patches: Incomplete | None = None) -> None: ...

# Names in __all__ with no definition:
#   Signature
#   __doc__
#   __file__
#   __package__
#   __path__
#   execute
#   log
#   messaging
#   registry
#   version_info_t
