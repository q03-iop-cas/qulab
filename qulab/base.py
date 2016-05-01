# -*- coding: utf-8 -*-
"""
Created on Fri Jan 08 17:59:56 2016

@author: feihoo87
"""
from PyQt4 import QtCore

class Manager(QtCore.QObject):
    def __init__(self, app):
        super(Manager, self).__init__()
        self.app = app
        
    def version(self):
        return self.app.__version__
        
    def program(self):
        return self.app.prog_name
        