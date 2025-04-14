from _typeshed import Incomplete
from celery import VERSION_BANNER as VERSION_BANNER
from celery.app.utils import find_app as find_app
from celery.bin.amqp import amqp as amqp
from celery.bin.base import CLIContext as CLIContext, CeleryCommand as CeleryCommand, CeleryOption as CeleryOption
from celery.bin.beat import beat as beat
from celery.bin.call import call as call
from celery.bin.control import control as control, inspect as inspect, status as status
from celery.bin.events import events as events
from celery.bin.graph import graph as graph
from celery.bin.list import list_ as list_
from celery.bin.logtool import logtool as logtool
from celery.bin.migrate import migrate as migrate
from celery.bin.multi import multi as multi
from celery.bin.purge import purge as purge
from celery.bin.result import result as result
from celery.bin.shell import shell as shell
from celery.bin.upgrade import upgrade as upgrade
from celery.bin.worker import worker as worker
from click.types import ParamType

UNABLE_TO_LOAD_APP_MODULE_NOT_FOUND: Incomplete
UNABLE_TO_LOAD_APP_ERROR_OCCURRED: Incomplete
UNABLE_TO_LOAD_APP_APP_MISSING: Incomplete

class App(ParamType):
    name: str
    def convert(self, value, param, ctx): ...

APP: Incomplete

def celery(ctx, app, broker, result_backend, loader, config, workdir, no_color, quiet, version, skip_checks) -> None: ...
def report(ctx, **kwargs) -> None: ...

previous_show_implementation: Incomplete
WRONG_APP_OPTION_USAGE_MESSAGE: str

def main() -> int: ...
