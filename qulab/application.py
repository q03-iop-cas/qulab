# -*- coding: utf-8 -*-
from qulab.utils import _get_settings_from_script, _get_local_config_dir
import logging

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

class ReadOnlyDict():
    def __init__(self):
        self.__dict = {}

    def __getitem__(self, key):
        return self.__dict[key]

    def setItem(self, key, value):
        self.__dict[key] = value

    def __setitem__(self, key, value):
        return

class Application:
    __title__   = "Qulab Application"
    __version__ = 'v0.1'

    def __init__(self, argv=None, parameters=None, parent=None):
        self.argv = argv
        self.args_parameters = parameters
        self.parent = parent
        self.children = []
        self.prog_name = os.path.basename(self.argv[0])
        self._configs = _get_local_config_dir()

        self.instruments = {}
        self.parameters = []
        self.record_templates = {}
        self.plots = []

        self.P   = ReadOnlyDict()
        self.ins = ReadOnlyDict()
        self.local_ins_server = None
        self._sweeps = []
        self._settings = None

        self.__param = []

    def get_settings(self):
        if self._settings is None:
            self._settings = _get_settings_from_script(self.argv[0])
        return self._settings

    def open_instr(self, addr):
        pass

    def P(self, key):
        for p in self.__param:
            if p.name == key:
                return p.value
        if self.parent is not None:
            return self.parent.P(key)
        else:
            return None

    def set_P(self, key, value):
        for p in self.__param:
            if p.name == key:
                p.value = value
                return
        if self.parent is not None:
            self.parent.set_P(key, value)
