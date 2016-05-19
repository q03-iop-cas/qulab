# -*- coding: utf-8 -*-
import struct
from visa import VisaIOWarning

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

class Driver(BaseDriver):
    error_command = ''
    surport_models = ['SR620']
    quants = [
        Q('DATAS', unit='', type=VECTOR)
    ]

    def performGetValue(self, quant, **kw):
        if quant.name == 'DATAS':
            if 'count' in kw.keys():
                count = kw['count']
            else:
                count = 100
            return self.get_Datas(count)
        else:
            return super(Driver, self).performGetValue(quant, **kw)

    def get_Datas(self, count=100):
        block = ''
        max = 5000
        loop = int(count/max)
        last = count % max
        self.write('*CLS')
        try:
            if last < count:
                for i in range(loop):
                    self.write('BDMP %d' % max)
                    block += self.__read(8*max)
            self.write('BDMP %d' % last)
            block += self.__read(8*last)
        except:
            raise
        mode = int(self.query('MODE?'))
        expd = int(self.query('EXPD?'))
        self.write('AUTM 1')
        return convert(list(struct.unpack('%dH' % 4*count, block)), mode, expd)

    def __read(self, size):
        try:
            buff = self.ins.visalib.read(self.ins.session, size)[0]
        except VisaIOWarning:
            pass
        return buff
