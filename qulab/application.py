# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 13:37:04 2015

@author: feihoo87
"""

import collections
from PyQt4 import QtCore, QtGui
import time
import visa
import os


def button(text, layout, callback, parent=None):
    btn = QtGui.QPushButton(text, parent=parent)
    btn.clicked.connect(callback)
    layout.addWidget(btn)
    return btn
    
    
class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        self.UI()
        
    def UI(self):
        self.centralwidget = QtGui.QWidget(self)
        self.layout = QtGui.QVBoxLayout(self.centralwidget)
        self.layout.addWidget(self.BaseUI())
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle(u'%s (QuLab %s)'%(self.app.__title__, self.app.__version__))

    def BaseUI(self):
        group = QtGui.QGroupBox(self)
        
        gp1 = QtGui.QGroupBox("Data Base", self)
        layout = QtGui.QHBoxLayout(gp1)
        layout.addWidget(QtGui.QLabel("Base Dir", parent=self))
        self.baseDir = QtGui.QLineEdit(self.app.main_cfg['Basic:path'], parent=self)
        btn = QtGui.QPushButton(u'Choose', parent=self)
        btn.clicked.connect(self.choose_base_dir)
        layout.addWidget(self.baseDir)
        layout.addWidget(btn)
        
        gp2 = QtGui.QGroupBox("Actions", self)
        layout = QtGui.QVBoxLayout(gp2)
        l1 = QtGui.QHBoxLayout()
        self.start_btn = button('Start',      l1, self.start)
        self.pause_btn = button('Pause',      l1, self.paused)
        self.ended_btn = button('Interrupt',  l1, self.interrupt)
        self.ended_btn.setEnabled(False)
        layout.addLayout(l1)
        l2 = QtGui.QHBoxLayout()
        self.hide_show_btn = button('Hide',  l2, self.hide_show)
        self.hide_show_btn.setEnabled(False)
        self.load_btn = button('Load',       l2, self.load_data)
        self.anal_btn = button('Analyse',    l2, self.analyse)
        layout.addLayout(l2)
        
        gp3 = QtGui.QGroupBox(self)
        self.user   = QtGui.QLineEdit(self.app.history.get("User", "default user"), parent=self)
        self.sample = QtGui.QLineEdit(self.app.history.get("Sample ID", "default"), parent=self)
        self.notes  = QtGui.QTextEdit(parent=self)
        layout1 = QtGui.QHBoxLayout()
        layout2 = QtGui.QHBoxLayout()
        layout3 = QtGui.QHBoxLayout()
        layout1.addWidget(QtGui.QLabel("User Name", parent=self))
        layout1.addWidget(self.user)
        layout2.addWidget(QtGui.QLabel("Sample ID", parent=self))
        layout2.addWidget(self.sample)
        layout3.addWidget(QtGui.QLabel("Notes    ", parent=self))
        layout3.addWidget(self.notes)
        layout = QtGui.QVBoxLayout(gp3)
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        
        layout = QtGui.QHBoxLayout(group)
        ll = QtGui.QVBoxLayout()
        lr = QtGui.QVBoxLayout()
        ll.addWidget(gp1)
        ll.addWidget(gp2)
        lr.addWidget(gp3)
        layout.addLayout(lr)
        layout.addLayout(ll)
        
        return group

    def choose_base_dir(self):
        dir_name = QtGui.QFileDialog.getExistingDirectory(None, "Directory", self.baseDir.text())
        self.baseDir.setText(dir_name)
        self.app.database = DataBase(str(dir_name))
    
    @QtCore.pyqtSlot()
    def start(self):        
        class Foo(QtCore.QThread):
            app = None
            started = QtCore.pyqtSignal()
            finished = QtCore.pyqtSignal()
            def run(self):
                self.started.emit()
                self.app.work()
                self.finished.emit()
                
        self.app.set_parameters()
        self.app.plot_manager.init()
        self.foo = Foo()
        self.foo.app = self.app
        self.foo.started.connect(self.on_work_start)
        self.foo.finished.connect(self.on_work_finished)
        self.foo.start()
        #self.app.plot_manager.show_all()
    
    @QtCore.pyqtSlot()
    def on_work_start(self):
        self.start_btn.setEnabled(False)
        self.ended_btn.setEnabled(True)
        self.hide_show_btn.setEnabled(True)
    
    @QtCore.pyqtSlot()
    def on_work_finished(self):
        self.start_btn.setEnabled(True)
        self.ended_btn.setEnabled(False)
        
    @QtCore.pyqtSlot()
    def on_proccess(self):
        pass
    
    def update(self):
        pass
    
    @QtCore.pyqtSlot()
    def paused(self):
        if str(self.pause_btn.text()) == "Pause":
            if self.app != None:
                self.app.paused(True)
            self.pause_btn.setText("Continue")
        elif str(self.pause_btn.text()) == "Continue":
            if self.app != None:
                self.app.paused(False)
            self.pause_btn.setText("Pause")
            
    # TODO: 设计使其终止后还能正常重启
    @QtCore.pyqtSlot()
    def interrupt(self):
        pass
    
    @QtCore.pyqtSlot()
    def hide_show(self):
        if str(self.hide_show_btn.text()) == "Hide":
            if self.app != None:
                self.app.plot_manager.hide_all()
            self.hide_show_btn.setText("Show")
        elif str(self.hide_show_btn.text()) == "Show":
            if self.app != None:
                self.app.plot_manager.show_all()
            self.hide_show_btn.setText("Hide")
    
    @QtCore.pyqtSlot()
    def load_data(self):
        fileName = QtGui.QFileDialog.getOpenFileName(None, "Open File", "D:\\", "All files (*.*)")
        self.app.data_manager.load_data(str(fileName))
        self.app.plot_manager.init()
        self.app.plot_manager.show_all()
        
    @QtCore.pyqtSlot()
    def analyse(self):
        pass


class DataBase():
    def __init__(self, url='.'):
        self.url = url
        
    def basedir(self):
        return self.url + '/' + time.strftime("%Y/%m/%Y%m%d")
        
import inspect
import functools
from qulab.task import TaskManager
from qulab.data import DataManager
from qulab.plot import PlotManager
from qulab.config import config


class Application:
    __title__   = "Qulab Application"
    __version__ = 'v0.1'
    
    def __init__(self, argv):
        self.argv = argv
        self.prog_name = os.path.basename(self.argv[0])
        self._sweeps = []
        self.cfg = {}
        self.config = config(self.prog_name)
        self.main_cfg = config('main')
        self.history = config('history')
        self.database     = DataBase(self.main_cfg["Basic:path"])
        self.task_manager = TaskManager(self)
        self.data_manager = DataManager(self)
        self.plot_manager = PlotManager(self)
        self.rm           = visa.ResourceManager()
        self.data = self.data_manager
        self.plot = self.plot_manager
        self._settings = None
        
    def _get_settings(self):
        settings = []
        in_setting_section = False
        
        with open(self.argv[0]) as f:
            lines = f.readlines()
            for line in lines:
                if line[0:4] == "#{{{":
                    in_setting_section = True
                elif line[0:4] == "#}}}":
                    in_setting_section = False
                elif in_setting_section:
                    settings.append(line)
                else:
                    pass
        return "".join(settings)
        
    def get_settings(self):
        if self._settings is None:
            self._settings = self._get_settings()
        return self._settings
        
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
    
    