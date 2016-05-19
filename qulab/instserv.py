# -*- coding: utf-8 -*-
import re
import os
import visa
from qulab.driver import load_driver

ats_addr = re.compile(r'^(ATS9626|ATS9850|ATS9870)::SYST([0-9]*)::([0-9]*)(|::INSTR)$')

def open_visa_resource(rm, addr):
    ins = rm.open_resource(addr)
    IDN = ins.query("*IDN?").split(',')
    company = IDN[0].strip()
    model   = IDN[1].strip()
    version = IDN[3].strip()
    return dict(ins=ins, company=company, model=model, version=version, addr=addr)

class Instrument():
    def __init__(self):
        self.serv = None
        self.name = None

    def write(self, msg):
        self.serv.write(self.name, msg)

    def query(self, msg):
        return self.serv.query(self.name, msg)

class InstServer():
    def __init__(self):
        self.instr = {}
        self.rm = visa.ResourceManager()
        self._driver_clss = []

    def add_instr(self, name, addr):
        m = ats_addr.search(addr)
        if m is not None:
            model = m.group(1)
            systemID = int(m.group(2))
            boardID = int(m.group(3))
            info = dict(ins=None,
                        company='AlazarTech',
                        model=model,
                        systemID=systemID,
                        boardID=boardID,
                        addr=addr)
        else:
            info = open_visa_resource(self.rm, addr)

        DriverClass = self._get_driver_by_model(info['model'])
        self.instr[name] = DriverClass(**info)

    def _get_driver_by_model(self, model):
        for driver_cls in self._driver_clss:
            if model in driver_cls.surport_models:
                return driver_cls

    def _get_driver_paths(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drivers')
        driver_paths = [path]
        return driver_paths

    def _load_drivers(self):
        driver_paths = self._get_driver_paths()
        for p in driver_paths:
            l = os.listdir(p)
            for n in l:
                DriverClass = load_driver(os.path.join(p,n,n+'.py'))
                self._driver_clss.append(DriverClass)

    def start(self):
        pass

    def stop(self):
        pass
