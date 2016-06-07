# -*- coding: utf-8 -*-

class Base():
    def __init__(self):
        pass
        
class Manager():
    def __init__(self, app):
        super(Manager, self).__init__()
        self.app = app

    def version(self):
        return self.app.__version__

    def program(self):
        return self.app.prog_name
