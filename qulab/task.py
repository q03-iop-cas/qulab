# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 17:55:53 2016

@author: feihoo87
"""

import functools
import inspect
import time
from PyQt4 import QtCore
from qulab.base import Manager


def step(follows=None):
    """@step(follows)

    This is a decorator applied to Python methods of a qulab.Application that marks them
    as an experiment step.

    Parameters
    ----------

    follows : a list of string, optional, default: None
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, **kwargs):
            argspec = inspect.getargspec(method)
            args = argspec.args
            defaults = () if argspec.defaults is None else argspec.defaults
            kw = {} if argspec.keywords is None else argspec.keywords
            for i in range(len(defaults)):
                kw[args[i+len(args)-len(defaults)]] = defaults[i]
            for name in args:
                if name == "self":
                    continue
                if name in kwargs.keys():
                    kw[name] = kwargs[name]
            method(self, **kw)
        wrapper._follows = [] if follows is None else follows
        wrapper.thread = None
        return wrapper
    return decorator
    

class Task(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)

    def __init__(self, func, obj=None, follows=None):
        super(Task, self).__init__()
        self.func = [func, obj]
        self.kwargs = {}
        self.follows = [] if follows is None else follows
        self.rest = {}
        self.myThread = None
        self._paused = False
        for name in follows:
            self.rest[name] = False
        self._isFinished = False

    def set_args(self, **kwargs):
        self.kwargs = kwargs

    @QtCore.pyqtSlot(str)
    def start(self, name=''):
        name = str(name)
        if name in self.follows:
            self.rest[name] = True

        if all(self.rest.values()):
            self.run()

    def reset(self):
        self._isFinished = False
        for name in self.follows:
            self.rest[name] = False

    def run(self):
        while self._paused:
            time.sleep(0.01)
            
        if self.func[1] is not None:
            self.func[0](self.func[1], **self.kwargs)
        else:
            self.func[0](**self.kwargs)

        self.finished.emit(self.func[0].__name__)
        self._isFinished = True

    def is_finished(self):
        return self._isFinished
        
        
class TaskManager(Manager):
    one_loop_finished = QtCore.pyqtSignal()
    
    def __init__(self, app):
        super(TaskManager, self).__init__(app)
        self._tasks = None
        self._paused = False
        
    def init(self):
        def _foo(**kw): pass
        def _bar(**kw): pass

        self._tasks = {"_foo": Task(_foo, follows=[])}

        for name, value in vars(self.app.__class__).items():
            if hasattr(value, '_follows'):
                value._follows.append("_foo")
                task = Task(value, self.app, value._follows)
                self._tasks[value.__name__] = task

        end_follows = [t.func[0].__name__ for t in self._tasks.values()]

        self._tasks["_bar"] = Task(_bar, follows=end_follows)

    def start_serv(self):
        self.init()
        for steps in self._tasks.values():
            steps.reset()
            for ft in steps.follows:
                self._tasks[ft].finished.connect(steps.start)
            thread = QtCore.QThread()
            steps.moveToThread(thread)
            steps.myThread = thread
            thread.start()
            
    def set_args_for_tasks(self, **kwargs):
        for t in self._tasks.values():
            t.set_args(**kwargs)
            t.reset()
            
    def start_tasks(self):
        self._tasks['_foo'].start()
    
    def wait_tasks_finish(self):
        while True:
            if self._tasks['_bar'].is_finished():
                break
            time.sleep(0.1)
        self.one_loop_finished.emit()
    
    def paused(self, p=True):
        for t in self._tasks.values():
            t._paused = p
        self._paused = p
            
    def is_paused(self):
        return self._paused
        