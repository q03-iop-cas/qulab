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
        Q('Datas', unit='', type=VECTOR),
        Q('Ext Level', unit='V', type=DOUBLE, set_cmd='LEVL 0,%(value)f', get_cmd='LEVL? 0'),
        Q('A Level', unit='V', type=DOUBLE, set_cmd='LEVL 1,%(value)f', get_cmd='LEVL? 1'),
        Q('B Level', unit='V', type=DOUBLE, set_cmd='LEVL 2,%(value)f', get_cmd='LEVL? 2'),
        Q('Ext Term', unit='', type=OPTION, set_cmd='TERM 0,%(option)s', get_cmd='TERM? 0', options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('A Term', unit='', type=OPTION, set_cmd='TERM 1,%(option)s', get_cmd='TERM? 1', options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('B Term', unit='', type=OPTION, set_cmd='TERM 2,%(option)s', get_cmd='TERM? 2', options={'50 Ohm' : '0', '1 MOhm' : '1'}),
        Q('Ext Slope', unit='', type=OPTION, set_cmd='TSLP 0,%(option)s', get_cmd='TSLP? 0', options={'Positive' : '0', 'Negative' : '1'}),
        Q('A Slope', unit='', type=OPTION, set_cmd='TSLP 1,%(option)s', get_cmd='TSLP? 1', options={'Positive' : '0', 'Negative' : '1'}),
        Q('B Slope', unit='', type=OPTION, set_cmd='TSLP 2,%(option)s', get_cmd='TSLP? 2', options={'Positive' : '0', 'Negative' : '1'}),
        Q('Ext Slope', unit='', type=OPTION, set_cmd='TSLP 0,%(option)s', get_cmd='TSLP? 0', options={'Positive' : '0', 'Negative' : '1'}),
        Q('A Slope', unit='', type=OPTION, set_cmd='TSLP 1,%(option)s', get_cmd='TSLP? 1', options={'Positive' : '0', 'Negative' : '1'}),
        Q('B Slope', unit='', type=OPTION, set_cmd='TSLP 2,%(option)s', get_cmd='TSLP? 2', options={'Positive' : '0', 'Negative' : '1'}),
        Q('A Coupling', unit='', type=OPTION, set_cmd='TCPL 1,%(option)s', get_cmd='TCPL? 1', options={'DC' : '0', 'AC' : '1'}),
        Q('B Coupling', unit='', type=OPTION, set_cmd='TCPL 2,%(option)s', get_cmd='TCPL? 2', options={'DC' : '0', 'AC' : '1'}),
        Q('Mode', type=OPTION, set_cmd='MODE %(option)s', get_cmd='MODE?',
            options = {
                'time' : '0',
                'width'  : '1',
                'tr/tf': '2',
                'freq' : '3',
                'period' : '4',
                'phase' : '5',
                'count' : '6',
            }),
        Q('Arming Mode', type=OPTION, set_cmd='ARMM %s', get_cmd='ARMM?',
            options = {
                '+- time' : '0',
                '+ time'  : '1',
                '1 period': '2',
                '0.01 s gate' : '3',
                '0.1 s gate' : '4',
                '1.0 s gate' : '5',
                'ext trig +- time' : '6',
                'ext trig + time' : '7',
                'ext gate/trig holdoff' : '8',
                'ext 1 period' : '9',
                'ext 0.01 s gate' : '10',
                'ext 0.1 s gate' : '11',
                'ext 1.0 s gate' : '12',
            }),
    ]

    def performGetValue(self, quant, **kw):
        if quant.name == 'Datas':
            if 'count' in kw.keys():
                count = kw['count']
            else:
                count = 100
            return self.get_Datas(count)
        else:
            return BaseDriver.performGetValue(self, quant, **kw)

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
