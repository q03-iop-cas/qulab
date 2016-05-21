# -*- coding: utf-8 -*-
from qulab.quantity import Quantity, QuantTypes
import logging
import string, struct
import copy
import os
import sys
import re
import visa
import numpy as np

logger = logging.getLogger("drivers")
logger.setLevel(logging.DEBUG)

def IEEE_488_2_BinBlock(datalist, dtype="int16", is_big_endian=True):
    """将一组数据打包成 IEEE 488.2 标准二进制块

    datalist : 要打包的数字列表
    dtype    : 数据类型
    endian   : 字节序

    返回二进制块, 以及其 'header'
    """
    types = {"b"      : (  int, 'b'), "B"      : (  int, 'B'),
             "h"      : (  int, 'h'), "H"      : (  int, 'H'),
             "i"      : (  int, 'i'), "I"      : (  int, 'I'),
             "q"      : (  int, 'q'), "Q"      : (  int, 'Q'),
             "f"      : (float, 'f'), "d"      : (float, 'd'),
             "int8"   : (  int, 'b'), "uint8"  : (  int, 'B'),
             "int16"  : (  int, 'h'), "uint16" : (  int, 'H'),
             "int32"  : (  int, 'i'), "uint32" : (  int, 'I'),
             "int64"  : (  int, 'q'), "uint64" : (  int, 'Q'),
             "float"  : (float, 'f'), "double" : (float, 'd'),
             "float32": (float, 'f'), "float64": (float, 'd')}

    datalist = np.array(datalist)
    datalist.astype(types[dtype][0])
    if is_big_endian:
        endianc = '>'
    else:
        endianc = '<'
    datablock = struct.pack('%s%d%s' % (endianc, len(datalist), types[dtype][1]), *datalist)
    size = '%d' % len(datablock)
    header = '#%d%s' % (len(size),size)

    return header+datablock, header

class InstrumentQuantity(Quantity):
    def __init__(self, name, value=None, type=QuantTypes.DOUBLE,
                 unit=None, dimension=None,
                 set_cmd=None, get_cmd=None, options={}):
        Quantity.__init__(self, name, value, type, unit, dimension)
        self.driver = None
        self.set_cmd = set_cmd
        self.get_cmd = get_cmd
        self.options = {}

    def setValue(self, value, **kw):
        self.value = value
        if self.driver is not None and self.set_cmd is not None:
            cmd = self.set_cmd % dict(value=value, **kw)
            self.driver.write(cmd)

    def getValue(self, **kw):
        if self.driver is not None and self.get_cmd is not None:
            cmd = self.get_cmd % dict(**kw)
            if self.type == QuantTypes.STRING:
                res = self.driver.query(cmd)
            else:
                res = self.driver.query_ascii_values(cmd)
            if self.type == QuantTypes.DOUBLE:
                res = res[0]
            elif self.type == QuantTypes.INTEGER:
                res = int(res[0])
            elif self.type == QuantTypes.BOOL:
                res = bool(res)
            self.value = res
        return self.value

