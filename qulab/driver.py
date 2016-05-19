from qulab.quantity import Quantity, QuantTypes
import logging, string, copy

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
        super(InstrumentQuantity, self).__init__(name, value, type, unit, dimension)
        self.driver = None
        self.set_cmd = set_cmd
        self.get_cmd = get_cmd
        self.options = {}

    def setValue(self, value, **kw):
        self.value = value
        if self.driver is not None and self.set_cmd is not None:
            cmd = self.set_cmd.format(value=value, **kw)
            self.driver.write(cmd)

    def getValue(self, **kw):
        if self.driver is not None and self.get_cmd is not None:
            self.value = self.driver.query(self.get_cmd.format(**kw))
        return self.value

import functools
import inspect

def with_log_and_error_check(logger, is_query=False, check_errors=False):
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
            log_msg = kw['message']
            logger.debug("%s << %s", str(self.ins), log_msg)
            try:
                ret = method(self, **kw)
            except:
                logger.exception("%s << %s", str(self.ins), log_msg)
                raise
            if isinstance(ret, str):
                logger.debug("%s >> %s", str(self.ins), ret)
            elif is_query:
                logger.debug("%s >> <%d RESULTS>", str(self.ins), len(ret))
            if check_errors:
                self.check_errors_and_log(log_msg)
            return ret
        return wrapper
    return decorator

class BaseDriver():
    error_command = 'SYST:ERR?'
    surport_models = []
    quants = []

    def __init__(self, ins, addr, model, timeout=3, **kw):
        self.addr = addr
        self.ins = ins
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

    def query_ascii_values(self, *args, **kw):
        ret = self.ins.query_ascii_values(*args, **kw)
        return ret

    def query_binary_values(self, *args, **kw):
        ret = self.ins.query_binary_values(*args, **kw)
        return ret

    def write(self, message, check_errors=False):
        """Send message to the instrument."""
        logger.debug("%s << %s", str(self.ins), message)
        try:
            ret = self.ins.write(message)
        except:
            logger.exception("%s << %s", str(self.ins), message)
            raise
        if check_errors:
            self.check_errors_and_log(message)
        return ret

    def write_ascii_values(self, *args, **kw):
        ret = self.ins.write_ascii_values(*args, **kw)
        return ret

    def write_binary_values(message, values,
                            datatype='f', is_big_endian=False,
                            termination=None, encoding=None, check_errors=False):
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

    def getValue(self, name):
        if name in self.quantities:
            return self.performGetValue(self.quantities[name])
        else:
            return None

    def setValue(self, name, value):
        if name in self.quantities:
            self.performSetValue(self.quantities[name], value)

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
        exec(f.read(), glb)
        return glb['Driver']
    return None
