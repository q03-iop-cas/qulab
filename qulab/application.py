# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 13:37:04 2015

@author: feihoo87
"""

import collections
from PyQt4 import QtCore, QtGui
import time
import os
import re
import inspect
import functools
from qulab.task import TaskManager
from qulab.data import DataManager
from qulab.plot import PlotManager
from qulab.config import config

inline_mod  = re.compile(r'^\s*(.*)#.*{{{setting}}}\s*$')
block_begin = re.compile(r'^(\s*)#{{{')
block_end   = re.compile(r'^(\s*)#}}}')

def __get_settings(fneme):
    settings = []
    in_setting_section = False
    indent = 0

    with open(fneme) as f:
        lines = f.readlines()
        for line in lines:
            if not in_setting_section:
                m = block_begin.search(line)
                if m != None:
                    in_setting_section = True
                    indent = len(m.group(1))
            elif in_setting_section:
                m = block_end.search(line)
                if m != None:
                    in_setting_section = False
                    indent = 0
                else:
                    settings.append(line[indent:])
            else:
                m = inline_mod.search(line)
                if m != None:
                    s = m.group(1)
                    settings.append(s.strip())

    return "".join(settings)

def __get_local_config_dir():
    appdata = os.getenv('LOCALAPPDATA')
    homepath = os.getenv('HOMEPATH')
    home = os.getenv('HOME')

    if appdata is not None:
        localdata_base = appdata
    elif homepath is not None:
        localdata_base = homepath
    elif home is not None:
        localdata_base = home
    else:
        localdata_base = '.'

    config_dir = os.path.join(localdata_base, 'QuLab')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

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
        self._configs = __get_local_config_dir()

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
            self._settings = __get_settings(self.argv[0])
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

    def sweep_channel(self, name, ranges, long_name='', unit='',
                      before=None, before_args=(),
                      after=None, after_args=()):
        def arbargs(func):
            @functools.wraps(func)
            def wrapper(**kwargs):
                argspec = inspect.getargspec(func)
                args = argspec.args
                defaults = () if argspec.defaults is None else argspec.defaults
                kw = {} if argspec.keywords is None else argspec.keywords
                for i in range(len(defaults)):
                    kw[args[i+len(args)-len(defaults)]] = defaults[i]
                for name in args:
                    if name in kwargs.keys():
                        kw[name] = kwargs[name]
                return func(**kw)
            return wrapper
        if isinstance(ranges, collections.Callable):
            _ranges = arbargs(ranges)
        else:
            _ranges = ranges
        long_name = name if long_name == '' else long_name
        before = arbargs(before) if before is not None else None
        after = arbargs(after) if after is not None else None
        self._sweeps.append(dict(name=name,
                                 ranges=_ranges,
                                 long_name=long_name,
                                 unit=unit,
                                 current=None,
                                 before=before,
                                 before_args=before_args,
                                 after=after,
                                 after_args=after_args))

    def get_sweep_by_name(self, name):
        for ch in self._sweeps:
            if ch['name'] == name:
                return ch
        for ch in self._sweeps:
            if ch['long_name'] == name:
                return ch
        return None

    def figures(self, fig_lst):
        self.plot_manager.Figures = fig_lst

    def set_sweep(self):
        pass

    def set_datas(self):
        pass

    def set_plots(self):
        pass

    def __next_options(self, lst, **kw):
        if len(lst) == 0:
            yield {}
        ch = lst[0]
        if isinstance(ch['ranges'], collections.Callable):
            ranges = ch['ranges'](**kw)
        else:
            ranges = ch['ranges']
        name = ch['name']
        if ch['before'] is not None:
            ch['before'](*ch['before_args'], **kw)
        for v in ranges:
            kw[name] = v
            ch['current'] = v
            if len(lst) == 1:
                yield kw
            else:
                for kw in self.__next_options(lst[1:], **kw):
                    yield kw
        if ch['after'] is not None:
            ch['after'](*ch['after_args'], **kw)

    def next_options(self):
        return self.__next_options(self._sweeps)

    def work(self):
        self._init()

        total = 0
        for options in self.next_options():
            total += 1

        for options in self.next_options():
            self.task_manager.set_args_for_tasks(**options)
            self.task_manager.start_tasks()
            self.task_manager.wait_tasks_finish()
        self._final()

    def _init(self):
        self.init()
        self.set_sweep()
        self.data_manager.start_capture()

    def _final(self):
        self.plot_manager.save_figs()
        self.data_manager.stop_capture()
        self.final()

    def set_parameters(self):
        pass

    def init(self):
        print "Init ... "

    def final(self):
        print "Final"

    def run(self):
        app = QtGui.QApplication(self.argv)
        self.set_datas()
        self.set_plots()
        self.task_manager.start_serv()
        #self.work()
        self.win = MainWindow(self)
        self.win.show()
        return app.exec_()

    def paused(self, p=True):
        self.task_manager.paused(p)

    def is_paused(self):
        return self.task_manager.is_paused()

    def user(self):
        self.history['User'] = str(self.win.user.text())
        return self.history['User']

    def sampleID(self):
        self.history['Sample ID'] = str(self.win.sample.text())
        return self.history['Sample ID']

    def notes(self):
        notes = str(self.win.notes.toPlainText())
        self.history['Notes'] = "''" if notes is '' else notes
        return self.history['Notes']
