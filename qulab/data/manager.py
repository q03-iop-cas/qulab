# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 18:06:40 2016

@author: feihoo87
"""
import time
import collections
from PyQt4 import QtCore
from qulab.base import Manager
from qulab.data.data import datatype_factory

import logging
logger = logging.getLogger("data")
logger.setLevel(logging.DEBUG)


class DataManager(Manager):
    data_updated = QtCore.pyqtSignal(str)
    max_trash = 100
    save_raw = True
    
    def __init__(self, app):
        super(DataManager, self).__init__(app)
        self.datas = {}
        self.templates = {}
        self._targets = []
        self.__trash = []
        
    def __getitem__(self, key):
        if key in self.datas.keys():
            return self.datas[key]
        else:
            self.datas[key] = self.new(key)
            return self.datas[key]
            
    def __setitem__(self, key, value):
        if key in self.templates.keys():
            data = self.new(key)
            data.paramenters = data.get_current_paramenters()
            if key in self.datas.keys():
                #while len(self.__trash) >= self.max_trash:
                #    self.__trash.pop(0)
                self.__trash.append(self.datas[key])
            self.datas[key] = data
        else:
            raise Exception('Key "%s" not in templates.' % key)
        data.reset_values(value)
            
    def new(self, name):
        data = self.templates[name][0](self)
        path, fname = self.gen_fname(data)
        if path == '':
            data.fname = '/'.join([self.app.database.basedir(),fname])
        else:
            data.fname = '/'.join([self.app.database.basedir(),path,fname])
        data.updated.connect(self.on_data_updated)
        data.is_auto_save = True
        return data
        
    def template(self, name, fname=None,
                 index=None, cols=None, doc = ''):
        MyData = datatype_factory(name, index, cols, doc)
        if fname is None:
            fname = '%s_{autoname}.txt' % name
        self.templates[name] = (MyData, fname)
        self._targets = [name]
        
    def targets(self, tgs):
        self._targets = []
        if isinstance(tgs, collections.Iterable) and not isinstance(tgs, str):
            for t in tgs:
                self._targets.append(t)
        else:
            self._targets.append(tgs)
        
    def get_current_index(self, data):
        ret = []
        for index_name in data.index_names:
            ret.append(self.app.get_sweep_by_name(index_name)['current'])
        return tuple(ret)
        
    def get_current_paramenters(self, data):
        ret = []
        for ch in self.app._sweeps:
            if ch['name'] in data.index_names\
            or ch['long_name'] in data.index_names:
                continue
            ret.append((ch['long_name'], ch['current'], ch['unit']))
        return ret
        
    def gen_fname(self, data):
        key = data.__class__.__name__
        cls, fname = self.templates[key]
        pars = ""
        path_list = []
        #data.paramenters = self.get_current_paramenters(data)
        for name, value, unit in data.paramenters:
            name = self.app.get_sweep_by_name(name)['name']
            if value is None:
                pars += ("%s_nan" % name)
                path_list.append("%s_nan" % name)
            else:
                pars += ("%s_%g" % (name, value))
                path_list.append("%s_%g" % (name, value))
            if unit != '':
                pars += ("_%s" % unit)
            pars += "_"
        if len(path_list) > 1:
            path = '/'.join(path_list[:-1])
        else:
            path = ''
        if pars != "":
            autoname = pars[:-1] + '_' + time.strftime("%Y%m%d%H%M%S")
        else:
            autoname = time.strftime("%Y%m%d%H%M%S")
        return path, fname.format(autoname = autoname)
        
    def start_capture(self):
        for name in self.templates.keys():
            self.datas[name] = self.new(name)
        for data in self.__trash:
            del data
    
    def stop_capture(self):
        pass
    
    @QtCore.pyqtSlot()
    def on_data_updated(self):
        data = self.sender()
        if data is None:
            return
            
        cls_name = data.__class__.__name__
        if data.is_auto_save:
            if cls_name in self._targets:
                if data.fname == None:
                    path, fname = self.gen_fname(data)
                    data.fname = '/'.join([self.app.database.basedir(), path, fname])
                data.save(data.fname)
            elif self.save_raw:
                path, fname = self.gen_fname(data)
                data.fname = fname if path == '' else path+'/'+fname
                zipfname = self.datas[self._targets[0]].fname+'.zip'
                data.tar(zipfname, data.fname)
            else:
                pass
                
        if data in self.__trash:
            pass
        else:
            self.data_updated.emit(cls_name)
            
        for d in self.__trash:
            if d.is_saved == True or not d.is_auto_save:
                self.__trash.remove(d)
                del d
            
    def load_data(self, fname):
        name = self._targets[0]
        MyData, fnameR = self.templates[name]
        self.datas[name] = MyData(self)
        self.datas[name].from_txt(fname)
    
    