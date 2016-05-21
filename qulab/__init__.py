# -*- coding: utf-8 -*-
import os, time
import numpy as np
import logging
import logging.handlers
from qulab.driver import InstrumentManager

class Lab():
    def __init__(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        socketHandler = logging.handlers.SocketHandler('localhost',\
                        logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)

        self.instr = InstrumentManager()

    def open_instr(self, name, addr):
        self.instr.add_instr(name, addr)
        return self.instr['name']

    def savetxt(self, name, X, database='D:\\', header=''):
        basedir = os.path.join(database, time.strftime('%Y/%m/%Y%m%d'))
        fname = '%s_%s.txt' % (name, time.strftime("%Y%m%d%H%M%S"))
        if basedir != '' and not os.path.exists(basedir):
            os.makedirs(basedir)
        fname = os.path.join(basedir, fname)
        np.savetxt(fname, X, header=header, comments="#")

def open_lab():
    return Lab()
