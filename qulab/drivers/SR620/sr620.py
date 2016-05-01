# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 00:01:19 2013

@author: feihoo87
"""
import struct
from pyvisa import vpp43
from pyvisa.visa import VisaIOWarning

from .error import DriverError
from .base import CounterDriver

def convert(data, mode, expd):
    """将读取出的二进制数据块转换成列表
    
    根据说明书第53页中的 C 语音代码改写而成。
    
    data : 读出的原始二进制数据块以16位整形数排列而成的列表
    mode : 通过向 SR620 发送 'MODE?' 命令获取
    expd : 通过向 SR620 发送 'EXPD?' 命令获取
    """
    factors=[1.05963812934E-14, 1.05963812934E-14,
             1.05963812934E-14, 1.24900090270331E-9,
             1.05963812934E-14, 8.3819032E-8, 0.00390625]

    l = len(data)/4
    ret = []
    for i in range(l):
        sign = (data[i*4+3] < 0)
        v = 0.0
        for j in range(4):
            v = v*65536.0 + (sign and ~data[i*4+3-j] or data[i*4+3-j])
        v = v*factors[mode]
        if expd != 0:
            v = v*1.0e-3
        if sign:
            v = -v-1.0
        ret.append(v)
    return ret

class sr620(CounterDriver):
    """SR620的驱动"""
    def __init__(self, ins, *args, **kwargs):
        """
        ins : 设备对象
        """
        super(sr620, self).__init__(ins, *args, **kwargs)
        self.ins = ins
        
    def __read(self, size):
        """从设备读取 size 个字节"""
        try:
            buff = vpp43.read(self.ins.vi, size)
        except VisaIOWarning:
            pass
        return buff

    def dump(self, n):
        """用快速模式从仪器上读取n个数"""
        block = ''
        max = 5000

        loop = n / max
        last = n % max
        
        self.exec_("*CLS")
        try:
            if last < n:
                for i in range(loop):
                    self.exec_("BDMP %d" % max)
                    block += self.__read(8*max)
            self.exec_("BDMP %d" % last)
            block += self.__read(8*last)
        except:
            #raise DriverError(self.ins, code=1, msg="SR620 Dump Error")
            raise
        tmp = list(struct.unpack("%dH" % 4*n, block))
        mode = int(self.ask('MODE?'))
        expd = int(self.ask('EXPD?'))
        self.ins.write("AUTM 1")
        return convert(tmp, mode, expd)
        
    def set_level(self, v):
        pass
    
    def set_mode(self, mode):
        pass
    
    def errors(self):
        """返回错误列表"""
        e = []
        return e
    