class BaseDriver():
    error_command = 'SYST:ERR?'
    surport_models = []
    quants = []

    def __init__(self, ins=None, addr=None, model=None, timeout=3, **kw):
        self.addr = addr
        self.ins = ins
        self.timeout = timeout
        if self.ins is not None:
            self.ins.timeout = timeout*1000
        self.quantities = {}
        self.model = model

        for q in self.quants:
            self._add_quant(q)

    def _add_quant(self, quant):
        self.quantities[quant.name] = copy.deepcopy(quant)
        self.quantities[quant.name].driver = self

    def _load_config(self):
        pass

    def set_timeout(self, t):
        self.timeout = t
        if self.ins is not None:
            self.ins.timeout = t*1000

    def errors(self):
        """返回错误列表"""
        e = []
        if self.error_command == '':
            return e
        while True:
            s = self.ins.query(self.error_command)
            _ = s[:-1].split(',"')
            code = string.atoi(_[0])
            msg = _[1]
            if code == 0:
                break
            e.append((code, msg))
        return e

    def check_errors_and_log(self, message):
        errs = self.errors()
        for e in errs:
            logger.error("%s << %s", str(self.ins), message)
            logger.error("%s >> %s", str(self.ins), ("%d : %s" % e))

    def query(self, message, check_errors=False):
        if self.ins is None:
            return None
        logger.debug("%s << %s", str(self.ins), message)
        try:
            res = self.ins.query(message)
        except:
            logger.exception("%s << %s", str(self.ins), message)
            raise
        logger.debug("%s >> %s", str(self.ins), res)
        if check_errors:
            self.check_errors_and_log(message)
        return res

    def query_ascii_values(self, message, converter='f', separator=',',
                           container="<type 'list'>", delay=None,
                           check_errors=False):
        if self.ins is None:
            return None
        logger.debug("%s << %s", str(self.ins), message)
        try:
            res = self.ins.query_ascii_values(message, converter, separator, container, delay)
        except:
            logger.exception("%s << %s", str(self.ins), message)
            raise
        logger.debug("%s >> <%d results>", str(self.ins), len(res))
        if check_errors:
            self.check_errors_and_log(message)
        return res

    def query_binary_values(self, message, datatype='f', is_big_endian=False,
                            container="<type 'list'>", delay=None,
                            header_fmt='ieee', check_errors=False):
        if self.ins is None:
            return None
        logger.debug("%s << %s", str(self.ins), message)
        try:
            res = self.ins.query_binary_values(message, datatype, is_big_endian,
                                               container, delay, header_fmt)
        except:
            logger.exception("%s << %s", str(self.ins), message)
            raise
        logger.debug("%s >> <%d results>", str(self.ins), len(res))
        if check_errors:
            self.check_errors_and_log(message)
        return res

    def write(self, message, check_errors=False):
        """Send message to the instrument."""
        if self.ins is None:
            return None
        logger.debug("%s << %s", str(self.ins), message)
        try:
            ret = self.ins.write(message)
        except:
            logger.exception("%s << %s", str(self.ins), message)
            raise
        if check_errors:
            self.check_errors_and_log(message)
        return ret

    def write_ascii_values(self, message, values, converter='f', separator=',',
                           termination=None, encoding=None, check_errors=False):
        if self.ins is None:
            return None
        log_msg = message+('<%d values>'%len(values))
        logger.debug("%s << %s", str(self.ins), log_msg)
        try:
            ret = self.ins.write_ascii_values(message, values, converter,
                                              separator, termination, encoding)
        except:
            logger.exception("%s << %s", str(self.ins), log_msg)
            raise
        if check_errors:
            self.check_errors_and_log(log_msg)
        return ret

    def write_binary_values(self, message, values,
                            datatype='f', is_big_endian=False,
                            termination=None, encoding=None, check_errors=False):
        if self.ins is None:
            return None
        block, header = IEEE_488_2_BinBlock(values, datatype, is_big_endian)
        log_msg = message+header+'<DATABLOCK>'
        logger.debug("%s << %s", str(self.ins), log_msg)
        try:
            ret = self.ins.write_binary_values(message, values, datatype,
                                           is_big_endian, termination, encoding)
        except:
            logger.exception("%s << %s", str(self.ins), log_msg)
            raise
        if check_errors:
            self.check_errors_and_log(log_msg)
        return ret

    def getValue(self, name, **kw):
        if name in self.quantities:
            return self.performGetValue(self.quantities[name], **kw)
        else:
            return None

    def setValue(self, name, value, **kw):
        if name in self.quantities:
            self.performSetValue(self.quantities[name], value, **kw)

    def performOpen(self, **kw):
        pass

    def performGetValue(self, quant, **kw):
        return quant.getValue(**kw)

    def performSetValue(self, quant, value, **kw):
        quant.setValue(value, **kw)

def load_driver(fname):
    glb = {
        'BaseDriver' : BaseDriver,
        'Q'          : InstrumentQuantity,
        'INTEGER'    : QuantTypes.INTEGER,
        'DOUBLE'     : QuantTypes.DOUBLE,
        'VECTOR'     : QuantTypes.VECTOR,
        'STRING'     : QuantTypes.STRING,
        'OPTION'     : QuantTypes.OPTION,
        'BOOL'       : QuantTypes.BOOL,
    }

    with open(fname,'r') as f:
        path = os.path.dirname(os.path.abspath(fname))
        if path in sys.path:
            exec(f.read(), glb)
        else:
            sys.path.append(path)
            exec(f.read(), glb)
            sys.path.remove(path)
        return glb['Driver']
    return None

ats_addr = re.compile(r'^(ATS9626|ATS9850|ATS9870)::SYSTEM([0-9]*)::([0-9]*)(|::INSTR)$')

def open_visa_resource(rm, addr):
    ins = rm.open_resource(addr)
    IDN = ins.query("*IDN?").split(',')
    company = IDN[0].strip()
    model   = IDN[1].strip()
    version = IDN[3].strip()
    return dict(ins=ins, company=company, model=model, version=version, addr=addr)

class InstrumentManager():
    def __init__(self):
        self.instr = {}
        self.rm = visa.ResourceManager()
        self._driver_clss = []
        self._load_drivers()

    def __getitem__(self, name):
        if name in self.instr.keys():
            return self.instr[name]
        else:
            return None

    def add_instr(self, name, addr):
        '''If success return True, else return False'''
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
        if DriverClass is None:
            return False
        else:
            self.instr[name] = DriverClass(**info)
            self.instr[name].performOpen()
            return True

    def _get_driver_by_model(self, model):
        for driver_cls in self._driver_clss:
            if model in driver_cls.surport_models:
                return driver_cls
        return None

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
