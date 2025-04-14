from .base import BaseLoader

__all__ = ['Loader', 'DEFAULT_CONFIG_MODULE']

DEFAULT_CONFIG_MODULE: str

class Loader(BaseLoader):
    def setup_settings(self, settingsdict): ...
    configured: bool
    def read_configuration(self, fail_silently: bool = True): ...
